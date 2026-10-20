# Tarea 2 — Voces y documentos peruanos: del archivo escaneado al texto buscable

**¿Se pueden convertir documentos escaneados y entrevistas en audio en un archivo de texto
estructurado y buscable?**

Alexander Noblejas (`@AlexNoblejas`) · Python Intermedio, Diplomatura en Ciencia de Datos (QLAB)

| | |
|---|---|
| Dashboard público | `PENDIENTE` |
| CER (OCR elegido) | `PENDIENTE` |
| WER (ASR elegido) | `PENDIENTE` |
| Acuerdo LLM–humano | `PENDIENTE`/20 |

---

## Pipeline

Documentos escaneados y entrevistas en audio → OCR (PaddleOCR) y ASR (faster-whisper con VAD
y diarización) → seudonimización → extracción de campos con un LLM → evaluación con CER y WER
contra referencias transcritas a mano → dashboard de exploración en Streamlit.

Todo lo pesado corre en los notebooks, en local con GPU. El dashboard solo lee CSV.

## Corpus

### Audio — 26 clips, 41 minutos de español peruano, todo CC BY-SA 4.0

Material público de Wikimedia Commons; no se grabó nada. Fuente, autor, licencia y modo de
recuperación de cada clip están en [`datos/fuentes.csv`](datos/fuentes.csv), y el inventario
vive en [`corpus_audio.py`](corpus_audio.py).

| Grupo | Clips | Minutos | Qué es |
|---|---|---|---|
| `calle` | 8 | 15.1 | Entrevistas de calle (Wikimedia Perú y colaboradores, 2022) |
| `conferencia` | 1 | 4.2 | Dirigente de Fenmucarinap en conferencia de prensa |
| `testimonio` | 1 | 8.8 | Testimonio de Lucinda Quispealaya, Junín |
| `resonando` | 14 | 11.2 | Proyecto *Resonando Juntas* (WikiAcción Perú + Asimtría) |
| `ruido` | 2 | 1.7 | Consignas coreadas en marcha: multitud y música |
| **Total** | **26** | **41.0** | mínimo exigido: 20 clips y 30 minutos |

`clip_06` tiene tres voces (entrevistador y dos vendedoras): es el audio de la diarización.
Como reserva para la bonificación hay tres entrevistas en **quechua de Huaylas** del proyecto
*Voces y plantas*, para transcribir con MMS.

Fecha de extracción: `PENDIENTE`. El audio crudo no se versiona; se recupera con:

```bash
python corpus_audio.py
```

### Documentos — 25 (8 impresos, 8 fotos, 9 manuscritos)

`PENDIENTE`: impresos a partir de PDF públicos; fotos y manuscritos, capturas propias sin
datos personales. Fuente y licencia de cada uno en `datos/fuentes.csv`.

## Ética y datos personales

- Las entrevistas de calle nombran personas reales. Todo texto publicado pasa por
  `voz.seudonimizar` (comparación difusa, atrapa nombres mal transcritos) **y** por revisión
  manual: el procedimiento automático no sustituye la lectura humana.
- Los testimonios de *Resonando Juntas* ya fueron recogidos de forma anónima por el proyecto;
  se mantienen anónimos y se citan con su atribución.
- Las descargas respetan las condiciones de Wikimedia: `User-Agent` descriptivo y pausa de
  1,5 s entre peticiones.

## Hallazgos

1. `PENDIENTE`
2. `PENDIENTE`

## Limitaciones

1. `PENDIENTE`
2. `PENDIENTE`

## Cómo ejecutar

Dos entornos a propósito: el del pipeline es pesado y solo vive en local; el del dashboard es
liviano y es el que instala Streamlit Community Cloud.

```bash
# 1. Pipeline (notebooks): OCR, ASR, métricas y LLM
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements-pipeline.txt
python corpus_audio.py            # baja el corpus de audio
jupyter lab                       # 01_extraccion.ipynb y luego 02_evaluacion.ipynb

# 2. Dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

```
tarea_2/
├── 01_extraccion.ipynb        OCR, ASR, seudonimización, limpieza y EDA
├── 02_evaluacion.ipynb        CER/WER, LLM, auditoría y comparación de modelos
├── app.py                     Dashboard Streamlit (solo lee CSV)
├── corpus_audio.py            Inventario y descarga del corpus de audio
├── voz.py                     Herramientas de la sesión 13 (VAD, ASR, diarización, métricas)
├── requirements.txt           Dependencias del dashboard
├── requirements-pipeline.txt  Dependencias de los notebooks
├── evidencias_ia/             Capturas de la conversación con Claude Code
├── datos/
│   ├── fuentes.csv            Fuente, licencia y acceso de cada archivo
│   ├── documentos.csv         Corpus OCR
│   ├── transcripciones.csv    Corpus ASR
│   ├── extraccion_llm.csv     Campos extraídos por el LLM
│   └── ejemplos/              Muestra ligera y publicable para el dashboard
└── modelos/                   Configuraciones y artefactos ligeros
```
