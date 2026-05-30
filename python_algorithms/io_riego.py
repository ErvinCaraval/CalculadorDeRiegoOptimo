"""
Módulo: io_riego.py
===================
Funciones de entrada/salida para el problema del riego óptimo.
"""

import sys
sys.dont_write_bytecode = True

from typing import List, Tuple


def parsear_finca_desde_archivo(ruta_archivo: str) -> List[Tuple[int, int, int, int]]:
    """
    Lee una finca desde un archivo de texto.

    ENTRADAS:
    ----------
    ruta_archivo : str
        Ruta absoluta o relativa del archivo de texto a leer.

    SALIDAS:
    ----------
    List[Tuple[int, int, int, int]]
        Lista de tablones representados como tuplas (ts, tr, p, ro).
        
    FORMATO ESPERADO:
    ------------------
        n
        ts0,tr0,p0,ro0
        ts1,tr1,p1,ro1
        ...
    """
    with open(ruta_archivo, 'r') as f:
        lineas = f.readlines()

    if not lineas:
        raise ValueError("Archivo vacío")

    try:
        n = int(lineas[0].strip())
    except (ValueError, IndexError):
        raise ValueError("Primera línea debe contener el número de tablones (entero)")
    
    if n <= 0:
        raise ValueError("El número de tablones debe ser positivo")

    finca = []

    for i in range(1, n + 1):
        if i >= len(lineas):
            raise ValueError(f"Se esperaban {n} tablones pero solo se encontraron {i-1}")
        
        try:
            partes = lineas[i].strip().split(',')
            if len(partes) < 4:
                raise ValueError(f"Tablón {i}: faltan parámetros (esperados 4)")
            
            ts = int(partes[0])
            tr = int(partes[1])
            p = int(partes[2])
            ro = int(partes[3])
            
            finca.append((ts, tr, p, ro))
        
        except ValueError as e:
            raise ValueError(f"Error parseando tablón {i}: {str(e)}")

    return finca


def escribir_resultado_a_archivo(ruta_archivo: str, orden: List[int], costo: int) -> None:
    """
    Escribe el resultado de la programación de riego a un archivo.

    ENTRADAS:
    ----------
    ruta_archivo : str
        Ruta absoluta o relativa del archivo donde se guardará la salida.
    orden : List[int]
        Lista con el orden de los índices de los tablones regados.
    costo : int
        Costo total obtenido por el algoritmo.

    SALIDAS:
    ----------
    None
        Genera un archivo de texto en la ruta especificada.

    FORMATO DE SALIDA:
    -------------------
        Costo
        pi0
        pi1
        ...
    """
    with open(ruta_archivo, 'w') as f:
        f.write(f"{costo}\n")
        for idx in orden:
            f.write(f"{idx}\n")
