import pytest

from src.core import GraphError
from src.graph import Graph


def test_grafo_nuevo_tiene_vertices_y_arcos_vacios():
    grafo = Graph()

    assert grafo.vertices == set()
    assert grafo.arcs == {}


def test_cada_grafo_tiene_sus_propios_vertices_y_arcos():
    primero = Graph()
    segundo = Graph()

    primero.vertices.update({"A", "B"})
    primero.arcs[("A", "B")] = 5

    assert segundo.vertices == set()
    assert segundo.arcs == {}


def test_agregar_un_centro_repetido_conserva_los_otros_centros():
    grafo = Graph()
    for centro in ("A", "B", "A"):
        grafo.add_vertex(centro)
    assert grafo.vertices == {"A", "B"}


@pytest.mark.parametrize("nombre", ["", "   "])
def test_rechaza_nombre_vacio(nombre):
    with pytest.raises(GraphError, match="vacío"):
        Graph().add_vertex(nombre)


@pytest.fixture
def red():
    grafo = Graph()
    for centro in ("A", "B", "C"):
        grafo.add_vertex(centro)
    grafo.add_arc("A", "B", 5)
    return grafo


@pytest.mark.parametrize("capacidad", [1, 12])
def test_agregar_ruta_valida(red, capacidad):
    red.add_arc("A", "C", capacidad)
    assert red.arcs == {("A", "B"): 5, ("A", "C"): capacidad}


@pytest.mark.parametrize(("u", "v", "mensaje"), [
    ("X", "A", "X"), ("A", "X", "X"), ("A", "A", "lazo"),
    ("A", "B", "ya existe"), ("B", "A", "inversa"),
])
def test_rechaza_ruta_invalida_sin_cambiar_la_red(red, u, v, mensaje):
    with pytest.raises(GraphError, match=mensaje):
        red.add_arc(u, v, 2)
    assert red.arcs == {("A", "B"): 5}


@pytest.mark.parametrize("capacidad", [0, 13, -4, 3.5, "5", True])
def test_rechaza_capacidad_invalida_al_agregar(red, capacidad):
    with pytest.raises(GraphError, match="Capacidad"):
        red.add_arc("B", "C", capacidad)
    assert ("B", "C") not in red.arcs


def test_desactivar_ruta_conserva_centros_y_permite_reponerla(red):
    red.disable_arc("A", "B")
    assert red.arcs == {}
    assert red.vertices == {"A", "B", "C"}
    red.add_arc("A", "B", 7)
    assert red.arcs["A", "B"] == 7


def test_desactivar_ruta_inexistente(red):
    with pytest.raises(GraphError):
        red.disable_arc("B", "A")


def test_cambia_solo_la_capacidad_elegida(red):
    red.add_arc("B", "C", 4)
    red.set_capacity("A", "B", 9)
    assert red.arcs == {("A", "B"): 9, ("B", "C"): 4}


@pytest.mark.parametrize("capacidad", [0, 13])
def test_cambio_invalido_conserva_capacidad_anterior(red, capacidad):
    with pytest.raises(GraphError):
        red.set_capacity("A", "B", capacidad)
    assert red.arcs["A", "B"] == 5


def test_cambiar_capacidad_de_ruta_inexistente(red):
    with pytest.raises(GraphError):
        red.set_capacity("A", "C", 3)
