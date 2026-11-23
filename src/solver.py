"""Punto único por el que la interfaz pide los cálculos de flujo y corte."""

from src.core import CutResult, FlowResult
from src.graph import Graph

USE_REAL_SOLVER: bool = False


def run_solver(graph: Graph, s: str, t: str) -> FlowResult:
    """Devuelve el flujo máximo de s a t; vacío si USE_REAL_SOLVER es False.
    Con True delega en max_flow y propaga su GraphError. No modifica graph."""
    if not USE_REAL_SOLVER:
        return FlowResult(value=0, flow={})
    from src.flow import max_flow  # se importa aquí para usar flow.py solo cuando hace falta

    return max_flow(graph, s, t)


def run_cut(graph: Graph, result: FlowResult, s: str, t: str) -> CutResult:
    """Devuelve el corte mínimo a partir de result; vacío si USE_REAL_SOLVER es False.
    Con True delega en min_cut y propaga su GraphError. No modifica graph ni result."""
    if not USE_REAL_SOLVER:
        return CutResult(S=set(), T=set(), cut_arcs=[], capacity=0)
    from src.flow import min_cut

    return min_cut(graph, result, s, t)
