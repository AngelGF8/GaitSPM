# Reproduce the checks

Use Python 3.12 and install `requirements.txt`; spm1d is included in `vendor/`.

Run from the repository root:

```sh
python app/sync_html_engine.py
python -m unittest discover -s tests -p test_audit.py -v
python tests/test_bridge.py
python tests/test_release.py
python tests/test_external_upload.py
npm install
npm run test:ui
```

`test_release.py` generates fixtures with real analysis results in `.test-output/` for `test_ui.cjs`. The DOM test uses jsdom and a mock bridge returning those results; it does not open a browser or verify pixels. Python tests separately validate statistics, import and the real bridge.

`test_browser.cjs` is an optional Playwright check requiring Chromium. `test_streamlit.py` and `run_matrix.py` are legacy utilities, not evidence of version 1.4 validation; Streamlit requires optional dependencies. Regenerable outputs are stored in `.test-output/`, which is excluded from Git.

See [the external CSV fixture](fixtures/movementrx/README.md) for its provenance and reproduction steps.

## Launcher and platform checks

`python tests/test_launcher.py` starts the real launcher with the current dependencies, verifies the served HTML bytes and loads a 60-participant example through HTTP. It does not open or test a browser. In a clean checkout only, `GAITSPM_TEST_BOOTSTRAP=1` exercises installation into a newly created `.venv`. CI runs this and the existing tests on Linux, Windows and macOS with Python 3.12. Source generation runs with EncodingWarnings treated as errors.


## Unreleased model concordance

```sh
python tests/test_spm1d_validation.py
```

This suite covers deterministic synthetic designs, rank/missing-data guards, factorial multiplicity and the browser bridge. CI runs these checks without uploading numerical reports. Research manuscripts and external multi-dataset results are maintained separately.
