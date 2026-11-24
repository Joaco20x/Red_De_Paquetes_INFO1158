from src.core import CAPACITY_MAX, CAPACITY_MIN, GraphError


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

    @staticmethod
    def _validate_capacity(capacity: int) -> None:
        if type(capacity) is not int or not CAPACITY_MIN <= capacity <= CAPACITY_MAX:
            raise GraphError(
                f"Capacidad inválida {capacity!r}: debe ser un entero "
                f"entre {CAPACITY_MIN} y {CAPACITY_MAX}."
            )

    def add_arc(self, u: str, v: str, capacity: int) -> None:
        """Registra u → v con su capacidad. Una ruta inválida produce GraphError."""
        for centro in (u, v):
            if centro not in self.vertices:
                raise GraphError(f"El vértice {centro!r} no existe.")
        if u == v:
            raise GraphError(f"La ruta {u} → {v} es un lazo.")
        if (u, v) in self.arcs:
            raise GraphError(f"La ruta {u} → {v} ya existe.")
        if (v, u) in self.arcs:
            raise GraphError(f"Ya existe la ruta inversa {v} → {u}.")
        self._validate_capacity(capacity)
        self.arcs[u, v] = capacity

    def disable_arc(self, u: str, v: str) -> None:
        """Elimina la ruta u → v y conserva sus centros. Si falta, lanza GraphError."""
        if (u, v) not in self.arcs:
            raise GraphError(f"La ruta {u} → {v} no existe.")
        del self.arcs[u, v]

    def set_capacity(self, u: str, v: str, capacity: int) -> None:
        """Actualiza u → v. Una ruta inexistente o capacidad inválida produce GraphError."""
        if (u, v) not in self.arcs:
            raise GraphError(f"La ruta {u} → {v} no existe.")
        self._validate_capacity(capacity)
        self.arcs[u, v] = capacity

    def isolated_vertices(self) -> list[str]:
        """Devuelve en orden alfabético los centros sin rutas de entrada ni de salida."""
        conectados = set()
        for origen, destino in self.arcs:
            conectados.add(origen)
            conectados.add(destino)
        return sorted(self.vertices - conectados)
