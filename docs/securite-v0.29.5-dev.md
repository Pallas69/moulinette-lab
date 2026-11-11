# Gestion des commandes bloquées et nettoyage — v0.29.5-dev

## Objectif et limites

Réduire les conséquences de blocages accidentels dans du code de confiance. Aucun mode ne rend sûr un dépôt ou programme hostile. Pas d'essai OOM, de saturation CPU, de remplissage mémoire ou de stockage dans les nouveaux tests.

## Commandes du moteur de projet

En mode Bubblewrap uniquement, chaque commande (compilation, Makefile, script et cas de test) est placée dans un nouveau groupe et une nouvelle session. À la fin normale ou au délai, le superviseur envoie SIGKILL au groupe. Il observe les membres du groupe via `/proc` pendant que le PID du chef est conservé non récolté ; les zombies ne s'exécutent plus mais leur récolte n'est pas prouvée. L'état illisible, l'échec du signal ou l'absence d'arrêt confirmé dans le court délai rend le projet indisponible. Un délai ou une commande indisponible pendant un cas interrompt les cas suivants et la Norminette ; aucun repli automatique.

La supervision individuelle est activée uniquement dans le namespace PID Bubblewrap, dont la destruction arrête les processus restants si le superviseur disparaît. En mode local non isolé, les commandes restent dans le groupe externe d'origine ; à un délai, le worker termine le projet sans commencer d'autre cas, et le superviseur externe signale le groupe avant de continuer. Ceci ne protège pas les fichiers de l'utilisateur.

**Limites :** l'observation du groupe ne couvre pas les descendants qui changent de groupe ou de session ; en mode local notamment, un descendant détaché peut subsister. Une course, un processus en état noyau non interruptible, SIGKILL, une coupure brutale, ou l'indisponibilité de `/proc` ne sont pas complètement maîtrisés. Le cgroup peut aider à l'arrêt collectif mais reste expérimental ; les limites sous charge ne sont pas validées. Un état ambigu ne doit pas être présenté comme un succès.

## Délai du canal cgroup

La réception du résultat après l'envoi de la demande dispose de **230 secondes au total**, même si le message arrive en plusieurs fragments. Le budget prévoit les 110 s de supervision du job projet, les 90 s de Norminette et une marge de 30 s pour les autres opérations. Une phase préliminaire, la création du scope, le nettoyage, l'entrée/sortie de fichiers ou l'ordonnancement peuvent toutefois ajouter du temps ou consommer la marge : ce n'est pas une borne globale de toute la commande. Le handshake a un délai distinct. Un délai ou protocole indéterminé retourne un résultat indisponible et déclenche le nettoyage du scope ; aucun repli local.

## Vérifications

Les nouveaux tests utilisent de courts processus dormants auto-bornés, une simulation d'erreur de signal, des messages fragmentés et un exemple de projet témoin dans Bubblewrap réel. La sélection sans charge compte 332 tests réussis en 155,465 s dans l'environnement de développement, sans skip affiché ; quatre témoins actifs sont exclus. Le test du délai cgroup est simulé et ne dure pas 230 s. La v0.29.5 reste à valider sur l'Ubuntu utilisateur et dans un scope réel ; les résultats cgroup de la v0.29.4 ne valident pas automatiquement cette version.
