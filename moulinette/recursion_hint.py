"""Indices syntaxiques non bloquants, pas une analyse complète du langage C.

Les données analysées sont celles déjà copiées pour la correction. Les macros,
les déclarations complexes, les pointeurs et les branches inactives peuvent
cacher ou simuler un appel. Jamais de conclusion de conformité.
"""
import re

TARGETS = {
    'c05/ex01': 'ft_recursive_factorial',
    'c05/ex03': 'ft_recursive_power',
    'c05/ex04': 'ft_fibonacci',
    'c05/ex08': 'ft_ten_queens_puzzle',
}
MAX_TOKENS = 65536
MAX_FUNCTIONS = 512
_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z_0-9]*$')
_MASK = re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.DOTALL)
_TOKEN = re.compile(r'[A-Za-z_][A-Za-z_0-9]*|[(){};]|[^\s]')


def _masked(text):
    # Maintenir les fins de ligne pour reconnaître les directives et leurs suites.
    text = _MASK.sub(lambda m: ''.join('\n' if c == '\n' else ' ' for c in m.group()), text)
    lines=[]
    continued=False
    for line in text.splitlines(keepends=True):
        directive=continued or line.lstrip().startswith('#')
        if directive:
            continued=line.rstrip('\r\n').rstrip().endswith('\\')
            lines.append('\n' if line.endswith('\n') else '')
        else:
            lines.append(line)
    return ''.join(lines)


def _closing(tokens, start, opening, closing):
    depth=0
    for i in range(start,len(tokens)):
        if tokens[i]==opening:depth+=1
        elif tokens[i]==closing:
            depth-=1
            if depth==0:return i
    return None


def _graph(source):
    tokens=[]
    for match in _TOKEN.finditer(_masked(source)):
        tokens.append(match.group())
        if len(tokens)>MAX_TOKENS:
            raise ValueError('source trop complexe')
    functions={}
    loops={}
    duplicates=set()
    i=0
    while i<len(tokens):
        token=tokens[i]
        if token=='{':
            end=_closing(tokens,i,'{','}')
            if end is None:raise ValueError('accolades non équilibrées')
            i=end+1
            continue
        if _IDENTIFIER.fullmatch(token) and i+1<len(tokens) and tokens[i+1]=='(':
            end=_closing(tokens,i+1,'(',')')
            if end is None:raise ValueError('parenthèses non équilibrées')
            if end+1<len(tokens) and tokens[end+1]=='{':
                body_end=_closing(tokens,end+1,'{','}')
                if body_end is None:raise ValueError('accolades non équilibrées')
                body=tokens[end+2:body_end]
                calls={body[j] for j in range(len(body)-1)
                       if _IDENTIFIER.fullmatch(body[j]) and body[j+1]=='('
                       and body[j] not in {'if','while','for','switch','sizeof','_Alignof','return'}}
                loop_kw={t for t in body if t in {'while','for','do','goto'}}
                if token in functions:duplicates.add(token)
                functions.setdefault(token,set()).update(calls)
                loops.setdefault(token,set()).update(loop_kw)
                if len(functions)>MAX_FUNCTIONS:raise ValueError('trop de fonctions')
                i=body_end+1
                continue
            i=end+1
            continue
        i+=1
    return functions,duplicates,loops


def _reachable_cycle(graph, target):
    # DFS itérative ; pas d'appels récursifs Python sur du code fourni par l'utilisateur.
    color={target:1}
    stack=[(target,iter(graph[target] & graph.keys()))]
    while stack:
        node,neighbors=stack[-1]
        next_node=next(neighbors,None)
        if next_node is None:
            color[node]=2;stack.pop();continue
        state=color.get(next_node,0)
        if state==1:return True
        if state==0:
            color[next_node]=1
            stack.append((next_node,iter(graph[next_node] & graph.keys())))
    return False


def recursion_hint(exercise, content):
    """Message informatif ou None si l'exercice ne demande pas ce diagnostic."""
    target=TARGETS.get(exercise)
    if target is None:return None
    try:
        if isinstance(content,bytes):content=content.decode('utf-8','strict')
        if not isinstance(content,str) or len(content)>262144:raise ValueError('source indisponible')
        graph,duplicates,loops=_graph(content)
        if target not in graph:
            return ('Analyse indicative indéterminée : définition de « '+target+' » non reconnue. '
                    'Vérifiez manuellement la récursivité ; ce résultat ne modifie pas la correction.')
        found=_reachable_cycle(graph,target)
        note=(' Plusieurs définitions conditionnelles ou ambiguës ont été rencontrées.' if duplicates else '')
        if exercise in ('c05/ex01','c05/ex03','c05/ex04') and loops.get(target):
            kw_list=', '.join(sorted(loops[target]))
            note+=f' Mot(s)-clé(s) d’itération ({kw_list}) repéré(s) dans « {target} ».'
        if found:
            result='Un cycle possible d’appels entre fonctions locales est repéré dans le texte.'
        else:
            result='Aucun cycle d’appels entre fonctions locales n’a été repéré dans le texte.'
        return (result+note+' Analyse indicative, pas une preuve : macros, code conditionnel, '
                'pointeurs de fonction et appels non exécutés peuvent modifier l’interprétation. '
                'Vérifiez manuellement la récursivité ; ce résultat ne modifie pas la correction.')
    except (ValueError,UnicodeError,TypeError,RecursionError):
        return ('Analyse indicative indéterminée : source non analysable. '
                'Vérifiez manuellement la récursivité ; ce résultat ne modifie pas la correction.')


_FN_PTR_ARRAY = re.compile(r'\(\s*\*\s*[A-Za-z_][A-Za-z_0-9]*\s*\[[^\]]*\]\s*\)\s*\(')
_TYPEDEF_FN_PTR = re.compile(r'\btypedef\b[^;]*\(\s*\*\s*([A-Za-z_][A-Za-z_0-9]*)\s*\)\s*\([^;]*\)\s*;')
_MAIN_DEF = re.compile(r'\bint\s+main\s*\(([^)]*)\)\s*\{')


def doop_hint(sources):
    """Indice non bloquant pour c11/ex05 (do-op) : recherche d'un tableau de pointeurs de fonctions."""
    try:
        texts=[]
        for content in (sources or {}).values():
            if isinstance(content,bytes):content=content.decode('utf-8','strict')
            if not isinstance(content,str) or len(content)>262144:continue
            texts.append(_masked(content))
        combined='\n'.join(texts)
        found=bool(_FN_PTR_ARRAY.search(combined))
        if not found:
            for alias in _TYPEDEF_FN_PTR.findall(combined):
                if re.search(r'\b'+re.escape(alias)+r'\s+[A-Za-z_][A-Za-z_0-9]*\s*\[',combined):
                    found=True;break
        head=('Déclaration d’un tableau de pointeurs de fonctions repérée dans le texte.'
              if found else
              'Aucun tableau explicite de pointeurs de fonctions n’a été repéré dans le texte.')
        return (head+' Analyse indicative et non bloquante, pas une preuve d’exécution : '
                'macros, typedef, code conditionnel et branches inactives peuvent modifier l’interprétation.')
    except (ValueError,UnicodeError,TypeError):
        return ('Analyse indicative indéterminée pour le tableau de pointeurs de fonctions ; '
                'ce résultat ne modifie pas la correction.')


def main_signature_hint(content):
    """Indice non bloquant sur la signature de main dans les programmes C06."""
    try:
        if isinstance(content,bytes):content=content.decode('utf-8','strict')
        if not isinstance(content,str) or len(content)>262144:return None
        masked=_masked(content)
        matches=_MAIN_DEF.findall(masked)
        if len(matches)!=1:
            return 'Signature de main non reconnue statiquement (macros ou code conditionnel possibles) ; diagnostic indicatif.'
        params=' '.join(matches[0].split())
        if re.fullmatch(r'int\s+[A-Za-z_][A-Za-z_0-9]*\s*,\s*char\s*(?:\*\s*\*\s*[A-Za-z_][A-Za-z_0-9]*|\*\s*[A-Za-z_][A-Za-z_0-9]*\s*\[\s*\])',params):
            return 'Signature int main(int, char **) repérée dans le texte (analyse indicative hors macros et code conditionnel).'
        if params in ('','void'):
            return 'Signature main sans (argc, argv) repérée dans le texte ; vérifiez l’accès aux arguments (analyse indicative).'
        return 'Signature de main repérée mais de forme inhabituelle (analyse indicative hors macros et code conditionnel).'
    except (ValueError,UnicodeError,TypeError):
        return None
