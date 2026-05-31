#!/usr/bin/env python3
"""
benchmark_voraces.py  (renombrado desde benchmark_voracesss.py)
====================
Benchmark experimental para comparar heurísticas voraces simples
contra la solución exacta (roPD) en el problema del riego óptimo.

Algoritmos evaluados:
  - voraz_edd   : Earliest Due Date  (menor ts primero)
  - voraz_spt   : Shortest Processing Time (menor tr primero)
  - voraz_wspt  : Weighted SPT (mayor p/tr primero)
  - voraz_wmdd  : Weighted Modified Due Date (regla pura, sin lookahead)
  - roV         : Voraz WMDD + Lookahead (implementación del proyecto)
  - roPD        : Programación Dinámica (referencia óptima)

Referencia de salidas:
  El costo óptimo (roPD) se lee directamente desde los archivos
  data/output/*_out.txt en lugar de ejecutar el algoritmo de PD.
  Los costos de las heurísticas también se comparan contra ese valor.

USO:
  python benchmark_voraces.py

  El script asume que se ejecuta desde la raíz del proyecto, donde
  existen las carpetas:
    - data/ejemplos/   (archivos *_in.txt de entrada)
    - data/output/     (archivos *_out.txt de referencia)
    - python_algorithms/ (módulos del proyecto)

Autor: Benchmark generado para Análisis de Algoritmos II
Python: 3.12+
"""

import os
import sys
import time
import statistics
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE RUTAS
# ─────────────────────────────────────────────────────────────────────────────

RAIZ_PROYECTO   = Path(__file__).parent
DIR_ALGORITMOS  = RAIZ_PROYECTO / "python_algorithms"
DIR_EJEMPLOS    = RAIZ_PROYECTO / "data" / "ejemplos"
DIR_OUTPUT      = RAIZ_PROYECTO / "data" / "output"

# Agregar el módulo Python al path
sys.path.insert(0, str(DIR_ALGORITMOS))

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTACIONES DEL PROYECTO
# ─────────────────────────────────────────────────────────────────────────────

try:
    from modelo_riego import roV
    from tablon import Tablon, construir_tablones
    from costo_tablon import calcular_costo_tablon
except ImportError as e:
    print(f"[ERROR] No se pudo importar módulo del proyecto: {e}", file=sys.stderr)
    print(f"        Asegúrate de ejecutar desde la raíz del proyecto.", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS INTERNOS
# ─────────────────────────────────────────────────────────────────────────────

# Una finca es una lista de tuplas (ts, tr, p, ro)
Finca      = List[Tuple[int, int, int, int]]
Resultado  = Tuple[List[int], int]          # (orden, costo)


# ─────────────────────────────────────────────────────────────────────────────
# CAPA DE I/O
# ─────────────────────────────────────────────────────────────────────────────

def leer_instancia(ruta: Path) -> Finca:
    """
    Lee una instancia del problema desde un archivo .txt.

    FORMATO ESPERADO:
    -----------------
        n
        ts0,tr0,p0,ro0
        ts1,tr1,p1,ro1
        ...

    ENTRADAS:
    ----------
    ruta : Path
        Ruta al archivo de entrada.

    SALIDAS:
    ----------
    Finca
        Lista de tuplas (ts, tr, p, ro) con los datos de los tablones.
    """
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = [l.strip() for l in f.readlines() if l.strip()]

    n = int(lineas[0])
    finca: Finca = []

    for i in range(1, n + 1):
        partes = lineas[i].split(",")
        ts, tr, p, ro = int(partes[0]), int(partes[1]), int(partes[2]), int(partes[3])
        finca.append((ts, tr, p, ro))

    return finca


def leer_salida_esperada(ruta: Path) -> Optional[Tuple[int, List[int]]]:
    """
    Lee la salida esperada desde un archivo *_out.txt.

    FORMATO ESPERADO:
    -----------------
        costo
        idx0
        idx1
        ...

    SALIDAS:
    ----------
    Optional[Tuple[int, List[int]]]
        (costo_esperado, permutacion_esperada) o None si el archivo no existe.
    """
    if not ruta.exists():
        return None

    with open(ruta, "r", encoding="utf-8") as f:
        lineas = [l.strip() for l in f.readlines() if l.strip()]

    costo = int(lineas[0])
    permutacion = [int(l) for l in lineas[1:]]
    return costo, permutacion


# ─────────────────────────────────────────────────────────────────────────────
# HEURÍSTICAS VORACES SIMPLES
# ─────────────────────────────────────────────────────────────────────────────
#
# Cada heurística recibe una Finca y devuelve (orden: List[int], costo: int).
# La función auxiliar _simular_costo() calcula el costo real de cualquier orden.
# ─────────────────────────────────────────────────────────────────────────────

def _simular_costo(finca: Finca, orden: List[int]) -> int:
    """
    Calcula el costo total real de una permutación dada.

    ENTRADAS:
    ----------
    finca  : Finca
        Datos de los tablones.
    orden  : List[int]
        Permutación a evaluar (índices de tablones).

    SALIDAS:
    ----------
    int
        Costo total acumulado según la función de costo del proyecto.
    """
    tablones = construir_tablones(finca)
    tiempo   = 0
    costo    = 0

    for idx in orden:
        costo  += calcular_costo_tablon(tablones[idx], tiempo)
        tiempo += tablones[idx].tiempo_regado

    return costo


def voraz_edd(finca: Finca) -> Resultado:
    """
    EDD – Earliest Due Date.
    Criterio de ordenamiento: menor ts (tiempo de supervivencia) primero.
    Intuición: atender primero los tablones que antes pierden viabilidad.
    Desempate: índice descendente (consistente con roV, roPD y roFB).

    Complejidad: O(n log n)
    """
    n      = len(finca)
    orden  = sorted(range(n), key=lambda i: (finca[i][0], -i))     # ts asc, idx desc
    costo  = _simular_costo(finca, orden)
    return orden, costo


def voraz_spt(finca: Finca) -> Resultado:
    """
    SPT – Shortest Processing Time.
    Criterio de ordenamiento: menor tr (tiempo de regado) primero.
    Intuición: terminar más trabajos por unidad de tiempo.
    Desempate: índice descendente (consistente con roV, roPD y roFB).

    Complejidad: O(n log n)
    """
    n      = len(finca)
    orden  = sorted(range(n), key=lambda i: (finca[i][1], -i))     # tr asc, idx desc
    costo  = _simular_costo(finca, orden)
    return orden, costo


def voraz_wspt(finca: Finca) -> Resultado:
    """
    WSPT – Weighted Shortest Processing Time.
    Criterio de ordenamiento: mayor ratio p/tr primero.
    Intuición: priorizar tablones con alta prioridad y bajo costo de tiempo.
    Desempate: índice descendente (consistente con roV, roPD y roFB).

    Complejidad: O(n log n)
    """
    n      = len(finca)
    # Ratio descendente: mayor p/tr → va antes; desempate: idx descendente
    orden  = sorted(range(n), key=lambda i: (-finca[i][2] / finca[i][1], -i))
    costo  = _simular_costo(finca, orden)
    return orden, costo


def voraz_wmdd(finca: Finca) -> Resultado:
    """
    WMDD – Weighted Modified Due Date (regla pura, SIN lookahead).
    Criterio de ordenamiento: en cada paso, elige el tablón con menor
    max(ts - tr, t_actual + tr) / p, donde t_actual es el tiempo corriente.

    Esta es la heurística de referencia que usa roV como sub-ordenamiento
    en su método piloto, pero aquí se aplica de forma greedy directa.

    Complejidad: O(n²)
    """
    n        = len(finca)
    tablones = construir_tablones(finca)
    pendientes = list(range(n))
    orden      : List[int] = []
    t_actual   = 0

    while pendientes:
        # Clave WMDD: max(ts - tr, t + tr) / p
        # Desempate: índice descendente (consistente con roV, roPD y roFB)
        mejor_score = float('inf')
        elegido = -1
        for j in pendientes:
            score = max(
                tablones[j].tiempo_supervivencia - tablones[j].tiempo_regado,
                t_actual + tablones[j].tiempo_regado,
            ) / tablones[j].prioridad
            if score < mejor_score or (score == mejor_score and j > elegido):
                mejor_score = score
                elegido = j
        orden.append(elegido)
        t_actual += tablones[elegido].tiempo_regado
        pendientes.remove(elegido)

    costo = _simular_costo(finca, orden)
    return orden, costo





def voraz_atc_dinamico(finca: Finca, K: float = 2.0) -> Resultado:
    """
    ATC Dinámico (Apparent Tardiness Cost) sin lookahead explícito.
    
    Criterio de ordenamiento: Maximizar el índice ATC en cada instante t.
    El índice combina la regla WSPT con un decaimiento exponencial basado 
    en la holgura del tablón y el promedio de tiempos de regado restantes.
    
    ENTRADAS:
    ----------
    finca : Finca
        Datos de los tablones.
    K     : float
        Parámetro de escalado de lookahead implícito (típicamente 1.5 - 3.0).
        
    Complejidad: O(n²)
    """
    n = len(finca)
    tablones = construir_tablones(finca)
    pendientes = list(range(n))
    orden: List[int] = []
    t_actual = 0

    while pendientes:
        # Mecanismo predictivo implícito: promedio de esfuerzo futuro
        tr_promedio = sum(tablones[j].tiempo_regado for j in pendientes) / len(pendientes)
        
        # Evitar división por cero en casos borde
        denominador_prediccion = K * tr_promedio if tr_promedio > 0 else 1e-5
        
        mejor_score = -1.0
        elegido = -1
        
        for j in pendientes:
            tablon = tablones[j]
            
            # Holgura: tiempo disponible antes de empezar a penalizar
            holgura = max(0, tablon.tiempo_supervivencia - t_actual - tablon.tiempo_regado)
            
            # WSPT Base
            if tablon.tiempo_regado > 0:
                wspt_base = tablon.prioridad / tablon.tiempo_regado
            else:
                wspt_base = float('inf')
                
            # Índice ATC
            score = wspt_base * math.exp(-holgura / denominador_prediccion)
            
            # Buscamos MAXIMIZAR el score. 
            # Desempate: índice descendente (consistente con roV, roPD y roFB)
            if score > mejor_score or (score == mejor_score and j > elegido):
                mejor_score = score
                elegido = j
                
        # Consolidar decisión
        orden.append(elegido)
        t_actual += tablones[elegido].tiempo_regado
        pendientes.remove(elegido)

    costo = _simular_costo(finca, orden)
    return orden, costo

# ─────────────────────────────────────────────────────────────────────────────
# CAPA DE EJECUCIÓN Y MEDICIÓN
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_algoritmo(
    nombre: str,
    funcion: Any,
    finca: Finca,
) -> Dict[str, Any]:
    """
    Ejecuta un algoritmo, mide su tiempo y devuelve un diccionario de métricas.

    ENTRADAS:
    ----------
    nombre   : str
        Nombre legible del algoritmo.
    funcion  : callable
        Función que recibe una Finca y retorna (orden, costo).
    finca    : Finca
        Instancia del problema.

    SALIDAS:
    ----------
    Dict[str, Any]
        {
          "nombre"   : str,
          "orden"    : List[int],
          "costo"    : int,
          "tiempo_ms": float,
        }
    """
    t0    = time.perf_counter()
    orden, costo = funcion(finca)
    t1    = time.perf_counter()

    return {
        "nombre"    : nombre,
        "orden"     : orden,
        "costo"     : int(costo),
        "tiempo_ms" : round((t1 - t0) * 1000, 3),
    }


def calcular_gap(costo_obtenido: int, costo_optimo: int) -> float:
    """
    Calcula el GAP porcentual entre el costo obtenido y el óptimo.

    Fórmula: gap = 100 * (costo - costo_optimo) / costo_optimo

    ENTRADAS:
    ----------
    costo_obtenido : int
    costo_optimo   : int

    SALIDAS:
    ----------
    float
        GAP en porcentaje. 0.0 si el costo es óptimo.
    """
    if costo_optimo == 0:
        return 0.0
    return round(100.0 * (costo_obtenido - costo_optimo) / costo_optimo, 2)


# ─────────────────────────────────────────────────────────────────────────────
# CAPA DE PRESENTACIÓN
# ─────────────────────────────────────────────────────────────────────────────

# Columnas de la tabla principal
_COLS = [
    ("Algoritmo",  "algoritmo",  18),
    ("Costo",      "costo",       8),
    ("GAP %",      "gap",         8),
    ("Tiempo(ms)", "tiempo_ms",  11),
    ("vs Output",  "vs_output",  11),
]

# Anchos para la tabla de resumen
_COLS_RESUMEN = [
    ("Algoritmo",   "algoritmo",   18),
    ("GAP Prom %",  "gap_prom",     11),
    ("GAP Mejor %", "gap_mejor",    11),
    ("GAP Peor %",  "gap_peor",     11),
    ("t̄ (ms)",      "t_prom",       11),
    ("Óptimos",     "optimos",       9),
    ("Total",       "total",         7),
]


def _separador(cols: list) -> str:
    """Genera una línea separadora ─ para la tabla."""
    return "+" + "+".join("─" * (ancho + 2) for _, _, ancho in cols) + "+"


def _encabezado(cols: list) -> str:
    """Genera la fila de encabezados."""
    celdas = [f" {titulo:<{ancho}} " for titulo, _, ancho in cols]
    return "|" + "|".join(celdas) + "|"


def _fila(cols: list, datos: Dict[str, Any]) -> str:
    """Genera una fila de datos."""
    celdas = []
    for _, clave, ancho in cols:
        valor = datos.get(clave, "")
        texto = str(valor)
        # Alineación numérica a la derecha para columnas de números
        if clave in ("costo", "gap", "tiempo_ms", "gap_prom", "gap_mejor",
                     "gap_peor", "t_prom", "optimos", "total"):
            celdas.append(f" {texto:>{ancho}} ")
        else:
            celdas.append(f" {texto:<{ancho}} ")
    return "|" + "|".join(celdas) + "|"


def imprimir_tabla_instancia(
    nombre_instancia: str,
    n_tablones: int,
    resultados: List[Dict[str, Any]],
    costo_optimo: int,
    costo_output: Optional[int],
) -> None:
    """
    Imprime la tabla de resultados para una instancia concreta.

    ENTRADAS:
    ----------
    nombre_instancia : str
    n_tablones       : int
    resultados       : List[Dict]  (uno por algoritmo, sin roPD que es referencia)
    costo_optimo     : int         (costo calculado por roPD)
    costo_output     : Optional[int] (costo del archivo _out.txt, puede ser None)
    """
    ref_str = f"Output={costo_output}" if costo_output is not None else "Sin output"
    print(f"\n{'━'*72}")
    print(f"  Instancia: {nombre_instancia}   |   n={n_tablones}   |   "
          f"Óptimo(PD)={costo_optimo}   |   {ref_str}")
    print(_separador(_COLS))
    print(_encabezado(_COLS))
    print(_separador(_COLS))

    for r in resultados:
        gap = calcular_gap(r["costo"], costo_optimo)

        # Comparar contra output esperado
        if costo_output is not None:
            diff = r["costo"] - costo_output
            if diff == 0:
                vs_output = "✓ igual"
            elif diff > 0:
                vs_output = f"+{diff}"
            else:
                vs_output = f"{diff}"
        else:
            vs_output = "N/A"

        fila_datos = {
            "algoritmo" : r["nombre"],
            "costo"     : r["costo"],
            "gap"       : f"{gap:.2f}",
            "tiempo_ms" : f"{r['tiempo_ms']:.3f}",
            "vs_output" : vs_output,
        }
        print(_fila(_COLS, fila_datos))

    # Fila de referencia roPD
    ref_datos = {
        "algoritmo" : "roPD (óptimo)",
        "costo"     : costo_optimo,
        "gap"       : "0.00",
        "tiempo_ms" : "—",
        "vs_output" : (
            "✓ igual" if costo_output == costo_optimo
            else (f"+{costo_optimo-costo_output}" if costo_output is not None else "N/A")
        ),
    }
    print(_separador(_COLS))
    print(_fila(_COLS, ref_datos))
    print(_separador(_COLS))


def imprimir_resumen_global(acumulados: Dict[str, List]) -> None:
    """
    Imprime la tabla resumen global al finalizar todas las instancias.

    ENTRADAS:
    ----------
    acumulados : Dict[str, List]
        Clave = nombre del algoritmo.
        Valor = lista de dicts {"gap": float, "tiempo_ms": float, "es_optimo": bool}
    """
    print(f"\n\n{'━'*72}")
    print("  RESUMEN GLOBAL — Todas las instancias")
    print(_separador(_COLS_RESUMEN))
    print(_encabezado(_COLS_RESUMEN))
    print(_separador(_COLS_RESUMEN))

    for nombre_algo, registros in acumulados.items():
        gaps     = [r["gap"] for r in registros]
        tiempos  = [r["tiempo_ms"] for r in registros]
        optimos  = sum(1 for r in registros if r["es_optimo"])
        total    = len(registros)

        datos = {
            "algoritmo" : nombre_algo,
            "gap_prom"  : f"{statistics.mean(gaps):.2f}",
            "gap_mejor" : f"{min(gaps):.2f}",
            "gap_peor"  : f"{max(gaps):.2f}",
            "t_prom"    : f"{statistics.mean(tiempos):.3f}",
            "optimos"   : f"{optimos}/{total}",
            "total"     : str(total),
        }
        print(_fila(_COLS_RESUMEN, datos))

    print(_separador(_COLS_RESUMEN))


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO DE ALGORITMOS A EVALUAR
# ─────────────────────────────────────────────────────────────────────────────




def voraz_atc(finca: Finca, k: float = 2.0) -> Resultado:
    """
    ATC – Apparent Tardiness Cost.

    Heurística voraz pura ampliamente estudiada en la literatura de
    scheduling de una máquina con penalidades ponderadas por tardanza.
    Referencia clásica: Vepsalainen & Morton (1987).

    CRITERIO DE PRIORIDAD:
    ----------------------
    En cada paso, se elige el tablón j con mayor índice ATC:

        ATC(j, t) = (p_j / tr_j) * exp( -max(ts_j - tr_j - t, 0) / (k * tr_prom) )

    Donde:
      - p_j   : prioridad del tablón j
      - tr_j  : tiempo de regado del tablón j
      - ts_j  : tiempo de supervivencia del tablón j
      - t     : tiempo actual
      - k     : parámetro de escala (típicamente 2–4; default=2)
      - tr_prom: promedio de tiempos de regado de los tablones PENDIENTES

    INTUICIÓN:
    ----------
    - El factor p/tr favorece tablones con alta prioridad y bajo tiempo de riego
      (similar a WSPT).
    - El factor exponencial penaliza tablones cuyo "holgura" (ts - tr - t) es
      grande: si un tablón tiene mucho margen, su urgencia decae exponencialmente.
    - Cuando la holgura es negativa (ya debería haber sido regado), el exponente
      vale exp(0)=1 y solo domina p/tr.
    - El parámetro k controla qué tan agresivamente se penaliza la baja urgencia.

    DESEMPATE: índice descendente (consistente con roV, roPD y roFB).

    Complejidad: O(n²)
    """
    import math

    n        = len(finca)
    tablones = construir_tablones(finca)
    pendientes = list(range(n))
    orden      : List[int] = []
    t_actual   = 0

    while pendientes:
        # tr promedio de los tablones aún pendientes
        tr_prom = sum(tablones[j].tiempo_regado for j in pendientes) / len(pendientes)
        if tr_prom == 0:
            tr_prom = 1  # evitar división por cero

        mejor_atc = -float('inf')
        elegido   = -1

        for j in pendientes:
            tr_j = tablones[j].tiempo_regado
            ts_j = tablones[j].tiempo_supervivencia
            p_j  = tablones[j].prioridad

            holgura = max(ts_j - tr_j - t_actual, 0)
            atc = (p_j / tr_j) * math.exp(-holgura / (k * tr_prom))

            # Mayor ATC va primero; desempate: índice descendente
            if atc > mejor_atc or (atc == mejor_atc and j > elegido):
                mejor_atc = atc
                elegido   = j

        orden.append(elegido)
        t_actual += tablones[elegido].tiempo_regado
        pendientes.remove(elegido)

    costo = _simular_costo(finca, orden)
    return orden, costo







def voraz_wcovert(finca: Finca, k: float = 2.0) -> Resultado:
    """
    W-COVERT Mejorado O(n²) — Adaptativo con Cola Exponencial Suavizada

    Aplica el índice lineal COVERT. Si la situación es relajada y el 
    horizonte decae bajo 0, en lugar de igualar todos a un multiplicador
    ciego de 1e-9 (cayendo a un simple WSPT), aplica un decaimiento 
    exponencial ATC para que haya desempate racional.
    """
    import math

    n        = len(finca)
    tablones = construir_tablones(finca)
    pendientes = list(range(n))
    orden: List[int] = []
    tiempo_actual = 0

    while pendientes:
        n_pend  = len(pendientes)
        
        # --- 1. Parámetros Globales de Congestión ---
        p_prom  = sum(tablones[j].tiempo_regado for j in pendientes) / n_pend
        p_total = sum(tablones[j].tiempo_regado for j in pendientes)
        d_prom  = sum(tablones[j].tiempo_supervivencia for j in pendientes) / n_pend

        # Tardiness Factor (TF): 0 (Todos relajados) -> 1.0 (Crisis estresada)
        if p_total > 0:
            tf = max(0.0, 1.0 - (d_prom - tiempo_actual) / p_total)
        else:
            tf = 1.0

        # Ventana elástica basada en la crisis de la finca
        if tf < 0.2:
            k_dinamico = 1.5   # Muchos márgenes libres -> Horizonte corto (EDD focus)
        elif tf < 0.6:
            k_dinamico = 2.0   # Tensión normal (clásico)
        elif tf < 0.9:
            k_dinamico = 2.8   # Tensión alta -> expandir panorama prioritario
        else:
            k_dinamico = 3.5   # Crisis máxima -> priorizar rentabilidad estricta

        decay = k_dinamico * p_prom if p_prom > 0 else 1e-5

        mejor_idx   = -1
        mejor_score = -float('inf')
        mejor_wspt  = -float('inf')

        for j in pendientes:
            tab   = tablones[j]
            p_j   = tab.tiempo_regado
            w_j   = tab.prioridad
            d_j   = tab.tiempo_supervivencia

            # Ratio puro de Rentabilidad y su Holgura
            wspt_j    = w_j / p_j if p_j > 0 else float('inf')
            holgura_j = max(0.0, d_j - p_j - tiempo_actual)

            # --- 2. Función COVERT con Remanente Exponencial ---
            factor = 1.0 - holgura_j / decay
            
            if factor > 0:
                # Régimen Crítico: El tablón está bajo amenaza certera en el horizonte
                score = wspt_j * factor
            else:
                # Régimen "Seguro"/Relajado: Está lejos, fuera del horizonte prioritario.
                # Utilizamos el decaimiento ATC para que NO se pierda el sentido
                # de gravedad relativo. Multiplicador de 1e-9 asegura que un trabajo
                # aquí jamás sobreescriba a un trabajo en Régimen Crítico.
                score = wspt_j * math.exp(-holgura_j / decay) * 1e-9

            # --- 3. Criterio de Selección Robusto y Desempates ---
            if mejor_idx == -1:
                mejor_idx = j; mejor_score = score; mejor_wspt = wspt_j
            elif score > mejor_score + 1e-12:
                mejor_idx = j; mejor_score = score; mejor_wspt = wspt_j
            elif abs(score - mejor_score) <= 1e-12:
                # Rentabilidad estricta en caso de tener valores idénticos de urgencia
                if wspt_j > mejor_wspt + 1e-12:
                    mejor_idx = j; mejor_score = score; mejor_wspt = wspt_j
                # Desempate indexado como la Programación Dinámica roPD de referencia
                elif abs(wspt_j - mejor_wspt) <= 1e-12:
                    if j > mejor_idx:
                        mejor_idx = j; mejor_wspt = wspt_j

        pendientes.remove(mejor_idx)
        orden.append(mejor_idx)
        tiempo_actual += tablones[mejor_idx].tiempo_regado

    costo = _simular_costo(finca, orden)
    return orden, costo



import math
from typing import List, Tuple
from tablon import construir_tablones, Tablon
from costo_tablon import calcular_costo_tablon

# Alias
Finca = List[Tuple[int, int, int, int]]
Resultado = Tuple[List[int], int]

def voraz_puro_estricto(finca: Finca) -> Resultado:
    """
    Algoritmo Voraz Dinámico Puro.
    Cumple estrictamente con la teoría de Reglas de Despacho (Dispatching Rules).
    Evalúa cada candidato basándose ÚNICAMENTE en sus propios atributos
    y el tiempo actual del reloj, sin simular el sistema global.
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)
    pendientes = set(range(n)) 
    orden = []
    tiempo_actual = 0
    costo_total_finca = 0

    # Ratios estáticos para desempates clásicos
    wspt_ratios = [t.prioridad / t.tiempo_regado for t in tablones]

    while pendientes:
        mejor_idx = -1
        # Ahora buscamos MAXIMIZAR la urgencia del tablón
        mejor_urgencia_local = float("-inf") 
        ganador_costo_propio = 0

        for j in pendientes:
            tab_j = tablones[j]
            tr = tab_j.tiempo_regado
            ts = tab_j.tiempo_supervivencia
            
            # ─────────────────────────────────────────────────────────────
            # LA FÓRMULA DE LA PUREZA VORAZ (Regla de Despacho Local)
            # Solo utilizamos: tab_j y tiempo_actual. Ni rastro de los demás.
            # ─────────────────────────────────────────────────────────────
            
            # Implementamos el Índice WMDD (Weighted Modified Due Date)
            # Matemáticamente: Prioridad / max(Tiempo de Supervivencia, Tiempo de Finalización si lo riego ya)
            tiempo_finalizacion = tiempo_actual + tr
            mdd = max(ts, tiempo_finalizacion)
            
            # Score de Urgencia (mayor score = más urgente regarlo ahora)
            # Evitamos división por cero si mdd llega a ser 0
            urgencia_local = (tab_j.prioridad / mdd) if mdd > 0 else float("inf")
            
            # --- FIN DE LA FÓRMULA PURA ---

            # Evaluación de la mejor opción
            if urgencia_local > mejor_urgencia_local:
                mejor_urgencia_local = urgencia_local
                mejor_idx = j
            elif urgencia_local == mejor_urgencia_local:
                # 1° Desempate: WSPT estático
                if wspt_ratios[j] > wspt_ratios[mejor_idx]:
                    mejor_idx = j
                elif wspt_ratios[j] == wspt_ratios[mejor_idx]:
                    # 2° Desempate: Lexicográfico descendente
                    if j > mejor_idx:
                        mejor_idx = j

        # Calculamos el costo real de haber elegido a este ganador en este momento
        ganador_costo_propio = calcular_costo_tablon(tablones[mejor_idx], tiempo_actual)

        # Fijar de forma irrevocable el ganador
        orden.append(mejor_idx)
        costo_total_finca += ganador_costo_propio
        tiempo_actual += tablones[mejor_idx].tiempo_regado
        
        pendientes.remove(mejor_idx)

    return orden, costo_total_finca


import math
from typing import List, Tuple
from tablon import construir_tablones, Tablon
from costo_tablon import calcular_costo_tablon

# Alias
Finca = List[Tuple[int, int, int, int]]
Resultado = Tuple[List[int], int]

def voraz_wcovert_puro(finca: Finca, k: float = 2.0) -> Resultado:
    """
    Algoritmo Voraz Puro Estricto: W-COVERT (Local Dispatching Rule).
    Cumple al 100% las 10 reglas académicas de "Greedy Puro":
    - Decisión local estricta f(j, t).
    - Cero evaluación del sistema global.
    - Cero lookahead o simulaciones.
    - Factor 'k' como constante externa (no derivada de la instancia).
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)
    
    # Manejo del estado local irrevocable
    pendientes = set(range(n)) 
    orden = []
    tiempo_actual = 0
    costo_total_finca = 0

    # Índices estáticos para desempates puros (Regla 1: Permitido usar atributos propios)
    wspt_ratios = [t.prioridad / t.tiempo_regado for t in tablones]

    while pendientes:
        mejor_idx = -1
        mejor_score = float("-inf")
        ganador_costo_propio = 0

        for j in pendientes:
            tab_j = tablones[j]
            tr_j = tab_j.tiempo_regado
            ts_j = tab_j.tiempo_supervivencia
            p_j = tab_j.prioridad
            
            # ─────────────────────────────────────────────────────────
            # REGLA DE DECISIÓN LOCAL ESTRICTA: f(j, estado_actual)
            # Solo variables de 'j' (tr_j, ts_j, p_j) y 'tiempo_actual'.
            # ─────────────────────────────────────────────────────────
            
            # 1. Calculamos la Holgura Local (Slack)
            # ¿Cuánto tiempo libre le queda a este tablón antes de entrar en déficit crítico (Caso 3)?
            holgura = ts_j - tiempo_actual - tr_j
            
            # 2. Función de Penalidad COVERT
            if holgura <= 0:
                # Si ya está en déficit o entrará en déficit si lo riego ahora: Urgencia Máxima (1.0)
                covert_factor = 1.0
            else:
                # Si tiene holgura, su urgencia decae linealmente.
                # USAMOS SU PROPIO 'tr_j' * k PARA EVITAR ESTADÍSTICAS GLOBALES DE LA COLA
                margen_local = k * tr_j
                covert_factor = max(0.0, 1.0 - (holgura / margen_local))
            
            # 3. Índice Dinámico Final W-COVERT
            # Ponderación WSPT * Factor de Holgura Local
            score = (p_j / tr_j) * covert_factor
            
            # ─────────────────────────────────────────────────────────

            # Evaluación Greedy y Desempates
            if score > mejor_score:
                mejor_score = score
                mejor_idx = j
            elif score == mejor_score:
                # 1° Desempate: Ratio WSPT estático
                if wspt_ratios[j] > wspt_ratios[mejor_idx]:
                    mejor_idx = j
                elif wspt_ratios[j] == wspt_ratios[mejor_idx]:
                    # 2° Desempate: Lexicográfico descendente (por consistencia con tu benchmark)
                    if j > mejor_idx:
                        mejor_idx = j

        # Calculamos el costo real usando la función de negocio solo para el ganador
        costo_ahora = calcular_costo_tablon(tablones[mejor_idx], tiempo_actual)

        # Fijar la elección de forma irrevocable (Regla 4)
        orden.append(mejor_idx)
        costo_total_finca += costo_ahora
        tiempo_actual += tablones[mejor_idx].tiempo_regado
        
        # Actualización de estado mínimo (Regla 7)
        pendientes.remove(mejor_idx)

    return orden, costo_total_finca



import math
from typing import List, Tuple
from tablon import construir_tablones, Tablon
from costo_tablon import calcular_costo_tablon

# Alias
Finca = List[Tuple[int, int, int, int]]
Resultado = Tuple[List[int], int]

def voraz_wcovert_puros(finca: Finca, k_slack: float = 2.0, k_ro: float = 1.0) -> Resultado:
    """
    Algoritmo Voraz Puro Estricto (Matemático Continuo).
    
    CUMPLE LAS 10 REGLAS DE PUREZA ABSOLUTA:
    - F(j, t) es una ÚNICA función continua (Reglas 1, 5, 8, 10).
    - CERO bifurcaciones (if/else) en el cálculo del score (Regla 8).
    - CERO evaluación global o simulaciones (Reglas 2, 3, 8).
    - Decisiones irrevocables (Reglas 4, 7).
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)
    
    # Manejo del estado local irrevocable (Regla 7)
    pendientes = set(range(n)) 
    orden = []
    tiempo_actual = 0
    costo_total_finca = 0

    # Índices estáticos para desempates deterministas (Reglas 1 y 9)
    wspt_ratios = [t.prioridad / t.tiempo_regado for t in tablones]

    while pendientes:
        mejor_idx = -1
        mejor_score = float("-inf")
        ganador_costo_propio = 0

        for j in pendientes:
            tab_j = tablones[j]
            tr_j = tab_j.tiempo_regado
            ts_j = tab_j.tiempo_supervivencia
            p_j = tab_j.prioridad
            ro_j = tab_j.riego_optimo
            t = tiempo_actual
            
            # ─────────────────────────────────────────────────────────
            # REGLA DE DECISIÓN LOCAL ESTRICTA: f(j, t)
            # Todo el comportamiento se rige por matemática pura y continua.
            # ─────────────────────────────────────────────────────────
            
            # 1. Base WSPT (Eficiencia intrínseca)
            peso = p_j / tr_j
            
            # 2. Factor de Riego Óptimo (Llegada)
            # Reemplaza la necesidad de un "if t < ro_j".
            # Si t < ro_j, la espera es positiva y math.exp() aplasta el score hacia 0.
            # Si t >= ro_j, max() da 0, y exp(0) = 1.0 (Vía libre, sin penalización).
            espera = max(0.0, ro_j - t)
            factor_ro = math.exp(-espera / (k_ro * tr_j))
            
            # 3. Factor de Holgura (Urgencia de Supervivencia)
            # Reemplaza la necesidad de un "if holgura <= 0".
            # Si queda mucha holgura, exp() da un número bajo (poca urgencia).
            # Si ya se pasó el límite (holgura negativa), max() da 0 y exp(0) = 1.0 (Urgencia Máxima).
            holgura = max(0.0, ts_j - t - tr_j)
            factor_holgura = math.exp(-holgura / (k_slack * tr_j))
            
            # 4. ÍNDICE DE DESPACHO ÚNICO Y CONTINUO (f(j, t))
            # Multiplicación estricta de las tres variables locales.
            score = peso * factor_ro * factor_holgura
            
            # ─────────────────────────────────────────────────────────

            # Selección del máximo local (Regla 9: Determinismo)
            if score > mejor_score:
                mejor_score = score
                mejor_idx = j
            elif score == mejor_score:
                if wspt_ratios[j] > wspt_ratios[mejor_idx]:
                    mejor_idx = j
                elif wspt_ratios[j] == wspt_ratios[mejor_idx] and j > mejor_idx:
                    mejor_idx = j

        # Calculamos el costo REAL de negocio de forma aislada (fuera de la decisión)
        costo_ahora = calcular_costo_tablon(tablones[mejor_idx], tiempo_actual)

        # Elección irrevocable (Reglas 4 y 7)
        orden.append(mejor_idx)
        costo_total_finca += costo_ahora
        tiempo_actual += tablones[mejor_idx].tiempo_regado
        
        pendientes.remove(mejor_idx)

    return orden, costo_total_finca

ALGORITMOS_BENCHMARK: List[Tuple[str, Any]] = [
    
    ("EDD",                    voraz_edd),           # Earliest Due Date
    ("SPT",                    voraz_spt),           # Shortest Processing Time
    ("WSPT",                   voraz_wspt),          # Weighted Shortest Processing Time
    ("WMDD",                   voraz_wmdd),          # Weighted Modified Due Date
    ("ATC  (k=2)",             voraz_atc),           # Apparent Tardiness Cost
    ("W-COVERT Adaptativo",    voraz_wcovert),       # COVERT con ventana dinámica global
    ("WMDD Voraz",             voraz_puro_estricto), # WMDD greedy puro (sin lookahead)
    ("W-COVERT Local",         voraz_wcovert_puro),  # COVERT lineal con holgura local
    ("roV  (ATCS)",            voraz_wcovert_puros), # ATCS con factor ro — algoritmo del proyecto
    

    
]

# ─────────────────────────────────────────────────────────────────────────────
# FLUJO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Punto de entrada principal del benchmark.

    Flujo:
    1. Descubrir todos los archivos *_in.txt en data/ejemplos/.
    2. Para cada instancia:
       a. Leer la finca.
       b. Leer el costo óptimo (roPD) desde el archivo *_out.txt precalculado.
       c. Ejecutar cada heurística voraz.
       d. Imprimir tabla de la instancia.
       e. Acumular métricas para el resumen.
    3. Imprimir tabla resumen global.
    """

    # ── Descubrir instancias ──────────────────────────────────────────────────
    if not DIR_EJEMPLOS.exists():
        print(f"[ERROR] No se encontró la carpeta: {DIR_EJEMPLOS}", file=sys.stderr)
        sys.exit(1)

    archivos = sorted(
        DIR_EJEMPLOS.glob("*_in.txt"),
        key=lambda p: int("".join(filter(str.isdigit, p.stem)) or "0"),
    )

    if not archivos:
        print(f"[ERROR] No se encontraron archivos *_in.txt en {DIR_EJEMPLOS}")
        sys.exit(1)

    print(f"\n{'═'*72}")
    print(f"  BENCHMARK DE HEURÍSTICAS VORACES — Problema del Riego Óptimo")
    print(f"  Instancias encontradas: {len(archivos)}")
    print(f"  Algoritmos evaluados  : {len(ALGORITMOS_BENCHMARK)} heurísticas + roPD (ref. precalculada)")
    print(f"{'═'*72}")

    # Acumuladores para el resumen global
    # { nombre_algoritmo: [{"gap": float, "tiempo_ms": float, "es_optimo": bool}] }
    acumulados: Dict[str, List[Dict[str, Any]]] = {
        nombre: [] for nombre, _ in ALGORITMOS_BENCHMARK
    }

    # ── Iterar sobre cada instancia ───────────────────────────────────────────
    for ruta_entrada in archivos:
        # Derivar nombre base: "test1_in" → "test1"
        base_id       = ruta_entrada.stem.replace("_in", "")
        ruta_output   = DIR_OUTPUT / f"{base_id}_out.txt"
        salida_esperada = leer_salida_esperada(ruta_output)
        costo_output  = salida_esperada[0] if salida_esperada is not None else None

        # Leer instancia
        try:
            finca = leer_instancia(ruta_entrada)
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo leer {ruta_entrada.name}: {e}")
            continue

        n = len(finca)

        # ── Leer costo óptimo (roPD) desde el archivo precalculado ───────────
        # El resultado de PD ya está en data/output/*_out.txt; se usa
        # directamente en lugar de volver a ejecutar el algoritmo.
        if salida_esperada is None:
            print(f"[ADVERTENCIA] No se encontró {ruta_output.name}; "
                  f"se omite la instancia {ruta_entrada.name}.")
            continue

        costo_optimo = salida_esperada[0]

        # ── Ejecutar cada heurística ──────────────────────────────────────────
        resultados_instancia: List[Dict[str, Any]] = []

        for nombre_algo, funcion_algo in ALGORITMOS_BENCHMARK:
            try:
                res = ejecutar_algoritmo(nombre_algo, funcion_algo, finca)
            except Exception as e:
                res = {
                    "nombre"    : nombre_algo,
                    "orden"     : [],
                    "costo"     : -1,
                    "tiempo_ms" : 0.0,
                }
                print(f"  [ERROR] {nombre_algo} en {ruta_entrada.name}: {e}")

            gap        = calcular_gap(res["costo"], costo_optimo)
            es_optimo  = (res["costo"] == costo_optimo)

            resultados_instancia.append(res)
            acumulados[nombre_algo].append({
                "gap"       : gap,
                "tiempo_ms" : res["tiempo_ms"],
                "es_optimo" : es_optimo,
            })

        # ── Imprimir tabla de esta instancia ──────────────────────────────────
        imprimir_tabla_instancia(
            nombre_instancia = ruta_entrada.name,
            n_tablones       = n,
            resultados       = resultados_instancia,
            costo_optimo     = costo_optimo,
            costo_output     = costo_output,
        )

    # ── Resumen global ────────────────────────────────────────────────────────
    imprimir_resumen_global(acumulados)

    print(f"\n{'═'*72}")
    print("  Benchmark completado.")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()