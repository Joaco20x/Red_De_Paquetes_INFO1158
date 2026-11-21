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
