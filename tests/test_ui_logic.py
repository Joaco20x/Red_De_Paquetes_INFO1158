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


# ---------- I3-04 · compute_positions ----------

TWELVE = {f"V{i:02d}" for i in range(12)}


@pytest.mark.parametrize("width, height", [(800, 600), (600, 800), (300, 300)])
def test_compute_positions_quedan_dentro_del_canvas_con_margen(width, height):
    positions = logic.compute_positions(TWELVE, width, height)

    assert set(positions) == TWELVE
    for x, y in positions.values():
        assert 20 <= x <= width - 20
        assert 20 <= y <= height - 20


def test_compute_positions_es_determinista():
    assert logic.compute_positions(TWELVE, 800, 600) == logic.compute_positions(set(TWELVE), 800, 600)


def test_compute_positions_no_repite_coordenadas():
    positions = logic.compute_positions(TWELVE, 800, 600)

    assert len(set(positions.values())) == len(TWELVE)


def test_compute_positions_un_vertice_va_al_centro():
    assert logic.compute_positions({"A"}, 800, 600) == {"A": (400, 300)}


def test_compute_positions_conjunto_vacio():
    assert logic.compute_positions(set(), 800, 600) == {}


# ---------- I3-05 · build_result_rows ----------

def test_build_result_rows_una_fila_por_arco_en_orden_alfabetico():
    graph = make_graph({("C", "D"): 6, ("A", "C"): 3, ("B", "D"): 4, ("A", "B"): 5})
    result = FlowResult(value=7, flow={("A", "B"): 4, ("A", "C"): 3, ("B", "D"): 4, ("C", "D"): 3})

    rows = logic.build_result_rows(graph, result)

    assert len(rows) == len(graph.arcs)
    assert [row["arc"] for row in rows] == ["A → B", "A → C", "B → D", "C → D"]
    assert rows[0] == {"arc": "A → B", "flow": 4, "capacity": 5}


def test_build_result_rows_arco_sin_flujo_muestra_cero():
    graph = make_graph(ARCS)

    rows = logic.build_result_rows(graph, FlowResult(value=0, flow={}))

    assert all(row["flow"] == 0 for row in rows)


def test_build_result_rows_ignora_arcos_desactivados():
    graph = make_graph(ARCS)
    result = FlowResult(value=7, flow={("A", "B"): 4, ("A", "C"): 3, ("B", "D"): 4, ("C", "D"): 3})
    del graph.arcs[("A", "C")]

    rows = logic.build_result_rows(graph, result)

    assert "A → C" not in [row["arc"] for row in rows]
    assert len(rows) == 3


# ---------- I3-06 · check_cut_matches ----------

def test_check_cut_matches_valores_iguales():
    cut = CutResult(S={"A"}, T={"B", "C", "D"}, cut_arcs=[("A", "B"), ("A", "C")], capacity=8)

    text = logic.check_cut_matches(FlowResult(value=8, flow={}), cut)

    assert "coincide" in text
    assert "8" in text


def test_check_cut_matches_valores_distintos():
    cut = CutResult(S={"A"}, T={"B"}, cut_arcs=[("A", "B")], capacity=9)

    text = logic.check_cut_matches(FlowResult(value=7, flow={}), cut)

    assert "discrepancia" in text
    assert "7" in text and "9" in text


def test_check_cut_matches_resultados_vacios():
    text = logic.check_cut_matches(FlowResult(0, {}), CutResult(set(), set(), [], 0))

    assert "coincide" in text
