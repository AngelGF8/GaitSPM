# Monte Carlo protocol: finite-scenario Type I error

Protocol ID: `gaitspm-mc-1`. Planned production run: **5,000 independent replications per scenario**, family alpha 0.05, 101 nodes, bundled **spm1d 0.4.53**. No evaluation or installation of 0.5 is part of this work. This is a prospective computational specification, not an externally preregistered study or a claim of general validity.

## Aim and scope

Evaluate false-positive probabilities of the production ANCOVA, numeric GLM t contrast, balanced independent two-way ANOVA and mixed two-way ANOVA paths, including Bonferroni across variables and all three factorial effects. Numerical agreement with direct spm1d calls remains a separate software integration check.

The study samples a finite, deliberately limited set of Gaussian, stationary, fully observed fields. It does not cover all biomechanical distributions, arbitrary GLMs, nonstationary smoothness, outliers, missing-data mechanisms, post-hoc selection, permutation validity, optional Streamlit/Pyodide execution, or clinical validity. No observed rate is a guarantee for future datasets.

## Data-generating mechanisms

An independent NumPy `Generator` stream is derived from master seed **20261026**, a SHA-256-derived scenario identifier, and the replication number. Worker count and scheduling do not change the random samples. Every replication generates new errors and covariates; there is no finite-sample moment matching, outcome-dependent rerunning, or stopping when a desired p-value is reached.

Gaussian white noise is smoothed along the node axis using a Gaussian kernel with standard deviation `FWHM / sqrt(8 log(2))`, truncated at four standard deviations. The generator pads both ends by the kernel radius and crops the central 101 nodes, avoiding circular endpoint dependence. Dividing by the square root of the sum of squared kernel weights restores theoretical pointwise variance one. FWHM here denotes the smoothing-kernel convention used by spm1d's generator, not the observed FWHM estimate from each model's residuals. No curve is individually standardized.

Three variables, when present, have equicorrelation 0, 0.8, or 0.5 as specified. Cross-variable dependence is imposed on residual fields, before adding mean effects. Participants are independent. Independent factorial designs use different participants in every group × condition cell. Mixed designs have three observations per participant, with compound-symmetric condition correlation 0.5 under the reference model. A separate robustness scenario uses AR(1) correlation 0.8 across three conditions, violating sphericity.

ANCOVA uses two groups and two continuous covariates (`speed`, `age`). Speed has a group-dependent mean shift 0.8; age equals 0.35 × speed plus independent normal noise scaled by `sqrt(1-0.35²)`. The response contains a common smooth nuisance contribution `(0.6 × speed + 0.3 × age) × bump`, where `bump = exp(-0.5 × ((node-50)/15)²)`. The tested adjusted group coefficient is zero under the null. Covariate names are illustrative, not clinically calibrated measurements.

GLM tests the first predictor adjusted for the second: `[intercept, centered_speed, centered_age]`, contrast `[0,1,0]`. Its response contains the nuisance term `0.6 × age × bump`; the speed coefficient is zero. Both covariates have the same correlated construction without the ANCOVA group shift. Group labels in this generator do not enter the GLM: its total N is the sum of the two stated sample counts.

## Scenario inventory (38 scenarios)

For **each of the four designs**, eight configurations are run:

| Configuration | Sample counts | Kernel FWHM | Variables | Residual correlation | Null |
|---|---|---:|---:|---:|---|
| Reference | 30, 30 | 10 | 1 | 0 | Global |
| Small sample | 12, 12 | 10 | 1 | 0 | Global |
| Large sample | 60, 60 | 10 | 1 | 0 | Global |
| Less smooth | 30, 30 | 5 | 1 | 0 | Global |
| More smooth | 30, 30 | 20 | 1 | 0 | Global |
| Independent variable family | 30, 30 | 10 | 3 | 0 | Global |
| Correlated variable family | 30, 30 | 10 | 3 | 0.8 | Global |
| Partial-null family | 30, 30 | 10 | 3 | 0.5 | Partial |

For ANCOVA the counts are participants per group; for GLM they sum to total independent N; for independent ANOVA they are participants per cell in each group; for mixed ANOVA they are participants per group measured in all three conditions. Both factorial designs have two groups and three conditions.

The partial-null family adds `1.5 × bump` times the tested predictor/group indicator **only to variable 0**. For factorial models, only that variable's group main effect is nonnull: its condition and interaction hypotheses remain null. False-positive counts exclude the known nonnull hypothesis. Thus these runs probe selected partial-null configurations; they do not establish strong FWER control for every possible alternative.

Six additional configurations use the reference settings unless stated otherwise:

1. ANCOVA: unequal sample sizes 12 and 36 with equal variance (within supported assumptions).
2. ANCOVA: 12 and 36, residual SD tripled in the smaller group (variance ratio 9; violation).
3. ANCOVA: 12 and 36, residual SD tripled in the larger group (violation).
4. GLM: residual SD tripled where the tested predictor exceeds zero (violation).
5. Independent ANOVA: residual SD tripled in group 1 / condition 2 (balanced counts; variance violation).
6. Mixed ANOVA: AR(1) condition correlation 0.8 instead of compound symmetry (sphericity violation).

Unbalanced factorial designs are **not supported** by this application and are tested as rejected inputs, not as inferential simulations. Robustness scenarios deliberately set `equal_var=True` while generating violating data to measure sensitivity to incorrect assumptions; this does not authorize those analyses for users.

## Estimands and decisions

The primary endpoint is whether **any true-null statistic field crosses its inference threshold anywhere on the 101-node domain**. Record that event per true-null variable/effect and as its union over the requested family. This is not the fraction of significant nodes. The secondary endpoint is whether any true-null cluster survives the application's displayed adjusted-p criterion (`confirmed_clusters`). Count both so that cluster filtering cannot conceal liberal threshold crossings.

Every factorial run fits and evaluates group, condition and interaction. Let `m` be the number of variables and `e` equal 3 for factorial designs or 1 otherwise. Inference uses `alpha/(m × e)`; adjusted cluster probabilities use that same multiplicity. Test t fields bilaterally and F fields in the upper tail. The per-field reference level is `0.05/(m × e)`; the family reference level is 0.05. Under partial nulls, the correction still includes the full planned family, including nonnull hypotheses.

A rate below the reference level can represent conservative inference. Bonferroni is a mathematical multiplicity bound when its constituent tests are valid, including under dependence; it does not fix invalid constituent tests. These simulations evaluate its implementation and the combined procedure in specified scenarios, not a new proof of Bonferroni.

## Execution and checks

All replications call `gaitspm_engine.infer_model_fields` and `apply_field_correction`, the same production inference and multiplicity functions used by the app. This shared path avoids reproducing the implementation solely inside a validation script. To avoid repeatedly importing large canonical tables for every replication, array inputs are generated directly. The **first replication of each 100-replication chunk** also passes through the full `run_analysis` pipeline, including subject/covariate preparation, shuffled metadata, each effect, statistic fields, thresholds, rejection decisions and confirmed cluster endpoints/probabilities. At 5,000 replications this provides 50 full-pipeline checkpoints per scenario (1,900 overall). This is explicitly a production inference study with sampled end-to-end checks, not 190,000 complete UI workflows.

The generator, interval calculations, deterministic streams, null masks, covariance construction and end-to-end parity receive small deterministic tests. A short run is a harness check, not evidence of inferential validity. The existing concordance suite must pass after extracting the shared inference function.

Before the production run, write a frozen manifest containing scenario definitions, requested replication count, seed, environment, source hashes, vendored spm1d hash and UTC timestamp. Resume only with the identical plan and source hashes. Save raw per-replication binary decisions, warning counts and atomic chunk files. Exceptions fail the run; never discard failed replications or replace them with successful ones. A report requires exactly the requested replications for every scenario. Source changes require a new output directory and a new manifest.

```sh
python app/sync_html_engine.py
python tests/test_spm1d_validation.py
python research/monte_carlo/test_harness.py
python research/monte_carlo/monte_carlo.py --plan-only
python research/monte_carlo/monte_carlo.py --replicates 5000 --workers 6
```

The default output is `paper/monte_carlo_runs/`, excluded from the public repository. Use a separate output directory for pilots. Research results and figures remain local until publication is explicitly authorized; public code and this protocol permit reproduction.

## Uncertainty, interpretation and reporting

Report numerator, denominator, rate, Monte Carlo standard error and an exact two-sided 95% Clopper–Pearson interval for each event. At a true rate of 0.05 and N=5,000, Monte Carlo SE is about 0.00308; the normal approximation gives a 95% half-width of roughly 0.006. These are **marginal** intervals, not simultaneous confidence bands across the scenario inventory. Whether a single interval includes 0.05 is not a universal pass/fail test.

As an exploratory screen, calculate one-sided exact binomial tests for inflation and Holm-adjust them across primary family endpoints in the assumption-respecting scenarios. Clearly distinguish this exploratory screen from the descriptive intervals. Failure to detect inflation does not establish equivalence; no equivalence margin is specified. Report all scenarios, including conservative and adverse findings, with assumptions/violations separated. Unsupported inputs, errors, warnings and partial-null scope must remain visible.

Deliverables: frozen JSON manifest; compressed per-replication decisions; CSV summary; English report; familywise-error figure in PNG, SVG and PDF; source/output checksums. Unexpected inflation requires investigation and may justify narrower usage claims. Do not change thresholds or the scenario inventory after seeing results merely to achieve a desired conclusion.

## Sources

- Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. *Statistics in Medicine*. 2019;38:2074–2102. [doi:10.1002/sim.8086](https://doi.org/10.1002/sim.8086). The protocol follows the aim/data-generating mechanism/estimand/method/performance-measure structure and reports Monte Carlo uncertainty.
- [spm1d 0.4 statistical documentation](https://spm1d.org/doc/Stats1D/). The pinned source `vendor/spm1d/stats/t.py` documents the GLM's lack of non-sphericity correction; `vendor/spm1d/stats/anova/ui.py` documents factorial and approximate repeated-measures inference; `vendor/spm1d/rft1d/random.py` documents the Gaussian smoothing convention.

## Archived runs

Previously completed runs retain their original source snapshots and commit identifiers. Reorganizing this repository does not rewrite frozen manifests or results. Use a separate output directory for runs under this layout; a source-hash mismatch must not be bypassed to resume an older run.
