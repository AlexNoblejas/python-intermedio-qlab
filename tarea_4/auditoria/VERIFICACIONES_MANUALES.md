# Verificaciones manuales contra fuentes externas

Cada afirmación se comprobó fuera del agente: en la tabla web del BCRP, que no es la API del servidor MCP, y en notas que atribuyen las cifras al INEI. Las hizo Claude Code en la sesión de desarrollo el 6 de noviembre de 2026.

**Confirmación del estudiante:** abrir los enlaces y marcar aquí cuando los haya revisado: `[ ]`

| N.º | Afirmación y origen | Valor calculado | Valor de referencia | Fuente | Método | Diferencia | Veredicto |
|---:|---|---:|---:|---|---|---:|---|
| 1 | Máximo de la inflación de Lima a 12 meses en 2020-2024: junio de 2022 (BCRP, `PN01273PM`) | 8.8126 % | 8.81 % | [Tabla BCRP 2022-2024](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html/2022-1/2024-12/) | Lectura de la tabla web | 0.00 al redondear | VALIDADO |
| 2 | Meses por encima de 3 % en 2020-2024, de junio de 2021 a marzo de 2024 (BCRP, `PN01273PM`) | 34 meses | 34 meses | [Tabla 2020-2021](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html/2020-1/2021-12/) y tabla anterior | Conteo en las tablas web: 7 en 2021, 12 en 2022, 12 en 2023 y 3 en 2024 | 0 | VALIDADO |
| 3 | Pobreza monetaria nacional 2024 (ENAHO, sumaria, `factor07 × mieperho`) | 27.58 % | 27.6 % | [Andina, 8 de mayo de 2025, cifra atribuida al INEI](https://andina.pe/ingles/noticia-peru-pobreza-monetaria-descendio-29-el-2023-a-276-ano-pasado-1028759.aspx) | Comparación con la cifra publicada | -0.02 pp | VALIDADO |
| 4 | Pobreza urbana y rural 2024 (ENAHO, sumaria) | 24.81 % y 39.30 % | 24.8 % y 39.3 % | La misma nota de Andina | Comparación con la cifra publicada | 0.01 y 0.00 pp | VALIDADO |
| 5 | Pobreza de Cajamarca y Loreto 2024 (ENAHO, sumaria) | 45.01 % y 42.97 % | 45 % y 43 % | La misma nota de Andina y `referencias/pobreza_departamento_2024_profesor.csv` | Comparación con la cifra publicada | 0.01 y -0.03 pp | VALIDADO |
| 6 | Lima concentra el 32.11 % de las personas pobres (ENAHO, sumaria) | 32.11 % | 32.11 % | Segundo cálculo en `evaluacion/preparar_verdades.py`, directo sobre el `.dta` y sin usar la Skill | Dos códigos independientes | 0.00 pp | VALIDADO |

## Diferencias y límites

- **Método de personas:** con residentes habituales y `facpob07`, las mismas tasas dan 27.53 %, 24.74 % y 39.44 %. La diferencia se debe a la unidad de análisis y al factor, no a un error; está explicada en `.claude/skills/limpiando-enaho/reference.md`.
- **Fuente del INEI:** no se pudo abrir el informe técnico del INEI desde la sesión. Las cifras se cotejaron con Andina, la agencia estatal de noticias, que las atribuye expresamente al INEI, y con la referencia de la Sesión 16.
- **Personas pobres en números absolutos:** el INEI publica 9,395,000 personas; la suma de los factores da unos 9.51 millones. Por eso el informe usa porcentajes y participaciones, no conteos absolutos.
- **Rango meta:** el rango de 1 % a 3 % está en la [página de política monetaria del BCRP](https://www.bcrp.gob.pe/politica-monetaria/).
