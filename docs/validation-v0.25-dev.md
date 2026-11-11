# Validation — v0.25-dev et C 02

## Ce qui a été vérifié

- PDF C 02 version 6 fourni par l'utilisateur : intitulés, fichiers, prototypes, fonctions autorisées et consignes de chaque exercice examinés, puis confrontés au Markdown. La correspondance générale des versions et des numéros C 00–C 13 ne signifie pas que tous les autres textes aient été comparés en détail.
- Suite standard dans l'environnement de développement : **264 tests réussis sans skip**, avec Bubblewrap et Norminette 3.3.59 disponibles.
- Les 13 exemples de confiance C 02 passent en Bubblewrap et Norminette réels. Leurs rapports passent la validation structurelle du lanceur cgroup : cela ne constitue pas un essai dans un scope réel. Les tests fonctionnels locaux rejettent aussi 13 variantes volontairement fausses et plusieurs erreurs moins évidentes (remplissage `strncpy`, capitalisation après chiffre, troncature `strlcpy`, échappements manquants). Le style des variantes incorrectes est simulé.
- `ft_print_memory` est testé avec une adresse réelle variable et plusieurs tailles ; une représentation d'adresse non complétée de zéros, en majuscules et avec préfixe `0X`, ainsi que du contenu hexadécimal en majuscules, a été acceptée dans le test de compatibilité. Les conventions ASCII et format sont dans `sujet-c02-v6.md`.
- Wheel v0.25 installé en environnement virtuel distinct : tableau de bord et récupération HTTPS GitHub réelle via le worker Bubblewrap pour `ChuOkupai/piscine42`, commit `cc5e12c0776839a33ef12658192a0f46abdcf095`, dossier `c02/ex00`. Le fichier a été comparé octet par octet à la source brute avant correction. Les **10 tests fonctionnels** passent ; le verdict global est **failed** car Norminette 3.3.59 relève `SPACE_REPLACE_TAB` ligne 15 colonne 8. Il ne s'agit donc pas d'une correction GitHub entièrement réussie.
- La v0.24 a été testée par l'utilisateur sous Ubuntu : 256 tests standard réussis ; tests réels de C 00/ex00 et C 01/ex00 réussis avec scope et Bubblewrap ; charge sautée. Ces résultats ne valident pas automatiquement la v0.25.
- Le témoin CPU/OOM reste désactivé ; aucune charge de saturation n'a été lancée.

## Limites

L'environnement de développement ne dispose pas de bus systemd utilisateur ; les tests C 02 en scope cgroup réel et les tests GitHub avec cgroup réel n'ont pas été exécutés ici. Un test facultatif de l'exemple C 02/ex12 est inclus dans `tests_real` pour une vérification groupée ultérieure. La sécurité reste en pause, code et dépôts de confiance seulement. Les tests sont non officiels et non exhaustifs. C 03–C 13 ne sont pas implémentés ; import automatique de sujets absent.
