"""Tableau de bord temps réel : serveur local, uniquement 127.0.0.1.

Il diffuse en direct (Server-Sent Events) les contrôles du moteur existant et
sert le tableau de bord Senthora (`render_dashboard`).
"""
import json
import os
import secrets
import stat
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__, progress
from .checker import check_exercise
from .dashboard import render_dashboard, write_dashboard
from .dashboard_insights import parse_diff, parse_norm, stage_of
from .exercise_catalog import ALL_EXERCISES, EXERCISES, canonical_exercise
from .history import HistoryError, read_history, store_attempt

MAX_SOURCE = 262144
MAX_SOURCE_FILES = 12
MAX_BODY = 8192
STAGES = ('files', 'build', 'tests', 'norm')


def read_sources(folder, exercise):
    """Lit les sources à afficher (lecture seule, sans lien symbolique)."""
    spec = ALL_EXERCISES[exercise]
    names = []
    try:
        if 'project' in spec or spec.get('piscine') in ('cpp', 'py'):
            names = sorted(n for n in os.listdir(folder) if n.endswith(('.c', '.h', '.cpp', '.hpp', '.py', '.txt', '.sh')) or n == 'Makefile')[:MAX_SOURCE_FILES]
        else:
            names = [spec['source']]
        dir_fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError:
        return {}
    out = {}
    try:
        for name in names:
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
            except OSError:
                continue
            with os.fdopen(fd, 'rb') as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_SOURCE:
                    continue
                out[name] = handle.read(MAX_SOURCE).decode('utf-8', 'replace').split('\n')
    finally:
        os.close(dir_fd)
    return out


class Run:
    """Une correction en cours ; les événements sont conservés pour les nouveaux abonnés."""

    def __init__(self, run_id):
        self.id = run_id
        self.events = []
        self.cond = threading.Condition()
        self.finished = False

    def push(self, event):
        with self.cond:
            event['seq'] = len(self.events)
            event['t'] = round(time.monotonic() - getattr(self, 't0', time.monotonic()), 3)
            self.events.append(event)
            self.cond.notify_all()


def _execute_run(run, folder, exercise, sandbox, record_history, db_path=None, output_path=None):
    """Lance la correction et pousse les événements ; ne lève jamais."""
    from .cli import stage_submission_path
    run.t0 = time.monotonic()
    spec = ALL_EXERCISES[exercise]
    with stage_submission_path(folder, exercise) as staged:
        sources = read_sources(staged, exercise)
        default_file = spec.get('source')
        run.push({'type': 'start', 'exercise': exercise, 'path': str(folder), 'version': __version__,
                  'mode': 'bubblewrap' if sandbox else 'local', 'stages': list(STAGES), 'sources': sources})

        def on_check(status, name, message):
            if status == 'plan':
                run.push({'type': 'plan', 'stage': name, 'total': int(message)})
                return
            event = {'type': 'check', 'stage': stage_of(name), 'status': status, 'name': name, 'message': message}
            if event['stage'] == 'norm' and status == 'fail':
                event['norm'] = parse_norm(message, default_file)
            if event['stage'] == 'tests' and status == 'fail':
                diff = parse_diff(message)
                if diff:
                    event['diff'] = diff
            run.push(event)

        report = None
        try:
            with progress.listening(on_check):
                report = check_exercise(Path(staged), exercise, sandbox=sandbox)
        except Exception as exc:
            run.push({'type': 'check', 'stage': 'files', 'status': 'unavailable', 'name': 'Exécution',
                      'message': 'Correction interrompue : ' + type(exc).__name__ + ' ' + str(exc)[:300]})
    saved = None
    if report is not None and record_history:
        try:
            store_attempt(report, str(folder), db_path=db_path)
            try:
                write_dashboard(output_path=output_path, db_path=db_path)
            except (HistoryError, OSError, ValueError):
                pass
            saved = True
        except (HistoryError, OSError, ValueError) as exc:
            saved = 'Historique non enregistré : ' + str(exc)[:200]
    run.push({'type': 'done', 'result': report['result'] if report else 'incomplete',
              'isolation': report['isolation'] if report else '', 'history': saved,
              'checks': len(report['checks']) if report else 0})
    run.finished = True


def execute_run(run, folder, exercise, sandbox, record_history, db_path=None, output_path=None):
    """Termine aussi les abonnements si la préparation ou le stockage échoue."""
    try:
        _execute_run(run, folder, exercise, sandbox, record_history, db_path, output_path)
    except Exception as exc:
        run.push({'type': 'check', 'stage': 'files', 'status': 'unavailable',
                  'name': 'Exécution', 'message': 'Correction interrompue : ' + type(exc).__name__ + ' ' + str(exc)[:300]})
        run.push({'type': 'done', 'result': 'incomplete', 'isolation': '', 'history': None, 'checks': 0})
    finally:
        with run.cond:
            run.finished = True
            run.cond.notify_all()


def make_handler(token, state, db_path=None, output_path=None):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'MoulinetteLive'
        protocol_version = 'HTTP/1.1'

        def log_message(self, *args):
            pass

        def _host_ok(self):
            port = self.server.server_address[1]
            return self.headers.get('Host', '') in (f'127.0.0.1:{port}', f'localhost:{port}')

        def _allowed_origin(self):
            origin = self.headers.get('Origin')
            port = self.server.server_address[1]
            if origin in (f'http://127.0.0.1:{port}', f'http://localhost:{port}', 'null'):
                return origin
            return None

        def _send(self, code, body, ctype='application/json; charset=utf-8', extra=None):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            elif isinstance(body, str):
                body = body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy',
                             "default-src 'none'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; connect-src 'self' http://127.0.0.1:* http://localhost:*; base-uri 'none'; form-action 'none'")
            allowed_orig = self._allowed_origin()
            if allowed_orig:
                self.send_header('Access-Control-Allow-Origin', allowed_orig)
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Moulinette-Token')
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            if not self._host_ok() or (self.headers.get('Origin') is not None and not self._allowed_origin()):
                return self._send(403, {'error': 'Origine refusée.'})
            return self._send(204, b'', 'text/plain; charset=utf-8')

        def _token_ok(self, query=None):
            given = self.headers.get('X-Moulinette-Token') or (query or {}).get('t', [''])[0]
            return secrets.compare_digest(given, token)

        def do_GET(self):
            url = urlparse(self.path)
            query = parse_qs(url.query)
            if not self._host_ok():
                return self._send(403, {'error': 'Hôte refusé.'})
            if url.path == '/':
                if not self._token_ok(query):
                    return self._send(403, {'error': 'Jeton absent : utilisez l’adresse affichée par la commande.'})
                return self._send(200, render_dashboard(read_history(db_path=db_path), live_mode=True, db_path=db_path), 'text/html; charset=utf-8')
            if not self._token_ok(query):
                return self._send(403, {'error': 'Jeton invalide.'})
            if url.path == '/api/exercises':
                return self._send(200, {'version': __version__, 'exercises': sorted(ALL_EXERCISES)})
            if url.path == '/api/history':
                return self._send(200, {'count': read_history(db_path=db_path).get('count', 0)})
            if url.path == '/api/events':
                return self._stream(query)
            return self._send(404, {'error': 'Introuvable.'})

        def _stream(self, query):
            run = state['runs'].get(query.get('run', [''])[0])
            if run is None:
                return self._send(404, {'error': 'Correction inconnue.'})
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            allowed_orig = self._allowed_origin()
            if allowed_orig:
                self.send_header('Access-Control-Allow-Origin', allowed_orig)
            self.end_headers()
            self.close_connection = True
            index = 0
            try:
                while True:
                    with run.cond:
                        while index >= len(run.events) and not run.finished:
                            run.cond.wait(timeout=15)
                            if index >= len(run.events) and not run.finished:
                                self.wfile.write(b': ping\n\n')
                                self.wfile.flush()
                        batch = run.events[index:]
                        done = run.finished and index + len(batch) >= len(run.events)
                    for event in batch:
                        self.wfile.write(b'data: ' + json.dumps(event, ensure_ascii=False).encode('utf-8') + b'\n\n')
                    self.wfile.flush()
                    index += len(batch)
                    if done:
                        return
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

        def do_POST(self):
            if not self._host_ok():
                return self._send(403, {'error': 'Hôte refusé.'})
            if self.path != '/api/run':
                return self._send(404, {'error': 'Introuvable.'})
            if not self._token_ok():
                return self._send(403, {'error': 'Jeton invalide.'})
            origin = self.headers.get('Origin')
            if origin is not None and not self._allowed_origin():
                return self._send(403, {'error': 'Origine refusée.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 0 or length > MAX_BODY:
                    raise ValueError
                data = json.loads(self.rfile.read(length) or b'{}')
                if not isinstance(data, dict):
                    raise ValueError
            except (ValueError, json.JSONDecodeError):
                return self._send(400, {'error': 'Requête invalide.'})
            raw_ex = data.get('exercise')
            exercise = None
            if raw_ex and raw_ex != 'auto':
                exercise = canonical_exercise(raw_ex)
                if exercise is None:
                    return self._send(400, {'error': 'Exercice non pris en charge.'})
            mode = data.get('mode', 'bubblewrap')
            if mode not in ('bubblewrap', 'local'):
                return self._send(400, {'error': 'Mode inconnu.'})
            if mode == 'local' and data.get('confirm_unsafe') is not True:
                return self._send(400, {'error': 'Le mode local non isolé exige une confirmation explicite.'})
            raw = data.get('path')
            if not isinstance(raw, str) or not raw.strip() or '://' in raw or raw.startswith('git@'):
                return self._send(400, {'error': 'Indiquez un fichier ou dossier local (les dépôts distants ne sont pas pris en charge ici).'})
            target_path = Path(raw).expanduser()
            if not (target_path.is_file() or target_path.is_dir()):
                return self._send(400, {'error': 'Fichier ou dossier introuvable : ' + raw[:200]})
            if exercise is None:
                from .cli import detect_exercise
                exercise, det_err = detect_exercise(str(target_path))
                if det_err:
                    return self._send(400, {'error': det_err})
            with state['lock']:
                if state['active'] is not None and not state['active'].finished:
                    return self._send(409, {'error': 'Une correction est déjà en cours.'})
                run = Run(secrets.token_hex(8))
                state['runs'][run.id] = run
                state['active'] = run
                while len(state['runs']) > 20:
                    state['runs'].pop(next(iter(state['runs'])))
            threading.Thread(target=execute_run, daemon=True,
                             args=(run, target_path, exercise, mode == 'bubblewrap', not data.get('no_history'), db_path, output_path)).start()
            return self._send(202, {'run': run.id})

    return Handler


def _daemon_state_file():
    from .history import data_directory
    return data_directory() / 'live-daemon.json'


def read_live_daemon():
    """Renvoie (port, token) si un démon local répond sur 127.0.0.1, sinon (None, None)."""
    import socket
    try:
        info = json.loads(_daemon_state_file().read_text(encoding='utf-8'))
        port = int(info['port'])
        token = str(info['token'])
        if not (1 <= port <= 65535) or not token:
            return None, None
        with socket.create_connection(('127.0.0.1', port), timeout=0.12):
            return port, token
    except Exception:
        return None, None


def ensure_live_daemon():
    """Démarre en arrière-plan le serveur local 127.0.0.1 s'il n'est pas déjà actif."""
    import subprocess, sys
    port, token = read_live_daemon()
    if port and token:
        return port, token
    try:
        subprocess.Popen(
            [sys.executable, '-m', 'moulinette', 'dashboard', '--live', '--no-open'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        for _ in range(30):
            time.sleep(0.05)
            port, token = read_live_daemon()
            if port and token:
                return port, token
    except OSError:
        pass
    return None, None


def serve(host='127.0.0.1', port=0, open_browser=True, announce=print, db_path=None, output_path=None):
    """Démarre le serveur ; bloque jusqu'à Ctrl+C."""
    if host not in ('127.0.0.1', 'localhost'):
        raise ValueError('Le serveur temps réel n’écoute que sur la boucle locale.')
    token = secrets.token_urlsafe(24)
    state = {'runs': {}, 'active': None, 'lock': threading.Lock()}
    httpd = ThreadingHTTPServer(('127.0.0.1', port), make_handler(token, state, db_path=db_path, output_path=output_path))
    httpd.daemon_threads = True
    actual_port = httpd.server_address[1]
    try:
        if db_path is None:
            sf = _daemon_state_file()
            # Remplacement atomique : ne jamais suivre un lien placé à sf.
            fd, temp_name = tempfile.mkstemp(prefix='.live-daemon-', dir=sf.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                    json.dump({'port': actual_port, 'token': token, 'pid': os.getpid()}, handle)
                os.replace(temp_name, sf)
            finally:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass
        write_dashboard(output_path=output_path, db_path=db_path)
    except (HistoryError, OSError, ValueError):
        httpd.server_close()
        raise
    url = f'http://127.0.0.1:{actual_port}/?t={token}'
    announce(f'Tableau de bord local : {url}')
    announce('Local uniquement ; code de confiance seulement. Ctrl+C pour arrêter.')
    if open_browser:
        import webbrowser
        try:
            if not webbrowser.open(url, new=2):
                announce('Navigateur non ouvert automatiquement ; ouvrez l’adresse indiquée.')
        except (OSError, webbrowser.Error):
            announce('Navigateur non ouvert automatiquement ; ouvrez l’adresse indiquée.')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0
