"""
Utilidades para el manejo del estado de tablones mediante Tuplas
"""
from typing import Generator

"""
====================================================================
REPRESENTACIÓN INTERNA: TUPLA DE ÍNDICES PENDIENTES
====================================================================
En lugar de un número entero con bits, usamos una tupla de enteros
donde cada elemento es el ÍNDICE de un tablón que aún falta regar.

  Ejemplo con 4 tablones, todos pendientes:  (0, 1, 2, 3)
  Después de regar el tablón 1:              (0, 2, 3)
  Sin tablones pendientes (caso base):       ()

Las ventajas frente al bitmask son:
  - Más legible e intuitiva de depurar.
  - Hashable (puede usarse como clave de diccionario), igual que el
    int original, por lo que la memoización de roPD sigue funcionando.

TRUCO 1: ¿Este tablón necesita agua? -> idx_tablon in pendientes
--------------------------------------------------------------------
Simplemente verificamos si el índice está presente en la tupla.
Es equivalente al (pendientes >> i) & 1 de la versión bitmask.

TRUCO 2: ¡Listo, ya regué este tablón! -> tuple(i for i in pendientes if i != idx)
--------------------------------------------------------------------
Construimos una nueva tupla excluyendo el índice del tablón regado.
Es equivalente al pendientes ^ (1 << i) de la versión bitmask.
====================================================================
"""


def tablon_esta_pendiente(pendientes: tuple, idx_tablon: int) -> bool:
    """
    Retorna True si el tablón `idx_tablon` aún no ha sido regado.

    ENTRADAS:
    ----------
    pendientes : tuple
        Tupla con los índices de tablones aún pendientes de riego.
    idx_tablon : int
        Índice del tablón a consultar.

    SALIDAS:
    ----------
    bool
        True si el índice está en la tupla, False si ya fue regado.
    """
    return idx_tablon in pendientes


def marcar_tablon_como_regado(pendientes: tuple, idx_tablon: int) -> tuple:
    """
    Retorna una nueva tupla con el tablón `idx_tablon` eliminado
    (es decir, marcado como ya regado).

    ENTRADAS:
    ----------
    pendientes : tuple
        Tupla con los índices de tablones aún pendientes de riego.
    idx_tablon : int
        Índice del tablón que se acaba de regar.

    SALIDAS:
    ----------
    tuple
        Nueva tupla sin el índice del tablón recién regado.
    """
    return tuple(i for i in pendientes if i != idx_tablon)


def tablones_pendientes_en(pendientes: tuple, total_tablones: int) -> Generator[int, None, None]:
    """
    Generador que emite los índices de tablones que aún están pendientes.

    ENTRADAS:
    ----------
    pendientes : tuple
        Tupla con los índices de tablones aún pendientes de riego.
    total_tablones : int
        Cantidad total de tablones (mantenido por compatibilidad de firma,
        no se usa internamente ya que la tupla contiene solo los pendientes).

    SALIDAS:
    ----------
    Generator[int, None, None]
        Secuencia de índices correspondientes a los tablones sin regar.
    """
    for idx in pendientes:
        yield idx


def bitmask_todos_pendientes(total_tablones: int) -> tuple:
    """
    Retorna el estado inicial donde TODOS los tablones están pendientes.
    Ejemplo: 4 tablones -> (0, 1, 2, 3)

    El nombre se conserva por compatibilidad con modelo_riego.py,
    aunque la representación ya no es un bitmask sino una tupla.

    ENTRADAS:
    ----------
    total_tablones : int
        Cantidad total de tablones en la finca.

    SALIDAS:
    ----------
    tuple
        Tupla con los índices 0..total_tablones-1, todos pendientes.
    """
    return tuple(range(total_tablones))
