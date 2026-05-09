"""
Utilidades para el manejo del estado de tablones mediante Tuplas
"""


"""
====================================================================
REPRESENTACIÓN INTERNA: TUPLA DE ÍNDICES PENDIENTES
====================================================================
Para llevar el control de qué tablones faltan por regar, usamos una
tupla inmutable de enteros, donde cada elemento representa el ÍNDICE
de un tablón.

  Ejemplo con 4 tablones, todos pendientes:  (0, 1, 2, 3)
  Después de regar el tablón 1:              (0, 2, 3)
  Sin tablones pendientes (caso base):       ()

La principal ventaja de este enfoque matemático es:
  - Legibilidad estructurada.
  - Al ser Hashable, es ideal como clave para diccionarios en la 
    Programación Dinámica (memorización de estados).
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
    # Forma mucho más limpia y humana de eliminar de una tupla sin usar ciclos for
    pos = pendientes.index(idx_tablon)
    return pendientes[:pos] + pendientes[pos+1:]


def tablones_pendientes_en(pendientes: tuple, total_tablones: int) -> tuple:
    """
    Retorna los índices de tablones que aún están pendientes.

    ENTRADAS:
    ----------
    pendientes : tuple
        Tupla con los índices de tablones aún pendientes de riego.
    total_tablones : int
        Cantidad total de tablones.

    SALIDAS:
    ----------
    tuple
        Secuencia de índices correspondientes a los tablones sin regar.
    """
    return pendientes


def estado_inicial_pendientes(total_tablones: int) -> tuple:
    """
    Genera el estado inmutable inicial donde TODOS los tablones están pendientes.
    Ejemplo para 4 tablones -> (0, 1, 2, 3)

    ENTRADAS:
    ----------
    total_tablones : int
        Cantidad total de tablones en la finca.

    SALIDAS:
    ----------
    tuple
        Tupla con los índices 0..total_tablones-1, todos listos para ser iterados.
    """
    return tuple(range(total_tablones))
