"""Ventana principal del simulador. Solo dibuja y lee controles; la lógica está en logic.py."""

import tkinter as tk
from tkinter import ttk

from src.core import CutResult, FlowResult
from src.examples import build_main_network
from src.graph import Graph

WINDOW_TITLE = "Simulador de red de distribución de paquetes"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 650
PANEL_WIDTH = 320               # ancho del panel lateral de controles
CANVAS_WIDTH = WINDOW_WIDTH - PANEL_WIDTH
CANVAS_HEIGHT = WINDOW_HEIGHT


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

        self.canvas = tk.Canvas(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
                                background="white", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.panel = ttk.Frame(self, width=PANEL_WIDTH, padding=12)
        self.panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.panel.pack_propagate(False)  # mantiene el ancho fijo aunque el contenido sea angosto


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
