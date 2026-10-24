# Auditoría previa a GitHub · GaitSPM 1.4.1

24 de octubre de 2026. Revisión técnica asistida por IA. No es validación clínica ni auditoría externa. Esta revisión amplía la 1.4.0 con datos ajenos a su generador y con pruebas del servidor real.

## Resultado

El recorrido carga → lectura → mapeo → análisis → explicación → exportación pasó por HTTP local con un CSV independiente. El original no dispone de IDs; se comprobó su rechazo y después se usó una adaptación documentada que conserva todos los ángulos. La comparación contra SciPy mostró un error absoluto máximo de 1,2434497875801753e-14 en el estadístico de Welch.

## CSV ajeno y alcance de la prueba

MovementRx, archivo público `L_KneeX_Ang_Ref.csv`, 20 participantes de referencia × 101 nodos. Fuente y licencia verificadas en el repositorio de sus autores; original intacto, checksum, atribución y script de adaptación incluidos en `tests/fixtures/movementrx/`. Artículo: https://doi.org/10.1038/s41598-023-29635-4.

La adaptación añade IDs, condición/lado y etiquetas TestA/TestB por filas alternas (10+10) y renombra nodos. **No se simula ni altera ningún valor de curva.** Las dos etiquetas son una partición arbitraria para probar el software, no grupos clínicos. La ausencia de clústeres significativos en esta prueba no es un hallazgo clínico ni evidencia de equivalencia. El tamaño 20 corresponde a este CSV externo; los ocho ejemplos de demostración siguen teniendo 30 casos + 30 controles.

## Errores encontrados y corregidos

| Hallazgo | Corrección | Verificación |
|---|---|---|
| CSV convertía 001 y 1 al mismo número; NA se convertía en valor ausente | Lectura textual de CSV y conversión numérica solo de medidas/covariables; Excel conserva texto | IDs 001, 1 y NA distintos, con decimal punto/coma |
| Cabeceras repetidas podían ser renombradas silenciosamente por pandas | Rechazo previo de duplicados tras quitar espacios | Test con dos columnas del mismo nombre |
| Tokens transpuestos duplicados o ausentes podían sobrescribir identidad | Roles de identidad únicos y tokens obligatorios | Dos pruebas de rechazo |
| Error de red/subida se ocultaba; formulario anterior podía seguir disponible | Mensaje visible y limpieza de formulario, datos y configuración anteriores | Test DOM con fallo de subida |
| Archivo nuevo fallido dejaba un dataframe anterior en el servidor | Limpieza al subir y al iniciar lectura | HTTP real: nuevo archivo inválido y rechazo del mapeo anterior |
| Configuración de ejecución inválida podía coexistir con resultados previos | Invalidación antes de validar; guardar configuración solo si válida | HTTP real: α inválida elimina resultados/configuración previos |
| Edición de clasificación articular sin guardar permitía desajuste cliente/servidor | Invalidar resultados y bloquear análisis hasta guardar | Prueba DOM en los ocho ejemplos |
| Descriptor de archivo no cerrado explícitamente | Lectura con gestor de contexto | Desaparecen ResourceWarnings en prueba de carga |

## Evidencias ejecutadas

- Las **20 pruebas Python anteriores** pasaron tras las correcciones del lector y mapeo: `../audit-v1.4/tests-prepublish.log`.
- **3 pruebas nuevas**: identidad/cabeceras, tokens transpuestos y recorrido completo del CSV externo con fallos posteriores: `tests-external.log`.
- Se repitieron las comprobaciones afectadas del puente/HTTP y la identidad del motor generado: `tests-final-targeted.log`.
- Ocho recorridos DOM ES/EN, guardado de mapeo, cambio de modo, invalidación y fallo de subida: `tests-ui.log`. El puente de estas pruebas DOM usa fixtures; la prueba externa usa el servidor y motor reales.
- CSV externo: 20 curvas completas, n=10+10 en el contraste de prueba, una variable. CSV/XLSX de tabla y PNG/SVG/PDF de figura generados y verificados. La figura PNG se inspeccionó visualmente sin cortes ni etiquetas superpuestas.
- `external-evidence.json` registra fuente, muestras, diferencia numérica, operaciones HTTP y tamaños de exportación. `external-result.png` es una salida real del motor, no un mockup.

## Preparación de GitHub

Cuenta conectada verificada: AngelGF8. No se localizó un repositorio GaitSPM entre los repositorios accesibles. La integración admite lectura y escritura de archivos, ramas y commits, pero no creación de repositorios. La página de creación de GitHub requiere inicio de sesión en el navegador. No se ha subido código a un repositorio ajeno ni se ha marcado la publicación como realizada. La publicación queda condicionada a disponer del repositorio correcto y acceso autorizado.

Se incluye un workflow de GitHub Actions con pruebas del motor, puente, regresiones, CSV externo y DOM. **Preparado no significa ejecutado en GitHub**: se verificarán sus resultados tras la subida. El paquete solo contiene código, ejemplos sintéticos y el pequeño CSV público atribuido, no datos privados de pacientes ni credenciales. Los mockups son propuestas y no evidencias de ejecución.

## Límites pendientes

No se ejecutó esta interfaz en un navegador real: sigue pendiente la comprobación visual y de interacción física con el selector de archivos. Se probó la subida HTTP del mismo servidor que utiliza el navegador, sin simular el backend. No se sustituyen estas pruebas por capturas de los mockups. Tampoco se verificó una instalación limpia Mac/Windows. El lanzador Linux con entorno preparado fue comprobado en la revisión anterior.

La auditoría no confirma supuestos de inferencia clínica, validez diagnóstica ni generalización a todos los CSV de laboratorios. El archivo externo necesita adaptación de metadatos; se documenta expresamente y no se afirma compatibilidad directa con cualquier exportación de Vicon/Visual3D.
