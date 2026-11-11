# Revue interne v0.15 — limites et points vérifiés

Cette revue est faite par le développeur du prototype ; **ce n'est pas un audit indépendant** et elle ne démontre pas la sécurité contre du code hostile. Les modes restent exclusivement réservés au code de confiance. Le sujet effectivement disponible ici est le PDF C Piscine C 00 v8, pas la totalité des sujets de piscine ni les rendus personnels de l'utilisateur.

## Retour Ubuntu

L'utilisateur a exécuté v0.14 ex05 avec Bubblewrap, scope cgroup et Norminette : tous les tests indiqués et le résultat global ont réussi. La recompilation sans protection de pile a été signalée. Pour ex06–ex08, les tests fonctionnels et Norminette avaient réussi en v0.13 mais les résultats globaux étaient incomplets ; ils n'ont pas été revérifiés sur Ubuntu en v0.14 ou v0.15.

## Point corrigé : analyse de sortie nm

Dans v0.14, `read_symbols` ignorait silencieusement les lignes de sortie non reconnues et ne détectait pas une capture atteignant sa limite. Une sortie de `nm` altérée, incompatible ou tronquée pouvait donc être interprétée à tort comme ne révélant aucun symbole interdit. Scénarios de reproduction **simulés**, sans prétendre qu'une attaque réelle a été réalisée : `tests/test_nm_robustness.py` fait renvoyer une ligne mal formée, des octets non UTF-8 ou une sortie atteignant la limite de capture tout en renvoyant code zéro. Sur v0.15, ces cas produisent `incomplete` ; dans le mode Bubblewrap, l'évaluation s'arrête avant la liaison et les tests. La sortie normalement fournie par le `nm` local reste acceptée.

Ce contrôle vérifie un format attendu de sortie GNU/compatible ; un format différent est traité comme indisponible, pas comme un échec étudiant. Il ne prouve pas l'absence d'appels interdits ou d'autres comportements : `nm` est une analyse statique partielle et l'outil système doit être de confiance.

## Limites qui restent ouvertes

- **Isolation non validée contre le code non fiable.** Noyau partagé, pas de seccomp, capacités et attaques du noyau non évaluées. L'option `--unsafe-local` n'isole rien.
- **Cgroup :** les limites et l'appartenance sont contrôlées avant l'exécution, mais les vérifications ne règlent pas les courses ou l'altération par le même UID. En cas de mort brutale du parent ou de migration de processus, le nettoyage n'est pas démontré dans tous les scénarios. Les limites CPU/mémoire en charge n'ont pas été vérifiées par un test sur Ubuntu. Sur l'environnement assistant, la chaîne cgroup est simulée faute de bus utilisateur ; Bubblewrap et Norminette sont réels dans les tests indiqués.
- **Compiler avec `-fno-stack-protector` :** en cas de symbole ambigu, la v0.14/v0.15 peut désactiver la protection de pile du rendu testé, le signale, et analyse puis lie le même objet recompilé. Cela modifie les options de compilation du sujet et peut changer le code conditionnel. La recompilation ne doit pas être considérée comme une mesure de sécurité.
- **Chemins et entrées :** FD de dossier et refus du lien final ne garantissent ni les composants parents, ni un instantané atomique contre une mutation concurrente. La Norminette utilise un venv de confiance monté en lecture seule ; il ne doit contenir aucun secret.
- **Tests et verdict :** tests non officiels, sorties exactes et prototypes partiels. L'absence de symbole détecté ou la réception d'un marqueur ne prouve pas l'absence de code dangereux. C 00 est couvert en prototype, pas certifié conforme aux tests privés 42.

## Suite

Faire examiner la version exacte par un auditeur indépendant avec `docs/prompt-audit-v0.15.md`, puis traiter les constats. Ne pas annoncer l'étape de sécurité terminée avant revue, corrections et vérification appropriées. Les tests de charge contrôlés et mesures de nettoyage, s'ils sont réalisés plus tard, doivent être bornés et non destructifs ; ne pas les déclencher sur la machine de l'utilisateur sans accord.
