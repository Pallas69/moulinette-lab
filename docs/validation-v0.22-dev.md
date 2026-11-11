# Validation de développement — v0.22-dev

## Essais dans l'environnement de développement

- Suite standard : **241 tests réussis, sans skip**, avec Bubblewrap et Norminette 3.3.59. Les premières régressions ciblées ont été écrites et observées en échec avant correction ; des cas complémentaires ont ensuite été ajoutés, notamment celui du vrai processus capturé.
- SIGTERM : sous-processus de confiance, CLI et worker cgroup **simulé** ; vérification du rapport incomplet et du retrait du répertoire temporaire dans ces scénarios. Une vraie capture lance un petit processus de confiance, qui est interrompu et récolté. Pas de saturation ni de scope systemd réel.
- Encodage non UTF-8 : rejets côté Git et conversion sûre dans les diagnostics locaux ; historique enregistré ; accents valides préservés.
- SQLite : refus des liens symboliques et physiques sur les trois auxiliaires, avec fichier témoin non modifié. Reproduction isolée d'une modification du témoin par un lien physique `-wal` avec la v0.21 et SQLite 3.46.1.
- Vérification des sorties de compilation en échec, du remplacement d'identité, du descripteur en erreur, des rapports favorables et de l'invocation directe de la sonde désactivée.
- Bubblewrap et Norminette réels : les neuf exemples ex00–ex08 passent et leurs rapports favorables satisfont la nouvelle validation.
- GitHub HTTPS réel : `Tednoob17/mini-moulinette` branche `main`, puis `ChuOkupai/piscine42` SHA `cc5e12c0776839a33ef12658192a0f46abdcf095`, `c00/ex00` ; cette dernière source passe la correction Bubblewrap/Norminette. Le cgroup réel de ce parcours n'a pas été utilisé dans cet environnement de développement.
- Wheel installé dans un environnement isolé : version v0.22, dashboard et récupération HTTPS GitHub au SHA épinglé vérifiés.
- Ancien opt-in `ML_TEST_CGROUP_LOAD=1` : le test de charge reste sauté. Aucun témoin OOM ou saturation n'a été lancé.

## Rappel des résultats Ubuntu v0.21

L'utilisateur a obtenu **228/228** tests standard, le test local cgroup réel réussi et le parcours GitHub+cgroup réel réussi. Le test de charge était sauté. Ces essais ne valident pas les changements v0.22.

## Si une vérification Ubuntu de la v0.22 est souhaitée après revue

Depuis le dossier extrait de la v0.22, et uniquement pour du code de confiance :

```bash
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s tests_real -v
```

Le second groupe contient le test ex00 réel et un test de charge toujours sauté. Aucun test OOM n'est proposé. Ne pas affaiblir la configuration du système si un test échoue. Tous les résultats restent non officiels et ne valident pas une sécurité face à du code hostile.
