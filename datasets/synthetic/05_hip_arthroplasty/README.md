# Artroplastia de cadera / Hip arthroplasty

30 casos + 30 controles; 1 condición/es. DATOS SINTÉTICOS.

Parámetros heredados de v1.3: [Bahr et al. (2021), Table 2, postoperative hip vs controls](https://doi.org/10.12659/MSM.934558).

Postoperative S-ROM total hip arthroplasty; n=23 cases, n=39 controls. Separate cross-sectional synthetic base, not a longitudinal pairing with base 03.

Configuración recomendada: `{"design": "ttest2", "groups": ["Control", "THA"], "cond": "BASE", "cond_levels": null, "group_filter": null, "side_mode": "L", "mode": "param", "equal_var": false, "alpha": 0.05, "two_tailed": true, "field_correction": "bonferroni"}`.

Cargar 05_hip_arthroplasty.csv o la hoja Curves_Wide de 05_hip_arthroplasty.xlsx. El modo guiado reconoce las bases originales y propone la configuración. Los archivos editados requieren revisión manual.

- DATOS SINTÉTICOS / SYNTHETIC DATA. No real patients. Not a sample-size calculation.
- 60 unique participants: 30 cases + 30 controls per example; repeated conditions do not increase independent n.
- Angles in degrees; 101 nodes = 0–100% of an already segmented gait cycle.
- L is an indexed simulated limb, not necessarily the clinically affected left side.
- First six examples preserve v1.3 scalar literature anchors by finite-sample moment matching; temporal shapes and covariance are assumed.
- Positive ROM anchors use positive skewed quantiles when normal quantiles would produce a negative ROM.
- Examples 07/08 add fully hypothetical repeated conditions. No published treatment or fatigue effect is reproduced.
- technical_score is a random numerical teaching covariate, not a validated clinical score.
- Cohorts are independent across files. Do not pair example 03 with 05 or pool controls.
- p-values and cluster locations are calculated from these synthetic arrays, not from the cited publications.
