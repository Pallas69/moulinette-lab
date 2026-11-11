"""Explications indicatives à partir des rapports enregistrés, sans relire le code."""
import ast
import re
from collections import Counter
from .exercise_catalog import ALL_EXERCISES, EXERCISES, PISCINES

_IDENTIFIER=r'[A-Za-z_][A-Za-z_0-9]*'
_QUOTE=r"['‘’`\"]"
_PATTERN=re.compile(r'_Generic\(\s*&('+_IDENTIFIER+r')\s*,\s*([A-Za-z_][A-Za-z_0-9\s*]*?)\s*\(\*\)\(([^()]*)\)\s*:')

_FILES_NAMES={'Dossier','Fichiers attendus','Fichiers supplémentaires','Fichier attendu',
              'Taille du fichier','Lecture du fichier','Projet'}
_BUILD_NAMES={'Compilation','Compilateur','Recompilation','Adaptation compilation','Édition des liens',
              'Prototype','Prototype et liaison','Fonctions externes','Plateforme',
              'Bubblewrap expérimental','Récursivité (indicative)','Structure (indicative)'}
_BYTES=r"""b'(?:[^'\\]|\\.)*'|b"(?:[^"\\]|\\.)*\""""
_EXPECTED=re.compile(r'Attendu\s*:?\s*('+_BYTES+r')(?:\s*\((\d+) octet)?')
_OBTAINED=re.compile(r'obtenu\s*:?\s*('+_BYTES+r')(?:\s*\((\d+) octet)?')
_NORM_ITEM=re.compile(r'([A-Z][A-Z0-9_]+) ligne (\d+|\?) col (\d+|\?): (.*)')
_NORM_FILE=re.compile(r'(\S+\.[ch]) : Norminette')


def stage_of(name):
    """Classe un contrôle dans l'une des quatre étapes exécutées par le moteur."""
    if not isinstance(name, str):return 'tests'
    if name.startswith('Norminette'):return 'norm'
    if name in _FILES_NAMES:return 'files'
    if name in _BUILD_NAMES:return 'build'
    if name=='Limites':return 'meta'
    return 'tests'


def summarize_stages(checks):
    """Récapitule l'état des 4 étapes dans l'ordre réel d'exécution du moteur."""
    counts={k:{'pass':0,'fail':0,'unavailable':0,'info':0} for k in ('files','build','tests','norm')}
    for c in (checks or []):
        if not isinstance(c,dict):continue
        stage=stage_of(c.get('name',''))
        status=c.get('status','info')
        if stage in counts and status in counts[stage]:
            counts[stage][status]+=1
    specs=(('files','01 · Fichiers'),('build','02 · Compilation'),
           ('tests','03 · Tests'),('norm','04 · Norminette'))
    out=[]
    for key,title in specs:
        c=counts[key]
        total=c['pass']+c['fail']+c['unavailable']
        if c['fail']:cls,label='bad','À revoir'
        elif c['unavailable']:cls,label='pending','Incomplet'
        elif c['pass']:cls,label='ok','Validé'
        else:cls,label='neutral','Non exécuté'
        detail=f"{c['pass']} ✓ · {c['fail']} ✗" if total else ('Info' if c['info'] else '—')
        out.append({'key':key,'title':title,'cls':cls,'label':label,'detail':detail,'total':total,'pass':c['pass'],'fail':c['fail']})
    return out


def summarize_history(history, piscine='c'):
    """Calcule la progression par module et la chronologie à partir de l'historique réel."""
    latest={x['exercise']:x for x in history.get('latest',[]) if isinstance(x,dict) and 'exercise' in x}
    catalog=PISCINES.get(piscine, EXERCISES)
    modules={}
    for ex in sorted(catalog):
        mod=ex.split('/')[0]
        entry=modules.setdefault(mod,{'module':mod,'label':mod.upper(),'done':0,'failed':0,'incomplete':0,'total':0})
        entry['total']+=1
        res=latest.get(ex,{}).get('result')
        if res=='passed':entry['done']+=1
        elif res=='failed':entry['failed']+=1
        elif res=='incomplete':entry['incomplete']+=1
    mod_list=[]
    for mod in sorted(modules):
        m=modules[mod]
        pct=round(m['done']/m['total']*100) if m['total'] else 0
        cls='ok' if m['done']==m['total'] and m['total']>0 else ('pending' if (m['done'] or m['failed'] or m['incomplete']) else 'neutral')
        mod_list.append({**m,'percent':pct,'cls':cls})
    recent=list(history.get('recent',[]))
    counts={'passed':0,'failed':0,'incomplete':0}
    timeline=[]
    cats={'passed':('ok','Réussi'),'failed':('bad','À revoir'),'incomplete':('pending','Incomplet')}
    for row in reversed(recent):
        if not isinstance(row,dict):continue
        r=row.get('result','')
        if r in counts:counts[r]+=1
        cls,lbl=cats.get(r,('neutral','Inconnu'))
        when=str(row.get('created_at','')).replace('T',' ')[:16]
        timeline.append({'exercise':str(row.get('exercise','')),'cls':cls,'label':lbl,'when':when})
    return {'modules':mod_list,'counts':counts,'timeline':timeline,'recent_total':len(timeline)}


def parse_diff(message):
    """Extrait attendu/obtenu d'un message de test via ast.literal_eval."""
    if not isinstance(message,str):return None
    e=_EXPECTED.search(message);o=_OBTAINED.search(message)
    if not e or not o:return None
    try:
        expected=ast.literal_eval(e.group(1))
        actual=ast.literal_eval(o.group(1))
    except (ValueError,SyntaxError):
        return None
    if not isinstance(expected,bytes) or not isinstance(actual,bytes):
        return None
    exp_total=int(e.group(2)) if e.group(2) else len(expected)
    act_total=int(o.group(2)) if o.group(2) else len(actual)
    return {'expected':list(expected),'actual':list(actual),
            'expected_total':exp_total,'actual_total':act_total,
            'truncated':exp_total>len(expected) or act_total>len(actual)}


def parse_norm(message, default_file=None):
    """Extrait les diagnostics `NOM ligne N col M: texte` d'un message Norminette."""
    if not isinstance(message,str):return []
    items=[];current=default_file
    for part in message.split(' ; '):
        f=_NORM_FILE.search(part)
        if f:current=f.group(1)
        m=_NORM_ITEM.search(part)
        if m and m.group(2)!='?':
            items.append({'file':current,'code':m.group(1),'line':int(m.group(2)),
                          'col':int(m.group(3)) if m.group(3)!='?' else None,'text':m.group(4)})
    return items


def expected_signature(exercise):
    spec=ALL_EXERCISES.get(exercise, {})
    prototype=spec.get('prototype') or spec.get('project',{}).get('prototype') or ''
    matches=_PATTERN.findall(prototype)
    # Les prototypes plus complexes ou multiples ne sont pas devinés.
    if len(matches)!=1:return None
    name,ret,args=matches[0]
    if not re.fullmatch(r'[A-Za-z_0-9\s,*]*',args):return None
    return ' '.join(ret.split())+' '+name+'('+(' '.join(args.split()) or 'void')+');'


def explanations(exercise, check):
    if check.get('name')!='Compilation' or check.get('status')!='fail':return []
    text=str(check.get('message',''))[:4000]; result=[];function=None
    for line in text.splitlines():
        context=re.search(r'In function\s+'+_QUOTE+r'('+_IDENTIFIER+r')'+_QUOTE,line)
        if context:function=context.group(1)
        unused=re.search(r'unused variable\s+'+_QUOTE+r'('+_IDENTIFIER+r')'+_QUOTE,line)
        if unused:
            where=(' dans '+function) if function else ''
            result.append('La variable « '+unused.group(1)+' »'+where+' est déclarée mais jamais utilisée. Supprimez-la si elle est inutile, ou utilisez-la si elle est nécessaire.')
        unused_param=re.search(r'unused parameter\s+'+_QUOTE+r'('+_IDENTIFIER+r')'+_QUOTE,line)
        if unused_param:
            where=(' dans '+function) if function else ''
            result.append('Le paramètre « '+unused_param.group(1)+' »'+where+' est déclaré mais non utilisé. Vérifiez si la fonction doit l’utiliser ou comment traiter ce paramètre selon le sujet.')
        implicit=re.search(r'implicit declaration of function\s+'+_QUOTE+r'('+_IDENTIFIER+r')'+_QUOTE,line)
        if implicit:
            result.append('Le compilateur ne voit pas de déclaration pour « '+implicit.group(1)+' ». Vérifiez le prototype, les en-têtes nécessaires et l’orthographe du nom.')
        if re.search(r'expected\s+'+_QUOTE+r';'+_QUOTE,line):
            result.append('Le compilateur attend un point-virgule. Vérifiez la ligne signalée et la fin de l’instruction précédente.')
        if 'control reaches end of non-void function' in line:
            who=('La fonction « '+function+' »') if function else 'Une fonction'
            result.append(who+' est censée retourner une valeur, mais peut arriver à sa fin sans en retourner. Vérifiez son type et ses instructions return.')
    signature=expected_signature(exercise)
    if signature:
        result.append('Prototype attendu pour cet exercice : '+signature+' La compilation a échoué ; ce prototype n’a pas encore été vérifié.')
        if re.search(r'In function\s+'+_QUOTE+r'main'+_QUOTE,text) and not ALL_EXERCISES.get(exercise, {}).get('project'):
            result.append('Le compilateur mentionne main. Pour cet exercice de fonction, gardez votre programme main de test hors du fichier rendu : le correcteur fournit son propre programme de test.')
    return list(dict.fromkeys(result))[:8]


def compare_checks(current, previous):
    """Comparer seulement des contrôles nommés uniques et réellement exécutés."""
    old=previous.get('checks',[]);new=current.get('checks',[])
    old_counts=Counter(c.get('name') for c in old if isinstance(c,dict))
    new_counts=Counter(c.get('name') for c in new if isinstance(c,dict))
    oldmap={c['name']:c.get('status') for c in old if isinstance(c,dict) and 'name' in c and old_counts[c['name']]==1}
    improved=[];regressed=[];indeterminate=[]
    for c in new:
        if not isinstance(c,dict):continue
        name=c.get('name');status=c.get('status');before=oldmap.get(name)
        if not isinstance(name,str) or new_counts[name]!=1 or before is None:continue
        if before=='fail' and status=='pass':improved.append(name)
        elif before=='pass' and status=='fail':regressed.append(name)
        elif before!=status and ('unavailable' in (before,status)):indeterminate.append(name)
    return improved,regressed,indeterminate
