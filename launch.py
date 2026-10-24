"""Start the local browser application in an isolated Python environment."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import threading
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent
REQUIRED = {'numpy':'2.3.5','scipy':'1.17.0','pandas':'2.2.3','matplotlib':'3.10.8','openpyxl':'3.1.5'}

def check_dependencies(python):
    code = 'import importlib.metadata as m; r='+repr(REQUIRED)+'; assert all(m.version(k)==v for k,v in r.items())'
    return subprocess.run([str(python),'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--no-browser',action='store_true')
    p.add_argument('--port',type=int,default=4173)
    p.add_argument('--use-current',action='store_true',help='Use the active environment, without installing dependencies')
    p.add_argument('--check',action='store_true',help='Check active environment and exit without installing or starting')
    a=p.parse_args()
    if sys.version_info < (3,11):
        raise SystemExit('Instala Python 3.12 / Install Python 3.12, then run again.')
    if not 1<=a.port<=65535:raise SystemExit('Invalid port')
    if a.check:
        if not check_dependencies(sys.executable):raise SystemExit('Missing/different dependencies. Run launch.py for setup.')
        sys.path.insert(0,str(ROOT/'app'));import gaitspm_engine
        print('Ready: GaitSPM '+gaitspm_engine.VERSION+' / spm1d '+gaitspm_engine.spm1d.__version__)
        return
    python=Path(sys.executable)
    if not a.use_current:
        target=ROOT/'.venv'
        python=target/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        if not python.exists():
            print('Preparando entorno local / Preparing local environment...',flush=True)
            venv.EnvBuilder(with_pip=True).create(target)
        if not check_dependencies(python):
            print('Instalando dependencias. Esta primera instalación necesita internet.',flush=True)
            subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
        os.execv(str(python),[str(python),str(Path(__file__).resolve()),'--use-current','--port',str(a.port)]+(['--no-browser'] if a.no_browser else []))
    if not check_dependencies(python):raise SystemExit('Install requirements.txt in the active environment first.')
    sys.path.insert(0,str(ROOT/'app'))
    import serve
    try:server=serve.ThreadingHTTPServer(('127.0.0.1',a.port),serve.Handler)
    except OSError as exc:raise SystemExit(f'No se puede abrir el puerto {a.port}. Prueba --port 4175. {exc}')
    url=f'http://127.0.0.1:{a.port}'
    print('GaitSPM: '+url+'\nDeja esta ventana abierta. Ctrl+C para cerrar.',flush=True)
    if not a.no_browser:
        timer=threading.Timer(.6,webbrowser.open,args=(url,));timer.daemon=True;timer.start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close()
        for session in serve.SESSIONS.values():session['tmp'].cleanup()

if __name__=='__main__':main()
