/**
 * Script Principal: app.js
 * 
 * Maneja toda la interacción del usuario en el frontend:
 * - Gestión de tablones
 * - Validación de datos
 * - Comunicación con el servidor
 * - Visualización de resultados
 * 
 * Autor: Ervin Caravali Camilo Hurrea
 */

// ============================================================================
// VARIABLES GLOBALES
// ============================================================================

let tablones = [];
let solucionActual = null;
let salidaEsperadaActual = null;

// Configuración de logging
const DEBUG = false; // Cambiar a true para verbose logging

/**
 * Log condicional: solo muestra si DEBUG está habilitado
 * @param {string} mensaje
 * @param {*} datos
 */
function debugLog(mensaje, datos = '') {
    if (DEBUG) {
        console.log(`[DEBUG] ${mensaje}`, datos);
    }
}

/**
 * Muestra un indicador de estado (loading)
 * @param {string} mensaje - Texto a mostrar
 */
function mostrarCargando(mensaje = 'Procesando...') {
    const overlay = document.getElementById('loadingOverlay');
    const texto = overlay.querySelector('span');
    texto.textContent = mensaje;
    overlay.style.display = 'flex';
}

/**
 * Oculta el indicador de estado
 */
function ocultarCargando() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

/**
 * Muestra un toast de error
 * @param {string} mensaje - Texto del error
 */
function mostrarError(mensaje) {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.innerHTML = `
        <i class="ph-fill ph-warning-circle toast-icon" style="font-size: 24px;"></i>
        <span class="toast-message">${mensaje}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Oculta el área de errores (legacy - ya no se usa con toasts)
 */
function ocultarError() {
    // Ya no necesario con el sistema de toasts
}

/**
 * Valida que un tablón tenga datos correctos
 * @param {Object} tablon - Objeto con los datos del tablón
 * @returns {Object} - { valido: boolean, error: string }
 */
function validarTablon(tablon) {
    if (tablon.ts === undefined || tablon.ts === '') {
        return { valido: false, error: 'TS (Tiempo de Supervivencia) es requerido' };
    }
    if (tablon.tr === undefined || tablon.tr === '') {
        return { valido: false, error: 'TR (Tiempo de Regado) es requerido' };
    }
    if (tablon.p === undefined || tablon.p === '') {
        return { valido: false, error: 'P (Prioridad) es requerida' };
    }
    if (tablon.ro === undefined || tablon.ro === '') {
        return { valido: false, error: 'RO (Riego Óptimo) es requerido' };
    }

    const ts = parseInt(tablon.ts, 10);
    const tr = parseInt(tablon.tr, 10);
    const p = parseInt(tablon.p, 10);
    const ro = parseInt(tablon.ro, 10);

    if (isNaN(ts) || ts <= 0) {
        return { valido: false, error: 'TS debe ser un número positivo' };
    }
    if (isNaN(tr) || tr <= 0) {
        return { valido: false, error: 'TR debe ser un número positivo' };
    }
    if (isNaN(p) || p < 1 || p > 4) {
        return { valido: false, error: 'P debe ser un número entre 1 y 4' };
    }
    if (isNaN(ro) || ro < 0 || ro > ts - tr) {
        return { valido: false, error: `RO debe estar entre 0 y ${ts - tr}` };
    }

    return { valido: true };
}

/**
 * Obtiene todos los tablones de la tabla
 * @returns {Array} - Array de objetos con los datos de los tablones
 */
function obtenerTablones() {
    const tablones = [];
    const filas = document.querySelectorAll('#cuerpoTabla tr');

    filas.forEach((fila, index) => {
        const inputTs = fila.querySelector('input.ts');
        const inputTr = fila.querySelector('input.tr');
        const selectP = fila.querySelector('select.p');
        const inputRo = fila.querySelector('input.ro');

        if (!inputTs || !inputTr || !selectP || !inputRo) {
            throw new Error(`Tablón ${index + 1}: Faltan campos en la fila`);
        }

        const tablon = {
            ts: parseInt(inputTs.value, 10),
            tr: parseInt(inputTr.value, 10),
            p: parseInt(selectP.value, 10),
            ro: parseInt(inputRo.value, 10)
        };

        // Validar este tablón
        const val = validarTablon(tablon);
        if (!val.valido) {
            throw new Error(`Tablón ${index + 1}: ${val.error}`);
        }

        tablones.push(tablon);
    });

    return tablones;
}

// ============================================================================
// GESTIÓN DE TABLONES
// ============================================================================

/**
 * Agrega una nueva fila de tablón a la tabla
 * @param {Object} datosPredefinidos - Datos opcionales para pre-llenar la fila
 */
function agregarTablon(datosPredefinidos = null) {
    const cuerpoTabla = document.getElementById('cuerpoTabla');
    const numTablon = cuerpoTabla.children.length + 1;

    const fila = document.createElement('tr');
    fila.innerHTML = `
        <td class="numero-tablon">${numTablon}</td>
        <td><input type="number" class="ts" min="1" value="${datosPredefinidos?.ts || 5}" required></td>
        <td><input type="number" class="tr" min="1" value="${datosPredefinidos?.tr || 2}" required></td>
        <td>
            <select class="p" required>
                <option value="">-</option>
                <option value="1" ${datosPredefinidos?.p === 1 ? 'selected' : ''}>1</option>
                <option value="2" ${datosPredefinidos?.p === 2 ? 'selected' : ''}>2</option>
                <option value="3" ${datosPredefinidos?.p === 3 ? 'selected' : ''}>3</option>
                <option value="4" ${datosPredefinidos?.p === 4 ? 'selected' : ''}>4</option>
            </select>
        </td>
        <td><input type="number" class="ro" min="0" value="${datosPredefinidos?.ro || 0}" required></td>
        <td>
            <button class="btn-delete" onclick="eliminarTablon(this)">
                <i class="ph ph-trash" style="font-size: 18px;"></i>
            </button>
        </td>
    `;

    // Agregar validación en tiempo real para RO
    const inputTs = fila.querySelector('.ts');
    const inputTr = fila.querySelector('.tr');
    const inputRo = fila.querySelector('.ro');

    function actualizarMaxRo() {
        const ts = parseInt(inputTs.value, 10) || 0;
        const tr = parseInt(inputTr.value, 10) || 0;
        const maxRo = Math.max(0, ts - tr);
        inputRo.max = maxRo;

        // Ajustar RO si excede el nuevo máximo
        const roActual = parseInt(inputRo.value, 10) || 0;
        if (roActual > maxRo) {
            inputRo.value = maxRo;
        }
    }

    inputTs.addEventListener('change', actualizarMaxRo);
    inputTr.addEventListener('change', actualizarMaxRo);
    
    // Si se modifica manualmente, invalidamos la salida esperada actual
    fila.addEventListener('input', () => salidaEsperadaActual = null);

    cuerpoTabla.appendChild(fila);
    actualizarNumerosTablones();
}

/**
 * Elimina una fila de tablón
 * @param {HTMLElement} boton - Botón de eliminar clickeado
 */
function eliminarTablon(boton) {
    boton.closest('tr').remove();
    actualizarNumerosTablones();
}

/**
 * Actualiza los números de los tablones, el contador y el estado vacío
 */
function actualizarNumerosTablones() {
    const filas = document.querySelectorAll('#cuerpoTabla tr');
    const total = filas.length;
    
    // Actualizar números de fila
    filas.forEach((fila, index) => {
        fila.querySelector('.numero-tablon').textContent = index + 1;
    });
    
    // Actualizar contador
    const contador = document.getElementById('tableCount');
    if (contador) {
        contador.textContent = `${total} tablón${total === 1 ? '' : 'es'}`;
    }
    
    // Toggle estado vacío
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
        emptyState.style.display = total === 0 ? 'flex' : 'none';
    }

    debugLog('Tabla actualizada', `${total} tablones`);
}

/**
 * Carga una finca completa en la tabla
 * @param {Array} tablonesNuevos - Array de objetos con datos de tablones
 */
function cargarFinca(tablonesNuevos) {
    document.getElementById('cuerpoTabla').innerHTML = '';
    tablonesNuevos.forEach(t => agregarTablon(t));
}

/**
 * Limpia todos los datos de la finca, resultados y formularios
 */
function limpiarTablones() {
    debugLog('Ejecutando limpieza total');
    
    // Limpiar tabla
    const cuerpo = document.getElementById('cuerpoTabla');
    if (cuerpo) cuerpo.innerHTML = '';
    
    // Actualizar UI de la tabla
    actualizarNumerosTablones();
    
    // Limpiar resultados
    const seccionResultados = document.getElementById('seccionResultados');
    if (seccionResultados) {
        seccionResultados.classList.remove('active');
        // Limpiar valores internos
        const vCosto = document.getElementById('valorCosto');
        const vAlgo = document.getElementById('valorAlgoritmo');
        const vTiempo = document.getElementById('valorTiempo');
        if (vCosto) vCosto.textContent = '-';
        if (vAlgo) vAlgo.textContent = '-';
        if (vTiempo) vTiempo.textContent = '-';
        
        const seq = document.getElementById('secuenciaRiego');
        const ana = document.getElementById('cuerpoAnalisis');
        if (seq) seq.innerHTML = '';
        if (ana) ana.innerHTML = '';
    }
    
    // Limpiar variables globales
    solucionActual = null;
    salidaEsperadaActual = null;
    tablones = [];
    
    // Resetear formulario manual
    const mTs = document.getElementById('manualTs');
    const mTr = document.getElementById('manualTr');
    const mP = document.getElementById('manualP');
    const mRo = document.getElementById('manualRo');
    if (mTs) mTs.value = 10;
    if (mTr) mTr.value = 3;
    if (mP) mP.value = 4;
    if (mRo) mRo.value = 0;
    
    // Scroll arriba suavemente
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================================
// RESOLUCIÓN DEL PROBLEMA
// ============================================================================

/**
 * Envía el problema al servidor para ser resuelto
 */
async function resolverProblema() {
    ocultarError();

    try {
        // Validar que se seleccionó un algoritmo
        const algoritmo = document.querySelector('input[name="algoritmo"]:checked');
        if (!algoritmo) {
            mostrarError('Por favor, seleccione un algoritmo');
            return;
        }

        // Obtener y validar tablones
        let tablones;
        try {
            tablones = obtenerTablones();
        } catch (error) {
            mostrarError(error.message);
            return;
        }

        if (tablones.length === 0) {
            mostrarError('Por favor, agregue al menos un tablón');
            return;
        }
        
        if (tablones.length > 30) {
            mostrarError('Máximo 30 tablones permitidos para evitar timeout');
            return;
        }

        // Mostrar indicador de carga
        mostrarCargando(`Ejecutando ${algoritmo.value}...`);

        // Crear objeto con los datos
        const finca = { tablones };

        // Enviar al servidor
        const respuesta = await fetch('/resolver', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                algoritmo: algoritmo.value,
                finca
            })
        });

        const datos = await respuesta.json();

        if (!datos.exito) {
            ocultarCargando();
            mostrarError(datos.error || 'Error desconocido');
            return;
        }

        // Guardar solución actual
        solucionActual = datos;

        // Mostrar resultados
        mostrarResultados(datos, tablones);
        ocultarCargando();
        
        if (salidaEsperadaActual) {
            mostrarComparacion(datos, salidaEsperadaActual);
        }

    } catch (error) {
        ocultarCargando();
        mostrarError(`Error: ${error.message}`);
    }
}

/**
 * Muestra los resultados de la ejecución del algoritmo
 * @param {Object} datos - Datos de la solución
 * @param {Array} tablones - Array de tablones
 */
function mostrarResultados(datos, tablones) {
    const seccion = document.getElementById('seccionResultados');

    // Llenar resumen
    document.getElementById('valorCosto').textContent = datos.costo;
    document.getElementById('valorAlgoritmo').textContent = obtenerNombreAlgoritmo(datos.algoritmo);
    document.getElementById('valorTiempo').textContent = `${datos.tiempoEjecucion}ms`;

    // Construir secuencia de riego
    const secuencia = document.getElementById('secuenciaRiego');
    secuencia.innerHTML = '';

    datos.permutacion.forEach((idx, posicion) => {
        const paso = document.createElement('div');
        paso.className = 'paso-riego';
        paso.textContent = `T${idx}`;
        secuencia.appendChild(paso);

        if (posicion < datos.permutacion.length - 1) {
            const flecha = document.createElement('div');
            flecha.className = 'flecha-riego';
            flecha.textContent = '→';
            secuencia.appendChild(flecha);
        }
    });

    // Calcular y mostrar análisis de tiempos
    const tiempos = calcularTiempos(tablones, datos.permutacion);
    mostrarAnalisisTiempos(tablones, datos.permutacion, tiempos, datos.costo);

    // Mostrar sección de resultados con animación
    seccion.classList.add('active');

    // Scroll a resultados
    seccion.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Muestra el modal de comparación entre salida obtenida y esperada
 */
function mostrarComparacion(obtenida, esperada) {
    const cuerpo = document.getElementById('cuerpoComparacion');
    
    let html = `
        <div class="comparacion-grid">
            <div class="comp-columna">
                <h4 style="color: var(--primary);"><i class="ph-fill ph-check-circle"></i> Salida Obtenida</h4>
                <div class="comp-dato"><strong>Costo:</strong> ${obtenida.costo}</div>
                <div class="comp-dato"><strong>Permutación:</strong><br>[${obtenida.permutacion.join(', ')}]</div>
            </div>
            <div class="comp-columna">
                <h4 style="color: var(--secondary);"><i class="ph-fill ph-target"></i> Salida Esperada</h4>
                <div class="comp-dato"><strong>Costo:</strong> ${esperada.costo}</div>
                <div class="comp-dato"><strong>Permutación:</strong><br>[${esperada.permutacion.join(', ')}]</div>
            </div>
        </div>
    `;
    
    const esIgual = obtenida.costo === esperada.costo && 
                    JSON.stringify(obtenida.permutacion) === JSON.stringify(esperada.permutacion);
                    
    if (esIgual) {
        html += `<div class="comp-resultado exito" style="color: var(--success); margin-top: var(--space-md); text-align: center; font-weight: 600;"><i class="ph-fill ph-check-circle"></i> ¡Los resultados coinciden exactamente!</div>`;
    } else {
        html += `<div class="comp-resultado error" style="color: var(--danger); margin-top: var(--space-md); text-align: center; font-weight: 600;"><i class="ph-fill ph-warning-circle"></i> Hay diferencias en los resultados.</div>`;
    }
    
    cuerpo.innerHTML = html;
    document.getElementById('modalComparacion').style.display = 'flex';
}

function cerrarComparacion() {
    document.getElementById('modalComparacion').style.display = 'none';
}

/**
 * Calcula los tiempos de inicio y fin para cada tablón según la permutación
 * @param {Array} tablones - Array de tablones
 * @param {Array} permutacion - Array con el orden de riego
 * @returns {Array} - Array con tiempos calculados
 */
function calcularTiempos(tablones, permutacion) {
    const tiempos = Array(tablones.length).fill(null).map(() => ({}));

    let tiempoActual = 0;

    for (let i = 0; i < permutacion.length; i++) {
        const idx = permutacion[i];
        const tablon = tablones[idx];

        tiempos[idx].inicio = tiempoActual;
        tiempos[idx].fin = tiempoActual + tablon.tr;
        tiempos[idx].orden = i + 1;

        // Calcular costo del tablón
        tiempos[idx].costo = calcularCostoTablon(tablon, tiempoActual);

        tiempoActual += tablon.tr;
    }

    return tiempos;
}

/**
 * Calcula el costo individual de un tablón
 * @param {Object} tablon - Datos del tablón
 * @param {number} tiempoInicio - Tiempo de inicio del riego
 * @returns {number} - Costo del tablón
 */
function calcularCostoTablon(tablon, tiempoInicio) {
    const tiempoFin = tiempoInicio + tablon.tr;

    // Caso 1: Riego perfecto
    if (tiempoInicio === tablon.ro) {
        return tablon.ts - tiempoFin;
    }

    // Caso 2: Antes del límite
    if (tablon.ts - tablon.tr >= tiempoInicio) {
        return 2 * (tablon.ts - tiempoFin);
    }

    // Caso 3: Después del límite
    return 2 * tablon.p * (tiempoFin - tablon.ts);
}

/**
 * Muestra la tabla de análisis de tiempos
 * @param {Array} tablones - Array de tablones
 * @param {Array} permutacion - Array con el orden de riego
 * @param {Array} tiempos - Array con tiempos calculados
 * @param {number} costoTotal - Costo total de la solución
 */
function mostrarAnalisisTiempos(tablones, permutacion, tiempos, costoTotal) {
    const cuerpoAnalisis = document.getElementById('cuerpoAnalisis');
    cuerpoAnalisis.innerHTML = '';

    let costoAcumulado = 0;

    for (let i = 0; i < permutacion.length; i++) {
        const idx = permutacion[i];
        const tablon = tablones[idx];
        const tiempo = tiempos[idx];

        costoAcumulado += tiempo.costo;

        const fila = document.createElement('tr');
        fila.innerHTML = `
            <td>${tiempo.orden}</td>
            <td>T${idx}</td>
            <td>${tiempo.inicio}</td>
            <td>${tiempo.fin}</td>
            <td>${tiempo.costo}</td>
        `;

        cuerpoAnalisis.appendChild(fila);
    }

    // Agregar fila de totales
    const filaTotal = document.createElement('tr');
    filaTotal.className = 'total-row';
    filaTotal.innerHTML = `
        <td colspan="4" style="text-align: right;">COSTO TOTAL:</td>
        <td>${costoTotal}</td>
    `;
    cuerpoAnalisis.appendChild(filaTotal);
}

/**
 * Convierte código de algoritmo a nombre legible
 * @param {string} codigo - "FB", "V" o "PD"
 * @returns {string} - Nombre del algoritmo
 */
function obtenerNombreAlgoritmo(codigo) {
    const nombres = {
        'FB': 'Fuerza Bruta',
        'V': 'Algoritmo Voraz',
        'PD': 'Programación Dinámica'
    };
    return nombres[codigo] || codigo;
}

/**
 * Descarga la solución en formato .txt según los requerimientos del PDF
 */
function descargarSolucion() {
    if (!solucionActual) {
        mostrarError('No hay solución para descargar');
        return;
    }

    // Formato requerido:
    // Costo
    // pi0
    // pi1
    // ...
    let contenido = `${solucionActual.costo}\n`;
    solucionActual.permutacion.forEach(idx => {
        contenido += `${idx}\n`;
    });

    const blob = new Blob([contenido], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `solucion_${solucionActual.algoritmo}.txt`;
    link.click();
    URL.revokeObjectURL(url);
}

/**
 * Carga un archivo .txt con los datos de la finca
 */
function cargarArchivo() {
    const inputArchivo = document.getElementById('inputArchivo');
    const archivo = inputArchivo.files[0];

    if (!archivo) {
        mostrarError('Por favor selecciona un archivo');
        return;
    }

    if (!archivo.name.endsWith('.txt')) {
        mostrarError('El archivo debe tener extensión .txt');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const contenido = e.target.result;
            const lineas = contenido.trim().split('\n');

            if (lineas.length < 2) {
                throw new Error('El archivo debe contener al menos 2 líneas');
            }

            // Parsear número de tablones
            const n = parseInt(lineas[0].trim());
            if (isNaN(n) || n <= 0) {
                throw new Error('El número de tablones debe ser un entero positivo');
            }

            if (lineas.length - 1 !== n) {
                throw new Error(`Se esperaban ${n} tablones pero hay ${lineas.length - 1} líneas de datos`);
            }

            // Limpiar tablones existentes
            tablones = [];
            salidaEsperadaActual = null;
            const cuerpoTabla = document.getElementById('cuerpoTabla');
            cuerpoTabla.innerHTML = '';

            // Parsear cada tablón
            for (let i = 1; i <= n; i++) {
                const partes = lineas[i].trim().split(',');
                if (partes.length !== 4) {
                    throw new Error(`Línea ${i + 1}: formato inválido. Use: ts,tr,p,ro`);
                }

                const ts = parseInt(partes[0].trim());
                const tr = parseInt(partes[1].trim());
                const p = parseInt(partes[2].trim());
                const ro = parseInt(partes[3].trim());

                if (isNaN(ts) || isNaN(tr) || isNaN(p) || isNaN(ro)) {
                    throw new Error(`Línea ${i + 1}: todos los valores deben ser números`);
                }

                agregarTablon({ ts, tr, p, ro });
            }

            console.log(`Archivo cargado: ${n} tablones`);
            inputArchivo.value = ''; // Limpiar input

        } catch (error) {
            mostrarError('Error al procesar archivo: ' + error.message);
        }
    };

    reader.onerror = function() {
        mostrarError('Error al leer el archivo');
    };

    reader.readAsText(archivo);
}

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

/**
 * Carga una lista de ejemplos desde el servidor
 */
async function cargarEjemplos() {
    try {
        mostrarCargando('Obteniendo ejemplos...');
        const respuesta = await fetch('/ejemplos');
        const ejemplos = await respuesta.json();
        ocultarCargando();

        const listado = document.getElementById('listadoEjemplos');
        listado.innerHTML = '';

        const keys = Object.keys(ejemplos).sort((a, b) => {
            const numA = parseInt(a.replace(/\D/g, '')) || 0;
            const numB = parseInt(b.replace(/\D/g, '')) || 0;
            return numA - numB;
        });
        if (keys.length === 0) {
            listado.innerHTML = '<p class="empty-msg">No se encontraron archivos de ejemplo en data/ejemplos/</p>';
        } else {
            for (const key of keys) {
                const datos = ejemplos[key];
                const card = document.createElement('div');
                card.className = 'opcion-ejemplo';
                card.innerHTML = `
                    <div class="ejemplo-info">
                        <h4>${datos.nombre}</h4>
                        <span>${datos.tablones.length} tablones</span>
                    </div>
                    <i class="ph-bold ph-caret-right" style="font-size: 20px; color: var(--text-muted);"></i>
                `;
                card.addEventListener('click', () => {
                    cargarFinca(datos.tablones);
                    salidaEsperadaActual = datos.salidaEsperada;
                    cerrarModal();
                });
                listado.appendChild(card);
            }
        }
        abrirModal();
    } catch (error) {
        ocultarCargando();
        mostrarError(`Error al cargar ejemplos: ${error.message}`);
    }
}

/**
 * Control del Modal
 */
function abrirModal() {
    document.getElementById('modalEjemplo').style.display = 'flex';
}

function cerrarModal() {
    document.getElementById('modalEjemplo').style.display = 'none';
}

/**
 * Inicializa la aplicación
 */
function inicializar() {
    // Asignar eventos a botones
    document.getElementById('btnAgregarTablon').addEventListener('click', () => agregarTablon());
    document.getElementById('btnLimpiar').addEventListener('click', limpiarTablones);
    document.getElementById('btnCargarEjemplo').addEventListener('click', cargarEjemplos);
    document.getElementById('btnCerrarModal').addEventListener('click', cerrarModal);
    const btnCerrarComp = document.getElementById('btnCerrarComparacion');
    if (btnCerrarComp) btnCerrarComp.addEventListener('click', cerrarComparacion);
    document.getElementById('btnEjecutar').addEventListener('click', resolverProblema);
    document.getElementById('btnDescargar').addEventListener('click', descargarSolucion);
    
    document.getElementById('inputArchivo').addEventListener('change', (e) => {
        if (e.target.files.length > 0) cargarArchivo();
    });

    // Cerrar modal al hacer click afuera
    window.addEventListener('click', (e) => {
        const modalEjemplo = document.getElementById('modalEjemplo');
        const modalComparacion = document.getElementById('modalComparacion');
        if (e.target === modalEjemplo) cerrarModal();
        if (e.target === modalComparacion) cerrarComparacion();
    });

    // Evento para el área de upload
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('inputArchivo').files = files;
                cargarArchivo();
            }
        });
    }

    // Seleccionar algoritmo por defecto
    const defaultAlgo = document.querySelector('input[name="algoritmo"][value="V"]');
    if (defaultAlgo) defaultAlgo.checked = true;

    console.log('Aplicación inicializada correctamente');
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
} else {
    inicializar();
}

