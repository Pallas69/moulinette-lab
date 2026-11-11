# Analyse des dépôts transmis — Moulinette Lab

Consultation des branches publiques et de fichiers ciblés. Les dépôts n'ont pas été exécutés, aucun code tiers n'a été copié dans l'outil à cette étape. Les conclusions ne constituent pas un audit exhaustif de chaque fichier. Les versions et licences peuvent évoluer.

## Sources pertinentes pour C 00

### mini-moulinette

- URL : https://github.com/Tednoob17/mini-moulinette
- Branche `main`, commit observé `c0debfed043857ffc6c2629c897f59bec4bf9c4a` ; licence MIT, copyright Khairul Haaziq.
- Arborescence vérifiée : `mini-moul/tests/C00/ex00` à `ex08`. Les tests sont intéressants pour la conception de notre propre catalogue.
- Exemple examiné : `mini-moul/tests/C00/ex00/ft_putchar.c`. Le test initialise un tampon à zéro, utilise `fgets`, puis `strcmp` pour vérifier un caractère nul. Si l'étudiant ne produit aucun octet pour `\0`, le tampon reste aussi une chaîne vide et ce contrôle peut donner un faux positif. Notre moteur compare des octets et leurs longueurs, et une régression explicite a été ajoutée.
- Pour `ex04`, le fichier comparé utilise `strncmp(..., 1)` ; cela ne vérifie que le premier octet, pas l'absence de sortie supplémentaire. Les tests futurs devront vérifier la sortie complète selon le sujet choisi.
- Source indicative, pas autorité sur le sujet version 8 ni reproduction exacte de la moulinette officielle.

### moulileuleu

- URL : https://github.com/Tednoob17/moulileuleu
- Branche `main`, commit observé `1a7df35df9da7ca4e0aa8963760784a9f29ec465` ; licence MIT, copyright 2022 aLeuleu.
- Dossiers observés : `c00/tests/test_ex00.c` à `test_ex08.c`, `c00/expected_results/`, ainsi que C01 et C02. Projet décrit comme adapté à une piscine 42 Lyon en 2022.
- Utile pour comparer les structures d'appels et les sorties attendues. Attention à la version du sujet et à la couverture effective ; les résultats, diffs et scripts ne sont pas des validations officielles.

Les licences MIT identifiées demandent de conserver les mentions de copyright et de licence si nous copions ou redistribuons des parties substantielles. Les ressources auxquelles un projet renvoie peuvent avoir d'autres licences. À ce stade les tests ajoutés au projet sont indépendants et ne reproduisent pas ces fichiers.

## Sources complémentaires

### Norminette

- URL : https://github.com/Tednoob17/norminette
- Fork du projet officiel ; branche `master`, commit observé `a9e1a3dde004b4f997194b3594292a7ee6eb49b3`. Licence MIT.
- GitHub indique que la branche est en retard sur `42school/norminette`. Préférer la source officielle et une version identifiée. Le moteur teste actuellement explicitement 3.3.59 ; une mise à jour exigera des tests d'adaptation.

### 42-resources

- URL : https://github.com/Tednoob17/42-resources
- Branche `main`, commit observé `b7fdf95482b6dfa7b2fd525544b5718b2db00bfe`. Licence MIT pour le dépôt lui-même.
- Index et ressources pédagogiques, pas un moteur de correction prêt à intégrer. Les liens externes et leurs contenus doivent être évalués séparément.

### EPITECH-Projects

- URL : https://github.com/Tednoob17/EPITECH-Projects
- Branche `master`, commit observé `957f9762671477aa7bc655f217b7aaffb3a5088f`. Aucune licence identifiée par les métadonnées GitHub ; les droits doivent être vérifiés avant toute copie.
- Dépôt de projets d'étudiant, comprenant `C_Pool` et `CPP_Pool`, dont des dossiers 2018. L'auteur indique que certains projets peuvent être incomplets ou défectueux.
- Intéressant plus tard comme exemples à confronter à des sujets Epitech, pas comme corrigé de référence ni pour le profil 42. Attention à ne pas divulguer de solution inutilement à l'apprenant.

### 42_Subjects

- URL : https://github.com/Tednoob17/42_Subjects
- Branche `master`, commit observé `eec0d8dcc5ff48729f790bfa78c125ced7eb1699` ; aucune licence identifiée par les métadonnées GitHub.
- Collection ancienne, comportant notamment des sujets OCaml et Python/Django ; leurs versions et leur pertinence devront être vérifiées.
- Le README du dépôt affirme des restrictions sur l'utilisation et la reproduction des sujets. Sans trancher la question juridique, ne pas intégrer ou redistribuer ses PDF sans examiner les autorisations applicables. Le PDF C 00 v8 fourni par l'utilisateur reste la référence de travail locale pour l'exercice déjà commencé.

## Plan d'utilisation

1. Continuer le durcissement et la validation du moteur avant d'accepter des dépôts non fiables.
2. Pour chaque exercice C 00, confronter le sujet versionné aux idées de tests communautaires, établir des tests propres et vérifier les cas limites.
3. Contrôler provenance, licence et attribution avant toute copie de tests ou redistribution de documents.
4. Prévoir plus tard Epitech et les autres langages sous forme de packs et profils distincts.
