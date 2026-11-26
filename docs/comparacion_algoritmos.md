# Comparación de algoritmos de flujo máximo: Ford–Fulkerson y Edmonds–Karp

## Resumen

Este documento compara dos variantes del método de Ford–Fulkerson para resolver el problema de flujo máximo en una red dirigida con capacidades: la variante que busca el camino aumentante con búsqueda en profundidad (DFS) y la variante que lo busca con búsqueda en anchura (BFS), conocida como algoritmo de Edmonds–Karp. La comparación considera el funcionamiento, la complejidad, las garantías de terminación y el comportamiento esperado en la red de la Figura 1 del proyecto. A partir de esa comparación se justifica la elección de Edmonds–Karp para el simulador.

---

## 1. Ford–Fulkerson con búsqueda en profundidad

### 1.1. Funcionamiento

El método de Ford–Fulkerson parte de un flujo nulo y lo aumenta repetidamente. En cada iteración se construye la red residual, se busca un camino dirigido desde la fuente `s` hasta el sumidero `t` cuyos arcos tengan capacidad residual estrictamente positiva, se calcula el cuello de botella del camino —el mínimo de las capacidades residuales de sus arcos— y se envía esa cantidad de flujo. El proceso termina cuando no existe ningún camino aumentante en la red residual; en ese momento, por el teorema de flujo máximo–corte mínimo, el flujo obtenido es máximo (Ford y Fulkerson, 1956; Cormen et al., 2009, cap. 26).

En la variante con búsqueda en profundidad, el camino aumentante se obtiene recorriendo la red residual con una pila o recursión: se avanza por los arcos disponibles hasta encontrar `t` o hasta agotar las alternativas, y se retrocede cuando una rama no conduce al sumidero. El orden en que se exploran los vecinos depende de la representación concreta del grafo y de la implementación, por lo que distintos órdenes pueden producir distintos caminos aumentantes y distintas descomposiciones del flujo final, aunque el valor máximo sea el mismo.

Cada arco residual `(u, v)` representa la posibilidad de aumentar flujo en el arco original `(u, v)` hasta `c(u, v) - f(u, v)`, y cada arco inverso `(v, u)` representa la posibilidad de cancelar flujo ya enviado por `(u, v)` hasta `f(u, v)`. Esta red residual es la que permite reencauzar flujo y corregir decisiones previas.

### 1.2. Complejidad

Con capacidades enteras, cada aumento incrementa el valor del flujo en al menos una unidad. Por lo tanto, el número de aumentos está acotado por el valor del flujo máximo `|f*|`. Si la búsqueda en profundidad recorre la red en tiempo `O(E)`, el costo total es `O(E |f*|)` (Cormen et al., 2009, §26.2). Si `C` es la capacidad máxima de la red, se cumple `|f*| ≤ |E| C`, de modo que la cota se puede escribir como `O(E² C)` en el peor caso.

La cota anterior depende del valor del flujo y, por lo tanto, de las capacidades. En una red con capacidades grandes, Ford–Fulkerson con DFS puede necesitar muchas más iteraciones que en una red con la misma estructura pero capacidades pequeñas. Esa dependencia es la principal debilidad de la variante con DFS.

### 1.3. Terminación con capacidades enteras

Si todas las capacidades son enteras, el cuello de botella de cada camino aumentante es un entero positivo, porque es el mínimo de números enteros positivos. En consecuencia, el valor del flujo aumenta al menos en 1 en cada iteración y no puede superar la suma de las capacidades de los arcos que salen de `s`, que es finita. El algoritmo debe terminar después de un número finito de aumentos (Ford y Fulkerson, 1956; Cormen et al., 2009, cap. 26).

Esta propiedad es la que garantiza el funcionamiento correcto en la red de este proyecto, donde todas las capacidades son enteras y están acotadas por las constantes del contrato. El mismo argumento se extiende a capacidades racionales: multiplicando todas las capacidades por un denominador común se obtiene una red equivalente con capacidades enteras.

### 1.4. El caso de capacidades irracionales

La garantía anterior se pierde cuando las capacidades son irracionales. En ese caso, el cuello de botella puede ser una cantidad positiva arbitrariamente pequeña y el valor del flujo puede aumentar en una sucesión infinita de cantidades cada vez menores, sin alcanzar nunca el máximo. Se conocen redes de tamaño pequeño en las que Ford–Fulkerson, con una elección desfavorable de los caminos, no termina (Zwick, 1995). Cormen et al. (2009, cap. 26) también advierten que la terminación del método depende de que las capacidades sean enteras o, más generalmente, racionales.

Este comportamiento patológico no ocurre en la red del proyecto porque sus capacidades son enteras, pero es relevante para la comparación: la variante con DFS no ofrece una garantía de terminación independiente de la representación numérica de las capacidades.

---

## 2. Edmonds–Karp (Ford–Fulkerson con búsqueda en anchura)

### 2.1. Funcionamiento

Edmonds–Karp conserva la estructura general de Ford–Fulkerson —red residual, camino aumentante, cuello de botella y aumento— pero cambia la forma de elegir el camino aumentante: utiliza búsqueda en anchura (BFS) desde `s` en la red residual. La BFS explora primero todos los vértices a distancia 1, luego los de distancia 2, y así sucesivamente; por eso el camino que encuentra hasta `t` es un camino con el menor número de arcos entre todos los caminos aumentantes disponibles en ese momento (Edmonds y Karp, 1972).

El algoritmo repite el ciclo hasta que la BFS no alcanza `t`. En cada iteración se actualiza el flujo con la misma operación de aumento que en Ford–Fulkerson: se suma el cuello de botella en los arcos directos y se resta en los arcos inversos. El valor final se calcula como el flujo neto que sale de `s`.

### 2.2. Cota de iteraciones

La elección por BFS introduce una cota de iteraciones que no depende de las capacidades. Sea `δ(v)` la distancia en número de arcos desde `s` hasta `v` en la red residual. La BFS garantiza que `δ(t)` nunca disminuye a lo largo de las iteraciones y que, cuando un arco `(u, v)` se satura y deja de estar disponible, la distancia `δ(u)` debe haber aumentado al menos en 2 antes de que ese arco pueda volver a ser crítico. Como `δ(u)` está acotado por `V - 1`, cada arco puede volver a ser crítico `O(V)` veces. Con `E` arcos, el número total de aumentos es `O(VE)` (Edmonds y Karp, 1972; Cormen et al., 2009, §26.2).

Esta cota es independiente de las capacidades: no importa cuán grandes sean los valores numéricos, el número de aumentos queda acotado por una función polinómica de `V` y `E`. Esa es la diferencia esencial con la variante que usa DFS.

### 2.3. Complejidad

Cada búsqueda en anchura recorre la red residual en tiempo `O(E)`. Como hay `O(VE)` aumentos, el tiempo total de Edmonds–Karp es `O(VE²)` (Edmonds y Karp, 1972; Cormen et al., 2009, §26.2; Kleinberg y Tardos, 2006, cap. 7). Esta cota es polinómica y no depende del valor del flujo ni de la magnitud de las capacidades.

En comparación, Ford–Fulkerson con DFS tiene costo `O(E |f*|)`, que puede ser mucho mayor cuando `|f*|` es grande. La mejora de Edmonds–Karp no proviene de un cambio en la operación de aumento, sino exclusivamente de la regla de selección del camino aumentante.

### 2.4. Por qué la búsqueda en anchura da esa garantía

La garantía de Edmonds–Karp se apoya en que la BFS siempre elige un camino de longitud mínima en la red residual. Esa propiedad hace que las distancias desde `s` sean monótonas y que cada arco pueda saturarse y volver a aparecer solo un número acotado de veces. Con DFS no existe esa monotonía: el algoritmo puede elegir caminos largos y con cuellos de botella pequeños, y el número de aumentos puede depender de las capacidades y del orden de exploración. Por eso la cota `O(VE)` de Edmonds–Karp es una garantía estructural, mientras que la cota de Ford–Fulkerson con DFS es una cota en función del valor del flujo (Edmonds y Karp, 1972; Cormen et al., 2009, §26.2).

---

## 3. Tabla comparativa

| Criterio | Ford–Fulkerson con DFS | Edmonds–Karp (BFS) |
|---|---|---|
| Idea central | Aumenta por un camino cualquiera encontrado con búsqueda en profundidad. | Aumenta por el camino más corto en número de arcos, encontrado con búsqueda en anchura. |
| Complejidad temporal | `O(E |f*|)` con capacidades enteras; en el peor caso, `O(E² C)` si `C` es la capacidad máxima (Cormen et al., 2009, §26.2). | `O(VE²)` (Edmonds y Karp, 1972; Cormen et al., 2009, §26.2). |
| Número de aumentos | Hasta `|f*|`; depende de las capacidades. | `O(VE)`; independiente de las capacidades. |
| Garantía de terminación | Garantizada con capacidades enteras o racionales; no garantizada con capacidades irracionales (Zwick, 1995). | Garantizada para capacidades reales no negativas, gracias a la cota `O(VE)` de aumentos. |
| Facilidad de implementación | Alta: requiere una pila o recursión para la DFS. | Alta: requiere una cola para la BFS; reutiliza la misma construcción de red residual y la misma operación de aumento. |
| Comportamiento en esta red | Encuentra el flujo máximo 14 y un corte mínimo de capacidad 14. Con capacidades enteras, realiza como máximo 14 aumentos, pero la descomposición del flujo depende del orden de exploración. | Encuentra el flujo máximo 14 y un corte mínimo de capacidad 14. La cota asintótica es `O(VE)`; con estos valores, `V · E = 6 · 7 = 42` aumentos. Con capacidades enteras, en la práctica no supera los 14 aumentos. La elección por BFS hace el resultado reproducible. |

La red de la Figura 1 tiene 6 vértices (`O`, `A`, `B`, `C`, `D`, `T`) y 7 arcos con capacidades `O→A = 8`, `O→B = 6`, `A→C = 5`, `A→D = 3`, `B→D = 6`, `C→T = 5` y `D→T = 9`. Su flujo máximo es 14, igual a la capacidad total que sale de `O`, y el corte `{C→T, D→T}` también tiene capacidad 14. En esta red ambos algoritmos terminan y obtienen el mismo valor máximo; la diferencia práctica está en que Edmonds–Karp entrega una garantía polinómica independiente de las capacidades y un comportamiento determinista, mientras que Ford–Fulkerson con DFS puede producir distintas descomposiciones del flujo según el orden en que se exploren los arcos.

---

## 4. Justificación de la elección

Se elige Edmonds–Karp porque su cota de iteraciones `O(VE)` es independiente de las capacidades y del valor del flujo, a diferencia de Ford–Fulkerson con DFS, cuyo número de aumentos está acotado por `|f*|` y puede crecer con la magnitud de las capacidades; además, con capacidades irracionales la variante con DFS ni siquiera garantiza la terminación. En esta red las capacidades son enteras y pequeñas, por lo que ambos algoritmos terminan, pero Edmonds–Karp conserva la garantía polinómica `O(VE²)` aunque en la interfaz se modifiquen las capacidades, y su elección por BFS hace que los resultados sean reproducibles para las pruebas y para la comparación de configuraciones. La decisión no se basa en una preferencia de estilo: se basa en una propiedad concreta del algoritmo, la cota de aumentos independiente de las capacidades (Edmonds y Karp, 1972; Cormen et al., 2009, §26.2). Además, la implementación reutiliza las mismas funciones de red residual, cuello de botella y aumento, y solo sustituye la búsqueda en profundidad por una búsqueda en anchura con cola, por lo que el costo de implementación es bajo.

---

## 5. Referencias

Cormen, T. H., Leiserson, C. E., Rivest, R. L. y Stein, C. (2009). *Introduction to Algorithms* (3.ª ed.). MIT Press. Capítulo 26, “Maximum Flow”.

Edmonds, J. y Karp, R. M. (1972). Theoretical improvements in algorithmic efficiency for network flow problems. *Journal of the ACM*, 19(2), 248–264. https://doi.org/10.1145/321694.321699

Ford, L. R. y Fulkerson, D. R. (1956). Maximal flow through a network. *Canadian Journal of Mathematics*, 8, 399–404. https://doi.org/10.4153/CJM-1956-045-5

Kleinberg, J. y Tardos, É. (2006). *Algorithm Design*. Addison-Wesley. Capítulo 7, “Network Flow”.

Zwick, U. (1995). The smallest networks on which the Ford-Fulkerson maximum flow procedure may fail to terminate. *Theoretical Computer Science*, 148(1), 165–170. https://doi.org/10.1016/0304-3975(95)00022-O
