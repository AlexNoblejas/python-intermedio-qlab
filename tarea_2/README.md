# Tarea 2 — Voces y documentos peruanos: del archivo escaneado al texto buscable

**¿Se pueden convertir documentos escaneados y entrevistas en audio en un archivo de texto
estructurado y buscable?**

Alexander Noblejas (`@AlexNoblejas`) · Python Intermedio, Diplomatura en Ciencia de Datos (QLAB)

| | |
|---|---|
| Dashboard público | `PENDIENTE` |
| CER — PaddleOCR sobre 10 documentos | `PENDIENTE` |
| WER — faster-whisper small sobre 10 clips | `PENDIENTE` |
| Acuerdo LLM–humano | `PENDIENTE`/20 |

---

## Qué hace

Documentos escaneados y entrevistas en audio → OCR con PaddleOCR y ASR con faster-whisper
(detección de voz propia y diarización por MFCC) → seudonimización automática **y** revisión
humana → extracción de campos estructurados con un LLM → evaluación con CER y WER contra
transcripciones hechas a mano → dashboard de exploración en Streamlit.

Los modelos corren solo en los notebooks. El dashboard únicamente lee CSV, así que arranca en
segundos y cabe en el plan gratuito de Streamlit Community Cloud.

## Corpus

### Audio — 33 clips, 41.0 minutos de español peruano, todo CC BY-SA 4.0

Material público de Wikimedia Commons; no se grabó nada para esta tarea. Fecha de extracción:
**25 de octubre de 2026**. Fuente, autor, licencia y modo de recuperación de cada archivo están
en [`datos/fuentes.csv`](datos/fuentes.csv); el inventario vive en
[`corpus_audio.py`](corpus_audio.py).

| Grupo | Clips | Minutos | Qué es |
|---|---|---|---|
| `calle` | 8 | 15.1 | Entrevistas de calle, Wikimedia Perú y colaboradores (2022) |
| `conferencia` | 3 | 4.2 | Dirigente de Fenmucarinap en conferencia de prensa |
| `testimonio` | 6 | 8.8 | Testimonio de Lucinda Quispealaya, Junín |
| `resonando` | 14 | 11.2 | Proyecto *Resonando Juntas* (WikiAcción Perú + Asimtría) |
| `ruido` | 2 | 1.7 | Consignas coreadas en marcha: multitud y música |

Los dos audios largos —la conferencia de 4,2 min y el testimonio de 8,8 min— se parten en
bloques de ~90 s cortando en pausas reales del habla. El `clip_06` queda entero a propósito:
tiene tres voces declaradas por la fuente y es el caso de la diarización.

Como reserva para la bonificación hay tres entrevistas en **quechua de Huaylas** del proyecto
*Voces y plantas*, listadas en `corpus_audio.QUECHUA`.

### Documentos — 27: 8 impresos, 10 fotos de celular, 9 manuscritos

- **Impresos:** páginas de cinco Resoluciones de Presidencia de Consejo Directivo del CEPLAN,
  descargadas de gob.pe y renderizadas a 300 dpi. El artículo 9 del Decreto Legislativo 822
  excluye de protección "los textos oficiales de carácter legislativo, administrativo o
  judicial", así que su texto puede publicarse. Los informes y guías del CEPLAN quedaron fuera
  justamente por lo contrario: llevan "© Derechos reservados".
- **Fotos y manuscritos:** capturas propias del estudiante, sin datos personales reales.

## Ética y datos personales

- Las entrevistas de calle nombran personas reales. Todo texto publicado pasa por
  `voz.seudonimizar` —comparación difusa, que atrapa el nombre aunque el modelo lo haya escrito
  mal— **y** por revisión manual, además de un control automático que busca patrones de DNI y
  correos. El procedimiento automático no sustituye la lectura humana.
- Los testimonios de *Resonando Juntas* ya fueron recogidos de forma anónima por el proyecto.
- Las descargas respetan las condiciones de Wikimedia y de gob.pe: `User-Agent` descriptivo y
  pausa de 1,5 s entre peticiones.
- No hay credenciales en el repositorio. La clave del LLM se lee de la variable de entorno
  `GROQ_API_KEY`.

## Hallazgos

1. `PENDIENTE`
2. `PENDIENTE`

## Limitaciones técnicas

1. **Todo corrió en CPU.** `pip install torch` entregó la rueda `+cpu` y reinstalar la de CUDA
   arrastra sus propias restricciones de numpy, el mismo conflicto que rompió el entorno en la
   Tarea 1. Consecuencias concretas: se usó faster-whisper `small` en lugar de un modelo mayor,
   y los factores de tiempo real que aparecen en la comparativa son los de CPU, no los que
   tendría un despliegue con GPU.
2. **La diarización usa MFCC y agrupamiento jerárquico, no un modelo de huellas de voz.**
   `voz.diarizar` depende de `pyannote.audio` y de un modelo restringido en Hugging Face, que
   exige token y aceptar términos. La alternativa implementada separa turnos razonablemente
   —medida sobre el `clip_06`, con las 3 voces declaradas reparte los turnos en 15/11/5 y
   alterna como una entrevista—, pero distingue voces peor que un modelo entrenado para eso:
   sirve para marcar turnos, no para afirmar identidades.
3. **El detector de voz es propio.** El VAD de faster-whisper corre sobre onnxruntime y en esta
   máquina tumbaba el intérprete sin dejar traceback. El de repuesto mide energía con numpy,
   cubre el 100 % del audio cortando en pausas y descarta solo silencio casi absoluto. Un
   umbral relativo más agresivo se comía el 60 % del `clip_06`, porque en una grabación de
   calle el ruido de fondo levanta el umbral por encima de la voz.

## Cómo ejecutar

Dos entornos a propósito: el del pipeline es pesado y vive solo en local; el del dashboard es
liviano y es el que instala Streamlit Community Cloud.

```bash
# 1. Pipeline (notebooks): OCR, ASR, métricas y LLM
python -m venv .venv
.venv\Scripts\activate                 # Windows
pip install -r requirements-pipeline.txt

python corpus_audio.py                 # baja y convierte el audio, y segmenta los largos
python corpus_documentos.py            # baja los PDF y renderiza los impresos a 300 dpi
python 00_verificar_entorno.py         # prueba de humo: mide OCR y ASR antes de lanzar nada

jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=-1 01_extraccion.ipynb

python leer_referencias.py             # carga las transcripciones manuales a los CSV
set GROQ_API_KEY=...                   # la clave no se guarda en el repositorio
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=-1 02_evaluacion.ipynb

python preparar_ejemplos.py            # muestra ligera y publicable para el dashboard

# 2. Dashboard
pip install -r requirements.txt
streamlit run app.py
```

El `--ExecutePreprocessor.timeout=-1` no es opcional: sin él nbconvert aborta cualquier celda
que pase de 30 segundos, y tanto el OCR como el ASR pasan de eso largamente.

## Estructura

```
tarea_2/
├── 01_extraccion.ipynb        OCR, ASR, seudonimización, limpieza y EDA
├── 02_evaluacion.ipynb        CER/WER, LLM, auditoría y comparación de modelos
├── app.py                     Dashboard Streamlit (solo lee CSV)
├── corpus_audio.py            Inventario, descarga, segmentación, VAD y diarización
├── corpus_documentos.py       Descarga y renderizado de los impresos
├── voz.py                     Herramientas de la sesión 13 (sin modificar)
├── 00_verificar_entorno.py    Prueba de humo del entorno
├── leer_referencias.py        Carga las referencias manuales del Excel a los CSV
├── preparar_ejemplos.py       Arma datos/ejemplos/ para el dashboard
├── referencias_plantilla.xlsx Plantilla de transcripción manual (10 + 10)
├── auditoria_humana.xlsx      Auditoría de 20 extracciones del LLM
├── requirements.txt           Dependencias del dashboard
├── requirements-pipeline.txt  Dependencias de los notebooks
├── evidencias_ia/             Capturas de la conversación con Claude Code
├── datos/
│   ├── documentos.csv         Corpus OCR
│   ├── transcripciones.csv    Corpus ASR
│   ├── extraccion_llm.csv     Campos extraídos por el LLM
│   ├── fuentes.csv            Fuente, licencia y acceso de cada archivo
│   ├── clips.csv              Inventario de clips tras la segmentación
│   ├── resultados.json        Métricas que lee el dashboard
│   └── ejemplos/              Muestra ligera y publicable
└── modelos/                   Configuraciones y artefactos ligeros
```

El corpus crudo (`datos/raw/`) y el audio convertido (`datos/audio_16k/`) no se versionan: se
recuperan con los dos scripts de corpus, y `datos/fuentes.csv` documenta de dónde sale cada
archivo.
