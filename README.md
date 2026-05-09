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

Siga estos pasos exactos para iniciar la aplicación:

### Paso 1: Abrir la Terminal
Navegue hasta la carpeta raíz del proyecto:
```bash
cd /home/ervin/Desktop/proyecto_prog_dinamica_prog_voraz
```

### Paso 2: Crear y Activar el Entorno Virtual (Python)
Este paso es fundamental para preparar el entorno de ejecución de los algoritmos:

1.  **Crear el entorno virtual:**
    ```bash
    En linux 
    sudo apt update
    sudo apt install pypy3 pypy3-venv
    pypy3 -m venv venv

    En Mac
    brew install pypy3
    pypy3 -m venv venv

    En windows powershell
    choco install pypy3
    pypy3 -m venv venv  # o pypy -m venv venv

    ```
2.  **Activar el entorno:**
    *   En **Linux o macOS**:
        ```bash
        source venv/bin/activate
        pip install -r requirements.txt
        ```
    *   En **Windows**:
        ```bash
        .\venv\Scripts\activate.ps1
        pip install -r requirements.txt
        ```
    *Sabrá que está activo porque aparecerá `(venv)` al inicio de su terminal.*

3. **Desactivar el entorno (Opcional.):**
   * 
   ```bash
   deactivate
   ```
   
### Paso 3: Instalar Dependencias de Node.js
Instale los paquetes necesarios para el servidor backend:
```bash
npm install
```

### Paso 4: Iniciar el Servidor
Ejecute el siguiente comando para poner en marcha el sistema:
```bash
npm start
```
*Debería ver un mensaje confirmando que el servidor está corriendo en el puerto 3000.*

### Paso 5: Abrir la Interfaz Web
Abra su navegador y entre a la siguiente dirección:
http://localhost:3000

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