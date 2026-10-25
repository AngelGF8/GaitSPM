"""Encode existing, unaltered UI screenshots as an animated walkthrough.
This is a slideshow of historical synthetic-example screenshots, not a recording
of the new models. Requires Pillow (already installed with Matplotlib).
"""
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
names = ['02_ejemplo_cargado.png', '03_control_calidad_mapeo.png',
         '04_configuracion_analisis.png', '06_resultados_figura_spm.png']
frames = []
for name in names:
    with Image.open(ROOT / 'capturas' / name) as source:
        frame = source.convert('RGB')
        frame.thumbnail((1024, 576), Image.Resampling.LANCZOS)
        frames.append(frame)
out = ROOT / 'docs/assets/workflow.gif'
out.parent.mkdir(parents=True, exist_ok=True)
frames[0].save(out, save_all=True, append_images=frames[1:], duration=2200, loop=0)
print(out)
