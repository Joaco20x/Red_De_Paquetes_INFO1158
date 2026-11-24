import pytest

from src.core import GraphError
from src.examples import (
    SINK, SOURCE, build_figure1, build_main_network, build_manual_case,
    build_variant_1, build_variant_2,
)
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
    assert build_main_network().validate_initial() == []


def test_red_principal_admite_dos_caminos():
    assert build_main_network().has_two_distinct_paths(SOURCE, SINK)


def test_variante_1_quita_solo_la_llegada_desde_g():
    original = build_main_network()
    esperadas = original.arcs.copy()
    del esperadas["G", "T"]
    assert build_variant_1().arcs == esperadas
    assert ("G", "T") in original.arcs


def test_variante_2_amplia_solo_la_llegada_desde_g():
    original = build_main_network()
    esperadas = original.arcs.copy()
    esperadas["G", "T"] = 6
    assert build_variant_2().arcs == esperadas
    assert original.arcs["G", "T"] == 4


def test_caso_manual_coincide_con_las_capacidades_del_calculo():
    red = build_manual_case()
    assert red.vertices == {"O", "A", "B", "C", "T"}
    assert red.arcs == {
        ("O", "A"): 8, ("O", "B"): 6, ("A", "C"): 3,
        ("B", "C"): 2, ("C", "T"): 8,
    }


def test_figura_1_tiene_seis_centros_y_siete_rutas():
    red = build_figure1()
    assert red.vertices == {"O", "A", "B", "C", "D", "T"}
    assert len(red.arcs) == 7


def red_con_tamano(centros, rutas):
    """Primero arma una cadena; luego agrega atajos hacia adelante."""
    red = Graph()
    nombres = [str(i) for i in range(centros)]
    for nombre in nombres:
        red.add_vertex(nombre)
    for distancia in range(1, centros):
        for inicio in range(centros - distancia):
            if len(red.arcs) == rutas:
                return red
            red.add_arc(nombres[inicio], nombres[inicio + distancia], 1)
    return red


@pytest.mark.parametrize(("centros", "rutas"), [(10, 15), (12, 20)])
def test_validacion_acepta_los_limites_inclusivos(centros, rutas):
    assert red_con_tamano(centros, rutas).validate_initial() == []


@pytest.mark.parametrize(("centros", "rutas", "regla"), [
    (9, 15, "vértices"), (13, 15, "vértices"),
    (10, 14, "arcos"), (10, 21, "arcos"),
])
def test_validacion_identifica_la_unica_regla_incumplida(centros, rutas, regla):
    errores = red_con_tamano(centros, rutas).validate_initial()
    assert len(errores) == 1
    assert regla in errores[0]


def test_validacion_nombra_el_centro_aislado():
    red = red_con_tamano(10, 15)
    red.add_vertex("X")
    assert red.validate_initial() == ["Vértices aislados: X"]


def test_una_vuelta_por_un_ciclo_no_cuenta_como_segundo_camino():
    red = Graph()
    for centro in ("O", "A", "B", "C", "T"):
        red.add_vertex(centro)
    for u, v in [("O", "A"), ("A", "B"), ("B", "C"), ("C", "A"), ("A", "T")]:
        red.add_arc(u, v, 1)
    assert not red.has_two_distinct_paths("O", "T")
