"""Freeze the dependency closure of the actually tested environment (Python 3.12)."""
from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root=Path(__file__).resolve().parents[1]
todo=['numpy','scipy','pandas','matplotlib','openpyxl'];pins={};missing=set()
while todo:
    name=canonicalize_name(todo.pop())
    if name in pins or name in missing:continue
    try:d=distribution(name)
    except PackageNotFoundError:
        missing.add(name);continue
    pins[name]=d.version
    for raw in d.requires or []:
        r=Requirement(raw)
        if r.marker is None or r.marker.evaluate({'extra':''}):todo.append(r.name)
if missing:
    raise SystemExit('Install missing declared dependencies before freezing: '+', '.join(sorted(missing)))
text='# Tested Python 3.12 Linux dependency closure; platform-specific extras may differ.\n'
text+='\n'.join(f'{n}=={v}' for n,v in sorted(pins.items()))+'\n'
(root/'config/requirements/lock.txt').write_text(text,encoding='utf-8')
print(f'Frozen {len(pins)} tested dependencies')
