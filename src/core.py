from dataclasses import dataclass


class GraphError(ValueError):
    """Violación de una regla de la red: lazo, arco repetido, arco recíproco,
        capacidad fuera de rango, vértice inexistente, vértice aislado, etc."""
Arc = tuple[str, str]          # arco dirigido (origen, destino)
Flow = dict[Arc, int]          # flujo asignado a cada arco original

CAPACITY_MIN = 1               # capacidad mínima de una ruta (paquetes/hora)
CAPACITY_MAX = 12              # capacidad máxima de una ruta (paquetes/hora)
VERTICES_MIN = 10              # |V| mínimo en la configuración inicial
VERTICES_MAX = 12              # |V| máximo en la configuración inicial
ARCS_MIN = 15                  # |E| mínimo en la configuración inicial
ARCS_MAX = 20                  # |E| máximo en la configuración inicial


@dataclass
class FlowResult:
    value: int          # cantidad neta que sale de s
    flow: Flow          # flujo de cada arco original, incluidos los de flujo 0


@dataclass
class CutResult:
    S: set[str]                 # vértices del lado de s
    T: set[str]                 # vértices del lado de t
    cut_arcs: list[Arc]         # arcos (u, v) con u en S y v en T
    capacity: int               # suma de capacidades originales de cut_arcs
