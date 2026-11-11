# Reprise de la sécurité — v0.28.2-dev

## Périmètre et conclusion

La sécurité est reprise, mais **n'est pas terminée**. Tous les modes restent réservés à du code et à des dépôts de confiance. Ce correctif réduit une exposition particulière ; il ne constitue pas une validation du bac face au code hostile.

## Constat : montage du venv Norminette dans les projets

Dans la v0.28.1-dev, le moteur projet montait l'environnement virtuel de Norminette en lecture seule sous `/opt/norminette` dans le même bac que le Makefile, les scripts et les binaires du rendu. La lecture seule empêche l'écriture par ce chemin, **pas la lecture**. Le moteur projet ne refusait pas non plus les racines larges et configurations `pyvenv.cfg` symboliques déjà refusées par le runner mono-fichier.

Le test de régression utilise exclusivement un fichier témoin fictif : il reproduit l'ancien montage dans Bubblewrap et lit ce témoin. Puis un vrai parcours projet Bubblewrap exécute un Makefile qui échouerait si le témoin était lisible à ce même emplacement ; ce parcours réussit, ainsi que sa vérification Norminette séparée. Cela démontre la visibilité de ce fichier pour la configuration testée, pas une exfiltration ni une sécurité générale. Aucun secret réel n'a été lu ou utilisé.

## Modification

- En mode Bubblewrap, le montage explicite `/opt/norminette` est supprimé du bac de compilation et d'exécution du projet. La Norminette s'exécute ensuite dans un bac Bubblewrap distinct, avec un montage en lecture seule de l'environnement Norminette et de la copie initiale du rendu. Elle n'exécute pas le Makefile ou le programme du rendu ; elle analyse les fichiers sources d'origine copiés, et non ceux qui auraient été modifiés dans le répertoire de compilation.
- Le moteur projet applique les mêmes refus de racines larges et de `pyvenv.cfg` symbolique que le runner mono-fichier. Ce contrôle n'établit ni que l'environnement virtuel est exempt de données sensibles, ni qu'il est inviolable. Un environnement dédié, de confiance, reste nécessaire.
- La phase Norminette borne son délai global à 90 secondes, avec un délai par invocation et des limites de capture et de ressources. Le statut Bubblewrap est vérifié ; en cas d'erreur la vérification de style est indisponible, sans repli local. Une version différente de 3.3.59 est refusée. Ces bornes ne remplacent pas une validation de limites sous charge.
- Le mode `--unsafe-local` reste **sans isolation** : le programme et son Makefile ont les droits de l'utilisateur et peuvent lire le venv et d'autres fichiers. Les étapes sont distinctes mais cela ne constitue pas une protection locale.

Le bac de projet monte toujours `/usr` en lecture seule ; si le venv ou d'autres données sont déjà accessibles par ce montage, supprimer le montage `/opt/norminette` ne les rend pas invisibles. La Norminette elle-même voit le venv entier dans son propre bac ; ses dépendances et l'installation doivent être de confiance. Les fichiers du rendu sont toujours susceptibles d'exploiter une vulnérabilité de l'analyseur ; aucune garantie n'est donnée.

## Limites encore ouvertes

- Le code étudiant et les Makefiles partagent le bac de projet avec `/project.json`, ses données de tests et des marqueurs, et `/proc`. Cette visibilité ne garantit ni le secret ni l'intégrité des tests face à un rendu hostile ; aucune exploitation particulière n'a été démontrée ici.
- Noyau partagé, absence de seccomp, risques de courses et d'accès par le même UID, nettoyage après interruption brutale et descendants détachés. Le réseau reste partagé pour la récupération Git expérimentale.
- Les limites CPU et mémoire sous charge et les cgroups n'ont pas été validés par ce travail. Aucun test OOM forcé n'a été exécuté ; la suite standard comprend cependant de courts témoins actifs de limites (voir la rectification ci-dessous). L'environnement de développement ne permet pas de vérifier un scope cgroup réel. L'ancien essai réel C12/ex08 concernait la v0.26 sur l'Ubuntu utilisateur, pas la présente version.
- La copie initiale n'est pas atomique face à un processus concurrent ; les racines montées et les autres ressources système demandent une étude plus approfondie. Un audit indépendant et un environnement jetable approprié sont nécessaires avant de modifier le modèle de confiance.

## Validation

Tests automatisés dans l'environnement de développement avec Bubblewrap et Norminette 3.3.59, y compris le témoin fictif et les régressions de version et de configuration. Voir `ETAT-CHANTIER.md` pour le résultat exact de la suite. La suite a ensuite réussi sur l'Ubuntu utilisateur ; ce ne sont pas des tests de sécurité exhaustifs.

## Rectification et retour Ubuntu ultérieurs

L'utilisateur a obtenu **308 tests en 199,591 s, OK**, sans skip affiché, sur Ubuntu. La formulation « aucun test de saturation » ci-dessus ne décrit pas fidèlement tous les anciens tests de la suite standard : elle inclut de courts témoins CPU et de remplissage d'un tmpfs, ainsi qu'une tentative d'allocation refusée par RLIMIT. Voir le détail et la sélection sans ces témoins dans `securite-v0.28.3-dev.md`. Aucun OOM forcé n'est revendiqué.
