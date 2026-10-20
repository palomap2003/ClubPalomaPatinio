import os
from datetime import datetime

import pytest

from app import create_app
from app.extensions import db
from app.seed import cargar_datos_ejemplo

AHORA = datetime(2026, 11, 10, 12, 0)  # martes 12:00 (hora Argentina)

IDENTIDADES = {
    "token-ana": {"uid": "uid-ana", "email": "ana@mail.com"},
    "token-beto": {"uid": "uid-beto", "email": "beto@mail.com"},
    "token-nuevo": {"uid": "uid-nuevo", "email": "nuevo@mail.com"},
}


@pytest.fixture()
def reloj():
    return {"ahora": AHORA}


class PushFalso:
    """Reemplaza a FCM en los tests: registra los envíos y permite simular fallas."""

    def __init__(self):
        self.enviados = []
        self.intentos = 0
        self.fallas = []  # excepciones a lanzar, una por intento, antes de tener éxito

    def __call__(self, token, titulo, cuerpo, data, ttl_segundos):
        self.intentos += 1
        if self.fallas:
            raise self.fallas.pop(0)
        self.enviados.append({"token": token, "titulo": titulo, "cuerpo": cuerpo, "data": data, "ttl": ttl_segundos})


@pytest.fixture()
def push():
    return PushFalso()


@pytest.fixture()
def app(reloj, push):
    app = create_app(
        {
            "PUSH_SENDER": push,
            "TESTING": True,
            # Por defecto SQLite en memoria; con TEST_DATABASE_URL se prueba contra PostgreSQL real.
            "SQLALCHEMY_DATABASE_URI": os.environ.get("TEST_DATABASE_URL", "sqlite://"),
            "TOKEN_VERIFIER": lambda token: IDENTIDADES.get(token),
            "CLOCK": lambda: reloj["ahora"],
            "CRON_SECRET": "secreto-de-test",
        }
    )
    with app.app_context():
        db.create_all()
        cargar_datos_ejemplo()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def cabecera(token):
    return {"Authorization": f"Bearer {token}"}


PERFIL_ANA = {"nombre": "Ana", "apellido": "Pérez", "dni": "30111222", "fecha_nacimiento": "1995-03-10"}
PERFIL_BETO = {"nombre": "Beto", "apellido": "Gómez", "dni": "31222333", "fecha_nacimiento": "1990-07-01"}


@pytest.fixture()
def ana(client):
    r = client.post("/api/v1/usuarios", json=PERFIL_ANA, headers=cabecera("token-ana"))
    assert r.status_code == 201
    return cabecera("token-ana")


@pytest.fixture()
def beto(client):
    r = client.post("/api/v1/usuarios", json=PERFIL_BETO, headers=cabecera("token-beto"))
    assert r.status_code == 201
    return cabecera("token-beto")
