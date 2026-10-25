"""Build docs and include the self-contained Pyodide app in one Pages artifact."""
from pathlib import Path
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
# Stage the app before MkDocs resolves links, then remove only our temporary copy.
target = ROOT / 'docs/app'
if target.exists():
    raise SystemExit('docs/app already exists; refusing to overwrite it')
try:
    target.mkdir()
    shutil.copy2(ROOT / 'app/gaitspm.html', target / 'index.html')
    subprocess.run([sys.executable, '-m', 'mkdocs', 'build', '--strict'], cwd=ROOT, check=True)
finally:
    shutil.rmtree(target)
