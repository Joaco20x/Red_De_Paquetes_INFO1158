from asyncio import graph
from dataclasses import dataclass
from operator import truediv
import core
from cola import ColaArreglo
@dataclass
class FlowResult:
    value: int
    flow: dict[tuple[int, str], int]


@dataclass
class CutResult:
    S: set[str] #origen
    T: set[str] #destino
    cut_arcs: list[core.Arc]
    capacity:int

def build_residual(graph:Graph, flow:core.Flow) -> dict[core.Arc, int]:
    residual= {}
    for arc in graph.arcs:
        c= graph.arcs.get(arc)
        f= flow.get(arc,0)
        if c - f > 0:
            residual[arc] = c - f
        if f > 0:
            residual[tuple(reversed(arc))] = f
    return residual

def bfs_augmenting_path(residual, s, t) -> list | None :
    cola= ColaArreglo(MAX_ELEM=core.VERTICES_MAX)
    cola.encolar(s)
    visitados= {} #visto : como llegue
    visitados[s]=None
    while not cola.estaVacia():
        x = cola.sacar()
        if x== t:
            break
        for arc in residual:
            if arc[0] == x and arc[1] not in visitados:
                cola.encolar(arc[1])
                visitados[arc[1]]=arc
    recorrido= []
    if t not in visitados:
        return None
    while visitados[t]:
        recorrido.append(visitados[t])
        t = visitados[t][0]
    recorrido= list(reversed(recorrido))
    return recorrido

def bottleneck(residual , path) -> int:
    aux = []
    if path == [] :
       raise core.GraphError
    for v in path:
        if v in residual:
            aux.append(residual[v])
        else:
            raise core.GraphError(f"arco {v} no está en la residual")
    return min(aux)

def augment(graph: Graph, flow: core.Flow, path, delta) -> None:
    for p in path:
        invert=tuple(reversed(p))
        if p in graph.arcs:
            flow[p] =flow.get(p,0) + delta
        elif invert in graph.arcs:
            flow[invert] = flow.get(invert,0) - delta
        else:
            raise core.GraphError

def edmonds_karp(graph, s, t) -> FlowResult:
    if s == t or s not in graph.vertices or t not in graph.vertices:
        raise core.GraphError(f"Vertices de entrada {s} o {t} invalidos")
    flow={clave: 0 for clave in graph.arcs}
    while True:
        residual = build_residual(graph,flow)
        camino = bfs_augmenting_path(residual, s , t)
        if camino == None:
            break
        cuello= bottleneck(residual,camino)
        augment(graph,flow,camino,cuello)
    value = 0
    for e in flow:
        if s in e:
            if e[0] == s:
                value += flow[e]
            if e[1] == s:
                value -= flow[e]
    return FlowResult(
        value = value,
        flow = flow
    )

def max_flow(graph: Graph, s: str, t: str) -> FlowResult:
    if isinstance(graph,Graph):
        flow = edmonds_karp(graph,s,t)
        return flow
    else:
        raise core.GraphError
        def reachable_from_source(residual, s):
            visitados = {s}
            cola = ColaArreglo(MAX_ELEM=core.VERTICES_MAX)
            cola.encolar(s)
            while not cola.estaVacia():
                x = cola.sacar()
                for (u, v) in residual:
                    if u == x and v not in visitados:
                        visitados.add(v)
                        cola.encolar(v)
            return visitados

def reachable_from_source(residual, s):
    visitados = {s}
    cola = ColaArreglo(MAX_ELEM=core.VERTICES_MAX)
    cola.encolar(s)
    while not cola.estaVacia():
        x = cola.sacar()
        for (u, v) in residual:
            if u == x and v not in visitados:
                visitados.add(v)
                cola.encolar(v)
    return visitados
def validate_flow(graph, result, s, t):
    errores = []
    flow = result.flow

    # 1. Capacidad: 0 <= flujo <= capacidad en cada arco
    for arc, cap in graph.arcs.items():
        f = flow.get(arc, 0)
        if f < 0:
            errores.append(f"flujo negativo en {arc}: {f}")
        if f > cap:
            errores.append(f"flujo {f} supera capacidad {cap} en {arc}")

    # 2. Conservación en vértices distintos de s y t
    for v in graph.vertices:
        if v in (s, t):
            continue
        entra = sum(flow.get(arc, 0) for arc in graph.arcs if arc[1] == v)
        sale = sum(flow.get(arc, 0) for arc in graph.arcs if arc[0] == v)
        if entra != sale:
            errores.append(f"conservación rota en {v}: entra {entra}, sale {sale}")

    # 3. Valor: neto que sale de s
    neto = 0
    for arc in graph.arcs:
        f = flow.get(arc, 0)
        if arc[0] == s:
            neto += f
        if arc[1] == s:
            neto -= f
    if neto != result.value:
        errores.append(f"valor declarado {result.value} distinto del neto {neto}")

    return errores


def min_cut(graph, result, s, t):
    residual = build_residual(graph, result.flow)
    S = reachable_from_source(residual, s)
    T = set(graph.vertices) - S
    cut_arcs = [arc for arc in graph.arcs if arc[0] in S and arc[1] in T]
    capacity = sum(graph.arcs[arc] for arc in cut_arcs)
    return CutResult(S=S, T=T, cut_arcs=cut_arcs, capacity=capacity)
