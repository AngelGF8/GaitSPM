# Guía de los ocho ejemplos

Resultados calculados el 24 de octubre de 2026 con GaitSPM 1.4.0 / spm1d 0.4.53, semillas fijas. Cada caso tiene 30 pacientes sintéticos y 30 controles sintéticos. Se proponen ejercicios de análisis, no conclusiones sobre pacientes reales.

Recorrido: cargar → revisar mapeo y calidad → configurar → ejecutar → leer interpretación y detalle → exportar. Por defecto se analizan todas las variables del caso, lado L, α=0,05 y Bonferroni entre variables. Dos grupos: Welch. Medidas repetidas: solo casos, mismos IDs.
## 01_fai · FAI sintomático

**Diseño:** `ttest2`. **Grupos:** ['Control', 'FAIS']. **Filtro:** ninguno. **Condiciones:** BASE.

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 | Ninguno |
| HipAdduction | 30 / 30 | Ninguno |
| HipRotation | 30 / 30 | Ninguno |

**Qué observar:** Aprende a distinguir diferencias visuales de un contraste que supera el umbral. Ninguna variable presenta clústeres confirmados con esta receta; esto no demuestra equivalencia.

**Archivos:** `datasets/synthetic/01_fai/01_fai.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## 02_knee_oa · Artrosis de rodilla

**Diseño:** `ttest2`. **Grupos:** ['Control', 'KOA']. **Filtro:** ninguno. **Condiciones:** BASE.

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–0.8%; p=0.050; 67.0–72.5%; p=0.049; 87.3–95.7%; p=0.048; 98.9–100.0%; p=0.050 |
| KneeFlexion | 30 / 30 | 0.0–100.0%; p<0,001 |
| AnkleDorsiflexion | 30 / 30 | Ninguno |

**Qué observar:** Localiza las regiones que superan el umbral y compáralas con las curvas medias. Revisa qué variables no son significativas y el signo del contraste antes de interpretar la dirección. La magnitud media mostrada dentro de un clúster es descriptiva.

**Archivos:** `datasets/synthetic/02_knee_oa/02_knee_oa.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## 03_hip_oa · Artrosis de cadera

**Diseño:** `ttest2`. **Grupos:** ['Control', 'HOA']. **Filtro:** ninguno. **Condiciones:** BASE.

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–39.2%; p<0,001; 51.9–100.0%; p<0,001 |
| HipAdduction | 30 / 30 | 0.0–59.7%; p<0,001; 83.7–100.0%; p=0.017 |
| HipRotation | 30 / 30 | 0.0–53.3%; p<0,001; 82.0–100.0%; p=0.002 |

**Qué observar:** Localiza las regiones que superan el umbral y compáralas con las curvas medias. Revisa qué variables no son significativas y el signo del contraste antes de interpretar la dirección. La magnitud media mostrada dentro de un clúster es descriptiva.

**Archivos:** `datasets/synthetic/03_hip_oa/03_hip_oa.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## 04_multiple_sclerosis · Esclerosis múltiple

**Diseño:** `ttest2`. **Grupos:** ['Control', 'MS']. **Filtro:** ninguno. **Condiciones:** BASE.

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 | Ninguno |
| KneeFlexion | 30 / 30 | 81.3–88.4%; p=0.022 |
| AnkleDorsiflexion | 30 / 30 | 0.0–56.0%; p<0,001; 65.3–100.0%; p<0,001 |

**Qué observar:** Localiza las regiones que superan el umbral y compáralas con las curvas medias. Revisa qué variables no son significativas y el signo del contraste antes de interpretar la dirección. La magnitud media mostrada dentro de un clúster es descriptiva.

**Archivos:** `datasets/synthetic/04_multiple_sclerosis/04_multiple_sclerosis.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## 05_hip_arthroplasty · Artroplastia de cadera

**Diseño:** `ttest2`. **Grupos:** ['Control', 'THA']. **Filtro:** ninguno. **Condiciones:** BASE.

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–33.6%; p<0,001; 56.1–100.0%; p<0,001 |
| HipAdduction | 30 / 30 | 0.0–57.3%; p<0,001; 90.3–100.0%; p=0.034 |
| HipRotation | 30 / 30 | Ninguno |

**Qué observar:** Localiza las regiones que superan el umbral y compáralas con las curvas medias. Revisa qué variables no son significativas y el signo del contraste antes de interpretar la dirección. La magnitud media mostrada dentro de un clúster es descriptiva.

**Archivos:** `datasets/synthetic/05_hip_arthroplasty/05_hip_arthroplasty.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## 06_acl · Reconstrucción LCA

**Diseño:** `ttest2`. **Grupos:** ['Control', 'ACLR']. **Filtro:** ninguno. **Condiciones:** BASE.

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–100.0%; p<0,001 |
| KneeFlexion | 30 / 30 | Ninguno |

**Qué observar:** Localiza las regiones que superan el umbral y compáralas con las curvas medias. Revisa qué variables no son significativas y el signo del contraste antes de interpretar la dirección. La magnitud media mostrada dentro de un clúster es descriptiva.

**Archivos:** `datasets/synthetic/06_acl/06_acl.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## 07_ms_fatigue · Esclerosis múltiple · fatiga y recuperación

**Diseño:** `anova1rm`. **Grupos:** None. **Filtro:** MS. **Condiciones:** ['BASE', 'FATIGUE', 'RECOVERY'].

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 / 30 | 48.0–89.4%; p<0,001 |
| KneeFlexion | 30 / 30 / 30 | 44.4–91.9%; p<0,001 |
| AnkleDorsiflexion | 30 / 30 / 30 | 47.3–88.1%; p<0,001 |

**Qué observar:** Identifica un efecto global entre BASE, FATIGUE y RECOVERY. Consulta los post hoc para localizar los pares. Las tres condiciones son de los mismos 30 casos; no son 90 pacientes. El cambio se introdujo deliberadamente en el generador y no representa eficacia clínica.

**Archivos:** `datasets/synthetic/07_ms_fatigue/07_ms_fatigue.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## 08_acl_retest · LCA · repetición sin cambio sistemático

**Diseño:** `paired_cond`. **Grupos:** None. **Filtro:** ACLR. **Condiciones:** ['TEST', 'RETEST'].

| Variable | n incluido | Clústeres confirmados (% ciclo; p ajustada) |
|---|---|---|
| HipFlexion | 30 / 30 | Ninguno |
| KneeFlexion | 30 / 30 | Ninguno |

**Qué observar:** Compara TEST y RETEST con emparejamiento por ID. El generador no incluye desplazamiento sistemático, pero sí ruido entre mediciones. No hay clústeres significativos con esta receta. No equivale a demostrar fiabilidad ni equivalencia; esos objetivos requieren diseños y medidas específicos.

**Archivos:** `datasets/synthetic/08_acl_retest/08_acl_retest.csv` y `.xlsx`. Las fórmulas ROM y media de Metrics se actualizan al editar Curves_Wide; los resultados SPM se recalculan en GaitSPM.

## Supuestos de simulación

Los casos 01–06 igualan medias y DE escalares heredadas de la versión 1.3 con cuantiles estandarizados; por ello no constituyen muestras iid de pacientes. Se impusieron formas, suavidad, fases y correlaciones. Los casos 07/08 añaden cambios y ruido hipotéticos. El caso 05 es un contexto posartroplastia, no una séptima patología. Los 480 IDs son diferentes entre conjuntos. Las fuentes y límites se documentan en references/README.md y en cada metadata.json.

Los resultados de esta guía solo corresponden a los archivos originales y a sus recetas. Cambiar variables, grupos, corrección, lado o método modifica los resultados. Guarda el JSON del análisis si necesitas conservar su configuración.
