import pytest

from src.core import GraphError
from src.graph import Graph


def test_grafo_nuevo_tiene_vertices_y_arcos_vacios():
    grafo = Graph()

    assert grafo.vertices == set()
    assert grafo.arcs == {}


def test_cada_grafo_tiene_sus_propios_vertices_y_arcos():
    primero = Graph()
    segundo = Graph()

    primero.vertices.update({"A", "B"})
    primero.arcs[("A", "B")] = 5

    assert segundo.vertices == set()
    assert segundo.arcs == {}


def test_agregar_un_centro_repetido_conserva_los_otros_centros():
    grafo = Graph()
    for centro in ("A", "B", "A"):
        grafo.add_vertex(centro)
    assert grafo.vertices == {"A", "B"}


@pytest.mark.parametrize("nombre", ["", "   "])
def test_rechaza_nombre_vacio(nombre):
    with pytest.raises(GraphError, match="vacío"):
        Graph().add_vertex(nombre)


@pytest.fixture
def red():
    grafo = Graph()
    for centro in ("A", "B", "C"):
        grafo.add_vertex(centro)
    grafo.add_arc("A", "B", 5)
    return grafo


@pytest.mark.parametrize("capacidad", [1, 12])
def test_agregar_ruta_valida(red, capacidad):
    red.add_arc("A", "C", capacidad)
    assert red.arcs == {("A", "B"): 5, ("A", "C"): capacidad}


@pytest.mark.parametrize(("u", "v", "mensaje"), [
    ("X", "A", "X"), ("A", "X", "X"), ("A", "A", "lazo"),
    ("A", "B", "ya existe"), ("B", "A", "inversa"),
])
def test_rechaza_ruta_invalida_sin_cambiar_la_red(red, u, v, mensaje):
    with pytest.raises(GraphError, match=mensaje):
        red.add_arc(u, v, 2)
    assert red.arcs == {("A", "B"): 5}


@pytest.mark.parametrize("capacidad", [0, 13, -4, 3.5, "5", True])
def test_rechaza_capacidad_invalida_al_agregar(red, capacidad):
    with pytest.raises(GraphError, match="Capacidad"):
        red.add_arc("B", "C", capacidad)
    assert ("B", "C") not in red.arcs


def test_desactivar_ruta_conserva_centros_y_permite_reponerla(red):
    red.disable_arc("A", "B")
    assert red.arcs == {}
    assert red.vertices == {"A", "B", "C"}
    red.add_arc("A", "B", 7)
    assert red.arcs["A", "B"] == 7


def test_desactivar_ruta_inexistente(red):
    with pytest.raises(GraphError):
        red.disable_arc("B", "A")


def test_cambia_solo_la_capacidad_elegida(red):
    red.add_arc("B", "C", 4)
    red.set_capacity("A", "B", 9)
    assert red.arcs == {("A", "B"): 9, ("B", "C"): 4}


@pytest.mark.parametrize("capacidad", [0, 13])
def test_cambio_invalido_conserva_capacidad_anterior(red, capacidad):
    with pytest.raises(GraphError):
        red.set_capacity("A", "B", capacidad)
    assert red.arcs["A", "B"] == 5


def test_cambiar_capacidad_de_ruta_inexistente(red):
    with pytest.raises(GraphError):
        red.set_capacity("A", "C", 3)


def test_aislados_en_orden_alfabetico(red):
    red.add_vertex("Z")
    red.add_vertex("D")
    assert red.isolated_vertices() == ["C", "D", "Z"]


def test_red_vacia_no_tiene_aislados():
    assert Graph().isolated_vertices() == []


def test_validacion_informa_todos_los_problemas(red):
    mensajes = red.validate_initial()
    assert len(mensajes) == 3
    assert any("vértices" in m for m in mensajes)
    assert any("arcos" in m for m in mensajes)
    assert any("aislados: C" in m for m in mensajes)


def test_un_camino_directo_es_insuficiente(red):
    assert not red.has_two_distinct_paths("A", "B")


def test_no_hay_camino_en_sentido_inverso(red):
    assert not red.has_two_distinct_paths("B", "A")


def test_dos_caminos_sin_intermedios_comunes(red):
    red.add_arc("A", "C", 1)
    red.add_arc("C", "B", 1)
    assert red.has_two_distinct_paths("A", "B")


def test_dos_caminos_pueden_compartir_un_tramo(red):
    red.add_vertex("T")
    red.add_arc("B", "T", 1)
    red.add_arc("B", "C", 1)
    red.add_arc("C", "T", 1)
    assert red.has_two_distinct_paths("A", "T")


@pytest.mark.parametrize(("s", "t"), [("A", "A"), ("X", "B"), ("A", "X")])
def test_extremos_invalidos_al_buscar_caminos(red, s, t):
    with pytest.raises(GraphError):
        red.has_two_distinct_paths(s, t)


def test_red_principal_cumple_las_reglas_iniciales():
    from src.examples import build_main_network
    assert build_main_network().validate_initial() == []


def test_red_principal_admite_dos_caminos():
    from src.examples import SOURCE, SINK, build_main_network
    assert build_main_network().has_two_distinct_paths(SOURCE, SINK)


def test_variante_1_quita_solo_la_llegada_desde_g():
    from src.examples import build_main_network, build_variant_1
    original = build_main_network()
    esperadas = original.arcs.copy()
    del esperadas["G", "T"]
    assert build_variant_1().arcs == esperadas
    assert ("G", "T") in original.arcs


def test_variante_2_amplia_solo_la_llegada_desde_g():
    from src.examples import build_main_network, build_variant_2
    original = build_main_network()
    esperadas = original.arcs.copy()
    esperadas["G", "T"] = 6
    assert build_variant_2().arcs == esperadas
    assert original.arcs["G", "T"] == 4
