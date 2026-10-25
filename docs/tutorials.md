# Reproducible tutorials

## Synthetic group difference

Load the FAIS example, keep the two independent groups, select a variable and run Welch t. Export the figure and result table. These simulated curves illustrate a workflow; they are not evidence about FAIS patients.

## Synthetic group by condition

Load example 07 (fatigue and recovery). In Laboratory mode choose mixed ANOVA, both groups and the three conditions, parametric inference and the interaction effect. Each group has 30 participants with repeated measurements. Alpha is divided across the three factorial effects and, when selected, across variables. Review the sphericity and approximate-residual warnings.

## Adjusting for a covariate

Load an example, choose ANCOVA and the two groups, select one condition and the `technical_score` covariate. This score is random and has no clinical meaning. For a scientific study use a measured covariate such as walking speed, its documented units and a prespecified adjustment rationale. Do not rename technical_score to speed.

## Public real curves

The MovementRx adaptation is in `tests/fixtures/movementrx/`. Run:

```sh
python scripts/prepare_external_csv.py
python tests/test_external_upload.py
```

The test groups are arbitrary software-test partitions, not clinical populations. All original angle values are preserved. The external CSV import workflow is a software check; research comparisons are maintained separately.

## Open dataset follow-up

Fukuchi running data and Schreiber–Moissenet walking data are candidates for additional tutorials. A one-click clinical tutorial requires a pinned original release, verified licence, participant/condition dictionary, preprocessing provenance and expected output. Until that adapter is implemented and validated, these are planned tutorials rather than downloadable GaitSPM examples.
