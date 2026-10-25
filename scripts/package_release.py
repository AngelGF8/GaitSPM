"""Build the user application ZIP; source and development tools stay on GitHub."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.search(r'^VERSION = "([^"]+)"', (ROOT/'app/gaitspm_app.py').read_text(encoding='utf-8'), re.M).group(1)
ROOT_FILES = ('launch.py', 'Iniciar_GaitSPM.bat', 'Iniciar_GaitSPM.command',
              'iniciar_gaitspm.sh', 'streamlit_app.py', 'requirements.txt',
              'requirements-streamlit.txt', 'requirements-lock.txt', 'LICENSE',
              'THIRD_PARTY_NOTICES.md', 'CITATION.cff', 'CHANGELOG.md', 'LEEME_PRIMERO.md')
USER_DOCS = ('guide.md', 'statistics.md', 'faq.md', 'GUIA_EJEMPLOS.md',
             'publication.md', 'validation-guide.md')


def package_files(root=ROOT):
    """Explicit public runtime roots; never collect arbitrary local project files."""
    files = [root/name for name in ROOT_FILES]
    files += [root/'docs'/name for name in USER_DOCS]
    for folder in ('app', 'vendor', 'datasets/synthetic', 'docs/licenses'):
        files.extend(p for p in (root/folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.name != '.DS_Store'
                     and not p.name.endswith(('.pyc', '.pyo', '.log')))
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise FileNotFoundError('Missing runtime files: '+', '.join(missing))
    return sorted(set(files))


def build(output_dir, manifest_only=False):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in package_files()}
    payload['README.md'] = (f'''# GaitSPM {VERSION}

This archive contains the application, synthetic examples and user documentation.
Install Python 3.12, then launch with `python launch.py`, or use the supplied
Windows/macOS/Linux launcher. First setup installs the pinned dependencies.

Start with LEEME_PRIMERO.md (Spanish) or docs/guide.md (English).
The complete source, tests and contribution instructions for this version are
available at https://github.com/AngelGF8/GaitSPM . This user ZIP excludes developer
outputs, historical audits and research manuscripts. The application and bundled
libraries retain their licences and source files.

Verify the included file checksums against MANIFEST.sha256 after extraction.
''').encode('utf-8')
    manifest = ''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n'
                       for name, data in sorted(payload.items()))
    (output_dir/'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
    if manifest_only:
        return output_dir/'MANIFEST.sha256'
    archive = output_dir/f'GaitSPM_v{VERSION}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo('gaitspm/'+name)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if name in ('iniciar_gaitspm.sh', 'Iniciar_GaitSPM.command') else 0o644
            info.external_attr = (0o100000 | mode) << 16
            z.writestr(info, data)
        z.writestr('gaitspm/MANIFEST.sha256', manifest)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'dist')
    parser.add_argument('--manifest-only', action='store_true')
    args = parser.parse_args()
    output = build(args.output_dir, args.manifest_only)
    print(json.dumps({'path': str(output), 'bytes': output.stat().st_size,
                      'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
