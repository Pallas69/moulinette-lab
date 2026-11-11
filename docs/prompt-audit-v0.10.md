# Audit indépendant de Moulinette Lab v0.10

Audite uniquement en lecture le code du nouveau mode `--experimental-cgroup-sandbox`. Il s'agit d'un prototype pour code de confiance, pas d'une sandbox sécurisée contre du code hostile. Ne modifie pas les fichiers, n'utilise pas root, ne modifie pas AppArmor ou le noyau, n'exécute pas de code tiers et ne fais ni fork-bomb, ni saturation de mémoire/disque ou tentative d'évasion destructrice. Si un test est risqué, décris-le au lieu de l'exécuter.

Vérifie surtout :
1. `cgroup_launcher.py`, `cgroup_worker.py`, `cgroup_gate.py` et `scope_protocol.py` : aucun accès au rendu ou lancement du compilateur avant vérification des limites par le superviseur et le parent et autorisation explicite ; pas de fallback non isolé.
2. Correspondance du PID, du nom de scope, de `cgroup.procs`, `pids.max`, `memory.max`, `memory.swap.max`, `cpu.max` ; effet des namespaces et hiérarchies différentes. Vérifie ce que l'on peut réellement conclure des valeurs et ce qui reste contestable.
3. Socket Unix, vérification et encadrement des messages, courses, modifications depuis le même UID et gestion des sorties mal formées ou interrompues.
4. Arrêt du scope et contrôle `cgroup.events` après succès, erreur, timeout et interruption ; limite du contrôle si le parent est tué ou si un processus change de cgroup. Ne suppose pas que l'absence du dossier prouve une résistance générale.
5. Que `check_ex00`, son compilateur, Norminette et les instances Bubblewrap héritent du bon cgroup avant leur démarrage ; limites par processus versus globales, tmpfs, swap, stockage et réseau.
6. Que les erreurs d'infrastructure restent `incomplete` et que le JSON reste exploitable ; vérifier les faux positifs et les tests qui ne couvrent que des simulations.
7. Examiner les risques et différences entre `--experimental-cgroup-sandbox`, `--experimental-sandbox` et `--unsafe-local`.

Exécute seulement la suite `python3 -m unittest discover -s tests -v` et la correction de l'exemple fixe avec la nouvelle option si l'utilisateur le souhaite. Indique les versions, tous les tests ignorés, les limites de ton environnement et si tu as réellement observé un scope systemd. Classe les problèmes avec références de code, reproduction non dangereuse et recommandations. Ne déclare jamais le mode sûr pour du code non fiable.
