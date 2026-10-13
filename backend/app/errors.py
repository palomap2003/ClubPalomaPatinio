import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


class ApiError(Exception):
    """Error de negocio/validación que se traduce a una respuesta JSON uniforme."""

    def __init__(self, status, codigo, mensaje):
        super().__init__(mensaje)
        self.status = status
        self.codigo = codigo
        self.mensaje = mensaje


def _respuesta(status, codigo, mensaje):
    return jsonify({"error": {"codigo": codigo, "mensaje": mensaje}}), status


def registrar_manejadores(app):
    @app.errorhandler(ApiError)
    def _api_error(e):
        return _respuesta(e.status, e.codigo, e.mensaje)

    @app.errorhandler(HTTPException)
    def _http_error(e):
        return _respuesta(e.code, e.name.upper().replace(" ", "_"), e.description)

    @app.errorhandler(Exception)
    def _inesperado(e):
        # No se expone el detalle interno al cliente (buena práctica de seguridad).
        log.exception("Error no controlado")
        return _respuesta(500, "ERROR_INTERNO", "Error interno del servidor.")
