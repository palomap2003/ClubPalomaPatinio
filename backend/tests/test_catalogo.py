from app.seed import SEDES


def test_endpoints_protegidos(client):
    for ruta in ("/api/v1/sedes", "/api/v1/espacios", "/api/v1/deportes", "/api/v1/reservas/mis-reservas"):
        assert client.get(ruta).status_code == 401


def test_listar_sedes_con_horarios(client, ana):
    r = client.get("/api/v1/sedes", headers=ana)
    assert r.status_code == 200
    assert len(r.json) == len(SEDES)
    moron = next(s for s in r.json if s["nombre"] == "Morón")
    assert moron["direccion"] == "Av. Rivadavia 19850"
    assert (moron["hora_apertura"], moron["hora_cierre"]) == ("08:00", "23:00")


def test_sede_inexistente(client, ana):
    r = client.get("/api/v1/sedes/999", headers=ana)
    assert r.status_code == 404
    assert r.json["error"]["codigo"] == "SEDE_INEXISTENTE"


def test_nombre_compuesto_del_espacio(client, ana):
    espacios = client.get("/api/v1/espacios", headers=ana).json
    nombres = {e["nombre"] for e in espacios}
    assert "Moron_Rivadavia_19850_Futbol5_1" in nombres
    assert "Moron_Rivadavia_19850_Futbol5_2" in nombres
    assert "RamosMejia_Belgrano_1240_Hockey7_1" in nombres


def test_listar_espacios_indica_sede(client, ana):
    espacio = client.get("/api/v1/espacios", headers=ana).json[0]
    assert espacio["sede"]["nombre"]
    assert espacio["sede"]["direccion"]


def test_filtrar_espacios_por_sede_deporte_y_tipo(client, ana):
    sedes = {s["nombre"]: s["id"] for s in client.get("/api/v1/sedes", headers=ana).json}
    deportes = {d["nombre"]: d for d in client.get("/api/v1/deportes", headers=ana).json}

    por_sede = client.get(f"/api/v1/espacios?sede_id={sedes['Morón']}", headers=ana).json
    assert por_sede and all(e["sede"]["nombre"] == "Morón" for e in por_sede)

    por_deporte = client.get(f"/api/v1/espacios?deporte_id={deportes['Paddle']['id']}", headers=ana).json
    assert por_deporte and all(e["deporte"] == "Paddle" for e in por_deporte)

    f7 = next(t for t in deportes["Fútbol"]["tipos"] if t["codigo"] == "F7")
    por_tipo = client.get(f"/api/v1/espacios?tipo_id={f7['id']}", headers=ana).json
    assert por_tipo and all(e["tipo"]["nombre"] == "Fútbol 7" for e in por_tipo)


def test_filtro_invalido(client, ana):
    assert client.get("/api/v1/espacios?sede_id=abc", headers=ana).status_code == 400


def test_deportes_incluyen_sus_tipos(client, ana):
    futbol = next(d for d in client.get("/api/v1/deportes", headers=ana).json if d["nombre"] == "Fútbol")
    assert {t["codigo"] for t in futbol["tipos"]} == {"F5", "F7", "F8", "F11"}


def test_nombres_siguen_el_formato_del_enunciado(client, ana):
    """Sede_Calle_Altura_Tipo_Numero, como Moron_Rivadavia_19850_Paddle_1."""
    nombres = {e["nombre"] for e in client.get("/api/v1/espacios", headers=ana).json}
    assert "Moron_Rivadavia_19850_Paddle_1" in nombres
    assert len(nombres) == 22  # todos distintos
