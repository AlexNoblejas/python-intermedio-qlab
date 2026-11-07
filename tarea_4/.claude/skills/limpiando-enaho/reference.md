# ENAHO 2024: decisiones reproducibles

## Archivos

| Módulo | Archivo dentro del zip | Una fila por | Filas | Llaves | Factor |
|---|---|---|---:|---|---|
| 34, sumaria | `sumaria-2024.dta` (no `sumaria-2024-12g.dta`) | hogar | 33,691 | `conglome`, `vivienda`, `hogar` | `factor07` |
| 02, miembros | `enaho01-2024-200.dta` | persona | 117,721 | las tres + `codperso` | `facpob07` |

Las llaves y el `ubigeo` se leen como texto, con sus ceros a la izquierda. `pobreza`: 1 extremo, 2 no extremo, 3 no pobre. Otras variables de miembros: `p203` parentesco, `p207` sexo, `p208a` edad.

## Reglas

- Residentes habituales: `((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))`. Quedan 108,664.
- Unión: `merge(..., validate="m:1")`; se exige que no se pierda ni se duplique ninguna persona.
- Departamento: `ubigeo[:2]`. Área urbana: `estrato <= 5`. Pobre: `pobreza <= 2`.

## Qué factor usa cada tasa

| Tasa | Base | Peso | Nacional | Urbana | Rural |
|---|---|---|---:|---:|---:|
| Oficial (nacional, área, departamento) | Todos los hogares de la sumaria | `factor07 × mieperho` | 27.58 % | 24.81 % | 39.30 % |
| Personas (sexo, edad y contraste) | Residentes habituales | `facpob07` | 27.53 % | 24.74 % | 39.44 % |

El módulo 34 trae la pobreza del hogar y el módulo 02 las características individuales: cada tasa usa el factor de su unidad de análisis. La sumaria reproduce las cifras publicadas por el INEI (27.6 %, 24.8 %, 39.3 %) y la referencia de la Sesión 16, con una diferencia máxima de 0.05 puntos por departamento. La base de personas difiere hasta 0.52 puntos en un departamento porque excluye a quienes no son residentes habituales y usa otro factor. Ambas cifras se conservan en `salidas/indicadores.csv`.

## Publicación

Los zip, `.dta` y el parquet de personas son microdatos: no se suben al repositorio. Se publican `validacion.txt` e `indicadores.csv`, que son agregados.
