# GaitSPM 1.4.2 · empieza aquí

El idioma inicial es inglés; pulsa **ES** para cambiar al español. La elección se recuerda en este navegador.

Aplicación local para explorar y analizar cinemática de la marcha en tu navegador. Incluye modos **Guiado** y **Laboratorio**, interfaz ES/EN y ocho ejemplos sintéticos. Basada en GaitSPM 1.3.0 recuperado; motor spm1d 0.4.53.

## Iniciar en tu ordenador

1. Descomprime todo el ZIP en una carpeta local con permiso de escritura. No ejecutes desde dentro del ZIP.
2. Necesitas Python 3.11 o posterior; la versión comprobada es **Python 3.12**. El lanzador crea un entorno `.venv` e instala las dependencias. La primera instalación necesita internet.
3. Mac: abre `Iniciar_GaitSPM.command`. Si el sistema no lo permite, abre Terminal en la carpeta y ejecuta `bash Iniciar_GaitSPM.command`.
4. Windows: ejecuta `Iniciar_GaitSPM.bat`. Linux: `bash iniciar_gaitspm.sh`.
5. Se abre `http://127.0.0.1:4173` en tu navegador. Deja la consola abierta; Ctrl+C detiene el servidor. Si el puerto está ocupado: `python3 launch.py --port 4175` (Windows: `py -3 launch.py --port 4175`).

También puedes ejecutar directamente `python3 launch.py`. El análisis se realiza en tu ordenador. Tras instalar las dependencias, el modo local no necesita internet. No hay cuentas ni servicio remoto de análisis. El archivo subido se guarda temporalmente en el equipo y se limpia al cerrar normalmente el servidor; no uses un equipo compartido para datos identificables. La aplicación no sustituye un sistema de gestión clínica.

## Primer recorrido

En **Modo guiado**, pulsa **Cargar ejemplo** en una tarjeta; revisa los participantes y el mapeo; abre **Configurar y analizar** y ejecuta. Las recetas se aplican al ejemplo original. Los casos 07/08 seleccionan automáticamente el grupo de pacientes y las condiciones repetidas.

Para probar la carga de archivos, usa CSV o Excel de esa misma tarjeta, o los archivos incluidos en `datasets/synthetic/`. El Excel tiene `Guide`, `Metrics`, `Curves_Wide` y `Participants`; la aplicación selecciona `Curves_Wide`. Revisa los campos y pulsa **Aplicar**. Los archivos originales se reconocen para proponer su configuración; si cambias los datos, configura el análisis manualmente.

En datos propios, confirma grados, segmentación de ciclos y mapeo articular. Los nodos 0–100 son porcentaje del ciclo ya segmentado: la aplicación no detecta eventos de marcha ni transforma señales de sensores en ángulos articulares. Consulta `docs/GUIA_EJEMPLOS.md` para resultados esperados y limitaciones.

## Ocho ejemplos, seis contextos clínicos

| Ejemplo | Contexto | Participantes | Diseño recomendado |
|---|---|---|---|
| 01 | Síndrome de pinzamiento femoroacetabular (FAIS) | 30 casos + 30 controles | Dos grupos, Welch |
| 02 | Artrosis de rodilla | 30 + 30 | Dos grupos, Welch |
| 03 | Artrosis de cadera | 30 + 30 | Dos grupos, Welch |
| 04 | Esclerosis múltiple | 30 + 30 | Dos grupos, Welch |
| 05 | Artroplastia de cadera | 30 + 30 | Dos grupos, Welch |
| 06 | Reconstrucción de LCA | 30 + 30 | Dos grupos, Welch |
| 07 | EM: fatiga y recuperación hipotéticas | 30 + 30, tres condiciones | ANOVA de medidas repetidas en 30 casos |
| 08 | LCA: repetición técnica sin efecto sistemático | 30 + 30, dos condiciones | t pareada en 30 casos |

Son **datos simulados**, no pacientes reales. Cada archivo contiene 60 IDs únicos. Hay 480 participantes sintéticos diferentes entre los ocho ejemplos; las condiciones repetidas conservan sus IDs. Solo se incluyen ángulos articulares en grados, sin fuerzas, momentos ni EMG. La covariable `technical_score` es aleatoria y no tiene significado clínico.

Los seis primeros mantienen los anclajes escalares documentados en 1.3; se simulan las formas de las curvas. Los dos últimos añaden situaciones didácticas de las mismas patologías. No emparejes los participantes de 03 con 05: son ejemplos independientes, no un seguimiento quirúrgico.

## Compatibilidad 1.4.2

Lectura y generación de fuentes con UTF-8 explícito, independiente de la configuración regional de Windows. El workflow de GitHub comprueba Linux, Windows y macOS: creación de un entorno `.venv` nuevo mediante `launch.py`, arranque sin abrir navegador, carga HTTP y análisis de ejemplos, CSV externo y pruebas DOM. La comprobación visual, el selector de archivos y el doble clic en los lanzadores siguen requiriendo una prueba manual. Estado de las ejecuciones: https://github.com/AngelGF8/GaitSPM/actions.

## Auditoría adicional 1.4.1

Se probó un CSV público independiente de MovementRx: 20 curvas reales de referencia, con adaptación explícita de encabezados e IDs. No se modificó ningún ángulo. Los grupos TestA/TestB son etiquetas arbitrarias de prueba, no grupos clínicos. El recorrido HTTP de carga, mapeo, Welch y exportaciones pasó; el estadístico coincidió con SciPy con error máximo 1,25×10⁻¹⁴. CSV de prueba: `tests/fixtures/movementrx/movementrx_import_test.csv`. Fuente, licencia y conversión: `tests/fixtures/movementrx/README.md`.

Se corrigieron IDs con ceros iniciales, interpretación de NA como ID, cabeceras y tokens duplicados, errores de subida ocultos, mapeos pendientes y reutilización de resultados tras una carga o configuración fallida. Consulta las pruebas reproducibles en `tests/README.md`.

## Qué cambia

- Recorrido de cuatro pasos, galería de ocho ejemplos y cambio entre modo guiado y laboratorio.
- Interpretación calculada con el resultado actual: n analizado, intervalos del ciclo, p de clúster, diferencias descriptivas y exclusiones. Exportación JSON con configuración y versiones.
- CSV español con coma decimal y delimitadores entre comillas; Excel con hoja de guía antes de los datos.
- Validación de roles, lateralidad, covariables y datos incompletos; evita completar artificialmente una curva combinando huecos de lados o ensayos distintos.
- Filtro de grupo en comparaciones pareadas de lados, invalidación de resultados al cambiar datos/configuración y bloqueo durante el cálculo.
- Lanzadores locales y spm1d incluido; exportaciones de gráficos y tablas conservadas.

## Interpretación y límites

SPM1D analiza campos de curvas continuas; sus clústeres no equivalen a pruebas independientes de cada nodo. El ajuste Bonferroni entre variables es adicional al control sobre el campo temporal. Un resultado no significativo no demuestra equivalencia. Los IC95 dibujados son puntuales y las diferencias dentro de clústeres son descriptivas, calculadas tras seleccionarlos.

Las recetas fijan α=0,05, pruebas bilaterales cuando procede y Bonferroni entre variables. No se debe cambiar de método buscando significación. La prueba de normalidad es orientativa; el modo automático no certifica supuestos. Las permutaciones de etiquetas entre grupos no ofrecen una alternativa Welch para varianzas desiguales. ANOVA de medidas repetidas depende de los supuestos de esfericidad: spm1d no aplica corrección de no esfericidad para ese diseño. Los post hoc son los que localizan pares tras el contraste global.

La documentación oficial del motor se encuentra en https://spm1d.org/doc/Stats1D/anova.html y https://spm1d.org/doc/Stats1D/ . Las instrucciones de verificación están en `tests/README.md`. Esta revisión es una auditoría técnica interna, no validación clínica ni certificación.

## Código y pruebas

Edita `app/gaitspm_app.py` para modificar el motor; `app/sync_html_engine.py` genera `gaitspm_engine.py` y el HTML desde las mismas fuentes. La interfaz está en `app/web/`; el servidor local es `app/serve.py`. Consulta `tests/README.md`.

El modo Streamlit se conserva como alternativa de desarrollo (`requirements-streamlit.txt`) pero no se ha probado en esta versión. Abrir directamente `app/gaitspm.html` activa la alternativa Pyodide, que requiere descargar su runtime y no se ha validado aquí. El camino recomendado es el lanzador local.

Autor: Ángel González de la Flor. Licencia GPL v3. La guía de publicación está en `docs/publication.md`.
