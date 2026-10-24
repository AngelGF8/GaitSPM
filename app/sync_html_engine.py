"""Build the native engine and self-contained HTML from reviewable sources."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent
MARKER = '# ----------------------------------------------------------------------------\n# Interfaz Streamlit'

def main():
    s = (ROOT / 'gaitspm_app.py').read_text(encoding='utf-8')
    engine = s.split(MARKER, 1)[0].rstrip() + '\n'
    engine = engine.replace('import streamlit as st\n', '').replace('@st.cache_data(show_spinner=False)\n', '')
    (ROOT / 'gaitspm_engine.py').write_text(engine)
    h = (ROOT / 'web/template.html').read_text().replace('/*LAB_CSS*/', (ROOT / 'web/laboratory.css').read_text()+'\n'+(ROOT/'web/guided.css').read_text())
    for name, source in [('py-engine', engine), ('py-simulation', (ROOT / 'simulation.py').read_text()), ('py-bridge', (ROOT / 'bridge.py').read_text())]:
        h += '<script type="text/x-python" id="' + name + '">\n' + source + '\n</script>\n'
    h += (ROOT / 'web/vendor-scripts.html').read_text()
    h += '<script>\n' + (ROOT / 'web/ui-core.js').read_text() + '\n' + (ROOT / 'web/laboratory.js').read_text() + '\n'+(ROOT/'web/guided.js').read_text()+'\nboot();\n</script></body></html>'
    (ROOT / 'gaitspm.html').write_text(h, encoding='utf-8')
    print('Built gaitspm_engine.py and gaitspm.html from shared sources')

if __name__ == '__main__':
    main()
