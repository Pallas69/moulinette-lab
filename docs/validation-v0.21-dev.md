# Validation de développement — v0.21-dev

## Tests effectués avant archivage

- Suite standard : **228 tests réussis, aucun skip** avec Bubblewrap et Norminette réels dans l'environnement de développement. La suite v0.20 comptait 229 tests : les anciens tests du témoin OOM retiré ont été remplacés par des tests de refus et des régressions ciblées ; il ne s'agit pas d'une comparaison de couverture par simple comptage.
- Ancien opt-in `ML_TEST_CGROUP_LOAD=1` : le test réel de charge est sauté et le module répond indisponible. Aucune charge réelle volontaire ni aucun OOM n'ont été lancés.
- Contrôles ciblés : refus du helper Git direct par défaut ; lien symbolique du dossier de données, lien physique de base SQLite valide, lien symbolique de destination dashboard ; interruption conservée malgré une attente de nettoyage expirée ; contrôles favorables en double ; limite CPU et montages du worker. Tests de régression écrits et vérifiés en échec avant les corrections.
- GitHub HTTPS réel par le worker borné : dépôt `Tednoob17/mini-moulinette`, branche `main` et SHA `c0debfed043857ffc6c2629c897f59bec4bf9c4a` ; provenance vérifiée. Dépôt `ChuOkupai/piscine42`, commit `cc5e12c0776839a33ef12658192a0f46abdcf095`, sous-dossier `c00/ex00` : correction ex00 réussie avec Bubblewrap et Norminette. Le scope cgroup du parcours GitHub n'a pas été exercé en réel ici.
- Deux rendus locaux de démonstration : correct `passed`, incorrect `failed` avec 10 tests fonctionnels en échec ; dashboard généré avec historique isolé.
- Wheel v0.21 construit et installé dans un environnement isolé : génération du dashboard et téléchargement GitHub au SHA épinglé réussis.
- Pas de bus systemd utilisateur utilisable ici : pas de test réel cgroup dans cet environnement. Le résultat Ubuntu v0.19 est un acquis historique, pas une validation de la v0.21.

## Vérifications groupées possibles sur Ubuntu, après revue

Depuis le dossier extrait de la v0.21, avec les dépendances déjà installées et accessibles, pour du code de confiance uniquement :

```bash
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s tests_real -v
```

La seconde commande lance seulement l'exemple de confiance en scope réel ; le test de charge est déclaré **skipped** par conception, même si l'ancien opt-in est présent. Ne pas exécuter les anciens tests de charge de la v0.20. En cas d'échec ou d'indisponibilité systemd, ne pas modifier la configuration de sécurité pour forcer le résultat ; communiquer la sortie pour diagnostic. Ces essais ne démontrent pas la sûreté face au code hostile ni l'application des limites en charge.
