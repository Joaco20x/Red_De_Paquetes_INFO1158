"""Redes de distribución para comparar escenarios y comprobar resultados."""

from src.graph import Graph

SOURCE = "O"
SINK = "T"


def _build_network(centros, rutas) -> Graph:
    """Construye una red nueva a partir de centros y ternas (origen, destino, capacidad)."""
    red = Graph()
    for centro in centros:
        red.add_vertex(centro)
    for origen, destino, capacidad in rutas:
        red.add_arc(origen, destino, capacidad)
    return red


def build_main_network() -> Graph:
    """Devuelve la red inicial de diez centros y quince rutas dirigidas."""
    # Las dos cadenas cubren todos los centros. Las cinco conexiones adicionales
    # van hacia la siguiente etapa, sin duplicar ni invertir ninguna ruta.
    rutas = [
        ("O", "A", 6), ("A", "C", 6), ("C", "E", 6), ("E", "G", 6), ("G", "T", 4),
        ("O", "B", 5), ("B", "D", 5), ("D", "F", 5), ("F", "H", 5), ("H", "T", 4),
        ("A", "D", 2), ("B", "C", 2), ("C", "F", 3), ("D", "E", 3), ("E", "H", 2),
    ]
    # Flujo máximo esperado: 8. Cada cadena admite 4 y a T solo entran 4 + 4.
    return _build_network(("O", "A", "B", "C", "D", "E", "F", "G", "H", "T"), rutas)


def build_variant_1() -> Graph:
    """Devuelve la red principal con una de las dos llegadas a T bloqueada."""
    red = build_main_network()
    # Cerrar G → T deja a H → T como única entrada, de 4 paquetes por hora.
    red.disable_arc("G", "T")
    return red


def build_variant_2() -> Graph:
    """Devuelve una red nueva que amplía la capacidad de la llegada desde G."""
    red = build_main_network()
    # Toda la cadena superior admite 6; ampliar su último tramo libera 2 paquetes/h.
    red.set_capacity("G", "T", 6)
    return red


def build_manual_case() -> Graph:
    """Devuelve la red de cinco centros resuelta en docs/caso_manual.md."""
    rutas = [
        ("O", "A", 8), ("O", "B", 6),
        ("A", "C", 3), ("B", "C", 2), ("C", "T", 8),
    ]
    return _build_network(("O", "A", "B", "C", "T"), rutas)


def build_figure1() -> Graph:
    """Devuelve el ejemplo de seis centros de la issue I1-09."""
    # Es un ejemplo ilustrativo de seis vértices. El flujo máximo esperado es 14.
    rutas = [
        ("O", "A", 8), ("O", "B", 6),
        ("A", "C", 5), ("A", "D", 3), ("B", "D", 6),
        ("C", "T", 5), ("D", "T", 9),
    ]
    return _build_network(("O", "A", "B", "C", "D", "T"), rutas)
