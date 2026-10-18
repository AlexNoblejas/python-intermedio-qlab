"""
Dashboard — Tarea 1: ¿Pueden convertir titulares peruanos en un clasificador de noticias?

Ejecucion local:
    streamlit run app.py

El modelo se busca, en este orden:
  1. ./modelo  (lo que deja 02_clasificacion.ipynb)
  2. el repositorio de Hugging Face indicado en HF_MODEL_ID
     (variable de entorno o secreto de Streamlit, para el despliegue en la nube)
"""
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
CATEGORIAS = ["politica", "economia", "deportes", "ciencia_tecnologia"]
PALETA = {"politica": "#2E5A88", "economia": "#2E8B6F",
          "deportes": "#C25E1E", "ciencia_tecnologia": "#7A4E9E"}

st.set_page_config(page_title="Titulares peruanos → categoría",
                   page_icon="🗞️", layout="wide")


# ──────────────────────────── carga ────────────────────────────
@st.cache_data
def cargar_noticias() -> pd.DataFrame:
    df = pd.read_csv(BASE / "datos" / "noticias.csv").fillna({"bajada": ""})
    df["largo_titular"] = df["titular"].str.len()
    return df


@st.cache_data
def cargar_metricas() -> dict:
    ruta = BASE / "modelo" / "metricas.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _origen_modelo():
    local = BASE / "modelo"
    tiene_pesos = list(local.glob("*.safetensors")) or list(local.glob("pytorch_model*.bin"))
    if (local / "config.json").exists() and tiene_pesos:
        return str(local)
    hub = os.getenv("HF_MODEL_ID")
    if not hub:
        try:
            hub = st.secrets.get("HF_MODEL_ID")
        except Exception:
            hub = None
    return hub


@st.cache_resource(show_spinner="Cargando el clasificador…")
def cargar_clasificador():
    origen = _origen_modelo()
    if not origen:
        return None
    from transformers import pipeline
    return pipeline("text-classification", model=origen,
                    top_k=None, truncation=True, max_length=96)


# ──────────────────────────── encabezado ────────────────────────────
st.markdown(
    "<h1 style='text-align:center;margin-bottom:0'>🗞️ ¿Pueden convertir titulares "
    "peruanos en un clasificador de noticias?</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#555;font-size:1.02rem'>"
    "Noticias reales de <b>La República</b> y <b>El Comercio</b>, etiquetadas de forma "
    "semi-supervisada con un LLM local, auditadas a mano en 20 casos y usadas para ajustar "
    "un Transformer ligero. Abajo puedes explorar el corpus y <b>probar un titular nuevo "
    "en vivo</b>.</p>",
    unsafe_allow_html=True,
)
st.divider()

df = cargar_noticias()
met = cargar_metricas()

# ──────────────────────────── filtros ────────────────────────────
st.sidebar.header("Filtros")
medios = st.sidebar.multiselect("Medio", sorted(df["medio"].unique()),
                                default=sorted(df["medio"].unique()))
cats = st.sidebar.multiselect("Categoría", CATEGORIAS, default=CATEGORIAS)
vista = df[df["medio"].isin(medios) & df["etiqueta"].isin(cats)]

st.sidebar.divider()
st.sidebar.caption(
    f"**Metodología**\n\n"
    f"- Modelo base: `{met.get('modelo_base', 'n/d')}`\n"
    f"- Etiquetado: `{met.get('modelo_llm', 'n/d')}`\n"
    f"- Split 70/15/15, semilla 42\n"
    f"- Entrenado en `{met.get('dispositivo', 'n/d')}` "
    f"({met.get('minutos_entrenamiento', '—')} min)"
)

# ──────────────────────────── indicadores ────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Noticias recolectadas", f"{len(df)}",
          delta=f"{len(vista)} con los filtros actuales" if len(vista) != len(df) else None)

if "f1_macro_test" in met:
    c2.metric("F1 macro en test (titular + bajada)", f"{met['f1_macro_test']:.3f}",
              delta=f"{met['f1_macro_test'] - met.get('f1_zero_shot_test', 0):+.3f} vs. zero-shot")
else:
    c2.metric("F1 macro en test (titular + bajada)", "N/D", help="Ejecuta 02_clasificacion.ipynb")

if met.get("auditoria_acuerdo") is not None:
    ok, tot = met["auditoria_acuerdo"], met.get("auditoria_total", 20)
    c3.metric("Concordancia LLM vs. humano", f"{ok}/{tot}", delta=f"{ok/tot:.0%}")
else:
    c3.metric("Concordancia LLM vs. humano", "N/D", help="Completa la auditoría de 20 casos")

st.divider()

# ──────────────────────────── exploración ────────────────────────────
izq, der = st.columns([3, 2])

with izq:
    st.subheader("Cobertura por categoría")
    if len(vista):
        conteo = vista.groupby(["etiqueta", "medio"]).size().reset_index(name="noticias")
        fig = px.bar(conteo, x="etiqueta", y="noticias", color="medio",
                     barmode="group", text="noticias",
                     labels={"etiqueta": "Categoría", "noticias": "Noticias", "medio": "Medio"})
        fig.update_layout(template="plotly_white", height=380,
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ningún dato con los filtros elegidos.")

with der:
    st.subheader("Largo del titular")
    if len(vista):
        fig2 = px.box(vista, x="medio", y="largo_titular", color="medio", points=False,
                      labels={"medio": "", "largo_titular": "Caracteres"})
        fig2.update_layout(template="plotly_white", height=380, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

st.subheader("Datos")
st.dataframe(
    vista[["titular", "bajada", "medio", "seccion_original", "etiqueta", "fecha", "url"]],
    use_container_width=True, hide_index=True,
    column_config={"url": st.column_config.LinkColumn("Enlace", display_text="abrir")},
)
st.download_button("⬇️ Descargar la selección en CSV",
                   vista.to_csv(index=False).encode("utf-8"),
                   "noticias_filtradas.csv", "text/csv")

st.divider()

# ──────────────────────────── probador en vivo ────────────────────────────
st.subheader("🔎 Probador en vivo")
st.caption("Escribe o pega un titular y el clasificador entrenado predice su categoría.")
if "f1_macro_test_solo_titular" in met:
    st.caption(
        f"Evaluación con solo titulares, como este probador: F1 macro "
        f"{met['f1_macro_test_solo_titular']:.3f} en las mismas 62 noticias de test. "
        "El indicador superior corresponde a titular + bajada. La confianza es "
        "la probabilidad asignada por el modelo; no está calibrada como garantía de acierto."
    )


EJEMPLOS = {
    "— escribe el tuyo —": "",
    "Política": "Congreso aprueba por insistencia la ley que recorta facultades al Ejecutivo",
    "Economía": "El BCR mantiene la tasa de referencia en 4,25% ante la desaceleración del consumo",
    "Deportes": "Alianza Lima venció 2-0 a Universitario en el Monumental y es puntero del Clausura",
    "Ciencia y tecnología": "Investigadores peruanos secuencian el genoma de una papa nativa resistente a la sequía",
}
elegido = st.selectbox("Ejemplos", list(EJEMPLOS), index=0)
texto = st.text_area("Titular", value=EJEMPLOS[elegido], height=90,
                     placeholder="Ej.: Alianza Lima venció 2-0 a Universitario en el Monumental")

if st.button("Clasificar", type="primary"):
    if not texto.strip():
        st.warning("Escribe un titular primero.")
    else:
        clf = cargar_clasificador()
        if clf is None:
            st.error(
                "No encuentro el modelo. Ejecuta `02_clasificacion.ipynb` (deja los pesos "
                "en `modelo/`) o define `HF_MODEL_ID` si lo subiste a Hugging Face."
            )
        else:
            salida = clf(texto.strip())
            if salida and isinstance(salida[0], list):
                salida = salida[0]
            res = (pd.DataFrame(salida)
                     .rename(columns={"label": "categoria", "score": "probabilidad"})
                     .sort_values("probabilidad", ascending=False)
                     .reset_index(drop=True))
            top = res.iloc[0]
            a, b = st.columns([1, 2])
            with a:
                st.success(f"**{top['categoria']}**")
                st.metric("Confianza", f"{top['probabilidad']:.1%}")
                if top["probabilidad"] < 0.60:
                    st.warning("Confianza baja: el titular es ambiguo entre categorías.")
            with b:
                figp = px.bar(res, x="probabilidad", y="categoria", orientation="h",
                              range_x=[0, 1], color="categoria",
                              color_discrete_map=PALETA, text_auto=".1%")
                figp.update_layout(template="plotly_white", height=250,
                                   showlegend=False, yaxis_title="", xaxis_title="")
                st.plotly_chart(figp, use_container_width=True)

st.divider()
st.caption(
    "Tarea 1 — Python Intermedio, Diplomatura en Ciencia de Datos (QLAB). "
    "Datos recolectados respetando el `robots.txt` de cada medio, con pausas de 1–2 s "
    "entre peticiones."
)
