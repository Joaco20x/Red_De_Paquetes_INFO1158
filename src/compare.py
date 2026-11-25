"""Copias de configuraciones de la red y tabla para compararlas."""

import copy

from src.core import CutResult, FlowResult
from src.graph import Graph


def snapshot(name: str, graph: Graph, result: FlowResult, cut: CutResult) -> dict:
    """Guarda una configuración para compararla después.

    Entrada: nombre de la configuración, su grafo y los resultados de flujo y corte.
    Salida: diccionario con las claves "name", "graph", "result" y "cut".
    Regla: el grafo, el resultado y el corte son copias profundas, así que modificar
    los originales después no cambia el snapshot. No lanza excepciones.
    """
    return {
        "name": name,
        "graph": copy.deepcopy(graph),
        "result": copy.deepcopy(result),
        "cut": copy.deepcopy(cut),
    }


def compare_configurations(snapshots: list[dict]) -> list[dict]:
    """Arma la tabla de comparación de las configuraciones guardadas.

    Entrada: lista de snapshots creados con snapshot().
    Salida: una fila por snapshot, en el mismo orden, con las claves "name",
    "num_arcs", "max_flow" y "min_cut_capacity". Lista vacía devuelve [].
    """
    return [
        {
            "name": saved["name"],
            "num_arcs": len(saved["graph"].arcs),
            "max_flow": saved["result"].value,
            "min_cut_capacity": saved["cut"].capacity,
        }
        for saved in snapshots
    ]
