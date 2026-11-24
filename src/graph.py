from src.core import GraphError


class Graph:
    """Red dirigida de centros logísticos y rutas con capacidad en paquetes por hora."""

    def __init__(self) -> None:
        """Crea una red vacía con vértices y arcos propios de esta instancia."""
        self.vertices: set[str] = set()
        self.arcs: dict[tuple[str, str], int] = {}

    def add_vertex(self, name: str) -> None:
        """Agrega el centro name una sola vez. Un nombre vacío produce GraphError."""
        if not isinstance(name, str) or not name.strip():
            raise GraphError("El nombre del vértice debe ser texto y no puede estar vacío.")
        self.vertices.add(name)
