# Validation fonctionnelle Ubuntu — Moulinette Lab v0.29.5-dev

## Sources et installation

L’utilisateur a extrait et testé les sources depuis `~/Téléchargements/moulinette-lab-v0.29.5-dev`. La version importée depuis ce dossier était `0.29.5.dev0`. L’installation par `python3 -m pip install --upgrade .` a réussi dans `~/.venvs/moulinette-lab-0283/`, en remplaçant la v0.29.4. Depuis `/tmp`, `python3 -m pip show moulinette-lab` a confirmé la version installée `0.29.5.dev0`.

## Sélection sans charge

`python3 tools/test_sans_charge.py` : **332 tests réussis en 181,974 secondes**, `OK`, aucun skip affiché. Quatre témoins actifs connus ont été exclus : dépassement de tmpfs, production continue sur tubes, témoin CPU RLIMIT et tentative d’allocation mémoire sous RLIMIT. Les tests exécutent des exemples de confiance et ne sont pas à consommation nulle. Aucun OOM ni saturation n’a été demandé dans cette sélection.

## Cgroup réel

`python3 -m unittest discover -s tests_real -p 'test_real_cgroup.py' -v` : **4 tests réussis en 2,627 secondes**, `OK` : C00/ex00, C01/ex00, C02/ex12 et le projet C12/ex08, dans un scope systemd utilisateur réel avec Bubblewrap. Ces tests utilisent des exemples de confiance et ne démontrent pas l’efficacité des limites sous charge.

## Commande installée

Depuis `/tmp`, `moulinette check` a corrigé avec succès l’exemple fourni C12/ex08 en mode `--experimental-cgroup-sandbox --no-history`. Le rapport montre notamment compilation C11, prototype et liaison réussis, deux tests réussis et Norminette 3.3.59 avec `INVALID_HEADER` ignoré. Le scope rapportait 32 tâches maximum, 536870912 octets de mémoire, swap 0 et quota CPU 100000/100000. Cette correction n’a pas été enregistrée dans l’historique.

## Portée

La validation est fonctionnelle et ciblée : elle ne constitue ni un audit de sécurité, ni une preuve de conformité officielle ou de couverture exhaustive. Les témoins légers des blocages et du nettoyage sont inclus dans la sélection, mais les descendants qui changent de groupe, les interruptions brutales et les états noyau non interruptibles restent des limites. Le délai global de réception cgroup de 230 secondes a été testé par simulation, pas par une attente réelle de 230 secondes ; il ne borne pas la durée de la commande entière. Le mode local n’est pas isolé ; Bubblewrap et cgroup restent expérimentaux et réservés au code de confiance. La suite standard complète, y compris les quatre témoins exclus, n’a pas été exécutée.
