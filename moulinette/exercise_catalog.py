"""Catalogue interne d’exercices validés, non chargeable depuis un rendu."""

CASES = [("NUL", 0), ("tabulation", 9), ("retour à la ligne", 10), ("espace", 32),
         ("lettre A", 65), ("chiffre 0", 48), ("DEL", 127), ("octet 128", 128), ("octet 255", 255)]
# Le harnais est lié à l’objet exact analysé par nm, y compris en cas de recompilation.
HARNESS = r'''#include <limits.h>
#include <stdlib.h>
#include <unistd.h>
static const unsigned char marker[] = { MARKER_BYTES };
void ft_putchar(char c);
_Static_assert(CHAR_BIT == 8, "Ce prototype requiert CHAR_BIT == 8");
int main(int argc, char **argv)
{
    int i;
    if (argc != 2) return 2;
    if (argv[1][0] == 'a') {
        for (i = 0; i < 256; ++i) ft_putchar((char)(unsigned char)i);
    } else ft_putchar((char)(unsigned char)strtol(argv[1], NULL, 10));
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''
# Contrôle de type indicatif : la compilation distincte et l'édition des liens restent indispensables.
PROTOTYPE = r'''#include "ft_putchar.c"
#undef char
#undef void
#undef ft_putchar
#undef _Generic
#undef _Static_assert
_Static_assert(_Generic(&ft_putchar, void (*)(char): 1, default: 0), "Prototype attendu : void ft_putchar(char c)");
'''


# Exercice vérifié à partir du sujet C 00 v8 fourni ; aucune copie de tests tiers.
ALPHABET = b"abcdefghijklmnopqrstuvwxyz"
HARNESS_EX01 = r'''#include <unistd.h>
static const unsigned char marker[] = { MARKER_BYTES };
void ft_print_alphabet(void);
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    ft_print_alphabet();
    if (argv[1][0] == '2') ft_print_alphabet();
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''
PROTOTYPE_EX01 = r'''#include "ft_print_alphabet.c"
#undef void
#undef ft_print_alphabet
#undef _Generic
#undef _Static_assert
_Static_assert(_Generic(&ft_print_alphabet, void (*)(void): 1, default: 0), "Prototype attendu : void ft_print_alphabet(void)");
'''
EXERCISES = {
    'c00/ex00': {'source': 'ft_putchar.c', 'executable': 'test-ex00', 'harness': HARNESS,
                 'prototype': PROTOTYPE,
                 'cases': [(label, str(value), bytes([value])) for label, value in CASES]
                          + [('256 octets successifs', 'all', bytes(range(256))) ]},
    'c00/ex01': {'source': 'ft_print_alphabet.c', 'executable': 'test-ex01', 'harness': HARNESS_EX01,
                 'prototype': PROTOTYPE_EX01,
                 'cases': [('alphabet', '1', ALPHABET), ('deux appels consécutifs', '2', ALPHABET * 2)]},
}


# Fiches ex02–ex04 rédigées à partir du sujet C 00 version 8 fourni.
def _no_argument_spec(function, label, expected):
    return {
        'source': function + '.c', 'executable': 'test-' + function,
        'harness': HARNESS_EX01.replace('ft_print_alphabet', function),
        'prototype': PROTOTYPE_EX01.replace('ft_print_alphabet', function),
        'cases': [(label, '1', expected), ('deux appels consécutifs', '2', expected * 2)],
    }

HARNESS_EX04 = r'''#include <limits.h>
#include <stdlib.h>
#include <unistd.h>
static const unsigned char marker[] = { MARKER_BYTES };
void ft_is_negative(int n);
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (argv[1][0] == 'm') ft_is_negative(INT_MIN);
    else if (argv[1][0] == 'x') ft_is_negative(INT_MAX);
    else if (argv[1][0] == 'p') {
        ft_is_negative(-1);
        ft_is_negative(0);
    } else ft_is_negative((int)strtol(argv[1], NULL, 10));
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''
PROTOTYPE_EX04 = r'''#include "ft_is_negative.c"
#undef int
#undef void
#undef ft_is_negative
#undef _Generic
#undef _Static_assert
_Static_assert(_Generic(&ft_is_negative, void (*)(int): 1, default: 0), "Prototype attendu : void ft_is_negative(int)");
'''
EXERCISES.update({
    'c00/ex02': _no_argument_spec('ft_print_reverse_alphabet', 'alphabet inversé', b'zyxwvutsrqponmlkjihgfedcba'),
    'c00/ex03': _no_argument_spec('ft_print_numbers', 'chiffres', b'0123456789'),
    'c00/ex04': {
        'source': 'ft_is_negative.c', 'executable': 'test-ft_is_negative',
        'harness': HARNESS_EX04, 'prototype': PROTOTYPE_EX04,
        'cases': [('int minimum', 'min', b'N'), ('négatif -42', '-42', b'N'),
                  ('négatif -1', '-1', b'N'), ('zéro', '0', b'P'),
                  ('positif 1', '1', b'P'), ('positif 42', '42', b'P'),
                  ('int maximum', 'xmax', b'P'), ('deux signes consécutifs', 'pair', b'NP')],
    },
})


def canonical_exercise(value):
    """Normaliser uniquement des identifiants internes explicitement reconnus (C, C++, Python)."""
    if not isinstance(value, str):
        return None
    s = value.strip().lower().replace(' ', '')
    for prefix in ('42/c/', '42/cpp/', '42/c++/', '42/py/', '42/python/'):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    for prefix, repl in (
        ('c/', ''),
        ('cpp/module', 'cpp'),
        ('c++/module', 'cpp'),
        ('cpp/', ''),
        ('c++/', ''),
        ('python/module', 'py'),
        ('py/module', 'py'),
        ('python/', ''),
        ('py/', ''),
    ):
        if s.startswith(prefix):
            s = repl + s[len(prefix):]
            break
    return s if s in ALL_EXERCISES else None


def piscine_of(exercise_id):
    """Retourne l'identifiant de piscine ('c', 'cpp' ou 'py') d'un exercice."""
    norm = canonical_exercise(exercise_id) or str(exercise_id or '')
    if norm.startswith('cpp'):
        return 'cpp'
    if norm.startswith('py'):
        return 'py'
    if norm.startswith('c'):
        return 'c'
    return None

# Génération indépendante des sorties attendues à partir des combinaisons du sujet.
from itertools import combinations
import ctypes


def _digit_combinations(n):
    return ', '.join(''.join(c) for c in combinations('0123456789', n)).encode('ascii')


def _two_number_combinations():
    return ', '.join(f'{a:02d} {b:02d}' for a in range(100) for b in range(a + 1, 100)).encode('ascii')


INT_BITS = ctypes.sizeof(ctypes.c_int) * 8
INT_MAX_PY = (1 << (INT_BITS - 1)) - 1
INT_MIN_PY = -INT_MAX_PY - 1

HARNESS_EX07 = r'''#include <limits.h>
#include <stdlib.h>
#include <unistd.h>
static const unsigned char marker[] = { MARKER_BYTES };
void ft_putnbr(int n);
_Static_assert(CHAR_BIT == 8 && INT_MAX == ML_INT_MAX && INT_MIN == (-ML_INT_MAX - 1), "ML_INT_PLATFORM_UNSUPPORTED");
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (argv[1][0] == 'm') ft_putnbr(INT_MIN);
    else if (argv[1][0] == 'x') ft_putnbr(INT_MAX);
    else if (argv[1][0] == 'p') {
        ft_putnbr(-1);
        ft_putnbr(0);
        ft_putnbr(1);
    } else ft_putnbr((int)strtol(argv[1], NULL, 10));
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''.replace('ML_INT_MAX', str(INT_MAX_PY))
PROTOTYPE_EX07 = r'''#include "ft_putnbr.c"
#undef int
#undef void
#undef ft_putnbr
#undef _Generic
#undef _Static_assert
_Static_assert(_Generic(&ft_putnbr, void (*)(int): 1, default: 0), "Prototype attendu : void ft_putnbr(int)");
'''
HARNESS_EX08 = r'''#include <stdlib.h>
#include <unistd.h>
static const unsigned char marker[] = { MARKER_BYTES };
void ft_print_combn(int n);
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (argv[1][0] == 'p') {
        ft_print_combn(2);
        ft_print_combn(2);
    } else ft_print_combn((int)strtol(argv[1], NULL, 10));
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''
PROTOTYPE_EX08 = r'''#include "ft_print_combn.c"
#undef int
#undef void
#undef ft_print_combn
#undef _Generic
#undef _Static_assert
_Static_assert(_Generic(&ft_print_combn, void (*)(int): 1, default: 0), "Prototype attendu : void ft_print_combn(int)");
'''

_nbr_values = [n for n in (-10000, -1000, -100, -42, -10, -9, -1, 0, 1, 9, 10, 42, 99, 100, 1000, 10000) if INT_MIN_PY <= n <= INT_MAX_PY]
EXERCISES.update({
    'c00/ex05': dict(_no_argument_spec('ft_print_comb', 'combinaisons de trois chiffres', _digit_combinations(3)), timeout=3),
    'c00/ex06': dict(_no_argument_spec('ft_print_comb2', 'paires de nombres', _two_number_combinations()), timeout=5),
    'c00/ex07': {
        'source': 'ft_putnbr.c', 'executable': 'test-ft_putnbr', 'harness': HARNESS_EX07,
        'prototype': PROTOTYPE_EX07,
        'cases': [('int minimum', 'min', str(INT_MIN_PY).encode())]
                 + [(f'nombre {n}', str(n), str(n).encode()) for n in _nbr_values]
                 + [('int maximum', 'xmax', str(INT_MAX_PY).encode()), ('trois appels consécutifs', 'pair', b'-101')],
    },
    'c00/ex08': {
        'source': 'ft_print_combn.c', 'executable': 'test-ft_print_combn', 'harness': HARNESS_EX08, 'timeout': 3,
        'prototype': PROTOTYPE_EX08,
        'cases': [(f'n = {n}', str(n), _digit_combinations(n)) for n in range(1, 10)]
                 + [('deux appels consécutifs n = 2', 'pair', _digit_combinations(2) * 2)],
    },
})

# Pack vérifié à partir du PDF C Piscine C 01, version 6 fourni.
from .c01_catalog import C01_EXERCISES
EXERCISES.update(C01_EXERCISES)
from .c02_catalog import C02_EXERCISES
EXERCISES.update(C02_EXERCISES)
from .c03_catalog import C03_EXERCISES
EXERCISES.update(C03_EXERCISES)
from .c04_catalog import build_c04
EXERCISES.update(build_c04(EXERCISES))
from .c05_catalog import C05_EXERCISES
EXERCISES.update(C05_EXERCISES)
from .c06_catalog import C06_EXERCISES
EXERCISES.update(C06_EXERCISES)
from .c07_catalog import C07_EXERCISES
EXERCISES.update(C07_EXERCISES)
from .c11_catalog import C11_EXERCISES
EXERCISES.update(C11_EXERCISES)
# C09/ex02 reprend le même contrat que C07/ex05.
from copy import deepcopy as _catalog_deepcopy
EXERCISES['c09/ex02'] = _catalog_deepcopy(C07_EXERCISES['c07/ex05'])
EXERCISES['c09/ex02']['subject_version'] = '5.0'
from .c08_catalog import C08_EXERCISES
EXERCISES.update(C08_EXERCISES)
from .c07_project_catalog import C07_PROJECT_EXERCISES
EXERCISES.update(C07_PROJECT_EXERCISES)
from .c09_project_catalog import C09_PROJECT_EXERCISES
EXERCISES.update(C09_PROJECT_EXERCISES)
from .c12_catalog import C12_EXERCISES
EXERCISES.update(C12_EXERCISES)
from .c13_catalog import C13_EXERCISES
EXERCISES.update(C13_EXERCISES)
from .c10_catalog import C10_EXERCISES
from .c11_project_catalog import C11_PROJECT_EXERCISES
EXERCISES.update(C10_EXERCISES)
EXERCISES.update(C11_PROJECT_EXERCISES)

from .cpp_catalog import CPP_EXERCISES
from .py_catalog import PY_EXERCISES

PISCINE_ORDER = ('c', 'cpp', 'py')
PISCINE_LABELS = {
    'c': 'Piscine C',
    'cpp': 'Piscine C++',
    'py': 'Piscine Python',
}
PISCINES = {
    'c': EXERCISES,
    'cpp': CPP_EXERCISES,
    'py': PY_EXERCISES,
}
ALL_EXERCISES = {**EXERCISES, **CPP_EXERCISES, **PY_EXERCISES}

