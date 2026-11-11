# C Piscine C 02 — version 6, prise en charge pédagogique

Source principale : PDF `C Piscine C 02.pdf` fourni par l'utilisateur, SHA-256 `a407aecf2bb29d5a834b7535011a02056bf1c3dec02dd3fb8a3fa0c7d5b7d419`. Les intitulés, fichiers, prototypes et fonctions autorisées des 13 exercices ont été lus dans le PDF et confrontés au Markdown. Profil 42 adapté aux autodidactes ; évaluation locale non officielle, sans accès aux tests officiels.

| Exercice | Fichier et fonction | Fonctions externes autorisées |
|---|---|---|
| ex00 | `ft_strcpy.c` / `char *ft_strcpy(char *dest, char *src)` | aucune |
| ex01 | `ft_strncpy.c` / `char *ft_strncpy(char *dest, char *src, unsigned int n)` | aucune |
| ex02 | `ft_str_is_alpha.c` / `int ft_str_is_alpha(char *str)` | aucune |
| ex03 | `ft_str_is_numeric.c` / `int ft_str_is_numeric(char *str)` | aucune |
| ex04 | `ft_str_is_lowercase.c` / `int ft_str_is_lowercase(char *str)` | aucune |
| ex05 | `ft_str_is_uppercase.c` / `int ft_str_is_uppercase(char *str)` | aucune |
| ex06 | `ft_str_is_printable.c` / `int ft_str_is_printable(char *str)` | aucune |
| ex07 | `ft_strupcase.c` / `char *ft_strupcase(char *str)` | aucune |
| ex08 | `ft_strlowcase.c` / `char *ft_strlowcase(char *str)` | aucune |
| ex09 | `ft_strcapitalize.c` / `char *ft_strcapitalize(char *str)` | aucune |
| ex10 | `ft_strlcpy.c` / `unsigned int ft_strlcpy(char *dest, char *src, unsigned int size)` | aucune |
| ex11 | `ft_putstr_non_printable.c` / `void ft_putstr_non_printable(char *str)` | `write` |
| ex12 | `ft_print_memory.c` / `void *ft_print_memory(void *addr, unsigned int size)` | `write` |

## Conventions et limites des tests

- Classification locale ASCII : lettres `A–Z` et `a–z`, chiffres `0–9`, imprimables d'octets 32 à 126. Les octets de 128 à 255 ne sont pas traités comme lettres ou caractères imprimables ; cette convention doit être gardée à l'esprit pour des interprétations différentes du sujet ou des locales.
- Les 255 octets non nuls sont essayés individuellement pour les cinq fonctions de classification et les deux changements de casse. Les chaînes vides, chaînes mixtes, NUL et valeurs de retour sont également vérifiés. `ft_strcapitalize` inclut l'exemple du sujet et des mots débutant par des chiffres.
- Les copies essaient diverses tailles, dont 0, 1, troncature, taille exacte et supérieure ; elles vérifient le retour, le remplissage de `strncpy`, le NUL de `strlcpy`, la source et les octets autour de la zone copiée. Chaînes valides, tampons suffisamment grands et distincts : ni chevauchement, ni pointeurs nuls ou invalides ne sont testés.
- `ft_putstr_non_printable` vérifie la sortie exacte, les échappements hexadécimaux minuscules et les octets de contrôle et élevés.
- `ft_print_memory` vérifie les colonnes selon l'exemple du PDF : octets hexadécimaux par paires, espaces de remplissage, caractères imprimables ou points, saut de ligne et adresse réelle de chaque ligne. L'adresse peut être complétée par des zéros ou non, en minuscules ou majuscules, avec ou sans préfixe `0x` ; les chiffres hexadécimaux du contenu peuvent également être en minuscules ou majuscules. Les tailles testées sont 0, 1, 2, 15, 16, 17, 32 et 33. Le retour doit être l'adresse originale, et les données ne doivent pas être modifiées. La sortie est capturée et comparée dans un harnais qui connaît l'adresse effective, sans supposer une adresse fixe.

La détection des fonctions non autorisées repose sur l'analyse partielle de l'objet compilé, qui est aussi celui lié au harnais. Les fichiers supplémentaires sont refusés. Norminette 3.3.59 utilise le profil adapté aux autodidactes. Les 13 rendus de démonstration sont dans `exemples/c02/`. Les tests ne garantissent ni note ni conformité officielle ; code de confiance uniquement. C 03–C 13 ne sont pas implémentés.
