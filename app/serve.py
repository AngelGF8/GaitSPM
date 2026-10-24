"""GaitSPM local server: the browser UI and Streamlit use the same Python engine.
Run: python app/serve.py --port 4173. No runtime download in local mode.
"""
import argparse
import json
import secrets
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import gaitspm_engine as engine
from simulation import synthetic_catalog

ROOT = Path(__file__).resolve().parent
SESSIONS = {}
LOCK = threading.RLock()
MAX_BODY = 50 * 1024 * 1024


def get_session(token):
    if not token or len(token) > 100 or not all(c.isalnum() or c == '-' for c in token):
        raise ValueError('Missing or invalid session token')
    now = time.monotonic()
    for k in list(SESSIONS):
        if now - SESSIONS[k]['time'] > 3600:
            SESSIONS.pop(k)['tmp'].cleanup()
    if token not in SESSIONS:
        if len(SESSIONS) >= 24:
            raise ValueError('Too many active sessions')
        ns = dict(engine.__dict__)
        exec((ROOT / 'simulation.py').read_text(encoding="utf-8"), ns)
        exec((ROOT / 'bridge.py').read_text(encoding="utf-8"), ns)
        tmp = tempfile.TemporaryDirectory(prefix='gaitspm-')
        ns['UPLOAD_PATH'] = str(Path(tmp.name) / 'upload.bin')
        SESSIONS[token] = {'ns': ns, 'tmp': tmp, 'time': now}
    SESSIONS[token]['time'] = now
    return SESSIONS[token]['ns']


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Patient values and uploaded filenames never enter HTTP logs.

    def send(self, status, data, mime='application/json'):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def same_origin(self):
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        hostname = urlsplit('http://' + host).hostname
        return hostname in {'127.0.0.1', 'localhost', 'terminal.local', '::1'} and (
            not origin or urlsplit(origin).netloc == host)

    def do_GET(self):
        if not self.same_origin():
            return self.send(403, '{"ok":false,"error":"Origin rejected"}')
        path = urlsplit(self.path).path
        if path == '/api/ping':
            return self.send(200, '{"ok":true,"mode":"native"}')
        if path in ('/', '/gaitspm.html'):
            return self.send(200, (ROOT / 'gaitspm.html').read_bytes(), 'text/html; charset=utf-8')
        if path.startswith('/examples/'):
            filename=path.removeprefix('/examples/')
            allowed={d['key']+ext:(d['key'],ext) for d in synthetic_catalog() for ext in ('.csv','.xlsx')}
            if filename in allowed:
                key,ext=allowed[filename]
                target=ROOT.parent/'datasets/synthetic'/key/filename
                if target.is_file():
                    return self.send(200,target.read_bytes(),'text/csv; charset=utf-8' if ext=='.csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            return self.send(404,'{"ok":false,"error":"Example file not found"}')
        if path == '/favicon.ico':
            return self.send(204, b'', 'image/x-icon')
        self.send(404, '{"ok":false,"error":"Not found"}')

    def do_POST(self):
        if not self.same_origin():
            return self.send(403, '{"ok":false,"error":"Origin rejected"}')
        try:
            n = int(self.headers.get('Content-Length', '0'))
            if not 0 < n <= MAX_BODY:
                return self.send(413, '{"ok":false,"error":"Maximum upload: 50 MB"}')
            data = self.rfile.read(n)
            with LOCK:  # Matplotlib and spm1d's random state are process globals.
                ns = get_session(self.headers.get('X-GaitSPM-Session'))
                if self.path == '/api/upload':
                    ns['STATE'].clear()
                    Path(ns['UPLOAD_PATH']).write_bytes(data)
                    return self.send(200, '{"ok":true}')
                if self.path != '/api/call':
                    return self.send(404, '{"ok":false,"error":"Not found"}')
                req = json.loads(data)
                name = req.get('name', '')
                if not name.startswith('js_') or name not in ns or not callable(ns[name]):
                    raise ValueError('Unknown operation')
                args = req.get('args', [])
                if not isinstance(args, list) or len(args) > 8:
                    raise ValueError('Invalid arguments')
                result = ns[name](*args)
                self.send(200, result)
        except Exception as exc:
            self.send(400, json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=4173)
    p.add_argument('--preview', action='store_true', help='Bind all interfaces for supervised development preview')
    a = p.parse_args()
    http = ThreadingHTTPServer(('0.0.0.0' if a.preview else '127.0.0.1', a.port), Handler)
    print(f'GaitSPM {engine.VERSION}: http://127.0.0.1:{a.port}', flush=True)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http.server_close()
        for session in SESSIONS.values():
            session['tmp'].cleanup()
