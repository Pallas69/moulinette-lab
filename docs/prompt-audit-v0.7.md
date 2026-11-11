# Mission Antigravity — audit de Moulinette Lab v0.7

Tu es chargé d'un audit technique indépendant d'un prototype pédagogique **local**, sans modifier les fichiers du projet. Le correcteur n'est pas considéré sûr pour du code non fiable. L'objectif n'est pas de certifier la sécurité mais d'identifier les faiblesses concrètes, les erreurs de conception et les régressions.

## Contexte

- Ubuntu ; Python 3.10 ou supérieur ; `cc`, `nm` et Bubblewrap. Si disponible : Norminette 3.3.59 dans un venv dédié visible dans le PATH.
- Exercice C 00/ex00 uniquement ; sujet C 00 v8 ; le profil autodidacte ne requiert pas l'en-tête 42.
- Mode `--experimental-sandbox` réservé au code de confiance ; aucun fallback local automatique.
- v0.7 : `/work` de compilation est un tmpfs de 32 Mio, `/tmp` un tmpfs de 32 Mio ; les fichiers d'entrée sont montés en lecture seule et un fichier de sortie précis en écriture sur l'hôte. RLIMIT_FSIZE à 16 Mio est appliqué par processus. Les commandes de compilation et nm ont des arguments fixés. L'ouverture du fichier source s'appuie sur un descripteur de répertoire ; les dossiers parents restent un point à examiner.
- Noyau partagé, cgroups et seccomp absents. Ces limitations sont connues et le mode n'est pas prêt pour du code non fiable.

## Règles de sécurité pour l'audit

Ne télécharge ni n'exécute du code tiers non fiable. N'exécute aucun fork-bomb, saturation de disque/mémoire/CPU ou essai d'évasion dangereux ; les sondes doivent être limitées et auto-terminantes. Ne modifie ni AppArmor, ni le noyau, ni les réglages de sécurité ; ne demande pas de secrets et ne lance aucune commande en root. Utilise des fichiers témoins sans donnée sensible dans un dossier temporaire. Si un test ne peut pas être réalisé sans risque, décris-le au lieu de l'exécuter. Ne modifie pas le projet ; signale les propositions de correctif.

## À vérifier

1. Lire `moulinette/checker.py`, `sandbox_runner.py`, `norm.py`, les sondes et les nouveaux tests. Examiner les montages, les limites, les chemins, les descripteurs hérités, les sorties et l'arrêt en cas ambigu.
2. Vérifier que le fichier de sortie lié à l'hôte est effectivement celui analysé et exécuté et qu'un succès incohérent ne valide rien ; examiner les cas de remplacement, lien symbolique ou écriture concurrente et les limites de `RLIMIT_FSIZE`.
3. Examiner le nettoyage des descendants, les limites de processus et la possibilité d'épuisement des ressources. Distinguer tests réalisés et hypothèses ; ne pas déduire une sécurité générale du seul témoin `timeout`.
4. Vérifier l'ancrage du dossier, y compris les parents et les modifications simultanées : quels risques subsistent ?
5. Vérifier qu'une panne de Bubblewrap, `nm`, Norminette ou du compilateur ne produit pas de succès trompeur ni de fallback local.
6. Contrôler les tests fonctionnels, le contrôle de prototype, l'analyse des symboles et le traitement exclusif de `INVALID_HEADER`.
7. Sur des exemples de confiance et sans privilèges, exécuter `python3 -m unittest discover -s tests -v`, puis la commande du README ; signaler précisément les tests ignorés, versions d'Ubuntu, Python, cc, nm, bwrap et Norminette.

Rends une synthèse hiérarchisée : constat, gravité, scénario ou référence de code, preuve ou limites de la preuve, correction recommandée, et différence entre défaut actuel et amélioration future. Signale explicitement tout échec, test ignoré et point non vérifié. Ne conclus pas que le mode est sûr pour du code non fiable.
