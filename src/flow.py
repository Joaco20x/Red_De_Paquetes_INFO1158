"""Funciones de flujo máximo y corte mínimo sobre ``Graph``.

Implementa Edmonds–Karp: Ford–Fulkerson con búsqueda en anchura.
"""

from src.cola import ColaArreglo
from src.core import (
    Arc,
    CutResult,
    Flow,
    FlowResult,
    GraphError,
    VERTICES_MAX,
)
from src.graph import Graph


def build_residual(graph: Graph, flow: Flow) -> dict[Arc, int]:
    """Devuelve la red residual de ``graph`` para el flujo ``flow``.

    Incluye solo arcos con capacidad residual estrictamente positiva.
    No lanza excepciones.
    """
    residual: dict[Arc, int] = {}
    for arc, capacity in graph.arcs.items():
        sent = flow.get(arc, 0)
        if capacity - sent > 0:
            residual[arc] = capacity - sent
        if sent > 0:
            inverse = (arc[1], arc[0])
            residual[inverse] = sent
    return residual


def bfs_augmenting_path(
    residual: dict[Arc, int], s: str, t: str
) -> list[Arc] | None:
    """Devuelve un camino aumentante de ``s`` a ``t`` con el menor número de arcos.

    Usa búsqueda en anchura sobre la red residual. Devuelve ``None`` si ``t``
    no es alcanzable. No lanza excepciones.
    """
    cola = ColaArreglo(MAX_ELEM=VERTICES_MAX)
    cola.encolar(s)
    visitados: dict[str, Arc | None] = {s: None}

    while not cola.estaVacia():
        actual = cola.sacar()
        if actual == t:
            break
        for arc in residual:
            if arc[0] == actual and arc[1] not in visitados:
                cola.encolar(arc[1])
                visitados[arc[1]] = arc

    if t not in visitados:
        return None

    camino: list[Arc] = []
    actual = t
    while visitados[actual] is not None:
        arc = visitados[actual]
        camino.append(arc)
        actual = arc[0]
    camino.reverse()
    return camino


def bottleneck(residual: dict[Arc, int], path: list[Arc]) -> int:
    """Devuelve el mínimo de las capacidades residuales del camino.

    Lanza ``GraphError`` si ``path`` está vacío o contiene un arco que no
    pertenece a la red residual.
    """
    if not path:
        raise GraphError("El camino aumentante no puede estar vacío")

    capacidades: list[int] = []
    for arc in path:
        if arc not in residual:
            raise GraphError(f"El arco {arc} no está en la red residual")
        capacidades.append(residual[arc])
    return min(capacidades)


def augment(graph: Graph, flow: Flow, path: list[Arc], delta: int) -> None:
    """Aplica un aumento de ``delta`` unidades a lo largo de ``path``.

    Suma en arcos directos y resta en arcos inversos. Modifica ``flow`` en el
    lugar. Lanza ``GraphError`` si un arco no pertenece a la red original ni
    es el inverso de uno existente.
    """
    for arc in path:
        inverse = (arc[1], arc[0])
        if arc in graph.arcs:
            flow[arc] = flow.get(arc, 0) + delta
        elif inverse in graph.arcs:
            flow[inverse] = flow.get(inverse, 0) - delta
        else:
            raise GraphError(f"El arco {arc} no pertenece a la red")


def edmonds_karp(graph: Graph, s: str, t: str) -> FlowResult:
    """Calcula el flujo máximo de ``s`` a ``t`` con Edmonds–Karp.

    Lanza ``GraphError`` si ``s`` o ``t`` no existen en el grafo, o si
    ``s == t``.
    """
    if s == t or s not in graph.vertices or t not in graph.vertices:
        raise GraphError(f"Vértices de entrada {s!r} o {t!r} inválidos")

    flow: Flow = {arc: 0 for arc in graph.arcs}
    while True:
        residual = build_residual(graph, flow)
        camino = bfs_augmenting_path(residual, s, t)
        if camino is None:
            break
        delta = bottleneck(residual, camino)
        augment(graph, flow, camino, delta)

    value = sum(sent for (u, _), sent in flow.items() if u == s)
    value -= sum(sent for (_, v), sent in flow.items() if v == s)
    return FlowResult(value=value, flow=flow)


def max_flow(graph: Graph, s: str, t: str) -> FlowResult:
    """Función pública de flujo máximo.

    Valida que ``graph`` sea un ``Graph`` y delega en ``edmonds_karp``.
    Lanza ``GraphError`` para entradas inválidas.
    """
    if not isinstance(graph, Graph):
        raise GraphError("graph debe ser una instancia de Graph")
    return edmonds_karp(graph, s, t)


def reachable_from_source(residual: dict[Arc, int], s: str) -> set[str]:
    """Devuelve los vértices alcanzables desde ``s`` por arcos residuales.

    El conjunto siempre incluye a ``s``. No lanza excepciones.
    """
    visitados = {s}
    cola = ColaArreglo(MAX_ELEM=VERTICES_MAX)
    cola.encolar(s)

    while not cola.estaVacia():
        actual = cola.sacar()
        for (u, v) in residual:
            if u == actual and v not in visitados:
                visitados.add(v)
                cola.encolar(v)
    return visitados


def validate_flow(graph: Graph, result: FlowResult, s: str, t: str) -> list[str]:
    """Verifica capacidad, conservación y valor de un flujo cualquiera.

    Es independiente de cómo se calculó el flujo. Devuelve un mensaje por cada
    violación; una lista vacía significa que el flujo es válido. No lanza
    excepciones.
    """
    errores: list[str] = []
    flow = result.flow

    for arc, cap in graph.arcs.items():
        f = flow.get(arc, 0)
        if f < 0:
            errores.append(f"flujo negativo en {arc}: {f}")
        if f > cap:
            errores.append(f"flujo {f} supera capacidad {cap} en {arc}")

    for v in graph.vertices:
        if v in (s, t):
            continue
        entra = sum(flow.get(arc, 0) for arc in graph.arcs if arc[1] == v)
        sale = sum(flow.get(arc, 0) for arc in graph.arcs if arc[0] == v)
        if entra != sale:
            errores.append(f"conservación rota en {v}: entra {entra}, sale {sale}")

    neto = sum(flow.get(arc, 0) for arc in graph.arcs if arc[0] == s)
    neto -= sum(flow.get(arc, 0) for arc in graph.arcs if arc[1] == s)
    if neto != result.value:
        errores.append(f"valor declarado {result.value} distinto del neto {neto}")

    return errores


def min_cut(graph: Graph, result: FlowResult, s: str, t: str) -> CutResult:
    """Construye el corte mínimo asociado al flujo ``result``.

    Usa el teorema de flujo máximo–corte mínimo: ``S`` son los vértices
    alcanzables desde ``s`` en la red residual. Lanza ``GraphError`` si ``s``
    o ``t`` no existen, o si ``s == t``.
    """
    if s == t or s not in graph.vertices or t not in graph.vertices:
        raise GraphError(f"Vértices de entrada {s!r} o {t!r} inválidos")

    residual = build_residual(graph, result.flow)
    S = reachable_from_source(residual, s)
    T = set(graph.vertices) - S
    cut_arcs = [arc for arc in graph.arcs if arc[0] in S and arc[1] in T]
    capacity = sum(graph.arcs[arc] for arc in cut_arcs)
    return CutResult(S=S, T=T, cut_arcs=cut_arcs, capacity=capacity)
