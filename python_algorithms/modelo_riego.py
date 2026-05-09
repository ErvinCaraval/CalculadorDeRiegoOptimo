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

from typing import List, Tuple, Dict, Any

from tablon import construir_tablones
from costo_tablon import calcular_costo_tablon
from utils_estado import (
    estado_inicial_pendientes,
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
    - COMPLEJIDAD TEMPORAL: O(n!)
    - COMPLEJIDAD ESPACIAL: O(n)
    - JUSTIFICACIÓN TEMPORAL: Para n tablones, hay n opciones para el primero, 
      (n-1) para el segundo, y así sucesivamente. No hay poda ni memorización, 
      por lo que se visitan todas las hojas del árbol de decisión.
    - JUSTIFICACIÓN ESPACIAL: La profundidad máxima del árbol de recursión es n. 
      En cada nivel de la pila de llamadas se almacena un estado temporal de tamaño n. 
      Por lo tanto, la memoria requerida en cualquier instante es puramente lineal O(n).
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)

    def explorar_sin_memo(pendientes: Any, tiempo_actual: int) -> Tuple[int, List[int]]:
        if not pendientes:
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

    todos_pendientes = estado_inicial_pendientes(n)
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
    - COMPLEJIDAD TEMPORAL: O(n^3 log n)
    - COMPLEJIDAD ESPACIAL: O(n)
    - JUSTIFICACIÓN TEMPORAL: El algoritmo ejecuta un bucle principal para tomar 'n' 
      decisiones. Por cada decisión, evalúa hasta 'n' candidatos posibles. 
      Para cada candidato, simula el futuro ordenando los tablones restantes, 
      lo cual toma O(n log n), y luego suma linealmente sus costos O(n). 
      El costo dominante es n * n * (n log n) = O(n^3 log n).
    - JUSTIFICACIÓN ESPACIAL: No usa recursión pesada ni guarda estados exponenciales. 
      Solo mantiene arreglos temporales (listas y tuplas de pendientes) de tamaño máximo 
      'n' a lo largo del proceso. Su consumo de memoria es lineal O(n).
    """
    n = len(finca)
    if n == 0:
        return [], 0
        
    tablones = construir_tablones(finca)
    pendientes = estado_inicial_pendientes(n)
    tiempo_actual = 0
    orden_final = []
    costo_total = 0
    
    while pendientes:
        mejor_idx = -1
        mejor_score = float('inf')
        
        for idx in tablones_pendientes_en(pendientes, n):
            tab_i = tablones[idx]
            costo_i_ahora = calcular_costo_tablon(tab_i, tiempo_actual)
            
            # --- MÉTODO PILOTO: SIMULACIÓN DEL HORIZONTE COMPLETO ---
            t_sim = tiempo_actual + tab_i.tiempo_regado
            
            resto_pendientes = marcar_tablon_como_regado(pendientes, idx)
            resto = list(tablones_pendientes_en(resto_pendientes, n))
            
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
        pendientes = marcar_tablon_como_regado(pendientes, mejor_idx)
        
    return orden_final, costo_total

# ──────────────────────────────────────────────────────────────────────
# Algoritmo 3: Programación Dinámica (roPD)
# ──────────────────────────────────────────────────────────────────────

def roPD(finca: List[Tuple[int, int, int, int]]) -> Tuple[List[int], int]:
    """
    Algoritmo de Programación Dinámica (Top-Down con Memorización).

    ENTRADAS:
    ----------
    finca : List[Tuple[int, int, int, int]]
        (Igual que en roFB) Datos de los tablones (tc, ts, tr, cp).

    SALIDAS:
    ----------
    Tuple[List[int], int]
        - orden_final: El orden óptimo absoluto encontrado.
        - costo_final: El costo mínimo absoluto garantizado.

    LÓGICA DEL ALGORITMO (Los 4 pasos de Programación Dinámica):
    -----------------------------------------------------------------------
    1) Caracterizar la estructura de la solución óptima (subestructura óptima):
       La solución óptima para regar un conjunto de tablones 'P' consiste en 
       elegir un tablón 'idx' para regar ahora, y luego resolver de forma óptima 
       el subproblema con los tablones restantes (P \ {idx}).

    2) Definir recursivamente el valor de la solución óptima:
       Sea C(P, t) el costo óptimo para los tablones pendientes P en el tiempo t:
       C(P, t) = min_{i en P} [ costo_tablon(i, t) + C(P \ {i}, t + tr_i) ]
       Caso base: C(vacío, t) = 0.

    3) Calcular el valor de la solución óptima (algoritmo):
       Calculamos C(P, t) recursivamente y almacenamos los resultados en una 
       tabla/diccionario (memoización) para no recalcular subproblemas. En esta
       fase SOLO calculamos el valor óptimo y guardamos qué decisión se tomó.

    4) Construir la solución óptima (algoritmo):
       A partir de las decisiones guardadas en el paso 3, reconstruimos el 
       camino (el orden de los tablones) que nos llevó al costo óptimo, 
       rastreando los estados desde el inicial hasta el final.

    ANÁLISIS DE COMPLEJIDAD:
    -------------------------
    - COMPLEJIDAD TEMPORAL: O(n * 2^n)
    - COMPLEJIDAD ESPACIAL: O(2^n)
    - JUSTIFICACIÓN TEMPORAL: Existen 2^n subconjuntos posibles de tablones. 
      Para cada estado, realizamos una transición iterando 'n' tablones posibles. 
      Gracias a la memorización, cada estado se calcula solo una vez.
    - JUSTIFICACIÓN ESPACIAL: Los diccionarios ('memo_valor' y 'memo_decision') 
      deben almacenar los resultados óptimos de CADA subproblema visitado. 
      Dado que hay 2^n subproblemas únicos, la memoria crece de forma exponencial O(2^n), 
      lo cual limita su uso en la práctica a ~25 tablones debido al límite de RAM.
    """
    n = len(finca)
    if n == 0:
        return [], 0

    tablones = construir_tablones(finca)
    
    # Tablas para memorización
    memo_valor: Dict[Any, float] = {}
    memo_decision: Dict[Any, int] = {}

    # PASO 3: Calcular el valor de la solución óptima
    def calcular_valor_optimo(pendientes: Any, tiempo_actual: int) -> float:
        # PASO 2 (Caso base): Costo cero si no hay tablones pendientes
        if not pendientes:
            return 0.0

        # Si ya fue calculado, devolvemos el valor óptimo
        if pendientes in memo_valor:
            return memo_valor[pendientes]

        mejor_costo = float('inf')
        mejor_idx = -1

        # Iteramos sobre todos los posibles tablones a elegir
        for idx in tablones_pendientes_en(pendientes, n):
            tab = tablones[idx]
            
            # PASO 1 y 2: Costo de la decisión local + Costo óptimo del subproblema
            costo_local = calcular_costo_tablon(tab, tiempo_actual)
            costo_resto = calcular_valor_optimo(
                marcar_tablon_como_regado(pendientes, idx),
                tiempo_actual + tab.tiempo_regado
            )
            
            costo_total = costo_local + costo_resto

            # Selección del mínimo y desempate lexicográfico DESCENDENTE
            # (Al comparar solo idx > mejor_idx aseguramos el orden descendente global
            # ya que 'idx' es el primer elemento de la secuencia resultante)
            if costo_total < mejor_costo:
                mejor_costo = costo_total
                mejor_idx = idx
            elif costo_total == mejor_costo:
                if idx > mejor_idx:
                    mejor_idx = idx

        # Guardamos el valor óptimo y la decisión (el tablón elegido) para este estado
        memo_valor[pendientes] = mejor_costo
        memo_decision[pendientes] = mejor_idx
        return mejor_costo

    # PASO 4: Construir la solución óptima
    def construir_solucion_optima(pendientes: Any) -> List[int]:
        orden = []
        estado_actual = pendientes
        
        # Recuperamos las decisiones tomadas haciendo 'backtracking' por los estados
        while estado_actual:
            idx_elegido = memo_decision[estado_actual]
            orden.append(idx_elegido)
            estado_actual = marcar_tablon_como_regado(estado_actual, idx_elegido)
            
        return orden

    todos_pendientes = estado_inicial_pendientes(n)
    
    # Ejecutamos el Paso 3 (Sólo calcula el valor óptimo y llena las tablas)
    costo_final = int(calcular_valor_optimo(todos_pendientes, tiempo_actual=0))
    
    # Ejecutamos el Paso 4 (Reconstruye la ruta óptima en base a las decisiones)
    orden_final = construir_solucion_optima(todos_pendientes)
    
    return orden_final, costo_final
