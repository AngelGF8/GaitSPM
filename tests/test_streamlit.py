"""Widget-driven smoke test of all tabs, language and appearance reruns."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from streamlit.testing.v1 import AppTest

at=AppTest.from_file(str(ROOT/'app/gaitspm_app.py'),default_timeout=90).run()
assert not at.exception,at.exception
at.selectbox(key='scenario').select('03_hip_oa').run()
at.button(key='load_synthetic').click().run()
assert not at.exception,at.exception
at.button(key='run').click().run()
assert not at.exception,at.exception
assert not at.error,[e.value for e in at.error]
before={k:v['z'].copy() for k,v in at.session_state['results'].items()}
at.radio(key='ui_language').set_value('en').run()
assert not at.exception,at.exception
assert any(x.label=='Methods' for x in at.text_area)
for widget in at.checkbox:
    if widget.label=='Cluster bars (%)':widget.check().run();break
assert not at.exception,at.exception
import numpy as np
for k,v in before.items():np.testing.assert_array_equal(v,at.session_state['results'][k]['z'])
assert at.session_state['cfg']['show_cluster_bars']
print('PASS: boot -> synthetic HOA -> 3-variable inference -> all tabs -> EN -> cluster bars; inference unchanged.')
