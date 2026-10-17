# 🗞️ Tarea 1 — Del titular al clasificador

**Alexander Noblejas** · Python Intermedio, Diplomatura en Ciencia de Datos (QLAB) · Opción **C — Comparada**

> Las líneas marcadas con `COMPLETAR` se llenan con los números de tu corrida.
> Los dos notebooks los imprimen: el 1 al final de la recolección y el 2 en la celda de métricas.

---

## 1. Pregunta del proyecto

**¿Pueden convertir titulares peruanos en un clasificador de noticias?**

El trabajo recolecta noticias reales de dos diarios peruanos, las etiqueta de forma
semi-supervisada con un LLM que corre en local, audita a mano una muestra de esas
etiquetas, ajusta un Transformer ligero sobre ellas y despliega un dashboard donde
cualquiera puede escribir un titular nuevo y ver la categoría predicha con su confianza.

Categorías: `politica`, `economia`, `deportes`, `ciencia_tecnologia`.

---

## 2. Medios y fechas de extracción

| | |
|---|---|
| **Opción** | C — Comparada (objetivo 200+200; ver limitación de volumen abajo) |
| **Medios** | La República (`larepublica.pe`) · El Comercio (`elcomercio.pe`) |
| **Fecha de descarga** | 17 de octubre de 2026 |
| **Ventana de publicación cubierta** | 8–17 de octubre de 2026 (~10 días; 1 nota atípica de abril se aísla) |
| **Volumen final** | 408 noticias (59 La República + 349 El Comercio) |

### Cómo se extrajo, y por qué así

Ambos diarios publican RSS oficiales, pero **cada feed trae solo 15–25 notas**: cuatro
secciones por medio dan unas 80 filas, muy por debajo de las 350+ que pide la tarea.
La República además prohíbe `/*/pag/*` en su `robots.txt`, así que paginar las secciones
no era una opción.

La recolección combina dos fuentes que el `robots.txt` **permite de forma explícita**:

| Fuente | Qué aporta | Endpoint |
|---|---|---|
| RSS | Titular y bajada ya limpios, de las notas recientes | `larepublica.pe/rss/{sección}.xml` · `elcomercio.pe/arc/outboundfeeds/google-news-feed/category/{sección}/?outputType=xml` |
| Sitemaps de sección | El volumen: cientos de URLs con fecha. El de El Comercio es un *índice* que apunta a sub-sitemaps, que el código sigue en profundidad | `larepublica.pe/sitemap/{sección}.xml` · `elcomercio.pe/sitemap/{sección}/?outputType=xml` |

De cada nota del sitemap se leen los metadatos Open Graph (`og:title`, `og:description`),
que es donde ambos diarios publican titular y bajada de forma estable.

**Buenas prácticas aplicadas:** `User-Agent` descriptivo que identifica el uso académico,
pausa aleatoria de 1 a 2 segundos entre peticiones, un solo reintento, y caché en disco de
cada respuesta (`datos/raw/`) para que la corrida sea reanudable y no se vuelva a pedir
nada que ya se descargó.

### Mapeo de secciones a categorías

| Medio | Sección del diario | Categoría final |
|---|---|---|
| La República | `politica` | `politica` |
| La República | `economia` | `economia` |
| La República | `deportes` | `deportes` |
| La República | `ciencia` | `ciencia_tecnologia` |
| El Comercio | `politica` | `politica` |
| El Comercio | `economia` | `economia` |
| El Comercio | `deporte-total` | `deportes` |
| El Comercio | `tecnologia` | `ciencia_tecnologia` |

Las notas cuya sección no cae en ninguna de las cuatro se **descartan y se reportan** en el
notebook. No se inventó una quinta categoría.

---

## 3. Dos hallazgos analíticos

**Hallazgo 1 — `COMPLETAR`**

> Pistas de dónde suele salir: la brecha entre el F1 del Transformer y el piso zero-shot;
> qué categoría salió mejor y cuál peor en la matriz de confusión; si `politica` y
> `economia` se confunden entre sí como es de esperar en noticias peruanas (presupuesto,
> AFP, minería son a la vez política y economía).

**Hallazgo 2 — `COMPLETAR`**

> Pistas: el acuerdo entre la etiqueta del LLM y la sección del diario (el notebook 2 lo
> imprime como porcentaje y como tabla cruzada). Dónde discrepan más, y si la opción C
> deja ver que los dos diarios archivan la misma clase de nota en secciones distintas —
> que es justamente el análisis de sesgo comparativo que la tarea ofrece como bonus.

---

## 4. Dos limitaciones técnicas

**Limitación 1 — Las etiquetas de entrenamiento no son verdad de oro.**
El modelo se entrenó sobre etiquetas generadas por un LLM, así que hereda sus sesgos y sus
errores sistemáticos. El F1 reportado mide **concordancia con el LLM**, no corrección
absoluta. Por eso el notebook 2 reporta además el F1 contra la sección del diario, que
nunca participó del entrenamiento: la brecha entre ambas cifras es la medida honesta de
cuánto queda por fuera.

**Limitación 2 — La ventana temporal es corta y el test es pequeño.**
El corpus retrata una coyuntura de pocos días, no un periodo largo: si esos días estuvieron
dominados por un tema (una crisis política, un torneo), el clasificador aprende esa
coyuntura y no el lenguaje estable de cada sección. Y con ~15% del dataset como test, cada
error individual mueve el F1 varios puntos, así que las métricas tienen varianza alta.

---

## 5. Cómo ejecutar en local

```bash
# 1. Entorno
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Etiquetado con LLM local — Ollama tiene que estar corriendo
ollama serve                       # en otra terminal
ollama pull qwen2.5:7b

# 3. Notebooks, en orden
jupyter lab
#   -> 01_recoleccion.ipynb     (scraping, limpieza, EDA  -> datos/noticias.csv)
#   -> 02_clasificacion.ipynb   (zero-shot, LLM, fine-tuning -> modelo/)

# 4. Dashboard
streamlit run app.py               # abre http://localhost:8501
```

**Nota sobre la GPU.** El notebook 2 detecta automáticamente CUDA (NVIDIA), MPS (Mac con
Apple Silicon) o CPU, y entrena sobre lo que encuentre. La celda de detección imprime qué
dispositivo está usando — vale la pena mirarla antes de entrenar, porque la diferencia
entre GPU y CPU es de minutos contra media hora.

### Despliegue (opcional)

Los pesos superan los 100 MB y están en `.gitignore`, así que Streamlit Community Cloud no
los verá en el repo. Para desplegar: sube el modelo a Hugging Face Hub (sección 9 del
notebook 2) y define el secreto `HF_MODEL_ID = "usuario/repositorio"` en Streamlit.

Enlace del dashboard: `COMPLETAR` (o indicar ejecución local comprobada).

---

## Estructura

```
tarea_1/
├── 01_recoleccion.ipynb      Scraping (RSS + sitemaps), limpieza y EDA
├── 02_clasificacion.ipynb    Zero-shot, etiquetado LLM, auditoría, fine-tuning, evaluación
├── app.py                    Dashboard Streamlit con probador en vivo
├── requirements.txt
├── README.md
├── .gitignore
├── datos/
│   ├── noticias.csv              dataset final, 7 columnas
│   ├── etiquetas_llm.csv         etiquetas del LLM con su confianza
│   ├── auditoria_humana.csv      los 20 casos revisados a mano
│   ├── particion.csv             qué fila cayó en train / val / test
│   ├── figs/                     matriz de confusión
│   └── raw/                      respaldo crudo (ignorado por git)
└── modelo/
    ├── config.json, tokenizer*   artefactos ligeros, sí se versionan
    ├── metricas.json             lo que lee el dashboard
    └── *.safetensors             pesos (ignorados por git)
```

## Resultados

| | |
|---|---|
| F1 macro en test (ref. etiquetas LLM) | `COMPLETAR` |
| F1 macro en test (ref. sección del diario) | `COMPLETAR` |
| F1 macro zero-shot | `COMPLETAR` |
| Acuerdo LLM vs. auditoría humana | `COMPLETAR`/20 |
| Latencia del clasificador | `COMPLETAR` ms por titular |
