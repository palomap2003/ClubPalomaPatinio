from flask import Blueprint, current_app, g, jsonify, request

from ..auth import con_perfil
from ..errors import ApiError
from ..reservas_servicio import cancelar_reserva, crear_reserva, listar_reservas, obtener_reserva
from ..serializadores import reserva_json
from ..utils import hora_a_int, parsear_fecha

bp = Blueprint("reservas", __name__, url_prefix="/api/v1/reservas")


@bp.post("")
@con_perfil
def reservar():
    """Reserva un espacio deportivo para una fecha y un rango de horas completas.
    El usuario sale del token: no se envía en el body. El backend valida la disponibilidad antes de registrar.
    ---
    tags: [Reservas]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [espacio_id, fecha, hora_inicio, hora_fin]
          properties:
            espacio_id: {type: integer, example: 1}
            fecha: {type: string, example: "2026-11-20"}
            hora_inicio: {type: string, example: "18:00"}
            hora_fin: {type: string, example: "19:00"}
    responses:
      201: {description: Reserva confirmada, schema: {$ref: '#/definitions/Reserva'}}
      400: {description: "Datos inválidos: hora no completa, fuera del horario de la sede, duración menor a 1h o fecha pasada", schema: {$ref: '#/definitions/Error'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
      404: {description: El espacio no existe, schema: {$ref: '#/definitions/Error'}}
      409: {description: El horario ya está ocupado, schema: {$ref: '#/definitions/Error'}}
    """
    datos = request.get_json(silent=True) or {}
    espacio_id = datos.get("espacio_id")
    if not isinstance(espacio_id, int) or isinstance(espacio_id, bool):
        raise ApiError(400, "DATOS_INCOMPLETOS", "El campo 'espacio_id' es obligatorio y debe ser un número.")
    fecha = parsear_fecha(datos.get("fecha"))
    hora_inicio = hora_a_int(datos.get("hora_inicio"), "hora_inicio")
    hora_fin = hora_a_int(datos.get("hora_fin"), "hora_fin", permitir_24=True)

    ahora = current_app.config["CLOCK"]()
    reserva = crear_reserva(g.usuario, espacio_id, fecha, hora_inicio, hora_fin, ahora)
    return jsonify(reserva_json(reserva, ahora)), 201


@bp.get("/mis-reservas")
@con_perfil
def mis_reservas():
    """Lista las reservas del usuario autenticado, con sede, espacio, fecha y horario.
    `proximas`: confirmadas que todavía no finalizaron. `historial`: finalizadas y canceladas.
    ---
    tags: [Reservas]
    security: [{Bearer: []}]
    parameters:
      - {in: query, name: tipo, type: string, enum: [proximas, historial], default: proximas}
    responses:
      200: {description: Reservas, schema: {type: array, items: {$ref: '#/definitions/Reserva'}}}
      400: {description: Filtro inválido, schema: {$ref: '#/definitions/Error'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
    """
    ahora = current_app.config["CLOCK"]()
    reservas = listar_reservas(g.usuario, request.args.get("tipo", "proximas"), ahora)
    return jsonify([reserva_json(r, ahora) for r in reservas])


@bp.get("/<int:reserva_id>")
@con_perfil
def detalle(reserva_id):
    """Detalle de una reserva propia (es la pantalla a la que lleva la notificación push).
    ---
    tags: [Reservas]
    security: [{Bearer: []}]
    parameters:
      - {in: path, name: reserva_id, type: integer, required: true}
    responses:
      200: {description: Reserva, schema: {$ref: '#/definitions/Reserva'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
      404: {description: La reserva no existe (o es de otro usuario), schema: {$ref: '#/definitions/Error'}}
    """
    return jsonify(reserva_json(obtener_reserva(g.usuario, reserva_id), current_app.config["CLOCK"]()))


@bp.delete("/<int:reserva_id>")
@con_perfil
def cancelar(reserva_id):
    """Cancela una reserva propia. El horario vuelve a estar disponible (cancelación lógica: queda en el historial).
    ---
    tags: [Reservas]
    security: [{Bearer: []}]
    parameters:
      - {in: path, name: reserva_id, type: integer, required: true}
    responses:
      200: {description: Reserva cancelada, schema: {$ref: '#/definitions/Reserva'}}
      400: {description: La reserva ya empezó o finalizó, schema: {$ref: '#/definitions/Error'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
      404: {description: La reserva no existe (o es de otro usuario), schema: {$ref: '#/definitions/Error'}}
      409: {description: La reserva ya estaba cancelada, schema: {$ref: '#/definitions/Error'}}
    """
    ahora = current_app.config["CLOCK"]()
    reserva = cancelar_reserva(g.usuario, reserva_id, ahora)
    return jsonify(reserva_json(reserva, ahora))
