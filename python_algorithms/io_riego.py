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

    Formato esperado:
        n
        ts0,tr0,p0,ro0
        ts1,tr1,p1,ro1
        ...
    """
    with open(ruta_archivo, 'r') as f:
        lineas = f.readlines()

    if not lineas:
        raise ValueError("Archivo vacío")

    n = int(lineas[0].strip())
    finca = []

    for i in range(1, n + 1):
        if i >= len(lineas):
            break
        partes = lineas[i].strip().split(',')
        if len(partes) < 4:
            continue
        ts = int(partes[0])
        tr = int(partes[1])
        p  = int(partes[2])
        ro = int(partes[3])
        finca.append((ts, tr, p, ro))

    return finca


def escribir_resultado_a_archivo(ruta_archivo: str, orden: List[int], costo: int) -> None:
    """
    Escribe el resultado de la programación de riego a un archivo.

    Formato de salida:
        Costo
        pi0
        pi1
        ...
    """
    with open(ruta_archivo, 'w') as f:
        f.write(f"{costo}\n")
        for idx in orden:
            f.write(f"{idx}\n")
