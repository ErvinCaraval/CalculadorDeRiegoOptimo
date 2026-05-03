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
    Caso 1 – Riego en tiempo óptimo:
        costo = ts − (t_inicio + tr)

    Caso 2 – Riego tardío pero sin déficit hídrico (ts − tr ≥ t_inicio):
        costo = 2 × (ts − (t_inicio + tr))

    Caso 3 – Déficit hídrico:
        costo = 2 × p × ((t_inicio + tr) − ts)
    """
    if tiempo_inicio_riego == tablon.riego_optimo:
        return tablon.tiempo_supervivencia - (tiempo_inicio_riego + tablon.tiempo_regado)

    limite_sin_deficit = tablon.tiempo_supervivencia - tablon.tiempo_regado

    if limite_sin_deficit >= tiempo_inicio_riego:
        return 2 * (tablon.tiempo_supervivencia - (tiempo_inicio_riego + tablon.tiempo_regado))

    return 2 * tablon.prioridad * ((tiempo_inicio_riego + tablon.tiempo_regado) - tablon.tiempo_supervivencia)