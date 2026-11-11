# C Piscine C 01 — version 6, prise en charge pédagogique

Source : PDF `C Piscine C 01.pdf` fourni par l'utilisateur, SHA-256 `3e0fcf48c006bf93f62ea6c275d4bf84fc0776f409de84f297738addc6aa2757`. Les intitulés, prototypes, noms de fichiers et fonctions autorisées des neuf exercices ont été lus dans ce PDF et confrontés au Markdown fourni. Profil 42 adapté aux autodidactes ; évaluation locale non officielle, sans accès aux tests officiels.

| Exercice | Fichier et fonction | Fonctions externes permises | Cas de test locaux |
|---|---|---|---|
| ex00 | `ft_ft.c` / `void ft_ft(int *nbr)` | aucune | valeurs initiales différentes, appels sur deux entiers |
| ex01 | `ft_ultimate_ft.c` / `void ft_ultimate_ft(int *********nbr)` | aucune | pointeur de profondeur 9, valeurs initiales zéro et négative |
| ex02 | `ft_swap.c` / `void ft_swap(int *a, int *b)` | aucune | valeurs différentes et égales, bornes de `int`, même adresse |
| ex03 | `ft_div_mod.c` / `void ft_div_mod(int a, int b, int *div, int *mod)` | aucune | divisions exactes et avec reste, signes, zéro au numérateur |
| ex04 | `ft_ultimate_div_mod.c` / `void ft_ultimate_div_mod(int *a, int *b)` | aucune | mêmes divisions, paramètres de sortie distincts |
| ex05 | `ft_putstr.c` / `void ft_putstr(char *str)` | `write` | vide, texte, contrôles, NUL, octets non ASCII, appels successifs |
| ex06 | `ft_strlen.c` / `int ft_strlen(char *str)` | aucune | vide, texte, premier NUL, caractères de contrôle, octets non ASCII |
| ex07 | `ft_rev_int_tab.c` / `void ft_rev_int_tab(int *tab, int size)` | aucune | tailles zéro, une, paires/impaires, doublons, extrêmes |
| ex08 | `ft_sort_int_tab.c` / `void ft_sort_int_tab(int *tab, int size)` | aucune | tailles zéro, une, paires/impaires, doublons, extrêmes, tableau trié |

Pour les divisions, les tests utilisent la sémantique C99 des entiers signés, sans diviseur nul ni débordement `INT_MIN / -1` ; les paramètres d'ex03 et ex04 ne présentent pas d'alias de sortie ambigu. Aucun pointeur invalide ou chaîne sans NUL n'est utilisé. Les tests sont utiles mais non exhaustifs ; ils ne garantissent ni une note ni une conformité officielle.

Les exercices C 01 autres qu'ex05 interdisent les appels externes, y compris `write`. La détection s'appuie sur l'analyse de l'objet compilé et reste partielle. Le même objet effectivement analysé est lié au harnais. Les fichiers supplémentaires sont refusés. Norminette 3.3.59 est utilisée en profil adapté sans obligation d'en-tête institutionnel. Les 9 exemples de démonstration sont dans `exemples/c01/`.

Les anciens exercices C 00 v8 demeurent pris en charge. Le sujet C 02 est également implémenté depuis la v0.25 ; C 03 à C 13 sont reçus mais pas encore implémentés. Import automatique de sujets non disponible. L'isolation reste expérimentale : seulement des rendus et dépôts de confiance.
