# Validation fonctionnelle Ubuntu — Moulinette Lab v0.29.6-dev

## Version et installation

L’utilisateur a testé les sources depuis `~/Téléchargements/moulinette-lab-v0.29.6-dev` : version importée `0.29.6.dev0`. L’installation avec `python3 -m pip install --upgrade .` a réussi dans `~/.venvs/moulinette-lab-0283/`, en remplaçant la v0.29.5. Depuis `/tmp`, `pip show moulinette-lab` a confirmé la version installée `0.29.6.dev0`.

## Suite sans charge

`python3 tools/test_sans_charge.py` : **334 tests réussis en 202,627 secondes**, `OK`, aucun skip affiché. Les quatre témoins actifs de limites connus ont été exclus : écriture au-delà de la limite tmpfs, production continue sur tubes, témoin CPU RLIMIT et tentative d’allocation mémoire sous RLIMIT. Les tests compilent et exécutent des exemples de confiance : ils ne sont pas à consommation nulle. Aucun OOM ni test de saturation n’a été demandé.

## Tests cgroup réels

`python3 -m unittest discover -s tests_real -p 'test_real_cgroup.py' -v` : **4 tests réussis en 3,087 secondes**, `OK`, sans skip affiché : C00/ex00, C01/ex00, C02/ex12 et projet C12/ex08, avec un scope systemd utilisateur réel et Bubblewrap. Ils n’établissent pas l’efficacité des limites sous charge.

## Commande installée et nouveaux cas

Depuis `/tmp`, la commande installée `moulinette check` a corrigé l’exemple fourni C05/ex06 avec `--experimental-cgroup-sandbox --no-history`. Résultat : **réussi**, Norminette 3.3.59 adaptée réussie, et tous les douze cas numériques ont réussi, y compris les cas ajoutés 37 et 49 et les cas d’indices 10 et 11, respectivement 100 et 104729. L’essai n’a pas été enregistré dans l’historique.

## Limites

Validation fonctionnelle et ciblée, pas un audit de sécurité ni une preuve de conformité officielle ou d’exhaustivité. Les 21 nouveaux cas couvrent certains comportements de C05, C10, C11, C12 et C13. Les contraintes de récursivité/itération en C05 et le tableau de pointeurs de fonctions dans do-op ne sont pas prouvés automatiquement ; les vérifications mémoire et les cas d’erreur restent partiels. Le mode local n’est pas isolé ; les modes Bubblewrap et cgroup sont expérimentaux et réservés au code de confiance. Les limites sous charge n’ont pas été validées.
