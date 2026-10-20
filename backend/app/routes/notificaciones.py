import hmac

from flask import Blueprint, current_app, jsonify, request

from ..errors import ApiError
from ..notificaciones_servicio import enviar_recordatorios

bp = Blueprint("notificaciones", __name__, url_prefix="/api/v1/notificaciones")


@bp.post("/recordatorios")
def procesar_recordatorios():
    """Envía los recordatorios push (24 h y 1 h antes) de las reservas confirmadas próximas.
    Lo invoca un planificador externo (cron) cada pocos minutos; no es para usuarios finales.
    Se protege con el header `X-Cron-Secret`, no con el token de Firebase.
    ---
    tags: [Notificaciones]
    parameters:
      - in: header
        name: X-Cron-Secret
        type: string
        required: true
    responses:
      200:
        description: Resumen del procesamiento
        schema:
          type: object
          properties:
            evaluadas: {type: integer}
            enviadas: {type: integer}
            sin_token: {type: integer}
            token_invalido: {type: integer}
            error: {type: integer}
      401: {description: Secreto ausente o incorrecto, schema: {$ref: '#/definitions/Error'}}
    """
    esperado = current_app.config.get("CRON_SECRET")
    recibido = request.headers.get("X-Cron-Secret", "")
    if not esperado or not hmac.compare_digest(esperado, recibido):
        raise ApiError(401, "NO_AUTORIZADO", "Secreto del planificador ausente o incorrecto.")
    resumen = enviar_recordatorios(current_app.config["CLOCK"](), current_app.config["PUSH_SENDER"])
    return jsonify(resumen)
