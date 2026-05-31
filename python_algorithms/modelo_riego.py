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
import math

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
        - ts: Tiempo de supervivencia (límite antes de empezar a perder valor).
        - tr: Tiempo de regado (duración de la tarea).
        - p:  Prioridad del tablón (peso del tablón en el costo).
        - ro: Tiempo de riego óptimo (instante ideal para iniciar el riego sin penalidad).

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


def roV(finca: List[Tuple[int, int, int, int]], k_slack: float = 2.0, k_ro: float = 1.0) -> Tuple[List[int], int]:
    """
    Implementación de una Heurística Voraz Pura para la secuenciación de riego.

    ENTRADAS:
    ----------
    finca : List[Tuple[int, int, int, int]]
        Lista de tablones, donde cada tupla contiene:
        - ts: Tiempo de supervivencia (límite antes de empezar a perder valor).
        - tr: Tiempo de regado (duración del proceso de riego).
        - p: Prioridad del tablón (peso económico o importancia).
        - ro: Riego óptimo (momento ideal recomendado para iniciar el riego).
    k_slack : float, opcional
        Parámetro de escala para la holgura de supervivencia (por defecto 2.0).
    k_ro : float, opcional
        Parámetro de escala para la ventana de riego óptimo (por defecto 1.0).

    SALIDAS:
    -------
    Tuple[List[int], int]
        - orden: Lista de enteros con la secuencia de riego decidida localmente.
        - costo_total_finca: Costo real acumulado de la secuencia obtenida.

    LÓGICA DEL ALGORITMO:
    ---------------------
    El algoritmo implementa un enfoque constructivo miope guiado por un índice de despacho 
    continuo adaptado de la regla ATCS (Apparent Tardiness Cost with Setup). En cada iteración, 
    el algoritmo evalúa los elementos del conjunto de candidatos pendientes calculando 
    dinámicamente un score. Este puntaje pondera tres componentes locales respecto al tiempo 
    actual 't': la eficiencia de la regla WSPT (prioridad/tiempo de riego), una penalización 
    exponencial por espera óptima insatisfecha, y una penalización exponencial basada en la 
    holgura límite de supervivencia del cultivo. El candidato con el score máximo es seleccionado 
    de forma irrevocable, integrándose a la secuencia y mutando el estado del sistema al 
    avanzar el reloj global, eliminando la necesidad de bifurcaciones condicionales o 
    simulaciones exhaustivas de subproblemas futuros.

    ANÁLISIS DE COMPLEJIDAD:
    ------------------------
    1. Complejidad Temporal:
       - El Paso 1 realiza la conversión de datos inicial tomando un tiempo de O(n).
       - El Paso 2 calcula el arreglo estático de desempate recorriendo los datos en O(n).
       - El Paso 3 ejecuta un bucle principal mientras queden elementos candidatos. Este ciclo 
         se repite exactamente n veces. Dentro de cada iteración, se evalúa el score de todos los 
         elementos que aún permanecen en el conjunto de pendientes, realizando comparaciones 
         continuas en O(1) por elemento. Esto describe una sumatoria decreciente de tamaño 
         n + (n-1) + (n-2) + ... + 1, equivalente a un comportamiento cuadrático. Por lo tanto, 
         el tiempo de ejecución en el peor de los casos y caso promedio está acotado por O(n^2).
    2. Complejidad Espacial:
       - Las estructuras de control auxiliares almacenan el conjunto de pendientes, el orden 
         resultante y el arreglo de ratios estáticos de tamaño proporcional al número de elementos 
         de entrada. No se derivan pilas de recursión ni tablas multidimensionales de estados 
         mapeados. Por consiguiente, la complejidad en espacio de memoria se mantiene acotada 
         linealmente por O(n).
    """
    n = len(finca)
    if n == 0:
        return [], 0

    # Convertimos la lista de tuplas en objetos Tablon oficiales del proyecto
    # para que las funciones como 'calcular_costo_tablon' funcionen sin reventar.
    tablones = construir_tablones(finca)
    
    # Manejo del estado local irrevocable
    pendientes = set(range(n)) 
    orden = []
    tiempo_actual = 0
    costo_total_finca = 0

    # Índices estáticos para desempates deterministas basados en WSPT
    wspt_ratios = [t.prioridad / t.tiempo_regado for t in tablones]

    while pendientes:
        mejor_idx = -1
        mejor_score = float("-inf")

        for j in pendientes:
            tab_j = tablones[j]
            ts_j = tab_j.tiempo_supervivencia
            tr_j = tab_j.tiempo_regado
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
            espera = max(0.0, ro_j - t)
            factor_ro = math.exp(-espera / (k_ro * tr_j))
            
            # 3. Factor de Holgura (Urgencia de Supervivencia)
            holgura = max(0.0, ts_j - t - tr_j)
            factor_soltura = math.exp(-holgura / (k_slack * tr_j))
            
            # 4. ÍNDICE DE DESPACHO ÚNICO Y CONTINUO (f(j, t))
            score = peso * factor_ro * factor_soltura
            
            # ─────────────────────────────────────────────────────────

            # Selección del máximo local con desempate determinista riguroso
            if score > mejor_score:
                mejor_score = score
                mejor_idx = j
            elif score == mejor_score:
                if wspt_ratios[j] > wspt_ratios[mejor_idx]:
                    mejor_idx = j
                elif wspt_ratios[j] == wspt_ratios[mejor_idx] and j > mejor_idx:
                    mejor_idx = j

        # Calculamos el costo REAL usando el objeto Tablon esperado por el proyecto
        costo_now = calcular_costo_tablon(tablones[mejor_idx], tiempo_actual)

        # Elección irrevocable (Escogencia Voraz)
        orden.append(mejor_idx)
        costo_total_finca += costo_now
        tiempo_actual += tablones[mejor_idx].tiempo_regado 
        
        pendientes.remove(mejor_idx)

    return orden, int(costo_total_finca)

# ──────────────────────────────────────────────────────────────────────
# Algoritmo 3: Programación Dinámica (roPD)
# ──────────────────────────────────────────────────────────────────────

def roPD(finca: List[Tuple[int, int, int, int]]) -> Tuple[List[int], int]:
    """
    Algoritmo de Programación Dinámica (Top-Down con Memorización).

    ENTRADAS:
    ----------
    finca : List[Tuple[int, int, int, int]]
        (Igual que en roFB) Datos de los tablones (ts, tr, p, ro).

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
