"""Fonctions partagées du pipeline de correction (symboles nm, canaris, rapport)."""
import re

CANARY_SYMBOLS = frozenset({'__stack_chk_fail', '__stack_chk_guard'})
_NM_UNDEF_LINE = re.compile(r'\s*[Uwv]\s+(\S+)\s*')


def parse_nm_undefined(raw_out):
    """Extrait la liste des symboles indéfinis depuis la sortie brute de `nm -u`."""
    try:
        lines = raw_out.decode('utf-8', 'strict').splitlines()
    except UnicodeError:
        return None
    syms = []
    for line in lines:
        if not line.strip():
            continue
        match = _NM_UNDEF_LINE.fullmatch(line)
        if not match:
            return None
        symbol = match.group(1)
        if '@' in symbol:
            return None
        syms.append(symbol)
    return syms


def classify_external_symbols(symbols, allowed):
    """Sépare les symboles interdits et les symboles de protection de pile."""
    allowed_set = set(allowed)
    prohibited = [x for x in symbols if x not in allowed_set and x not in CANARY_SYMBOLS]
    canary_hits = CANARY_SYMBOLS.intersection(symbols)
    return prohibited, canary_hits


def build_report(exercise, spec, sandbox, checks):
    """Construit le dictionnaire de rapport normalisé pour un exercice."""
    status = (
        'failed' if any(x['status'] == 'fail' for x in checks)
        else 'incomplete' if any(x['status'] == 'unavailable' for x in checks)
        else 'passed'
    )
    return {
        'exercise': '42/c/' + exercise,
        'subject_version': spec.get('subject_version', '8'),
        'profile': '42-autodidacte',
        'isolation': (
            'Bubblewrap expérimental — code de confiance uniquement'
            if sandbox else 'aucune — mode local non sécurisé'
        ),
        'checks': checks,
        'result': status,
    }
