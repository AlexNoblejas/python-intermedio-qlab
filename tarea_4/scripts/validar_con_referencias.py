"""Independent ENAHO audit: sumaria weights vs published course reference.

Does not modify poverty values. It compares person-weighted outputs (facpob07)
with household sumaria-weighted outputs (factor07 * mieperho), which are
expected to differ slightly. Reference CSV comes from Session 16 of the course.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LIMPIAR = ROOT / ".claude/skills/limpiando-enaho/scripts/limpiar.py"
REF = ROOT / "referencias/pobreza_departamento_2024_profesor.csv"


def sumaria_pobreza_por_departamento(hogares: pd.DataFrame) -> pd.DataFrame:
    """Poverty incidence over persons using factor07*mieperho per household."""
    hogares = hogares.copy()
    required = {"pobreza", "factor07", "mieperho", "ubigeo"}
    if not required.issubset(hogares.columns):
        raise ValueError("Missing fields in sumaria: " + ", ".join(sorted(required - set(hogares.columns))))
    hogares["peso"] = pd.to_numeric(hogares.factor07, errors="raise") * pd.to_numeric(hogares.mieperho, errors="raise")
    if hogares.peso.isna().any() or (hogares.peso <= 0).any():
        raise ValueError("Invalid sumaria weights")
    hogares["pobre"] = pd.to_numeric(hogares.pobreza, errors="raise").le(2)
    hogares["ccdd"] = hogares.ubigeo.astype(str).str.replace(r"\.0+$", "", regex=True).str.zfill(6).str[:2]
    records = []
    for ccdd, grupo in hogares.groupby("ccdd", observed=True):
        records.append({"ccdd": ccdd, "sumaria_pct": float(100 * (grupo.pobre * grupo.peso).sum() / grupo.peso.sum()),
                        "n_hogares": len(grupo)})
    return pd.DataFrame(records)


def comparar(base: pd.DataFrame, hogares: pd.DataFrame, referencia: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if base["departamento"].nunique() != 25 or referencia["ccdd"].nunique() != 25:
        raise ValueError("Exactly 25 departments required in base and reference")
    ref = referencia.copy()
    ref["ccdd"] = ref.ccdd.astype(str).str.zfill(2)
    sumaria = sumaria_pobreza_por_departamento(hogares)
    persona = base.copy()
    persona["ccdd"] = persona.departamento.astype(str).str.zfill(2)
    w = pd.to_numeric(persona.facpob07, errors="raise")
    persona["peso"] = w
    persona["pobreza_ponderada"] = persona.pobre.astype(float) * w
    tot = persona.groupby("ccdd").agg(pesos=("peso", "sum"), numerador=("pobreza_ponderada", "sum"))
    tot["personas_pct"] = 100 * tot.numerador / tot.pesos
    merged = (ref.merge(sumaria, on="ccdd", validate="1:1")
                 .merge(tot[["personas_pct"]].reset_index(), on="ccdd", validate="1:1"))
    if len(merged) != 25:
        raise ValueError("Department missing from independent comparison")
    merged["dif_sumaria_ref_pp"] = merged.sumaria_pct - merged.pobreza_pct
    merged["dif_personas_ref_pp"] = merged.personas_pct - merged.pobreza_pct
    peso_h = pd.to_numeric(hogares.factor07, errors="raise") * pd.to_numeric(hogares.mieperho, errors="raise")
    pobreza_h = float(100 * (pd.to_numeric(hogares.pobreza).le(2) * peso_h).sum() / peso_h.sum())
    pobreza_p = float(100 * (base.pobre.astype(float) * base.facpob07).sum() / base.facpob07.sum())
    resumen = {
        "hogares_sumaria": int(len(hogares)),
        "residentes_personas": int(len(base)),
        "tasa_sumaria_pct": pobreza_h,
        "tasa_personas_pct": pobreza_p,
        "dif_tasas_pp": pobreza_p - pobreza_h,
        "departamentos": int(len(merged)),
        "max_dif_sumaria_ref_pp": float(merged.dif_sumaria_ref_pp.abs().max()),
        "max_dif_personas_ref_pp": float(merged.dif_personas_ref_pp.abs().max()),
    }
    return merged, resumen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--referencia", type=Path, default=REF)
    args = parser.parse_args()
    validation = ROOT / "salidas/validacion.txt"
    if not validation.exists() or "RESULTADO: APROBADO" not in validation.read_text(encoding="utf-8"):
        raise SystemExit("Run ENAHO cleaning and pass essential validations first")
    spec = importlib.util.spec_from_file_location("limpiar", LIMPIAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    households = mod.leer_dta_zip(ROOT / "datos/966-Modulo34.zip", "sumaria-2024")
    people = pd.read_parquet(ROOT / "salidas/personas_2024.parquet")
    reference = pd.read_csv(args.referencia, dtype={"ccdd": str})
    comparison, stats = comparar(people, households, reference)
    output = ROOT / "salidas/validacion_referencia_departamentos.csv"
    comparison.to_csv(output, index=False)
    lines = ["# Contraste independiente ENAHO 2024", "",
             "Fuente: INEI ENAHO 2024, modulo 34 y modulo 02, y CSV de referencia de la Sesion 16.", "",
             "Dos formas de ponderar se muestran por separado. Nunca reajustar valores para forzar coincidencia.", ""]
    for key, val in stats.items():
        lines.append(f"- **{key}**: {val:.5f}" if isinstance(val, float) else f"- **{key}**: {val}")
    lines += ["", "Nota: el curso publica tasas por sumaria (factor07 x mieperho);",
              "el proyecto tambien calcula tasas por personas (facpob07). Diferencias metodologicas pequenas son esperables.",
              "Consulte el CSV por departamento para documentar la magnitud de cada diferencia."]
    report = ROOT / "salidas/validacion_metodologica.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Audit output:", output, "\n", "\n".join(lines))
    if abs(stats["tasa_sumaria_pct"] - 27.6) > 0.1:
        raise SystemExit("Sumaria incidence too far from INEI 27.6%")
    if len(people) != 108664:
        raise SystemExit("Resident count differs from course reference")


if __name__ == "__main__":
    main()
