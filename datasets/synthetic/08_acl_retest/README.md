# ACL · repeat measurement without systematic change

30 cases + 30 controls; 2 condition(s). SYNTHETIC DATA.

Hypothetical teaching scenario added in v1.4. No published clinical effects.

Simulación longitudinal: 30 ACLR y 30 controles, TEST/RETEST. Generador sin cambio sistemático; un resultado no significativo no prueba equivalencia.

Recommended configuration: `{"design": "paired_cond", "groups": null, "cond": null, "cond_levels": ["TEST", "RETEST"], "group_filter": "ACLR", "side_mode": "L", "mode": "param", "equal_var": true, "alpha": 0.05, "two_tailed": true, "field_correction": "bonferroni"}`.

Load 08_acl_retest.csv or the Curves_Wide sheet in 08_acl_retest.xlsx. Guided mode recognizes the original datasets and proposes settings. Edited files require manual review.

- SYNTHETIC DATA. No real patients. Not a sample-size calculation.
- 60 unique participants: 30 cases + 30 controls per example; repeated conditions do not increase independent n.
- Angles in degrees; 101 nodes = 0–100% of an already segmented gait cycle.
- L is an indexed simulated limb, not necessarily the clinically affected left side.
- First six examples preserve v1.3 scalar literature anchors by finite-sample moment matching; temporal shapes and covariance are assumed.
- Positive ROM anchors use positive skewed quantiles when normal quantiles would produce a negative ROM.
- Examples 07/08 add fully hypothetical repeated conditions. No published treatment or fatigue effect is reproduced.
- technical_score is a random numerical teaching covariate, not a validated clinical score.
- Cohorts are independent across files. Do not pair example 03 with 05 or pool controls.
- p-values and cluster locations are calculated from these synthetic arrays, not from the cited publications.
