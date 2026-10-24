# CSV externo: MovementRx

**Origen independiente de GaitSPM:** https://github.com/aalhossary/MovementRx, commit `70f97b52b55e476fa52f9e733a98cefe55532c18`.

Archivo original: `spmclient/res/refData/kinematic/L_KneeX_Ang_Ref.csv`. Se conserva sin cambios en `original/`; su blob SHA-1 es `b971c393d1fa5219e49ba7755ce784189e36c4f8`. Licencia GPL v3 del repositorio conservada en LICENSE; README original en UPSTREAM_README.md.

Artículo: Alhossary A, Pataky T, Ang WT, Chua KSG, Kwong WH, Donnelly CJ. Versatile clinical movement analysis using statistical parametric mapping in MovementRx. Scientific Reports. 2023;13:2414. https://doi.org/10.1038/s41598-023-29635-4

El artículo describe una curva media de ensayos por participante en los archivos de referencia. Este CSV contiene 20 filas y 101 ángulos de rodilla izquierda en el plano X/sagital. La convención de signos del original se conserva. No se reconstruyen ni simulan trayectorias.

## Adaptación explícita

El original tiene columnas V1…V100 y una última cabecera vacía. No incluye identificadores ni grupos, y por tanto **no se importa directamente como base de participantes válida**. GaitSPM rechaza la falta de ID; no debe usarse una columna de ángulos como identificador.

`movementrx_import_test.csv` añade IDs de fila MRX01…MRX20, condición REFERENCE, lado L y renombra los 101 nodos como KneeSagittal_0…100. Las filas pares/impares reciben TestA/TestB, 10 en cada etiqueta. Esta división es exclusivamente técnica y arbitraria: **no representa patologías ni intervenciones**. Todos los valores de las curvas son idénticos al original (diferencia máxima 0).

La prueba compara Welch entre esas etiquetas para verificar el programa, no para formular una conclusión clínica. No hay clústeres significativos con esta configuración. Eso no demuestra equivalencia. No mezclar este control de software con los ocho ejemplos sintéticos de 30+30 participantes.

## Repetir en GaitSPM

1. Inicia `python launch.py` y carga `movementrx_import_test.csv`.
2. Aplica subject → ID, group → grupo, condition → condición, side → lado.
3. Comprueba 20 participantes, TestA=10/TestB=10, 101 nodos y KneeSagittal → rodilla/sagital; confirma unidades y mapeo.
4. Selecciona dos grupos independientes, TestA/TestB, REFERENCE, solo L, paramétrico, varianzas iguales desactivado (Welch), bilateral, α=0,05, Bonferroni.
5. Ejecuta y exporta. La figura obtenida durante la auditoría está en `audit-v1.4.1/external-result.png`.

Recrear la adaptación: `python scripts/prepare_external_csv.py`. Prueba reproducible de carga HTTP real: `python tests/test_external_upload.py`.
