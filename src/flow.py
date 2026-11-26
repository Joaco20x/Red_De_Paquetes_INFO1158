from asyncio import graph
from dataclasses import dataclass
from operator import truediv
import core
from cola import ColaArreglo
#arc= aristas
class Graph:#Clase de grafo para hacer pruebas (borrar al terminar issues)
    def __init__(self,vertices,arcs) -> None:
        self.vertices= vertices
        self.arcs= arcs
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
