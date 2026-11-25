# Caso manual de distribución

Queremos saber cuántos paquetes pueden llegar desde O hasta T en una hora.
Las dos rutas pasan por C. Probamos enviar 3 paquetes por O → A → C → T y
2 por O → B → C → T.

| Arco | Capacidad (paquetes/h) | Flujo propuesto (paquetes/h) |
|---|---:|---:|
| O → A | 8 | 3 |
| O → B | 6 | 2 |
| A → C | 3 | 3 |
| B → C | 2 | 2 |
| C → T | 8 | 5 |

## Conservación del flujo

En cada centro intermedio debe salir la misma cantidad que entra.

- A recibe 3 desde O y envía 3 a C. Su balance es 3 − 3 = 0.
- B recibe 2 desde O y envía 2 a C. Su balance es 2 − 2 = 0.
- C recibe 3 + 2 y envía 5 a T. Su balance es 3 + 2 − 5 = 0.

Ninguna ruta supera su capacidad. O despacha 5 paquetes/h y T recibe los 5.

## Por qué 5 es el máximo

Separamos los centros en dos grupos, {O, A, B} y {C, T}. Para llegar a T
todo paquete debe cruzar por A → C o B → C. Juntas, esas rutas admiten
3 + 2 = 5 paquetes/h. Ese corte impone un límite de 5 y el flujo de la tabla
lo alcanza. Por lo tanto, el flujo es máximo y el corte es mínimo.

Al ejecutar el algoritmo sobre `build_manual_case()`, el valor esperado del
flujo máximo y la capacidad esperada del corte mínimo son ambos 5 paquetes/h.
