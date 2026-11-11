"""Historique local des corrections ; aucun envoi réseau."""
import json
import os
import sqlite3
import stat
import tempfile
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
from .exercise_catalog import canonical_exercise, CPP_EXERCISES, EXERCISES, PY_EXERCISES
from .safe_text import safe_text

class HistoryError(Exception):
    pass


def data_directory():
    value=os.environ.get('XDG_DATA_HOME','')
    base=Path(value).expanduser() if value and Path(value).is_absolute() else Path.home()/'.local'/'share'
    return base/'moulinette-lab'


def _db(db_path=None):
    if db_path is not None:
        path = Path(db_path).expanduser()
        folder = path.parent
    else:
        folder = data_directory()
        path = folder / 'history.sqlite3'
    try:
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        info=folder.lstat()
        if not stat.S_ISDIR(info.st_mode): raise HistoryError('Le dossier de données doit être un dossier réel, pas un lien.')
        if path.is_symlink(): raise HistoryError('Le fichier d’historique ne doit pas être un lien symbolique.')
        fd=os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC|os.O_NOFOLLOW, 0o600)
        os.close(fd)
    except FileExistsError:
        pass
    except OSError as e:
        raise HistoryError(f'Accès à l’historique impossible : {e}') from e
    try:
        info=path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise HistoryError('Le fichier d’historique doit être un fichier régulier sans lien multiple.')
    except OSError as e:
        raise HistoryError(f'Accès à l’historique impossible : {e}') from e
    # Les auxiliaires SQLite peuvent exister pendant l'utilisation normale.
    # Refuser les liens/fichiers spéciaux déjà présents, sans les supprimer.
    try:
        for suffix in ('-journal', '-wal', '-shm'):
            sidecar=path.with_name(path.name+suffix)
            try: info=sidecar.lstat()
            except FileNotFoundError: continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise HistoryError('Fichier auxiliaire SQLite non régulier ou à liens multiples.')
    except OSError as e:
        raise HistoryError(f'Accès à l’historique impossible : {e}') from e
    # Contrôle statique uniquement : sqlite3.connect(path) reste sujet à une
    # course face à un processus capable de modifier ce dossier.
    connection=None
    try:
        connection=sqlite3.connect(path,timeout=3)
        connection.execute('''CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, exercise TEXT NOT NULL,
            source_label TEXT NOT NULL, result TEXT NOT NULL, isolation TEXT NOT NULL,
            checks_json TEXT NOT NULL)''')
        connection.execute('''CREATE TABLE IF NOT EXISTS piscine_unlocks (
            piscine TEXT PRIMARY KEY, unlocked_at TEXT NOT NULL)''')
        connection.commit()
        return connection
    except sqlite3.Error as e:
        if connection is not None: connection.close()
        raise HistoryError(f'Base d’historique indisponible : {e}') from e


def store_attempt(report, source_path, db_path=None):
    exercise=canonical_exercise(report.get('exercise'))
    result=report.get('result'); checks=report.get('checks')
    if not exercise or result not in ('passed','failed','incomplete') or not isinstance(checks,list) or len(checks)>128:
        raise HistoryError('Rapport non reconnu ; historique non enregistré.')
    clean=[]
    for c in checks:
        if not isinstance(c,dict) or c.get('status') not in ('pass','fail','unavailable','info') or not isinstance(c.get('name'),str) or not isinstance(c.get('message'),str):
            raise HistoryError('Contrôle non reconnu ; historique non enregistré.')
        clean.append({'status':c['status'],'name':safe_text(c['name'])[:200],'message':safe_text(c['message'])[:4000]})
    label=safe_text(Path(source_path).name or '.')[:255]
    source=report.get('source')
    if isinstance(source,dict) and source.get('kind')=='github':
        url=source.get('url'); commit=source.get('commit'); subdir=source.get('subdir')
        if isinstance(url,str) and isinstance(commit,str) and isinstance(subdir,str):
            label=safe_text('GitHub '+url.removeprefix('https://github.com/')+'@'+commit+':'+subdir)[:255]
    isolation=report.get('isolation','non précisé')
    if not isinstance(isolation,str): isolation='non précisé'
    try:
        with closing(_db(db_path=db_path)) as db, db:
            now_iso = datetime.now(timezone.utc).isoformat(timespec='seconds')
            db.execute('INSERT INTO attempts (created_at,exercise,source_label,result,isolation,checks_json) VALUES (?,?,?,?,?,?)',
                       (now_iso,exercise,label,result,safe_text(isolation)[:300],json.dumps(clean,ensure_ascii=False)))
            _sync_unlocks_in_tx(db, now_iso)
    except sqlite3.Error as e:
        raise HistoryError(f'Enregistrement impossible : {e}') from e


def _sync_unlocks_in_tx(db, now_iso=None):
    """Débloque de façon permanente cpp puis py lorsque tous les exercices de la piscine précédente sont réussis."""
    if now_iso is None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec='seconds')
    rows = db.execute(
        'SELECT a.exercise, a.result FROM attempts a '
        'JOIN (SELECT exercise, MAX(id) AS mid FROM attempts GROUP BY exercise) b ON a.id = b.mid'
    ).fetchall()
    latest_map = { canonical_exercise(r[0]) or r[0]: r[1] for r in rows }
    unlocked = { r[0] for r in db.execute('SELECT piscine FROM piscine_unlocks').fetchall() }
    if 'cpp' not in unlocked and all(latest_map.get(ex) == 'passed' for ex in EXERCISES):
        db.execute('INSERT OR IGNORE INTO piscine_unlocks (piscine, unlocked_at) VALUES (?, ?)', ('cpp', now_iso))
        unlocked.add('cpp')
    if 'cpp' in unlocked and 'py' not in unlocked and all(latest_map.get(ex) == 'passed' for ex in CPP_EXERCISES):
        db.execute('INSERT OR IGNORE INTO piscine_unlocks (piscine, unlocked_at) VALUES (?, ?)', ('py', now_iso))


def read_unlocked_piscines(history=None, db_path=None):
    """Retourne l'ensemble des piscines débloquées ('c', éventuellement 'cpp' et 'py')."""
    unlocked = {'c'}
    if isinstance(history, dict) and isinstance(history.get('unlocked_piscines'), (set, list, tuple)):
        unlocked.update(x for x in history['unlocked_piscines'] if x in ('c', 'cpp', 'py'))
    db_file = Path(db_path).expanduser() if db_path is not None else data_directory() / 'history.sqlite3'
    if db_file.exists() and not db_file.is_symlink():
        try:
            with closing(_db(db_path=db_path)) as db, db:
                _sync_unlocks_in_tx(db)
                rows = db.execute('SELECT piscine FROM piscine_unlocks').fetchall()
                unlocked.update(r[0] for r in rows if r[0] in ('c', 'cpp', 'py'))
        except Exception:
            pass
    if isinstance(history, dict):
        latest_map = {
            canonical_exercise(x.get('exercise')) or x.get('exercise'): x.get('result')
            for x in history.get('latest', []) if isinstance(x, dict)
        }
        if all(latest_map.get(ex) == 'passed' for ex in EXERCISES):
            unlocked.add('cpp')
        if 'cpp' in unlocked and all(latest_map.get(ex) == 'passed' for ex in CPP_EXERCISES):
            unlocked.add('py')
    return unlocked


def read_history(limit=50, db_path=None):
    try:
        with closing(_db(db_path=db_path)) as db:
            db.row_factory=sqlite3.Row
            count=db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
            rows=db.execute('SELECT * FROM attempts ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
            latest=db.execute('SELECT a.* FROM attempts a JOIN (SELECT exercise,MAX(id) AS mid FROM attempts GROUP BY exercise) b ON a.id=b.mid ORDER BY a.exercise').fetchall()
        def convert(row):
            obj=dict(row)
            try: obj['checks']=json.loads(obj.pop('checks_json'))
            except (ValueError,TypeError) as e: raise HistoryError('Historique illisible : contrôles JSON invalides.') from e
            if not isinstance(obj['checks'],list): raise HistoryError('Historique illisible : contrôles invalides.')
            return obj
        return {'count':count,'recent':[convert(r) for r in rows], 'latest':[convert(r) for r in latest]}
    except sqlite3.Error as e:
        raise HistoryError(f'Lecture de l’historique impossible : {e}') from e



def reset_history(db_path=None):
    """Sauvegarde SQLite cohérente puis efface tentatives et déblocages, transactionnellement.

    L'appelant doit obtenir une confirmation explicite avant d'appeler cette fonction.
    Arrêter les corrections/live au préalable : une correction ultérieure peut réécrire.
    """
    path = Path(db_path).expanduser() if db_path is not None else data_directory() / 'history.sqlite3'
    backup_path = None
    # Ne crée ni base inexistante, ni schéma dans une base étrangère.
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise HistoryError('Base cible non régulière ou à liens multiples ; reset annulé.')
    except FileNotFoundError:
        raise HistoryError('Base introuvable ; rien à réinitialiser.')
    except OSError as exc:
        raise HistoryError(f'Base inaccessible : {exc}') from exc
    try:
        with closing(sqlite3.connect(path.absolute().as_uri() + '?mode=ro', uri=True, timeout=3)) as probe:
            names = {r[0] for r in probe.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'attempts', 'piscine_unlocks'} <= names:
                raise HistoryError('Base non reconnue comme historique Moulinette ; reset annulé.')
    except sqlite3.Error as exc:
        raise HistoryError(f'Base illisible ; reset annulé : {exc}') from exc
    try:
        with closing(_db(db_path=db_path)) as db:
            db.execute('BEGIN IMMEDIATE')
            fd, name = tempfile.mkstemp(prefix=path.name + '.sauvegarde-', suffix='.sqlite3', dir=path.parent)
            backup_path = Path(name)
            os.close(fd)
            # Lecture indépendante pendant le verrou : le snapshot inclut le WAL.
            with closing(sqlite3.connect(path, timeout=3)) as source, closing(sqlite3.connect(backup_path, timeout=3)) as dest:
                source.backup(dest)
                if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise HistoryError('Sauvegarde SQLite invalide ; reset annulé.')
            with backup_path.open('rb') as saved:
                os.fsync(saved.fileno())
            db.execute('DELETE FROM attempts')
            db.execute('DELETE FROM piscine_unlocks')
            db.commit()
        return backup_path
    except (OSError, sqlite3.Error, HistoryError) as e:
        if backup_path is not None:
            try: backup_path.unlink()
            except OSError: pass
        if isinstance(e, HistoryError): raise
        raise HistoryError(f'Réinitialisation annulée : {e}') from e

def score(attempt):
    """% de contrôles passés parmi pass/fail uniquement si vérification complète."""
    checks=attempt['checks']
    if attempt['result']=='incomplete' or any(c.get('status')=='unavailable' for c in checks if isinstance(c,dict)):
        return None
    passed=sum(isinstance(c,dict) and c.get('status')=='pass' for c in checks)
    failed=sum(isinstance(c,dict) and c.get('status')=='fail' for c in checks)
    return round(100*passed/(passed+failed)) if passed+failed else None
