# Validation — v0.23-dev

## Résultats de développement

- **249 tests standard réussis sans skip**, avec Bubblewrap et Norminette 3.3.59. Régressions ciblées écrites avant les corrections sur les interruptions, le cumul des diagnostics et l'étiquette GitHub ; des essais complémentaires ont suivi.
- Interruptions en historique et dashboard simulées, ainsi que deux SIGTERM dans un sous-processus de confiance avec lanceur cgroup simulé ; aucune unité systemd ni charge mémoire n'ont été provoquées par ces tests.
- Diagnostic de nettoyage du runner : erreur d'origine et deux incertitudes distinctes préservées en cas simulé ; erreurs de signalement du groupe et d'attente conservées dans la capture.
- Répertoire local non UTF-8 : rapport JSON représentable et historique ; provenance GitHub non UTF-8 construite artificiellement dans un appel interne : étiquette d'historique échappée.
- Accès HTTPS réel GitHub dans Bubblewrap : branche `main` de `Tednoob17/mini-moulinette` ; commit épinglé `cc5e12c0776839a33ef12658192a0f46abdcf095` de `ChuOkupai/piscine42`, `c00/ex00` : correction réussie avec Bubblewrap et Norminette réels. Aucun scope cgroup réel pour ce parcours dans l'environnement de développement.
- Wheel installé dans un environnement isolé : version, dashboard et récupération HTTPS GitHub au SHA épinglé vérifiés.
- `ML_TEST_CGROUP_LOAD=1` ne réactive pas le test de charge, qui est sauté. Aucun OOM ni témoin de saturation n'a été exécuté.

## Acquis de la v0.22 sur Ubuntu utilisateur

Sur Ubuntu, la v0.22 a obtenu **241 tests réussis sans skip**, un exemple local réussi en cgroup réel et un parcours GitHub + cgroup réel réussi ; le témoin de charge était sauté. Ces résultats ne valident pas les changements v0.23.

## Vérifications Ubuntu groupées possibles après revue

Depuis le dossier extrait v0.23 et uniquement pour du code de confiance :

```bash
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s tests_real -v
```

Le groupe réel comprend un seul essai ex00 et le test de charge désactivé, toujours skipped. Les limites en charge ne sont pas démontrées ; ne pas lancer le témoin OOM de la v0.20.
