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




residual= {("s","a"): 1, ("a","t"): 1, ("s","b"): 1, ("b","c"): 1, ("c","t"): 1}
residual2= {("s","a"): 1, ("b","t"): 1}
residual3= {("s","b"): 1, ("b","a"): 1, ("a","t"): 1}
residual4 ={("s","a"): 1, ("b","a"): 1}
print(bfs_augmenting_path(residual,"s","t"))
print(bfs_augmenting_path(residual2,"s","t"))
print(bfs_augmenting_path(residual3,"s","t"))
print(bfs_augmenting_path(residual4,"s","t"))
