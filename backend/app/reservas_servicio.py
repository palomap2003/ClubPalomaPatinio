"""Reglas de negocio de reservas y disponibilidad (todo lo que exige el enunciado del TP)."""

from datetime import datetime, time, timedelta

from sqlalchemy import and_, or_

from .errors import ApiError
from .extensions import db
from .models import ESTADO_CANCELADA, ESTADO_CONFIRMADA, Espacio, Reserva, Usuario, utcnow


def obtener_espacio_reservable(espacio_id):
    espacio = db.session.get(Espacio, espacio_id)
    if espacio is None or not espacio.activo or not espacio.sede.activa:
        raise ApiError(404, "ESPACIO_INEXISTENTE", "El espacio deportivo no existe o no está disponible.")
    return espacio


def _hay_superposicion(fecha, hora_inicio, hora_fin, espacio_id=None, usuario_id=None):
    """Dos rangos [a,b) y [c,d) se superponen si a < d y b > c. Rangos contiguos (19-20 y 20-21) NO se superponen.
    Se filtra por espacio (otro usuario ya lo ocupa) o por usuario (ya tiene otra reserva en ese horario)."""
    q = db.session.query(Reserva.id).filter(
        Reserva.fecha == fecha,
        Reserva.estado == ESTADO_CONFIRMADA,
        Reserva.hora_inicio < hora_fin,
        Reserva.hora_fin > hora_inicio,
    )
    if espacio_id is not None:
        q = q.filter(Reserva.espacio_id == espacio_id)
    if usuario_id is not None:
        q = q.filter(Reserva.usuario_id == usuario_id)
    return q.first() is not None


def _inicio_dt(fecha, hora):
    return datetime.combine(fecha, time.min) + timedelta(hours=hora)


def calcular_slots(espacio, fecha, duracion, ahora, usuario=None):
    """Franjas de inicio posibles dentro del horario de la sede. Una franja no está disponible si el espacio ya
    está ocupado, si ya pasó o si el usuario ya tiene otra reserva (en cualquier espacio) que se superpone."""
    sede = espacio.sede
    consulta = db.session.query(Reserva.hora_inicio, Reserva.hora_fin).filter(
        Reserva.fecha == fecha, Reserva.estado == ESTADO_CONFIRMADA
    )
    ocupadas = consulta.filter(Reserva.espacio_id == espacio.id).all()
    propias = consulta.filter(Reserva.usuario_id == usuario.id).all() if usuario is not None else []
    slots = []
    for inicio in range(sede.hora_apertura, sede.hora_cierre - duracion + 1):
        fin = inicio + duracion
        libre = all(not (inicio < o_fin and fin > o_ini) for o_ini, o_fin in ocupadas + propias)
        futura = _inicio_dt(fecha, inicio) > ahora
        slots.append({"inicio": inicio, "fin": fin, "disponible": libre and futura})
    return slots


def crear_reserva(usuario, espacio_id, fecha, hora_inicio, hora_fin, ahora):
    espacio = obtener_espacio_reservable(espacio_id)
    sede = espacio.sede

    if hora_fin - hora_inicio < 1:
        raise ApiError(400, "DURACION_INVALIDA", "La reserva debe durar como mínimo una hora.")
    if hora_inicio < sede.hora_apertura or hora_fin > sede.hora_cierre:
        raise ApiError(
            400,
            "FUERA_DE_HORARIO",
            f"El horario debe estar entre las {sede.hora_apertura:02d}:00 y las {sede.hora_cierre:02d}:00 de la sede.",
        )
    if _inicio_dt(fecha, hora_inicio) <= ahora:
        raise ApiError(400, "HORARIO_PASADO", "La reserva debe ser para un horario futuro.")

    # Se bloquea la fila del espacio hasta el commit: dos reservas simultáneas sobre el mismo
    # espacio se procesan de a una, así la validación de superposición no puede "pisarse".
    # También se bloquea la fila del usuario: dos pedidos simultáneos suyos sobre canchas distintas no se pisan.
    db.session.query(Usuario).filter_by(id=usuario.id).with_for_update().first()
    db.session.query(Espacio).filter_by(id=espacio.id).with_for_update().first()
    if _hay_superposicion(fecha, hora_inicio, hora_fin, espacio_id=espacio.id):
        raise ApiError(409, "HORARIO_NO_DISPONIBLE", "El horario seleccionado ya no está disponible. Elegí otro turno.")
    if _hay_superposicion(fecha, hora_inicio, hora_fin, usuario_id=usuario.id):
        raise ApiError(
            409,
            "RESERVA_SUPERPUESTA_USUARIO",
            "Ya tenés una reserva en ese horario. No podés reservar dos espacios a la misma hora.",
        )

    reserva = Reserva(
        usuario_id=usuario.id,
        espacio_id=espacio.id,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        estado=ESTADO_CONFIRMADA,
        precio_total=espacio.precio_hora * (hora_fin - hora_inicio),
    )
    db.session.add(reserva)
    db.session.commit()
    return reserva


def obtener_reserva(usuario, reserva_id):
    # Si la reserva es de otro usuario se responde 404 (no se revela que existe).
    reserva = db.session.query(Reserva).filter_by(id=reserva_id, usuario_id=usuario.id).first()
    if reserva is None:
        raise ApiError(404, "RESERVA_INEXISTENTE", "La reserva no existe.")
    return reserva


def cancelar_reserva(usuario, reserva_id, ahora):
    reserva = obtener_reserva(usuario, reserva_id)
    if reserva.estado == ESTADO_CANCELADA:
        raise ApiError(409, "RESERVA_YA_CANCELADA", "La reserva ya estaba cancelada.")
    if reserva.inicio <= ahora:
        raise ApiError(400, "RESERVA_NO_CANCELABLE", "No se pueden cancelar reservas pasadas o en curso.")
    reserva.estado = ESTADO_CANCELADA
    reserva.cancelada_en = utcnow()
    db.session.commit()  # el horario queda libre automáticamente: la superposición solo mira las confirmadas
    return reserva


def _filtro_proximas(ahora):
    """Confirmada y que todavía no terminó (incluye la que está en curso)."""
    hoy, minutos = ahora.date(), ahora.hour * 60 + ahora.minute
    return and_(
        Reserva.estado == ESTADO_CONFIRMADA,
        or_(Reserva.fecha > hoy, and_(Reserva.fecha == hoy, Reserva.hora_fin * 60 > minutos)),
    )


def listar_reservas(usuario, tipo, ahora):
    q = db.session.query(Reserva).filter(Reserva.usuario_id == usuario.id)
    if tipo == "proximas":
        q = q.filter(_filtro_proximas(ahora)).order_by(Reserva.fecha, Reserva.hora_inicio)
    elif tipo == "historial":
        # Historial: reservas ya finalizadas y canceladas.
        q = q.filter(~_filtro_proximas(ahora)).order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc())
    else:
        raise ApiError(400, "FILTRO_INVALIDO", "El parámetro 'tipo' debe ser 'proximas' o 'historial'.")
    return q.all()
