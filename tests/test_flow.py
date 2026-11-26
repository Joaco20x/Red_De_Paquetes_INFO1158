"""Pruebas unitarias del núcleo algorítmico de ``src/flow.py`` (I2-13).

Regla de independencia: cada fixture construye su propio ``Graph`` asignando
directamente ``vertices`` y ``arcs``. Ningún test importa ``src/examples.py``.

Los valores esperados de los fixtures están calculados a mano y documentados
en sus comentarios, no se obtienen ejecutando el propio algoritmo.
"""

from pathlib import Path
import sys

import pytest

# ``src/flow.py`` usa imports planos (``import core``, ``from cola import ...``),
# por lo que el directorio ``src`` debe estar en sys.path para poder importarlo.
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import core  # noqa: E402
import flow  # noqa: E402


# ---------------------------------------------------------------------------
# Utilidades y fixtures
# ---------------------------------------------------------------------------


def make_graph(arcs: dict[tuple[str, str], int], extra_vertices=()) -> flow.Graph:
    """Crea un Graph con los arcos dados y sus extremos como vértices.

    Se asignan los atributos directamente para no depender de ``examples.py``
    ni de los métodos de construcción del integrante 1.
    """
    vertices = {v for arc in arcs for v in arc} | set(extra_vertices)
    return flow.Graph(vertices=vertices, arcs=dict(arcs))


@pytest.fixture
def small_graph() -> flow.Graph:
    """Red de 4 vértices con dos caminos que comparten un arco intermedio.

    Arcos: s→a (2), s→b (2), b→a (2), a→t (3).

    Cálculo a mano:
      - Por s→a→t se envían min(2, 3) = 2 unidades.
      - Quedan s→b = 2 y b→a = 2, pero a→t solo tiene 3 - 2 = 1 unidad
        libre, así que por s→b→a→t se envía 1 unidad más.
      - Flujo máximo = 2 + 1 = 3.

    La suma de capacidades que salen de s es 2 + 2 = 4, pero el máximo es 3
    porque los dos caminos comparten el arco a→t.
    Corte mínimo: S = {s, a, b}, T = {t}, arco a→t, capacidad 3.
    """
    return make_graph(
        {
            ("s", "a"): 2,
            ("s", "b"): 2,
            ("b", "a"): 2,
            ("a", "t"): 3,
        }
    )


@pytest.fixture
def figure1_graph() -> flow.Graph:
    """Red de la Figura 1 con las capacidades del issue I1-09.

    Arcos: O→A (8), O→B (6), A→C (5), A→D (3), B→D (6), C→T (5), D→T (9).

    Cálculo a mano:
      - O→A→C→T: min(8, 5, 5) = 5.
      - O→A→D→T: quedan 8 - 5 = 3 en O→A; min(3, 3, 9) = 3.
      - O→B→D→T: min(6, 6, 9 - 3) = 6.
      - Flujo máximo = 5 + 3 + 6 = 14, igual a la capacidad total que sale
        de O (8 + 6 = 14).

    Corte mínimo esperado: {C→T, D→T}, capacidad 5 + 9 = 14.
    """
    return make_graph(
        {
            ("O", "A"): 8,
            ("O", "B"): 6,
            ("A", "C"): 5,
            ("A", "D"): 3,
            ("B", "D"): 6,
            ("C", "T"): 5,
            ("D", "T"): 9,
        }
    )


@pytest.fixture
def no_path_graph() -> flow.Graph:
    """Red sin camino de s a t.

    Arcos: s→a (3) y b→t (2). No existe una secuencia de arcos que una s con t.
    Cálculo a mano: el flujo máximo es 0 y todos los flujos quedan en 0.
    """
    return make_graph({("s", "a"): 3, ("b", "t"): 2})


@pytest.fixture
def reverse_graph() -> flow.Graph:
    """Red donde la solución greedy inicial no es óptima y hace falta un inverso.

    Arcos: s→d (1), s→a (5), d→b (3), d→c (4), a→b (4), b→t (2), c→t (3).

    Cálculo a mano:
      - Una elección greedy envía s→d→b→t (1 unidad) y luego s→a→b→t
        (1 unidad). Con eso b→t queda saturado y el valor es 2.
      - Para llegar al máximo hay que cancelar parte del flujo d→b usando el
        arco residual inverso b→d: el camino
        s→a→b→d→c→t permite enviar 1 unidad más, dejando d→b en 0 y
        habilitando d→c→t.
      - Flujo máximo = 3: b→t recibe 2 y c→t recibe 1.
    """
    return make_graph(
        {
            ("s", "d"): 1,
            ("s", "a"): 5,
            ("d", "b"): 3,
            ("d", "c"): 4,
            ("a", "b"): 4,
            ("b", "t"): 2,
            ("c", "t"): 3,
        }
    )


# ---------------------------------------------------------------------------
# I2-03: build_residual
# ---------------------------------------------------------------------------


def test_build_residual_con_flujo_vacio(small_graph):
    """Con flujo vacío la residual coincide con las capacidades originales."""
    residual = flow.build_residual(small_graph, {})

    assert residual == {
        ("s", "a"): 2,
        ("s", "b"): 2,
        ("b", "a"): 2,
        ("a", "t"): 3,
    }


def test_build_residual_incluye_inverso_y_omite_saturado(small_graph):
    """Un arco saturado desaparece y su inverso aparece con el flujo enviado."""
    residual = flow.build_residual(small_graph, {("s", "a"): 2, ("a", "t"): 1})

    assert ("s", "a") not in residual  # f == c, no queda capacidad directa
    assert residual[("a", "s")] == 2  # inverso de s→a
    assert residual[("a", "t")] == 2  # 3 - 1
    assert residual[("t", "a")] == 1  # inverso de a→t
    assert all(capacidad > 0 for capacidad in residual.values())


# ---------------------------------------------------------------------------
# I2-04: bfs_augmenting_path
# ---------------------------------------------------------------------------


def test_bfs_devuelve_camino_mas_corto(small_graph):
    """Entre s→a→t (2 arcos) y s→b→a→t (3 arcos), BFS devuelve el de 2."""
    residual = flow.build_residual(small_graph, {})

    assert flow.bfs_augmenting_path(residual, "s", "t") == [
        ("s", "a"),
        ("a", "t"),
    ]


def test_bfs_camino_consecutivo_y_residual_positivo(small_graph):
    """Los arcos del camino son consecutivos y existen con capacidad positiva."""
    residual = flow.build_residual(small_graph, {})
    camino = flow.bfs_augmenting_path(residual, "s", "t")

    assert camino is not None
    assert all(arco in residual and residual[arco] > 0 for arco in camino)
    assert all(camino[i][1] == camino[i + 1][0] for i in range(len(camino) - 1))


def test_bfs_sin_camino_devuelve_none(no_path_graph):
    """Si t no es alcanzable, el resultado es None."""
    residual = flow.build_residual(no_path_graph, {})

    assert flow.bfs_augmenting_path(residual, "s", "t") is None


# ---------------------------------------------------------------------------
# I2-05: bottleneck
# ---------------------------------------------------------------------------


def test_bottleneck_devuelve_el_minimo():
    """Con capacidades residuales 5, 2 y 9, el cuello de botella es 2."""
    residual = {("s", "a"): 5, ("a", "b"): 2, ("b", "t"): 9}

    assert flow.bottleneck(residual, [("s", "a"), ("a", "b"), ("b", "t")]) == 2


def test_bottleneck_camino_de_un_arco():
    """Con un solo arco de capacidad 7, el resultado es 7."""
    assert flow.bottleneck({("s", "t"): 7}, [("s", "t")]) == 7


def test_bottleneck_camino_vacio_lanza_graph_error():
    """Un camino vacío no tiene cuello de botella: debe lanzar GraphError."""
    with pytest.raises(core.GraphError):
        flow.bottleneck({}, [])


def test_bottleneck_arco_ausente_lanza_graph_error():
    """Un arco que no está en la residual también es un error de dominio."""
    with pytest.raises(core.GraphError):
        flow.bottleneck({("s", "a"): 1}, [("a", "t")])


# ---------------------------------------------------------------------------
# I2-06: augment
# ---------------------------------------------------------------------------


def test_augment_arcos_directos(small_graph):
    """Un camino solo con arcos directos suma delta en cada arco."""
    flujo = {arco: 0 for arco in small_graph.arcs}

    flow.augment(small_graph, flujo, [("s", "a"), ("a", "t")], 2)

    assert flujo[("s", "a")] == 2
    assert flujo[("a", "t")] == 2
    assert flujo[("s", "b")] == 0
    assert flujo[("b", "a")] == 0


def test_augment_usa_arco_inverso(reverse_graph):
    """Un arco residual inverso resta flujo al arco original (cancelación)."""
    # Flujo greedy inicial: s→d→b→t y s→a→b→t, 1 unidad por cada camino.
    flujo = {arco: 0 for arco in reverse_graph.arcs}
    flujo[("s", "d")] = 1
    flujo[("d", "b")] = 1
    flujo[("b", "t")] = 2
    flujo[("s", "a")] = 1
    flujo[("a", "b")] = 1

    # El arco (b, d) es inverso del original (d, b).
    camino = [("s", "a"), ("a", "b"), ("b", "d"), ("d", "c"), ("c", "t")]
    flow.augment(reverse_graph, flujo, camino, 1)

    assert flujo[("d", "b")] == 0  # se canceló el flujo por el inverso
    assert flujo[("s", "a")] == 2
    assert flujo[("a", "b")] == 2
    assert flujo[("d", "c")] == 1
    assert flujo[("c", "t")] == 1
    assert flujo[("b", "t")] == 2  # no cambia


def test_augment_arco_inexistente_lanza_graph_error(small_graph):
    """Un arco que no es directo ni inverso no puede aumentarse."""
    with pytest.raises(core.GraphError):
        flow.augment(small_graph, {}, [("x", "y")], 1)


# ---------------------------------------------------------------------------
# I2-07: edmonds_karp
# ---------------------------------------------------------------------------


def test_edmonds_karp_red_pequena(small_graph):
    """El flujo máximo de small_graph es 3 (cálculo a mano en el fixture)."""
    resultado = flow.edmonds_karp(small_graph, "s", "t")

    assert resultado.value == 3
    assert resultado.flow == {
        ("s", "a"): 2,
        ("s", "b"): 1,
        ("b", "a"): 1,
        ("a", "t"): 3,
    }


def test_edmonds_karp_figura1(figure1_graph):
    """El flujo máximo de la Figura 1 es 14 (cálculo a mano en el fixture)."""
    resultado = flow.edmonds_karp(figure1_graph, "O", "T")

    assert resultado.value == 14
    assert resultado.flow == {
        ("O", "A"): 8,
        ("O", "B"): 6,
        ("A", "C"): 5,
        ("A", "D"): 3,
        ("B", "D"): 6,
        ("C", "T"): 5,
        ("D", "T"): 9,
    }


def test_edmonds_karp_sin_camino(no_path_graph):
    """Sin camino de s a t el valor es 0 y todos los flujos quedan en 0."""
    resultado = flow.edmonds_karp(no_path_graph, "s", "t")

    assert resultado.value == 0
    assert all(valor == 0 for valor in resultado.flow.values())


def test_edmonds_karp_un_solo_arco():
    """Un único arco s→t de capacidad 4 devuelve valor 4."""
    graph = make_graph({("s", "t"): 4})

    resultado = flow.edmonds_karp(graph, "s", "t")

    assert resultado.value == 4
    assert resultado.flow == {("s", "t"): 4}


@pytest.mark.parametrize("s, t", [("s", "s"), ("x", "t"), ("s", "x")])
def test_edmonds_karp_entrada_invalida(small_graph, s, t):
    """s == t o un vértice inexistente deben lanzar GraphError."""
    with pytest.raises(core.GraphError):
        flow.edmonds_karp(small_graph, s, t)


# ---------------------------------------------------------------------------
# I2-08: max_flow
# ---------------------------------------------------------------------------


def test_max_flow_delega_en_edmonds_karp(small_graph):
    """Para una entrada válida, max_flow devuelve lo mismo que edmonds_karp."""
    assert flow.max_flow(small_graph, "s", "t") == flow.edmonds_karp(
        small_graph, "s", "t"
    )


def test_max_flow_sin_camino(no_path_graph):
    """La función pública también devuelve 0 cuando no hay camino."""
    assert flow.max_flow(no_path_graph, "s", "t").value == 0


def test_max_flow_grafo_invalido_lanza_graph_error():
    """max_flow exige que el primer argumento sea un Graph."""
    with pytest.raises(core.GraphError):
        flow.max_flow("esto no es un grafo", "s", "t")


@pytest.mark.parametrize("s, t", [("s", "s"), ("x", "t"), ("s", "x")])
def test_max_flow_vertices_invalidos(small_graph, s, t):
    """max_flow valida s y t antes de delegar."""
    with pytest.raises(core.GraphError):
        flow.max_flow(small_graph, s, t)


# ---------------------------------------------------------------------------
# I2-09: validate_flow
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture_name, s, t",
    [
        ("small_graph", "s", "t"),
        ("figure1_graph", "O", "T"),
        ("no_path_graph", "s", "t"),
    ],
)
def test_validate_flow_acepta_max_flow(request, fixture_name, s, t):
    """validate_flow acepta el flujo de max_flow en las tres redes de prueba."""
    graph = request.getfixturevalue(fixture_name)
    resultado = flow.max_flow(graph, s, t)

    assert flow.validate_flow(graph, resultado, s, t) == []


def test_validate_flow_detecta_capacidad_excedida(figure1_graph):
    """Un flujo mayor que la capacidad produce un mensaje que nombra el arco."""
    resultado = flow.max_flow(figure1_graph, "O", "T")
    manipulado = flow.FlowResult(
        value=resultado.value,
        flow=dict(resultado.flow),
    )
    manipulado.flow[("O", "A")] = 99

    errores = flow.validate_flow(figure1_graph, manipulado, "O", "T")

    assert errores
    assert any("O" in error and "A" in error for error in errores)


def test_validate_flow_detecta_flujo_negativo(small_graph):
    """Un flujo negativo viola la regla 0 <= f <= c."""
    manipulado = flow.FlowResult(
        value=0,
        flow={arco: 0 for arco in small_graph.arcs},
    )
    manipulado.flow[("s", "a")] = -1

    errores = flow.validate_flow(small_graph, manipulado, "s", "t")

    assert any("negativo" in error for error in errores)


def test_validate_flow_detecta_conservacion_rota(small_graph):
    """Quitar el flujo b→a rompe la conservación en el vértice b."""
    resultado = flow.max_flow(small_graph, "s", "t")
    manipulado = flow.FlowResult(
        value=resultado.value,
        flow=dict(resultado.flow),
    )
    manipulado.flow[("b", "a")] = 0

    errores = flow.validate_flow(small_graph, manipulado, "s", "t")

    assert any("conservación" in error and "b" in error for error in errores)


def test_validate_flow_detecta_valor_incorrecto(small_graph):
    """El valor declarado debe coincidir con el flujo neto que sale de s."""
    resultado = flow.max_flow(small_graph, "s", "t")
    manipulado = flow.FlowResult(
        value=resultado.value + 1,
        flow=dict(resultado.flow),
    )

    errores = flow.validate_flow(small_graph, manipulado, "s", "t")

    assert any("valor" in error for error in errores)


# ---------------------------------------------------------------------------
# I2-10: reachable_from_source
# ---------------------------------------------------------------------------


def test_reachable_flujo_vacio(small_graph):
    """Con flujo vacío se alcanzan todos los vértices de small_graph."""
    residual = flow.build_residual(small_graph, {})

    assert flow.reachable_from_source(residual, "s") == {"s", "a", "b", "t"}


def test_reachable_tras_flujo_maximo(small_graph):
    """Con el flujo máximo, t deja de ser alcanzable desde s."""
    resultado = flow.max_flow(small_graph, "s", "t")
    residual = flow.build_residual(small_graph, resultado.flow)

    alcanzables = flow.reachable_from_source(residual, "s")

    assert alcanzables == {"s", "a", "b"}
    assert "t" not in alcanzables


def test_reachable_sin_camino(no_path_graph):
    """Solo se alcanzan los vértices conectados por arcos residuales."""
    residual = flow.build_residual(no_path_graph, {})

    assert flow.reachable_from_source(residual, "s") == {"s", "a"}


def test_reachable_vertice_aislado():
    """El vértice s siempre pertenece al conjunto, aunque no tenga arcos."""
    assert flow.reachable_from_source({("a", "b"): 1}, "s") == {"s"}


# ---------------------------------------------------------------------------
# I2-11: min_cut
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture_name, s, t",
    [
        ("small_graph", "s", "t"),
        ("figure1_graph", "O", "T"),
        ("no_path_graph", "s", "t"),
    ],
)
def test_min_cut_capacidad_igual_flujo_maximo(request, fixture_name, s, t):
    """En las tres redes, la capacidad del corte mínimo es el flujo máximo."""
    graph = request.getfixturevalue(fixture_name)
    resultado = flow.max_flow(graph, s, t)

    corte = flow.min_cut(graph, resultado, s, t)

    assert corte.capacity == resultado.value
    assert corte.S & corte.T == set()
    assert corte.S | corte.T == set(graph.vertices)
    assert s in corte.S
    assert t in corte.T
    assert all(u in corte.S and v in corte.T for u, v in corte.cut_arcs)
    assert corte.capacity == sum(graph.arcs[arco] for arco in corte.cut_arcs)


def test_min_cut_red_pequena(small_graph):
    """El corte de small_graph es S={s,a,b}, T={t}, con el arco a→t."""
    resultado = flow.max_flow(small_graph, "s", "t")

    corte = flow.min_cut(small_graph, resultado, "s", "t")

    assert corte.S == {"s", "a", "b"}
    assert corte.T == {"t"}
    assert corte.cut_arcs == [("a", "t")]
    assert corte.capacity == 3


def test_min_cut_figura1_corte_esperado(figure1_graph):
    """La Figura 1 tiene un corte mínimo {C→T, D→T} de capacidad 14."""
    resultado = flow.max_flow(figure1_graph, "O", "T")

    corte = flow.min_cut(figure1_graph, resultado, "O", "T")

    assert corte.capacity == 14

    # Comprobación independiente del corte {C→T, D→T}: S={O,A,B,C,D}, T={T}.
    S = {"O", "A", "B", "C", "D"}
    T = {"T"}
    arcos_del_corte = [
        arco for arco in figure1_graph.arcs if arco[0] in S and arco[1] in T
    ]
    assert set(arcos_del_corte) == {("C", "T"), ("D", "T")}
    assert sum(figure1_graph.arcs[arco] for arco in arcos_del_corte) == 14


def test_min_cut_sin_camino(no_path_graph):
    """Sin camino de s a t, el corte mínimo tiene capacidad 0."""
    resultado = flow.max_flow(no_path_graph, "s", "t")

    corte = flow.min_cut(no_path_graph, resultado, "s", "t")

    assert corte.S == {"s", "a"}
    assert corte.T == {"b", "t"}
    assert corte.cut_arcs == []
    assert corte.capacity == 0


def test_min_cut_detecta_que_el_flujo_no_es_maximo(small_graph):
    """Si result no es máximo, la igualdad capacity == result.value falla."""
    # Flujo factible pero no máximo: solo se enviaron 2 unidades por s→a→t.
    flujo_parcial = {
        ("s", "a"): 2,
        ("s", "b"): 0,
        ("b", "a"): 0,
        ("a", "t"): 2,
    }
    resultado_parcial = flow.FlowResult(value=2, flow=flujo_parcial)

    corte = flow.min_cut(small_graph, resultado_parcial, "s", "t")

    assert corte.capacity != resultado_parcial.value
