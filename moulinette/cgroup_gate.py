"""Vérification préliminaire d'un scope cgroup v2 déjà créé.

Module en développement, pas encore branché au correcteur. Valider des valeurs
ne prouve ni la résistance du noyau ni la sûreté d'un code non fiable.
"""
import os
import re
from pathlib import Path


class CgroupGateUnavailable(Exception):
    """Cgroup, appartenance ou limites non démontrés : arrêt obligatoire."""


def verify_current_scope(expected_scope, *, root=Path('/sys/fs/cgroup'),
                         proc_cgroup=Path('/proc/self/cgroup'), pid=None,
                         pids_max=32, memory_max=512 * 1024 * 1024, cpu_cores=1, swap_max=None):
    """Valide les limites du scope courant, sans le créer ni exécuter de code.

    Une hiérarchie non mappable, une lecture ambiguë, une valeur illimitée ou
    une appartenance non prouvée sont des erreurs. Les limites d'un ancêtre
    peuvent être plus strictes. Cette vérification reste indicative : les
    courses et altérations par un processus sous le même UID ne sont pas résolues.
    """
    if not isinstance(expected_scope, str) or not re.fullmatch(r'moulinette-[a-f0-9]{32}\.scope', expected_scope):
        raise CgroupGateUnavailable('Nom du scope incorrect.')
    if any(type(n) is not int or n <= 0 for n in (pids_max, memory_max, cpu_cores)):
        raise CgroupGateUnavailable('Limites de configuration invalides.')
    if swap_max is not None and (type(swap_max) is not int or swap_max < 0):
        raise CgroupGateUnavailable('Limite de swap invalide.')
    if pid is None:
        pid = os.getpid()
    if type(pid) is not int or pid <= 0:
        raise CgroupGateUnavailable('Identifiant de processus invalide.')
    try:
        lines = proc_cgroup.read_text(encoding='ascii').splitlines()
        unified = [line[3:] for line in lines if line.startswith('0::')]
        if len(unified) != 1:
            raise ValueError('hiérarchie v2 absente ou ambiguë')
        group = unified[0]
        if not group.startswith('/') or '..' in Path(group).parts or Path(group).name != expected_scope:
            raise ValueError('scope incorrect ou chemin non mappable')
        resolved_root = root.resolve(strict=True)
        base = (resolved_root / group.lstrip('/')).resolve(strict=True)
        if not base.is_relative_to(resolved_root) or base.name != expected_scope:
            raise ValueError('répertoire du scope hors hiérarchie')
        members = (base / 'cgroup.procs').read_text(encoding='ascii').split()
        if str(pid) not in members:
            raise ValueError('processus absent du scope')
        pids_value = (base / 'pids.max').read_text(encoding='ascii').strip()
        memory_value = (base / 'memory.max').read_text(encoding='ascii').strip()
        cpu_value = (base / 'cpu.max').read_text(encoding='ascii').split()
        if not pids_value.isdecimal() or not memory_value.isdecimal() or len(cpu_value) != 2 or not all(v.isdecimal() for v in cpu_value):
            raise ValueError('limite absente, illimitée ou mal formée')
        pids, memory = int(pids_value), int(memory_value)
        quota, period = map(int, cpu_value)
        if swap_max is not None:
            swap_value = (base / 'memory.swap.max').read_text(encoding='ascii').strip()
            if not swap_value.isdecimal() or int(swap_value) > swap_max:
                raise ValueError('limite swap absente, illimitée ou trop haute')
        if not (0 < pids <= pids_max and 0 < memory <= memory_max and 0 < quota <= cpu_cores * period and period > 0):
            raise ValueError('limite insuffisante ou incompatible avec la politique')
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        raise CgroupGateUnavailable(f'Contrôle cgroup impossible : {exc}') from exc
    return {'scope': expected_scope, 'group': group, 'pids_max': pids, 'memory_max': memory,
            'cpu_quota': quota, 'cpu_period': period}
