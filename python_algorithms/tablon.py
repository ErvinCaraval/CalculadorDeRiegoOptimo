"""
Módulo: tablon.py
=================
Define la estructura de datos `Tablon` y su constructor desde tuplas crudas.
"""


from typing import List, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class Tablon:
    """
    Representa un tablón con sus características inmutables.

    Atributos:
        tiempo_supervivencia: días que puede estar sin riego (ts)
        tiempo_regado:        días que toma regarlo          (tr)
        prioridad:            valor 1-4, siendo 4 la máxima  (p)
        riego_optimo:         día ideal para iniciar el riego (ro)
    """
    tiempo_supervivencia: int
    tiempo_regado: int
    prioridad: int
    riego_optimo: int


def construir_tablones(finca: List[Tuple[int, int, int, int]]) -> List[Tablon]:
    """
    Convierte la lista de tuplas (ts, tr, p, ro) en objetos Tablon.

    ENTRADAS:
    ----------
    finca : List[Tuple[int, int, int, int]]
        Lista de tuplas con los datos de cada tablón (ts, tr, p, ro).

    SALIDAS:
    ----------
    List[Tablon]
        Lista de objetos inmutables tipo Tablon.
    """
    return [
        Tablon(
            tiempo_supervivencia=finca[i][0],
            tiempo_regado=finca[i][1],
            prioridad=finca[i][2],
            riego_optimo=finca[i][3],
        )
        for i in range(len(finca))
    ]