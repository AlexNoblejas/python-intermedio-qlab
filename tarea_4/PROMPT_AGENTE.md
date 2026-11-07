Investiga esta pregunta con datos oficiales y cálculos reproducibles:

**Entre 2020 y 2024, ¿cuánto tiempo estuvo la inflación de Lima a 12 meses fuera del rango meta del BCRP (1 % a 3 %) y, en 2024, dónde era más alta la pobreza monetaria y dónde vivía la mayor parte de las personas pobres, por área y por departamento?**

Trabaja en este orden y en esta misma sesión:

1. **Plan.** Escribe primero un plan breve: qué dato sale de qué fuente y con qué herramienta.
2. **BCRP por MCP.** Identifica la serie con `buscar_series`. Calcula con `resumen` y con `episodios_fuera_de_rango` (mínimo 1, máximo 3), de 2020-01 a 2024-12. Genera el gráfico con `graficar_serie`, usando `banda_min=1`, `banda_max=3` y un título que diga el hallazgo.
3. **ENAHO por Skills.** Usa la Skill `limpiando-enaho` y comprueba que `salidas/validacion.txt` diga `RESULTADO: APROBADO`. Usa `graficando-enaho` para las figuras de área, departamento y concentración. Usa `mapeando-enaho` para el mapa de 25 departamentos, con Lima y Callao separados. Revisa `mapas/pobreza_departamento_vs_referencia.csv`.
4. **Contraste.** Compara tus cifras nacionales y departamentales con `salidas/validacion.txt` y con la referencia de la Sesión 16. Si algo no cuadra, explícalo; no lo ajustes.
5. **Informe.** Escribe `informes/informe_final.md` con estas secciones, en este orden:
   1. Pregunta de investigación: tema, objetivo y delimitación.
   2. Fuentes y metodología: datos, procesamiento, indicadores y por qué cada tasa usa su factor de expansión.
   3. Resultados: al menos tres hallazgos, cada uno con cifra, periodo, unidad y origen (código y URL del BCRP, o archivo de `salidas/`).
   4. Visualizaciones: el gráfico del BCRP, al menos un gráfico de la ENAHO y el mapa, con rutas relativas (`../figuras/...`, `../mapas/...`).
   5. Interpretación: los patrones principales, en especial la diferencia entre dónde la tasa es más alta y dónde viven más personas pobres.
   6. Limitaciones: cobertura temporal, inflación de Lima frente a pobreza nacional, error muestral y ausencia de causalidad demostrada.
   7. Reproducibilidad: scripts, archivos y series usados.

El rango meta de 1 % a 3 % es un dato de la política del BCRP: cítalo con esta fuente, https://www.bcrp.gob.pe/politica-monetaria/ . Cada cifra debe salir de una herramienta o de un archivo generado por las Skills, no de tu memoria. Si una herramienta falla, informa el bloqueo y sigue con lo demás; no inventes resultados.

Al terminar, enumera los nombres exactos de las herramientas MCP y las Skills que ejecutaste y qué archivos generaste.
