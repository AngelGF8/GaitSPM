"""Build the native engine and self-contained HTML from reviewable sources."""
from pathlib import Path
import base64, json, zlib
ROOT = Path(__file__).resolve().parent
MARKER = '# ----------------------------------------------------------------------------\n# Streamlit interface'

def main():
    s = (ROOT / 'gaitspm_app.py').read_text(encoding='utf-8')
    engine = s.split(MARKER, 1)[0].rstrip() + '\n'
    engine = engine.replace('import streamlit as st\n', '').replace('@st.cache_data(show_spinner=False)\n', '')
    (ROOT / 'gaitspm_engine.py').write_text(engine, encoding="utf-8")
    h = (ROOT / 'web/template.html').read_text(encoding="utf-8").replace('/*LAB_CSS*/', (ROOT / 'web/laboratory.css').read_text(encoding="utf-8")+'\n'+(ROOT/'web/guided.css').read_text(encoding="utf-8"))
    bundled = {}
    for item in json.loads((ROOT.parent / 'datasets/synthetic/catalog.json').read_text(encoding='utf-8')):
        if item.get('source_kind') == 'bundled_csv':
            key = item['key']
            data = (ROOT.parent / 'datasets/synthetic' / key / (key + '.csv')).read_bytes()
            bundled[key] = base64.b64encode(zlib.compress(data, 9)).decode('ascii')
    simulation = (ROOT / 'simulation.py').read_text(encoding='utf-8').replace(
        'BUNDLED_EXAMPLE_CSV = {}', 'BUNDLED_EXAMPLE_CSV = ' + repr(bundled))
    for name, source in [('py-engine', engine), ('py-simulation', simulation), ('py-bridge', (ROOT / 'bridge.py').read_text(encoding="utf-8"))]:
        h += '<script type="text/x-python" id="' + name + '">\n' + source + '\n</script>\n'
    h += (ROOT / 'web/vendor-scripts.html').read_text(encoding="utf-8")
    h += '<script>\n' + (ROOT / 'web/ui-core.js').read_text(encoding="utf-8") + '\n' + (ROOT / 'web/laboratory.js').read_text(encoding="utf-8") + '\n'+(ROOT/'web/guided.js').read_text(encoding="utf-8")+'\nboot();\n</script></body></html>'
    (ROOT / 'gaitspm.html').write_text(h, encoding='utf-8')
    print('Built gaitspm_engine.py and gaitspm.html from shared sources')

if __name__ == '__main__':
    main()
