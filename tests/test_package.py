"""Exercise the actual user ZIP: checksums, examples, exclusions and extracted startup."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class UserPackageTests(unittest.TestCase):
    def test_archive_is_complete_and_excludes_development_and_research(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            subprocess.run([sys.executable, str(ROOT/'scripts/package_release.py'),
                            '--output-dir', str(out)], check=True, capture_output=True)
            archive = next(out.glob('GaitSPM_v*.zip'))
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                for name in names:
                    self.assertFalse(any(part in {'tests','scripts','paper','outreach', '.github',
                        '.test-output','node_modules','.venv','capturas','research','.local'} or part.startswith('audit')
                        for part in Path(name).parts), name)
                    self.assertNotIn('docs/validation/',name)
                self.assertIn('gaitspm/docs/licenses/THIRD_PARTY_NOTICES.md', names)
                self.assertIn('gaitspm/docs/project/changelog.md', names)
                self.assertIn('gaitspm/config/requirements/lock.txt', names)
                lines=z.read('gaitspm/MANIFEST.sha256').decode('utf-8').splitlines()
                self.assertEqual(len(lines),len(names)-1)
                for line in lines:
                    digest,name=line.split('  ',1)
                    self.assertEqual(hashlib.sha256(z.read('gaitspm/'+name)).hexdigest(),digest)
                self.assertTrue(z.getinfo('gaitspm/Iniciar_GaitSPM.command').external_attr >> 16 & 0o111)
                for folder in (ROOT/'datasets/synthetic').iterdir():
                    if not folder.is_dir():continue
                    for suffix in ('.csv','.xlsx'):
                        filename=f'datasets/synthetic/{folder.name}/{folder.name}{suffix}'
                        self.assertEqual(z.read('gaitspm/'+filename),(ROOT/filename).read_bytes())
                z.extractall(out/'extracted')
            launch=out/'extracted/gaitspm/launch.py'
            result=subprocess.run([sys.executable,str(launch),'--check'],capture_output=True,text=True,check=True)
            self.assertIn('Ready: GaitSPM',result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
