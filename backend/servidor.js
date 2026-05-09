/**
 * Servidor Express: Controlador MVC
 * 
 * Propósito: Actúa como intermediario entre la Vista (Frontend) y el Modelo (Python).
 * - Recibe datos de entrada del usuario
 * - Valida y formatea los datos
 * - Ejecuta el script de Python con el algoritmo especificado
 * - Parsea y devuelve los resultados al cliente
 * 
 * Autor: Ervin Caravali Ibarra Camilo Urrea 
 */

const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');
const os = require('os');
const app = express();
const PORT = 3000;

// Configuración de middlewares
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ limit: '10mb', extended: true }));
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// Directorio temporal para archivos
const TEMP_DIR = path.join(__dirname, 'temp');
if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
}

// ============================================================================
// VALIDACIONES Y UTILIDADES
// ============================================================================

/**
 * Valida que los datos de entrada sean correctos.
 * 
 * @param {Object} finca - Objeto con los tablones
 * @returns {Object} - { valido: boolean, error: string }
 */
function validarFinca(finca) {
    if (!finca || !Array.isArray(finca.tablones) || finca.tablones.length === 0) {
        return { valido: false, error: 'La finca debe contener al menos un tablón' };
    }

    for (let i = 0; i < finca.tablones.length; i++) {
        const t = finca.tablones[i];

        // Validar presencia de campos
        if (t.ts === undefined || t.tr === undefined || t.p === undefined || t.ro === undefined) {
            return {
                valido: false,
                error: `Tablón ${i}: faltan campos (ts, tr, p, ro requeridos)`
            };
        }

        // Validar tipos
        if (!Number.isInteger(t.ts) || !Number.isInteger(t.tr) ||
            !Number.isInteger(t.p) || !Number.isInteger(t.ro)) {
            return {
                valido: false,
                error: `Tablón ${i}: todos los valores deben ser enteros`
            };
        }

        // Validar rangos
        if (t.ts <= 0) {
            return {
                valido: false,
                error: `Tablón ${i}: ts debe ser positivo`
            };
        }
        if (t.tr <= 0) {
            return {
                valido: false,
                error: `Tablón ${i}: tr debe ser positivo`
            };
        }
        if (t.p < 1 || t.p > 4) {
            return {
                valido: false,
                error: `Tablón ${i}: p debe estar entre 1 y 4`
            };
        }
        if (t.ro < 0 || t.ro > t.ts - t.tr) {
            return {
                valido: false,
                error: `Tablón ${i}: ro debe satisfacer 0 ≤ ro ≤ ts - tr`
            };
        }
    }

    return { valido: true };
}

/**
 * Convierte los datos de la finca al formato de archivo esperado por el modelo Python.
 * 
 * Formato:
 * n
 * ts0,tr0,p0,ro0
 * ts1,tr1,p1,ro1
 * ...
 * 
 * @param {Object} finca - Objeto con los tablones
 * @returns {string} - Contenido del archivo
 */
function serializarFinca(finca) {
    let contenido = `${finca.tablones.length}\n`;

    for (const tablon of finca.tablones) {
        contenido += `${tablon.ts},${tablon.tr},${tablon.p},${tablon.ro}\n`;
    }

    return contenido;
}

/**
 * Parsea la salida del modelo Python (archivo de resultado).
 * 
 * Formato esperado:
 * Costo
 * pi0
 * pi1
 * ...
 * 
 * @param {string} contenido - Contenido del archivo de salida
 * @returns {Object} - { costo: number, permutacion: number[] }
 */
function parsearSolucion(contenido) {
    const lineas = contenido.trim().split('\n');

    if (lineas.length < 1) {
        throw new Error('Archivo de salida vacío');
    }

    const costo = parseInt(lineas[0], 10);
    if (isNaN(costo)) {
        throw new Error('Costo no es un número válido');
    }

    const permutacion = [];
    for (let i = 1; i < lineas.length; i++) {
        const idx = parseInt(lineas[i], 10);
        if (isNaN(idx)) {
            throw new Error(`Índice de permutación no es válido: ${lineas[i]}`);
        }
        permutacion.push(idx);
    }

    return { costo, permutacion };
}

/**
 * Ejecuta el script de Python de forma asincrónica.
 * Compatible con Windows, Linux y macOS usando venv.
 * 
 * @param {string} algoritmo - "FB", "V" o "PD"
 * @param {string} archivoEntrada - Ruta del archivo de entrada
 * @param {string} archivoSalida - Ruta del archivo de salida
 * @returns {Promise} - Promesa que se resuelve cuando termina la ejecución
 */
function ejecutarPython(algoritmo, archivoEntrada, archivoSalida) {
    return new Promise((resolve, reject) => {

        // Ruta del script principal Python
        const scriptPython = path.resolve(
            __dirname,
            '..',
            'python_algorithms',
            'resolver_riego.py'
        );

        // Detectar sistema operativo
        const isWindows = os.platform() === 'win32';

        // Ruta del ejecutable Python dentro del venv
        const pythonVenv = isWindows
            ? path.resolve(__dirname, '..', 'venv', 'Scripts', 'python.exe')
            : path.resolve(__dirname, '..', 'venv', 'bin', 'python3');

        // Verificar que exista el entorno virtual
        if (!fs.existsSync(pythonVenv)) {
            return reject(
                new Error(
                    `No se encontró el entorno virtual Python en:\n${pythonVenv}\n\n` +
                    `Cree el entorno virtual usando:\n` +
                    `python -m venv venv`
                )
            );
        }

        // Verificar que exista el script Python
        if (!fs.existsSync(scriptPython)) {
            return reject(
                new Error(`No se encontró el script Python: ${scriptPython}`)
            );
        }

        console.log(
            `[${new Date().toISOString()}] Ejecutando:\n` +
            `${pythonVenv} ${scriptPython} ${algoritmo} ${archivoEntrada} ${archivoSalida}`
        );

        // Crear proceso Python
        const pythonProcess = spawn(pythonVenv, [
            '-B',
            scriptPython,
            algoritmo,
            archivoEntrada,
            archivoSalida
        ]);

        let stdout = '';
        let stderr = '';

        // Capturar salida estándar
        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        // Capturar errores
        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        // Evento cuando termina el proceso
        pythonProcess.on('close', (code) => {

            console.log(
                `[${new Date().toISOString()}] Python terminó con código: ${code}`
            );

            if (stdout.trim()) {
                console.log('Python stdout:\n', stdout);
            }

            if (stderr.trim()) {
                console.error('Python stderr:\n', stderr);
            }

            // Código distinto de 0 = error
            if (code !== 0) {
                return reject(
                    new Error(
                        `Proceso Python finalizó con código ${code}\n${stderr}`
                    )
                );
            }

            // Verificar que el archivo de salida exista
            if (!fs.existsSync(archivoSalida)) {
                return reject(
                    new Error(
                        `El algoritmo terminó pero no generó el archivo de salida:\n${archivoSalida}`
                    )
                );
            }

            resolve(stdout);
        });

        // Error al iniciar el proceso
        pythonProcess.on('error', (error) => {
            reject(
                new Error(
                    `Error al ejecutar Python:\n${error.message}`
                )
            );
        });

        // Timeout de seguridad (7 minutos)
        const timeout = setTimeout(() => {

            pythonProcess.kill();

            reject(
                new Error(
                    'Timeout: La ejecución excedió el límite de 7 minutos'
                )
            );

        }, 420000);

        // Limpiar timeout cuando termine
        pythonProcess.on('close', () => {
            clearTimeout(timeout);
        });
    });
}

// ============================================================================
// RUTAS HTTP
// ============================================================================

/**
 * Ruta GET: Página principal
 */
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
});

/**
 * Ruta POST: Resolver el problema del riego óptimo
 */
app.post('/resolver', async (req, res) => {
    const { algoritmo, finca } = req.body;
    let archivoEntrada, archivoSalida;

    try {
        // Validar algoritmo
        if (!['FB', 'V', 'PD'].includes(algoritmo)) {
            return res.status(400).json({ exito: false, error: `Algoritmo inválido: ${algoritmo}` });
        }

        // Validar finca
        const validacion = validarFinca(finca);
        if (!validacion.valido) {
            return res.status(400).json({ exito: false, error: validacion.error });
        }

        // Crear archivos temporales
        const timestamp = Date.now();
        archivoEntrada = path.resolve(TEMP_DIR, `entrada_${timestamp}.txt`);
        archivoSalida = path.resolve(TEMP_DIR, `salida_${timestamp}.txt`);

        // Escribir entrada
        fs.writeFileSync(archivoEntrada, serializarFinca(finca));

        const inicio = Date.now();
        await ejecutarPython(algoritmo, archivoEntrada, archivoSalida);
        const tiempoEjecucion = Date.now() - inicio;

        // Leer y parsear resultado
        const contenidoSalida = fs.readFileSync(archivoSalida, 'utf8');
        const { costo, permutacion } = parsearSolucion(contenidoSalida);

        res.json({
            exito: true,
            costo,
            permutacion,
            tiempoEjecucion,
            algoritmo
        });

    } catch (error) {
        console.error(`Error en /resolver:`, error.message);
        res.status(500).json({ exito: false, error: error.message });
    } finally {
        // Limpieza garantizada de temporales
        try {
            if (archivoEntrada && fs.existsSync(archivoEntrada)) fs.unlinkSync(archivoEntrada);
            if (archivoSalida && fs.existsSync(archivoSalida)) fs.unlinkSync(archivoSalida);
        } catch (e) { }
    }
});

/**
 * Ruta GET: Cargar ejemplos desde el sistema de archivos
 */
app.get('/ejemplos', (req, res) => {
    const EJEMPLOS_DIR = path.join(__dirname, '..', 'data', 'ejemplos');
    const OUTPUT_DIR = path.join(__dirname, '..', 'data', 'output');
    const ejemplos = {};

    try {
        if (!fs.existsSync(EJEMPLOS_DIR)) {
            return res.json({});
        }

        const archivos = fs.readdirSync(EJEMPLOS_DIR).filter(f => f.endsWith('.txt'));

        // Ordenar archivos de menor a mayor basado en el número
        archivos.sort((a, b) => {
            const numA = parseInt(a.replace(/\D/g, '')) || 0;
            const numB = parseInt(b.replace(/\D/g, '')) || 0;
            return numA - numB;
        });

        archivos.forEach(archivo => {
            const contenido = fs.readFileSync(path.join(EJEMPLOS_DIR, archivo), 'utf8');
            const lineas = contenido.trim().split('\n');
            const n = parseInt(lineas[0]);
            const tablones = [];

            for (let i = 1; i <= n; i++) {
                if (!lineas[i]) continue;
                const [ts, tr, p, ro] = lineas[i].split(',').map(Number);
                tablones.push({ ts, tr, p, ro });
            }

            const id = archivo.replace('.txt', '');
            const baseId = id.replace('_in', ''); // Ej: test1
            const nombre = baseId.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

            let salidaEsperada = null;
            const outputArchivo = path.join(OUTPUT_DIR, `${baseId}_out.txt`);
            if (fs.existsSync(outputArchivo)) {
                try {
                    const outContent = fs.readFileSync(outputArchivo, 'utf8');
                    salidaEsperada = parsearSolucion(outContent);
                } catch (e) {
                    console.error(`Error parseando salida esperada para ${baseId}:`, e.message);
                }
            }

            ejemplos[id] = {
                nombre: nombre,
                tablones: tablones,
                salidaEsperada: salidaEsperada
            };
        });

        res.json(ejemplos);
    } catch (error) {
        res.status(500).json({ error: 'Error al cargar ejemplos' });
    }
});


// ============================================================================
// INICIALIZACIÓN DEL SERVIDOR
// ============================================================================

app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════╗
║  SERVIDOR DE RIEGO ÓPTIMO                          ║
║  http://localhost:${PORT}                           ║
╚════════════════════════════════════════════════════╝
    `);
});

// Manejo de errores no capturados
process.on('unhandledRejection', (reason, promise) => {
    console.error('Rechazo no manejado:', reason);
});
