from datetime import datetime

import pytest

from app.push import ErrorTemporal, TokenInvalido

SECRETO = {"X-Cron-Secret": "secreto-de-test"}
FECHA = "2026-11-11"  # reserva a las 13:00 del miércoles


@pytest.fixture(autouse=True)
def sin_esperas(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)


def con_token(client, headers, token="tok-ana"):
    assert client.put("/api/v1/usuarios/me/fcm-token", json={"token": token}, headers=headers).status_code == 204


def reservar(client, headers, ini="13:00", fin="14:00"):
    r = client.post(
        "/api/v1/reservas",
        json={"espacio_id": 1, "fecha": FECHA, "hora_inicio": ini, "hora_fin": fin},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json["id"]


def procesar(client):
    r = client.post("/api/v1/notificaciones/recordatorios", headers=SECRETO)
    assert r.status_code == 200
    return r.json


# ---------- recordatorio de 24 h ----------
def test_envia_recordatorio_24h(client, ana, push, reloj):
    con_token(client, ana)
    reserva_id = reservar(client, ana)
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)  # faltan 23 h

    assert procesar(client)["enviadas"] == 1
    envio = push.enviados[0]
    assert envio["token"] == "tok-ana"
    assert envio["titulo"] == "Tenés una reserva mañana"
    assert "Moron_Rivadavia_Futbol_F5_1" in envio["cuerpo"] and "13:00 a 14:00" in envio["cuerpo"]
    assert envio["data"] == {"reserva_id": reserva_id, "tipo": "recordatorio_24h"}
    assert envio["ttl"] == 23 * 3600  # el TTL es el tiempo que falta para la reserva


def test_no_envia_si_falta_mas_de_24h_ni_se_repite(client, ana, push, reloj):
    con_token(client, ana)
    reservar(client, ana)
    reloj["ahora"] = datetime(2026, 11, 10, 12, 0)  # faltan 25 h: todavía no
    assert procesar(client)["evaluadas"] == 0

    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)
    assert procesar(client)["enviadas"] == 1
    assert procesar(client)["evaluadas"] == 0  # un mismo recordatorio nunca se envía dos veces
    assert len(push.enviados) == 1


# ---------- recordatorio de 1 h ----------
def test_envia_recordatorio_1h_ademas_del_de_24h(client, ana, push, reloj):
    con_token(client, ana)
    reservar(client, ana)
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)
    procesar(client)
    reloj["ahora"] = datetime(2026, 11, 11, 12, 30)  # falta media hora
    assert procesar(client)["enviadas"] == 1
    assert [e["titulo"] for e in push.enviados] == ["Tenés una reserva mañana", "Tu reserva comienza en 1 hora"]


def test_no_envia_si_la_reserva_ya_empezo(client, ana, push, reloj):
    con_token(client, ana)
    reservar(client, ana)
    reloj["ahora"] = datetime(2026, 11, 11, 13, 30)
    assert procesar(client)["evaluadas"] == 0 and push.enviados == []


# ---------- flujos alternativos ----------
def test_reserva_cancelada_no_genera_recordatorio(client, ana, push, reloj):
    con_token(client, ana)
    reserva_id = reservar(client, ana)
    assert client.delete(f"/api/v1/reservas/{reserva_id}", headers=ana).status_code == 200
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)
    assert procesar(client)["evaluadas"] == 0 and push.enviados == []


def test_sin_token_se_registra_y_no_se_envia(client, ana, push, reloj):
    reservar(client, ana)  # nunca guardó token (permiso denegado o sin sesión)
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)
    assert procesar(client)["sin_token"] == 1 and push.enviados == []


def test_token_invalido_se_elimina_de_la_cuenta(client, ana, push, reloj):
    con_token(client, ana)
    reservar(client, ana)
    push.fallas = [TokenInvalido("no registrado")]
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)

    assert procesar(client)["token_invalido"] == 1
    assert push.intentos == 1  # no se reintenta sobre un token inválido
    reloj["ahora"] = datetime(2026, 11, 10, 14, 5)
    procesar(client)
    assert push.enviados == []  # y el usuario quedó sin token


def test_error_temporal_se_reintenta_y_termina_enviando(client, ana, push, reloj):
    con_token(client, ana)
    reservar(client, ana)
    push.fallas = [ErrorTemporal("503"), ErrorTemporal("503")]
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)

    assert procesar(client)["enviadas"] == 1
    assert push.intentos == 3


def test_tres_errores_seguidos_se_registran_y_no_se_reintentan(client, ana, push, reloj):
    con_token(client, ana)
    reservar(client, ana)
    push.fallas = [ErrorTemporal("503")] * 3
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)

    assert procesar(client)["error"] == 1 and push.intentos == 3
    assert procesar(client)["evaluadas"] == 0  # no vuelve a intentarlo


# ---------- seguridad del endpoint ----------
@pytest.mark.parametrize("headers", [{}, {"X-Cron-Secret": "otro"}, {"Authorization": "Bearer token-ana"}])
def test_endpoint_exige_el_secreto_del_planificador(client, headers):
    r = client.post("/api/v1/notificaciones/recordatorios", headers=headers)
    assert r.status_code == 401 and r.json["error"]["codigo"] == "NO_AUTORIZADO"


# ---------- detalle de reserva y token ----------
def test_detalle_de_reserva_propia(client, ana):
    reserva_id = reservar(client, ana)
    r = client.get(f"/api/v1/reservas/{reserva_id}", headers=ana)
    assert r.status_code == 200 and r.json["id"] == reserva_id and r.json["estado"] == "confirmada"


def test_detalle_de_reserva_ajena_da_404(client, ana, beto):
    reserva_id = reservar(client, ana)
    assert client.get(f"/api/v1/reservas/{reserva_id}", headers=beto).status_code == 404


def test_cerrar_sesion_borra_el_token_fcm(client, ana, push, reloj):
    con_token(client, ana)
    reservar(client, ana)
    assert client.delete("/api/v1/usuarios/me/fcm-token", headers=ana).status_code == 204
    reloj["ahora"] = datetime(2026, 11, 10, 14, 0)
    assert procesar(client)["sin_token"] == 1
