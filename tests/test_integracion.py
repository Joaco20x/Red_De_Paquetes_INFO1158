"""Comprueba el cálculo que usa la interfaz al abrir el simulador."""

from src.examples import SINK, SOURCE, build_main_network
from src.solver import run_cut, run_solver


def test_red_inicial_con_la_configuracion_predeterminada():
    """La red inicial transporta 8 paquetes/h y su corte tiene capacidad 8."""
    red = build_main_network()
    flujo = run_solver(red, SOURCE, SINK)
    corte = run_cut(red, flujo, SOURCE, SINK)

    assert flujo.value == 8
    assert corte.capacity == flujo.value
    assert set(corte.cut_arcs) == {("G", "T"), ("H", "T")}
