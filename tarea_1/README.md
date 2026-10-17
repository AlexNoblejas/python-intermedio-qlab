# 🗞️ Tarea 1 — Del titular al clasificador

**Alexander Noblejas** · Python Intermedio, Diplomatura en Ciencia de Datos (QLAB) · Opción **C — Comparada**

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

**Hallazgo 1 — El fine-tuning le saca +0.38 de F1 al zero-shot (0.89 vs 0.51).**
Con solo 284 titulares de entrenamiento —etiquetados por el LLM, sin una sola etiqueta hecha
a mano— DistilBERT multilingüe alcanza **F1 macro 0.89** (accuracy 0.90) en el test reservado,
frente a **0.51** del zero-shot NLI sobre ese mismo test. Y lo hace en **48 ms por titular**,
unas 9 veces más rápido que el zero-shot (~450 ms). Destilar el criterio de un LLM pesado a un
clasificador ligero no solo es viable: rinde mucho más y corre en milisegundos, que es el
argumento para llevarlo a producción.

**Hallazgo 2 — El modelo generaliza en vez de solo imitar al LLM; los errores viven en la
frontera economía/tecnología.** El F1 contra la **sección real del diario** (0.894) es casi
idéntico al F1 contra las etiquetas del LLM (0.891): el clasificador no se limitó a copiar los
sesgos del LLM, aprendió una señal que coincide con cómo los propios diarios archivan sus notas.
Por categoría, `politica` (F1 0.97) y `deportes` (0.97) salen casi perfectas, mientras
`ciencia_tecnologia` (0.78) y `economia` (0.84) son las más débiles y se confunden entre sí:
muchas notas de tecnología son también de negocio (despidos de Netflix, productos,
infraestructura). Es exactamente la frontera que marcó la auditoría humana (caso #15, una feria
de infraestructura que el LLM mandó a `politica`). El acuerdo LLM–humano de **19/20** y el
acuerdo LLM–sección de **87.7%** confirman que la supervisión débil es confiable salvo en esos
casos de frontera.

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

Enlace del dashboard: ejecución local comprobada con `streamlit run app.py` (los pesos del modelo pesan ~540 MB y no se versionan; ver Despliegue para subirlo a HF Hub).

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
| F1 macro en test (ref. etiquetas LLM) | **0.891** |
| F1 macro en test (ref. sección del diario) | 0.894 |
| F1 macro zero-shot (mismo test) | 0.511 |
| Acuerdo LLM vs. auditoría humana | 19/20 |
| Latencia del clasificador | 47.6 ms por titular (CPU) |
