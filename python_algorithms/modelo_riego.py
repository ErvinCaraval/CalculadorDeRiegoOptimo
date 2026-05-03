"""
Módulo de Algoritmos para el Problema del Riego Óptimo
=======================================================
Este módulo contiene tres enfoques algorítmicos para resolver el problema 
de programación de riego, optimizando el costo total basado en la prioridad 
y supervivencia de los tablones.

Implementaciones incluidas:
  1. roFB: Fuerza Bruta (Exacto, exhaustivo).
  2. roV:  Algoritmo Voraz con Rollout (Heurístico, alta calidad).
  3. roPD: Programación Dinámica (Exacto, eficiente en espacio de estados).
"""

import sys
sys.dont_write_bytecode = True
sys.setrecursionlimit(100_000)

from typing import List, Tuple, Dict

from tablon import Tablon, construir_tablones
from costo_tablon import calcular_costo_tablon
from utils_bits import (
    bitmask_todos_pendientes,
    marcar_tablon_como_regado,
    tablones_pendientes_en,
)


# ──────────────────────────────────────────────────────────────────────
# Algoritmo 1: Fuerza Bruta (roFB)
# ──────────────────────────────────────────────────────────────────────

def roFB(finca: List[Tuple[int, int, int, int]]) -> Tuple[List[int], int]:
    """
    Implementación por Fuerza Bruta para encontrar el orden óptimo de riego.

    ENTRADAS:
    ----------
    finca : List[Tuple[int, int, int, int]]
        Lista de tablones, donde cada tupla contiene:
        - tc: Tiempo de crecimiento (no afecta el costo directamente).
        - ts: Tiempo de supervivencia (límite antes de empezar a perder valor).
        - tr: Tiempo de regado (duración de la tarea).
        - cp: Coeficiente de prioridad (peso del tablón en el costo).

    SALIDAS:
    ----------
    Tuple[List[int], int]
        - orden_final: Una lista con los índices de los tablones en el orden 
          en que deben ser regados para minimizar el costo.
        - costo_final: El valor entero del costo total mínimo alcanzado.

    LÓGICA DEL ALGORITMO:
    ----------------------
    El algoritmo genera todas las permutaciones posibles de riego mediante 
    recursión. En cada nivel de la recursión:
    1. Itera sobre cada tablón que aún no ha sido regado (pendientes).
    2. Calcula el costo de regar ese tablón en el tiempo actual.
    3. Llama recursivamente para resolver el problema con los tablones restantes.
    4. Compara todos los resultados y selecciona el camino que minimice 
       la suma total de costos.
    Al no usar memoria, garantiza la exploración de los n! caminos.

    ANÁLISIS DE COMPLEJIDAD:
    -------------------------
    - COMPLEJIDAD TEÓRICA: O(n!)
    - COMPLEJIDAD REAL: O(n!)
    - JUSTIFICACIÓN: Para n tablones, hay n opciones para el primero, (n-1) 
      para el segundo, y así sucesivamente. No hay poda ni memorización, 
      por lo que se visitan todas las hojas del árbol de decisión.
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)

    def explorar_sin_memo(pendientes: int, tiempo_actual: int) -> Tuple[int, List[int]]:
        if pendientes == 0:
            return 0, []

        mejor_costo = float('inf')
        mejor_orden: List[int] = []

        for idx in tablones_pendientes_en(pendientes, n):
            tab = tablones[idx]
            tr  = tab.tiempo_regado

            # Cálculo del costo individual
            costo_de_regar_idx_ahora = calcular_costo_tablon(tab, tiempo_actual)

            # Exploración profunda (Recursión)
            costo_del_resto, orden_del_resto = explorar_sin_memo(
                marcar_tablon_como_regado(pendientes, idx),
                tiempo_actual + tr,
            )

            costo_total = costo_de_regar_idx_ahora + costo_del_resto

            # Selección del mínimo global con desempate lexicográfico DESCENDENTE
            # (cuando hay múltiples órdenes con el mismo costo, se elige el lexicográficamente mayor)
            orden_candidata = [idx] + orden_del_resto
            if (costo_total < mejor_costo or 
                (costo_total == mejor_costo and orden_candidata > mejor_orden)):
                mejor_costo = costo_total
                mejor_orden = orden_candidata

        return mejor_costo, mejor_orden

    todos_pendientes = bitmask_todos_pendientes(n)
    costo_final, orden_final = explorar_sin_memo(todos_pendientes, tiempo_actual=0)
    return orden_final, costo_final


# ──────────────────────────────────────────────────────────────────────
# Algoritmo 2: Voraz (roV)
# ──────────────────────────────────────────────────────────────────────

def roV(finca: List[Tuple[int, int, int, int]]) -> Tuple[List[int], int]:
    """
    Algoritmo Voraz Recursivo (con Simulación Heurística Avanzada).

    ENTRADAS y SALIDAS:
    -------------------
    finca : Lista de tuplas (tc, ts, tr, cp).
    Retorna (orden_final, costo_total).

    LÓGICA DEL ALGORITMO (Voraz Puro con Lookahead):
    -------------------------------------------------
    El algoritmo toma decisiones irrevocables paso a paso mediante recursión:
      1. Caso base: Si no hay pendientes, retorna costo 0.
      2. Evaluación: Para cada tablón, simula "qué pasaría si lo elijo". 
         El futuro se simula asumiendo que el resto se regará siguiendo una 
         heurística estática estricta (Urgencia -> Prioridad -> Rapidez).
      3. Elección: Se selecciona el tablón cuyo impacto proyectado 
         (costo inmediato + costo del futuro simulado) sea el mínimo absoluto.
      4. Recursión: Se compromete con esa decisión y avanza al siguiente paso.

    MEJORA DE PRECISIÓN (Heurística Multicriterio):
    ------------------------------------------------
    Para que la simulación sea muy precisa, el ordenamiento de los tablones 
    restantes no solo mira cuándo se marchitan (ts - tr), sino que da peso 
    a la prioridad (cp). Esto acerca drásticamente el resultado al óptimo.

    ANÁLISIS DE COMPLEJIDAD:
    ------------------------
    - COMPLEJIDAD TEÓRICA ESPERADA: O(n log n)
    - COMPLEJIDAD REAL: O(n³ log n)
      Justificación: La recursión tiene una profundidad de n. En cada nivel, 
      iteramos sobre hasta n candidatos. Por cada candidato, la simulación 
      ordena hasta n elementos restantes con sorted(), lo que toma O(n log n).
      Total: n * n * (n log n) = O(n³ log n). 
      Se asume esta complejidad deliberadamente para maximizar la cercanía al 
      óptimo global dentro del paradigma voraz.
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)
    
    # ── MEJORA AQUI: Heurística multicriterio para la simulación ──
    # 1. Menor margen de supervivencia (ts - tr)
    # 2. Mayor prioridad (-cp) para que los más valiosos vayan primero
    # 3. Menor tiempo de regado (tr) como último desempate
    clave_orden = [
        (t.tiempo_supervivencia - t.tiempo_regado, -t.prioridad, t.tiempo_regado) 
        for t in tablones
    ]

    def paso_voraz(pendientes: List[int], tiempo_actual: int) -> Tuple[List[int], int]:
        # 1. CASO BASE
        if not pendientes:
            return [], 0

        mejor_idx = -1
        mejor_impacto_proyectado = float('inf')

        # 2. EVALUACIÓN Y SIMULACIÓN
        for i in pendientes:
            tab_i = tablones[i]
            costo_ahora = calcular_costo_tablon(tab_i, tiempo_actual)
            t_simulado = tiempo_actual + tab_i.tiempo_regado

            # Simular el futuro ordenando los restantes con la clave avanzada
            resto = sorted([j for j in pendientes if j != i], key=lambda x: clave_orden[x])
            
            costo_futuro = 0
            for j in resto:
                tab_j = tablones[j]
                costo_futuro += calcular_costo_tablon(tab_j, t_simulado)
                t_simulado += tab_j.tiempo_regado

            impacto_total = costo_ahora + costo_futuro

            if impacto_total < mejor_impacto_proyectado:
                mejor_impacto_proyectado = impacto_total
                mejor_idx = i

        # 3. RECURSIÓN Y AVANCE IRREVOCABLE
        tab_elegido = tablones[mejor_idx]
        costo_real_de_este_paso = calcular_costo_tablon(tab_elegido, tiempo_actual)
        
        siguientes_pendientes = [p for p in pendientes if p != mejor_idx]
        
        orden_resto, costo_resto = paso_voraz(
            siguientes_pendientes, 
            tiempo_actual + tab_elegido.tiempo_regado
        )

        # 4. CONSTRUIR SOLUCIÓN
        return [mejor_idx] + orden_resto, costo_real_de_este_paso + costo_resto

    return paso_voraz(list(range(n)), 0)


# ──────────────────────────────────────────────────────────────────────
# Algoritmo 3: Programación Dinámica (roPD)
# ──────────────────────────────────────────────────────────────────────

def roPD(finca: List[Tuple[int, int, int, int]]) -> Tuple[List[int], int]:
    """
    Algoritmo de Programación Dinámica con Memorización (Top-Down).

    ENTRADAS:
    ----------
    finca : List[Tuple[int, int, int, int]]
        (Igual que en roFB) Datos de los tablones (tc, ts, tr, cp).

    SALIDAS:
    ----------
    Tuple[List[int], int]
        - orden_final: El orden óptimo absoluto encontrado.
        - costo_final: El costo mínimo absoluto garantizado.

    LÓGICA DEL ALGORITMO:
    ----------------------
    Utiliza el principio de optimalidad de Bellman para evitar cálculos redundantes:
    1. Define un estado como (pendientes, tiempo_actual).
    2. Antes de resolver un subproblema, verifica en un diccionario (memo) 
       si ya ha sido resuelto para ese conjunto exacto de tablones pendientes.
    3. Si es nuevo, explora las opciones (similar a FB) pero guarda el 
       mejor resultado encontrado para ese estado.
    4. Dado que el tiempo_actual es determinista según los tablones ya regados, 
       el número de estados se reduce drásticamente de n! a 2^n.

    ANÁLISIS DE COMPLEJIDAD:
    -------------------------
    - COMPLEJIDAD TEÓRICA DE TIEMPO: O(n * 2^n)
    - COMPLEJIDAD REAL DE ESPACIO: O(2^n)
    - JUSTIFICACIÓN:
        Existen 2^n subconjuntos posibles de tablones (estados del bitmask). 
        Para cada estado, realizamos una transición de costo O(n) al iterar 
        los posibles tablones a regar. Esto es exponencial, pero mucho 
        más eficiente que el factorial de la Fuerza Bruta.
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)
    memo: Dict[Tuple[int, int], Tuple[int, List[int]]] = {}

    def resolver_con_memo(pendientes: int, tiempo_actual: int) -> Tuple[int, List[int]]:
        if pendientes == 0:
            return 0, []

        clave_estado = (pendientes, tiempo_actual)
        if clave_estado in memo:
            return memo[clave_estado]

        mejor_costo = float('inf')
        mejor_orden: List[int] = []

        for idx in tablones_pendientes_en(pendientes, n):
            tab = tablones[idx]
            tr  = tab.tiempo_regado

            costo_de_regar_idx_ahora = calcular_costo_tablon(tab, tiempo_actual)

            costo_del_resto, orden_del_resto = resolver_con_memo(
                marcar_tablon_como_regado(pendientes, idx),
                tiempo_actual + tr,
            )

            costo_total = costo_de_regar_idx_ahora + costo_del_resto

            # Desempate lexicográfico DESCENDENTE para consistencia entre FB y PD
            orden_candidata = [idx] + orden_del_resto
            if (costo_total < mejor_costo or 
                (costo_total == mejor_costo and orden_candidata > mejor_orden)):
                mejor_costo = costo_total
                mejor_orden = orden_candidata

        memo[clave_estado] = (mejor_costo, mejor_orden)
        return memo[clave_estado]

    todos_pendientes = bitmask_todos_pendientes(n)
    costo_final, orden_final = resolver_con_memo(todos_pendientes, tiempo_actual=0)
    return orden_final, costo_final