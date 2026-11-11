# Validation — v0.24-dev et C 01

## Ce qui a été vérifié

- Les versions déclarées et les listes de numéros d'exercices correspondent pour les 14 paires PDF/Markdown C 00–C 13. Ceci ne constitue pas une comparaison exhaustive de leur contenu.
- C 01 v6 : intitulés, fichiers, fonctions autorisées et prototypes lus dans le PDF `C Piscine C 01.pdf`, SHA-256 `3e0fcf48c006bf93f62ea6c275d4bf84fc0776f409de84f297738addc6aa2757`, et confrontés au Markdown. Les conventions des tests sont documentées dans `sujet-c01-v6.md`.
- Suite standard : **256 tests réussis sans skip** dans l'environnement de développement, avec Bubblewrap et Norminette 3.3.59 disponibles. Les nouveaux tests vérifient les neuf rendus de référence, neuf variantes volontairement fausses, les restrictions de fonctions, un mauvais prototype, des fichiers supplémentaires, les rapports et le tableau de bord. Les variantes fausses sont vérifiées localement avec style simulé ; les neuf rendus de référence passent aussi séparément avec Bubblewrap et Norminette réels.
- Les neuf rapports C 01 favorables générés avec Bubblewrap réel passent la validation de structure du lanceur cgroup ; ce n'est **pas** un test d'un scope réel.
- Récupération HTTPS GitHub réelle dans le worker Bubblewrap pour `ChuOkupai/piscine42`, commit `cc5e12c0776839a33ef12658192a0f46abdcf095`, dossier `c01/ex00` : source lue, comparée octet par octet à la source HTTPS brute, puis correction Bubblewrap/Norminette réussie. Le cgroup réel de ce parcours n'a pas été exercé ici.
- Wheel v0.24 installé dans un environnement virtuel isolé : tableau de bord et récupération/correction GitHub C 01 réussis.
- Le témoin de charge demeure désactivé même avec l'ancien opt-in ; aucun OOM n'a été lancé.

## Ce qui reste à vérifier

L'environnement de développement ne dispose pas d'un bus systemd utilisateur : les nouveaux essais réels de C 01 en cgroup n'ont pas été exécutés ici. La v0.23 a réussi sur l'Ubuntu de l'utilisateur, mais cela ne valide pas automatiquement la v0.24. Les tests C 01 ne sont ni officiels ni exhaustifs ; C 02–C 13 ne sont pas encore implémentés. La sécurité reste en pause et le prototype réservé au code et aux dépôts de confiance.

Pour une validation Ubuntu ultérieure groupée, depuis cette version :

```bash
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s tests_real -v
```

Les tests réels incluent maintenant deux exemples de confiance, C 00 ex00 et C 01 ex00, ainsi qu'un témoin de charge toujours sauté. Ne pas exécuter le témoin OOM de la v0.20.
