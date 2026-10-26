# Changelog

## Unreleased

### Added

- Cerebral palsy crouch-gait teaching example: original CSV/Excel, 60 synthetic participants and 12 variables, available locally and bundled in the browser app.

- Two-group ANCOVA with multiple numeric covariates and subject-aligned complete cases.
- Numeric-predictor GLM with explicit t contrast, rank and contrast validation.
- Balanced independent and mixed group × condition ANOVA, selectable effects and Bonferroni protection across the three effects.
- Laboratory and Streamlit controls for the new designs.
- Reproducible synthetic spm1d concordance suite.
- MkDocs Material documentation, Pages build workflow, contribution guidance and publication guidance.

### Repository maintenance

- Removed historical logs, audit outputs, duplicated English README and internal outreach drafts from the public tree.
- Test outputs now use ignored `.test-output/`; application ZIPs contain runtime code, examples and user documentation, with a per-release checksum manifest.

### Limits

- New models require parametric inference and equal variance. Factorial designs require balance; mixed designs assume sphericity and can use approximate residuals in spm1d.
- ANCOVA covers two groups with common covariate slopes; the generic GLM exposes t contrasts on numeric predictors, not arbitrary categorical/mixed models.
- Hosted deployment, a Zenodo DOI and journal acceptance are separate external steps.

## 1.4.2 — 2026-10-24

- Explicit UTF-8 source handling and launcher tests.
- Linux, Windows and macOS CI configuration using Python 3.12.

## 1.4.1

- External MovementRx import and export checks. Historical audit files remain in Git history.
