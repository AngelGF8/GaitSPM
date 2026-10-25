# ACL reconstruction

30 cases + 30 controls; 1 condition(s). SYNTHETIC DATA.

Scalar parameters retained from v1.3: [Noehren et al. (2013), Table 2, walking (not running)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4313379/).

Females after ACL reconstruction, mean 5.2 years since surgery. Knee flexion sign reversed to flexion-positive; SD unchanged. Scalar loading-response values assigned to synthetic nodes.

Recommended configuration: `{"design": "ttest2", "groups": ["Control", "ACLR"], "cond": "BASE", "cond_levels": null, "group_filter": null, "side_mode": "L", "mode": "param", "equal_var": false, "alpha": 0.05, "two_tailed": true, "field_correction": "bonferroni"}`.

Load 06_acl.csv or the Curves_Wide sheet in 06_acl.xlsx. Guided mode recognizes the original datasets and proposes settings. Edited files require manual review.

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
