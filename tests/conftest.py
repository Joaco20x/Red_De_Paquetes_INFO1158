"""Fixtures compartidos. Los grafos se construyen directamente con Graph."""

from src.graph import Graph


def make_graph(arcs: dict[tuple[str, str], int], extra_vertices: set[str] | None = None) -> Graph:
    """Crea un Graph con los arcos dados y sus extremos como vértices.

    Asigna los atributos directamente para no depender de add_vertex/add_arc
    mientras integrante 1 los implementa.
    """
    graph = Graph()
    graph.arcs = dict(arcs)
    graph.vertices = {v for arc in arcs for v in arc} | set(extra_vertices or ())
    return graph
