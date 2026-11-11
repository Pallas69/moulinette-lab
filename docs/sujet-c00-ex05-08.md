# Fiches de travail — C Piscine C 00, exercices 05 à 08

**Source :** PDF « C Piscine C 00 » version 8 fourni par l'utilisateur, pages imprimées 13 à 16 (pages PDF 14 à 17). Résumé de travail, pas une reproduction complète ni une garantie de conformité aux tests privés.

| Exercice | Fichier | Prototype | Tests principaux |
|---|---|---|---|
| ex05 | `ft_print_comb.c` | `void ft_print_comb(void);` | 120 combinaisons croissantes de trois chiffres distincts et deux appels successifs |
| ex06 | `ft_print_comb2.c` | `void ft_print_comb2(void);` | 4 950 paires `00 01` à `98 99`, dans l'ordre et deux appels successifs |
| ex07 | `ft_putnbr.c` | `void ft_putnbr(int n);` | Zéro, valeurs positives et négatives, limites `INT_MIN` et `INT_MAX`, appels successifs |
| ex08 | `ft_print_combn.c` | `void ft_print_combn(int n);` | Combinaisons de chiffres distincts pour chaque `n` de 1 à 9, plus deux appels successifs |

Fonction autorisée : `write`. Compilation générale du sujet : `cc -Wall -Wextra -Werror`. Le moteur ajoute `-fno-builtin` et effectue un contrôle partiel des symboles. Dans le profil autodidacte, l'en-tête institutionnel n'est pas exigé et Norminette 3.3.59 ignore uniquement `INVALID_HEADER`.

Pour les combinaisons, le moteur génère les sorties indépendamment à partir des règles du sujet et vérifie les séparateurs `, ` sans séparateur final. Le testeur n'accepte pas de saut de ligne ajouté ; cette convention est mentionnée comme choix local. Pour ex08, les valeurs de `n` hors de 1 à 9 ne sont pas évaluées car le sujet ne les spécifie pas.

Pour ex07, les limites attendues sont calculées d'après `ctypes.c_int` et le modèle d'entier est vérifié lors de la compilation du harnais. Si le compilateur ne correspond pas au modèle pris en charge, le résultat est `incomplete` et non un échec imputé au rendu. Les marqueurs de fin et les contrôles de prototype/symboles restent partiels ; aucun mode n'est considéré sûr pour du code non fiable.
