# Développement : contrôle préalable d'un scope cgroup

## État

La v0.9 a été testée sur l'Ubuntu de l'utilisateur : le scope témoin a refusé une nouvelle tâche à `pids.max=8`, le compteur `pids.events` a augmenté et les 7 enfants créés ont été attendus. C'est un résultat de faisabilité, pas une validation de la mémoire ou de la sécurité globale.

Dans cette branche de développement, `moulinette/cgroup_gate.py` contient une vérification isolée et ses tests : elle exige un nom de scope propre au projet, un chemin de cgroup v2 mappable sous la hiérarchie visible, la présence du PID appelant dans `cgroup.procs`, et des limites `pids.max`, `memory.max` et `cpu.max` finies, compatibles avec la politique demandée. Elle échoue fermé si un contrôle est impossible. Les tests emploient une hiérarchie fictive : ils ne prouvent pas son comportement dans un scope Ubuntu réel.

**Ce module n'est pas appelé par `check`. Il ne crée pas de scope et ne lance aucun programme. Il n'ajoute donc pas de protection à la v0.9.** La branche n'est pas une version distribuée et tous les modes restent réservés au code de confiance.

## Étapes nécessaires pour un futur lanceur

1. Générer un nom de scope imprévisible propre à chaque correction et démarrer un superviseur de confiance sous `systemd-run --user --scope`, avec les propriétés nécessaires et sans élévation de privilège. Aucune source étudiante ni compilation ne doit démarrer à cette étape.
2. Depuis le superviseur, appeler la vérification du scope en se basant sur son propre PID et les limites réellement lues. Refuser un groupe inattendu, des fichiers illisibles, l'absence de contrôleurs ou une configuration trop permissive.
3. Concevoir un canal d'état et une synchronisation empêchant tout début d'évaluation avant la confirmation du groupe par le processus parent. Tester la transmission des descripteurs dans `systemd-run` sur Ubuntu : si le canal n'est pas disponible, arrêter sans lancer la correction. Ne pas traiter stdout d'un programme étudiant comme preuve d'isolement.
4. Exécuter les étapes Bubblewrap, leur compilateur et tous leurs descendants à l'intérieur de ce scope, tout en préservant les autres limites. Le scope doit englober l'exécution dès son tout premier processus ; déplacer après démarrage crée une fenêtre non protégée. Les contrôles par étape et la gestion du timeout doivent distinguer panne, OOM, fin fonctionnelle et état ambigu.
5. Contrôler nettoyage du groupe et des descendants y compris en cas d'échec, signal, arrêt du parent, perte du bus ou dépassement de délai. Définir les limites des tests sans saturer l'hôte, puis faire auditer l'architecture.

## Risques non couverts par le module actuel

La seule lecture de contrôleurs cgroup ne prouve pas leur résistance à un adversaire disposant du même UID ; symlinks, remplacement du chemin, migrations, délégation, namespace cgroup ou modification après vérification nécessitent une conception renforcée. Les limites mémoire et processus n'isolent pas les fichiers, le réseau, le stockage ou le noyau partagé. `CPUQuota` limite un débit moyen, pas directement la durée totale. Un filtrage seccomp avant l'`execve` initial empêcherait le lancement du programme. Rien ici n'autorise du code non fiable.

## Canal de contrôle en cours de développement

`scope_protocol.py` fournit un encadrement JSON borné pour une future synchronisation parent/superviseur. La réception gère les fragments et refuse les messages incomplets, trop longs, mal formés, les clés JSON dupliquées et les délais ; les tests utilisent des sockets locaux et ne lancent aucun rendu. Ce module **n'est pas encore relié** au lancement sous systemd ni au correcteur. Il ne prouve ni l'identité du pair ni l'isolement ; l'héritage du descripteur, l'authentification du scope, le protocole d'autorisation, les signaux et le nettoyage restent à concevoir et vérifier sur Ubuntu.


## Implémentation candidate v0.10

Un nouveau mode explicite `--experimental-cgroup-sandbox` relie le superviseur au correcteur. Le superviseur vérifie son scope, envoie son PID au parent par un socket Unix dans un répertoire temporaire privé, puis attend l'autorisation. Le parent vérifie à son tour le scope et les valeurs ; le superviseur revérifie avant `check_ex00`. Le parent demande l'arrêt de l'unité et n'accepte pas un résultat si le groupe est encore peuplé ou son état inconnu. Les tests de ce mécanisme utilisent des scopes et superviseurs simulés ; la combinaison réelle n'est pas validée dans l'environnement assistant sans bus utilisateur.

Le socket et ses permissions ne protègent pas contre d'autres processus ayant le même UID. Les vérifications par lecture de fichiers système comportent encore des courses possibles, et la disparition du scope ne prouve pas qu'un processus n'a pas pu être déplacé ailleurs. Aucun de ces contrôles ne certifie la sécurité face au code non fiable. En cas de SIGKILL du parent ou d'échec du gestionnaire systemd, le nettoyage complet est à auditer. La charge mémoire, l'épuisement et la résistance du noyau ne sont pas validés.
