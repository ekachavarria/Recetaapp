import pytest

from recetaapp.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "recetas.json")
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _crear_receta(client, nombre="Ensalada de espinaca"):
    return client.post(
        "/recetas/nueva",
        data={
            "nombre": nombre,
            "categoria": "Almuerzo",
            "tiempo_preparacion_min": "10",
            "porciones": "2",
            "ingredientes": "2, tazas, espinaca\n1, unidad, aguacate",
            "pasos": "Lavar la espinaca\nCortar el aguacate\nMezclar",
        },
        follow_redirects=True,
    )


def test_listar_vacio_muestra_mensaje(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "No se encontraron recetas".encode() in resp.data


def test_crear_receta(client):
    resp = _crear_receta(client)
    assert resp.status_code == 200
    assert "creada correctamente".encode() in resp.data
    assert "Ensalada de espinaca".encode() in resp.data


def test_crear_receta_invalida_muestra_error(client):
    resp = client.post(
        "/recetas/nueva",
        data={
            "nombre": "",
            "categoria": "Almuerzo",
            "tiempo_preparacion_min": "10",
            "porciones": "2",
            "ingredientes": "2, tazas, espinaca",
            "pasos": "Mezclar",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "no puede estar vac".encode() in resp.data


def test_editar_receta(client):
    _crear_receta(client)
    recetario = client.application.config["RECETARIO"]
    id_receta = recetario.listar()[0].id

    resp = client.post(
        f"/recetas/{id_receta}/editar",
        data={
            "nombre": "Ensalada de espinaca especial",
            "categoria": "Almuerzo",
            "tiempo_preparacion_min": "12",
            "porciones": "3",
            "ingredientes": "2, tazas, espinaca",
            "pasos": "Mezclar todo",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "actualizada correctamente".encode() in resp.data
    assert "Ensalada de espinaca especial".encode() in resp.data


def test_eliminar_receta(client):
    _crear_receta(client)
    recetario = client.application.config["RECETARIO"]
    id_receta = recetario.listar()[0].id

    resp = client.post(f"/recetas/{id_receta}/eliminar", follow_redirects=True)
    assert resp.status_code == 200
    assert "eliminada".encode() in resp.data
    assert recetario.listar() == []


def test_buscar_por_ingrediente(client):
    _crear_receta(client)
    resp = client.get("/?q=aguacate")
    assert "Ensalada de espinaca".encode() in resp.data

    resp = client.get("/?q=no-existe")
    assert "No se encontraron recetas".encode() in resp.data


def test_filtrar_por_categoria(client):
    _crear_receta(client)
    resp = client.get("/?categoria=Cena")
    assert "No se encontraron recetas".encode() in resp.data

    resp = client.get("/?categoria=Almuerzo")
    assert "Ensalada de espinaca".encode() in resp.data
