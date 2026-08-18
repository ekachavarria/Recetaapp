import json

import pytest

from recetaapp.models.receta import Ingrediente
from recetaapp.models.recetario import RecetaInvalidaError, RecetaNoEncontradaError, Recetario


@pytest.fixture
def recetario(tmp_path):
    return Recetario(tmp_path / "recetas.json")


def _crear_ensalada(recetario):
    return recetario.crear(
        nombre="Ensalada de espinaca",
        categoria="Almuerzo",
        ingredientes=[
            Ingrediente(nombre="espinaca", cantidad=2, unidad="tazas"),
            Ingrediente(nombre="aguacate", cantidad=1, unidad="unidad"),
        ],
        pasos=["Lavar la espinaca", "Cortar el aguacate", "Mezclar"],
        tiempo_preparacion_min=10,
        porciones=2,
    )


def test_crear_y_listar(recetario):
    receta = _crear_ensalada(recetario)
    assert receta.id
    assert [r.nombre for r in recetario.listar()] == ["Ensalada de espinaca"]


def test_crear_receta_duplicada_falla(recetario):
    _crear_ensalada(recetario)
    with pytest.raises(RecetaInvalidaError):
        _crear_ensalada(recetario)


def test_crear_sin_ingredientes_falla(recetario):
    with pytest.raises(RecetaInvalidaError):
        recetario.crear(
            nombre="Vacía",
            categoria="Snack",
            ingredientes=[],
            pasos=["Nada"],
            tiempo_preparacion_min=5,
            porciones=1,
        )


def test_obtener_por_id_inexistente_falla(recetario):
    with pytest.raises(RecetaNoEncontradaError):
        recetario.obtener_por_id("no-existe")


def test_actualizar_receta(recetario):
    receta = _crear_ensalada(recetario)
    actualizada = recetario.actualizar(receta.id, porciones=4)
    assert actualizada.porciones == 4
    assert actualizada.nombre == receta.nombre
    assert actualizada.fecha_actualizacion >= receta.fecha_actualizacion


def test_eliminar_receta(recetario):
    receta = _crear_ensalada(recetario)
    recetario.eliminar(receta.id)
    assert recetario.listar() == []
    with pytest.raises(RecetaNoEncontradaError):
        recetario.obtener_por_id(receta.id)


def test_buscar_por_nombre_e_ingrediente(recetario):
    _crear_ensalada(recetario)
    assert len(recetario.buscar("espinaca")) == 1
    assert len(recetario.buscar("aguacate")) == 1
    assert len(recetario.buscar("no-existe")) == 0


def test_filtrar_por_categoria_y_tiempo(recetario):
    _crear_ensalada(recetario)
    assert len(recetario.filtrar(categoria="Almuerzo")) == 1
    assert len(recetario.filtrar(categoria="Cena")) == 0
    assert len(recetario.filtrar(tiempo_max=5)) == 0
    assert len(recetario.filtrar(tiempo_max=15)) == 1


def test_persistencia_en_disco(tmp_path):
    ruta = tmp_path / "recetas.json"
    r1 = Recetario(ruta)
    _crear_ensalada(r1)

    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    assert len(contenido) == 1

    r2 = Recetario(ruta)
    assert len(r2.listar()) == 1
    assert r2.listar()[0].nombre == "Ensalada de espinaca"
