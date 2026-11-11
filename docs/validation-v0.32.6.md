# Validation et limites — v0.32.6-dev

## Historique et reset

Tests utilisant uniquement des bases SQLite fictives et distinctes : déblocages persistants après régression et indépendants selon la base, tableau statique et compteur live sélectionnés, écriture live dans la base demandée, conservation de la base et de la page par défaut, démon par défaut non réutilisé et non remplacé pour une base personnalisée. Le tableau HTML statique d'une base personnalisée est distinct ; il ne contient pas le jeton du démon par défaut. `check` sans option de base continue d'utiliser l'historique par défaut.

Tests du reset : entrée refusée ou fermée sans suppression, cible par défaut et cible explicite, confirmation RESET et `--yes`, sauvegarde vérifiée contenant les données antérieures et droits 0600, suppression des tentatives et déblocages, données WAL présentes dans la sauvegarde, échec simulé de sauvegarde sans effacement, refus de base inexistante ou étrangère. Le navigateur a montré deux électrons/orbites avant puis zéro après reset sur une base fictive ; sauvegarde de deux tentatives contrôlée.

Limites : un processus autorisé peut écrire après le reset ; arrêter le mode live et les corrections avant la commande. Les courses de fichiers et processus appartenant au même utilisateur ne sont pas éliminées. La sauvegarde contient des informations personnelles. Test local sans historique réel utilisateur ; résultats à valider sur l'Ubuntu utilisateur.

## v0.32.5, puis v0.32.6

Sur la v0.32.5, la sélection élargie a exécuté 376 tests, avec 70 ignorés et 3 échecs : deux sous-cas d'un test comparaient les nouveaux PDF aux anciens fichiers v0.29.8 ; un test supposait pandas absent alors qu'il était disponible. Ce résultat n'est pas une réussite de la suite v0.32.5. Les deux tests ont été corrigés dans la v0.32.6 : référence PDF actualisée et absence de pandas simulée, sans changer le correcteur Python. Aucun nouveau sujet ou test de conformité C++/Python n'est revendiqué.

Sur v0.32.6, sélection sans charge après revue : 386 tests exécutés, 70 ignorés, aucun échec. Six témoins de boucle active, production continue, remplissage tmpfs ou limites mémoire/CPU sont explicitement exclus. Environnement de développement distinct de l'Ubuntu utilisateur ; les 70 ignorés ne sont pas des réussites. La suite complète, qui inclut ces témoins, n'a pas été lancée.

Chromium : atome, historique vide, humour, reset, filtres, thèmes, mobile et quatre téléchargements, dont sans JavaScript. Lecture des quatre PDF et égalité textuelle entre variantes vérifiées. Sur la v0.32.5, un historique complètement vide donne zéro orbite et électron lors d'un essai navigateur synthétique ; cela n'est pas une confirmation visuelle par l'utilisateur.

## Sécurité : limites et ordre des travaux

Les régressions de sécurité incluses dans la sélection légère ne suffisent pas à déclarer les quatre étapes achevées. L'étape 3 reste inachevée et un audit indépendant n'a pas été réalisé ; une étape ultérieure ne doit pas être présentée comme validée avant ses prérequis. Aucun témoin OOM, remplissage tmpfs, boucle active ni test de saturation n'a été lancé. Aucun code hostile ne doit être exécuté : Bubblewrap, seccomp, cgroup, contrôle de chemins et nettoyage sont expérimentaux et non exhaustifs. Pas de promesse de sécurité complète ni de conformité officielle.
