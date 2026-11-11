# Mission facultative pour Antigravity : audit du prototype

Tu es auditeur technique indépendant. Le projet ci-joint `moulinette-lab` est un prototype Ubuntu/Python destiné à évaluer du code étudiant. Lis le README, `moulinette/checker.py`, `moulinette/cli.py`, `tests/test_checker.py` et `docs/feuille-de-route.md`.

Objectif : produire une revue critique et actionnable, sans modifier les fichiers, sans publier et sans utiliser de secrets. Ne prétends pas que l'exécution locale est une sandbox. Ne lance ni scripts ni dépôts inconnus ; n'utilise que les exemples présents et de confiance.

1. Identifie les risques de sécurité liés à la compilation et à l'exécution (fichiers, réseau, processus, ressources, faux sentiment de sécurité).
2. Propose une architecture d'isolation Ubuntu pour les prochaines versions, en distinguant protections réelles, prérequis et limites ; justifie le choix. Précise comment tester l'isolation.
3. Évalue la solidité des tests de `ft_putchar`, le contrôle du prototype et les limites de `nm`, avec des cas manquants conformes au sujet. Ne suppose pas que les comportements non définis par le sujet sont obligatoires.
4. Propose comment intégrer la Norminette en mode autodidacte sans cacher d'autres erreurs, en précisant ce qui dépend de sa version. Ne présume pas que ses options ou son format sont stables : cite tes sources et versions.
5. Signale les problèmes de fiabilité, portabilité Ubuntu et faux positifs. Classe les actions par gravité et donne pour chacune un correctif et un test.

Livrable : rapport Markdown, avec constats fondés sur les fichiers lus, hypothèses et incertitudes séparées, et liens sources si tu utilises le Web. Ne modifie rien ; ne pousse rien. Je transmettrai ce rapport à l'équipe principale pour décision.
