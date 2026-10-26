# Numerical concordance with spm1d 0.4.53

Run `python tests/test_spm1d_validation.py` after regenerating the shared engine with `python app/sync_html_engine.py`.

The deterministic synthetic fixtures exercise independent and paired tests, regression, one-way and repeated-measures ANOVA, numeric GLM, ANCOVA, and independent/mixed two-way ANOVA. Reference models are assembled independently and call spm1d directly. Assertions cover full statistic fields, critical thresholds, rejection decisions, cluster counts, endpoints and probabilities. Additional tests check rank, complete-case selection, repeated IDs, balance, correction across variables/effects, and the browser bridge.

Both paths use the bundled spm1d implementation. These checks establish numerical concordance for the tested configurations and check data preparation and software integration. They do **not** establish Type I error control across all supported designs or data distributions, independently validate the underlying statistical algorithms, or establish clinical validity. A shared inferential implementation can agree exactly while producing inappropriate false-positive rates when its assumptions fail. See the statistical-design guide for model assumptions and limitations.

CI runs software checks without publishing research reports. Manuscripts, external multi-dataset findings, figures and numerical report files are maintained outside this public software update.

## Separate evaluation of error rates

The [Monte Carlo protocol](monte-carlo-protocol.md) specifies 38 scenarios and 5,000 replications per scenario for the new adjusted and factorial paths. It separates assumption-respecting models from deliberate variance/sphericity violations, and measures both per-field false-positive events and their familywise union. Factorial effects and cross-variable multiplicity are included; selected partial-null families are also tested.

Concordance checks are deterministic software regression tests. Monte Carlo error estimates are finite-scenario research results with sampling uncertainty. A rate below 0.05 can be conservative; a nonsignificant inflation test is not proof of equivalence. Neither form of evidence licenses arbitrary GLMs or unrestricted mixed designs. Research outputs stay separate from the public software documentation until explicitly released.

The simulation runner calls the shared production inference and correction functions, with full data-preparation checkpoints, rather than evaluating a newly written statistical implementation. Small CI checks test the harness, not inferential validity. See the protocol for reproducibility, endpoints, assumptions, exact binomial intervals, and reporting rules.

The bundled dependency remains spm1d **0.4.53**. Testing or migrating to 0.5 is deferred until the upstream author supplies it; no compatibility claim is made.
