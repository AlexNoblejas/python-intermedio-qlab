"""Mapa de pobreza por departamento: union por codigos UBIGEO y FIRST_IDDP."""
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
GEOJSON = ROOT / "datos" / "peru_departamental_simple.geojson"
REFERENCIA = ROOT / "referencias" / "pobreza_departamento_2024_profesor.csv"
# Etiquetas que no caben dentro del departamento: van afuera, con linea guia.
DESPLAZAR = {"07": (-2.1, 0.0), "14": (-1.7, -0.5), "24": (-1.1, 0.5), "01": (-2.9, 1.6)}


def tasas_por_departamento(indicadores: pd.DataFrame) -> pd.DataFrame:
    dep = indicadores.loc[indicadores.nivel == "Departamento", ["codigo", "nombre", "pobreza_pct"]].copy()
    dep["codigo"] = dep.codigo.astype(str).str.zfill(2)
    if dep.codigo.nunique() != 25 or dep.pobreza_pct.isna().any():
        raise ValueError("Se requieren 25 departamentos con dato.")
    return dep


def unir(geometria: gpd.GeoDataFrame, tasas: pd.DataFrame) -> gpd.GeoDataFrame:
    if "FIRST_IDDP" not in geometria.columns:
        raise ValueError("Falta el identificador FIRST_IDDP en el GeoJSON.")
    shapes = geometria.copy()
    shapes["FIRST_IDDP"] = shapes.FIRST_IDDP.astype(str).str.zfill(2)
    if shapes.FIRST_IDDP.nunique() != 25:
        raise ValueError("El GeoJSON debe tener 25 codigos territoriales unicos.")
    union = shapes.merge(tasas, left_on="FIRST_IDDP", right_on="codigo", how="left", validate="1:1", indicator=True)
    if len(union) != 25 or not union._merge.eq("both").all() or union.pobreza_pct.isna().any():
        raise ValueError("La union territorial por codigos genero huecos o duplicaciones.")
    if not {"07", "15"}.issubset(set(union.FIRST_IDDP)):
        raise ValueError("Lima y Callao deben estar separados.")
    return union


def dibujar(union: gpd.GeoDataFrame, destino: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.7, 10.6))
    tope = float(union.pobreza_pct.max())
    union.plot(ax=ax, column="pobreza_pct", cmap="Blues", vmin=0, vmax=tope, legend=True,
               legend_kwds={"label": "Pobreza monetaria (% de personas)", "shrink": .55, "pad": .01},
               edgecolor="#6b7c86", linewidth=.45)
    puntos = union.to_crs(32718).representative_point().to_crs(union.crs)
    for (_, fila), punto in zip(union.iterrows(), puntos):
        dx, dy = DESPLAZAR.get(fila.FIRST_IDDP, (0, 0))
        color = "white" if fila.pobreza_pct > .62 * tope else "#14232c"
        etiqueta = f"{fila.nombre}\n{fila.pobreza_pct:.1f} %"
        if dx or dy:
            ax.annotate(etiqueta, xy=(punto.x, punto.y), xytext=(punto.x + dx, punto.y + dy), size=6.6,
                        ha="center", va="center", color="#14232c", arrowprops={"arrowstyle": "-", "lw": .6})
        else:
            ax.text(punto.x, punto.y, etiqueta, size=6.6, ha="center", va="center", color=color)
    maximo, minimo = union.loc[union.pobreza_pct.idxmax()], union.loc[union.pobreza_pct.idxmin()]
    ax.set_title(f"La pobreza va de {minimo.pobreza_pct:.1f} % en {minimo.nombre} a {maximo.pobreza_pct:.1f} % en "
                 f"{maximo.nombre}\nPobreza monetaria por departamento, Perú, 2024", fontsize=13, loc="left")
    ax.set_axis_off()
    fig.text(.08, .045, "Fuente: INEI, ENAHO 2024 (módulo 34), ponderado con factor07 x mieperho. Límites: repositorio "
                        "del curso.\nUnión por código: ubigeo[:2] = FIRST_IDDP. Lima (15) y Callao (07) separados.", size=8)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)


def comparar_con_referencia(union: gpd.GeoDataFrame, referencia: pd.DataFrame) -> pd.DataFrame:
    ref = referencia.assign(ccdd=referencia.ccdd.astype(str).str.zfill(2)).rename(columns={"pobreza_pct": "referencia_pct"})
    tabla = pd.DataFrame(union.drop(columns="geometry"))[["FIRST_IDDP", "NOMBDEP", "pobreza_pct"]].merge(
        ref[["ccdd", "referencia_pct"]], left_on="FIRST_IDDP", right_on="ccdd", how="left", validate="1:1")
    if tabla.referencia_pct.isna().any():
        raise ValueError("Falta un departamento en la referencia de la Sesion 16.")
    tabla["diferencia_pp"] = (tabla.pobreza_pct - tabla.referencia_pct).round(4)
    return tabla.drop(columns="ccdd").sort_values("FIRST_IDDP")


def main():
    indicadores = ROOT / "salidas" / "indicadores.csv"
    validacion = ROOT / "salidas" / "validacion.txt"
    if (not indicadores.is_file() or not validacion.is_file()
            or "RESULTADO: APROBADO" not in validacion.read_text(encoding="utf-8")):
        raise SystemExit("Primero ejecute limpiando-enaho: faltan datos validados.")
    if not GEOJSON.is_file():
        raise SystemExit(f"Descargue el GeoJSON con scripts/descargar_datos.py: falta {GEOJSON}")
    tasas = tasas_por_departamento(pd.read_csv(indicadores, dtype={"codigo": str}))
    union = unir(gpd.read_file(GEOJSON), tasas)
    dibujar(union, ROOT / "mapas" / "pobreza_departamento.png")
    tabla = comparar_con_referencia(union, pd.read_csv(REFERENCIA, dtype={"ccdd": str}))
    tabla.to_csv(ROOT / "mapas" / "pobreza_departamento_vs_referencia.csv", index=False, encoding="utf-8")
    print(f"Mapa de {len(union)} departamentos; Lima y Callao separados; "
          f"diferencia maxima con la Sesion 16: {tabla.diferencia_pp.abs().max():.3f} pp.")


if __name__ == "__main__":
    main()
