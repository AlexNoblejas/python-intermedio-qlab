# Ruta de ejecución — Tarea 1

**Entrega: domingo 18 de octubre, 23:59 (hora de Perú).**
Rúbrica: GitHub 2 · Parte 1 → 6 · Parte 2 → 8 · Parte 3 → 4 = **20 puntos**.

Este archivo es para ti, no para entregar. Bórralo antes del push final si prefieres.

---

## ⚠️ Lo primero, esta noche

El punto de **commits distribuidos (1 pt)** pide historial en varios días y solo quedan
sábado y domingo. Haz el primer commit ahora, aunque no hayas corrido nada:

```bash
cd tu-repo-del-curso
mkdir -p tarea_1 && cp -r /ruta/a/tarea_1/* tarea_1/
git add tarea_1
git commit -m "chore: estructura inicial de tarea_1 (notebooks, app, deps)"
git push
```

Y crea los **3 issues** (texto abajo) en tu repo, también hoy. Con eso ya tienes tres días
en el log en vez de uno.

---

## Sábado por la mañana — Parte 1 (6 pts)

1. `jupyter lab` → abre `01_recoleccion.ipynb`.
2. Corre de arriba abajo. La celda de sitemaps es la lenta: unas **400 peticiones con pausa
   de 1–2 s**, así que calcula **12 a 18 minutos**. Déjala corriendo y ve por un café.
   - Si se corta, vuelve a correrla: el caché en `datos/raw/` evita volver a descargar.
   - Si al final te quedas corto de 350 filas, sube `CUPO` de 55 a 70 y repite solo la
     celda de sitemaps.
3. Revisa los **tres títulos de los gráficos**. Vienen redactados como conclusión, pero con
   los números de tu corrida: léelos y ajústalos si la conclusión que afirman no es la que
   muestran tus datos. La rúbrica evalúa exactamente eso.
4. Llena la sección 9 del notebook (conclusiones de la recolección).

```bash
git add tarea_1/01_recoleccion.ipynb tarea_1/datos/noticias.csv
git commit -m "scrape: 400+ titulares de La Republica y El Comercio via RSS y sitemaps"
```

## Sábado por la tarde — Parte 2 (8 pts)

Antes de empezar: `ollama serve` en una terminal y `ollama pull qwen2.5:7b`.

1. Corre `02_clasificacion.ipynb` hasta el paso 2.
   - El zero-shot descarga ~500 MB la primera vez.
   - El etiquetado con el LLM es lo más lento: a 1–3 s por titular son **15 a 25 minutos**
     para 400. También guarda avance cada 25 filas, así que se puede reanudar.
2. **La auditoría de 20 casos la haces tú.** El notebook crea
   `datos/auditoria_humana.csv`; ábrelo, pon 1 o 0 en `de_acuerdo` y escribe un comentario
   en los que falló. Guarda y corre la celda siguiente. No delegues esto: es 2.5 pts de la
   rúbrica junto con el baseline.
3. Sigue con el split y el fine-tuning. Con GPU son 3–8 minutos; en CPU, 20–40.
4. Escribe la **reflexión por categoría** (después de la matriz de confusión) y la
   **decisión de producción** (paso 6). Ambas están como `…` esperando tu texto.

```bash
git commit -am "train: distilbert 3 epocas, F1 macro 0.XX en test"
```

## Domingo — Parte 3 (4 pts) y cierre

1. `streamlit run app.py`. Comprueba filtros, las 3 métricas, el gráfico, la tabla y el
   probador en vivo. **Pruébalo en ventana de incógnito** antes de dar por buena la app.
2. Llena el `README.md`: los dos hallazgos, las dos limitaciones y todos los `COMPLETAR`.
3. `pip freeze > requirements.txt` — la rúbrica pide dependencias exactas, y ahora mismo el
   archivo tiene rangos.
4. Cierra los 3 issues con un comentario de qué quedó hecho en cada uno.
5. Verifica que los **dos notebooks estén guardados con sus salidas visibles** en GitHub
   (ábrelos en el navegador después del push: si ves las tablas y los gráficos, está bien).
6. Comenta en el Issue #188 con el formato de abajo.

---

## Texto de los 3 issues

**`T1 – Parte 1: Recolección y Limpieza`**
```
Extraer 400 titulares (200 La República + 200 El Comercio) en las 4 categorías oficiales.

- [ ] Revisar robots.txt de ambos medios y documentarlo
- [ ] RSS por sección de los dos diarios
- [ ] Sitemaps por sección para completar el volumen (el RSS solo da ~20 por sección)
- [ ] Limpieza: duplicados por URL, titulares vacíos, mapeo sección → categoría
- [ ] Reporte de descartes con motivos
- [ ] 3 gráficos Plotly con títulos que enuncien la conclusión
- [ ] Exportar datos/noticias.csv con las 7 columnas
```

**`T1 – Parte 2: Modelado y Clasificación`**
```
Del LLM al clasificador: línea base, supervisión débil y fine-tuning.

- [ ] Baseline zero-shot sobre 40 titulares (piso a superar)
- [ ] Etiquetado del dataset completo con Ollama local
- [ ] Auditoría humana de 20 casos al azar
- [ ] Split 70/15/15 estratificado, semilla 42, test aislado
- [ ] Fine-tuning de DistilBERT: 3 épocas, batch 16, F1 macro como métrica
- [ ] Evaluación en test: accuracy, F1 macro, matriz de confusión
- [ ] Tabla comparativa y justificación de qué modelo iría a producción
```

**`T1 – Parte 3: Dashboard y Despliegue`**
```
Dashboard interactivo en Streamlit.

- [ ] Filtros por medio y categoría en la barra lateral
- [ ] 3 indicadores con st.metric (total, F1 macro, concordancia LLM-humano)
- [ ] Gráfico Plotly + tabla descargable en CSV
- [ ] Probador en vivo: escribir un titular y ver categoría + probabilidad
- [ ] README con las 5 secciones y requirements.txt congelado
- [ ] Probar en ventana de incógnito
```

---

## Comentario de entrega (pegar en el Issue #188)

La última celda del notebook 2 imprime estas líneas ya con tus números:

```
Tarea 1 – Individual
Medio: Comparada
Estudiante: Alexander Noblejas (@tu_usuario_github)
Dashboard en vivo: https://...streamlit.app  (o indicar ejecución local comprobada)
Carpeta del trabajo: https://github.com/<tu_usuario>/<tu_repo>/tree/main/tarea_1
Resultados Test: F1 Macro: 0.xx | Zero-shot: 0.xx | Acuerdo LLM-Humano: xx/20
```

---

## Riesgos y cómo quedan cubiertos

| Riesgo que advierte el issue | Cómo lo cubre esta carpeta |
|---|---|
| Scraping que corre una vez y se cae | Caché en `datos/raw/`: cada corrida retoma donde quedó |
| Bloqueo del medio | RSS y sitemaps, ambos permitidos por `robots.txt`; sin paginación |
| Pesos > 100 MB rompen el push | `.gitignore` + opción de subir a HF Hub para el despliegue |
| `requirements.txt` incompleto | Cubierto con rangos; **haz `pip freeze` al final** |
| Métricas infladas | Test aislado hasta el paso 5, y además control contra la sección del diario |
| Clave de API subida al repo | No hay ninguna: el LLM corre local con Ollama |

## Checklist final

- [ ] `tarea_1/` con ambos notebooks, `app.py`, `requirements.txt`, `README.md`, `datos/noticias.csv`, `datos/etiquetas_llm.csv`
- [ ] Notebooks ejecutados y con salidas visibles en GitHub
- [ ] 3 issues documentados y cerrados
- [ ] Commits repartidos en varios días
- [ ] Sin archivos > 100 MB ni credenciales
- [ ] `streamlit run app.py` sin errores, probado en incógnito
