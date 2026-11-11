# Audit facultatif — mode Bubblewrap expérimental 0.5

Agis comme auditeur indépendant du projet `moulinette-lab-v0.5`, sans modifier les fichiers, sans pousser de code et sans utiliser de secrets. Examine en particulier `moulinette/sandbox_runner.py`, `moulinette/checker.py`, `moulinette/cli.py`, `moulinette/sandbox_selftest.py` et `tests/test_experimental_runner.py`, ainsi que le README.

Ce mode est explicitement réservé au code de confiance ; ne le qualifie pas de sûr pour du code hostile. Ne lance pas de charge malveillante ni de tests destructifs ou de consommation excessive sur l'hôte personnel. Utilise des tests inoffensifs, à faible ressource, avec des fichiers témoins temporaires uniquement.

1. Vérifie que la compilation, `nm` et l'exécution passent bien par Bubblewrap et qu'en cas d'échec il n'y a aucun retour silencieux au mode non isolé.
2. Examine les chemins, liens symboliques, montages, fuites de données et de variables, cycle de vie des processus, temporisations, ressources et éventuels faux résultats du test témoin.
3. Identifie les problèmes dus aux différents profils AppArmor et configurations Ubuntu. Indique ce qui a réellement été testé et la version des outils.
4. Propose comment ajouter des limites de processus, seccomp et un espace de compilation borné, en indiquant les contraintes de compatibilité et limites résiduelles. Ne suggère pas de désactiver les protections système.
5. Propose comment intégrer Norminette dans l'environnement isolé sans monter tout le dossier personnel, sans exposer de secrets et sans masquer les diagnostics. Précise toute incertitude.

Rends un rapport classé par gravité avec constats, hypothèses, correctifs et tests de non-régression. Ne présente pas des tests limités comme une certification de sécurité.
