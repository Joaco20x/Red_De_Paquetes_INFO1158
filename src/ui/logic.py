"""Lógica de la interfaz separada de tkinter, para poder probarla sin abrir ventanas."""

import math
import re

from src.core import CAPACITY_MAX, CAPACITY_MIN, CutResult, FlowResult, GraphError
from src.graph import Graph

_INTEGER = re.compile(r"-?\d+", re.ASCII)


def parse_capacity(text: str) -> int:
    """Convierte el texto de un Entry en una capacidad entre CAPACITY_MIN y CAPACITY_MAX.
    Lanza GraphError si no es un entero o si queda fuera del rango."""
    text = text.strip()
    if not _INTEGER.fullmatch(text):
        raise GraphError("La capacidad debe ser un número entero.")
    capacity = int(text)
    if not CAPACITY_MIN <= capacity <= CAPACITY_MAX:
        raise GraphError(f"La capacidad debe estar entre {CAPACITY_MIN} y {CAPACITY_MAX}.")
    return capacity


def validate_selection(s: str | None, t: str | None, vertices: set[str]) -> str | None:
    """Devuelve None si el origen y el destino son válidos, o un mensaje con el problema.
    Revisa en orden: falta origen, falta destino, vértice inexistente, origen igual a destino."""
    if not s:
        return "Falta seleccionar el centro de origen."
    if not t:
        return "Falta seleccionar el centro de destino."
    for vertex in (s, t):
        if vertex not in vertices:
            return f"El centro '{vertex}' no existe en la red."
    if s == t:
        return "El origen y el destino deben ser centros distintos."
    return None
