# Contributing

Use GitHub issues for reproducible bugs and feature proposals. Include the version, OS, design, anonymised or synthetic input, expected result and minimal reproduction. Never upload identifiable participant data.

Edit `app/gaitspm_app.py`, then run `python app/sync_html_engine.py`. Do not edit the generated engine or HTML directly. UI sources live in `app/web/`. Keep subject IDs, complete-case selection and correction semantics explicit.

Before a pull request:

```sh
python tests/test_spm1d_validation.py
python -m unittest discover -s tests -p test_audit.py
python tests/test_bridge.py
python tests/test_release.py
python tests/test_external_upload.py
npm ci
npm run test:ui
```

Describe the scientific behaviour changed, limitations and test results. Statistical changes need a direct upstream comparison of fields, thresholds and clusters, including p-values. Numerical agreement alone does not justify a new model's assumptions.

Good first issue candidates: improve bilingual help text; reproduce a documented tutorial on another platform; add a licensed external CSV fixture with explicit provenance; document a common import error. Maintainer review is required before merge. The maintainer currently handles releases and statistical review; there is no promised response SLA.

## Repository language

Write documentation, contributor instructions and code comments in English. The default application language is English. Preserve optional Spanish interface translations, locale-specific import fixtures, original third-party material and author names. `LEEME_PRIMERO.md` is the existing Spanish installation guide; keep it unchanged. Its legacy launcher filenames remain supported for compatibility. Research manuscripts and private validation results are not published with repository updates.
