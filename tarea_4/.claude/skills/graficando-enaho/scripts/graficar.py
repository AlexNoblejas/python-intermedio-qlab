"""Graficos ponderados de pobreza ENAHO 2024 basados en los indicadores validados."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
COLOR = "#215c77"
COLOR_LINEA = "#b4532a"
FUENTE_HOGARES = "Fuente: INEI, ENAHO 2024 (módulo 34); ponderado con factor07 x mieperho."
FUENTE_PERSONAS = "Fuente: INEI, ENAHO 2024 (módulos 02 y 34); residentes habituales, ponderado con facpob07."
EJE = "Pobreza monetaria (% de personas)"


def barras(tabla: pd.Series, titulo: str, eje: str, fuente: str, destino: Path,
           referencia: float | None = None) -> pd.Series:
    """Barras desde cero, ordenadas, un solo color y el valor escrito en cada una."""
    if tabla.empty:
        raise ValueError(f"Sin datos para {destino.name}")
    tabla = tabla.sort_values(ascending=False)
    horizontal = len(tabla) > 5
    fig, ax = plt.subplots(figsize=(10.2, 7.6 if horizontal else 5.3))
    tope = float(tabla.max()) * 1.17
    if horizontal:
        rects = ax.barh(tabla.index.astype(str), tabla.values, color=COLOR)
        ax.invert_yaxis()
        ax.set_xlabel(eje)
        ax.set_xlim(0, tope)
        for r, v in zip(rects, tabla.values):
            ax.text(r.get_width() + tope * .008, r.get_y() + r.get_height() / 2, f"{v:.1f} %", va="center", size=8)
        if referencia is not None:
            ax.axvline(referencia, color=COLOR_LINEA, ls="--", lw=1.2, label=f"Nacional: {referencia:.1f} %")
            ax.legend(frameon=False, loc="lower right")
    else:
        rects = ax.bar(tabla.index.astype(str), tabla.values, color=COLOR, width=.55)
        ax.set_ylabel(eje)
        ax.set_ylim(0, tope)
        for r, v in zip(rects, tabla.values):
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + tope * .012, f"{v:.1f} %", ha="center", size=10)
        if referencia is not None:
            ax.axhline(referencia, color=COLOR_LINEA, ls="--", lw=1.2, label=f"Nacional: {referencia:.1f} %")
            ax.legend(frameon=False, loc="upper right")
    ax.set_title(titulo, fontsize=12.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    fig.text(.02, .005, fuente, size=8)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0, .035, 1, 1])
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return tabla


def _nivel(df: pd.DataFrame, nivel: str, columna: str = "pobreza_pct") -> pd.Series:
    parte = df[df.nivel == nivel]
    return pd.Series(parte[columna].astype(float).values, index=parte.nombre.values)


def figura(tipo: str, df: pd.DataFrame, carpeta: Path) -> pd.Series:
    nacional = float(df.loc[df.nivel == "Nacional", "pobreza_pct"].iloc[0])
    if tipo == "area":
        t = _nivel(df, "Area")
        titulo = (f"La pobreza rural supera a la urbana en {t['Rural'] - t['Urbana']:.1f} puntos porcentuales\n"
                  "Pobreza monetaria por área de residencia, Perú, 2024")
        return barras(t, titulo, EJE, FUENTE_HOGARES, carpeta / "pobreza_area_2024.png", nacional)
    if tipo == "sexo":
        t = _nivel(df, "Sexo")
        titulo = (f"La brecha de pobreza entre mujeres y hombres es de {abs(t['Mujer'] - t['Hombre']):.1f} puntos "
                  "porcentuales\nPobreza monetaria por sexo, Perú, 2024")
        return barras(t, titulo, EJE, FUENTE_PERSONAS, carpeta / "pobreza_sexo_2024.png")
    if tipo == "edad":
        t = _nivel(df, "Edad")
        titulo = (f"El grupo de {t.idxmax()} años registra la mayor pobreza ({t.max():.1f} %) y el de {t.idxmin()} "
                  f"la menor ({t.min():.1f} %)\nPobreza monetaria por grupo de edad, Perú, 2024")
        return barras(t, titulo, EJE, FUENTE_PERSONAS, carpeta / "pobreza_edad_2024.png")
    if tipo == "departamento":
        t = _nivel(df, "Departamento")
        titulo = (f"{t.idxmax()} ({t.max():.1f} %) tiene una pobreza {t.max() / t.min():.1f} veces la de "
                  f"{t.idxmin()} ({t.min():.1f} %)\nPobreza monetaria por departamento, Perú, 2024")
        return barras(t, titulo, EJE, FUENTE_HOGARES, carpeta / "pobreza_departamento_barras_2024.png", nacional)
    if tipo == "concentracion":
        t = _nivel(df, "Departamento", "participacion_pobres_pct")
        titulo = (f"{t.idxmax()} concentra el {t.max():.1f} % de las personas pobres del Perú\n"
                  "Distribución de las personas en pobreza monetaria por departamento, Perú, 2024")
        return barras(t, titulo, "Participación en el total de personas pobres (%)", FUENTE_HOGARES,
                      carpeta / "concentracion_pobres_departamento_2024.png")
    raise ValueError(f"Tipo desconocido: {tipo}")


def main():
    tipos = ["area", "sexo", "edad", "departamento", "concentracion"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipo", choices=[*tipos, "todos"], default="todos")
    args = parser.parse_args()
    validacion = ROOT / "salidas" / "validacion.txt"
    indicadores = ROOT / "salidas" / "indicadores.csv"
    if (not indicadores.is_file() or not validacion.is_file()
            or "RESULTADO: APROBADO" not in validacion.read_text(encoding="utf-8")):
        raise SystemExit("Primero ejecute la skill limpiando-enaho y supere la validacion.")
    df = pd.read_csv(indicadores, dtype={"codigo": str})
    for tipo in (tipos if args.tipo == "todos" else [args.tipo]):
        tabla = figura(tipo, df, ROOT / "figuras")
        print(f"{tipo}: {len(tabla)} grupos; mayor {tabla.index[0]} {tabla.iloc[0]:.2f}; "
              f"menor {tabla.index[-1]} {tabla.iloc[-1]:.2f}")


if __name__ == "__main__":
    main()
