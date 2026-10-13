from conftest import PERFIL_ANA, PERFIL_BETO, cabecera


def test_registro_exitoso_toma_email_del_token(client):
    r = client.post("/api/v1/usuarios", json=PERFIL_ANA, headers=cabecera("token-ana"))
    assert r.status_code == 201
    assert r.json["email"] == "ana@mail.com"
    assert r.json["nombre"] == "Ana"


def test_registro_sin_token_es_401(client):
    assert client.post("/api/v1/usuarios", json=PERFIL_ANA).status_code == 401


def test_registro_con_token_invalido_es_401(client):
    r = client.post("/api/v1/usuarios", json=PERFIL_ANA, headers=cabecera("token-falso"))
    assert r.status_code == 401
    assert r.json["error"]["codigo"] == "TOKEN_INVALIDO"


def test_registro_campos_incompletos(client):
    r = client.post("/api/v1/usuarios", json={"nombre": "Ana"}, headers=cabecera("token-ana"))
    assert r.status_code == 400
    assert r.json["error"]["codigo"] == "DATOS_INCOMPLETOS"


def test_registro_dni_invalido_y_fecha_futura(client):
    h = cabecera("token-ana")
    assert client.post("/api/v1/usuarios", json={**PERFIL_ANA, "dni": "abc"}, headers=h).status_code == 400
    assert client.post("/api/v1/usuarios", json={**PERFIL_ANA, "fecha_nacimiento": "2999-01-01"}, headers=h).status_code == 400


def test_registro_usuario_ya_registrado(client, ana):
    r = client.post("/api/v1/usuarios", json=PERFIL_ANA, headers=ana)
    assert r.status_code == 409
    assert r.json["error"]["codigo"] == "USUARIO_YA_REGISTRADO"


def test_registro_dni_duplicado_en_otra_cuenta(client, ana):
    r = client.post("/api/v1/usuarios", json={**PERFIL_BETO, "dni": PERFIL_ANA["dni"]}, headers=cabecera("token-beto"))
    assert r.status_code == 409
    assert r.json["error"]["codigo"] == "DNI_YA_REGISTRADO"


def test_ver_perfil(client, ana):
    r = client.get("/api/v1/usuarios/me", headers=ana)
    assert r.status_code == 200
    assert r.json["apellido"] == "Pérez"


def test_perfil_inexistente_para_cuenta_sin_registro(client):
    r = client.get("/api/v1/usuarios/me", headers=cabecera("token-nuevo"))
    assert r.status_code == 404
    assert r.json["error"]["codigo"] == "PERFIL_INEXISTENTE"


def test_editar_perfil_no_cambia_email_ni_dni(client, ana):
    r = client.put(
        "/api/v1/usuarios/me",
        json={"nombre": "Ana María", "apellido": "Pérez", "fecha_nacimiento": "1995-03-11", "email": "otro@mail.com", "dni": "1"},
        headers=ana,
    )
    assert r.status_code == 200
    assert r.json["nombre"] == "Ana María"
    assert r.json["fecha_nacimiento"] == "1995-03-11"
    assert r.json["email"] == "ana@mail.com"
    assert r.json["dni"] == PERFIL_ANA["dni"]


def test_guardar_fcm_token(client, ana):
    assert client.put("/api/v1/usuarios/me/fcm-token", json={"token": "abc123"}, headers=ana).status_code == 204
    assert client.put("/api/v1/usuarios/me/fcm-token", json={}, headers=ana).status_code == 400
