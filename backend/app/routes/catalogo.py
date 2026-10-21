from flask import Blueprint, current_app, g, jsonify, request

from ..auth import con_perfil
from ..errors import ApiError
from ..extensions import db
from ..models import Deporte, Espacio, Sede, TipoEspacio
from ..reservas_servicio import calcular_slots, obtener_espacio_reservable
from ..serializadores import deporte_json, espacio_json, sede_json
from ..utils import int_a_hora, parsear_fecha

bp = Blueprint("catalogo", __name__, url_prefix="/api/v1")


@bp.get("/sedes")
@con_perfil
def listar_sedes():
    """Lista las sedes con sus horarios de funcionamiento.
    ---
    tags: [Sedes]
    security: [{Bearer: []}]
    responses:
      200: {description: Listado de sedes, schema: {type: array, items: {$ref: '#/definitions/Sede'}}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
    """
    sedes = db.session.query(Sede).filter_by(activa=True).order_by(Sede.nombre).all()
    return jsonify([sede_json(s) for s in sedes])


@bp.get("/sedes/<int:sede_id>")
@con_perfil
def ver_sede(sede_id):
    """Detalle de una sede.
    ---
    tags: [Sedes]
    security: [{Bearer: []}]
    parameters:
      - {in: path, name: sede_id, type: integer, required: true}
    responses:
      200: {description: Sede, schema: {$ref: '#/definitions/Sede'}}
      404: {description: La sede no existe, schema: {$ref: '#/definitions/Error'}}
    """
    sede = db.session.get(Sede, sede_id)
    if sede is None or not sede.activa:
        raise ApiError(404, "SEDE_INEXISTENTE", "La sede no existe.")
    return jsonify(sede_json(sede))


@bp.get("/deportes")
@con_perfil
def listar_deportes():
    """Lista los deportes y sus tipos (sirve para armar el filtro de espacios).
    ---
    tags: [Espacios deportivos]
    security: [{Bearer: []}]
    responses:
      200: {description: Deportes con sus tipos, schema: {type: array, items: {$ref: '#/definitions/Deporte'}}}
    """
    deportes = db.session.query(Deporte).order_by(Deporte.nombre).all()
    return jsonify([deporte_json(d) for d in deportes])


@bp.get("/espacios")
@con_perfil
def listar_espacios():
    """Lista espacios deportivos indicando su sede. Se puede filtrar por sede y por deporte/tipo.
    ---
    tags: [Espacios deportivos]
    security: [{Bearer: []}]
    parameters:
      - {in: query, name: sede_id, type: integer, description: Filtra por sede}
      - {in: query, name: deporte_id, type: integer, description: "Filtra por deporte (Fútbol, Paddle, Básquet...)"}
      - {in: query, name: tipo_id, type: integer, description: "Filtra por tipo (Fútbol 5, Fútbol 7...)"}
    responses:
      200: {description: Listado de espacios, schema: {type: array, items: {$ref: '#/definitions/Espacio'}}}
      400: {description: Filtro inválido, schema: {$ref: '#/definitions/Error'}}
    """
    q = (
        db.session.query(Espacio)
        .join(Sede)
        .join(TipoEspacio)
        .filter(Espacio.activo.is_(True), Sede.activa.is_(True))
    )
    for param, columna in (("sede_id", Espacio.sede_id), ("tipo_id", Espacio.tipo_espacio_id), ("deporte_id", TipoEspacio.deporte_id)):
        valor = request.args.get(param)
        if valor is not None:
            if not valor.isdigit():
                raise ApiError(400, "FILTRO_INVALIDO", f"'{param}' debe ser un número.")
            q = q.filter(columna == int(valor))
    espacios = q.order_by(Sede.nombre, Espacio.nombre).all()
    return jsonify([espacio_json(e) for e in espacios])


@bp.get("/espacios/<int:espacio_id>")
@con_perfil
def ver_espacio(espacio_id):
    """Detalle de un espacio deportivo.
    ---
    tags: [Espacios deportivos]
    security: [{Bearer: []}]
    parameters:
      - {in: path, name: espacio_id, type: integer, required: true}
    responses:
      200: {description: Espacio, schema: {$ref: '#/definitions/Espacio'}}
      404: {description: El espacio no existe, schema: {$ref: '#/definitions/Error'}}
    """
    return jsonify(espacio_json(obtener_espacio_reservable(espacio_id)))


@bp.get("/espacios/<int:espacio_id>/disponibilidad")
@con_perfil
def disponibilidad(espacio_id):
    """Franjas horarias de un espacio para una fecha, dentro del horario de la sede.
    Cada franja indica si está disponible: libre, futura y sin otra reserva del usuario que se superponga.
    ---
    tags: [Espacios deportivos]
    security: [{Bearer: []}]
    parameters:
      - {in: path, name: espacio_id, type: integer, required: true}
      - {in: query, name: fecha, type: string, required: true, description: "YYYY-MM-DD", example: "2026-11-20"}
      - {in: query, name: duracion, type: integer, default: 1, description: "Horas de la reserva (mínimo 1)"}
    responses:
      200: {description: Franjas, schema: {type: array, items: {$ref: '#/definitions/Franja'}}}
      400: {description: Fecha o duración inválida, schema: {$ref: '#/definitions/Error'}}
      404: {description: El espacio no existe, schema: {$ref: '#/definitions/Error'}}
    """
    espacio = obtener_espacio_reservable(espacio_id)
    fecha = parsear_fecha(request.args.get("fecha"))
    duracion = request.args.get("duracion", "1")
    if not duracion.isdigit() or int(duracion) < 1:
        raise ApiError(400, "DURACION_INVALIDA", "La duración debe ser un número entero de horas (mínimo 1).")
    ahora = current_app.config["CLOCK"]()
    slots = calcular_slots(espacio, fecha, int(duracion), ahora, g.usuario)
    return jsonify(
        [
            {"hora_inicio": int_a_hora(s["inicio"]), "hora_fin": int_a_hora(s["fin"]), "disponible": s["disponible"]}
            for s in slots
        ]
    )
