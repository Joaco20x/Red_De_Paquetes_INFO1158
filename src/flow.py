from dataclasses import dataclass
import core
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
