"""Exercise the real launcher, optionally including a fresh .venv installation.

No browser is opened. This checks startup and HTTP serving, not visual rendering.
Set GAITSPM_TEST_BOOTSTRAP=1 only in a clean checkout without an existing .venv.
"""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def test_launcher_serves_html_and_creates_analysis_session(self):
        bootstrap = os.environ.get('GAITSPM_TEST_BOOTSTRAP') == '1'
        if bootstrap:
            self.assertFalse((ROOT / '.venv').exists(), 'Bootstrap requires a clean checkout')
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        command = [sys.executable, str(ROOT / 'launch.py'), '--no-browser', '--port', str(port)]
        if not bootstrap:
            command.append('--use-current')
        options = ({'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
                   if os.name == 'nt' else {'start_new_session': True})
        with tempfile.TemporaryDirectory(prefix='gait-launch-test-') as directory:
            log_path = Path(directory) / 'startup.log'
            with log_path.open('wb') as log:
                process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log, **options)
                try:
                    deadline = time.monotonic() + (300 if bootstrap else 60)
                    while True:
                        try:
                            with urllib.request.urlopen(base + '/api/ping', timeout=2) as response:
                                self.assertEqual(json.load(response), {'ok': True, 'mode': 'native'})
                            break
                        except (urllib.error.URLError, TimeoutError):
                            if time.monotonic() >= deadline or process.poll() not in (None, 0):
                                self.fail('Launcher did not become ready:\n' + log_path.read_text(encoding='utf-8', errors='replace'))
                            time.sleep(0.2)
                    with urllib.request.urlopen(base, timeout=10) as response:
                        self.assertEqual(response.read(), (ROOT / 'app/gaitspm.html').read_bytes())
                    request = urllib.request.Request(
                        base + '/api/call', json.dumps({'name': 'js_load_synthetic', 'args': ['01_fai']}).encode('utf-8'),
                        headers={'Content-Type': 'application/json', 'Origin': base,
                                 'X-GaitSPM-Session': 'LauncherCrossPlatformTest'})
                    with urllib.request.urlopen(request, timeout=30) as response:
                        result = json.load(response)
                    self.assertTrue(result['ok'], result)
                    self.assertEqual(result['n_subj'], 60)
                    if bootstrap:
                        python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
                        self.assertTrue(python.is_file())
                        subprocess.run([str(python), str(ROOT / 'launch.py'), '--check'], cwd=ROOT, check=True)
                finally:
                    if os.name == 'nt':
                        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                    else:
                        try:
                            os.killpg(process.pid, signal.SIGINT)
                        except ProcessLookupError:
                            pass
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        if os.name == 'nt':
                            process.kill()
                        else:
                            os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
