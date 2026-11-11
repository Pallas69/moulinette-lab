# Étape 3 — v0.23-dev, travail expérimental après revue v0.22

Usage réservé au code et aux dépôts de confiance. Aucun mode ne constitue une protection validée contre du code hostile. Les limites mémoire et CPU sous charge restent non validées ; aucun témoin OOM n'a été lancé. Les témoins de charge de la v0.22 restent désactivés dans la v0.23, y compris avec l'ancien opt-in. Ne pas lancer le témoin OOM de la v0.20 sur la session utilisateur.

## Analyse de la revue transmise

L'archive v0.22-dev locale a pour SHA-256 `e05b0e14c517f4e0ad4709af089933958dc7ba93840508d67311c5aa4244d893` ; les fichiers concernés ont aussi été comparés octet par octet à leur copie extraite de cette archive. La revue transmise annonce la même empreinte et des essais réussis, mais comporte de **nombreuses descriptions qui ne correspondent pas au code de cette archive**. Il n'est donc pas possible de traiter toutes ses conclusions détaillées comme une vérification fiable de ce code ; demander une revue corrigée fondée sur l'archive exacte.

Exemples contrôlés :
- Le worker Git monte **neuf modules** Python, et non cinq. `RLIMIT_CPU` est `(30,46)` pour le worker et `(45,46)` pour Git, pas 20 et 15 secondes.
- Il n'existe ni fichier `moulinette/exercises.py`, ni option `--norm-mode off`, ni option `--github-subdir`. Les contrôles requis réels sont définis dans `cgroup_launcher._required_passes` et le catalogue `exercise_catalog.py`.
- La sonde désactivée ne contient pas `run_cgroup_load_selftest` : `witness_main` écrit un JSON indisponible et l'entrée `__main__` sort avec 2.
- Le rapport local construit par `checker` n'a pas de champ `source.path`, contrairement au scénario V22-03 présenté. Le test d'un nom de dossier local contenant un octet non UTF-8 passe déjà sur la v0.22 pour le cas exercé. Cela ne prouve pas que toute autre entrée est sûre.
- La description précise de l'ouverture SQLite et plusieurs noms de tests/fonctions ne correspondent pas non plus à l'archive. Ces divergences n'invalident pas les questions techniques, mais leurs causes ne sont pas établies.

## Corrections effectuées

**V22-01 — interruptions.** Le `KeyboardInterrupt` pendant `store_attempt` est traité : la CLI retourne un rapport incomplet avec code 2 et indique que l'état de l'historique est inconnu. Une interruption en dehors des phases déjà traitées remonte au gestionnaire de dernier ressort, qui écrit un message d'incertitude sur stderr et renvoie 2. Un test simule deux SIGTERM séparés, le premier dans un lanceur cgroup imbriqué et le second pendant l'historique ; le lanceur y est simulé et aucune unité systemd n'est lancée. Les contextes imbriqués conservent chacun leur propre état de signal : leur architecture n'a pas été refondue. L'historique peut avoir été écrit juste avant l'interruption ; aucune annulation n'est promise. Si une interruption arrive pendant l'écriture elle-même, la sortie JSON peut être absente ou partielle ; SIGKILL, un deuxième signal, les threads et l'état du noyau peuvent encore empêcher tout nettoyage ou rapport.

**V22-02 — cumul et propagation des incertitudes.** Le runner et la capture préservent les diagnostics de nettoyage précédents au lieu de les écraser ; un échec de signalement du groupe et une attente expirée sont tous deux conservés. Le correcteur les inclut dans son rapport `unavailable`, et la couche Git les inclut lors de la conversion des exceptions. Les scénarios ont été testés au moyen de substitutions et fichiers temporaires ; ils ne prouvent pas l'arrêt de tous les descendants. Les incertitudes de nettoyage et courses même UID décrites en v0.22 restent ouvertes.

**V22-03 — données non UTF-8.** Le scénario d'un champ `source.path` local ne s'applique pas à ce code. En revanche, un appel direct de `store_attempt` avec une provenance GitHub contenant un surrogate non filtré pouvait empêcher l'enregistrement SQLite. Son étiquette est désormais échappée avec `safe_text`, comme l'étiquette locale. Les entrées Git reçues par la CLI sont toujours contrôlées en amont. Aucun remplacement global des chemins opérationnels n'a été effectué : les noms réels ne doivent pas être altérés pour les opérations de fichiers.

## Éléments non résolus

Pas de validation en charge de `memory.max` / `cpu.max`, pas de budget global pour le téléchargement Git hors cgroup, réseau partagé, pas de seccomp, noyau partagé, courses SQLite et fichiers locaux même UID, descendants détachés et nettoyage après interruption brutale. Une VM jetable et un protocole spécifique revu sont nécessaires pour les futurs essais OOM. L'étape 3 reste inachevée. Voir `validation-v0.23-dev.md` pour les essais réellement effectués.
