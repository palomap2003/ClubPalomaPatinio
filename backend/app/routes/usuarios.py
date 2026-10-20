from datetime import date

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..auth import autenticado, con_perfil
from ..errors import ApiError
from ..extensions import db
from ..models import Usuario
from ..serializadores import usuario_json
from ..utils import parsear_fecha

bp = Blueprint("usuarios", __name__, url_prefix="/api/v1/usuarios")


def _texto(datos, campo, maximo=80):
    valor = datos.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise ApiError(400, "DATOS_INCOMPLETOS", f"El campo '{campo}' es obligatorio.")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ApiError(400, "DATOS_INVALIDOS", f"El campo '{campo}' supera los {maximo} caracteres.")
    return valor


def _fecha_nacimiento(datos):
    f = parsear_fecha(datos.get("fecha_nacimiento"), "fecha_nacimiento")
    if f >= date.today() or f.year < 1900:
        raise ApiError(400, "DATOS_INVALIDOS", "La fecha de nacimiento no es válida.")
    return f


@bp.post("")
@autenticado
def registrar():
    """Completa el perfil del usuario recién creado en Firebase.
    El email y el uid se toman del token (no del body), así nadie puede registrar datos de otra cuenta.
    ---
    tags: [Usuarios]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [nombre, apellido, dni, fecha_nacimiento]
          properties:
            nombre: {type: string, example: Paloma}
            apellido: {type: string, example: Patiño}
            dni: {type: string, example: "40123456"}
            fecha_nacimiento: {type: string, example: "2003-05-20"}
    responses:
      201: {description: Perfil creado, schema: {$ref: '#/definitions/Usuario'}}
      400: {description: Datos incompletos o inválidos, schema: {$ref: '#/definitions/Error'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
      409: {description: Usuario o DNI ya registrado, schema: {$ref: '#/definitions/Error'}}
    """
    datos = request.get_json(silent=True) or {}
    nombre, apellido = _texto(datos, "nombre"), _texto(datos, "apellido")
    dni = _texto(datos, "dni", 12)
    if not dni.isdigit() or not 7 <= len(dni) <= 9:
        raise ApiError(400, "DATOS_INVALIDOS", "El DNI debe contener entre 7 y 9 números.")
    fecha_nac = _fecha_nacimiento(datos)

    uid, email = g.identidad["uid"], g.identidad["email"]
    if not email:
        raise ApiError(400, "DATOS_INVALIDOS", "La cuenta no tiene un email asociado.")
    if db.session.query(Usuario).filter_by(firebase_uid=uid).first():
        raise ApiError(409, "USUARIO_YA_REGISTRADO", "El usuario ya está registrado.")
    if db.session.query(Usuario).filter_by(email=email).first():
        raise ApiError(409, "USUARIO_YA_REGISTRADO", "El correo electrónico ya está registrado.")
    if db.session.query(Usuario).filter_by(dni=dni).first():
        raise ApiError(409, "DNI_YA_REGISTRADO", "El DNI ya está registrado.")

    usuario = Usuario(
        firebase_uid=uid, email=email, nombre=nombre, apellido=apellido, dni=dni, fecha_nacimiento=fecha_nac
    )
    db.session.add(usuario)
    try:
        db.session.commit()
    except IntegrityError:  # dos registros simultáneos con los mismos datos
        db.session.rollback()
        raise ApiError(409, "USUARIO_YA_REGISTRADO", "El usuario o el DNI ya están registrados.")
    return jsonify(usuario_json(usuario)), 201


@bp.get("/me")
@con_perfil
def ver_perfil():
    """Devuelve el perfil del usuario autenticado.
    ---
    tags: [Usuarios]
    security: [{Bearer: []}]
    responses:
      200: {description: Perfil, schema: {$ref: '#/definitions/Usuario'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
      404: {description: El usuario tiene cuenta pero no completó su perfil, schema: {$ref: '#/definitions/Error'}}
    """
    return jsonify(usuario_json(g.usuario))


@bp.put("/me")
@con_perfil
def editar_perfil():
    """Edita nombre, apellido, DNI y fecha de nacimiento. El email no se puede modificar.
    ---
    tags: [Usuarios]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [nombre, apellido, fecha_nacimiento]
          properties:
            nombre: {type: string}
            apellido: {type: string}
            fecha_nacimiento: {type: string, example: "2003-05-20"}
    responses:
      200: {description: Perfil actualizado, schema: {$ref: '#/definitions/Usuario'}}
      400: {description: Datos incompletos o inválidos, schema: {$ref: '#/definitions/Error'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
    """
    datos = request.get_json(silent=True) or {}
    g.usuario.nombre = _texto(datos, "nombre")
    g.usuario.apellido = _texto(datos, "apellido")
    g.usuario.fecha_nacimiento = _fecha_nacimiento(datos)
    db.session.commit()
    return jsonify(usuario_json(g.usuario))


@bp.put("/me/fcm-token")
@con_perfil
def guardar_fcm_token():
    """Guarda el token del dispositivo para enviarle notificaciones push (recordatorios de reservas).
    ---
    tags: [Usuarios]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [token]
          properties:
            token: {type: string}
    responses:
      204: {description: Token guardado}
      400: {description: Falta el token, schema: {$ref: '#/definitions/Error'}}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
    """
    datos = request.get_json(silent=True) or {}
    g.usuario.fcm_token = _texto(datos, "token", 512)
    db.session.commit()
    return "", 204


@bp.delete("/me/fcm-token")
@con_perfil
def borrar_fcm_token():
    """Quita el token del dispositivo (al cerrar sesión), para no enviar avisos a un teléfono sin sesión.
    ---
    tags: [Usuarios]
    security: [{Bearer: []}]
    responses:
      204: {description: Token eliminado}
      401: {description: Sin token o token inválido, schema: {$ref: '#/definitions/Error'}}
    """
    g.usuario.fcm_token = None
    db.session.commit()
    return "", 204
