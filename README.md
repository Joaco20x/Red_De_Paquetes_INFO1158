# CONTRATO.md · Simulador de red de distribución de paquetes (INFO1158)

Este documento fija los nombres, firmas, tipos y reglas que los tres integrantes usan para trabajar en paralelo. Cualquier cambio en este archivo se hace por Pull Request revisado por los tres integrantes.

---

## 1. Estructura del repositorio

````
proyecto/
├── CONTRATO.md
├── README.md
├── requirements.txt
├── pytest.ini
├── docs/
│   ├── comparacion_algoritmos.md     (integrante 2)
│   └── caso_manual.md                (integrante 1)
├── src/
│   ├── __init__.py
│   ├── graph.py                      (integrante 1)
│   ├── examples.py                   (integrante 1)
│   ├── flow.py                       (integrante 2)
│   ├── solver.py                     (integrante 3)
│   ├── compare.py                    (integrante 3)
│   └── ui/
│       ├── __init__.py
│       └── app.py                    (integrante 3)
└── tests/
    ├── conftest.py                   (compartido)
    ├── test_graph.py                 (integrante 1)
    ├── test_flow.py                  (integrante 2)
    └── test_ui_logic.py              (integrante 3)
````

**Propiedad de archivos:** cada integrante es dueño de sus archivos. Modificar un archivo ajeno requiere acuerdo explícito en el PR.

---

## 2. Tipos y constantes compartidas (`src/graph.py`)

````python
Arc = tuple[str, str]          # arco dirigido (origen, destino)
Flow = dict[Arc, int]          # flujo asignado a cada arco original

CAPACITY_MIN = 1               # capacidad mínima de una ruta (paquetes/hora)
CAPACITY_MAX = 12              # capacidad máxima de una ruta (paquetes/hora)
VERTICES_MIN = 10              # |V| mínimo en la configuración inicial
VERTICES_MAX = 12              # |V| máximo en la configuración inicial
ARCS_MIN = 15                  # |E| mínimo en la configuración inicial
ARCS_MAX = 20                  # |E| máximo en la configuración inicial
````

Los nombres de vértices son cadenas no vacías. Todos los integrantes usan estas constantes y no escriben los números del enunciado directamente.

---

## 3. Excepción (`src/graph.py`)

````python
class GraphError(ValueError):
    """Violación de una regla de la red: lazo, arco repetido, arco recíproco,
    capacidad fuera de rango, vértice inexistente, vértice aislado, etc."""
````

Toda regla del enunciado que se incumple se reporta con `GraphError`. No se usan otras excepciones para reglas de dominio.

---

## 4. Clase `Graph` (`src/graph.py`, integrante 1)

### Atributos

| Atributo | Tipo | Significado |
|---|---|---|
| `vertices` | `set[str]` | Conjunto V de centros logísticos |
| `arcs` | `dict[Arc, int]` | Conjunto E con su capacidad c(u, v) |

### Métodos

| Método | Firma | Lanza `GraphError` cuando |
|---|---|---|
| `add_vertex` | `add_vertex(self, name: str) -> None` | `name` es vacío o solo espacios. Si ya existe, no hace nada. |
| `add_arc` | `add_arc(self, u: str, v: str, capacity: int) -> None` | `u` o `v` no existe; `u == v`; `(u, v)` ya existe; `(v, u)` ya existe; `capacity` no es `int` o está fuera de `[CAPACITY_MIN, CAPACITY_MAX]`. Si lanza, `arcs` no cambia. |
| `disable_arc` | `disable_arc(self, u: str, v: str) -> None` | `(u, v)` no existe. Los vértices no se eliminan. |
| `set_capacity` | `set_capacity(self, u: str, v: str, capacity: int) -> None` | `(u, v)` no existe, o `capacity` no cumple la regla de `add_arc`. Si lanza, la capacidad anterior se mantiene. |
| `isolated_vertices` | `isolated_vertices(self) -> list[str]` | Nunca lanza. Devuelve los vértices sin arcos entrantes ni salientes, en orden alfabético. |
| `validate_initial` | `validate_initial(self) -> list[str]` | Nunca lanza. Devuelve un mensaje por cada regla incumplida: |V| fuera de `[VERTICES_MIN, VERTICES_MAX]`, |E| fuera de `[ARCS_MIN, ARCS_MAX]`, o vértices aislados. Lista vacía = cumple. |
| `has_two_distinct_paths` | `has_two_distinct_paths(self, s: str, t: str) -> bool` | `s` o `t` no existen, o `s == t`. Devuelve `True` si hay al menos dos caminos dirigidos simples y distintos de `s` a `t`. |

**Regla de `add_arc`:** los mensajes de error deben nombrar el problema concreto (qué vértice falta, qué arco ya existe, qué valor está fuera de rango).

---

## 5. Clases de resultado (`src/flow.py`, integrante 2)

````python
@dataclass
class FlowResult:
    value: int          # cantidad neta que sale de s
    flow: Flow          # flujo de cada arco original, incluidos los de flujo 0

@dataclass
class CutResult:
    S: set[str]                 # vértices del lado de s
    T: set[str]                 # vértices del lado de t
    cut_arcs: list[Arc]         # arcos (u, v) con u en S y v en T
    capacity: int               # suma de capacidades originales de cut_arcs
````

Las claves de `FlowResult.flow` son exactamente las claves de `Graph.arcs`, sin claves adicionales.

---

## 6. Funciones de flujo (`src/flow.py`, integrante 2)

| Función | Firma | Descripción breve | Lanza `GraphError` cuando |
|---|---|---|---|
| `build_residual` | `build_residual(graph: Graph, flow: Flow) -> dict[Arc, int]` | Red residual. Solo incluye arcos con capacidad > 0. | Nunca |
| `bfs_augmenting_path` | `bfs_augmenting_path(residual: dict[Arc, int], s: str, t: str) -> list[Arc] \| None` | Camino aumentante más corto por BFS, o `None`. | Nunca |
| `bottleneck` | `bottleneck(residual: dict[Arc, int], path: list[Arc]) -> int` | Mínimo de las capacidades residuales del camino. | `path` vacío |
| `augment` | `augment(graph: Graph, flow: Flow, path: list[Arc], delta: int) -> None` | Modifica `flow` en el lugar. Suma en arcos directos, resta en inversos. | Nunca |
| `edmonds_karp` | `edmonds_karp(graph: Graph, s: str, t: str) -> FlowResult` | Algoritmo completo. | `s` o `t` no existen, o `s == t` |
| `max_flow` | `max_flow(graph: Graph, s: str, t: str) -> FlowResult` | Función pública. Valida y delega en `edmonds_karp`. | Igual que `edmonds_karp` |
| `validate_flow` | `validate_flow(graph: Graph, result: FlowResult, s: str, t: str) -> list[str]` | Verifica capacidad, conservación y valor. Lista vacía = válido. | Nunca |
| `reachable_from_source` | `reachable_from_source(residual: dict[Arc, int], s: str) -> set[str]` | Vértices alcanzables desde `s` por arcos residuales. Incluye a `s`. | Nunca |
| `min_cut` | `min_cut(graph: Graph, result: FlowResult, s: str, t: str) -> CutResult` | Corte mínimo a partir del flujo máximo. | `s` o `t` no existen, o `s == t` |

**Regla de `validate_flow`:** es independiente de cómo se calculó el flujo. Debe poder verificar cualquier `FlowResult`, incluido uno construido a mano.

---

## 7. Configuraciones de ejemplo (`src/examples.py`, integrante 1)

````python
SOURCE: str   # origen s de la red principal; valor fijado por integrante 1 en I1-13
SINK: str     # destino t de la red principal; valor fijado por integrante 1 en I1-13

def build_figure1() -> Graph: ...        # red de la Figura 1 (6 vértices: O, A, B, C, D, T)
def build_main_network() -> Graph: ...   # red principal, cumple validate_initial()
def build_variant_1() -> Graph: ...      # primera modificación de la principal
def build_variant_2() -> Graph: ...      # segunda modificación de la principal
def build_manual_case() -> Graph: ...    # red de 4 a 6 vértices para cálculo manual
````

Cada función devuelve un `Graph` nuevo en cada llamada. No devuelve referencias a un objeto compartido.

---

## 8. Solver y comparación (integrante 3)

### `src/solver.py`

````python
USE_REAL_SOLVER: bool = False

def run_solver(graph: Graph, s: str, t: str) -> FlowResult: ...
def run_cut(graph: Graph, result: FlowResult, s: str, t: str) -> CutResult: ...
````

La interfaz llama únicamente a estas dos funciones, nunca directamente a `flow.py`. Con `USE_REAL_SOLVER = False`, devuelven resultados vacíos. Con `True`, delegan en `max_flow` y `min_cut`.

### `src/compare.py`

````python
def snapshot(name: str, graph: Graph, result: FlowResult, cut: CutResult) -> dict: ...
def compare_configurations(snapshots: list[dict]) -> list[dict]: ...
````

- `snapshot` guarda copias profundas de `vertices`, `arcs`, `result` y `cut`. Modificar el grafo original después no altera la copia.
- `snapshot` devuelve un `dict` con las claves `"name"`, `"graph"`, `"result"` y `"cut"`.
- `compare_configurations` devuelve una fila por snapshot con las claves `"name"`, `"num_arcs"`, `"max_flow"` y `"min_cut_capacity"`.

---

## 9. Fixtures compartidos (`tests/conftest.py`)

Construidos directamente con `Graph`, sin importar `examples.py`:

| Fixture | Contenido | Valor esperado |
|---|---|---|
| `figure1_graph` | Red de la Figura 1 | Flujo máximo 14; corte mínimo `{C→T, D→T}`, capacidad 14 |
| `small_graph` | Red de 4 vértices con caminos que comparten un arco intermedio | Se calcula a mano y se documenta en el fixture |
| `no_path_graph` | Red sin camino de `s` a `t` | Flujo máximo 0 |

Los valores esperados están en comentarios del fixture y se calculan a mano, no a partir del código.

---

## 10. Reglas de trabajo

1. **Firmas fijas.** Ningún nombre de función, método, atributo, clase o constante de este documento cambia sin PR aprobado por los tres integrantes.
2. **Stubs primero.** Antes de crear las ramas, `main` contiene todos los archivos con todas las firmas. Cada cuerpo es `raise NotImplementedError`. Al ejecutar `pytest`, los tests fallan con `NotImplementedError` y **nunca con `ImportError`**. Si aparece un `ImportError`, el contrato está incompleto y se corrige antes de seguir.
3. **Una rama por integrante:** `feature/modelo`, `feature/algoritmo`, `feature/interfaz`.
4. **Un Pull Request por issue o por bloque de issues,** hacia `main`. Cada PR debe pasar `pytest`.
5. **No modificar tests ajenos** para que pasen. Si un test está mal, se discute en el PR.
6. **Docstrings obligatorios** en cada función pública: entrada, salida, excepción y regla principal.
7. **Sin bibliotecas de flujo.** No se usan funciones de flujo ni de corte de `networkx` o similares. Solo se permiten las estructuras básicas de Python, `pytest` y `tkinter`.

---

## 11. Verificación de aceptación del contrato

- [ ] `pytest` ejecutado sobre el esqueleto de `main` no produce `ImportError`.
- [ ] Todas las firmas de este documento existen en su archivo correspondiente.
- [ ] Las constantes de la sección 2 coinciden exactamente con el enunciado.
- [ ] Los tres integrantes firman el documento (nombre y fecha).

**Firmas:**
- Integrante 1: ____________________ Fecha: ________
- Integrante 2: ____________________ Fecha: ________
- Integrante 3: ____________________ Fecha: ________
````
````

Nota: cambié la firma de `snapshot` respecto de lo que propuse antes (ahora recibe nombre, grafo, resultado y corte), porque así guarda todo lo que necesita la tabla de comparación. Los issues de integrante 3 deben actualizarse a esta firma.
