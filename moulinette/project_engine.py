"""Moteur expérimental de projets : fichiers, en-têtes et Makefiles.

Réservé au code de confiance. Le bac temporaire et Bubblewrap ne constituent
pas une protection contre un dépôt hostile ; aucun repli automatique.
"""
import base64
import json
import os
import resource
import re
import secrets
import shutil
import stat
import tempfile
import time
from pathlib import Path
from .norm import parse_norm_result
from .process_capture import run_bounded
from .recursion_hint import doop_hint
from .safe_text import safe_text
from .seccomp_filter import seccomp_fd
from .pipeline import build_report
from . import progress

MAX_FILES=80
MAX_FILE=262144
MAX_TOTAL=4*1024*1024

class ProjectUnavailable(Exception): pass
class ProjectSubmissionError(Exception): pass

def snapshot_submission(folder,dest,cfg):
    """Copier uniquement des fichiers réguliers, sans modifier le rendu.

    Contrôles indicatifs ; cette copie n'est pas un instantané atomique et
    ne rend pas le moteur sûr contre un processus concurrent malveillant.
    """
    root=Path(folder)
    try: st=root.lstat()
    except FileNotFoundError as exc:raise ProjectSubmissionError('Dossier introuvable.') from exc
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):raise ProjectSubmissionError('Le dossier doit être un répertoire réel.')
    names=[];dirnames=[];total=0
    for base,dirs,files in os.walk(root,followlinks=False):
        if cfg.get('omit_root_git') and Path(base)==root and '.git' in dirs:
            dirs.remove('.git')
        for name in dirs:
            item=Path(base)/name
            if item.is_symlink():raise ProjectSubmissionError('Lien symbolique de répertoire refusé.')
            dirnames.append(item.relative_to(root).as_posix())
            if len(names)+len(dirnames)>MAX_FILES:raise ProjectSubmissionError('Trop de fichiers ou répertoires dans le rendu.')
        for name in files:
            item=Path(base)/name;rel=item.relative_to(root).as_posix()
            if any(ord(c)<32 or ord(c)==127 for c in rel):raise ProjectSubmissionError('Nom de fichier non pris en charge.')
            st=item.lstat()
            if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:raise ProjectSubmissionError('Fichier non régulier, lien symbolique ou physique refusé : '+rel)
            names.append(rel)
            if len(names)+len(dirnames)>MAX_FILES:raise ProjectSubmissionError('Trop de fichiers ou répertoires dans le rendu.')
            fd=os.open(item,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
            with os.fdopen(fd,'rb') as f:
                before=os.fstat(f.fileno());data=f.read(MAX_FILE+1);after=os.fstat(f.fileno())
            if len(data)>MAX_FILE:raise ProjectSubmissionError('Fichier trop volumineux : '+rel)
            if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns) or len(data)!=after.st_size:
                raise ProjectUnavailable('Fichier modifié pendant la copie : '+rel)
            total+=len(data)
            if total>MAX_TOTAL:raise ProjectSubmissionError('Rendu trop volumineux.')
            target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    required=set(cfg.get('required_files',[]));missing=required-set(names)
    if missing:raise ProjectSubmissionError('Fichiers requis absents : '+', '.join(sorted(missing)))
    if cfg.get('exact_files',False):
        valid_dirs={str(p) for f in required for p in Path(f).parents if str(p)!='.'}
        extra=(set(names)-required)|(set(dirnames)-valid_dirs)
        if extra:raise ProjectSubmissionError('Fichiers supplémentaires : '+', '.join(sorted(extra)))
    return names

def _limits():
    resource.setrlimit(resource.RLIMIT_CPU,(90,90))
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def _norm_command(sandbox):
    found=shutil.which('norminette')
    if not found:return None,None
    p=Path(found).resolve();venv=p.parent.parent
    cfg=venv/'pyvenv.cfg'
    if sandbox:
        home=Path.home().resolve()
        protected={Path('/'),Path('/tmp'),Path('/var'),Path('/usr'),Path('/usr/local'),Path('/opt'),home,home/'.local',home/'.local'/'share'}
        if venv in protected or home.is_relative_to(venv) or cfg.is_symlink():
            raise ProjectUnavailable('Norminette doit être installée dans un environnement virtuel dédié ; dossier personnel large ou configuration symbolique refusés.')
    if not cfg.is_file() or not (venv/'bin'/'python').exists():return None,None
    return (['/opt/norminette/bin/python','-I','-B','-m','norminette'] if sandbox else [str(venv/'bin'/'python'),'-I','-B','-m','norminette']),venv


def _isolated_norm(stage,cfg,sandbox,command,venv):
    """Vérifier le style dans une phase séparée, sans exécuter le rendu.

    Le venv de Norminette n'est jamais monté dans la phase de compilation ni
    dans celle des programmes du rendu. Cette séparation ne rend pas fiable
    l'analyse d'un fichier ou d'un environnement Norminette non fiables.
    """
    filenames=cfg.get('style_files',[])
    if not filenames:return [{'not_applicable':True}]
    if not command:return [{'error':'Norminette indisponible.'}]
    deadline=time.monotonic()+90
    def run(args,timeout):
        remaining=deadline-time.monotonic()
        if remaining<=0:return {'error':'Délai global Norminette dépassé.'}
        if sandbox:
            bwrap=shutil.which('bwrap')
            if not bwrap:return {'error':'Bubblewrap introuvable pour Norminette.'}
            cmd=[bwrap,'--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr',
                 '--symlink','usr/bin','/bin','--symlink','usr/lib','/lib']
            if Path('/usr/lib64').exists():cmd+=['--symlink','usr/lib64','/lib64']
            cmd+=['--proc','/proc','--dev','/dev','--dir','/opt','--ro-bind',str(venv),'/opt/norminette',
                  '--ro-bind',str(stage),'/work','--size',str(16*1024*1024),'--tmpfs','/tmp',
                  '--chdir','/work','--clearenv','--setenv','PATH','/usr/bin:/bin','--setenv','LC_ALL','C','--',*command,*args]
        else:cmd=[*command,*args]
        env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'}
        try:
            with tempfile.TemporaryFile() as status, seccomp_fd() as sfd:
                passfds=()
                if sandbox:
                    extra=['--json-status-fd',str(status.fileno())]+(['--seccomp',str(sfd)] if sfd is not None else [])
                    cmd[1:1]=extra;passfds=(status.fileno(),) if sfd is None else (status.fileno(),sfd)
                code,out,err,timed=run_bounded(cmd,stage,min(timeout,remaining),env,_limits,
                                               pass_fds=passfds,max_stdout=65537,max_stderr=65537)
                status.seek(0);raw=status.read(8193)
            if timed or len(out)>65536 or len(err)>65536:return {'error':'Norminette : délai dépassé ou sortie trop volumineuse.'}
            if sandbox:
                events=[json.loads(line) for line in raw.decode('utf-8','strict').splitlines() if line.strip()]
                if (len(raw)>8192 or len(events)!=2 or not isinstance(events[0],dict) or
                    type(events[0].get('child-pid')) is not int or events[0]['child-pid']<=0 or
                    not isinstance(events[1],dict) or type(events[1].get('exit-code')) is not int or events[1]['exit-code']!=code):
                    return {'error':'Statut Bubblewrap Norminette incomplet.'}
            return {'code':code,'out':out,'err':err}
        except (OSError,ValueError,TypeError,UnicodeError,json.JSONDecodeError) as exc:
            return {'error':'Norminette indisponible : '+str(exc)[:300]}
    version=run(['--version'],15)
    version_text=version.get('out',b'')+b'\n'+version.get('err',b'')
    match=re.search(rb'\bnorminette\s+(\d+\.\d+\.\d+)\b',version_text,re.I)
    if version.get('error') or version.get('code')!=0 or not match or match.group(1)!=b'3.3.59':
        return [{'error':version.get('error','Norminette 3.3.59 indisponible.')}]
    styles=[]
    for name in filenames:
        args=['-f','json','--no-colors']+(['-R','CheckDefine'] if name in cfg.get('checkdefine',[]) else [])+['./'+name]
        result=run(args,15)
        if result.get('error'):
            styles.append({'error':name+' : '+result['error']});continue
        styles.append({'name':name,'code':result['code'],'timeout':False,'unavailable':False,
                       'out':base64.b64encode(result['out']).decode(),'err':base64.b64encode(result['err']).decode()})
    return styles

def evaluate_project(folder,exercise,spec,sandbox=False,sanitize=False):
    cfg=dict(spec['project']); checks=[]
    def add(status,name,message):
        s,n,m=status,safe_text(name),safe_text(message)
        checks.append({'status':s,'name':n,'message':m});progress.emit(s,n,m)
    def report():
        return build_report(exercise, spec, sandbox, checks)
    try:
        with tempfile.TemporaryDirectory(prefix='moulinette-projet-') as tmp:
            tmp=Path(tmp);stage=tmp/'input';stage.mkdir();work=tmp/'work';work.mkdir()
            names=snapshot_submission(folder,stage,cfg)
            if cfg.get('style_all_sources'):
                cfg['style_files']=[n for n in names if n.endswith(('.c','.h'))]
                if not any(n.endswith('.c') for n in cfg['style_files']):
                    raise ProjectSubmissionError('Aucun fichier C trouvé dans le rendu.')
            if cfg.get('build')=='auto_program':
                if 'Makefile' in names:
                    cfg['build']='make'
                else:
                    cfg['build']='cc'
                    cfg['sources']=[n for n in names if n.endswith('.c')]
                    cfg['link_program']=True
            add('pass','Fichiers attendus',f'{len(names)} fichier(s) copiés dans un espace de travail temporaire.')
            if exercise=='c11/ex05':
                src_map={n:(stage/n).read_bytes() for n in names if n.endswith(('.c','.h'))}
                add('info','Structure (indicative)',doop_hint(src_map))
            marker=secrets.token_bytes(16)
            if cfg.get('harness') is not None:
                cfg['harness']=cfg['harness'].replace('MARKER_BYTES',', '.join(str(b) for b in marker))
            cases=[]
            for c in cfg['cases']:
                c=dict(c);expected=c['expected']
                if not isinstance(expected,bytes):raise ProjectUnavailable('Test interne sans sortie binaire.')
                if c.pop('marker',False):expected+=marker
                c['expected']=expected.hex()
                if isinstance(c.get('stdin'),bytes):c['stdin']=c['stdin'].hex()
                if isinstance(c.get('expected_stderr'),bytes):c['expected_stderr']=c['expected_stderr'].hex()
                c['fixtures']={k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.get('fixtures',{}).items()}
                cases.append(c)
            cfg['cases']=cases
            progress.emit('plan','tests',str(len(cases)))
            # Ne pas exposer le venv Norminette à make, aux scripts ni au rendu.
            # Le style est évalué plus tard dans un autre processus/sandbox.
            norm_command,venv=_norm_command(sandbox) if cfg.get('style_files') else (None,None)
            cfg['norm_cmd']=None
            cfg['_isolated_job']=bool(sandbox)
            specpath=tmp/'project.json';specpath.write_text(json.dumps(cfg),encoding='utf-8')
            job=Path(__file__).with_name('project_job.py').resolve()
            if sandbox:
                bwrap=shutil.which('bwrap')
                if not bwrap:raise ProjectUnavailable('Bubblewrap introuvable ; aucun repli local.')
                cmd=[bwrap,'--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib']
                if Path('/usr/lib64').exists():cmd+=['--symlink','usr/lib64','/lib64']
                cc=shutil.which('cc')
                if not cc or not Path(cc).resolve().is_relative_to('/usr'):
                    raise ProjectUnavailable('Compilateur système introuvable ou hors de /usr.')
                cmd+=['--dir','/etc','--dir','/etc/alternatives','--symlink',str(Path(cc).resolve()),'/etc/alternatives/cc']
                cmd+=['--dir','/input','--ro-bind',str(stage),'/input','--ro-bind',str(specpath),'/project.json','--ro-bind',str(job),'/project_job.py',
                      '--size',str(32*1024*1024),'--tmpfs','/work','--size',str(16*1024*1024),'--tmpfs','/tmp','--proc','/proc','--dev','/dev']
                cmd+=['--chdir','/work','--clearenv','--setenv','PATH','/usr/bin:/bin','--setenv','LC_ALL','C','--','/usr/bin/python3','-I','-B','/project_job.py','/input','/work','/project.json']
            else:
                cmd=['/usr/bin/python3','-I','-B',str(job),str(stage),str(work),str(specpath)]
            env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'}
            with tempfile.TemporaryFile() as status, seccomp_fd() as sfd:
                passfds=()
                if sandbox:
                    extra=['--json-status-fd',str(status.fileno())]+(['--seccomp',str(sfd)] if sfd is not None else [])
                    cmd[1:1]=extra;passfds=(status.fileno(),) if sfd is None else (status.fileno(),sfd)
                code,out,err,timed=run_bounded(cmd,tmp,110,env,_limits,pass_fds=passfds,max_stdout=2*1024*1024,max_stderr=8193)
                status.seek(0);raw=status.read(8193)
            if timed or code!=0 or err.strip() or len(out)>=2*1024*1024:
                raise ProjectUnavailable('Superviseur de projet indisponible : '+err.decode('utf-8','replace')[:300])
            if sandbox:
                events=[json.loads(line) for line in raw.decode('utf-8','strict').splitlines() if line.strip()]
                if len(events)!=2 or type(events[0].get('child-pid')) is not int or events[1].get('exit-code')!=code:
                    raise ProjectUnavailable('Statut Bubblewrap incomplet.')
            data=json.loads(out.decode('utf-8','strict'))
            if 'error' in data:raise ProjectUnavailable('Superviseur de projet : '+str(data['error'])[:400])
            for c in data['checks']:
                if set(c)!={'status','name','message'} or c['status'] not in ('pass','fail','info','unavailable'):
                    raise ProjectUnavailable('Rapport de projet incohérent.')
                add(c['status'],c['name'],c['message'])
            if sanitize and not any(c['status'] in ('fail','unavailable') for c in checks):
                add('info','Sanitizer (optionnel)','Vérification sanitizer optionnelle non applicable aux exercices multi-fichiers/Makefiles sans modifier leur chaîne de compilation ; résultat habituel inchangé.')
            styles=data['styles']
            if styles and styles!=[{'not_applicable':True}]:
                styles=_isolated_norm(stage,cfg,sandbox,norm_command,venv)
            if styles:
                statuses=[];messages=[]
                if styles==[{'not_applicable':True}]:
                    add('info','Norminette adaptée','Aucun fichier C ou en-tête du rendu à vérifier.')
                for item in styles:
                    if item.get('not_applicable'):continue
                    if 'error' in item:statuses.append('unavailable');messages.append(item['error']);continue
                    if item['timeout'] or item['unavailable'] or item['code'] not in (0,1):
                        statuses.append('unavailable');messages.append(item['name']+' : Norminette indisponible.');continue
                    out=base64.b64decode(item['out'],validate=True);err=base64.b64decode(item['err'],validate=True)
                    if err.strip() or len(out)>65536:status='unavailable';message='Sortie Norminette inattendue.'
                    else:status,message=parse_norm_result(out,item['code'])
                    statuses.append(status);messages.append(item['name']+' : '+message)
                if statuses:
                    status='fail' if 'fail' in statuses else 'unavailable' if 'unavailable' in statuses else 'pass'
                    add(status,'Norminette adaptée',' ; '.join(messages)[:6000])
            elif not any(c['status'] in ('fail','unavailable') for c in checks):
                add('unavailable','Norminette adaptée','Aucun fichier style vérifié.')
    except ProjectSubmissionError as exc:add('fail','Fichiers attendus',str(exc))
    except (ProjectUnavailable,OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:add('unavailable','Projet',str(exc)[:800])
    limits='Prototype multi-fichiers ; code de confiance seulement. Analyse des appels partielle ; réseau et noyau non garantis sûrs.'
    if exercise=='c11/ex05':
        limits+=' Tableau de pointeurs de fonctions demandé par le sujet non vérifié automatiquement.'
    if exercise.startswith('c10/'):
        limits+=' Options, erreurs, gestion des grands fichiers et règles Makefile non vérifiées exhaustivement.'
    add('info','Limites',limits)
    return report()
