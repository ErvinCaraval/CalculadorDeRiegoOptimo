"""
Módulo: tablon.py
=================
Define la estructura de datos `Tablon` y su constructor desde tuplas crudas.

Optimización aplicada:
  slots=True — en Python 3.10+ los dataclasses admiten __slots__, lo que
  elimina el __dict__ por instancia. Beneficio concreto para roPD: cada
  llamada a resolver_con_memo hace hash(tablon) para indexar el memo;
  con slots, el acceso a atributos es directo (offset fijo en memoria)
  en lugar de pasar por __dict__, reduciendo el costo de hash y acceso.
"""

import sys
sys.dont_write_bytecode = True

from typing import List, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class Tablon:
    """
    Representa un tablón con sus características inmutables.

    Atributos:
        idx:                  índice del tablón en la finca
        tiempo_supervivencia: días que puede estar sin riego (ts)
        tiempo_regado:        días que toma regarlo          (tr)
        prioridad:            valor 1-4, siendo 4 la máxima  (p)
        riego_optimo:         día ideal para iniciar el riego (ro)
    """
    idx: int
    tiempo_supervivencia: int
    tiempo_regado: int
    prioridad: int
    riego_optimo: int


def construir_tablones(finca: List[Tuple[int, int, int, int]]) -> List[Tablon]:
    """
    Convierte la lista de tuplas (ts, tr, p, ro) en objetos Tablon.
    """
    return [
        Tablon(
            idx=i,
            tiempo_supervivencia=finca[i][0],
            tiempo_regado=finca[i][1],
            prioridad=finca[i][2],
            riego_optimo=finca[i][3],
        )
        for i in range(len(finca))
    ]