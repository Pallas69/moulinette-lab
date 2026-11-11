# Feuille de route — état après audit

## Décisions validées

Ubuntu ; CLI et futur tableau de bord HTML local ; code local ou, plus tard, GitHub en lecture seule ; mode autodidacte transparent ; parcours et langages séparés ; futurs imports de sujets PDF/Markdown avec validation des tests ; thème Night Owl et humour désactivable. L'outil ne prétend pas reproduire les tests ni le score officiels.

## Avancement actuel — v0.29.7-dev

1. **Correcteur et 109 exercices : disponibles en prototype.** Les 14 sujets C 00–C 13 sont intégrés avec des tests fonctionnels, sans tests officiels ni garantie d'exhaustivité. La récursivité/itération de C 05 et le tableau de fonctions de do-op ne sont pas prouvés ; les erreurs/options et Makefiles C 10 restent partiels.
2. **Style : 42 autodidacte.** Norminette 3.3.59 ; seul INVALID_HEADER est ignoré. La prise en charge de C 12 utilise C11 pour les prototypes historiques ; l'adaptation est signalée.
3. **Sécurité : reprise, non terminée.** Code et dépôts de confiance uniquement ; Bubblewrap et cgroup sont expérimentaux. Aucun test OOM n'est demandé ou exécuté. L'Ubuntu utilisateur a validé un parcours cgroup réel de confiance C 12/ex08 en v0.26, pas la sécurité ni tous les parcours.
4. **GitHub : récupération expérimentale de confiance.** Dépôts publics HTTPS et multi-fichiers ; pas de dépôt hostile, privé, SSH ou LFS. La récupération utilise un réseau partagé.
5. **Tableau de bord : refonte v0.27.** Historique SQLite local, 50 derniers résultats, 109 exercices, filtres et score non officiel ; thèmes mémorisés ou aléatoires et couleurs d’état ; page statique à régénérer. Manuel utilisateur statique complet intégré en v0.28 ; deux guides en Blanc ou Océan avec téléchargement direct en v0.29.4.
6. **Import PDF/Markdown : non implémenté.** Les 14 sujets fournis ont été analysés et intégrés manuellement ; un import automatique ne produirait pas à lui seul des tests validés.
7. **Prochaine étape : validation sans charge sur Ubuntu et poursuite de l’analyse.** La v0.28.3-dev a réussi 313 tests légers et quatre exemples en scope réel sur l'Ubuntu utilisateur ; la v0.29.7-dev reste à y vérifier. Voir `securite-v0.28.3-dev.md`.

## Historique des versions

## Travail en 0.7 après la v0.6 validée

La v0.7 est une livraison de test, non encore validée sur Ubuntu. Deux tests de sortie exacte ont été ajoutés après l'étude des tests communautaires. L'inventaire et l'ouverture du fichier source sont maintenant relatifs à un descripteur du dossier ouvert ; le dernier composant du dossier et le fichier source ne peuvent pas être des liens symboliques. Un test simule le remplacement du chemin du dossier entre l'inventaire et l'ouverture : le fichier reste ouvert depuis le dossier initial. Les commandes de compilation et d'analyse sont prédéfinies, leurs entrées montées en lecture seule et un seul fichier de sortie prédéfini est monté en écriture avec RLIMIT_FSIZE ; `/work` et `/tmp` sont des tmpfs bornés. Un témoin simple couvre un cas de nettoyage après timeout. Tests : 51/51 dans l'environnement de développement, avec Bubblewrap 0.12.0 et Norminette 3.3.59.

Ces protections sont partielles : les composants parents peuvent toujours contenir des liens ou être modifiés pendant la résolution, le contenu du fichier peut être modifié pendant sa lecture et l'inventaire n'est pas un instantané atomique. Ces tmpfs ne constituent pas un quota global : les limites CPU/mémoire et le nettoyage ne remplacent pas des cgroups. Le noyau est partagé ; pas de politique seccomp ni audit indépendant complet. Ne pas accepter du code non fiable et ne pas attribuer de garantie de sécurité à ces tests. Prochaine priorité : concevoir et expérimenter des limites de ressources adaptées, puis faire auditer le tout avant de changer ce niveau de confiance.


## Travail en 0.8 après audit v0.7

La v0.7 a réussi 51 tests sans tests ignorés sur Ubuntu 26.04.1 de l'utilisateur, ainsi que la correction de l'exemple avec Norminette 3.3.59. L'audit Antigravity a été analysé ; voir `analyse-audit-v0.7.md`. La v0.8 contient plusieurs correctifs et 60 tests ont réussi dans l'environnement de développement, avec bwrap 0.12.0 et Norminette 3.3.59 ; elle reste à valider sur l'Ubuntu de l'utilisateur. Ce n'est pas une validation de sécurité.

Cgroups (processus, mémoire et CPU), menaces liées au noyau, isolement du compilateur, chemins parents, modifications par le même UID, robustesse des sondes, limitations de la Norminette et audit indépendant restent ouverts. Les tests ex01 et le tableau de bord connecté ne sont pas encore développés.


## Étude en 0.9 : témoin cgroup

Après validation de la v0.8, l'utilisateur a exécuté une première commande systemd sans root : son scope affichait pids.max=32, memory.max=536870912 et cpu.max=100000 100000. Cela confirme ces valeurs pour ce scope seulement. La v0.9 ajoute `sandbox cgroup-selftest` : vérification d'un autre scope temporaire et témoin contrôlé de limitation des tâches, sans code étudiant et sans charge mémoire. Aucune intégration cgroup n'est encore effectuée dans `check`. La limite mémoire en charge et la sécurité globale ne sont pas prouvées. La sonde réelle n'a pas pu être lancée dans l'environnement assistant dépourvu de bus utilisateur ; ses tests automatisés incluent des simulations. Prochaines étapes : valider le témoin sur Ubuntu, puis concevoir un lanceur supervisé qui vérifie les limites avant l'exécution et échoue fermé ; pas de passage au code non fiable sans audit plus complet.


## Candidat v0.10

La sonde v0.9 a été validée sur l'Ubuntu de l'utilisateur : limite de 8 tâches observée et 7 enfants récupérés. Le candidat v0.10 ajoute une première intégration du correcteur dans un scope cgroup vérifié, avec Bubblewrap et sans fallback local. Tests simulés et tests Bubblewrap/Norminette réels dans l'environnement assistant : 88 réussis. La combinaison réelle scope + correction reste à tester sur l'Ubuntu de l'utilisateur et à auditer ; code de confiance uniquement. Les autres exercices ne sont pas encore implémentés.

## État après le test Ubuntu de la v0.10

Sur l'Ubuntu de l'utilisateur, 88 tests ont réussi sans test ignoré. Le premier `check` expérimental sous cgroup a corrigé l'exemple ex00 avec Norminette 3.3.59 : 32 tâches, 512 Mio, swap 0 et quota CPU 100 % étaient affichés. C'est un résultat fonctionnel, pas un audit ni une validation de sécurité contre du code non fiable. L'audit indépendant v0.10 reste à recevoir.

## Candidat v0.11 : C 00/ex01

`c00/ex01` utilise un catalogue interne et les mêmes principes de contrôles et de modes d'exécution que `ex00`. Le testeur explicite sa convention de sortie exacte sans saut de ligne. Les tests ex01 comprennent une sortie correcte, des sorties altérées, deux appels successifs, le prototype, les symboles, Norminette et le dispatch du scope. Les tests d'intégration scope sont simulés dans l'environnement assistant ; la version v0.11 reste à tester sur Ubuntu. `ex02` à `ex08`, GitHub et le tableau de bord connecté restent à faire.

## État après le test Ubuntu v0.11 et candidat v0.12

L'utilisateur a corrigé l'exemple ex01 avec succès sur Ubuntu, avec le mode cgroup et Norminette 3.3.59. L'audit de sécurité indépendant du mode cgroup reste à recevoir et aucun mode n'est autorisé pour du code non fiable.

Le candidat v0.12 ajoute ex02, ex03 et ex04 dans le catalogue interne. Les tests des trois exemples ont réussi dans le Bubblewrap réel de l'environnement assistant avec Norminette 3.3.59 ; les chemins cgroup ont été simulés faute de bus systemd utilisateur. La v0.12 et ses trois nouveaux exercices restent à valider sur l'Ubuntu de l'utilisateur. Ex05 à ex08, GitHub et le tableau de bord connecté restent à faire.

## État après le test Ubuntu v0.12 et candidat v0.13

Sur l'Ubuntu de l'utilisateur, les trois exemples ex02, ex03 et ex04 ont été corrigés avec succès sous Bubblewrap, cgroup et Norminette 3.3.59. L'audit indépendant du lanceur reste à recevoir ; pas de code non fiable.

Le candidat v0.13 ajoute les quatre exercices restants ex05 à ex08 : le catalogue couvre maintenant les neuf exercices C 00 v8. Les sorties de combinaisons sont calculées par le testeur et contrôlées pour l'ordre, les séparateurs et les limites ; la capture a été augmentée pour tester deux sorties ex06 sans troncature. Les 124 tests, dont Bubblewrap et Norminette réels, ont réussi chez l'assistant. La combinaison cgroup + quatre nouveaux exercices reste à tester sur Ubuntu, faute de bus systemd utilisateur dans l'environnement assistant. GitHub et le tableau de bord connecté ne sont pas implémentés.

## Test Ubuntu v0.13 et candidat correctif v0.14

Les tests fonctionnels et Norminette des quatre exemples ex05 à ex08 ont réussi sur l'Ubuntu de l'utilisateur, mais les quatre résultats étaient **incomplets** : `__stack_chk_fail`, dont l'origine n'était pas établie, figurait dans les objets. Il ne faut pas annoncer leur validation globale.

La v0.14 tente en cas d'ambiguïté une seconde compilation avec `-fno-stack-protector`. Elle analyse ce second objet et lie le harnais à cet objet exact. La protection de pile du rendu est alors désactivée : c'est une adaptation explicite et une mitigation en moins, pas une amélioration de sécurité. Le symbole encore présent reste ambigu et entraîne un résultat incomplet. Sans ambiguïté, aucun changement des protections de compilation par défaut. Simulation d'un compilateur durci avec Bubblewrap réel et Norminette : quatre exemples réussis. Le mode cgroup complet sur l'Ubuntu utilisateur avec le correctif reste à vérifier ; l'audit indépendant reste ouvert et aucun mode n'est autorisé pour du code non fiable.

## Test Ubuntu v0.14 et candidat v0.15

Sur l'Ubuntu de l'utilisateur, ex05 a réussi en v0.14 avec scope cgroup, Norminette et recompilation explicitée sans protection de pile. Ex06–ex08 restent non retestés globalement depuis v0.13.

En revue interne, une lacune de robustesse a été identifiée dans l'interprétation de la sortie de `nm` : format inconnu ou capture tronquée pouvaient être ignorés. La v0.15 les classe en analyse indisponible, avec arrêt en mode Bubblewrap. Cinq régressions couvrent ces cas, dont un arrêt sous Bubblewrap réel avec résultat `nm` simulé. Un rapport de revue interne et un prompt d'audit indépendant mis à jour sont fournis ; cette revue ne remplace pas l'audit. Sécurité toujours incomplète, code de confiance uniquement.

## Audit indépendant v0.15 et candidat v0.16

L'utilisateur a confirmé sur Ubuntu 135 tests sans skip et le succès global de ex05–ex08 en v0.15 sous Bubblewrap, cgroup et Norminette. Antigravity a remis son audit en lecture seule. Voir `analyse-audit-v0.15.md` pour la vérification des constats et leurs limites.

La v0.16 regroupe des corrections : arrêt avant liaison/exécution si l'analyse de symboles est interdite ou indéterminée, contrôle d'identité du pair socket, refus des rapports de succès incomplets, sorties du superviseur séparées, traitement partiel de SIGTERM/SIGHUP, attente bornée du nettoyage, et limites supplémentaires sur le chemin du venv. 151 tests réussissent chez l'assistant avec Bubblewrap et Norminette réels, mais le scope v0.16 y reste simulé. Un test d'intégration réel séparé existe mais n'a pas été exécuté ici. Nettoyage après SIGKILL, pression mémoire/CPU, même UID et absence de seccomp restent ouverts. Étape 3 non terminée ; code de confiance seulement.


## Préférences d'interface retenues après v0.17

L'utilisateur indique que la page fonctionne bien. Dans la branche de travail suivante, la mention « L'atelier des autodidactes » est retirée de l'interface générée ; ce changement n'est pas rétroactif sur sa v0.17 installée. Proposition pour plus tard, non prioritaire : changer les couleurs aléatoirement à chaque accès. Cette fonction n'est pas implémentée et devra préserver lisibilité et accessibilité.


## Première tranche GitHub — v0.18

Version issue de la v0.17 validée visuellement, avec retrait de la mention demandé et GitHub public de confiance. 187 tests ont réussi dans l'environnement de développement avec Bubblewrap et Norminette réels ; scope cgroup simulé. Récupération réelle distincte sur `Tednoob17/mini-moulinette` : HEAD, branche `main` et SHA complet vérifiés ; une correction réelle sur le fichier de test du dépôt a été correctement refusée à la compilation car ce fichier dépend d'un rendu externe. Un autre dépôt public, après vérification du source et épinglage du commit, a produit un résultat réussi pour ex00 sous Bubblewrap et Norminette réels. Ce ne sont pas des tests de sécurité ni une validation générale des dépôts. Les opérations Git ont lieu sur l'hôte, pas en sandbox. Code et dépôts de confiance uniquement ; sécurité inachevée.


## Travail sécurité en v0.19-dev : capture et nettoyage

La capture des sorties du correcteur et de Git a été retravaillée pour éviter les fichiers temporaires stdout/stderr hôte et les attentes de récolte non bornées. 202 tests standard ont réussi sans skip dans l'environnement assistant ; Bubblewrap et Norminette réels, cgroup simulé. Des témoins réels ont exercé RLIMIT mémoire et CPU hors cgroup. La portée exacte, les tests et les points bloquants figurent dans `securite-v0.19-dev.md`. Étape 3 toujours inachevée ; code et dépôts de confiance seulement.

### Validation Ubuntu du candidat sécurité

L'utilisateur a obtenu 202/202 tests standard sans skip et 1/1 test d'exemple de confiance sous scope systemd réel pour la v0.19-dev. C'est une validation fonctionnelle supplémentaire de la nouvelle capture avec le cgroup ; les tests de charge cgroup, quotas disque globaux et audit indépendant restent ouverts. L'étape 3 n'est pas terminée.


## Travail sécurité v0.20-dev

Le chemin CLI GitHub passe désormais par un montage tmpfs Bubblewrap de 128 Mio, avec réseau partagé et sans repli sur l'hôte. La portée et les limites sont documentées dans `securite-v0.20-dev.md`. Les anciens témoins de charge CPU et mémoire sont **désactivés en v0.21**, en particulier celui qui provoquait un OOM ; aucune validation réelle de memory.max en charge n'est acquise. L'étape 3 reste inachevée ; code et dépôts de confiance uniquement.

## Correctifs après audit — v0.21-dev

Voir `securite-v0.21-dev.md` pour le relevé des vérifications, divergences et limites. Les essais OOM restent suspendus : une VM jetable et une nouvelle revue du protocole sont nécessaires.

## Correctifs après audit — v0.22-dev

La revue indépendante de l’archive v0.21 a conduit à des correctifs expérimentaux et à de nouveaux tests, détaillés dans `securite-v0.22-dev.md`. Les essais OOM restent désactivés et les limites en charge non validées.

## Correctifs après revue v0.22 — v0.23-dev

Une nouvelle branche corrige des interruptions en dehors de la phase de correction et la conservation des diagnostics de nettoyage. Certains constats de la revue décrivent un code différent de l’archive ; voir `securite-v0.23-dev.md`. Les témoins de charge restent désactivés.

## Extension fonctionnelle v0.24-dev — C 01

Les 9 exercices C 01 v6 sont ajoutés aux 9 exercices C 00 v8. Les 14 paires PDF/Markdown ont été inventoriées ; seul C 01 a été analysé en détail pour cette tranche. Tests pédagogiques non officiels ; développement de sécurité en pause. Voir `sujet-c01-v6.md` et `inventaire-sujets-piscine-c.md`.

## Extension fonctionnelle v0.25-dev — C 02

Les 13 exercices C 02 v6 sont ajoutés aux exercices C 00 et C 01 : 31 exercices intégrés. Tests pédagogiques non officiels ; sécurité en pause. Voir `sujet-c02-v6.md`.
