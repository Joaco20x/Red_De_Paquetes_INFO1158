class Graph:
    """Red dirigida de centros logísticos y rutas con capacidad en paquetes por hora."""

    def __init__(self) -> None:
        """Crea una red vacía con vértices y arcos propios de esta instancia."""
        self.vertices: set[str] = set()
        self.arcs: dict[tuple[str, str], int] = {}
