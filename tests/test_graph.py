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
