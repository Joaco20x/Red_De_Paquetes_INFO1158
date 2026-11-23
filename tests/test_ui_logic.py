"""Pruebas de la lógica de interfaz y comparación, sin abrir ventanas."""

import sys
import types

from conftest import make_graph
from src import solver
from src.core import CutResult, FlowResult

ARCS = {("A", "B"): 5, ("A", "C"): 3, ("B", "D"): 4, ("C", "D"): 6}


# ---------- I3-01 · solver.py ----------

def test_run_solver_con_bandera_falsa_devuelve_resultado_vacio(monkeypatch):
    monkeypatch.setattr(solver, "USE_REAL_SOLVER", False)
    graph = make_graph(ARCS)

    assert solver.run_solver(graph, "A", "D") == FlowResult(value=0, flow={})


def test_run_cut_con_bandera_falsa_devuelve_corte_vacio(monkeypatch):
    monkeypatch.setattr(solver, "USE_REAL_SOLVER", False)
    graph = make_graph(ARCS)

    cut = solver.run_cut(graph, FlowResult(0, {}), "A", "D")

    assert cut == CutResult(S=set(), T=set(), cut_arcs=[], capacity=0)


def test_solver_no_modifica_el_grafo(monkeypatch):
    monkeypatch.setattr(solver, "USE_REAL_SOLVER", False)
    graph = make_graph(ARCS)

    result = solver.run_solver(graph, "A", "D")
    solver.run_cut(graph, result, "A", "D")

    assert graph.arcs == ARCS
    assert graph.vertices == {"A", "B", "C", "D"}


def test_solver_con_bandera_verdadera_delega_en_flow(monkeypatch):
    expected_flow = FlowResult(value=9, flow={})
    expected_cut = CutResult(S={"A"}, T={"B", "C", "D"}, cut_arcs=[], capacity=9)
    calls = []

    def fake_max_flow(graph, s, t):
        calls.append(("max_flow", s, t))
        return expected_flow

    def fake_min_cut(graph, result, s, t):
        calls.append(("min_cut", s, t))
        return expected_cut

    fake_flow = types.ModuleType("src.flow")
    fake_flow.max_flow = fake_max_flow
    fake_flow.min_cut = fake_min_cut
    monkeypatch.setitem(sys.modules, "src.flow", fake_flow)
    monkeypatch.setattr(solver, "USE_REAL_SOLVER", True)
    graph = make_graph(ARCS)

    assert solver.run_solver(graph, "A", "D") is expected_flow
    assert solver.run_cut(graph, expected_flow, "A", "D") is expected_cut
    assert calls == [("max_flow", "A", "D"), ("min_cut", "A", "D")]
