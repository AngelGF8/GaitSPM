# LCA · repetición sin cambio sistemático / ACL · repeat measurement without systematic change

30 casos + 30 controles; 2 condición/es. DATOS SINTÉTICOS.

Escenario didáctico hipotético añadido en v1.4. Sin efectos clínicos publicados.

Simulación longitudinal: 30 ACLR y 30 controles, TEST/RETEST. Generador sin cambio sistemático; un resultado no significativo no prueba equivalencia.

Configuración recomendada: `{"design": "paired_cond", "groups": null, "cond": null, "cond_levels": ["TEST", "RETEST"], "group_filter": "ACLR", "side_mode": "L", "mode": "param", "equal_var": true, "alpha": 0.05, "two_tailed": true, "field_correction": "bonferroni"}`.

Cargar 08_acl_retest.csv o la hoja Curves_Wide de 08_acl_retest.xlsx. El modo guiado reconoce las bases originales y propone la configuración. Los archivos editados requieren revisión manual.

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
