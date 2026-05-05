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


def calcular_costo_tablon(tablon: Tablon, tiempo_inicio_riego: int, nivel_caso: int = 1) -> int:
    """
    Calcula el costo de riego para un tablón según las reglas del enunciado.
    Implementación recursiva a través de los niveles de evaluación (Casos 1, 2 y 3).

    ENTRADAS:
    ----------
    tablon : Tablon
        Instancia inmutable con los datos del tablón a regar.
    tiempo_inicio_riego : int
        Día/tiempo en el que se comienza a regar este tablón.
    nivel_caso : int
        Controla la recursión para evaluar el caso correspondiente.

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
    # Caso 1 – Riego en tiempo óptimo
    if nivel_caso == 1:
        if tiempo_inicio_riego == tablon.riego_optimo:
            return tablon.tiempo_supervivencia - (tiempo_inicio_riego + tablon.tiempo_regado)
        # Si no cumple, exploramos recursivamente el Caso 2
        return calcular_costo_tablon(tablon, tiempo_inicio_riego, nivel_caso + 1)

    # Caso 2 – Riego tardío sin déficit hídrico
    if nivel_caso == 2:
        limite_sin_deficit = tablon.tiempo_supervivencia - tablon.tiempo_regado
        if limite_sin_deficit >= tiempo_inicio_riego:
            return 2 * (tablon.tiempo_supervivencia - (tiempo_inicio_riego + tablon.tiempo_regado))
        # Si no cumple, exploramos recursivamente el Caso 3
        return calcular_costo_tablon(tablon, tiempo_inicio_riego, nivel_caso + 1)

    # Caso 3 – Déficit hídrico (Caso base final por descarte)
    return 2 * tablon.prioridad * ((tiempo_inicio_riego + tablon.tiempo_regado) - tablon.tiempo_supervivencia)