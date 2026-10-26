# Changelog

## Unreleased

### Repository layout

- Grouped project documentation, configuration, screenshots and research tools into dedicated subdirectories. Research simulations are no longer promoted on the homepage or documentation navigation. Launchers and the Spanish installation guide remain compatible.

### Added

- Reproducible 38-scenario Monte Carlo protocol and runner for adjusted/factorial inference and multiplicity; research results remain separate from public software checks.
- Shared production inference entry point with sampled end-to-end checks in the simulation harness.

### Clarified

- Numerical concordance with spm1d 0.4.53 does not establish general Type I error control or clinical validity. Variance and sphericity violations are evaluated separately from supported assumptions.
- spm1d remains pinned to bundled 0.4.53; evaluation of 0.5 is deferred until supplied by the upstream author.

### Previously added in this development cycle

- Cerebral palsy crouch-gait teaching example: original CSV/Excel, 60 synthetic participants and 12 variables, available locally and bundled in the browser app.

- Two-group ANCOVA with multiple numeric covariates and subject-aligned complete cases.
- Numeric-predictor GLM with explicit t contrast, rank and contrast validation.
- Balanced independent and mixed group × condition ANOVA, selectable effects and Bonferroni adjustment across the three effects.
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
