# Auditoría técnica de GaitSPM 1.4.0

Fecha: 24/10/2026. Autor del proyecto: Ángel González de la Flor. Revisión y desarrollo asistidos por IA. No es una auditoría externa ni validación clínica.

## Base recuperada y alcance

La versión más reciente localizada en los archivos disponibles fue GaitSPM_v1.3.0.zip, del 05/09/2026. SHA-256: `6dcfe7dadb6bd398bec985796908ced10bab81ed488a3c67bb5ca0a32ddae1b3`. Se creó una copia de trabajo y se conservó el original. La confirmación del usuario de que no había modificado nada permite usarla como base de esta actualización; no se afirma que se haya inspeccionado su disco local.

Requisitos: navegador en el ordenador, 30 por grupo, seis contextos clínicos existentes, ocho ejemplos, modo Laboratorio y Guiado, solo cinemática. Entrega local, sin publicación en GitHub. spm1d 0.4.53 se conserva para reproducibilidad; no se afirma que sea la última versión publicada del motor.

## Correcciones comprobadas

| Problema | Cambio | Evidencia |
|---|---|---|
| Delimitadores CSV confundidos con decimales o contenido entre comillas | Detección por estructura de filas y análisis CSV real | CSV español, transpuesto y campos entre comillas |
| Excel con guía antes de datos | Selección preferente de Curves_Wide | Ocho Excel importados y equivalentes al generador |
| Un mismo campo asignado a varios roles | Validación explícita | Prueba de rechazo |
| Lateralidad declarada incompatible con el nombre de variable | Rechazo de contradicción, normalización de nombres de lados | Prueba de conflicto |
| Huecos complementarios entre ensayos o lados podían aparentar una curva completa | Conservación de valores ausentes, exclusión conservadora y n real | Pruebas con huecos opuestos |
| Covariable cambiante dentro de sujeto | Filtro adecuado y error explícito; no promediar silenciosamente | Prueba de inconsistencia |
| Comparación pareada de lados sin filtro de grupo en UI | Se ofrece el filtro | Revisión del código y cobertura de configuración |
| Resultados antiguos visibles después de cambios | Invalidación y bloqueo al cargar/configurar; impedir análisis con archivo pendiente de mapear | Pruebas DOM |
| Texto de corrección y post hoc no coherente con resultado actual | Bonferroni y clústeres confirmados en texto, idioma y detalles | Pruebas de puente y regresión |
| Tamaños de ejemplo e idioma desactualizados | Ocho ejemplos, 30+30, recuentos e interpretación con n real | Ocho recorridos DOM ES/EN |

Se añadieron receta por ejemplo, explicación de clústeres calculada desde resultados, muestra incluida/excluida, exportación JSON y lanzadores locales. Modificar apariencia no recalcula la inferencia. Los cambios del motor se sincronizan con el HTML desde una única fuente.

## Verificación ejecutada

- **20 pruebas Python aprobadas**: suite del motor (10), puente/servidor (2) y regresiones 1.4 (8). `tests-python.log`: 59,337 s en esta ejecución.
- **40 conversiones equivalentes**: ocho ejemplos × CSV ancho, CSV español, Excel, largo y transpuesto. Valores comparados con las curvas del generador.
- Comparación de estadísticos t con SciPy, RM-ANOVA con cálculo independiente de sumas de cuadrados, normalidad/resolución SnPM y estabilidad de semillas; pruebas heredadas contra regresiones estadísticas conservadas.
- Ocho recetas y **22 contrastes de variables** ejecutados; `example-results.csv`. Todos los grupos/condiciones analizados contienen n=30. En 07 y 08 el n total del contraste es 30, con medidas repetidas, aunque el archivo contiene 60 participantes únicos.
- Exportación CSV/XLSX, figuras PNG/SVG/PDF y resultados ES/EN para los ocho ejemplos por el puente Python real.
- Descarga HTTP de los 16 archivos CSV/Excel idéntica a sus bytes originales; rechazo de rutas no permitidas, origen externo y operaciones no autorizadas; sesiones separadas. Suite ampliada repetida: `tests-http-final.log`.
- **Ocho recorridos de interfaz en jsdom**, evaluando el código JS real con salidas del motor guardadas: carga, receta, n=30, informe, ES/EN, cambio de modo, validación α, invalidación y protección de archivo pendiente. `tests-ui.log`. Son pruebas DOM fuera de navegador, no pruebas de renderizado.
- **3600 valores de fórmulas Excel** verificados contra NumPy en los ocho libros. Fórmulas de ROM/media comprobadas tras una modificación en memoria; archivos entregados no alterados. `workbooks-validation.json`, `recalculation.json`.
- Las cuatro hojas de cada Excel se renderizaron y revisaron en vistas de muestra (32 vistas), incluyendo guía, métricas, curvas y participantes. No es una inspección visual de cada celda de las 101 columnas por variable.
- Lanzador probado en Linux/Python 3.12.14 con dependencias presentes: inicia en loopback, responde ping, sirve HTML y cierra limpiamente. `launcher.log`. Se comprobó `launch.py --check`.

## Resultados didácticos

01 no presenta clústeres confirmados con la receta prevista. 02–06 ofrecen combinaciones de diferencias y variables sin significación. 07 presenta efectos globales entre condiciones en las tres variables; 08 no presenta clústeres significativos en ninguna de sus dos variables. Los intervalos y p exactos se documentan en `docs/GUIA_EJEMPLOS.md` y se calculan de nuevo en la aplicación.

El generador usa datos sintéticos con anclajes escalares heredados en 01–06. Los cambios de fatiga/recuperación y el ruido de repetición son supuestos didácticos. No se han obtenido nuevos pacientes ni reconstruido curvas publicadas. Las fuentes heredadas no se han reauditado artículo por artículo en esta revisión.

## Límites y comprobaciones pendientes

La comprobación visual en un navegador real quedó bloqueada por la política de acceso del entorno. La instalación disponible tampoco tenía Chromium operativo. **No se verificaron píxeles, reflujo móvil, interacción real con el selector de archivos ni accesibilidad con lector de pantalla en esta revisión**. `tests/test_browser.cjs` queda como prueba preparada, no aprobada. Las pruebas de importación del motor y del servidor sí pasaron.

No se probó una instalación limpia en Mac/Windows ni la descarga inicial de dependencias del lanzador. La aplicación necesita Python y una instalación inicial con internet. Los modos alternativos Streamlit y Pyodide se conservan pero no se ejecutaron en esta versión.

La inferencia requiere datos segmentados, comparables y supuestos estadísticos apropiados. No se detectan eventos de marcha automáticamente. Normalidad automática no valida independencia ni esfericidad; spm1d no corrige no esfericidad en ANOVA de medidas repetidas (documentación oficial: https://spm1d.org/doc/Stats1D/anova.html). Permutaciones de etiquetas no son Welch. Los IC95 son puntuales; n.s. no prueba equivalencia. Las diferencias medias dentro de clústeres son descriptivas tras selección. No se demuestra validez diagnóstica ni relevancia clínica.

## Reproducibilidad

Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3, Matplotlib 3.10.8, openpyxl 3.1.5, spm1d 0.4.53 incluido. `requirements-lock.txt` registra el cierre de dependencias del entorno probado; puede variar por plataforma. Semillas y recetas están en metadata.json y app/simulation.py. `MANIFEST.sha256` identifica los archivos entregados. Instrucciones para repetir las comprobaciones: tests/README.md.
