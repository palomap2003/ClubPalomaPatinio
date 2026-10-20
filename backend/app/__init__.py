import os

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify

from .errors import registrar_manejadores
from .extensions import db
from .utils import ahora_ar

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "ClubPalomaPatinio - API de gestión de espacios deportivos",
        "description": (
            "API REST para reservar espacios deportivos.\n\n"
            "**Autenticación:** el login se hace en Firebase Authentication desde la app. Cada request debe enviar "
            "`Authorization: Bearer <ID Token de Firebase>`. En Swagger, usá el botón *Authorize* y pegá "
            "`Bearer <token>`."
        ),
        "version": "1.0.0",
    },
    "securityDefinitions": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header", "description": "Bearer <ID Token>"}
    },
    "definitions": {
        "Error": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {"codigo": {"type": "string", "example": "HORARIO_NO_DISPONIBLE"}, "mensaje": {"type": "string"}},
                }
            },
        },
        "Usuario": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "email": {"type": "string"},
                "nombre": {"type": "string"},
                "apellido": {"type": "string"},
                "dni": {"type": "string"},
                "fecha_nacimiento": {"type": "string", "example": "2003-05-20"},
            },
        },
        "Sede": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "nombre": {"type": "string", "example": "Morón"},
                "direccion": {"type": "string", "example": "Av. Rivadavia 19850"},
                "hora_apertura": {"type": "string", "example": "08:00"},
                "hora_cierre": {"type": "string", "example": "23:00"},
            },
        },
        "Deporte": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "nombre": {"type": "string", "example": "Fútbol"},
                "tipos": {"type": "array", "items": {"type": "object"}},
            },
        },
        "Espacio": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "nombre": {"type": "string", "example": "Moron_Rivadavia_Futbol_F5_1"},
                "numero": {"type": "integer"},
                "deporte": {"type": "string", "example": "Fútbol"},
                "tipo": {"type": "object"},
                "precio_hora": {"type": "number", "example": 3800},
                "techado": {"type": "boolean"},
                "iluminacion": {"type": "boolean"},
                "sede": {"type": "object"},
            },
        },
        "Franja": {
            "type": "object",
            "properties": {
                "hora_inicio": {"type": "string", "example": "18:00"},
                "hora_fin": {"type": "string", "example": "19:00"},
                "disponible": {"type": "boolean"},
            },
        },
        "Reserva": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "estado": {"type": "string", "enum": ["confirmada", "cancelada"]},
                "fecha": {"type": "string", "example": "2026-11-20"},
                "hora_inicio": {"type": "string", "example": "18:00"},
                "hora_fin": {"type": "string", "example": "19:00"},
                "precio_total": {"type": "number"},
                "puede_cancelar": {"type": "boolean"},
                "espacio": {"type": "object"},
                "sede": {"type": "object"},
            },
        },
    },
}


def create_app(config=None):
    load_dotenv()
    app = Flask(__name__)

    uri = os.environ.get("DATABASE_URL", "sqlite:///club.db")
    if uri.startswith("postgres://"):  # Render entrega este formato; SQLAlchemy 2 exige "postgresql://"
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        CLOCK=ahora_ar,  # inyectable para poder testear reglas de "horario futuro"
        TOKEN_VERIFIER=None,  # función token -> {uid, email} | None
        CRON_SECRET=os.environ.get("CRON_SECRET"),
        PUSH_SENDER=None,  # función (token, titulo, cuerpo, data, ttl_segundos); por defecto FCM
    )
    app.json.sort_keys = False
    if config:
        app.config.update(config)

    if app.config["TOKEN_VERIFIER"] is None:
        from .auth import init_firebase, verificar_token_firebase

        init_firebase()
        app.config["TOKEN_VERIFIER"] = verificar_token_firebase

    if app.config["PUSH_SENDER"] is None:
        from .push import enviar_push

        app.config["PUSH_SENDER"] = enviar_push

    db.init_app(app)
    registrar_manejadores(app)

    from .routes import catalogo, notificaciones, reservas, usuarios

    for modulo in (usuarios, catalogo, reservas, notificaciones):
        app.register_blueprint(modulo.bp)

    @app.get("/health")
    def health():
        """Chequeo de salud del servicio.
        ---
        tags: [Sistema]
        responses:
          200: {description: El servicio está activo}
        """
        return jsonify({"estado": "ok"})

    Swagger(app, template=SWAGGER_TEMPLATE, config={
        "headers": [],
        "specs": [{"endpoint": "apispec", "route": "/apispec.json", "rule_filter": lambda r: True, "model_filter": lambda t: True}],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    })

    from .cli import registrar_comandos

    registrar_comandos(app)
    return app
