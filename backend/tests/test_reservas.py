from datetime import datetime

import pytest

ESPACIO = 1  # Moron_Rivadavia_Futbol_F5_1 (sede Morón: 08:00 a 23:00, $3.800/h)
FECHA = "2026-11-12"  # el reloj de los tests está en 2026-11-10 12:00


def reservar(client, headers, fecha=FECHA, ini="18:00", fin="19:00", espacio=ESPACIO):
    return client.post(
        "/api/v1/reservas",
        json={"espacio_id": espacio, "fecha": fecha, "hora_inicio": ini, "hora_fin": fin},
        headers=headers,
    )


def codigo(r):
    return r.json["error"]["codigo"]


# ---------- crear ----------
def test_reserva_exitosa_calcula_precio_total(client, ana):
    r = reservar(client, ana, ini="18:00", fin="20:00")
    assert r.status_code == 201
    assert r.json["estado"] == "confirmada"
    assert r.json["precio_total"] == 7600
    assert r.json["sede"]["nombre"] == "Morón"
    assert r.json["espacio"]["nombre"] == "Moron_Rivadavia_Futbol_F5_1"
    assert r.json["puede_cancelar"] is True


@pytest.mark.parametrize("ini,fin", [("18:30", "19:30"), ("18:00", "19:15")])
def test_horas_deben_empezar_y_terminar_en_minuto_00(client, ana, ini, fin):
    r = reservar(client, ana, ini=ini, fin=fin)
    assert r.status_code == 400 and codigo(r) == "HORA_NO_COMPLETA"


def test_formato_de_hora_invalido(client, ana):
    assert codigo(reservar(client, ana, ini="6pm")) == "HORA_INVALIDA"


def test_duracion_minima_una_hora(client, ana):
    assert codigo(reservar(client, ana, ini="18:00", fin="18:00")) == "DURACION_INVALIDA"
    assert codigo(reservar(client, ana, ini="19:00", fin="18:00")) == "DURACION_INVALIDA"


def test_no_puede_empezar_antes_de_la_apertura(client, ana):
    r = reservar(client, ana, ini="07:00", fin="08:00")
    assert r.status_code == 400 and codigo(r) == "FUERA_DE_HORARIO"


def test_fin_no_puede_superar_el_cierre(client, ana):
    assert codigo(reservar(client, ana, ini="22:00", fin="24:00")) == "FUERA_DE_HORARIO"
    assert reservar(client, ana, ini="22:00", fin="23:00").status_code == 201  # termina justo al cierre


def test_debe_ser_horario_futuro(client, ana):
    r = reservar(client, ana, fecha="2026-11-10", ini="11:00", fin="12:00")  # ya pasó (son las 12:00)
    assert r.status_code == 400 and codigo(r) == "HORARIO_PASADO"
    r = reservar(client, ana, fecha="2026-11-10", ini="12:00", fin="13:00")  # empieza "ahora": no es futuro
    assert codigo(r) == "HORARIO_PASADO"
    assert reservar(client, ana, fecha="2026-11-10", ini="13:00", fin="14:00").status_code == 201


def test_fecha_invalida_y_espacio_inexistente(client, ana):
    assert codigo(reservar(client, ana, fecha="12/11/2026")) == "FECHA_INVALIDA"
    r = reservar(client, ana, espacio=9999)
    assert r.status_code == 404 and codigo(r) == "ESPACIO_INEXISTENTE"


def test_requiere_autenticacion(client):
    assert reservar(client, {}).status_code == 401


# ---------- superposición ----------
@pytest.mark.parametrize(
    "ini,fin",
    [("18:00", "19:00"), ("17:00", "19:00"), ("18:00", "20:00"), ("17:00", "21:00"), ("18:00", "19:00")],
)
def test_no_permite_superposicion(client, ana, beto, ini, fin):
    assert reservar(client, ana, ini="18:00", fin="20:00").status_code == 201
    r = reservar(client, beto, ini=ini, fin=fin)
    assert r.status_code == 409 and codigo(r) == "HORARIO_NO_DISPONIBLE"


def test_horarios_contiguos_no_se_superponen(client, ana, beto):
    assert reservar(client, ana, ini="18:00", fin="19:00").status_code == 201
    assert reservar(client, beto, ini="19:00", fin="20:00").status_code == 201
    assert reservar(client, beto, ini="17:00", fin="18:00").status_code == 201


def test_mismo_horario_en_otro_espacio_o_fecha_es_valido(client, ana, beto):
    assert reservar(client, ana).status_code == 201
    assert reservar(client, beto, espacio=2).status_code == 201
    assert reservar(client, beto, fecha="2026-11-13").status_code == 201


# ---------- disponibilidad ----------
def franjas(client, headers, fecha=FECHA, duracion=1, espacio=ESPACIO):
    r = client.get(f"/api/v1/espacios/{espacio}/disponibilidad?fecha={fecha}&duracion={duracion}", headers=headers)
    assert r.status_code == 200
    return {f["hora_inicio"]: f["disponible"] for f in r.json}


def test_disponibilidad_respeta_horario_de_la_sede(client, ana):
    f = franjas(client, ana)
    assert list(f)[0] == "08:00" and list(f)[-1] == "22:00"  # última franja de 1h: 22:00-23:00
    assert all(f.values())


def test_disponibilidad_marca_ocupadas_y_se_libera_al_cancelar(client, ana, beto):
    reserva = reservar(client, ana, ini="18:00", fin="20:00").json
    f = franjas(client, beto)
    assert f["18:00"] is False and f["19:00"] is False and f["17:00"] is True and f["20:00"] is True

    assert client.delete(f"/api/v1/reservas/{reserva['id']}", headers=ana).status_code == 200
    assert franjas(client, beto)["18:00"] is True


def test_disponibilidad_con_duracion_de_2_horas(client, ana):
    reservar(client, ana, ini="19:00", fin="20:00")
    f = franjas(client, ana, duracion=2)
    assert f["17:00"] is True  # 17-19 libre
    assert f["18:00"] is False and f["19:00"] is False  # pisan la reserva de 19-20
    assert list(f)[-1] == "21:00"  # 21-23, termina al cierre


def test_disponibilidad_excluye_horas_pasadas(client, ana):
    f = franjas(client, ana, fecha="2026-11-10")  # hoy, son las 12:00
    assert f["11:00"] is False and f["12:00"] is False and f["13:00"] is True


def test_disponibilidad_parametros_invalidos(client, ana):
    assert client.get("/api/v1/espacios/1/disponibilidad", headers=ana).status_code == 400
    assert client.get(f"/api/v1/espacios/1/disponibilidad?fecha={FECHA}&duracion=0", headers=ana).status_code == 400
    assert client.get(f"/api/v1/espacios/999/disponibilidad?fecha={FECHA}", headers=ana).status_code == 404


# ---------- cancelar ----------
def test_cancelar_reserva(client, ana):
    reserva = reservar(client, ana).json
    r = client.delete(f"/api/v1/reservas/{reserva['id']}", headers=ana)
    assert r.status_code == 200 and r.json["estado"] == "cancelada" and r.json["puede_cancelar"] is False
    assert reservar(client, ana).status_code == 201  # el horario volvió a estar disponible


def test_no_se_puede_cancelar_dos_veces(client, ana):
    rid = reservar(client, ana).json["id"]
    client.delete(f"/api/v1/reservas/{rid}", headers=ana)
    r = client.delete(f"/api/v1/reservas/{rid}", headers=ana)
    assert r.status_code == 409 and codigo(r) == "RESERVA_YA_CANCELADA"


def test_no_se_puede_cancelar_reserva_ajena(client, ana, beto):
    rid = reservar(client, ana).json["id"]
    r = client.delete(f"/api/v1/reservas/{rid}", headers=beto)
    assert r.status_code == 404 and codigo(r) == "RESERVA_INEXISTENTE"


def test_no_se_puede_cancelar_reserva_en_curso_o_pasada(client, ana, reloj):
    rid = reservar(client, ana, ini="18:00", fin="19:00").json["id"]
    reloj["ahora"] = datetime(2026, 11, 12, 18, 30)  # la reserva ya empezó
    r = client.delete(f"/api/v1/reservas/{rid}", headers=ana)
    assert r.status_code == 400 and codigo(r) == "RESERVA_NO_CANCELABLE"


# ---------- listados ----------
def test_mis_reservas_proximas_e_historial(client, ana, beto, reloj):
    futura = reservar(client, ana, fecha="2026-11-12", ini="18:00", fin="19:00").json["id"]
    cancelada = reservar(client, ana, fecha="2026-11-13", ini="18:00", fin="19:00").json["id"]
    client.delete(f"/api/v1/reservas/{cancelada}", headers=ana)
    pasada = reservar(client, ana, fecha="2026-11-10", ini="13:00", fin="14:00").json["id"]
    reservar(client, beto, fecha="2026-11-12", ini="20:00", fin="21:00")  # de otro usuario

    reloj["ahora"] = datetime(2026, 11, 10, 15, 0)  # la reserva de 13-14 ya finalizó
    proximas = client.get("/api/v1/reservas/mis-reservas?tipo=proximas", headers=ana).json
    historial = client.get("/api/v1/reservas/mis-reservas?tipo=historial", headers=ana).json

    assert [r["id"] for r in proximas] == [futura]
    assert {r["id"] for r in historial} == {cancelada, pasada}
    assert {r["estado"] for r in historial} == {"cancelada", "confirmada"}
    assert all(r["sede"]["nombre"] and r["espacio"]["nombre"] and r["fecha"] for r in proximas + historial)


def test_reserva_en_curso_figura_como_proxima_pero_no_cancelable(client, ana, reloj):
    reservar(client, ana, ini="18:00", fin="20:00")
    reloj["ahora"] = datetime(2026, 11, 12, 19, 0)
    r = client.get("/api/v1/reservas/mis-reservas", headers=ana).json  # por defecto: próximas
    assert len(r) == 1 and r[0]["puede_cancelar"] is False


def test_filtro_de_listado_invalido(client, ana):
    assert client.get("/api/v1/reservas/mis-reservas?tipo=otra", headers=ana).status_code == 400


# ---------- errores generales ----------
def test_ruta_inexistente_devuelve_json(client):
    r = client.get("/api/v1/no-existe")
    assert r.status_code == 404 and "error" in r.json


def test_swagger_disponible(client):
    r = client.get("/apispec.json")
    assert r.status_code == 200
    rutas = r.json["paths"]
    assert "/api/v1/reservas" in rutas and "/api/v1/usuarios" in rutas
