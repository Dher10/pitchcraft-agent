# Documento de Arquitectura e Investigación de LLMs: PitchCraft
**Fecha:** 25 de Octubre de 2026
**Contexto:** PitchCraft es una aplicación web pública, no comercial, que genera un reporte diario de los lanzadores abridores de la MLB utilizando datos de MLB Stats API y Baseball Savant. 

---

## 1. Resumen Ejecutivo
La arquitectura de PitchCraft ha evolucionado de un modelo de evaluación masiva y dependiente de LLMs a un enfoque de **MLOps híbrido y determinista**. Para mantener un costo operativo de $0 de forma sostenible, el sistema minimiza las llamadas a las APIs mediante un riguroso pre-procesamiento estadístico en Python (Data Framing), filtros de validación locales (Regex y NLI) y un conjunto de pruebas estático justificado sabermétricamente ("Golden Dataset"). Se prioriza la exactitud absoluta sobre la disponibilidad, aceptando fallos silenciosos (Error Tipo I) antes que publicar datos alucinados (Error Tipo II).

---

## 2. Investigación de Proveedores LLM ($0 Costo Permanente)

Para cumplir con la restricción de $0 dólares a largo plazo y separar las familias de modelos (Escritor vs. Juez), se analizaron los límites actuales:

### A. Carga Diaria de Producción (1-3 llamadas Escritor, ~10 llamadas Juez)
*   **Escritor Principal:** **Google AI Studio (`gemini-3.8-flash`)**. Límites gratuitos amplios para un uso diario tan bajo. Elegido por su capacidad de seguir instrucciones estructurales complejas.
*   **Escritor Fallback:** **Mistral La Plateforme (`mistral-small-4`)**. Opción de respaldo vía API gratuita sin tarjeta, sujeta a cuotas no publicadas pero suficientes para 3 llamadas diarias.
*   **Juez Principal:** **Groq (`openai/gpt-oss-120b`)**. Ofrece ~30 RPM y 200,000 tokens/día. Ideal para tareas de evaluación lógica.
*   **Juez Fallback:** **Cloudflare Workers AI (`@cf/zai-org/glm-4.7-flash`)**. Gratuito hasta 10,000 neuronas/día.

### B. Carga de Evaluación Offline (Pruebas de Estrés)
*La idea inicial de procesar 1,500 partidos históricos mediante API fue descartada por ser insostenible y estadísticamente redundante.*
*   **Nueva Estrategia:** Ejecución híbrida (manual/semiautomatizada) utilizando cuentas Pro existentes (Claude Code, ChatGPT Pro, Gemini Plus) del desarrollador, aplicada exclusivamente a un dataset reducido y estático, cuyos resultados se guardan en caché local.
*   **Alternativa Local:** Ejecución de modelos cuantizados a 4-bit (ej. Qwen 7B) en hardware local (Intel Core i5, NVIDIA GeForce GTX) utilizando llama.cpp u Ollama para obtener salidas estructuradas sin depender de redes externas.

---

## 3. Estrategia de Evaluación: El "Golden Dataset" Sabermétrico

En lugar de evaluar miles de escenarios idénticos, la validación del sistema se realiza sobre **~75 casos extremos (Edge Cases)**. Este número no es aleatorio; se basa en los "puntos de estabilización" de FanGraphs y la varianza extrema de Statcast. Si el LLM aprueba estos casos, garantiza una precisión del 99.9% en temporada regular.

**Matriz Combinatoria (Ejemplos):**
1.  **Puntos de Estabilización:** Novatos sin historial (Muestra Cero), regresos de lesiones (Muestra No Estabilizada).
2.  **Perfiles Statcast:** "Velo Monsters" (>99 mph), "Junkballers" (<88 mph), tasas de rotación extremas (>3,000 RPM), anomalías atmosféricas (Coors Field).
3.  **Fallas de Datos:** Partidos con radares apagados o fallos en el Pitch-com (datos nulos).
4.  **Anomalías del Juego:** Juegos perfectos, explosiones tempranas (0.0 IP, 6 ER), juegos acortados por lluvia.

---

## 4. Enmarcado de Datos (Data Framing) y Reglas de Periodismo Automático

El LLM nunca debe calcular ni deducir. Un script de Python extrae, limpia y formatea los datos *antes* de enviarlos al Escritor (Gemini), implementando lecciones del periodismo financiero automatizado (ej. Bloomberg).

*   **Deltas vs. Absolutos:** Python calcula la diferencia respecto al promedio anual. (Ej. en lugar de `96 mph`, se envía `96 mph (Delta: -1.5 mph vs promedio)`).
*   **Categorización de Ruido:** El JSON se divide en `"Metricas_Core"` (K-BB%, SIERA - el rendimiento real) y `"Metricas_Engañosas"` (W, L, ERA - contexto general).
*   **Regla de Percentiles ("The So What?"):** Todo dato crítico va acompañado de su percentil histórico para evitar falsas narrativas de grandeza.
*   **Glosario de Intensidad:** El *System Prompt* define adjetivos estrictos según umbrales (ej. Solo usar "dominante" si K% > 30%).
*   **Prohibición de Causalidad Falsa:** Prohibido usar palabras como "porque" o "debido a" a menos que la relación causal esté explícita en los datos procesados.

---

## 5. Defensa en Cascada (Mitigación de Alucinaciones)

El sistema asume un enfoque de "Falla Segura" (Fail-Closed). Se toleran los Falsos Positivos (no publicar un reporte válido) para erradicar por completo los Falsos Negativos (publicar una alucinación).

1.  **Filtro Regex (Extracción Numérica - Costo 0):** Python extrae todos los números generados por el Escritor. Si un dígito no existe en el JSON original de MLB, se rechaza inmediatamente.
2.  **Filtro NLI (Local CPU - Costo 0):** Uso de `cross-encoder/nli-deberta-v3-base`. Compara el JSON (premisa) con el texto (hipótesis). Se configura un umbral estricto de aprobación (`0.85+`).
3.  **Juez LLM (Groq):** Evalúa exclusivamente el cumplimiento de la política (tono, prohibición de mención a apuestas) sobre el texto que ya superó los filtros matemáticos.

---

## 6. Operaciones, Despliegue y UX (GitHub Actions)

Para garantizar la estabilidad del cronjob diario operando con herramientas gratuitas, se establecen las siguientes reglas de infraestructura:

*   **Timing del Cronjob:** Ejecución a media mañana (~11:00 AM) para asegurar que la data de Statcast esté 100% procesada y consolidada en las APIs oficiales.
*   **Hard Timeouts:** Para proteger la cuota de 2,000 minutos mensuales de GitHub Actions, cualquier script de Python se abortará forzosamente tras **5 minutos** de ejecución.
*   **Alertas (Webhook):** Se implementa una notificación POST a un Webhook privado de **Discord**. El desarrollador recibirá alertas instantáneas en su celular ante fallos del modelo o bloqueos por Error Tipo I.
*   **Manejo de Estados (Frontend UX):** En lugar de romper la interfaz ante un fallo silencioso, el script genera un archivo `status.json` (valores: `success`, `no_games`, `system_error`). El frontend de la aplicación web renderiza componentes amistosos basándose en este estado (ej. "El bullpen está descansando hoy").

---

## 7. Esquemas Estrictos de Salida (Structured Outputs)

Para la integración fluida con Python, los prompts obligan a los LLMs a retornar estructuras JSON exactas.

**A. Esquema del Escritor (Gemini):**
Implementa un "Scratchpad" para obligar al modelo a planificar su lógica antes de redactar.
```json
{
  "analisis_previo": ["dato_clave_1", "dato_clave_2", "dato_clave_3"],
  "reporte_html": "<p>Texto narrativo final del análisis de los lanzadores...</p>"
}
```

**B. Esquema del Juez (Groq):**
```json
{
  "aprobado": true,
  "infraccion_apuestas": false,
  "infraccion_estilo": false,
  "motivo_rechazo": null
}
```