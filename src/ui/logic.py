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
