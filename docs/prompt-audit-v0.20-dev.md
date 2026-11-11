> **HISTORIQUE : ce prompt concerne l’archive v0.20, pas la v0.21. Ne pas exécuter le témoin OOM.**

# Prompt — audit indépendant de Moulinette Lab v0.20-dev

À transmettre à Antigravity avec l'archive v0.20-dev et ces instructions :

```text
Tu es auditeur sécurité indépendant. Travaille uniquement en lecture seule : ne modifie aucun fichier du projet, n'installe rien et ne désactive aucune protection. N'exécute pas le témoin de charge/OOM ni du code non fiable sans accord distinct de l'utilisateur. Ne considère jamais les promesses du README comme des preuves.

Objectif : vérifier précisément les changements de sécurité de Moulinette Lab v0.20-dev, issus de v0.19-dev. Le projet est réservé à Ubuntu et au code/dépôts de confiance ; l'objectif n'est pas de certifier une sandbox.

Contexte vérifié : la v0.19-dev a obtenu 202 tests sans skip sur l'Ubuntu utilisateur, ainsi qu'un test ex00 sous vrai scope systemd. La v0.20-dev ajoute la récupération Git CLI sous Bubblewrap avec tmpfs de 128 Mio et un témoin optionnel de charge cgroup ; ce dernier n'a pas été validé en scope réel dans l'environnement de développement.

Priorités de revue :
1. `moulinette/github_bounded.py`, `github_worker.py` et `github_source.py` : bornes réelles du stockage, montages et réseau, impossibilité de fallback, tailles d'export, inventaire complet, liens, chemins et SHA ; vérifier notamment ce que le helper interne non borné permet s'il est appelé hors worker.
2. `moulinette/process_capture.py`, `checker.py`, `sandbox_runner.py` et `cgroup_launcher.py` : identité des processus, séquence waitid/killpg, attente et nettoyage, descendants détachés, statuts Bubblewrap, descripteurs, cas d'échec et validation des rapports.
3. `moulinette/cgroup_load_probe.py` et `tests_real/test_real_cgroup_load.py` : toutes les vérifications avant fork, limites mémoire/CPU, risque d'OOM hors scope ou de mort du superviseur, compteurs, délais, nettoyage, comportement en absence de bus, races et conditions où le témoin pourrait être faux-positif. Chercher en priorité toute raison de NE PAS le lancer sur l'Ubuntu utilisateur.
4. Tests et documentation : distinguer tests réels, simulations et omissions ; identifier les régressions, données ou communications potentiellement accessibles, et les promesses inexactes.

Pour chaque constat : identifiant, gravité, fichier et lignes, scénario et préconditions, conséquences, preuve ou reproduction sûre si possible, correctif recommandé, et comment vérifier le correctif. Précise ce qui n'est qu'une hypothèse et ce que tu n'as pas testé. Priorise les erreurs de sécurité réelles ; ne déclare pas l'étape 3 terminée ni le code hostile autorisé sur la seule base des tests. Termine par un avis explicite : peut-on exécuter sans risque déraisonnable le témoin opt-in sur une machine personnelle, et sous quelles conditions ?
```
