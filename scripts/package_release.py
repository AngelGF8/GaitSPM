"""Create one local v1.4.2 release archive. Never publishes or includes screenshots."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'GaitSPM_v1.4.2.zip'
EXCLUDED={'.git','__pycache__','node_modules','.venv','data_private','design-preview','original_demo','screenshots','design','audit','workbooks'}
EXCLUDED_FILES={'ui-fixtures.json','workbook_inputs.json','requirements-design.txt','build_design_assets.py','preview-server.mjs'}
def eligible(p):
    rel=p.relative_to(ROOT)
    return p.is_file() and not any(x in EXCLUDED for x in rel.parts) and p.name not in EXCLUDED_FILES and not p.name.endswith(('.pyc','.inspect.ndjson')) and p.name not in {'install.log','MANIFEST.sha256'}
def main():
    paths=sorted(p for p in ROOT.rglob('*') if eligible(p))
    manifest=ROOT/'MANIFEST.sha256'
    manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in paths), encoding="utf-8")
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths+[manifest]:z.write(p,'gaitspm/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        assert sum(n.endswith('.xlsx') for n in z.namelist())==8
        assert not any('/screenshots/' in n for n in z.namelist())
    print(json.dumps({'path':str(OUT),'bytes':OUT.stat().st_size,'files':len(paths)+1,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
