"""
Utilidades para el manejo de máscaras de bits (Bitmask)
"""
from typing import List, Tuple, Dict


"""
====================================================================
EXPLICACIÓN DE LAS MÁSCARAS DE BITS (BITMASKS) PARA HUMANOS
====================================================================
En lugar de usar listas pesadas, usamos un número entero para 
representar los tablones. Imagina que es un panel de bombillos:
  💡 (1) = ¡Peligro! El tablón falta por regar.
  🌑 (0) = Tranquilo, el tablón ya está regado.

Un estado como 0b1111 significa que los 4 están pendientes (💡💡💡💡).

TRUCO 1: ¿Este tablón necesita agua? -> (pendientes >> i) & 1
--------------------------------------------------------------------
Imagina que los bombillos están en una cinta transportadora:
1. (>> i) : Mueve la cinta 'i' espacios a la derecha hasta que el
            bombillo que nos interesa quede justo enfrente (posición 0).
2. (& 1)  : Nos ponemos un tubo de cartón en el ojo para ignorar el
            resto de los bombillos y ver SOLO el que tenemos enfrente.
            Si vemos luz (1), falta por regar. Si no (0), ya está.

TRUCO 2: ¡Listo, ya regué este tablón! -> pendientes ^ (1 << i)
--------------------------------------------------------------------
Queremos apagar el bombillo 'i' a distancia sin tocar los demás:
1. (1 << i) : Movemos la mira de un puntero láser 'i' espacios hacia
              la izquierda para apuntar exactamente a ese bombillo.
2. ( ^ )    : Presionamos el botón de apagado (XOR). Esto dispara el 
              láser y apaga ÚNICAMENTE el bombillo al que estamos 
              apuntando, dejando a todos los demás intactos.
====================================================================
"""

def tablon_esta_pendiente(pendientes: int, idx_tablon: int) -> bool:
    """Retorna True si el tablón `idx_tablon` aún no ha sido regado."""
    return bool((pendientes >> idx_tablon) & 1)


def marcar_tablon_como_regado(pendientes: int, idx_tablon: int) -> int:
    """
    Retorna un nuevo bitmask con el tablón `idx_tablon` marcado como regado.
    Usa XOR para apagar el bit correspondiente.
    """
    return pendientes ^ (1 << idx_tablon)


def tablones_pendientes_en(pendientes: int, total_tablones: int):
    """
    Generador que yield-ea los índices de tablones que aún están pendientes.

    Args:
        pendientes:      bitmask del estado actual
        total_tablones:  cantidad total de tablones en la finca
    """
    for idx in range(total_tablones):
        if tablon_esta_pendiente(pendientes, idx):
            yield idx


def bitmask_todos_pendientes(total_tablones: int) -> int:
    """
    Retorna el bitmask inicial donde TODOS los tablones están pendientes.
    Ejemplo: 4 tablones → 0b1111 = 15
    """
    return (1 << total_tablones) - 1
