"""Pruebas de la lógica de interfaz y comparación, sin abrir ventanas."""

import sys
import types

import pytest

from conftest import make_graph
from src import solver
from src.core import CAPACITY_MAX, CAPACITY_MIN, CutResult, FlowResult, GraphError
from src.ui import logic

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


# ---------- I3-02 · parse_capacity ----------

@pytest.mark.parametrize("text, expected", [("7", 7), (" 7 ", 7), ("1", 1), ("12", 12)])
def test_parse_capacity_acepta_enteros_en_rango(text, expected):
    assert logic.parse_capacity(text) == expected


@pytest.mark.parametrize("text", ["0", "13", "-2"])
def test_parse_capacity_fuera_de_rango_menciona_el_rango(text):
    with pytest.raises(GraphError) as error:
        logic.parse_capacity(text)

    assert f"{CAPACITY_MIN} y {CAPACITY_MAX}" in str(error.value)


@pytest.mark.parametrize("text", ["3.5", "abc", "", "   "])
def test_parse_capacity_no_entero_pide_un_entero(text):
    with pytest.raises(GraphError, match="entero"):
        logic.parse_capacity(text)


# ---------- I3-03 · validate_selection ----------

VERTICES = {"A", "B", "C", "D"}


def test_validate_selection_valida_devuelve_none():
    assert logic.validate_selection("A", "D", VERTICES) is None


@pytest.mark.parametrize("s, t, fragment", [
    (None, "D", "origen"),
    ("", "D", "origen"),
    ("A", None, "destino"),
    ("A", "", "destino"),
    ("X", "D", "'X'"),
    ("A", "Z", "'Z'"),
    ("A", "A", "distintos"),
])
def test_validate_selection_cada_regla_tiene_su_mensaje(s, t, fragment):
    assert fragment in logic.validate_selection(s, t, VERTICES)


def test_validate_selection_sin_origen_ni_destino_reporta_el_origen():
    assert "origen" in logic.validate_selection(None, None, VERTICES)
