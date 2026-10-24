"""Preserve the exact installed dependency notices in the HTML vendor archives."""
import base64,io,re,sys,zipfile,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];packages=Path(sys.argv[1])
vendor=root/'app/web/vendor-scripts.html';html=vendor.read_text(encoding="utf-8")
notices=root/'docs/licenses';notices.mkdir(exist_ok=True)
for package,files,script in [
    ('spm1d-0.4.53.dist-info',['licenses/LICENSE.txt','METADATA'],'spm1d-zip'),
    ('openpyxl-3.1.5.dist-info',['LICENCE.rst','METADATA'],'xlsx-zip'),
    ('et_xmlfile-2.0.0.dist-info',['LICENCE.rst','LICENCE.python','AUTHORS.txt','METADATA'],'xlsx-zip')]:
    match=re.search(r'(<script[^>]*id="'+script+r'"[^>]*>)(.*?)(</script>)',html,re.S)
    old=zipfile.ZipFile(io.BytesIO(base64.b64decode(match[2])));buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for name in old.namelist():z.writestr(name,old.read(name))
        for name in files:
            p=packages/package/name;arc=package+'/'+name
            if arc not in old.namelist():z.writestr(arc,p.read_bytes())
            if name!='METADATA':shutil.copy2(p,notices/(package+'_'+Path(name).name))
    html=html[:match.start(2)]+base64.b64encode(buf.getvalue()).decode()+html[match.end(2):]
vendor.write_text(html,encoding='utf-8')
print('GPLv3 and MIT/Python notices preserved verbatim')
