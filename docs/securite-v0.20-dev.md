> **DOCUMENT HISTORIQUE v0.20 — OBSOLÈTE POUR CETTE VERSION.** Ne pas lancer son témoin OOM. Voir `securite-v0.21-dev.md`.

# Étape 3 — travail en cours v0.20-dev

**Statut : non terminée et non auditée indépendamment.** Réservée au code et aux dépôts de confiance. La v0.19-dev a été validée fonctionnellement sur l'Ubuntu de l'utilisateur : 202 tests standard et un essai ex00 sous cgroup réel. Les modifications de la v0.20-dev n'ont pas encore été essayées sur cette machine.

## Encadrement du téléchargement GitHub

La commande CLI GitHub démarre un superviseur fixe dans Bubblewrap avant la correction. Dans son espace de noms, le clone, ses fichiers temporaires et le checkout se trouvent sur un unique montage tmpfs `/work` limité à **128 Mio** (`--size` immédiatement avant `--tmpfs`). `/tmp` pointe vers ce même montage. Le code de l'application, `/usr`, les certificats et la configuration minimale DNS sont montés en lecture seule. Le réseau est **partagé avec l'hôte** ; les identifiants et la configuration Git de l'utilisateur ne sont pas transmis. Les hooks et sous-modules restent désactivés ; les URL, références, chemins, SHA, inventaire et données retournées sont validés. Aucun repli Git sur l'hôte n'est permis si Bubblewrap ou le protocole échoue.

L'export vers le correcteur est limité : noms des 1 000 entrées au plus, source plafonnée à 256 Kio + 1 octet, tampon JSON borné à 2 Mio et petit répertoire de staging sur l'hôte. Les fichiers supplémentaires restent visibles sous forme d'entrées témoins ; les liens source restent refusés par le correcteur. Les fichiers ajoutés à l'historique et aux caches système ne sont pas dans ce tmpfs.

**Limites :** 128 Mio s'appliquent au montage tmpfs prévu, pas à l'ensemble du système, des montages possibles, des pages mémoire ou aux autres fichiers de la moulinette. Ce tmpfs peut utiliser RAM et swap et ne se trouve pas dans le scope cgroup de correction ; les limites CPU/mémoire par processus ne sont pas des quotas globaux. Un processus détaché, un accès par le même UID, le noyau partagé ou une vulnérabilité de Git/Bubblewrap ne sont pas écartés. DNS et HTTPS sortants ne sont pas filtrés par une isolation réseau. Les dépôts privés, SSH, redirections, LFS et sous-modules ne sont pas pris en charge. Dépôt trop volumineux ou configuration TLS/DNS/Bubblewrap indisponible : résultat incomplet, pas de repli.

Le helper interne `github_source.trusted_public_repository` utilise l'espace temporaire qui lui est fourni ; **seul le chemin CLI passant par `github_bounded.bounded_public_repository` le place dans ce tmpfs**. Il n'est pas une API sûre pour du code hostile ; toute utilisation directe le contourne.

## Témoins de charge cgroup : opt-in et non validés en scope réel ici

Deux témoins fixes ont été préparés dans `cgroup_load_probe.py`, appelés uniquement par le test séparé `tests_real/test_real_cgroup_load.py` si `ML_TEST_CGROUP_LOAD=1` : scope provisoire `MemoryMax=128M`, swap 0, `TasksMax=8`, CPU 50 %. Avant tout fork, le scope, son identité et ses limites sont vérifiés, ainsi que la mémoire disponible, une marge dans les cgroups ancêtres et `memory.oom.group=0`. Le témoin mémoire crée **un seul enfant de confiance** qui alloue par blocs et est censé être tué par le mécanisme OOM du scope ; le compteur local `oom_kill` et le signal sont tous deux exigés. Le témoin CPU crée ensuite un seul enfant qui travaille pendant trois secondes ; deux compteurs de throttling doivent augmenter. Des délais et une demande d'arrêt du scope sont prévus. En cas d'absence de preuve ou de problème, le résultat ne peut pas être favorable.

Ces mesures diminuent les risques mais ne garantissent pas qu'aucun autre processus ne sera affecté si l'état de la machine change ou si une hypothèse est fausse. Le test consomme de la mémoire et CPU et **provoque intentionnellement un OOM à l'intérieur du scope** : ne le lancer qu'avec consentement explicite, après revue du code et sur une machine non critique avec suffisamment de mémoire. S'il manque le bus systemd, les contrôleurs, la marge mémoire ou une limite, ne pas affaiblir les garde-fous pour forcer le test. Le test n'exécute pas de rendu étudiant.

Le développement actuel ne dispose pas d'un bus systemd utilisateur : seuls les contrôles et mesures ont été testés sur des fixtures simulées. **Le succès des témoins de charge en scope réel reste inconnu.** Le test optionnel simple de la v0.19 validé par l'utilisateur ne les exerçait pas.

## Vérifications de développement

- Test réel Bubblewrap : un tmpfs de 16 Mio refuse le remplissage de deux fichiers cumulant 18 Mio (`ENOSPC`), témoin du plafond du montage, pas d'un quota hôte global.
- Téléchargements HTTPS réels dans le nouveau tmpfs du dépôt public `Tednoob17/mini-moulinette` pour la branche `main` et le SHA `c0debfed043857ffc6c2629c897f59bec4bf9c4a` ; inventaire et SHA contrôlés.
- Correction réelle ex00 du dépôt public `ChuOkupai/piscine42` au SHA `cc5e12c0776839a33ef12658192a0f46abdcf095`, après lecture et comparaison octet par octet de la source, avec Bubblewrap et Norminette : réussie. Le scope cgroup du parcours GitHub est resté simulé/non testé ici.
- Suite standard : **229 tests réussis sans skip** dans l’environnement assistant, dont absence de repli, tailles, protocole, chemins, inventaire, liens, SHA, préconditions de charge et compteurs simulés ; Bubblewrap et Norminette réels. La charge cgroup réelle optionnelle est distincte et n’a pas été lancée ici.
- Sources ex00 correct et volontairement erroné de la simulation précédente : respectivement `passed` et `failed` en correction locale avec Bubblewrap réel.
- Référence Bubblewrap `--size` : https://manpages.debian.org/testing/bubblewrap/bwrap.1.en.html

## Points ouverts

- Revue de sécurité **indépendante**, en particulier des hypothèses précédentes et du témoin OOM, avant de demander un test de charge utilisateur. Prompt dans `prompt-audit-v0.20-dev.md`.
- Valider sur Ubuntu le nouveau chemin GitHub complet avec cgroup et le témoin de charge **après accord et revue**. Ce test serait localisé, non une preuve contre du code hostile.
- Le stockage total hors du tmpfs n'est pas couvert et la récupération partage le réseau. L'absence de seccomp, les descendants détachés, les changements par le même UID, la mort brutale du parent, les courses de chemin et le noyau partagé restent des risques. Un passage au code non fiable demanderait une architecture et une validation supplémentaires ; ne pas déclarer l'étape 3 terminée sur ces seuls résultats.
