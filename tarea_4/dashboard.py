"""Dashboard opcional. No entrena modelos; muestra solo resultados ejecutados."""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Observatorio socioeconomico - Peru", page_icon="📊", layout="wide")
st.title("Observatorio socioeconomico del Peru")
st.caption("Tarea 4 | INEI ENAHO 2024 + BCRP | datos oficiales y calculos reproducibles")

validacion = ROOT / "salidas/validacion.txt"
indicadores = ROOT / "salidas/indicadores.csv"
if not validacion.exists() or not indicadores.exists():
    st.info("El agente aun no ha generado indicadores validados. Ejecutar primero la skill limpiando-enaho.")
    st.code("uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py")
    st.stop()
if "RESULTADO: APROBADO" not in validacion.read_text(encoding="utf-8"):
    st.error("La validacion ENAHO no esta aprobada. No se muestran cifras.")
    st.stop()

df = pd.read_csv(indicadores, dtype={"codigo": str})
nacional = df.loc[(df.nivel == "Nacional") & (df.codigo == "PERU")]
if nacional.empty:
    st.error("No existe una tasa nacional validada.")
    st.stop()
a, b, c = st.columns(3)
a.metric("Pobreza monetaria nacional, 2024", f"{nacional.iloc[0].pobreza_pct:.2f}%")
b.metric("Residentes en muestra", f"{int(nacional.iloc[0].n_muestra):,}")
c.metric("Departamentos", f"{sum(df.nivel=='Departamento')}/25")

t1, t2, t3 = st.tabs(["Indicadores y graficos", "Mapa territorial", "BCRP e investigacion"])
with t1:
    grupo = st.selectbox("Desagregacion", ["Area", "Sexo", "Departamento"])
    sub = df.loc[df.nivel == grupo, ["codigo", "pobreza_pct"]].set_index("codigo")
    st.bar_chart(sub)
    st.dataframe(df.loc[df.nivel == grupo], hide_index=True, use_container_width=True)
    for imagen in ["pobreza_area_2024.png", "pobreza_sexo_2024.png", "pobreza_departamento_barras_2024.png"]:
        ruta = ROOT / "figuras" / imagen
        if ruta.exists():
            st.image(str(ruta), caption=imagen, use_container_width=True)
with t2:
    archivo = ROOT / "mapas/pobreza_departamento.png"
    if archivo.exists():
        st.image(str(archivo), use_container_width=True)
    else:
        st.warning("Mapa aun no generado. Ejecutar la skill mapeando-enaho.")
with t3:
    figuras = sorted((ROOT / "figuras").glob("bcrp_*.png"))
    if figuras:
        for figura in figuras:
            st.image(str(figura), caption=figura.stem, use_container_width=True)
    else:
        st.info("Falta graficar una serie oficial mediante graficar_serie del servidor MCP.")
    informe = ROOT / "informes/informe_final.md"
    if informe.exists():
        st.markdown(informe.read_text(encoding="utf-8"))
st.caption("Fuente: INEI ENAHO 2024 y BCRP. Las asociaciones entre series no son causales.")
