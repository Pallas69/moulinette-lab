"""Worker de compilation multi-fichiers : usage interne, prototypes en cours.

Lancé dans Bubblewrap par project_engine ; tous les fichiers écrits sont dans
un répertoire de travail temporaire. Ne prétend pas sécuriser du code hostile.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import signal
import select
import time
from pathlib import Path

CAP=65536

# Activé seulement dans le namespace PID Bubblewrap : si ce superviseur meurt,
# la destruction du namespace termine aussi ses groupes enfants. En local, on
# garde le groupe externe afin que le parent puisse le nettoyer globalement.
ISOLATED_JOB = False

class CleanupUnconfirmed(Exception):
    pass

def _wait_group_quiet(pgid, timeout=.5):
    """Observer /proc pendant que le PID du chef reste réservé.

    Couvre le groupe et la session du chef ; les nouvelles sessions (setsid) hors
    namespace PID ne sont pas couvertes. Un état illisible n'est jamais supposé vide.
    """
    deadline=time.monotonic()+timeout
    while True:
        active=False
        try:
            with os.scandir('/proc') as entries:
                pids=[entry.name for entry in entries if entry.name.isdigit()]
            for pid in pids:
                try: raw=Path('/proc',pid,'stat').read_text()
                except (FileNotFoundError,ProcessLookupError): continue
                tail=raw.rsplit(')',1)[1].split()
                if len(tail)<4:raise ValueError('stat incomplet')
                state,group,session=tail[0],int(tail[2]),int(tail[3])
                if (group==pgid or session==pgid) and state not in ('Z','X','x'):
                    if group!=pgid:
                        try: os.kill(int(pid),signal.SIGKILL)
                        except ProcessLookupError: continue
                    active=True
        except (OSError,ValueError,IndexError) as exc:
            raise CleanupUnconfirmed('Observation du groupe impossible : '+str(exc)) from exc
        if not active:return
        if time.monotonic()>=deadline:
            raise CleanupUnconfirmed('Arrêt des descendants du groupe non confirmé.')
        time.sleep(.01)

def _execute_isolated(args, cwd, stdin, timeout, out, err):
    required=('waitid','P_PID','WEXITED','WNOHANG','WNOWAIT')
    if not all(hasattr(os,n) for n in required):
        raise CleanupUnconfirmed('waitid indisponible ; commande non lancée.')
    p = subprocess.Popen(args,cwd=cwd,stdin=subprocess.PIPE,stdout=out,stderr=err,
                         start_new_session=True,bufsize=0)
    deadline=time.monotonic()+timeout
    timed=False
    identity_safe=True
    original=None
    cleanup_error=None
    try:
        os.set_blocking(p.stdin.fileno(),False)
        pending=memoryview(stdin)
        while True:
            try:
                finished=os.waitid(os.P_PID,p.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
            except ChildProcessError as exc:
                identity_safe=False
                raise CleanupUnconfirmed('État du processus perdu ; groupe non signalé.') from exc
            if finished is not None: break
            remaining=deadline-time.monotonic()
            if remaining<=0:
                timed=True
                break
            if not pending and p.stdin is not None:
                p.stdin.close()
            if pending:
                _,ready,_=select.select([], [p.stdin], [], min(.025,remaining))
                if ready:
                    try: n=os.write(p.stdin.fileno(),pending[:65536])
                    except BrokenPipeError:
                        pending=memoryview(b'');p.stdin.close()
                    else: pending=pending[n:]
            else:
                time.sleep(min(.025,remaining))
    finally:
        original=sys.exc_info()[1]
        # Le chef n'a pas encore été récolté, son PID ne peut pas être recyclé.
        if identity_safe:
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            except OSError as exc: cleanup_error='Arrêt du groupe impossible : '+str(exc)
            if cleanup_error is None:
                try: _wait_group_quiet(p.pid)
                except CleanupUnconfirmed as exc: cleanup_error=str(exc)
        if p.stdin is not None and not p.stdin.closed:p.stdin.close()
        try:p.wait(timeout=.5)
        except subprocess.TimeoutExpired:
            cleanup_error=(cleanup_error+' ' if cleanup_error else '')+'Arrêt du processus non confirmé.'
        if cleanup_error:
            raise CleanupUnconfirmed(cleanup_error) from original
    return p.returncode,timed

def execute(args, cwd, stdin=b'', timeout=10):
    # Fichiers temporaires bornés par le parent et lecture plafonnée.
    import tempfile
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            if ISOLATED_JOB:
                code,timeout_hit=_execute_isolated(args,cwd,stdin,timeout,out,err)
            else:
                p=subprocess.Popen(args,cwd=cwd,stdin=subprocess.PIPE,stdout=out,stderr=err)
                try:p.communicate(stdin,timeout=timeout);timeout_hit=False
                except subprocess.TimeoutExpired:
                    p.kill();p.communicate(timeout=2);timeout_hit=True
                code=p.returncode
        except CleanupUnconfirmed:
            raise
        except (OSError,subprocess.SubprocessError) as exc:
            return {'code':None,'out':b'','err':str(exc).encode(),'timeout':False,'unavailable':True}
        out.seek(0);err.seek(0);o=out.read(CAP+1);e=err.read(CAP+1)
        return {'code':code,'out':o,'err':e,'timeout':timeout_hit,'unavailable':False}

def msg(r):
    if r['unavailable']: return 'Outil indisponible : '+r['err'].decode('utf-8','replace')[:600]
    if r['timeout']: return 'Délai dépassé.'
    if len(r['out'])>CAP or len(r['err'])>CAP:return 'Sortie tronquée.'
    return (r['err'] or r['out']).decode('utf-8','replace')[:1800] or f"Code {r['code']}"

def fail_status(r):
    return 'unavailable' if r['unavailable'] or r['timeout'] or len(r['out'])>CAP or len(r['err'])>CAP else 'fail'

def main():
    global ISOLATED_JOB
    inp=Path(sys.argv[1]); work=Path(sys.argv[2]); cfg=json.loads(Path(sys.argv[3]).read_text())
    ISOLATED_JOB = cfg.pop('_isolated_job', False) is True
    work.mkdir(parents=True,exist_ok=True)
    for src in inp.rglob('*'):
        if src.is_file():
            dst=work/src.relative_to(inp);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    for name,content in cfg.get('provided_files',{}).items():
        dst=work/name;dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists(): raise ValueError('Un fichier fourni par le harnais est présent dans le rendu : '+name)
        dst.write_text(content,encoding='utf-8')
    checks=[]; styles=[]
    def add(status,name,message):checks.append({'status':status,'name':name,'message':message})
    strategy=cfg['build']; objects=[]; adaptations=[]
    standard=cfg.get('compile_standard')
    if standard not in (None, 'c11'):raise ValueError('Standard C non pris en charge')
    standard_args=['-std='+standard] if standard else []
    if standard:adaptations.append('Compilation des sources en C11 pour les prototypes historiques du sujet.')
    if strategy=='cc':
        for i,name in enumerate(cfg.get('sources',[])):
            obj=f'.ml-submission-{i}.o'
            result=execute(['cc','-Wall','-Wextra','-Werror',*standard_args,'-fno-builtin','-c',name,'-o',obj],work)
            if result['code']!=0 or result['timeout'] or result['unavailable']:
                add(fail_status(result),'Compilation',name+' : '+msg(result));return {'checks':checks,'styles':styles}
            objects.append(obj)
        add('pass','Compilation','Tous les fichiers C du rendu ont été compilés séparément.' if objects else 'En-tête vérifié avec le harnais de compilation.')
    elif strategy in ('make','script'):
        command=(['make','--no-print-directory']+cfg.get('make_args',[])) if strategy=='make' else ['/bin/sh',cfg['script']]
        result=execute(command,work,timeout=25)
        if result['code']!=0 or result['timeout'] or result['unavailable']:
            add(fail_status(result),'Compilation',('Makefile : ' if strategy=='make' else 'Script : ')+msg(result));return {'checks':checks,'styles':styles}
        if cfg.get('make_compile_pattern') and not re.search(cfg['make_compile_pattern'],result['out'].decode('utf-8','replace'),re.MULTILINE):
            add('fail','Compilation','Commandes de compilation attendues non visibles ou options absentes.');return {'checks':checks,'styles':styles}
        add('pass','Compilation',('Makefile' if strategy=='make' else 'Script')+' exécuté dans le répertoire de travail temporaire.')
        objects=[str(p.relative_to(work)) for p in work.rglob('*.o') if p.is_file() and not p.is_symlink()]
    else: raise ValueError('Stratégie non reconnue')
    if not objects and cfg.get('fallback_inspection'):
        # Certains Makefiles lient directement leurs fichiers C. Ces objets
        # séparés rendent l'analyse indicative : ils ne sont pas ceux liés au binaire.
        for i,name in enumerate(n for n in cfg.get('style_files',[]) if n.endswith('.c')):
            obj=f'.ml-inspect-{i}.o'
            inspect=execute(['cc','-Wall','-Wextra','-Werror',*standard_args,'-fno-builtin','-I.','-Iincludes','-c',name,'-o',obj],work)
            if inspect['code']!=0 or inspect['timeout'] or inspect['unavailable']:
                add('unavailable','Fonctions externes','Compilation indicative impossible pour '+name+' : '+msg(inspect));return {'checks':checks,'styles':styles}
            objects.append(obj)
        if objects:add('info','Convention de test','Les objets analysés ont été recompilés séparément ; ils ne sont pas ceux liés au programme Makefile.')
    # Un script peut supprimer ses objets après création de la bibliothèque.
    # Les extraire dans le bac permet d'analyser les membres effectivement liés.
    for idx,archive in enumerate(cfg.get('inspect_archives',[])):
        arch=(work/archive).resolve()
        if not arch.is_file() or not arch.is_relative_to(work.resolve()):
            add('fail','Compilation','Bibliothèque attendue absente : '+archive);return {'checks':checks,'styles':styles}
        listing=execute(['ar','t',str(arch)],work)
        if listing['code']!=0 or listing['timeout'] or listing['unavailable']:
            add(fail_status(listing),'Compilation','Lecture de la bibliothèque impossible : '+msg(listing));return {'checks':checks,'styles':styles}
        members=listing['out'].decode('utf-8','strict').splitlines()
        if not members or len(members)>80 or len(set(members))!=len(members) or any(not m.endswith('.o') or '/' in m or m in ('.','..') for m in members):
            add('unavailable','Fonctions externes','Membres de bibliothèque inattendus.');return {'checks':checks,'styles':styles}
        dest=work/f'.ml-archive-{idx}';dest.mkdir()
        extraction=execute(['ar','x',str(arch)],dest)
        if extraction['code']!=0 or extraction['timeout'] or extraction['unavailable']:
            add(fail_status(extraction),'Fonctions externes','Extraction de la bibliothèque impossible.');return {'checks':checks,'styles':styles}
        objects.extend(str((dest/m).relative_to(work)) for m in members)
    # Examiner les objets d'origine avant toute adaptation, puis les éventuels
    # objets de remplacement : une vraie fonction interdite ne doit pas être
    # masquée par la présence simultanée d'un symbole de protection de pile.
    def scan(paths):
        undefined=[]; defined=set()
        for obj in paths:
            u=execute(['nm','-u',obj],work);d=execute(['nm','-g','--defined-only',obj],work)
            if any(r['code']!=0 or r['timeout'] or r['unavailable'] or r['err'].strip() or len(r['out'])>CAP for r in (u,d)):
                return None
            try:
                for line in u['out'].decode('ascii','strict').splitlines():
                    parts=line.split()
                    if len(parts)!=2 or parts[0] not in ('U','w','v') or '@' in parts[1]:return None
                    undefined.append(parts[1])
                for line in d['out'].decode('ascii','strict').splitlines():
                    parts=line.split()
                    if len(parts)!=3 or len(parts[1])!=1 or '@' in parts[2]:return None
                    defined.add(parts[2])
            except UnicodeError:return None
        allowed=set(cfg.get('allowed_functions',[]))|set(cfg.get('support_functions',[]))|defined|{'_GLOBAL_OFFSET_TABLE_'}
        return set(undefined)-allowed
    if not objects and cfg.get('require_objects',True) and not cfg.get('skip_external_inspection',False):
        add('unavailable','Fonctions externes','Aucun objet à analyser après la compilation.');return {'checks':checks,'styles':styles}
    prohibited=scan([] if cfg.get('skip_external_inspection') else objects)
    if prohibited is None:
        add('unavailable','Fonctions externes','Format nm inattendu ou outil indisponible.');return {'checks':checks,'styles':styles}
    canary={'__stack_chk_fail','__stack_chk_guard'}
    forbidden=prohibited-canary
    if forbidden:
        add('fail','Fonctions externes','Symboles non autorisés détectés : '+', '.join(sorted(forbidden)));return {'checks':checks,'styles':styles}
    if prohibited&canary:
        # Avec une archive d'un script, on ne peut pas remplacer les membres
        # tout en prétendant tester la bibliothèque produite par ce script.
        if cfg.get('inspect_archives'):
            add('unavailable','Fonctions externes','Protection de pile ambiguë dans une bibliothèque ; aucune substitution silencieuse.');return {'checks':checks,'styles':styles}
        sources=cfg.get('sources',[]) if strategy=='cc' else [n for n in cfg.get('style_files',[]) if n.endswith('.c')]
        if not sources:
            add('unavailable','Fonctions externes','Protection de pile ambiguë ; sources de recompilation indisponibles.');return {'checks':checks,'styles':styles}
        alternate=[]
        for i,name in enumerate(sources):
            obj=f'.ml-nocanary-{i}.o'
            result=execute(['cc','-Wall','-Wextra','-Werror',*standard_args,'-fno-builtin','-fno-stack-protector',
                            '-I.','-Iincludes','-c',name,'-o',obj],work)
            if result['code']!=0 or result['timeout'] or result['unavailable'] or len(result['out'])>CAP or len(result['err'])>CAP:
                add('unavailable','Fonctions externes','Recompilation sans protection de pile impossible pour '+name+' : '+msg(result));return {'checks':checks,'styles':styles}
            alternate.append(obj)
        alt_prohibited=scan(alternate)
        if alt_prohibited is None:
            add('unavailable','Fonctions externes','Analyse nm des objets recompilés impossible.');return {'checks':checks,'styles':styles}
        alt_forbidden=alt_prohibited-canary
        if alt_forbidden:
            add('fail','Fonctions externes','Symboles non autorisés dans les objets recompilés : '+', '.join(sorted(alt_forbidden)));return {'checks':checks,'styles':styles}
        if alt_prohibited&canary:
            add('unavailable','Fonctions externes','Symbole de protection de pile toujours présent après recompilation : '+', '.join(sorted(alt_prohibited&canary)));return {'checks':checks,'styles':styles}
        if strategy=='cc':
            # Les objets recontrôlés sont ceux liés au programme/harnais.
            objects=alternate
            adaptations.append('Rendu recompilé avec -fno-stack-protector : protection de pile désactivée pour les objets liés et testés.')
        else:
            # L'exécutable du Makefile reste celui d'origine. La comparaison
            # est indicative : les objets alternatifs ne sont pas ceux liés.
            adaptations.append('Objets recompilés pour analyse avec -fno-stack-protector ; analyse indicative : ils ne sont pas ceux liés au programme Makefile, dont la protection reste inchangée.')
    if adaptations:add('info','Adaptation compilation',' '.join(adaptations))
    add('info','Fonctions externes',('Fichiers source fournis par le harnais : contrôle des fonctions externes non applicable au Makefile.' if cfg.get('skip_external_inspection') else 'Analyse des objets et de leurs définitions internes : contrôle partiel, pas une garantie.' if objects else 'Aucun objet étudiant : contrôle des appels non applicable à cet en-tête.'))
    if cfg.get('prototype'):
        (work/'.ml-prototype.c').write_text(cfg['prototype'])
        r=execute(['cc','-Wall','-Wextra','-Werror','-std=c11','-I.','-c','.ml-prototype.c','-o','.ml-prototype.o'],work)
        if r['code']!=0 or r['timeout'] or r['unavailable']:
            add(fail_status(r),'Prototype',msg(r));return {'checks':checks,'styles':styles}
    binary=cfg['binary']
    if cfg.get('harness') is not None:
        (work/'.ml-harness.c').write_text(cfg['harness'])
        support=[]
        if cfg.get('support'):
            (work/'.ml-support.c').write_text(cfg['support']);support=['.ml-support.c']
        r=execute(['cc','-Wall','-Wextra','-Werror','-std=c11','-I.','.ml-harness.c',*support,*cfg.get('link_inputs',objects),'-o',binary],work)
        if r['code']!=0 and not r['timeout'] and not r['unavailable'] and strategy=='cc' and not cfg.get('link_inputs') and b'multiple definition of' in r['err'] and b'main' in r['err']:
            nomain_objs=[]
            extra_flags=['-fno-stack-protector'] if any(o.startswith('.ml-nocanary-') for o in objects) else []
            for i,name in enumerate(cfg.get('sources',[])):
                obj=f'.ml-nomain-{i}.o'
                rc=execute(['cc','-Wall','-Wextra','-Werror',*standard_args,'-fno-builtin',*extra_flags,'-Dmain=__moulinette_student_main','-Wno-unused-function','-Wno-return-type','-I.','-Iincludes','-c',name,'-o',obj],work)
                if rc['code']==0 and not rc['timeout'] and not rc['unavailable']:
                    nomain_objs.append(obj)
            if len(nomain_objs)==len(cfg.get('sources',[])):
                objects=nomain_objs
                r=execute(['cc','-Wall','-Wextra','-Werror','-std=c11','-I.','.ml-harness.c',*support,*objects,'-o',binary],work)
                if r['code']==0 and not r['timeout'] and not r['unavailable']:
                    add('info','Adaptation compilation','Fonction main() de test détectée dans le fichier et neutralisée pour lier le harnais (retirez main() pour un rendu 42 strict).')
        if r['code']!=0 or r['timeout'] or r['unavailable']:
            add(fail_status(r),'Édition des liens',msg(r));return {'checks':checks,'styles':styles}
    elif cfg.get('link_program'):
        r=execute(['cc','-Wall','-Wextra','-Werror','-std=c11',*objects,'-o',binary],work)
        if r['code']!=0 or r['timeout'] or r['unavailable']:
            add(fail_status(r),'Édition des liens',msg(r));return {'checks':checks,'styles':styles}
    elif not (work/binary).is_file():
        add('fail','Édition des liens','Programme attendu absent après construction : '+binary);return {'checks':checks,'styles':styles}
    add('pass','Prototype et liaison','Liaison des objets inspectés et prototype vérifié.' if cfg.get('prototype') else 'Programme construit ; prototype non vérifié séparément.')
    for case in cfg['cases']:
        for path,content in case.get('fixtures',{}).items():
            f=work/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(bytes.fromhex(content))
        command=(['make','--no-print-directory',*case.get('argv',[])] if case.get('runner')=='make'
                 else [str((work/binary).resolve()),*case.get('argv',[])])
        r=execute(command,work,bytes.fromhex(case.get('stdin','')),case.get('timeout',2))
        expected=bytes.fromhex(case['expected'])
        expected_err=bytes.fromhex(case['expected_stderr']) if 'expected_stderr' in case else None
        missing=[x for x in case.get('must_exist',[]) if not (work/x).exists()]
        unexpected=[x for x in case.get('must_absent',[]) if (work/x).exists()]
        wrong_out=(not case.get('ignore_stdout',False) and r['out']!=expected) or (case.get('stdout_nonempty',False) and not r['out'].strip())
        codes=case.get('codes',[case.get('code',0)])
        if (r['code'] not in codes or wrong_out or (expected_err is not None and r['err']!=expected_err)
            or missing or unexpected or r['timeout'] or r['unavailable']):
            detail=f"Attendu {expected[:80]!r}, obtenu {r['out'][:80]!r}, code {r['code']}. "
            if missing:detail+='Fichiers absents : '+', '.join(missing)+'. '
            if unexpected:detail+='Fichiers non supprimés : '+', '.join(unexpected)+'. '
            add(fail_status(r),'Test '+case['label'],detail+msg(r))
            if r['timeout'] or r['unavailable']:
                return {'checks':checks,'styles':styles}
        else:add('pass','Test '+case['label'],'Sortie, code de retour et fichiers attendus.')
    # La phase de style est exécutée séparément par le parent.
    styles.append({'requires_norm':True} if cfg.get('style_files') else {'not_applicable':True})
    return {'checks':checks,'styles':styles}

if __name__=='__main__':
    try: print(json.dumps(main(),ensure_ascii=True,separators=(',',':')))
    except Exception as exc: print(json.dumps({'error':type(exc).__name__+': '+str(exc)[:500]},ensure_ascii=True,separators=(',',':')))
