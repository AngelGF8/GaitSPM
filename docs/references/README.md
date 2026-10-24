# Fuentes y supuestos de simulación

Unidades: grados. Los **34 pares media/DE** completos están en datasets/synthetic/calibration_all.csv; cada base incluye metadatos con población, anclajes y supuestos.

| Base | Fuente primaria y tabla | Parámetros |
| --- | --- | --- |
| FAI | [Hao 2025](https://doi.org/10.1186/s12891-025-08727-4), tabla 2, FAIS sin BDDH | Tres ROM de cadera |
| Rodilla OA | [Huang 2008](https://doi.org/10.1016/j.medengphy.2008.02.006), tabla 3 | Cadera/rodilla T1 y tobillo T3 |
| Cadera OA | [Bahr 2021](https://doi.org/10.12659/MSM.934558), tabla 2 PreOP | Tres ROM de cadera |
| EM | [Lencioni 2016](https://doi.org/10.3389/fnhum.2016.00620), tabla 1 | ROM sagital cadera, rodilla y tobillo |
| Artroplastia | [Bahr 2021](https://doi.org/10.12659/MSM.934558), tabla 2 PostOP | Tres ROM de cadera |
| LCA | [Noehren 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC4313379/), tabla 2 WALK | Flexión cadera/rodilla al impacto inicial; no carrera |

Ejemplos control frente a caso:

- FAI ROM sagital cadera: 46,86 ± 3,79 vs 46,11 ± 5,82.
- Rodilla OA, cadera T1: 27,57 ± 4,66 vs 22,77 ± 7,47.
- Cadera OA ROM sagital: 43,61 ± 4,78 vs 25,27 ± 9,93.
- EM ROM rodilla: 56 ± 5 vs 46 ± 15.
- Artroplastia ROM sagital cadera: 43,61 ± 4,78 vs 33,14 ± 8,55.
- LCA flexión cadera: 26,1 ± 7,4 vs 20,0 ± 7,4. Rodilla: signo invertido a flexión positiva, DE sin cambio.

## Alcance

El n=60 (30 por grupo) es el tamaño didáctico, no la muestra original de los artículos. Treinta cuantiles estandarizados por grupo igualan media y DE muestral (ddof=1); para ROM que produciría valores negativos se usan cuantiles lognormales reescalados; no son observaciones iid clínicas. Formas PCHIP, offsets, fases, ruido suave sigma=4 nodos y correlaciones son asumidos. Un ROM no identifica una trayectoria completa.

Los valores de fase se imponen en nodos sintéticos especificados. En LCA, los anclajes se asignan a nodos 0 y 12 como ejercicio técnico, no afirmando que el artículo midiera esos instantes. No se reconstruyen picos individuales.

EM representa marcha lenta (EDSS medio 5,8), no todo su espectro. FAI sintomático no equivale a cam asintomático. Los ejemplos Bahr son independientes: **no emparejar 03 y 05 ni inferir recuperación**. technical_score es aleatorio, sin significado clínico. L es lado índice simulado, no lateralidad real de los artículos.

Los clústeres de estas curvas artificiales no replican resultados clínicos ni justifican conclusiones diagnósticas. Las tablas publicadas calibran escalares, no todos los nodos de las curvas.

## Casos 07 y 08 añadidos en 1.4

Reutilizan EM y LCA con nuevos IDs. Fatiga/recuperación y repetición técnica son escenarios hipotéticos. Sus amplitudes de cambio, correlación entre medidas y ausencia de efecto sistemático en 08 son supuestos didácticos, no datos publicados. Cada caso conserva 30 casos y 30 controles; el diseño recomendado analiza las condiciones de los 30 casos.
