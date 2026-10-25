# Software validation methodology

Run `python tests/test_spm1d_validation.py` after regenerating the shared engine with `python app/sync_html_engine.py`.

The deterministic synthetic fixtures exercise independent and paired tests, regression, one-way and repeated-measures ANOVA, numeric GLM, ANCOVA, and independent/mixed two-way ANOVA. Reference models are assembled independently and call spm1d directly. Assertions cover full statistic fields, critical thresholds, rejection decisions, cluster counts, endpoints and probabilities. Additional tests check rank, complete-case selection, repeated IDs, balance, correction across variables/effects, and the browser bridge.

Both paths use the bundled spm1d implementation. These checks validate data preparation and software integration; they do not independently prove spm1d algorithms or establish clinical validity. See the statistical-design guide for model assumptions and limitations.

CI runs software checks without publishing research reports. Manuscripts, external multi-dataset findings, figures and numerical report files are maintained outside this public software update.
