# Perfectionnement ciblé de C11 — v0.29.8-dev

## Portée

Neuf cas fonctionnels non officiels ont été ajoutés à cinq exercices du sujet C11 v8 fourni, sans changer la sécurité, les modes ou l'historique. Ils ne remplacent pas une évaluation humaine, ne prouvent pas la conformité 42 et restent partiels.

- `ft_map` : transformation et allocation distincte pour un tableau d'un élément.
- `ft_any` : ordre du callback quand la correspondance est au milieu ; le parcours peut s'arrêter immédiatement après ou continuer jusqu'à la fin.
- `do-op` : trop peu ou trop d'arguments, opérateur en mot, opérateur commençant par un symbole valide mais suivi d'autres caractères, conversion du premier opérande. Le sujet donne explicitement `foo plus bar` et `toto3 + 4` comme exemples ; les autres cas suivent les règles sur le nombre d'arguments et les opérateurs valides.
- `ft_sort_string_tab` et `ft_advanced_sort_string_tab` : tableau vide et tableau d'un élément, conservation du pointeur et du contenu.

Aucun ordre de tri stable pour les doublons, comportement d'overflow, arrêt obligatoire de `ft_any` après la première correspondance ou résultat de `malloc(0)` n'est imposé. Le tableau de pointeurs de fonctions demandé par `do-op` reste non vérifié automatiquement.

## Témoins

Trois variantes erronées de code de confiance ont été évaluées : `do-op` qui accepte trop d'arguments, `do-op` qui ne vérifie que le premier caractère de l'opérateur, et `ft_map` qui échoue pour une longueur égale à un. Chacune réussit les anciens cas fonctionnels correspondants et échoue à un nouveau cas. Cela ne signifie pas que l'ancienne correction complète aurait forcément réussi, notamment le contrôle de style restant indépendant. Les cinq exemples de référence réussissent ; une variante de `ft_any` parcourant toute la table réussit les contrôles fonctionnels, comme la version s'arrêtant à la première correspondance.

Les essais utilisent du code de confiance, sans OOM ni saturation. Ils ne prouvent pas l'absence d'autres défauts. La v0.29.7 a été validée sur l'Ubuntu utilisateur ; la v0.29.8 reste à y valider.
