#!/usr/bin/env python3
"""
Script ejecutable para resolver el problema del riego óptimo.
Actúa como la interfaz de línea de comandos (CLI) principal.

ENTRADAS (Argumentos CLI):
---------------------------
    1. algoritmo      : "FB", "V", o "PD".
    2. archivo_entrada: Ruta del archivo .txt con los datos de la finca.
    3. archivo_salida : Ruta del archivo .txt donde se guardará el resultado.

SALIDAS:
---------
    - Escribe el resultado óptimo en 'archivo_salida'.
    - Imprime en la salida estándar (stdout): "SUCCESS|<algoritmo>|<tiempo_ms>ms"
    - En caso de error, imprime en (stderr): "ERROR: <mensaje>"

USO:
----
    python resolver_riego.py <algoritmo> <archivo_entrada> <archivo_salida>
"""

import sys
sys.dont_write_bytecode = True
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from modelo_riego import roFB, roV, roPD
    from io_riego import parsear_finca_desde_archivo, escribir_resultado_a_archivo
except ImportError as e:
    print(f"Error: No se pudo importar el modelo - {e}", file=sys.stderr)
    sys.exit(1)


def main():
    """Punto de entrada principal del programa."""

    if len(sys.argv) != 4:
        print("Error: Se requieren exactamente 3 argumentos", file=sys.stderr)
        print("Uso: python resolver_riego.py <algoritmo> <archivo_entrada> <archivo_salida>", file=sys.stderr)
        sys.exit(1)

    algoritmo      = sys.argv[1].upper()
    archivo_entrada = sys.argv[2]
    archivo_salida  = sys.argv[3]

    algoritmos_validos = {'FB', 'V', 'PD'}
    if algoritmo not in algoritmos_validos:
        print(f"Error: Algoritmo inválido '{algoritmo}'", file=sys.stderr)
        sys.exit(1)

    try:
        if not Path(archivo_entrada).exists():
            raise FileNotFoundError(f"El archivo de entrada no existe: {archivo_entrada}")

        finca = parsear_finca_desde_archivo(archivo_entrada)

        inicio = time.time()

        if algoritmo == 'FB':
            orden, costo = roFB(finca)
        elif algoritmo == 'V':
            orden, costo = roV(finca)
        elif algoritmo == 'PD':
            orden, costo = roPD(finca)

        fin          = time.time()
        duracion_ms  = int((fin - inicio) * 1000)

        escribir_resultado_a_archivo(archivo_salida, orden, int(costo))

        print(f"SUCCESS|{algoritmo}|{duracion_ms}ms")
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
