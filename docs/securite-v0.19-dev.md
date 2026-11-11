# Étape 3 — tranche de travail v0.19-dev

## Statut : sécurité non terminée

Branche de développement issue de la v0.18, pas une certification ni une autorisation d'utiliser du code non fiable. Les modes demeurent expérimentaux et réservés aux sources et dépôts de confiance. Cette tranche ne couvre pas les quotas disque globaux, seccomp, la résistance au même UID, les chemins parents, l'arrêt en SIGKILL du parent ni toutes les conséquences des processus détachés. Le noyau reste partagé. Le téléchargement Git continue sur l'hôte avec accès réseau.

## Modifications

- Les captures stdout et stderr du correcteur et de Git passent par deux tubes drainés simultanément. Le correcteur conserve au plus 131 072 octets par flux ; Git conserve au plus 4 097 et 2 049 octets. Le surplus est jeté tout en continuant à drainer jusqu'à la fin ou au délai. Cela borne les captures en mémoire et n'implique pas que le programme produit moins de données ; `RLIMIT_FSIZE` ne limite pas les octets écrits dans un tube.
- Sous Linux, le superviseur utilise `waitid(WNOWAIT)` afin de constater la fin du chef sans le récolter avant de demander l'arrêt de son groupe. Cela évite le recyclage de son PID pendant cette séquence, sans démontrer la disparition de tous les descendants ou protéger d'un tiers possédant le même UID. Si cet état n'est pas disponible ou si le chef a été récolté ailleurs, arrêt prudent.
- L'attente après demande d'arrêt est bornée ; si les sorties restent ouvertes ou que le processus ne peut pas être récolté dans le délai, l'erreur devient un résultat incomplet. Après un vrai timeout, le groupe est signalé avant récolte ; le mode Bubblewrap conserve sa classification prudente `unavailable` en cas de délai ambigu.
- Ces changements ont été conçus à partir de la branche de tubes non livrée, mais ne sont pas une intégration brute de cette branche : une attente `proc.wait()` sans délai a notamment été supprimée et des scénarios de nettoyage indéterminé ont été ajoutés. L'invariant « l'objet inspecté est celui lié et testé » reste inchangé.

## Vérifications de cette tranche

- **202 tests de la suite standard réussis sans skip** dans l'environnement de développement, avec Bubblewrap 0.12.0 et Norminette 3.3.59 réels ; cgroups simulés. Le scope réel n'a pas pu être lancé ici faute de bus systemd utilisateur.
- Témoins de confiance réels : sorties stdout/stderr dépassant les plafonds, production continue jusqu'au délai, descripteurs stdout non positionnables et non lisibles, tubes fermés avant la fin, descendant du même groupe arrêté, descendant `setsid` gardant un tube ouvert menant à une erreur plutôt qu'à un succès, et Bubblewrap réellement utilisé. Un témoin Bubblewrap ne détecte pas de descripteur ouvert entre 3 et 1023 dans le programme testé : observation limitée à ce scénario, pas une preuve générale.
- `RLIMIT_AS` et `RLIMIT_CPU` ont été observées en charge dans deux processus témoins de confiance, hors cgroup. **Ce ne sont pas des tests de charge des limites cgroup mémoire ou CPU.**
- Tests simulés : échec de récolte après arrêt, PID déjà récolté, capture Git trop longue et nettoyage Git non confirmé ; vérification qu'un résultat incertain n'est pas validé.
- Simulation Git locale distincte : les quatre scénarios ex00 (rendu correct, erroné, fichier supplémentaire, chemin interdit) et l'historique isolé passent. Accès HTTPS réel distinct : `Tednoob17/mini-moulinette`, branche et SHA épinglé ; exemple ex00 préalablement vérifié du dépôt `ChuOkupai/piscine42` au SHA `cc5e12c0776839a33ef12658192a0f46abdcf095`, réussi avec Bubblewrap/Norminette réels. Le cgroup réel de ce parcours n'a pas été exercé.

## Points bloquants pour annoncer l'étape 3 terminée

1. Tester la nouvelle capture combinée au scope systemd réel sur Ubuntu, notamment les scénarios de nettoyage et de charge mémoire/CPU. Le témoin existant `tests_real/test_real_cgroup.py` ne couvre qu'un exemple simple de confiance et ne constitue pas ce programme de validation.
2. Concevoir et valider l'encadrement global du téléchargement et du stockage Git : le plafond par fichier n'est pas un quota disque total, et le réseau n'est pas isolé. Ne pas recevoir de dépôts non fiables en attendant.
3. Résoudre ou accepter explicitement, avec justification et preuves, les limites concernant descendants détachés, nettoyage après mort brutale, confiance du même UID, montage d'outils, chemins parents et politique syscall/seccomp.
4. Faire une revue de sécurité indépendante des changements et de leurs limites ; des tests positifs et une revue interne ne suffisent pas.

Le guide PDF embarqué est encore celui de la v0.18. Aucun système de sécurité ne doit être désactivé pour faire passer les tests.

## Résultat Ubuntu communiqué par l'utilisateur

Sur l'Ubuntu de l'utilisateur, depuis le dossier extrait v0.19-dev : **202 tests standard réussis sans skip en 26,285 s**, puis `test_trusted_example_with_real_scope_and_bwrap` réussi (**1 test en 0,683 s**). Ce dernier confirme le parcours ex00 de confiance avec le nouveau superviseur, Bubblewrap et un scope systemd utilisateur réellement vérifié. Il ne met pas en charge les limites mémoire ou CPU, ne teste pas le nouveau parcours GitHub en scope réel et ne valide pas la résistance au code hostile. Le point 1 ci-dessus reste donc partiellement ouvert ; les autres points restent également ouverts.
