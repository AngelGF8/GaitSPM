# Changelog

## Unreleased

### Added

- Two-group ANCOVA with multiple numeric covariates and subject-aligned complete cases.
- Numeric-predictor GLM with explicit t contrast, rank and contrast validation.
- Balanced independent and mixed group × condition ANOVA, selectable effects and Bonferroni protection across the three effects.
- Laboratory and Streamlit controls for the new designs.
- Reproducible synthetic spm1d concordance suite.
- MkDocs Material documentation, Pages build workflow, contribution guidance and publication guidance.

### Limits

- New models require parametric inference and equal variance. Factorial designs require balance; mixed designs assume sphericity and can use approximate residuals in spm1d.
- ANCOVA covers two groups with common covariate slopes; the generic GLM exposes t contrasts on numeric predictors, not arbitrary categorical/mixed models.
- Hosted deployment, a Zenodo DOI and journal acceptance are separate external steps.

## 1.4.2 — 2026-10-24

- Explicit UTF-8 source handling and launcher tests.
- Linux, Windows and macOS CI configuration using Python 3.12.

## 1.4.1

- External MovementRx import and export checks; historical audit in `audit-v1.4.1/`.
