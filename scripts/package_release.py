"""Create a versioned local source archive or refresh its manifest. Never publishes."""
from pathlib import Path
import argparse,hashlib,json,re,zipfile
ROOT=Path(__file__).resolve().parents[1]
VERSION=re.search(r'^VERSION = "([^"]+)"', (ROOT/'app/gaitspm_app.py').read_text(encoding='utf-8'), re.M).group(1)
OUT=ROOT.parent/f'GaitSPM_v{VERSION}.zip'
EXCLUDED={'.git','__pycache__','node_modules','.venv','data_private','design-preview','original_demo','screenshots','design','audit','workbooks','site','paper','public_validation'}
EXCLUDED_FILES={'ui-fixtures.json','workbook_inputs.json','requirements-design.txt','build_design_assets.py','preview-server.mjs','test_public_validation.py','IMPLEMENTATION_STATUS.md','audit-v1.4.2-original-manifest.sha256'}
def eligible(p):
    rel=p.relative_to(ROOT)
    return not rel.as_posix().startswith('docs/validation/') and p.is_file() and not any(x in EXCLUDED for x in rel.parts) and p.name not in EXCLUDED_FILES and not p.name.endswith(('.pyc','.inspect.ndjson')) and p.name not in {'install.log','MANIFEST.sha256','.DS_Store'}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest-only',action='store_true')
    args=parser.parse_args()
    paths=sorted(p for p in ROOT.rglob('*') if eligible(p))
    manifest=ROOT/'MANIFEST.sha256'
    manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in paths), encoding="utf-8")
    if args.manifest_only:
        print(f'Manifest: {len(paths)} files, GaitSPM {VERSION}')
        return
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths+[manifest]:z.write(p,'gaitspm/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        assert sum(n.endswith('.xlsx') for n in z.namelist())==8
        assert not any('/screenshots/' in n for n in z.namelist())
    print(json.dumps({'path':str(OUT),'bytes':OUT.stat().st_size,'files':len(paths)+1,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
