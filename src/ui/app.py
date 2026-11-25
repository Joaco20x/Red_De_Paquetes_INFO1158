"""Ventana principal del simulador. Solo dibuja y lee controles; la lógica está en logic.py."""

import math
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from src.compare import compare_configurations, snapshot
from src.core import CutResult, FlowResult, GraphError
from src.examples import SINK, SOURCE, build_main_network
from src.graph import Graph
from src.solver import run_cut, run_solver
from src.ui.logic import (
    build_result_rows, check_cut_matches, compute_positions, format_arc,
    parse_arc, parse_capacity, validate_selection,
)

WINDOW_TITLE = "Simulador de red de distribución de paquetes"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 650
PANEL_WIDTH = 340               # ancho del panel lateral de controles
CANVAS_WIDTH = WINDOW_WIDTH - PANEL_WIDTH
CANVAS_HEIGHT = WINDOW_HEIGHT

VERTEX_RADIUS = 18              # radio de cada círculo de vértice, en píxeles
LABEL_OFFSET = 10               # separación de la etiqueta respecto de la línea del arco

COLOR_SOURCE = "#43a047"        # verde: origen s
COLOR_SINK = "#e53935"          # rojo: destino t
COLOR_NEUTRAL = "#d9d9d9"       # gris claro: resto de los vértices
COLOR_ARC = "#424242"           # gris oscuro: arco normal
COLOR_ARC_HIGHLIGHT = "#d50000"  # rojo: arco del corte mínimo
ARC_WIDTH = 1.5
ARC_WIDTH_HIGHLIGHT = 3.5

COMPARISON_NAMES = ("Base", "Variante 1", "Variante 2")  # máximo tres configuraciones


def draw_vertices(canvas: tk.Canvas, positions: dict[str, tuple[int, int]],
                  s: str | None, t: str | None) -> None:
    """Dibuja cada vértice como un círculo con su nombre centrado.

    Entrada: canvas, posiciones de compute_positions y la selección de origen y destino.
    Regla: s va en verde y t en rojo; si s o t son None, todos usan el color neutro.
    Cada vértice lleva las etiquetas de canvas "vertex" y "vertex:<nombre>".
    """
    mark_terminals = s is not None and t is not None
    for name, (x, y) in positions.items():
        color = COLOR_NEUTRAL
        if mark_terminals and name == s:
            color = COLOR_SOURCE
        elif mark_terminals and name == t:
            color = COLOR_SINK
        tags = ("vertex", f"vertex:{name}")
        canvas.create_oval(x - VERTEX_RADIUS, y - VERTEX_RADIUS, x + VERTEX_RADIUS, y + VERTEX_RADIUS,
                           fill=color, outline="#616161", width=1.5, tags=tags)
        canvas.create_text(x, y, text=name, font=("Segoe UI", 10, "bold"), tags=tags)


def draw_arc(canvas: tk.Canvas, p1: tuple[int, int], p2: tuple[int, int],
             label: str, highlight: bool = False) -> tuple[int, int] | None:
    """Dibuja una flecha de p1 a p2 con label escrito junto a su punto medio.

    Entrada: centros de los vértices de origen y destino, texto de la etiqueta y
    si el arco va resaltado (rojo y más grueso) o no (gris oscuro).
    Salida: ids de canvas (línea, etiqueta), o None si p1 y p2 coinciden.
    Regla: la línea se acorta VERTEX_RADIUS en cada extremo para no entrar en los
    círculos, y la etiqueta se desplaza LABEL_OFFSET en perpendicular a la línea.
    """
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return None
    ux, uy = dx / length, dy / length
    start = (p1[0] + ux * VERTEX_RADIUS, p1[1] + uy * VERTEX_RADIUS)
    end = (p2[0] - ux * VERTEX_RADIUS, p2[1] - uy * VERTEX_RADIUS)
    line_id = canvas.create_line(
        *start, *end, arrow=tk.LAST, arrowshape=(10, 12, 4),
        fill=COLOR_ARC_HIGHLIGHT if highlight else COLOR_ARC,
        width=ARC_WIDTH_HIGHLIGHT if highlight else ARC_WIDTH,
    )
    mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    label_id = canvas.create_text(
        mid_x - uy * LABEL_OFFSET, mid_y + ux * LABEL_OFFSET, text=label,
        font=("Segoe UI", 9, "bold" if highlight else "normal"),
        fill=COLOR_ARC_HIGHLIGHT if highlight else "#1a237e",
    )
    return line_id, label_id


class App(tk.Tk):
    """Ventana con la red dibujada a la izquierda y los controles a la derecha."""

    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)

        self.graph: Graph = build_main_network()
        self.last_result: FlowResult | None = None
        self.last_cut: CutResult | None = None
        self.snapshots: list[dict] = []
        self._snapshot_terminals: list[tuple[str, str]] = []  # (s, t) usados por cada snapshot

        self.canvas = tk.Canvas(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
                                background="white", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.panel = ttk.Frame(self, width=PANEL_WIDTH, padding=8)
        self.panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.panel.pack_propagate(False)  # mantiene el ancho fijo aunque el contenido sea angosto

        notebook = ttk.Notebook(self.panel)
        notebook.pack(fill=tk.BOTH, expand=True)
        calc_tab = ttk.Frame(notebook, padding=8)
        edit_tab = ttk.Frame(notebook, padding=8)
        compare_tab = ttk.Frame(notebook, padding=8)
        notebook.add(calc_tab, text="Cálculo")
        notebook.add(edit_tab, text="Editar red")
        notebook.add(compare_tab, text="Comparar")

        self._build_calc_tab(calc_tab)
        self._build_edit_tab(edit_tab)
        self._build_compare_tab(compare_tab)

        if SOURCE in self.graph.vertices and SINK in self.graph.vertices:
            self.source_var.set(SOURCE)
            self.sink_var.set(SINK)
        self._refresh_choices()
        self._clear_results()
        self.redraw()

    # ---------- construcción del panel ----------

    def _build_calc_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(1, weight=1)
        self.source_var = tk.StringVar()
        self.sink_var = tk.StringVar()
        ttk.Label(tab, text="Origen (s)").grid(row=0, column=0, sticky="w", pady=2)
        self.source_combo = ttk.Combobox(tab, textvariable=self.source_var, state="readonly", width=12)
        self.source_combo.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(tab, text="Destino (t)").grid(row=1, column=0, sticky="w", pady=2)
        self.sink_combo = ttk.Combobox(tab, textvariable=self.sink_var, state="readonly", width=12)
        self.sink_combo.grid(row=1, column=1, sticky="ew", pady=2)
        for combo in (self.source_combo, self.sink_combo):
            combo.bind("<<ComboboxSelected>>", lambda _event: self.on_selection_changed())

        self.selection_message = ttk.Label(tab, foreground=COLOR_SINK, wraplength=290)
        self.selection_message.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 6))

        self.flow_button = ttk.Button(tab, text="Calcular flujo máximo", command=self.compute_flow)
        self.flow_button.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)
        self.cut_button = ttk.Button(tab, text="Calcular corte mínimo", command=self.compute_cut)
        self.cut_button.grid(row=4, column=0, columnspan=2, sticky="ew", pady=2)

        big_font = tkfont.nametofont("TkDefaultFont").copy()
        big_font.configure(size=13, weight="bold")
        self.flow_label = ttk.Label(tab, font=big_font)
        self.flow_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.check_label = ttk.Label(tab, wraplength=290)
        self.check_label.grid(row=6, column=0, columnspan=2, sticky="w")
        self.cut_sets_label = ttk.Label(tab, wraplength=290, justify=tk.LEFT)
        self.cut_sets_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(2, 6))

        table = ttk.Frame(tab)
        table.grid(row=8, column=0, columnspan=2, sticky="nsew")
        tab.rowconfigure(8, weight=1)
        self.result_tree = ttk.Treeview(table, columns=("arc", "flow", "capacity"),
                                        show="headings", height=10)
        for column, title, width in (("arc", "Arco", 120), ("flow", "Flujo", 70), ("capacity", "Capacidad", 80)):
            self.result_tree.heading(column, text=title)
            self.result_tree.column(column, width=width, anchor="center")
        scroll = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scroll.set)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_edit_tab(self, tab: ttk.Frame) -> None:
        disable_box = ttk.LabelFrame(tab, text="Desactivar ruta", padding=8)
        disable_box.pack(fill=tk.X, pady=(0, 8))
        self.disable_arc_var = tk.StringVar()
        self.disable_arc_combo = ttk.Combobox(disable_box, textvariable=self.disable_arc_var,
                                              state="readonly", width=14)
        self.disable_arc_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.disable_button = ttk.Button(disable_box, text="Desactivar", command=self.disable_selected_arc)
        self.disable_button.pack(side=tk.LEFT, padx=(6, 0))

        capacity_box = ttk.LabelFrame(tab, text="Modificar capacidad", padding=8)
        capacity_box.pack(fill=tk.X, pady=(0, 8))
        self.capacity_arc_var = tk.StringVar()
        self.capacity_var = tk.StringVar()
        self.capacity_arc_combo = ttk.Combobox(capacity_box, textvariable=self.capacity_arc_var,
                                               state="readonly", width=10)
        self.capacity_arc_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.capacity_arc_combo.bind("<<ComboboxSelected>>", lambda _event: self._show_current_capacity())
        ttk.Entry(capacity_box, textvariable=self.capacity_var, width=5).pack(side=tk.LEFT, padx=(6, 0))
        self.capacity_button = ttk.Button(capacity_box, text="Modificar", command=self.modify_capacity)
        self.capacity_button.pack(side=tk.LEFT, padx=(6, 0))

        add_box = ttk.LabelFrame(tab, text="Agregar conexión", padding=8)
        add_box.pack(fill=tk.X)
        self.new_origin_var = tk.StringVar()
        self.new_destination_var = tk.StringVar()
        self.new_capacity_var = tk.StringVar()
        ttk.Label(add_box, text="Desde").grid(row=0, column=0, sticky="w")
        self.new_origin_combo = ttk.Combobox(add_box, textvariable=self.new_origin_var,
                                             state="readonly", width=6)
        self.new_origin_combo.grid(row=0, column=1, padx=4)
        ttk.Label(add_box, text="Hasta").grid(row=0, column=2, sticky="w")
        self.new_destination_combo = ttk.Combobox(add_box, textvariable=self.new_destination_var,
                                                  state="readonly", width=6)
        self.new_destination_combo.grid(row=0, column=3, padx=4)
        ttk.Label(add_box, text="Capacidad").grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Entry(add_box, textvariable=self.new_capacity_var, width=6).grid(row=1, column=2, sticky="w",
                                                                             pady=(6, 0))
        ttk.Button(add_box, text="Agregar", command=self.add_connection).grid(row=1, column=3, pady=(6, 0))

    def _build_compare_tab(self, tab: ttk.Frame) -> None:
        ttk.Label(tab, wraplength=290, justify=tk.LEFT,
                  text="Guarda la red inicial como base y dos versiones modificadas como "
                       "variantes para comparar su flujo máximo y corte mínimo.").pack(fill=tk.X, pady=(0, 8))
        self.save_buttons = []
        labels = ("Guardar como base", "Guardar como variante 1", "Guardar como variante 2")
        for index, text in enumerate(labels):
            button = ttk.Button(tab, text=text, command=lambda i=index: self.save_configuration(i))
            button.pack(fill=tk.X, pady=2)
            self.save_buttons.append(button)
        ttk.Button(tab, text="Recalcular todo", command=self.recalculate_all).pack(fill=tk.X, pady=(8, 2))
        ttk.Button(tab, text="Vaciar comparación", command=self.clear_comparison).pack(fill=tk.X, pady=2)

        columns = (("name", "Configuración", 100), ("num_arcs", "Arcos", 50),
                   ("max_flow", "Flujo máx.", 70), ("min_cut_capacity", "Corte mín.", 70))
        self.compare_tree = ttk.Treeview(tab, columns=[c[0] for c in columns], show="headings", height=4)
        for column, title, width in columns:
            self.compare_tree.heading(column, text=title)
            self.compare_tree.column(column, width=width, anchor="center")
        self.compare_tree.pack(fill=tk.X, pady=(8, 0))

    # ---------- dibujo ----------

    def _selected_terminals(self) -> tuple[str | None, str | None]:
        return self.source_var.get() or None, self.sink_var.get() or None

    def redraw(self) -> None:
        """Borra el canvas y dibuja la red completa con el estado actual.

        Regla: primero los arcos y después los vértices, para que los círculos queden
        encima. La etiqueta es la capacidad, o flujo/capacidad si hay last_result, y los
        arcos de last_cut van resaltados. Cada arco lleva las etiquetas "arc" y "arc:u:v".
        """
        self.canvas.delete("all")
        positions = compute_positions(self.graph.vertices, CANVAS_WIDTH, CANVAS_HEIGHT)
        cut_arcs = set(self.last_cut.cut_arcs) if self.last_cut else set()
        for (u, v), capacity in sorted(self.graph.arcs.items()):
            if self.last_result is not None:
                label = f"{self.last_result.flow.get((u, v), 0)}/{capacity}"
            else:
                label = str(capacity)
            ids = draw_arc(self.canvas, positions[u], positions[v], label, highlight=(u, v) in cut_arcs)
            if ids:
                line_id, label_id = ids
                self.canvas.itemconfigure(line_id, tags=("arc", f"arc:{u}:{v}"))
                self.canvas.itemconfigure(label_id, tags=("arc_label", f"arc_label:{u}:{v}"))
        draw_vertices(self.canvas, positions, *self._selected_terminals())

    # ---------- selección y resultados ----------

    def _refresh_choices(self) -> None:
        """Actualiza las listas de vértices y arcos después de un cambio en el grafo."""
        vertices = sorted(self.graph.vertices)
        for combo, var in ((self.source_combo, self.source_var), (self.sink_combo, self.sink_var),
                           (self.new_origin_combo, self.new_origin_var),
                           (self.new_destination_combo, self.new_destination_var)):
            combo.configure(values=vertices)
            if var.get() not in self.graph.vertices:
                var.set("")

        arcs = sorted(format_arc(u, v) for u, v in self.graph.arcs)
        for combo, var in ((self.disable_arc_combo, self.disable_arc_var),
                           (self.capacity_arc_combo, self.capacity_arc_var)):
            combo.configure(values=arcs)
            if var.get() not in arcs:
                var.set("")
        state = "normal" if arcs else "disabled"
        self.disable_button.configure(state=state)
        self.capacity_button.configure(state=state)

    def _clear_results(self) -> None:
        """Olvida el flujo y el corte calculados, porque ya no corresponden a la red o la selección."""
        self.last_result = None
        self.last_cut = None
        self.flow_label.configure(text="Flujo máximo: —")
        self.check_label.configure(text="")
        self.cut_sets_label.configure(text="")
        self.result_tree.delete(*self.result_tree.get_children())
        self.cut_button.configure(state="disabled")

    def on_selection_changed(self) -> None:
        """Limpia los resultados, muestra el problema de la selección si lo hay y redibuja."""
        self._clear_results()
        s, t = self._selected_terminals()
        self.selection_message.configure(text=validate_selection(s, t, self.graph.vertices) or "")
        self.redraw()

    def _show_flow(self, result: FlowResult) -> None:
        self.last_result = result
        self.last_cut = None
        self.flow_label.configure(text=f"Flujo máximo: {result.value} paquetes/hora")
        self.check_label.configure(text="")
        self.cut_sets_label.configure(text="")
        self.result_tree.delete(*self.result_tree.get_children())
        for row in build_result_rows(self.graph, result):
            self.result_tree.insert("", tk.END, values=(row["arc"], row["flow"], row["capacity"]))
        self.cut_button.configure(state="normal")

    def _show_cut(self, cut: CutResult) -> None:
        self.last_cut = cut
        self.check_label.configure(text=check_cut_matches(self.last_result, cut))
        self.cut_sets_label.configure(
            text=f"S = {{{', '.join(sorted(cut.S))}}}\nT = {{{', '.join(sorted(cut.T))}}}")

    def _valid_terminals(self) -> tuple[str, str] | None:
        """Devuelve (s, t) si la selección es válida; si no, muestra el aviso y devuelve None."""
        s, t = self._selected_terminals()
        message = validate_selection(s, t, self.graph.vertices)
        if message:
            self.selection_message.configure(text=message)
            messagebox.showwarning("Selección incompleta", message, parent=self)
            return None
        return s, t

    def compute_flow(self) -> None:
        """Calcula el flujo máximo de s a t con run_solver y muestra el valor y la tabla.
        Con una selección inválida o un GraphError avisa y no cambia los resultados."""
        terminals = self._valid_terminals()
        if terminals is None:
            return
        try:
            result = run_solver(self.graph, *terminals)
        except GraphError as error:
            messagebox.showerror("No se pudo calcular el flujo", str(error), parent=self)
            return
        self._show_flow(result)
        self.redraw()

    def compute_cut(self) -> None:
        """Calcula el corte mínimo a partir de last_result y resalta sus arcos.
        Sin flujo calculado, o con un GraphError, avisa y no calcula."""
        if self.last_result is None:
            messagebox.showwarning("Falta el flujo", "Primero calcula el flujo máximo.", parent=self)
            return
        terminals = self._valid_terminals()
        if terminals is None:
            return
        try:
            cut = run_cut(self.graph, self.last_result, *terminals)
        except GraphError as error:
            messagebox.showerror("No se pudo calcular el corte", str(error), parent=self)
            return
        self._show_cut(cut)
        self.redraw()

    # ---------- edición de la red ----------

    def _after_graph_change(self) -> None:
        self._clear_results()
        self._refresh_choices()
        self.redraw()

    def _selected_arc(self, var: tk.StringVar) -> tuple[str, str] | None:
        try:
            return parse_arc(var.get())
        except GraphError as error:
            messagebox.showwarning("Ruta no seleccionada", str(error), parent=self)
            return None

    def disable_selected_arc(self) -> None:
        """Desactiva la ruta elegida con graph.disable_arc. Un GraphError se muestra y no cambia nada."""
        arc = self._selected_arc(self.disable_arc_var)
        if arc is None:
            return
        try:
            self.graph.disable_arc(*arc)
        except GraphError as error:
            messagebox.showerror("No se pudo desactivar la ruta", str(error), parent=self)
            return
        self._after_graph_change()

    def _show_current_capacity(self) -> None:
        try:
            self.capacity_var.set(str(self.graph.arcs[parse_arc(self.capacity_arc_var.get())]))
        except (GraphError, KeyError):
            self.capacity_var.set("")

    def modify_capacity(self) -> None:
        """Cambia la capacidad de la ruta elegida con parse_capacity y graph.set_capacity.
        Un GraphError de cualquiera de los dos se muestra y el grafo queda igual."""
        arc = self._selected_arc(self.capacity_arc_var)
        if arc is None:
            return
        try:
            capacity = parse_capacity(self.capacity_var.get())
            self.graph.set_capacity(*arc, capacity)
        except GraphError as error:
            messagebox.showerror("No se pudo modificar la capacidad", str(error), parent=self)
            return
        self._after_graph_change()
        self.capacity_arc_var.set(format_arc(*arc))
        self.capacity_var.set(str(capacity))

    def add_connection(self) -> None:
        """Agrega la ruta origen → destino con graph.add_arc.
        Los GraphError (lazo, ruta repetida o recíproca, capacidad inválida) se muestran tal cual."""
        u, v = self.new_origin_var.get(), self.new_destination_var.get()
        if not u or not v:
            messagebox.showwarning("Faltan centros", "Elige el centro de origen y el de destino.", parent=self)
            return
        try:
            capacity = parse_capacity(self.new_capacity_var.get())
            self.graph.add_arc(u, v, capacity)
        except GraphError as error:
            messagebox.showerror("No se pudo agregar la conexión", str(error), parent=self)
            return
        self._after_graph_change()
        self.new_capacity_var.set("")

    # ---------- comparación ----------

    def _refresh_comparison(self) -> None:
        self.compare_tree.delete(*self.compare_tree.get_children())
        for row in compare_configurations(self.snapshots):
            self.compare_tree.insert("", tk.END, values=(
                row["name"], row["num_arcs"], row["max_flow"], row["min_cut_capacity"]))

    def save_configuration(self, index: int) -> None:
        """Guarda la configuración COMPARISON_NAMES[index] para la tabla de comparación.

        Regla: la base es la red inicial sin modificar; las variantes son la red actual.
        Si faltan el flujo o el corte, los calcula antes de guardar. Como máximo hay tres
        configuraciones y cada nombre se guarda una sola vez; otro intento muestra aviso.
        """
        name = COMPARISON_NAMES[index]
        if any(saved["name"] == name for saved in self.snapshots):
            messagebox.showwarning("Configuración ya guardada",
                                   f"La configuración «{name}» ya está guardada. "
                                   "Usa «Vaciar comparación» para empezar de nuevo.", parent=self)
            return
        if len(self.snapshots) >= len(COMPARISON_NAMES):
            messagebox.showwarning("Comparación completa",
                                   f"Solo se pueden guardar {len(COMPARISON_NAMES)} configuraciones.", parent=self)
            return
        terminals = self._valid_terminals()
        if terminals is None:
            return
        graph = build_main_network() if index == 0 else self.graph
        try:
            if graph is self.graph and self.last_result is not None and self.last_cut is not None:
                result, cut = self.last_result, self.last_cut
            else:
                result = run_solver(graph, *terminals)
                cut = run_cut(graph, result, *terminals)
        except GraphError as error:
            messagebox.showerror("No se pudo guardar", str(error), parent=self)
            return
        self.snapshots.append(snapshot(name, graph, result, cut))
        self._snapshot_terminals.append(terminals)
        self._refresh_comparison()

    def recalculate_all(self) -> None:
        """Vuelve a calcular flujo y corte de cada configuración guardada y actualiza la tabla."""
        try:
            updated = []
            for saved, (s, t) in zip(self.snapshots, self._snapshot_terminals):
                result = run_solver(saved["graph"], s, t)
                cut = run_cut(saved["graph"], result, s, t)
                updated.append(snapshot(saved["name"], saved["graph"], result, cut))
        except GraphError as error:
            messagebox.showerror("No se pudo recalcular", str(error), parent=self)
            return
        self.snapshots = updated
        self._refresh_comparison()

    def clear_comparison(self) -> None:
        """Borra las configuraciones guardadas para volver a empezar la comparación."""
        self.snapshots = []
        self._snapshot_terminals = []
        self._refresh_comparison()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
