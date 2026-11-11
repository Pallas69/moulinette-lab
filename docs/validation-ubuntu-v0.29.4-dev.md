# Validation fonctionnelle sur Ubuntu — Moulinette Lab v0.29.4-dev

## Environnement communiqué par l’utilisateur

- Sources : `~/Téléchargements/moulinette-lab-v0.29.4-dev` ; version importée depuis ce dossier : `0.29.4.dev0`.
- Paquet installé dans `~/.venvs/moulinette-lab-0283/` : `0.29.4.dev0` ; commande `moulinette` trouvée dans le même environnement virtuel.
- Python 3.14.4, noyau Linux 7.0.0-42-generic, glibc 2.43, Bubblewrap présent dans `/usr/bin/bwrap`.
- Norminette 3.3.59, trouvée dans `~/.local/bin/norminette`.

## Suite sans charge

`python3 tools/test_sans_charge.py` : **323 tests réussis en 157,765 secondes**, `OK`, aucun skip affiché. Les quatre témoins actifs de limites connus ont été explicitement exclus : écriture au-delà d’une limite tmpfs, production continue sur tubes, témoin CPU RLIMIT et tentative d’allocation mémoire sous RLIMIT. La suite compile et exécute des exemples de confiance ; elle n’est pas à consommation nulle. Aucun test OOM ou de saturation n’a été demandé dans cette sélection.

## Cgroup réel et Bubblewrap

`python3 -m unittest discover -s tests_real -p 'test_real_cgroup.py' -v` : **4 tests réussis en 2,352 secondes**, `OK` : C00/ex00, C01/ex00, C02/ex12 et projet C12/ex08. Les tests utilisent des exemples fournis de confiance et un scope systemd utilisateur réel. Ils ne démontrent pas l’efficacité des limites sous charge ni la sécurité face à du code hostile.

## Tableau de bord et guides

Depuis `/tmp`, la commande installée `moulinette dashboard` a généré `~/.local/share/moulinette-lab/dashboard.html`. L’utilisateur confirme que le tableau de bord s’ouvre et que les quatre PDF se téléchargent et s’ouvrent correctement dans les couleurs attendues : manuel et guide du style C, chacun en Blanc et Océan.

Le terminal a affiché une ligne du navigateur Chromium mentionnant `zygote_linux.cc` et `Relais brisé (pipe)`. Malgré ce message, l’utilisateur confirme le fonctionnement de l’ouverture et des quatre PDF. La cause exacte de cette ligne n’a pas été établie.

## Portée et limites

Cette validation est **fonctionnelle et ciblée**, pas une certification de sécurité ni de conformité à la moulinette officielle. La suite complète, y compris les quatre témoins exclus, n’a pas été exécutée. Aucun OOM ni test de saturation n’a été effectué. Tous les exercices ont des tests, mais les cas ne sont pas exhaustifs. Le mode local n’est pas isolé ; les modes Bubblewrap et cgroup restent expérimentaux et réservés au code de confiance. Les délais et le nettoyage de certains descendants restent des points à améliorer.
