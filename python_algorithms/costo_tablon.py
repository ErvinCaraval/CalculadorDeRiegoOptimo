"""
Módulo: costo_tablon.py
=======================
Función de costo para un tablón según las reglas del enunciado.

Sin @lru_cache: la función realiza 3 comparaciones y 1 multiplicación.
El overhead de hash(Tablon) + dict lookup del cache es 2× más costoso
que calcular el resultado directamente.
"""

import sys
sys.dont_write_bytecode = True

from tablon import Tablon


def calcular_costo_tablon(tablon: Tablon, tiempo_inicio_riego: int) -> int:
    """
    Calcula el costo de riego para un tablón según las reglas del enunciado.
    Evaluación secuencial de los tres casos posibles de penalización.

    ENTRADAS:
    ----------
    tablon : Tablon
        Instancia inmutable con los datos del tablón a regar.
    tiempo_inicio_riego : int
        Día/tiempo en el que se comienza a regar este tablón.

    SALIDAS:
    ----------
    int
        Costo penalizado calculado para este tablón.

    REGLAS DE COSTO:
    -----------------
    Caso 1 – Riego en tiempo óptimo (t_inicio == ro):
        costo = ts − (t_inicio + tr)
        Penalidad mínima: el tablón fue regado en el momento ideal.

    Caso 2 – Riego tardío pero sin déficit hídrico (ts − tr ≥ t_inicio > ro):
        costo = 2 × (ts − (t_inicio + tr))
        Penalidad moderada: no hay estrés hídrico pero hay retraso.

    Caso 3 – Déficit hídrico crítico (t_inicio + tr > ts):
        costo = 2 × p × ((t_inicio + tr) − ts)
        Penalidad severa: proporcional a la prioridad del tablón y días en déficit.
    """
    tiempo_fin = tiempo_inicio_riego + tablon.tiempo_regado
    limite_sin_deficit = tablon.tiempo_supervivencia - tablon.tiempo_regado
    
    # Caso 1: Riego exacto en tiempo óptimo
    if tiempo_inicio_riego == tablon.riego_optimo:
        return tablon.tiempo_supervivencia - tiempo_fin
    
    # Caso 2: Riego tardío sin déficit hídrico
    if tiempo_inicio_riego <= limite_sin_deficit:
        return 2 * (tablon.tiempo_supervivencia - tiempo_fin)
    
    # Caso 3: Déficit hídrico crítico (caso base por descarte)
    return 2 * tablon.prioridad * (tiempo_fin - tablon.tiempo_supervivencia)