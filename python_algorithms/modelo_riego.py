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

from tablon import construir_tablones
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
            # (cuando hay múltiples órdenes con el mismo costoo, se elige el lexicográficamente mayor)
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
    Algoritmo Voraz con Método Piloto (Lookahead) y Heurística WMDD.

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
          heurístico decidido para minimizar el costo.
        - costo_final: El valor entero del costo total alcanzado por la heurística.

    LÓGICA DEL ALGORITMO:
    ----------------------
    Evita la "miopía" clásica de los algoritmos voraces evaluando no solo el 
    costo inmediato, sino el "daño en cadena" proyectado sobre el resto de la finca.
    
    1. En cada etapa, toma a cada tablón candidato y calcula su costo inmediato.
    2. Aplica el "Método Piloto" (Simulación Lookahead): Avanza el tiempo simulando 
       que el candidato fue elegido.
    3. Para simular el impacto en el resto de los tablones pendientes, los ordena 
       rápidamente usando la heurística WMDD (Weighted Modified Due Date). Esta 
       regla penaliza severamente los tablones con alta prioridad y poco margen de 
       supervivencia frente al tiempo proyectado.
    4. Suma el costo inmediato y el costo del escenario futuro simulado para 
       obtener un 'score_total'.
    5. En caso de empates en el score, desempata de forma lexicográfica DESCENDENTE 
       (elige el tablón con el índice mayor) para mantener consistencia con los 
       algoritmos exactos.
    6. Selecciona de forma irrevocable el tablón con el menor 'score_total' y 
       avanza al siguiente turno.

    ANÁLISIS DE COMPLEJIDAD:
    -------------------------
    - COMPLEJIDAD TEÓRICA: O(n^3 log n)
    - COMPLEJIDAD REAL: O(n^3 log n)
    - JUSTIFICACIÓN: El algoritmo ejecuta un bucle principal para tomar 'n' 
      decisiones. Por cada decisión, evalúa hasta 'n' candidatos posibles. 
      Para cada candidato, simula el futuro ordenando los tablones restantes, 
      lo cual toma O(n log n), y luego suma linealmente sus costos O(n). 
      El costo dominante es n * n * (n log n) = O(n^3 log n). 
      Esta complejidad le permite escalar fluidamente a cientos de tablones en 
      fracciones de segundo, sin requerir la memoria exponencial O(2^n) de la 
      Programación Dinámica, manteniendo un margen de error mínimo respecto al óptimo.
    """
    n = len(finca)
    if n == 0:
        return [], 0
        
    tablones = construir_tablones(finca)
    pendientes = list(range(n))
    tiempo_actual = 0
    orden_final = []
    costo_total = 0
    
    while pendientes:
        mejor_idx = -1
        mejor_score = float('inf')
        
        for idx in pendientes:
            tab_i = tablones[idx]
            costo_i_ahora = calcular_costo_tablon(tab_i, tiempo_actual)
            
            # --- MÉTODO PILOTO: SIMULACIÓN DEL HORIZONTE COMPLETO ---
            t_sim = tiempo_actual + tab_i.tiempo_regado
            resto = [j for j in pendientes if j != idx]
            
            # Heurística WMDD (Weighted Modified Due Date)
            resto_ordenado = sorted(resto, key=lambda j: 
                max(
                    tablones[j].tiempo_supervivencia - tablones[j].tiempo_regado, 
                    t_sim + tablones[j].tiempo_regado
                ) / tablones[j].prioridad
            )
            
            # Simulamos el costo en cadena para el resto de la finca
            costo_futuro = 0
            t_temp = t_sim
            for j in resto_ordenado:
                costo_futuro += calcular_costo_tablon(tablones[j], t_temp)
                t_temp += tablones[j].tiempo_regado
                
            # Métrica maestra de decisión
            score_total = costo_i_ahora + costo_futuro
            
            # Búsqueda del menor daño global
            if score_total < mejor_score:
                mejor_score = score_total
                mejor_idx = idx
            elif score_total == mejor_score:
                # Desempate lexicográfico DESCENDENTE para consistencia con FB y PD
                if idx > mejor_idx:
                    mejor_idx = idx
                    
        # --- APLICAR DECISIÓN VORAZ IRREVOCABLE ---
        tab_elegido = tablones[mejor_idx]
        costo_total += calcular_costo_tablon(tab_elegido, tiempo_actual)
        tiempo_actual += tab_elegido.tiempo_regado
        
        orden_final.append(mejor_idx)
        pendientes.remove(mejor_idx)
        
    return orden_final, costo_total

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