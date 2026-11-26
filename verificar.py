"""Reproduce en la terminal los casos del informe con el mismo cálculo que la interfaz."""

from src.examples import (
    SINK, SOURCE, build_figure1, build_main_network, build_manual_case,
    build_variant_1, build_variant_2,
)
from src.flow import validate_flow
from src.solver import run_cut, run_solver


def comprobar(nombre, red, esperado):
    """Calcula el flujo y el corte de O a T y los compara con el valor manual."""
    flujo = run_solver(red, SOURCE, SINK)
    corte = run_cut(red, flujo, SOURCE, SINK)
    errores = validate_flow(red, flujo, SOURCE, SINK)
    if errores:
        raise ValueError(", ".join(errores))
    if flujo.value != esperado or corte.capacity != esperado:
        raise ValueError(f"{nombre}: el flujo o el corte difiere de {esperado}")

    print(f"{nombre}: flujo {flujo.value}, corte {corte.capacity} paquetes/h")
    print("  S =", ", ".join(sorted(corte.S)), "| T =", ", ".join(sorted(corte.T)))
    for u, v in corte.cut_arcs:
        print(f"  {u} → {v}: capacidad {red.arcs[u, v]}")
    return flujo


if __name__ == "__main__":
    comprobar("Inicial", build_main_network(), 8)
    comprobar("Variante 1", build_variant_1(), 4)
    comprobar("Variante 2", build_variant_2(), 10)
    manual = build_manual_case()
    flujo_manual = comprobar("Caso manual", manual, 5)
    for arco, capacidad in manual.arcs.items():
        u, v = arco
        print(f"  {u} → {v}: {flujo_manual.flow[arco]}/{capacidad}")
    comprobar("Figura 1 de la pauta", build_figure1(), 14)
