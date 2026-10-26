# GaitSPM

GaitSPM turns participant-level gait curves into SPM1D analyses using the upstream spm1d engine. Use the local launcher for the verified native workflow.

[Open browser application](app/index.html) · [Clinical guide](guide.md) · [Numerical concordance](validation-guide.md)

The browser application is hosted on GitHub Pages. It downloads Pyodide dependencies on first use; uploaded data are processed in your browser. Native local mode works offline after installation. A hosted Streamlit deployment would process uploads on its server.

## Cite GaitSPM

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23636819.svg)](https://doi.org/10.5281/zenodo.23636819)

González de la Flor, Á. (2026). *GaitSPM: graphical kinematic SPM1D analysis 1.5.0*. Zenodo. [10.5281/zenodo.23636819](https://doi.org/10.5281/zenodo.23636819).

The record is labelled **1.5.0** and archives commit `c11160f`, whose source version is **1.5.0.dev0**. It is a development snapshot, not a separately tagged stable release. Cite the spm1d methods separately.

## Quick start

```sh
python3 launch.py
```

Load an example, inspect subject IDs, choose the design and review the exported figure and results. Examples are synthetic unless explicitly identified as public external data.

## Development

```sh
python -m pip install -r requirements.txt
python app/sync_html_engine.py
python tests/test_spm1d_validation.py
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

The canonical engine source is `app/gaitspm_app.py`. Regenerate the native engine and HTML after changing it. The supported verification environment is Python 3.12 with the pinned native dependencies.
