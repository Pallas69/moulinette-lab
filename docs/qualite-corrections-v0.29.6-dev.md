# Renforcement ciblé des corrections — v0.29.6-dev

## Méthode et portée

Ajout de 21 cas sur 17 exercices à partir des sujets fournis : C05 v7, C10 v7.1, C11 v8.0, C12 v9.0 et C13 v6.0. Les cas sont non officiels et non exhaustifs. Les rendus et exemples sont du code de confiance ; ces tests ne prouvent ni la conformité 42 ni la sécurité. Pas de test OOM ou de saturation.

- **C05** : factoriels 6 et 11, puissance négative impaire, racine carrée de 120 et 121, nombres premiers 37 et 49, prochain premier depuis 90. Aucun résultat de débordement n'est exigé.
- **C10** : fichiers binaires de 5 Kio pour display_file et cat, fin d'un fichier binaire de 5 Kio pour tail -c, hexdump -C sur entrée standard binaire. Le test n'impose pas une taille de tampon ou un nombre d'appels read. Les règles Makefile et la gestion des erreurs restent partielles ; les signes de tail ne sont pas exigés.
- **C11** : contrôle de l'ordre et des valeurs transmis aux callbacks pour `ft_any` sans correspondance et `ft_count_if` ; comparateur donnant -17 ou 42 pour `ft_is_sort`, car seul le signe importe. Le tableau de fonctions de do-op n'est toujours pas prouvé.
- **C12** : vérification que `ft_list_clear` transmet chaque donnée distincte une fois au callback, sans imposer un ordre non demandé par le sujet. Ce test ne prouve pas l'absence de fuites mémoire.
- **C13** : élément absent dans un arbre non vide ; hauteur d'un arbre dont la branche droite est plus longue.

Le harnais générique antérieur sélectionnait les cas au moyen d'un caractère et ne pouvait pas correctement distinguer les indices 10 et plus. Il décode maintenant un indice numérique ; un test distinct contrôle les indices 0, 9, 10 et 11. Le format des résultats et les interfaces utilisateur ne changent pas.

## Témoins et limites

Cinq variantes volontairement erronées de confiance ont été comparées aux anciens cas fonctionnels et aux cas enrichis : nombre premier reconnu par liste limitée, `ft_count_if` parcourant à l'envers, callback de libération recevant une mauvaise donnée, hauteur ne considérant que la branche gauche et `ft_cat` ne produisant qu'un premier bloc. Pour chacune, tous les anciens cas fonctionnels correspondants ont réussi et un nouveau cas a détecté le défaut. Cela ne signifie pas que l'ancienne correction entière aurait nécessairement réussi : le style ou d'autres contrôles peuvent échouer.

Les 109 exemples ont été vérifiés en Bubblewrap et avec la Norminette adaptée dans l'environnement de développement ; C09/ex01 ne comporte pas de fichier C à vérifier au style. Ces résultats ne remplacent ni d'autres implémentations correctes, ni des tests sur Ubuntu utilisateur. Les fonctions itératives ou récursives de C05 ne sont toujours pas reconnues structurellement ; les vérifications d'appels externes, mémoire et cas limites restent partielles.

La sélection sans charge a réussi **334 tests en 159,479 secondes**, sans skip affiché, dans l'environnement de développement, quatre anciens témoins actifs de limites exclus. Le téléchargement des guides a été testé dans Chromium et le paquet installé de manière isolée. Le scope systemd cgroup réel n'était pas disponible dans cet environnement et la v0.29.6 n'a pas été testée sur l'Ubuntu utilisateur.
