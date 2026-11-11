# Validation fonctionnelle Ubuntu — Moulinette Lab v0.29.7-dev

## Sources et installation

L'utilisateur a extrait l'archive dans `~/Téléchargements/workspace_moulinette_arena/moulinette-lab-v0.29.7-dev`, puis a activé l'environnement `~/.venvs/moulinette-lab-0283`. L'installation `python3 -m pip install --upgrade .` a remplacé la v0.29.6 ; depuis `/tmp`, `moulinette --version` a affiché `moulinette 0.29.7.dev0`.

Le premier essai de correction a échoué parce que le chemin fourni pointait vers `~/Téléchargements/moulinette-lab-v0.29.7-dev`, sans le dossier intermédiaire `workspace_moulinette_arena`. L'essai corrigé ci-dessous a réussi.

## Suite sans charge

`python3 tools/test_sans_charge.py` : **342 tests réussis en 187,132 secondes**, `OK`, aucun skip affiché. Les quatre témoins actifs de limites connus ont été exclus : limite tmpfs, production continue sur tubes, témoin CPU RLIMIT et allocation mémoire sous RLIMIT. La suite compile et exécute néanmoins des exemples de confiance ; aucun test OOM ou de saturation n'a été demandé.

## Tests cgroup réels

`python3 -m unittest discover -s tests_real -p 'test_real_cgroup.py' -v` : **4 tests réussis en 2,538 secondes**, `OK`, sans skip affiché. Tests de C00/ex00, C01/ex00, C02/ex12 et C12/ex08 dans un scope systemd utilisateur réel avec Bubblewrap. Ces tests fonctionnels ne démontrent pas l'efficacité des limites sous charge.

## Commande installée et diagnostic C05/ex08

Depuis `/tmp`, la commande installée a corrigé l'exemple fourni de confiance avec :

```bash
moulinette check ~/Téléchargements/workspace_moulinette_arena/moulinette-lab-v0.29.7-dev/exemples/c05/ex08 --exercise c05/ex08 --experimental-cgroup-sandbox --no-history
```

Le cgroup a été déclaré vérifié ; la compilation, le prototype, les **724 placements valides et distincts** et la Norminette adaptée ont réussi. Le rapport a signalé un cycle d'appels possible comme **information indicative**, puis affiché `Résultat : réussi`. `--no-history` évite d'ajouter cet essai à l'historique. Le diagnostic ne prouve ni la récursivité effective ni la conformité du sujet.

## Limites

Validation fonctionnelle ciblée, pas audit de sécurité ni preuve de conformité officielle ou d'exhaustivité. Les contrôles de récursivité sont textuels, indicatifs et non bloquants ; l'itération n'est pas prouvée. Les cas fonctionnels, Makefiles, tableaux de fonctions et vérifications mémoire restent partiels. Les modes Bubblewrap et cgroup sont expérimentaux et réservés au code de confiance ; les limites sous charge n'ont pas été validées.
