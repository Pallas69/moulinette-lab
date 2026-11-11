"""Récupération expérimentale de dépôts GitHub publics *de confiance*.

Helper interne non borné par lui-même ; le worker CLI l'exécute dans un tmpfs Bubblewrap. Réseau partagé.
Aucune garantie contre un dépôt hostile ; pas de sous-modules ni de credentials.
"""
import contextlib
import os
import re
import resource
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from .checker import MAX_FILE
from .exercise_catalog import EXERCISES
from .process_capture import run_bounded, exception_with_cleanup

MAX_GIT_FILE=64*1024*1024
GIT_TIMEOUT=45

class GitHubSourceError(Exception):
    pass


def normalize_url(value):
    if not isinstance(value,str) or len(value)>240 or any(ord(c)<33 or ord(c)>126 for c in value):
        raise GitHubSourceError('URL GitHub invalide.')
    try:
        u=urlsplit(value)
        if (u.scheme != 'https' or u.netloc.lower() != 'github.com' or u.query or u.fragment
            or not u.path.startswith('/') or '%' in u.path or '\\' in u.path):
            raise ValueError
        components=u.path.strip('/').split('/')
        if len(components)!=2 or u.path.startswith('//') or u.path.endswith('//'):
            raise ValueError
        owner,repo=components
        if repo.endswith('.git'): repo=repo[:-4]
        if (not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?',owner)
            or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',repo)
            or repo in ('.','..') or repo.lower().endswith('.git')):
            raise ValueError
        return f'https://github.com/{owner}/{repo}.git',owner,repo
    except ValueError as exc:
        raise GitHubSourceError('URL attendue : https://github.com/proprietaire/depot, sans identifiants ni chemin supplémentaire.') from exc


def normalize_ref(value):
    if value is None: return None
    if not isinstance(value,str) or not 1<=len(value)<=200 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*',value):
        raise GitHubSourceError('Référence Git invalide : utiliser une branche, un tag ou un SHA complet.')
    if (value.endswith(('/', '.', '.lock')) or '..' in value or '//' in value
        or '@{' in value or any(part.startswith('.') or part.endswith('.lock') for part in value.split('/'))):
        raise GitHubSourceError('Référence Git invalide.')
    if re.fullmatch(r'[0-9a-fA-F]{7,39}',value):
        raise GitHubSourceError('Pour un commit, fournir le SHA complet de 40 caractères.')
    return value


def normalize_subdir(value):
    if value in (None,'.',''): return ()
    if not isinstance(value,str) or len(value)>1024 or value.startswith('/') or '\\' in value or any(ord(c)<32 or ord(c)==127 for c in value):
        raise GitHubSourceError('Sous-dossier invalide : chemin relatif à la racine du dépôt uniquement.')
    parts=value.split('/')
    try:
        if any(part in ('','.','..','.git') or len(part.encode('utf-8','strict'))>255 or len(os.fsencode(part))>255 for part in parts):
            raise GitHubSourceError('Sous-dossier invalide : pas de traversée, de lien ou de dossier .git.')
    except UnicodeError as exc:
        raise GitHubSourceError('Sous-dossier Git non représentable en UTF-8.') from exc
    return tuple(parts)


def _git(argv, cwd, git, env):
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(45,46))
        resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
        resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_GIT_FILE,MAX_GIT_FILE))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    command=[git,'-c','protocol.allow=never','-c','protocol.https.allow=always',
             '-c','http.followRedirects=false','-c','core.hooksPath=/dev/null',
             '-c','submodule.recurse=false']+argv
    try:
        code, stdout, stderr, timed_out = run_bounded(command, cwd, GIT_TIMEOUT, env, limits,
                                                       max_stdout=4097, max_stderr=2049)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitHubSourceError(f'Git indisponible ou nettoyage non confirmé : {exception_with_cleanup(exc)}') from exc
    if timed_out:
        raise GitHubSourceError('Délai Git dépassé ; aucune correction lancée.')
    if code != 0:
        detail=stderr.decode('utf-8','replace').strip().replace('\n',' ')[:400]
        raise GitHubSourceError('Récupération Git impossible : '+(detail or f'code {code}'))
    if len(stdout)>4096: raise GitHubSourceError('Réponse Git inattendue ou trop longue.')
    return stdout.decode('ascii','strict').strip()


def _prepare_submission(repo,subdir,stage,source_name):
    target=repo
    for name in subdir:
        target=target/name
        try: st=target.lstat()
        except OSError as e: raise GitHubSourceError(f'Sous-dossier introuvable : {name}') from e
        if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
            raise GitHubSourceError('Le sous-dossier doit traverser uniquement des répertoires réels, sans lien symbolique.')
    try:
        entries=os.listdir(target)
        if not subdir and '.git' in entries: entries.remove('.git')
        if len(entries)>1000: raise GitHubSourceError('Trop de fichiers dans le dossier sélectionné.')
        stage.mkdir(mode=0o700)
        # Les noms supplémentaires suffisent au correcteur pour arrêter la correction ;
        # leur contenu n'est pas lu ni recopié.
        for name in entries:
            if name != source_name:
                (stage/name).touch(mode=0o600,exist_ok=False)
        if source_name not in entries: return
        entry=target/source_name
        info=entry.lstat()
        if stat.S_ISLNK(info.st_mode):
            (stage/source_name).symlink_to('source-symlink-refuse')
        elif stat.S_ISDIR(info.st_mode):
            (stage/source_name).mkdir(mode=0o700)
        elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
            fd=os.open(entry,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
            with os.fdopen(fd,'rb') as src:
                before=os.fstat(src.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1: raise GitHubSourceError('Fichier source inattendu.')
                contents=src.read(MAX_FILE+1); after=os.fstat(src.fileno())
                if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
                    raise GitHubSourceError('Source modifiée pendant la copie.')
            (stage/source_name).write_bytes(contents)
        else:
            raise GitHubSourceError('Fichier source non régulier ou avec lien physique refusé.')
    except OSError as e:
        raise GitHubSourceError(f'Lecture du dépôt impossible : {e}') from e


@contextlib.contextmanager
def trusted_public_repository(url, exercise, *, ref=None, subdir=None, _allow_unbounded_environment=False):
    if _allow_unbounded_environment is not True:
        raise GitHubSourceError('Helper Git interne : environnement borné non confirmé. Utiliser bounded_public_repository.')
    canonical,owner,repo_name=normalize_url(url)
    ref=normalize_ref(ref); parts=normalize_subdir(subdir)
    if exercise not in EXERCISES: raise GitHubSourceError('Exercice inconnu.')
    git=shutil.which('git')
    if not git or not Path(git).resolve().is_relative_to('/usr'):
        raise GitHubSourceError('Git système introuvable ou hors de /usr ; aucune récupération lancée.')
    git=str(Path(git).resolve())
    try:
        temporary = tempfile.TemporaryDirectory(prefix='moulinette-github-')
    except OSError as exc:
        raise GitHubSourceError(f'Création du dossier temporaire impossible : {exc}') from exc
    with temporary as tmp:
        root=Path(tmp); repo=root/'repo'; stage=root/'submission'; home=root/'git-home'
        try: home.mkdir(mode=0o700)
        except OSError as exc: raise GitHubSourceError(f'Création du dossier Git impossible : {exc}') from exc
        env={'PATH':'/usr/bin:/bin','HOME':str(home),'XDG_CONFIG_HOME':str(home),
             'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0',
             'GIT_ASKPASS':'/bin/false','SSH_ASKPASS':'/bin/false','GIT_LFS_SKIP_SMUDGE':'1',
             'LC_ALL':'C','LANG':'C'}
        is_sha=bool(ref and re.fullmatch(r'[0-9a-fA-F]{40}',ref))
        args=['clone','--quiet','--depth=1','--single-branch','--no-tags','--no-recurse-submodules']
        if ref and ref != 'HEAD' and not is_sha: args+=['--branch',ref]
        args+=['--',canonical,str(repo)]
        try:
            _git(args,root,git,env)
            if is_sha:
                _git(['fetch','--quiet','--depth=1','--no-tags','--no-recurse-submodules','origin',ref],repo,git,env)
                _git(['checkout','--quiet','--detach','--force',ref],repo,git,env)
            commit=_git(['rev-parse','--verify','HEAD^{commit}'],repo,git,env)
        except (UnicodeError,ValueError) as exc:
            raise GitHubSourceError('Réponse Git invalide.') from exc
        except OSError as exc:
            raise GitHubSourceError(f'Erreur temporaire ou système pendant Git : {exc}') from exc
        if not re.fullmatch(r'[0-9a-fA-F]{40}',commit): raise GitHubSourceError('Empreinte de commit inconnue ; correction refusée.')
        if is_sha and commit.lower()!=ref.lower(): raise GitHubSourceError('Le commit obtenu ne correspond pas au commit demandé.')
        if 'project' in EXERCISES[exercise]:
            from .project_engine import snapshot_submission, ProjectSubmissionError, ProjectUnavailable
            target=repo
            for part in parts:
                target=target/part
                st=target.lstat()
                if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
                    raise GitHubSourceError('Le sous-dossier doit être un répertoire réel.')
            stage.mkdir(mode=0o700)
            try:
                snapshot_submission(target,stage,{'omit_root_git':not parts})
            except (ProjectSubmissionError,ProjectUnavailable,OSError) as exc:
                raise GitHubSourceError('Copie du projet impossible : '+str(exc)) from exc
        else:
            _prepare_submission(repo,parts,stage,EXERCISES[exercise]['source'])
        yield stage, {'kind':'github','url':canonical.removesuffix('.git'),'commit':commit.lower(),
                      'ref':ref or 'HEAD','subdir':'/'.join(parts) or '.'}
