"""Dashboard de la Tarea 2 — Voces y documentos peruanos.

    streamlit run app.py

Lee únicamente los CSV y el JSON que producen los notebooks: no ejecuta OCR, ASR ni LLM, así
que arranca en segundos y cabe en el plan gratuito de Streamlit Community Cloud.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"

st.set_page_config(page_title="Voces y documentos peruanos", page_icon="🎙️", layout="wide")


@st.cache_data
def cargar():
    def csv(nombre, **kw):
        ruta = DATOS / nombre
        return pd.read_csv(ruta, **kw) if ruta.exists() else pd.DataFrame()

    res = {}
    if (DATOS / "resultados.json").exists():
        res = json.loads((DATOS / "resultados.json").read_text(encoding="utf-8"))

    llm = csv("extraccion_llm.csv")
    campos = {}
    if len(llm):
        for r in llm.itertuples():
            try:
                campos[r.id] = json.loads(r.campos_json)
            except Exception:
                campos[r.id] = {}

    return (csv("documentos.csv"), csv("transcripciones.csv"), csv("fuentes.csv"),
            csv("evaluacion_documentos.csv"), csv("evaluacion_audio.csv"),
            csv("comparativa_modelos.csv"), llm, campos, res)


docs, trans, fuentes, ev_doc, ev_aud, comparativa, llm, campos, res = cargar()

if docs.empty and trans.empty:
    st.error("No hay datos todavía. Ejecuta `01_extraccion.ipynb` y `02_evaluacion.ipynb`.")
    st.stop()

for df, col in ((docs, "texto_ocr"), (docs, "texto_referencia"),
                (trans, "texto_asr"), (trans, "texto_referencia")):
    if col in df:
        df[col] = df[col].fillna("")


def metrica(valor, formato="{:.3f}"):
    return "—" if valor is None or valor != valor else formato.format(valor)


# ───────────────────────────────────────────────────────────── encabezado
st.title("¿Se puede convertir un archivo escaneado y una entrevista en texto buscable?")
st.caption("Alexander Noblejas · Python Intermedio, Diplomatura en Ciencia de Datos (QLAB) · "
           "Tarea 2")

with st.expander("Cómo se construyó esto", expanded=False):
    st.markdown(f"""
**Pipeline.** Documentos escaneados y entrevistas en audio → OCR con PaddleOCR y ASR con
faster-whisper (VAD propio por energía y diarización por MFCC) → seudonimización revisada a
mano → extracción de campos con un LLM → evaluación con CER y WER contra transcripciones
**hechas a mano** sobre 10 documentos y 10 clips elegidos antes de correr cualquier modelo.

**Corpus.** {res.get('n_documentos', len(docs))} documentos en tres tipos —impresos, fotos de
celular y manuscritos— y {res.get('n_clips', len(trans))} clips con
{res.get('minutos_audio', '—')} minutos de español peruano. El audio es material CC BY-SA 4.0
de Wikimedia Commons; los impresos son páginas de resoluciones del CEPLAN, textos oficiales de
carácter administrativo sin protección por el art. 9 del DL 822; las fotos y los manuscritos
son capturas propias sin datos personales reales.

**Modelos.** OCR: {res.get('modelo_ocr', '—')} · ASR: {res.get('modelo_asr', '—')} ·
LLM: {res.get('modelo_llm', '—')}. Todo corrió en CPU.

**Ética.** Todo texto publicado pasó por seudonimización automática con comparación difusa
**y** por revisión humana. Las descargas respetaron las condiciones de Wikimedia:
User-Agent descriptivo y pausa de 1,5 s entre peticiones.
""")

c = st.columns(5)
c[0].metric("Documentos procesados", res.get("n_documentos", len(docs)))
c[1].metric("Minutos transcritos", res.get("minutos_audio", "—"))
c[2].metric("CER · OCR", metrica(res.get("CER")), help="Sobre los 10 documentos de la muestra")
c[3].metric("WER · ASR", metrica(res.get("WER")), help="Sobre los 10 clips de la muestra")
c[4].metric("Acuerdo LLM–humano",
            metrica(res.get("acuerdo_llm_humano"), "{:.0%}"),
            help="Extracciones correctas en la auditoría manual de 20 casos")

resumen, tab_doc, tab_aud, tab_mod = st.tabs(
    ["Resumen", "Documentos", "Audios", "Modelos"])

# ───────────────────────────────────────────────────────────── resumen
with resumen:
    izq, der = st.columns(2)
    if len(docs):
        g = docs.tipo.value_counts().reindex(["impreso", "foto", "manuscrito"]).dropna()
        fig = px.bar(g.reset_index(), x="tipo", y="count", color="tipo", text="count",
                     title="Los manuscritos son el grupo más numeroso: el caso difícil del corpus",
                     labels={"tipo": "Tipo de documento", "count": "Documentos"})
        fig.update_layout(showlegend=False, title_font_size=14)
        izq.plotly_chart(fig, use_container_width=True)

    if len(trans):
        fig = px.bar(trans.sort_values("duracion_seg"), x="id", y="duracion_seg", color="grupo",
                     title="Segmentar los audios largos dejó clips parejos, sin que ninguno "
                           "domine el corpus",
                     labels={"id": "Clip", "duracion_seg": "Duración (s)", "grupo": "Condición"})
        fig.update_layout(title_font_size=14, xaxis_tickangle=-60, showlegend=False)
        der.plotly_chart(fig, use_container_width=True)

    if len(ev_aud) and "wer_whisper_small" in ev_aud:
        fig = px.bar(ev_aud.sort_values("wer_whisper_small"), x="id", y="wer_whisper_small",
                     color="grupo", title="El error del ASR no se reparte igual: la condición de "
                                          "grabación manda más que la duración",
                     labels={"id": "Clip", "wer_whisper_small": "WER", "grupo": "Condición"})
        fig.update_layout(title_font_size=14)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Fuentes y licencias")
    if len(fuentes):
        st.dataframe(fuentes, use_container_width=True, height=260)
        st.download_button("Descargar fuentes.csv", fuentes.to_csv(index=False),
                           "fuentes.csv", "text/csv")

# ───────────────────────────────────────────────────────────── documentos
with tab_doc:
    st.subheader("Buscar en los textos extraídos")
    f1, f2 = st.columns([2, 1])
    consulta = f1.text_input("Palabra o frase en el texto OCR", key="q_doc",
                             placeholder="por ejemplo: resolución, inteligencia artificial…")
    tipos = f2.multiselect("Tipo de documento", sorted(docs.tipo.unique()),
                           default=sorted(docs.tipo.unique()))

    vista = docs[docs.tipo.isin(tipos)]
    if consulta.strip():
        vista = vista[vista.texto_ocr.str.contains(consulta.strip(), case=False, na=False)]
    st.caption(f"{len(vista)} de {len(docs)} documentos")

    cols = [c for c in ("id", "tipo", "n_caracteres", "confianza_media", "segundos_ocr",
                        "modelo_ocr", "fuente") if c in vista]
    st.dataframe(vista[cols], use_container_width=True, height=240)
    st.download_button("Descargar la selección en CSV", vista.to_csv(index=False),
                       "documentos_filtrados.csv", "text/csv", key="dl_doc")

    st.divider()
    st.subheader("Explorador de documentos")
    elegido = st.selectbox("Documento", vista.id.tolist() or docs.id.tolist(), key="sel_doc")
    fila = docs[docs.id == elegido].iloc[0]

    izq, der = st.columns([1, 1])
    imagen = AQUI / "datos" / "ejemplos" / "imagenes" / f"{elegido}.jpg"
    with izq:
        if imagen.exists():
            st.image(str(imagen), caption=f"{elegido} · {fila.tipo}", use_container_width=True)
        else:
            st.info("La imagen de este documento no se publica; su texto y metadatos sí están "
                    "disponibles.")
        ev = ev_doc[ev_doc.id == elegido] if len(ev_doc) else pd.DataFrame()
        if len(ev) and "cer_paddleocr" in ev:
            m = st.columns(2)
            m[0].metric("CER PaddleOCR", metrica(ev.cer_paddleocr.iloc[0]))
            if "cer_ocr2" in ev:
                m[1].metric("CER segundo OCR", metrica(ev.cer_ocr2.iloc[0]))

    with der:
        st.markdown("**Texto extraído por el OCR**")
        st.text_area("ocr", fila.texto_ocr or "(vacío)", height=220, label_visibility="collapsed")
        if str(fila.texto_referencia).strip():
            with st.expander("Transcripción de referencia, hecha a mano"):
                st.write(fila.texto_referencia)

    if elegido in campos:
        st.markdown("**Campos extraídos por el LLM**")
        st.json(campos[elegido])

# ───────────────────────────────────────────────────────────── audios
with tab_aud:
    st.subheader("Buscar en las transcripciones")
    f1, f2, f3 = st.columns([2, 1, 1])
    consulta = f1.text_input("Palabra o frase en el texto ASR", key="q_aud",
                             placeholder="por ejemplo: Perú, hospital, mujeres…")
    grupos = f2.multiselect("Condición de grabación", sorted(trans.grupo.unique()),
                            default=sorted(trans.grupo.unique()))
    maximo = int(trans.duracion_seg.max()) + 1
    dur = f3.slider("Duración (s)", 0, maximo, (0, maximo))

    vista = trans[trans.grupo.isin(grupos) & trans.duracion_seg.between(*dur)]
    if consulta.strip():
        vista = vista[vista.texto_asr.str.contains(consulta.strip(), case=False, na=False)]
    st.caption(f"{len(vista)} de {len(trans)} clips · "
               f"{vista.duracion_seg.sum() / 60:.1f} de {trans.duracion_seg.sum() / 60:.1f} min")

    cols = [c for c in ("id", "grupo", "duracion_seg", "n_hablantes", "n_palabras",
                        "factor_tiempo_real", "modelo_asr") if c in vista]
    st.dataframe(vista[cols], use_container_width=True, height=240)
    st.download_button("Descargar la selección en CSV", vista.to_csv(index=False),
                       "transcripciones_filtradas.csv", "text/csv", key="dl_aud")

    st.divider()
    st.subheader("Explorador de audios")
    elegido = st.selectbox("Clip", vista.id.tolist() or trans.id.tolist(), key="sel_aud")
    fila = trans[trans.id == elegido].iloc[0]

    audio = AQUI / "datos" / "ejemplos" / "audio" / f"{elegido}.wav"
    if audio.exists():
        st.audio(str(audio))
    else:
        st.info("Este clip no se publica como archivo; su transcripción y metadatos sí. "
                "El original está en Wikimedia Commons, con su enlace en `fuentes.csv`.")

    m = st.columns(4)
    m[0].metric("Duración", f"{fila.duracion_seg:.0f} s")
    m[1].metric("Hablantes detectados", int(fila.n_hablantes))
    m[2].metric("Palabras", int(fila.n_palabras) if "n_palabras" in fila else "—")
    m[3].metric("Factor de tiempo real",
                f"x{fila.factor_tiempo_real:.2f}" if "factor_tiempo_real" in fila else "—")

    ev = ev_aud[ev_aud.id == elegido] if len(ev_aud) else pd.DataFrame()
    if len(ev) and "wer_asr2" in ev and ev.wer_asr2.notna().any():
        izq, der = st.columns(2)
        izq.markdown(f"**{res.get('modelo_asr', 'modelo base')}** · "
                     f"WER {metrica(ev.wer_whisper_small.iloc[0])}")
        izq.text_area("a", ev.texto_asr.iloc[0], height=200, label_visibility="collapsed")
        der.markdown(f"**{res.get('segundo_asr', 'segundo modelo')}** · "
                     f"WER {metrica(ev.wer_asr2.iloc[0])}")
        der.text_area("b", ev.texto_asr2.iloc[0], height=200, label_visibility="collapsed")
    else:
        st.markdown("**Transcripción**")
        st.text_area("asr", fila.texto_asr or "(vacío)", height=200,
                     label_visibility="collapsed")

    if str(fila.texto_referencia).strip():
        with st.expander("Transcripción de referencia, hecha a mano"):
            st.write(fila.texto_referencia)

    if elegido in campos:
        st.markdown("**Campos extraídos por el LLM**")
        st.json(campos[elegido])

# ───────────────────────────────────────────────────────────── modelos
with tab_mod:
    st.subheader("Comparación de modelos sobre las mismas muestras")
    if len(comparativa):
        st.dataframe(comparativa, use_container_width=True)
        fig = px.bar(comparativa.dropna(subset=["valor"]), x="modelo", y="valor",
                     color="modalidad", text="valor",
                     title="Dos modelos por modalidad, medidos sobre los mismos 10 casos",
                     labels={"valor": "CER / WER", "modelo": ""})
        fig.update_layout(title_font_size=14, xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("La comparativa aparece al ejecutar `02_evaluacion.ipynb`.")

    if len(ev_doc):
        st.markdown("**CER por tipo de documento**")
        cols = [c for c in ("cer_paddleocr", "cer_ocr2") if c in ev_doc]
        st.dataframe(ev_doc.groupby("tipo")[cols].mean().round(3), use_container_width=True)
    if len(ev_aud):
        st.markdown("**WER por condición de grabación**")
        cols = [c for c in ("wer_whisper_small", "wer_asr2") if c in ev_aud]
        st.dataframe(ev_aud.groupby("grupo")[cols].mean().round(3), use_container_width=True)

    st.caption("Las métricas se calculan contra transcripciones hechas a mano, sobre los mismos "
               "10 documentos y 10 clips para todos los modelos. La muestra se fijó antes de "
               "correr cualquier modelo.")
