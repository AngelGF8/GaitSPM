# Reproducir comprobaciones

Python 3.12: instala `requirements.txt`; spm1d está incluido en `vendor/`.

Desde la raíz:

```sh
python app/sync_html_engine.py
python -m unittest discover -s tests -p test_audit.py -v
python tests/test_bridge.py
python tests/test_release.py
python tests/test_external_upload.py
npm install
npm run test:ui
```

`test_release.py` genera fixtures con resultados reales para `test_ui.cjs`. La prueba DOM usa jsdom y un puente simulado con esas salidas; no abre navegador ni verifica píxeles. Los tests Python validan por separado estadísticas, importación y puente real.

`test_browser.cjs` es una comprobación opcional Playwright preparada para un entorno con Chromium. No se ejecutó satisfactoriamente en esta revisión. `test_streamlit.py` y `run_matrix.py` son utilidades heredadas, no evidencia de pruebas 1.4; Streamlit requiere requisitos opcionales. Los resultados de la versión actual se documentan en audit-v1.4/INFORME.md.

Prueba externa: tests/fixtures/movementrx/README.md. Informe adicional: audit-v1.4.1/INFORME.md.
