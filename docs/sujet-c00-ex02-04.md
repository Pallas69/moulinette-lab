# Fiches de travail — C Piscine C 00, exercices 02 à 04

**Source :** PDF « C Piscine C 00 » version 8 fourni par l'utilisateur, pages imprimées 9 à 11 (pages PDF 10 à 12). Résumé de travail et pas reproduction intégrale du sujet.

| Exercice | Fichier | Prototype | Résultat attendu |
|---|---|---|---|
| ex02 | `ft_print_reverse_alphabet.c` | `void ft_print_reverse_alphabet(void);` | Lettres minuscules de z à a |
| ex03 | `ft_print_numbers.c` | `void ft_print_numbers(void);` | Chiffres de 0 à 9 |
| ex04 | `ft_is_negative.c` | `void ft_is_negative(int n);` | `N` si négatif, `P` si zéro ou positif |

Pour les trois, la fonction autorisée est `write` et la compilation générale du sujet est `cc -Wall -Wextra -Werror`. L'adaptateur ajoute `-fno-builtin`, vérifie partiellement les symboles et ne prétend pas reproduire les tests privés.

Ex02 et ex03 sont testés une fois et deux fois dans le même processus. Ex04 est testé avec zéro, différents signes, `INT_MIN`, `INT_MAX` (définis par `<limits.h>` sur la machine de compilation) et deux signes consécutifs. Une sortie supplémentaire est refusée ; pour les séquences, l'absence d'un saut de ligne supplémentaire est une convention propre à ce testeur, non une affirmation sur les tests officiels.

Profil autodidacte : pas d'en-tête institutionnel ; Norminette 3.3.59 ignore uniquement `INVALID_HEADER`. Les modes d'exécution restent réservés au code de confiance.
