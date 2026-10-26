# Numerical concordance with spm1d 0.4.53

Run `python tests/test_spm1d_validation.py` after regenerating the shared engine with `python app/sync_html_engine.py`.

The deterministic synthetic fixtures exercise independent and paired tests, regression, one-way and repeated-measures ANOVA, numeric GLM, ANCOVA, and independent/mixed two-way ANOVA. Reference models are assembled independently and call spm1d directly. Assertions cover full statistic fields, critical thresholds, rejection decisions, cluster counts, endpoints and probabilities. Additional tests check rank, complete-case selection, repeated IDs, balance, correction across variables/effects, and the browser bridge.

Both paths use the bundled spm1d implementation. These checks establish numerical concordance for the tested configurations and check data preparation and software integration. They do **not** establish Type I error control across all supported designs or data distributions, independently validate the underlying statistical algorithms, or establish clinical validity. A shared inferential implementation can agree exactly while producing inappropriate false-positive rates when its assumptions fail. See the statistical-design guide for model assumptions and limitations.

CI runs software checks without publishing research reports. Manuscripts, external multi-dataset findings, figures and numerical report files are maintained outside this public software update.

## Further methodological work

Research protocols and reproducibility tools are organized separately in the repository’s [research directory](https://github.com/AngelGF8/GaitSPM/tree/main/research). They are not part of the user application or a claim of general statistical validity. Research results remain separate from public software checks.

The bundled dependency remains spm1d **0.4.53**. No evaluation or migration to 0.5 is included.
