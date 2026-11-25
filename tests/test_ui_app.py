"""Pruebas de la ventana. Crean la App oculta y se saltan si no hay pantalla disponible."""

import math

import pytest

from src.core import CutResult, FlowResult, GraphError
from src.examples import SINK, SOURCE, build_main_network

tk = pytest.importorskip("tkinter")
app_module = pytest.importorskip("src.ui.app")


@pytest.fixture
def messages(monkeypatch):
    """Reemplaza los messagebox para que no bloqueen y registra (tipo, mensaje)."""
    shown = []
    for kind in ("showwarning", "showerror", "showinfo"):
        monkeypatch.setattr(app_module.messagebox, kind,
                            lambda title, message, _kind=kind, **_: shown.append((_kind, message)))
    return shown


@pytest.fixture
def app(messages):
    # En Windows, crear muchas ventanas seguidas a veces falla al leer los archivos de
    # Tcl/Tk (por ejemplo, por el antivirus). Se reintenta antes de saltar la prueba.
    for attempt in range(5):
        try:
            window = app_module.App()
            break
        except tk.TclError as error:
            last_error = error
    else:
        pytest.skip(f"No se pudo abrir tkinter: {last_error}")
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture
def canvas(app):
    app.canvas.delete("all")  # parte vacío, sin la red que dibuja la App al abrir
    return app.canvas


def fake_result(graph, value=8):
    """Flujo simulado: cada arco lleva 1, salvo que la capacidad sea menor."""
    return FlowResult(value=value, flow={arc: 1 for arc in graph.arcs})


def use_fake_solver(monkeypatch, value=8, cut_arcs=(("G", "T"), ("H", "T")), cut_capacity=8):
    calls = []

    def run_solver(graph, s, t):
        calls.append(("solver", s, t))
        return fake_result(graph, value)

    def run_cut(graph, result, s, t):
        calls.append(("cut", s, t))
        T = {t, *(v for _, v in cut_arcs)}
        return CutResult(S=graph.vertices - T, T=T, cut_arcs=list(cut_arcs), capacity=cut_capacity)

    monkeypatch.setattr(app_module, "run_solver", run_solver)
    monkeypatch.setattr(app_module, "run_cut", run_cut)
    return calls


def select(app, s, t):
    app.source_var.set(s)
    app.sink_var.set(t)
    app.on_selection_changed()


def arc_lines(app):
    return {tag for item in app.canvas.find_withtag("arc")
            for tag in app.canvas.gettags(item) if tag.startswith("arc:")}


def arc_label(app, u, v):
    return app.canvas.itemcget(app.canvas.find_withtag(f"arc_label:{u}:{v}")[0], "text")


def tree_arcs(app):
    return [app.result_tree.item(row, "values")[0] for row in app.result_tree.get_children()]


# ---------- I3-07 · App ----------

def test_app_empieza_con_la_red_principal_y_sin_resultados(app):
    assert isinstance(app.graph, app_module.Graph)
    assert app.graph.vertices
    assert app.last_result is None
    assert app.last_cut is None
    assert app.title() == app_module.WINDOW_TITLE


# ---------- I3-08 · draw_vertices ----------

POSITIONS = {"A": (100, 100), "B": (300, 100), "C": (200, 300)}


def vertex_colors(canvas):
    colors = {}
    for item in canvas.find_withtag("vertex"):
        if canvas.type(item) == "oval":
            name = next(tag for tag in canvas.gettags(item) if tag.startswith("vertex:"))[7:]
            assert name not in colors  # cada vértice aparece una sola vez
            colors[name] = canvas.itemcget(item, "fill")
    return colors


def test_draw_vertices_dibuja_cada_vertice_una_vez_con_s_y_t_destacados(canvas):
    app_module.draw_vertices(canvas, POSITIONS, "A", "C")

    colors = vertex_colors(canvas)
    assert set(colors) == set(POSITIONS)
    assert colors["A"] == app_module.COLOR_SOURCE
    assert colors["C"] == app_module.COLOR_SINK
    assert colors["B"] == app_module.COLOR_NEUTRAL
    texts = [canvas.itemcget(i, "text") for i in canvas.find_withtag("vertex") if canvas.type(i) == "text"]
    assert sorted(texts) == ["A", "B", "C"]


@pytest.mark.parametrize("s, t", [(None, "C"), ("A", None), (None, None)])
def test_draw_vertices_sin_s_o_t_usa_color_neutro(canvas, s, t):
    app_module.draw_vertices(canvas, POSITIONS, s, t)

    assert set(vertex_colors(canvas).values()) == {app_module.COLOR_NEUTRAL}


# ---------- I3-09 · draw_arc ----------

def test_draw_arc_apunta_a_p2_y_se_acorta_por_el_radio(canvas):
    line_id, _ = app_module.draw_arc(canvas, (100, 100), (300, 100), "5")

    x1, y1, x2, y2 = canvas.coords(line_id)
    radius = app_module.VERTEX_RADIUS
    assert (x1, y1, x2, y2) == pytest.approx((100 + radius, 100, 300 - radius, 100))
    assert canvas.itemcget(line_id, "arrow") == "last"


def test_draw_arc_etiqueta_desplazada_del_punto_medio_y_fuera_de_los_circulos(canvas):
    p1, p2 = (100, 100), (220, 260)
    _, label_id = app_module.draw_arc(canvas, p1, p2, "3/6")

    x, y = canvas.coords(label_id)
    assert math.dist((x, y), (160, 180)) == pytest.approx(app_module.LABEL_OFFSET)
    assert canvas.itemcget(label_id, "text") == "3/6"
    for center in (p1, p2):
        assert math.dist((x, y), center) > app_module.VERTEX_RADIUS


def test_draw_arc_resaltado_usa_otro_color_y_es_mas_grueso(canvas):
    normal, _ = app_module.draw_arc(canvas, (0, 0), (100, 100), "1")
    highlighted, _ = app_module.draw_arc(canvas, (0, 0), (100, 100), "1", highlight=True)

    assert canvas.itemcget(normal, "fill") != canvas.itemcget(highlighted, "fill")
    assert float(canvas.itemcget(highlighted, "width")) > float(canvas.itemcget(normal, "width"))


# ---------- I3-10 · redraw ----------

def test_redraw_dibuja_cada_arco_una_vez_con_su_capacidad(app):
    app.redraw()
    app.redraw()  # no deben quedar dibujos anteriores

    assert arc_lines(app) == {f"arc:{u}:{v}" for u, v in app.graph.arcs}
    assert len(app.canvas.find_withtag("arc")) == len(app.graph.arcs)
    for (u, v), capacity in app.graph.arcs.items():
        assert arc_label(app, u, v) == str(capacity)


def test_redraw_con_resultado_muestra_flujo_y_resalta_el_corte(app):
    app.last_result = FlowResult(8, {("G", "T"): 4})
    app.last_cut = CutResult(set(), set(), [("G", "T"), ("H", "T")], 8)
    app.redraw()

    assert arc_label(app, "G", "T") == "4/4"
    assert arc_label(app, "O", "A") == "0/6"
    highlighted = {tag for item in app.canvas.find_withtag("arc")
                   if app.canvas.itemcget(item, "fill") == app_module.COLOR_ARC_HIGHLIGHT
                   for tag in app.canvas.gettags(item) if tag.startswith("arc:")}
    assert highlighted == {"arc:G:T", "arc:H:T"}


# ---------- I3-11 · selectores ----------

def test_selectores_tienen_exactamente_los_vertices(app):
    expected = sorted(app.graph.vertices)

    assert list(app.source_combo.cget("values")) == expected
    assert list(app.sink_combo.cget("values")) == expected
    assert (app.source_var.get(), app.sink_var.get()) == (SOURCE, SINK)


def test_cambiar_la_seleccion_limpia_los_resultados(app, monkeypatch):
    use_fake_solver(monkeypatch)
    app.compute_flow()
    app.compute_cut()

    select(app, "A", SINK)

    assert app.last_result is None and app.last_cut is None
    assert str(app.cut_button.cget("state")) == "disabled"


def test_mismo_origen_y_destino_muestra_el_mensaje_de_validacion(app):
    select(app, "A", "A")

    assert "distintos" in app.selection_message.cget("text")


# ---------- I3-12 · calcular flujo ----------

def test_calcular_flujo_sin_seleccion_avisa_y_no_calcula(app, monkeypatch, messages):
    calls = use_fake_solver(monkeypatch)
    select(app, "", SINK)

    app.compute_flow()

    assert calls == []
    assert messages and "origen" in messages[0][1]
    assert app.last_result is None


def test_calcular_flujo_muestra_valor_y_una_fila_por_arco(app, monkeypatch):
    calls = use_fake_solver(monkeypatch, value=8)
    assert str(app.cut_button.cget("state")) == "disabled"

    app.compute_flow()

    assert calls == [("solver", SOURCE, SINK)]
    assert app.flow_label.cget("text") == "Flujo máximo: 8 paquetes/hora"
    assert len(app.result_tree.get_children()) == len(app.graph.arcs)
    assert str(app.cut_button.cget("state")) == "normal"
    assert arc_label(app, "O", "A") == "1/6"


def test_calcular_flujo_muestra_el_graph_error(app, monkeypatch, messages):
    def failing(graph, s, t):
        raise GraphError("No existe el vértice.")

    monkeypatch.setattr(app_module, "run_solver", failing)
    app.compute_flow()

    assert messages == [("showerror", "No existe el vértice.")]
    assert app.last_result is None


# ---------- I3-13 · calcular corte ----------

def test_calcular_corte_sin_flujo_avisa_y_no_calcula(app, monkeypatch, messages):
    calls = use_fake_solver(monkeypatch)

    app.compute_cut()

    assert calls == []
    assert messages and messages[0][0] == "showwarning"
    assert app.last_cut is None


def test_calcular_corte_resalta_sus_arcos_y_comprueba_el_valor(app, monkeypatch):
    use_fake_solver(monkeypatch, value=8, cut_capacity=8)
    app.compute_flow()

    app.compute_cut()

    assert app.last_cut.cut_arcs == [("G", "T"), ("H", "T")]
    assert "coinciden" in app.check_label.cget("text")
    assert "S = {" in app.cut_sets_label.cget("text")
    highlighted = [item for item in app.canvas.find_withtag("arc")
                   if app.canvas.itemcget(item, "fill") == app_module.COLOR_ARC_HIGHLIGHT]
    assert {next(t for t in app.canvas.gettags(i) if t.startswith("arc:")) for i in highlighted} == {
        "arc:G:T", "arc:H:T"}


# ---------- I3-14 · desactivar ruta ----------

def test_desactivar_ruta_la_quita_del_canvas_y_de_la_tabla(app, monkeypatch):
    use_fake_solver(monkeypatch)
    app.disable_arc_var.set("G → T")

    app.disable_selected_arc()
    app.compute_flow()

    assert ("G", "T") not in app.graph.arcs
    assert "arc:G:T" not in arc_lines(app)
    assert "G → T" not in tree_arcs(app)
    assert "G → T" not in app.disable_arc_combo.cget("values")
    assert app.canvas.find_withtag("vertex:G")  # el vértice sigue dibujado


def test_desactivar_ruta_muestra_el_graph_error_y_sigue_funcionando(app, monkeypatch, messages):
    def failing(u, v):
        raise GraphError("La ruta no existe.")

    monkeypatch.setattr(app.graph, "disable_arc", failing)
    app.disable_arc_var.set("O → A")
    arcs_before = dict(app.graph.arcs)

    app.disable_selected_arc()

    assert messages == [("showerror", "La ruta no existe.")]
    assert app.graph.arcs == arcs_before


def test_sin_arcos_activos_el_boton_desactivar_queda_deshabilitado(app):
    for u, v in list(app.graph.arcs):
        app.disable_arc_var.set(f"{u} → {v}")
        app.disable_selected_arc()

    assert app.graph.arcs == {}
    assert str(app.disable_button.cget("state")) == "disabled"
    assert len(app.canvas.find_withtag("vertex")) == 2 * len(app.graph.vertices)


# ---------- I3-15 · modificar capacidad ----------

@pytest.mark.parametrize("text", ["abc", "3.5", "0", "13"])
def test_modificar_capacidad_invalida_muestra_error_y_no_cambia(app, messages, text):
    app.capacity_arc_var.set("G → T")
    app.capacity_var.set(text)

    app.modify_capacity()

    assert app.graph.arcs[("G", "T")] == 4
    assert len(messages) == 1 and messages[0][0] == "showerror"


def test_modificar_capacidad_valida_actualiza_el_canvas(app):
    app.capacity_arc_var.set("G → T")
    app.capacity_var.set(" 6 ")

    app.modify_capacity()

    assert app.graph.arcs[("G", "T")] == 6
    assert arc_label(app, "G", "T") == "6"
    assert app.capacity_var.get() == "6"


# ---------- I3-16 · agregar conexión ----------

@pytest.mark.parametrize("u, v", [("A", "A"), ("O", "A"), ("A", "O")])
def test_agregar_conexion_invalida_muestra_el_mensaje_de_add_arc(app, messages, u, v):
    app.new_origin_var.set(u)
    app.new_destination_var.set(v)
    app.new_capacity_var.set("3")
    with pytest.raises(GraphError) as expected:
        build_main_network().add_arc(u, v, 3)

    app.add_connection()

    assert messages == [("showerror", str(expected.value))]


def test_agregar_conexion_valida_aparece_en_canvas_y_combobox(app):
    app.new_origin_var.set("A")
    app.new_destination_var.set("T")
    app.new_capacity_var.set("5")

    app.add_connection()

    assert app.graph.arcs[("A", "T")] == 5
    assert "arc:A:T" in arc_lines(app)
    assert "A → T" in app.disable_arc_combo.cget("values")


# ---------- I3-19 · comparación ----------

def compare_rows(app):
    return [app.compare_tree.item(row, "values") for row in app.compare_tree.get_children()]


def test_se_guardan_tres_configuraciones_y_una_cuarta_se_rechaza(app, monkeypatch, messages):
    use_fake_solver(monkeypatch)
    for index in range(3):
        app.save_configuration(index)

    app.save_configuration(1)

    assert [row[0] for row in compare_rows(app)] == ["Base", "Variante 1", "Variante 2"]
    assert len(messages) == 1 and messages[0][0] == "showwarning"


def test_base_es_la_red_inicial_y_no_cambia_al_editar(app, monkeypatch):
    use_fake_solver(monkeypatch)
    app.disable_arc_var.set("G → T")
    app.disable_selected_arc()

    app.save_configuration(0)
    app.save_configuration(1)
    app.disable_arc_var.set("H → T")
    app.disable_selected_arc()

    assert [row[:2] for row in compare_rows(app)] == [("Base", "15"), ("Variante 1", "14")]


def test_recalcular_todo_actualiza_los_valores(app, monkeypatch):
    use_fake_solver(monkeypatch, value=0, cut_capacity=0)
    app.save_configuration(0)
    assert compare_rows(app)[0][2:] == ("0", "0")

    use_fake_solver(monkeypatch, value=8, cut_capacity=8)
    app.recalculate_all()

    assert compare_rows(app)[0][2:] == ("8", "8")
