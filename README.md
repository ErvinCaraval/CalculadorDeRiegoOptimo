# Proyecto: Calculador de Riego Óptimo

Este proyecto es una solución integral para el problema del riego óptimo de una finca. Utiliza una arquitectura Modelo-Vista-Controlador (MVC) para comparar tres estrategias algorítmicas: Fuerza Bruta, Algoritmo Voraz y Programación Dinámica.

---

## Requisitos Previos

Antes de comenzar, asegúrese de tener instalado:
*   Node.js (v14 o superior)
*   Python (v3.7 o superior)
*   Un navegador web moderno (Chrome, Firefox, Edge, etc.)

---

## Guía Paso a Paso para Ejecutar

Siga estos pasos exactos para iniciar la aplicación en Windows:

### Ejecución en Windows

1. Crear el entorno virtual:
    ```powershell
    python -m venv venv
    ```

2. Habilitar scripts:
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

3. Activar el entorno:
    ```powershell
    .\venv\Scripts\activate
    ```

4. Instalar requisitos:
    ```powershell
    pip install -r requirements.txt
    ```

5. Acceder a la carpeta del backend e instalar paquetes:
    ```powershell
    cd .\backend\
    npm i
    ```

6. Ejecutar proyecto:
    ```powershell
    npm start
    ```

---

## Cómo usar la Aplicación

Una vez dentro de la interfaz web, tiene tres formas de ingresar datos:

1.  **Cargar Archivo (.txt):** Haga clic en el área de carga o arrastre un archivo .txt.
2.  **Cargar Ejemplo:** Use el botón "Cargar Ejemplo" para elegir fincas ya configuradas.
3.  **Manual:** Agregue tablones uno por uno usando el botón "+ Agregar Tablón".

**Para resolver:**
1. Seleccione el algoritmo que desea probar (Fuerza Bruta, Voraz o P. Dinámica).
2. Haga clic en el botón "Ejecutar Algoritmo".
3. El sistema mostrará el costo mínimo, el orden de riego y el análisis de tiempos.

---

## Estructura del Proyecto

*   backend/: Servidor Node.js (Controlador).
*   frontend/: Interfaz web interactiva (Vista).
*   python_algorithms/: Implementación de los algoritmos (Modelo).
*   data/ejemplos/: Archivos .txt de prueba.

---

## Notas Técnicas

*   Optimización: Los scripts de Python están configurados para no generar carpetas __pycache__, manteniendo el proyecto limpio.
*   Algoritmos: 
    *   roFB: Fuerza Bruta (Recursivo).
    *   roPD: Programación Dinámica (Recursivo + Memoization).
    *   roV: Algoritmo Voraz (Recursivo con Heurística de Urgencia).
*   Formato de Salida: El sistema genera archivos .txt siguiendo estrictamente el formato solicitado en el PDF del curso.