# Proyecto 2 de Teoría de Grafos

Desde la carpeta que contiene `src`, con Python 3.10 o superior y Tkinter, abre la aplicación con:

```sh
python3 -m src.ui.app
```

La interfaz usa la biblioteca estándar de Python. Puedes comprobar que tu instalación dispone de Tkinter con `python3 -m tkinter`.

## Comparar las tres redes

1. Con origen O y destino T, pulsa **Calcular flujo máximo** y **Calcular corte mínimo**. En **Comparar**, pulsa **Guardar como base**. La red inicial da 8 paquetes/h.
2. En **Editar red**, desactiva G → T. Repite los dos cálculos y guarda la variante 1. Da 4 paquetes/h.
3. Agrega de nuevo G → T con capacidad 4 y cambia su capacidad a 6. Repite los cálculos y guarda la variante 2. Da 10 paquetes/h. Así la única diferencia respecto de la base es la capacidad de G → T.
4. En **Comparar**, pulsa **Recalcular todo**. Cada fila debe mostrar el mismo valor de flujo y de corte.

## Reproducir el informe o ejecutar las pruebas

```sh
python3 verificar.py
```

El comando muestra los cinco casos y comprueba capacidad, conservación y valor del flujo. Para ejecutar las pruebas del repositorio:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

Las pruebas de ventana requieren una sesión gráfica. En Windows, activa el entorno con `.venv\Scripts\activate`.
