# GaitSPM

GaitSPM turns participant-level gait curves into SPM1D analyses using the upstream spm1d engine. Use the local launcher for the verified native workflow.

[Open browser application](app/index.html) · [Clinical guide](guide.md) · [Software validation](validation-guide.md)

The browser application becomes available here after the Pages workflow is deployed. It downloads Pyodide dependencies on first use; uploaded data are processed in your browser. Native local mode works offline after installation. A hosted Streamlit deployment would process uploads on its server.

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
