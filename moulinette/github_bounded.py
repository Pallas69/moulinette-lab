"""Récupération Git dans un tmpfs Bubblewrap borné ; confiance requise.

Le réseau reste partagé et le noyau commun. Ce n'est PAS une protection
validée contre un dépôt hostile ni un quota global pour toute la moulinette.
"""
import base64
import binascii
import contextlib
import json
import os
import re
import resource
import shutil
import subprocess
import tempfile
from pathlib import Path
from .exercise_catalog import EXERCISES
from .github_source import (GitHubSourceError, MAX_FILE, normalize_ref, normalize_subdir,
                            normalize_url)
from .process_capture import run_bounded, exception_with_cleanup
from .scope_protocol import _unique_object

GIT_TMPFS_BYTES = 128 * 1024 * 1024
WORKER_TIMEOUT = 100
MAX_WORKER_OUTPUT = 6 * 1024 * 1024


def _parse_snapshot(payload, url, ref, subdir, source_name):
    """Valider entièrement le protocole avant toute création de fichier hôte."""
    if not isinstance(payload,dict) or set(payload)!={'version','entries','source_type','source_b64','source'} or type(payload['version']) is not int or payload['version']!=1:
        raise GitHubSourceError('Réponse du superviseur Git invalide.')
    entries=payload['entries']; kind=payload['source_type']; src=payload['source']; data=payload['source_b64']
    if not isinstance(entries,list) or len(entries)>1000 or any(not isinstance(n,str) for n in entries):
        raise GitHubSourceError('Inventaire Git invalide.')
    try:
        if any(not n or n in ('.','..') or '/' in n or '\x00' in n or
               any(ord(c)<32 or ord(c)==127 for c in n) or len(n.encode('utf-8', 'strict'))>255 or len(os.fsencode(n))>255 for n in entries):
            raise GitHubSourceError('Nom de fichier Git invalide.')
    except UnicodeError as exc:
        raise GitHubSourceError('Nom de fichier Git non représentable.') from exc
    if len(entries)!=len(set(entries)) or kind not in ('absent','file','dir','symlink'):
        raise GitHubSourceError('Inventaire Git incohérent.')
    if (source_name in entries) != (kind!='absent') or not isinstance(data,str):
        raise GitHubSourceError('Source Git incohérente.')
    if not isinstance(src,dict) or set(src)!={'kind','url','commit','ref','subdir'} or any(not isinstance(v,str) for v in src.values()):
        raise GitHubSourceError('Provenance Git invalide.')
    commit=src['commit']
    if (src['kind']!='github' or src['url']!=url or not re.fullmatch(r'[0-9a-f]{40}',commit)
        or src['ref']!=ref or src['subdir']!=subdir or
        (re.fullmatch(r'[0-9a-fA-F]{40}',ref) and commit!=ref.lower())):
        raise GitHubSourceError('Provenance Git incohérente.')
    if len(data)>((MAX_FILE+1+2)//3)*4:
        raise GitHubSourceError('Source Git trop volumineuse.')
    try: content=base64.b64decode(data,validate=True)
    except (binascii.Error,ValueError,UnicodeError) as exc: raise GitHubSourceError('Source Git illisible.') from exc
    if len(content)>MAX_FILE+1 or (kind!='file' and content):
        raise GitHubSourceError('Contenu de source Git incohérent.')
    return {'entries':entries,'kind':kind,'contents':content,'source':src}


def _parse_project_snapshot(payload,url,ref,subdir):
    """Contrôler noms, tailles et provenance avant de reconstituer un projet."""
    from .project_engine import MAX_FILES, MAX_FILE, MAX_TOTAL
    if not isinstance(payload,dict) or set(payload)!={'version','files','dirs','source'} or type(payload['version']) is not int or payload['version']!=2:
        raise GitHubSourceError('Réponse du projet Git invalide.')
    files=payload['files'];dirs=payload['dirs'];src=payload['source']
    if not isinstance(files,list) or not isinstance(dirs,list) or len(files)+len(dirs)>MAX_FILES:
        raise GitHubSourceError('Inventaire du projet Git invalide.')
    if not isinstance(src,dict) or set(src)!={'kind','url','commit','ref','subdir'} or any(not isinstance(v,str) for v in src.values()):
        raise GitHubSourceError('Provenance Git invalide.')
    commit=src['commit']
    if (src['kind']!='github' or src['url']!=url or not re.fullmatch(r'[0-9a-f]{40}',commit)
        or src['ref']!=ref or src['subdir']!=subdir or (re.fullmatch(r'[0-9a-fA-F]{40}',ref) and commit!=ref.lower())):
        raise GitHubSourceError('Provenance Git incohérente.')
    def valid_path(path):
        if not isinstance(path,str) or not path or path.startswith('/') or '\\' in path or '\x00' in path:return False
        parts=path.split('/')
        try:return len(path.encode('utf-8','strict'))<=4096 and all(p not in ('','.','..') and len(p.encode('utf-8','strict'))<=255 and not any(ord(c)<32 or ord(c)==127 for c in p) for p in parts)
        except UnicodeError:return False
    if any(not valid_path(d) for d in dirs) or len(set(dirs))!=len(dirs):raise GitHubSourceError('Répertoires Git invalides.')
    decoded={};total=0
    for item in files:
        if not isinstance(item,dict) or set(item)!={'path','data_b64'} or not valid_path(item['path']) or not isinstance(item['data_b64'],str) or item['path'] in decoded:
            raise GitHubSourceError('Fichier Git invalide.')
        if len(item['data_b64'])>((MAX_FILE+2)//3)*4:raise GitHubSourceError('Fichier Git trop volumineux.')
        try:content=base64.b64decode(item['data_b64'],validate=True)
        except (binascii.Error,ValueError,UnicodeError) as exc:raise GitHubSourceError('Fichier Git illisible.') from exc
        if len(content)>MAX_FILE:raise GitHubSourceError('Fichier Git trop volumineux.')
        total+=len(content)
        if total>MAX_TOTAL:raise GitHubSourceError('Projet Git trop volumineux.')
        decoded[item['path']]=content
    if set(decoded)&set(dirs):raise GitHubSourceError('Inventaire Git incohérent.')
    # Every ancestor must be an advertised directory; a file cannot be an ancestor.
    for path in list(decoded)+dirs:
        for parent in Path(path).parents:
            p=parent.as_posix()
            if p!='.' and p not in dirs:raise GitHubSourceError('Arborescence Git incohérente.')
    return {'files':decoded,'dirs':dirs,'source':src}


def _fetch_snapshot(canonical,exercise,ref,subdir):
    bwrap=shutil.which('bwrap')
    if not bwrap: raise GitHubSourceError('Bubblewrap introuvable : récupération Git bornée impossible, aucun repli sur l’hôte.')
    package=Path(__file__).resolve().parent
    python=Path('/usr/bin/python3')
    inputs=[Path('/etc/ssl/certs'),Path('/etc/resolv.conf'),Path('/etc/nsswitch.conf')]
    if not python.is_file() or not all(p.exists() for p in inputs):
        raise GitHubSourceError('Python système ou configuration TLS/DNS indisponible ; récupération arrêtée.')
    command=[bwrap,'--unshare-all','--share-net','--die-with-parent','--new-session',
             '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib']
    if Path('/usr/lib64').exists(): command += ['--symlink','usr/lib64','/lib64']
    modules=('__init__.py','github_worker.py','github_source.py','checker.py','norm.py',
             'exercise_catalog.py','c01_catalog.py','c02_catalog.py','c03_catalog.py','c04_catalog.py','c05_catalog.py','c06_catalog.py','c07_catalog.py','c07_project_catalog.py','c08_catalog.py','c09_project_catalog.py','c10_catalog.py','c11_catalog.py','c11_project_catalog.py','c12_catalog.py','c13_catalog.py','project_catalog.py','project_engine.py','sandbox_runner.py','process_capture.py','safe_text.py','c_memguard.py','cpp_catalog.py','cpp_engine.py','py_catalog.py','py_engine.py','pipeline.py','progress.py','recursion_hint.py','seccomp_filter.py')
    if not all((package/name).is_file() for name in modules):
        raise GitHubSourceError('Modules du superviseur Git indisponibles.')
    command += ['--dir','/app','--dir','/app/moulinette']
    for name in modules:
        command += ['--ro-bind',str(package/name),'/app/moulinette/'+name]
    command += ['--dir','/etc','--dir','/etc/ssl','--ro-bind',str(inputs[0]),'/etc/ssl/certs',
                '--ro-bind',str(inputs[1]),'/etc/resolv.conf','--ro-bind',str(inputs[2]),'/etc/nsswitch.conf',
                '--size',str(GIT_TMPFS_BYTES),'--tmpfs','/work',
                '--symlink','work','/tmp','--proc','/proc','--dev','/dev','--chdir','/work',
                '--clearenv','--setenv','PATH','/usr/bin:/bin','--setenv','LC_ALL','C',
                '--setenv','HOME','/work','--setenv','TMPDIR','/work','--',str(python),'-I','-B','-c',
                'import sys;sys.path.insert(0,"/app");from moulinette.github_worker import main;main()',
                canonical,exercise,ref or '',subdir or '']
    def limits():
        # Git ajuste son soft CPU à 45 s ; hard 46 s permet cette limite imbriquée.
        resource.setrlimit(resource.RLIMIT_CPU,(30,46))
        resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
        resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024*1024,64*1024*1024))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C'}
    with tempfile.TemporaryFile() as status_file:
        command[1:1]=['--json-status-fd',str(status_file.fileno())]
        try:
            code,out,err,timed_out=run_bounded(command,Path('/'),WORKER_TIMEOUT,env,limits,
                                                 pass_fds=(status_file.fileno(),),
                                                 max_stdout=MAX_WORKER_OUTPUT,max_stderr=8193)
        except (OSError,subprocess.SubprocessError) as exc:
            raise GitHubSourceError(f'Récupération bornée indisponible : {exception_with_cleanup(exc)}') from exc
        status_file.seek(0); raw=status_file.read(8193)
    if timed_out: raise GitHubSourceError('Délai de récupération bornée dépassé ; correction arrêtée.')
    if code != 0:
        detail=err.decode('utf-8','replace').strip().replace('\n',' ')[:400]
        raise GitHubSourceError('Récupération bornée impossible : ' + (detail or f'code {code}'))
    try:
        if len(raw)>8192 or len(out)>=MAX_WORKER_OUTPUT or len(err)>=8193: raise ValueError('capture trop grande')
        events=[json.loads(line) for line in raw.decode('utf-8','strict').splitlines() if line.strip()]
        if (len(events)!=2 or not isinstance(events[0],dict) or type(events[0].get('child-pid')) is not int
            or events[0]['child-pid']<=0 or not isinstance(events[1],dict)
            or type(events[1].get('exit-code')) is not int or events[1]['exit-code']!=code):
            raise ValueError('statut Bubblewrap incohérent')
        if code!=0: raise ValueError('échec du superviseur')
        if err.strip(): raise ValueError('sortie d’erreur inattendue')
        def reject_constant(value): raise ValueError('constante JSON non standard')
        payload=json.loads(out.decode('utf-8','strict'), object_pairs_hook=_unique_object, parse_constant=reject_constant)
        if not isinstance(payload,dict): raise ValueError('objet JSON attendu')
        if set(payload)=={'version','error'} and payload['version']==1 and isinstance(payload['error'],str):
            raise GitHubSourceError('Récupération Git impossible : '+payload['error'][:500])
        return payload
    except (UnicodeError,ValueError,TypeError,RecursionError) as exc:
        raise GitHubSourceError('Supervision Git bornée indisponible ou résultat incohérent ; aucun repli.') from exc


@contextlib.contextmanager
def bounded_public_repository(url,exercise,*,ref=None,subdir=None):
    canonical,_,_=normalize_url(url); ref=normalize_ref(ref); parts=normalize_subdir(subdir)
    if exercise not in EXERCISES: raise GitHubSourceError('Exercice inconnu.')
    subdir_name='/'.join(parts) or '.'
    payload=_fetch_snapshot(canonical,exercise,ref,subdir)
    is_project='project' in EXERCISES[exercise]
    parsed=(_parse_project_snapshot(payload,canonical.removesuffix('.git'),ref or 'HEAD',subdir_name)
            if is_project else _parse_snapshot(payload,canonical.removesuffix('.git'),ref or 'HEAD',subdir_name,EXERCISES[exercise]['source']))
    try: tmp=tempfile.TemporaryDirectory(prefix='moulinette-github-stage-')
    except OSError as exc: raise GitHubSourceError(f'Dossier temporaire indisponible : {exc}') from exc
    with tmp as folder:
        stage=Path(folder)/'submission'; name=EXERCISES[exercise]['source']
        try:
            stage.mkdir(mode=0o700)
            if is_project:
                for directory in sorted(parsed['dirs'],key=lambda x:(x.count('/'),x)):
                    (stage/directory).mkdir(mode=0o700,parents=True,exist_ok=True)
                for file,content in parsed['files'].items():
                    (stage/file).write_bytes(content)
            else:
                for extra in parsed['entries']:
                    if extra!=name: (stage/extra).touch(mode=0o600,exist_ok=False)
                kind=parsed['kind']
                if kind=='file': (stage/name).write_bytes(parsed['contents'])
                elif kind=='dir': (stage/name).mkdir(mode=0o700)
                elif kind=='symlink': (stage/name).symlink_to('source-symlink-refuse')
        except OSError as exc:
            raise GitHubSourceError(f'Préparation locale impossible : {exc}') from exc
        yield stage,parsed['source']
