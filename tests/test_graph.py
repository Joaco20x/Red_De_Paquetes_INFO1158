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
