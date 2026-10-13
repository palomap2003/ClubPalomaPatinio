import json
import os
from functools import wraps

import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials
from flask import current_app, g, request

from .errors import ApiError
from .extensions import db
from .models import Usuario


def init_firebase():
    """Inicializa Firebase Admin una sola vez. Las credenciales vienen de variables de entorno, nunca del repo."""
    if firebase_admin._apps:
        return
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
    elif cred_path:
        cred = credentials.Certificate(cred_path)
    else:
        raise RuntimeError(
            "Falta FIREBASE_CREDENTIALS_JSON o GOOGLE_APPLICATION_CREDENTIALS (ver backend/README.md)."
        )
    firebase_admin.initialize_app(cred)


def verificar_token_firebase(token):
    """Devuelve {'uid', 'email'} si el ID Token es válido (firma, formato y vigencia); si no, None."""
    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception:
        return None
    return {"uid": decoded["uid"], "email": decoded.get("email")}


def _extraer_token():
    cabecera = request.headers.get("Authorization", "")
    if not cabecera.startswith("Bearer ") or not cabecera[7:].strip():
        raise ApiError(401, "NO_AUTENTICADO", "Falta el token de autenticación (Authorization: Bearer <token>).")
    return cabecera[7:].strip()


def autenticado(f):
    """Exige un ID Token válido. Deja en g.identidad el uid/email del usuario autenticado."""

    @wraps(f)
    def envoltura(*args, **kwargs):
        identidad = current_app.config["TOKEN_VERIFIER"](_extraer_token())
        if not identidad:
            raise ApiError(401, "TOKEN_INVALIDO", "El token es inválido o expiró. Iniciá sesión nuevamente.")
        g.identidad = identidad
        return f(*args, **kwargs)

    return envoltura


def con_perfil(f):
    """Además de autenticado, exige que el usuario ya tenga su perfil cargado en la base de datos."""

    @wraps(f)
    @autenticado
    def envoltura(*args, **kwargs):
        usuario = db.session.query(Usuario).filter_by(firebase_uid=g.identidad["uid"]).first()
        if usuario is None:
            raise ApiError(404, "PERFIL_INEXISTENTE", "El usuario no completó su registro.")
        g.usuario = usuario
        return f(*args, **kwargs)

    return envoltura
