from .utils import int_a_hora


def usuario_json(u):
    return {
        "id": u.id,
        "email": u.email,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "dni": u.dni,
        "fecha_nacimiento": u.fecha_nacimiento.isoformat(),
    }


def sede_json(s):
    return {
        "id": s.id,
        "nombre": s.nombre,
        "direccion": s.direccion,
        "hora_apertura": int_a_hora(s.hora_apertura),
        "hora_cierre": int_a_hora(s.hora_cierre),
    }


def deporte_json(d):
    return {
        "id": d.id,
        "nombre": d.nombre,
        "tipos": [{"id": t.id, "nombre": t.nombre, "codigo": t.codigo} for t in d.tipos],
    }


def espacio_json(e):
    return {
        "id": e.id,
        "nombre": e.nombre,
        "numero": e.numero,
        "deporte": e.tipo.deporte.nombre,
        "tipo": {"id": e.tipo.id, "nombre": e.tipo.nombre},
        "precio_hora": float(e.precio_hora),
        "techado": e.techado,
        "iluminacion": e.iluminacion,
        "sede": {"id": e.sede.id, "nombre": e.sede.nombre, "direccion": e.sede.direccion},
    }


def reserva_json(r, ahora):
    e = r.espacio
    return {
        "id": r.id,
        "estado": r.estado,
        "fecha": r.fecha.isoformat(),
        "hora_inicio": int_a_hora(r.hora_inicio),
        "hora_fin": int_a_hora(r.hora_fin),
        "precio_total": float(r.precio_total),
        "puede_cancelar": r.estado == "confirmada" and r.inicio > ahora,
        "espacio": {"id": e.id, "nombre": e.nombre, "deporte": e.tipo.deporte.nombre, "tipo": e.tipo.nombre},
        "sede": {"id": e.sede.id, "nombre": e.sede.nombre, "direccion": e.sede.direccion},
    }
