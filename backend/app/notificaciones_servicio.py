"""Recordatorios de reservas próximas (CU-24.1): 24 h y 1 h antes del inicio."""

import time
from datetime import timedelta

from .extensions import db
from .models import (
    ESTADO_CONFIRMADA,
    TIPO_RECORDATORIO_1H,
    TIPO_RECORDATORIO_24H,
    Notificacion,
    Reserva,
)
from .push import ErrorTemporal, TokenInvalido
from .utils import int_a_hora

# Ventana de tiempo restante en la que corresponde cada recordatorio. Con un planificador que corre cada
# pocos minutos alcanza; la de 24 h es ancha para tolerar alguna ejecución perdida.
VENTANAS = {
    TIPO_RECORDATORIO_24H: (timedelta(hours=22), timedelta(hours=24)),
    TIPO_RECORDATORIO_1H: (timedelta(0), timedelta(hours=1)),
}
TITULOS = {
    TIPO_RECORDATORIO_24H: "Tenés una reserva mañana",
    TIPO_RECORDATORIO_1H: "Tu reserva comienza en 1 hora",
}
MAX_INTENTOS = 3


def _mensaje(reserva):
    return (
        f"{reserva.espacio.sede.nombre} · {reserva.espacio.nombre} · {reserva.fecha.strftime('%d/%m/%Y')} "
        f"de {int_a_hora(reserva.hora_inicio)} a {int_a_hora(reserva.hora_fin)}"
    )


def _enviar_con_reintentos(enviar, esperar, *args):
    """Hasta 3 intentos con espera exponencial (1 s, 2 s) ante errores temporales."""
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            enviar(*args)
            return
        except ErrorTemporal:
            if intento == MAX_INTENTOS:
                raise
            esperar(2 ** (intento - 1))


def enviar_recordatorios(ahora, enviar, esperar=None):
    """Evalúa las reservas confirmadas próximas y envía los recordatorios que correspondan.
    Devuelve un resumen {evaluadas, enviadas, sin_token, token_invalido, error}."""
    esperar = esperar or time.sleep
    resumen = {"evaluadas": 0, "enviadas": 0, "sin_token": 0, "token_invalido": 0, "error": 0}
    candidatas = (
        db.session.query(Reserva)
        .filter(
            Reserva.estado == ESTADO_CONFIRMADA,
            Reserva.fecha >= ahora.date(),
            Reserva.fecha <= ahora.date() + timedelta(days=2),
        )
        .all()
    )
    for reserva in candidatas:
        restante = reserva.inicio - ahora
        for tipo, (minimo, maximo) in VENTANAS.items():
            if not (minimo < restante <= maximo):
                continue
            if any(n.tipo == tipo for n in reserva.notificaciones):
                continue  # ya procesado: nunca se repite
            resumen["evaluadas"] += 1
            usuario = reserva.usuario
            if not usuario.fcm_token:
                resultado = "sin_token"  # queda el aviso dentro de la app (tarjeta de próximas reservas)
            else:
                try:
                    _enviar_con_reintentos(
                        enviar,
                        esperar,
                        usuario.fcm_token,
                        TITULOS[tipo],
                        _mensaje(reserva),
                        {"reserva_id": reserva.id, "tipo": tipo},
                        restante.total_seconds(),
                    )
                    resultado = "enviada"
                except TokenInvalido:
                    usuario.fcm_token = None  # no se reintenta sobre un token que ya no existe
                    resultado = "token_invalido"
                except ErrorTemporal:
                    resultado = "error"
            db.session.add(Notificacion(reserva_id=reserva.id, tipo=tipo, resultado=resultado))
            db.session.commit()
            resumen["enviadas" if resultado == "enviada" else resultado] += 1
    return resumen
