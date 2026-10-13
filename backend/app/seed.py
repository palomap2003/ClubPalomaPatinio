"""Datos de ejemplo (basados en el diseño de Figma). Las altas de sedes/espacios no son parte de esta entrega."""

from .extensions import db
from .models import Deporte, Espacio, Sede, TipoEspacio, generar_nombre_espacio

DEPORTES = {
    "Fútbol": [("F5", "Fútbol 5"), ("F7", "Fútbol 7"), ("F8", "Fútbol 8"), ("F11", "Fútbol 11")],
    "Tenis": [("Polvo", "Polvo de Ladrillo"), ("Cemento", "Cemento"), ("Sintetico", "Sintético")],
    "Paddle": [("Paddle", "Paddle")],
    "Hockey": [("H7", "Hockey 7"), ("H11", "Hockey 11")],
    "Vóley": [("Playa", "Vóley Playa"), ("Indoor", "Indoor Parquet")],
    "Básquet": [("Basquet", "Básquet")],
}

# nombre, calle, altura, apertura, cierre
SEDES = [
    ("Morón", "Av. Rivadavia", "19850", 8, 23),
    ("Ramos Mejía", "Calle Belgrano", "1240", 9, 22),
    ("San Justo", "Av. Casanova", "320", 9, 23),
    ("Castelar", "Av. Rivadavia", "22500", 10, 22),
]

# sede, deporte, codigo_tipo, cantidad, precio_hora, techado
ESPACIOS = [
    ("Morón", "Fútbol", "F5", 1, 3800, False),
    ("Morón", "Fútbol", "F5", 1, 4200, True),
    ("Morón", "Fútbol", "F7", 1, 5500, False),
    ("Morón", "Fútbol", "F11", 1, 9000, False),
    ("Morón", "Tenis", "Polvo", 2, 2500, False),
    ("Morón", "Tenis", "Cemento", 1, 3000, True),
    ("Morón", "Paddle", "Paddle", 2, 3200, False),
    ("Ramos Mejía", "Fútbol", "F5", 1, 4000, True),
    ("Ramos Mejía", "Fútbol", "F11", 1, 8000, False),
    ("Ramos Mejía", "Hockey", "H7", 1, 3500, False),
    ("Ramos Mejía", "Vóley", "Indoor", 1, 2800, True),
    ("San Justo", "Fútbol", "F5", 2, 4200, False),
    ("San Justo", "Fútbol", "F8", 1, 6000, False),
    ("San Justo", "Tenis", "Sintetico", 1, 2700, False),
    ("Castelar", "Tenis", "Polvo", 1, 2400, False),
    ("Castelar", "Tenis", "Cemento", 1, 2900, False),
    ("Castelar", "Vóley", "Playa", 1, 2200, False),
    ("Castelar", "Hockey", "H11", 1, 7000, False),
    ("Castelar", "Básquet", "Basquet", 1, 3000, True),
]


def cargar_datos_ejemplo():
    """Idempotente: si ya hay sedes no hace nada. Devuelve True si cargó datos."""
    if db.session.query(Sede).first():
        return False

    tipos = {}
    for nombre, lista in DEPORTES.items():
        deporte = Deporte(nombre=nombre)
        db.session.add(deporte)
        for codigo, nombre_tipo in lista:
            tipo = TipoEspacio(deporte=deporte, codigo=codigo, nombre=nombre_tipo)
            db.session.add(tipo)
            tipos[(nombre, codigo)] = tipo

    sedes = {}
    for nombre, calle, altura, apertura, cierre in SEDES:
        sede = Sede(nombre=nombre, calle=calle, altura=altura, hora_apertura=apertura, hora_cierre=cierre)
        db.session.add(sede)
        sedes[nombre] = sede
    db.session.flush()

    contadores = {}
    for sede_n, deporte, codigo, cantidad, precio, techado in ESPACIOS:
        sede, tipo = sedes[sede_n], tipos[(deporte, codigo)]
        for _ in range(cantidad):
            clave = (sede.id, tipo.id)
            contadores[clave] = contadores.get(clave, 0) + 1
            numero = contadores[clave]
            db.session.add(
                Espacio(
                    sede=sede,
                    tipo=tipo,
                    numero=numero,
                    nombre=generar_nombre_espacio(sede, tipo, numero),
                    precio_hora=precio,
                    techado=techado,
                )
            )
    db.session.commit()
    return True
