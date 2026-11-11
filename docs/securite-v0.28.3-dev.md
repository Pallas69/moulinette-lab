# Examen des limites et du nettoyage — v0.28.3-dev

## Portée

Travail pour du code et des dépôts de confiance, notamment pour réduire l'impact des erreurs accidentelles. Cet examen et ses tests ne prouvent pas la résistance au code hostile, ni l'efficacité des limites sous charge. Pas de témoin OOM, de boucle CPU active, de remplissage de tmpfs ou d'épuisement de tâches dans les tests réalisés pour cette version.

## 1. Limites examinées

### Scope systemd/cgroup expérimental

Le lanceur demande `TasksMax=32`, `MemoryMax=512M`, `MemorySwapMax=0` et `CPUQuota=100%`. Le worker vérifie son appartenance et les valeurs effectives avant la correction et juste avant son démarrage ; le lanceur effectue aussi sa propre vérification. Des limites plus strictes sont acceptées. Les 32 tâches incluent les processus et threads du scope, superviseurs compris. Le CPU à 100 % limite le débit collectif à l'équivalent d'un cœur, ce n'est pas une limite de durée totale.

`memory.max` est la limite cgroup du groupe, différente de `RLIMIT_AS` par processus ; elle ne prouve pas qu'une charge mémoire n'affectera jamais la session. La hiérarchie et les mécanismes du système restent partagés. Ni l'application réelle sous charge de ces limites, ni le comportement en OOM ne sont validés ici. Le système peut ne pas permettre ce mode : pas de repli automatique local.

### Durées et limites par processus

- Mono-fichier : compilation généralement 10 s, test généralement 1 s, selon le catalogue ; `RLIMIT_CPU` 2/3 s et `RLIMIT_AS` 256 Mio pour les tests ; respectivement 10/11 s et 1 Gio pour les autres étapes. `RLIMIT_FSIZE` est 1 Mio ou 16 Mio ; les core dumps sont désactivés. Le temps CPU est par processus et l'espace d'adressage virtuel ne correspond pas directement à la mémoire résidente.
- Projets : le superviseur parent est limité à 110 s, CPU 90 s par processus, espace d'adressage 1 Gio par processus, taille par fichier 16 Mio ; le Makefile a 25 s, les autres commandes souvent 10 s et chaque test 2 s par défaut, avec exceptions du catalogue. La phase Norminette séparée a un budget global de 90 s et 15 s par invocation. `/work` et `/tmp` Bubblewrap sont bornés, mais ces tailles ne constituent pas un quota global du système.
- Le canal du lanceur cgroup a un timeout socket de 120 s **par opération**, pas une échéance globale de correction. Il peut donc couper prématurément un projet qui prendrait jusqu'à 110 s puis 90 s de style. C'est une limite de disponibilité connue, non corrigée dans cette étape ; l'échec ne doit pas devenir une réussite. La durée totale n'est pas garantie par cette seule valeur. Les délais s'ajoutent aux phases de lancement et de nettoyage.
- En mode local non isolé, les limites par processus ne protègent pas les fichiers et ne forment pas un budget collectif comparable à un cgroup.

Les tests sur ces valeurs utilisent des appels `setrlimit` simulés : ils vérifient le code de configuration, pas l'application réelle des limites par le noyau.

## 2. Arrêt et nettoyage

La capture garde le chef de groupe non récolté avant de signaler son groupe ; un délai ou une interruption déclenche le nettoyage. Des témoins légers de confiance ont vérifié l'arrêt d'un processus endormi et d'un enfant resté dans le même groupe, ainsi que SIGTERM pendant une capture. Un ancien témoin Bubblewrap séparé vérifie un descendant détaché dans un cas précis. Un zombie peut rester dans `/proc` même s'il ne s'exécute plus ; l'observation ne prouve pas qu'il a été récolté par son parent.

Le lanceur cgroup demande l'arrêt du scope puis vérifie son état `populated` ; en cas d'état inconnu ou de groupe encore peuplé, il refuse le rapport favorable. Si le scope n'a pas été validé, le nettoyage est signalé comme non confirmé. Pour un projet, à l'expiration d'une commande, `project_job` tue d'abord le processus direct ; le nettoyage des descendants dépend des couches externes et n'est pas garanti immédiatement avant les étapes suivantes.

**Correctif ciblé :** lorsque `cgroup.events` est absent alors que le répertoire du scope existe encore, le résultat est désormais inconnu plutôt que vide. Si le répertoire du scope a disparu mais que son parent est accessible, le lanceur considère le scope absent, comme auparavant. Accès ou état ambigu : résultat non confirmé. Cela réduit un faux constat de nettoyage, sans supprimer les courses de système de fichiers ou les risques liés à un même UID.

SIGKILL, coupure brutale, processus détachés en dehors du groupe surveillé et états noyau non interruptibles ne sont pas tous contrôlables par les signaux. L'arrêt du scope et la lecture `cgroup.events` ne prouvent pas l'absence de toute course ou de tout effet externe. Les cas nouveaux en cgroup sont simulés ; aucun scope systemd réel n'était disponible dans l'environnement de développement.

## 3. Tests légers, erreurs et interruptions

`tests/test_cgroup_safety_light.py` couvre configurations RLIMIT simulées, états cgroup réels sur fichiers fictifs, refus des états inconnus, délai d'un témoin endormi avec un enfant dans son groupe et SIGTERM pendant une capture d'un témoin endormi. Ils ne lancent ni allocation mémoire importante ni boucle active.

`python3 tools/test_sans_charge.py` lance la suite standard de cette version sauf quatre témoins explicitement listés : remplissage d'un tmpfs limité, production continue sur tubes, boucle CPU RLIMIT et tentative d'allocation refusée par RLIMIT. Les autres tests lancent notamment compilateurs, Bubblewrap et programmes de confiance : ils ne sont pas à consommation nulle. `cgroup-selftest` et `tests_real/` ne sont pas lancés par cette commande. Les exclusions doivent être revues si la suite évolue.

Le test séparé `tests_real/test_real_cgroup.py` comporte aussi l'exemple de confiance C12/ex08 pour le moteur projet. Il peut être lancé volontairement sur Ubuntu avec `python3 -m unittest discover -s tests_real -p test_real_cgroup.py -v` si systemd utilisateur, Bubblewrap et Norminette sont disponibles ; il ne sature pas les ressources et ne démontre pas les limites sous charge. Ce test n'a pas été exécuté dans l'environnement de développement faute de bus systemd utilisateur.

## 4. Validation Ubuntu précédente et limites

L'utilisateur a communiqué pour la **v0.28.2-dev** : `Ran 308 tests in 199.591s` puis `OK`, sans skip affiché. Cela valide l'exécution de cette suite sur sa machine, pas le scope réel de la v0.28.2 ni la sécurité. La v0.28.3 n'a pas encore été testée sur son Ubuntu.

**Précision historique :** la suite standard v0.28.2 comprend de courts témoins actifs CPU et de remplissage d'un tmpfs de 1 Mio, ainsi qu'une tentative d'allocation refusée par RLIMIT. La formulation antérieure « aucun test de saturation » était trop large pour la suite standard. Aucun témoin OOM forcé n'a été réalisé ou demandé. Pour la v0.28.3, ces témoins ont été exclus de la sélection ci-dessus.

La sélection sans charge a réussi **313 tests en 138,756 s**, sans skip affiché, dans l'environnement de développement avec Bubblewrap et Norminette 3.3.59 ; le test navigateur a aussi réussi. Voir `ETAT-CHANTIER.md`. Une analyse des délais cumulés, les vrais cgroups, la résistance aux interruptions et la validation sous charge en VM restent à poursuivre. Noyau partagé, pas de seccomp et autres limites documentées en v0.28.2 restent applicables.
