# Statistical designs

| Question | Design | Observation unit |
|---|---|---|
| Difference between independent groups | Student or Welch t | One curve per participant |
| Within-participant change | Paired t | Matched participant across conditions or sides |
| Differences among three or more groups | One-way ANOVA | Independent participant |
| Three or more within-participant conditions | Repeated-measures ANOVA | Complete matched participant |
| Association with one continuous predictor | Regression | Independent participant |
| Two-group difference adjusted for speed or other covariates | ANCOVA | Independent participant, one condition |
| Linear combination of numeric predictor coefficients | GLM t contrast | Independent participant, one condition |
| Group × condition with different people in every cell | Two-way independent ANOVA | Independent participant in one cell only |
| Group × condition with the same people across conditions | Mixed ANOVA | Participant nested within group |

## ANCOVA and GLM

The GLM accepts selected numeric predictors, an automatically added intercept and an explicit nonzero t-contrast. Predictors are centered after complete-case selection. With speed and age selected, `[0, 1, 0]` tests the speed coefficient adjusted for age. Predictor order is the selection order; the stored model includes subject IDs, columns, matrix and contrast. Categorical covariates require explicit coding outside this interface. This release does not implement arbitrary omnibus F contrasts or repeated-measures GLMs.

ANCOVA supports exactly two groups and one or more numeric covariates. The design is `[intercept, second_group_indicator, centered_covariates...]`; contrast `[0, 1, 0, ...]` estimates the adjusted second-minus-first group difference. It assumes common slopes; it does not test or fit group-by-covariate interactions. Covariates must be constant within each selected participant/condition/side. Missing covariates exclude a participant; conflicting metadata, zero contrasts, constant/collinear predictors and rank-deficient models are rejected.

Both require parametric inference and equal residual variance. No Welch, mixed-effects covariance, or nonparametric GLM is implied. Numerical normality checks are not currently computed for these new designs.

## Factorial ANOVA

The two factors are the imported `group` and `condition` columns. At least two levels of each and three complete participants per cell are required. Only balanced cell sizes after exclusions are supported in this release. Independent ANOVA rejects any participant appearing in more than one cell. Mixed ANOVA intersects complete participants across the selected conditions within each group.

Choose group, condition or interaction for display. Every analysis divides alpha by three for the factorial family, even if only one effect is displayed. Across-variable Bonferroni is additional: with three variables, inference uses alpha/9. Displayed adjusted p-values include both corrections. Choosing no across-variable correction still preserves the factor-family correction. There are no automatic factorial post-hoc comparisons.

Mixed ANOVA assumes sphericity and equal variance. With one averaged response per subject/condition, spm1d uses approximate residuals for inference; the warning is preserved in the results. This matches upstream behaviour and is a methodological limitation, not something concordance tests remove.

## Permutations and multiplicity

Existing independent, paired, one-way ANOVA and regression paths retain their permutation options. Permutation validity depends on exchangeability. Label permutation is not a Welch alternative. Family correction across variables is Bonferroni or none; cluster-minimum Holm/FDR adjustment is not offered.

Sources: the bundled, unmodified `vendor/spm1d/stats/t.py` and `vendor/spm1d/stats/anova/ui.py`; [official spm1d documentation](https://spm1d.org/doc/Stats1D/). See the [numerical concordance scope](validation-guide.md) for precisely what is tested.

Agreement with direct spm1d calls does not establish false-positive control for these extensions across arbitrary data distributions. In particular, variance violations and nonsphericity are robustness challenges, not supported alternatives to the stated assumptions.
