# État v0.32.8-dev — réduction de l'espace vide

La zone d'apprentissage est remontée vers les documents PDF, sur ordinateur et mobile. L'atome reste centré sur la carte de progression. Aucun changement fonctionnel ou de sécurité ; les limites de sécurité de la v0.32.7 restent valables.

---

# État v0.32.7-dev — passe de durcissement ciblée

Copie distincte de la v0.32.6 : préparations de fichier bornées, fichier d'état live remplacé sans suivre de lien final, fin live en cas d'erreur, capture C++ avec entrée standard, modules manquants du worker Git. Détails et limites dans `docs/securite-v0.32.7-dev.md`. Suite légère : 392 tests dont 70 ignorés, aucun échec ; six témoins actifs exclus. Tests réels Bubblewrap, cgroup et Git non effectués ici. Étape 3 et audit indépendant restent ouverts ; uniquement code et dépôts de confiance.

---

# État v0.32.6-dev — isolation et reset

Cette version sélectionne la base explicitement pour le tableau de bord et les corrections live. Le fichier HTML d’une base personnalisée ne remplace pas celui de la base par défaut ; la commande `check` seule conserve la base par défaut. `moulinette reset` sauvegarde la base puis, après confirmation, remet à zéro tentatives et déblocages. La sauvegarde est vérifiée ; un échec annule la suppression. Les processus live ou corrections en cours doivent être arrêtés avant un reset.

Le correcteur C++/Python n’a pas été modifié. Sélection sans charge : 386 tests, 70 ignorés, sans échec ; six témoins actifs exclus. La v0.32.5 avait trois échecs (deux sous-cas PDF obsolètes et une hypothèse pandas), décrits dans `docs/validation-v0.32.6.md`. Les validations ne permettent pas de déclarer la sécurité complète. Les notes plus anciennes ci-dessous sont historiques et peuvent décrire des comportements remplacés.

---

# État v0.31-dev — atome évolutif sans légende et commandes simplifiées

Copie distincte `moulinette-lab-v0.31-dev` (version `0.31.0.dev0`) issue de `v0.30.09-dev`, sans modifier les versions précédentes, l'installation globale ni l'historique réel :
- Suppression des pastilles Protons/Neutrons/Électrons et de la phrase d'analogie sous l'atome ; l'animation reste pilotée par les compteurs réels (`data-protons`, `data-neutrons`, `data-electrons`) : nucléons réels, électrons allumés au prorata des réussites, halo proportionnel à la progression.
- CLI : `moulinette <chemin>`, `moulinette` seul → tableau de bord, alias `ui`, options courtes `-e -m -a -l -s -w`, `--cgroup`, Bubblewrap par défaut s'il est présent (jamais le mode local implicitement), `list`, `dashboard --db/--output`.
- Le test `test_refuses_unisolated_by_default` vérifie désormais le refus quand `bwrap` est absent ; nouveau fichier `tests/test_v031.py`.
- Les PDF téléchargeables n'ont pas été régénérés (ReportLab absent) : voir `docs/audit-documents-telechargeables-v0.31.md`.

---

# État v0.30.09-dev — ajout des piscines C++ et Python, progression séquentielle par piscine et atome 3D

Évolution réalisée dans une copie distincte (`moulinette-lab-v0.30.09-dev`) sans modifier les anciennes versions ni l'historique SQLite existant :
- **Piscines C++ (`45` exercices `cpp00/ex00`..`cpp08/ex04`) et Python (`36` exercices `py00/ex00`..`py04/ex07`)** ajoutées aux `109` exercices C (`190` exercices au total), avec moteurs dédiés (`cpp_engine.py`, `py_engine.py`), détection d'outils manquants (`unavailable` → `incomplete`) et interdiction de toute installation automatique ou accès réseau.
- **Ordre et déblocage permanent des piscines (`1. Piscine C` → `2. Piscine C++` → `3. Piscine Python`)** : carte de progression unique évolutive sur le tableau de bord, déblocage automatique et permanent (`piscine_unlocks`) lorsque tous les exercices d'une piscine ont leur dernière tentative à `passed`, verrouillage limité au tableau de bord (CLI toujours disponible pour C, C++ et Python) et accès en lecture conservé sur les piscines précédentes.
- **Animation 3D de l'atome (`#atom-canvas` + repli `#atom-svg`)** inspirée de la vidéo de référence (noyau plasma concentrique rose/or, nucléons 3D, orbites elliptiques 3D et électrons cyan à traînée lumineuse) et reliée par analogie visuelle aux compteurs réels de la piscine affichée (`Protons` = réussis, `Neutrons` = à revoir, `Électrons` = total de la piscine ou du module filtré).

---

# État v0.30.08-dev — déclenchement direct de la correction depuis la page et icône d'onglet `</>`

Démarrage automatique d'un démon local `127.0.0.1` en arrière-plan lors de `moulinette dashboard` afin que l'appui sur le bouton « Corriger ce fichier » (`#live-submit`) sur `dashboard.html` déclenche immédiatement la correction en direct (`SSE`) depuis la page, ajout du favicon SVG `</>` (carré arrondi violet) sur l'onglet du navigateur et fusion des 105 phrases d'humour de la `v0.29.9-dev`.

---

# État v0.30.07-dev — correction directe d'un fichier `.c` et neutralisation d'un `main()` de test

Prise en charge directe d'un chemin de fichier `.c` (ex. `moulinette check "/home/.../ft_is_negative.c"`) dans `detect_exercise` et `stage_submission_path` (isolation du fichier visé même s'il réside dans un dossier de travail contenant d'autres fichiers `.c` ou binaires), et neutralisation automatique d'une fonction `main()` de test éventuelle lors de la liaison avec le harnais C.

---

# État v0.30.06-dev — animation de structure atomique derrière la carte de progression

Ajout derrière la carte de progression en pourcentage (`.hero-art` / `.progress-card`) d'une structure atomique SVG animée (`#atom-svg`) composée d'un noyau central lumineux, d'un halo et de trois orbites elliptiques inclinées (`-30°`, `30°`, `90°`) sur lesquelles gravitent 6 électrons lumineux (`.atom-electron`), synchronisés avec les couleurs du thème actif et respectant `prefers-reduced-motion`.

---

# État v0.30.05-dev — barre de recherche et de correction de fichier permanente

Affichage permanent du panneau « Corriger un fichier ou un dossier » (`#direct` / `#live-path`) sur le tableau de bord généré par `moulinette dashboard`, avec prise en charge directe d'un chemin de fichier `.c` ou de dossier et détection automatique de l'exercice (`auto`).

---

# État v0.30.04-dev — pages de garde mémoire, suivi malloc/free, pipeline unifié et --jobs

Intégration dans le harnais C (`moulinette/c_memguard.py`) d'un allocateur par pages de garde `PROT_NONE` avec poison `0xA5`, quarantaine `PROT_NONE` sur `free()`, comptage des maillons non libérés (`ml_unfreed_count`) pour `c12/ex06` et `c12/ex12`, et pages `PROT_READ` (`ml_ro_str`) pour les chaînes d'entrée. Détection indicative des mots-clés de boucle (`while`, `for`, `do`, `goto`) dans C05, factorisation du pipeline dans `moulinette/pipeline.py` et ajout de `-j` / `--jobs` sur `--module` et `--all`.

---

# État v0.30.03-dev — animation Matrix/terminal en arrière-plan, sélecteur de police et égalisation

Déplacement de l'animation en arrière-plan (`#bg-matrix` et `#bg-terminal`, sans extraits d'exercices de la Piscine), ajout d'un sélecteur de police hors ligne (`#font` : `DM Sans`, `Terminal Mono`, `Éditorial Serif`, `Néo-Grotesque`, `Humaniste`), égalisation en largeur et hauteur des sections de la page, simplification du titre « Votre progression » et régénération automatique de `dashboard.html` lors de chaque correction.

---

# État v0.30.02-dev — animation de code C et nouveaux thèmes

Ajout sur le tableau de bord d'une animation interactive de code C (`#code-anim` avec frappe en direct, coloration syntaxique, trace et jetons C orbitaux, désactivée automatiquement si `prefers-reduced-motion: reduce` est actif) ainsi que de six nouveaux thèmes (`Sakura Nocturne`, `Cyberpunk Néon`, `Matcha Kyoto`, `Espresso Caramel`, `Fjord Polaire`, `Mirage Doré`) mémorisés hors ligne dans `localStorage`.

---

# État v0.30.01-dev — tableau de bord enrichi, options C/CLI et isolation ciblée

Version préparée dans une copie distincte (`moulinette-lab-v0.30.01-dev`) à partir de `v0.29.8-dev`, sans modifier la version installée (`0.29.8.dev0`) ni l'historique SQLite existant :
- Tableau de bord Senthora préservé hors ligne (thèmes, aléatoire, humour, quatre guides PDF Blanc/Océan), enrichi des étapes réelles du moteur (`01 · Fichiers`, `02 · Compilation`, `03 · Tests`, `04 · Norminette`), d'un comparateur côte-à-côte (`Expected Output` vs `Your Output`) avec caractères invisibles (`\n`, `\0`, `\t`, espaces de fin de ligne) sur les octets réellement capturés, du surlignage Norminette et de deux visualisations d'historique SQLite (`Progression par module`, `Activité enregistrée`), ainsi que d'un mode local optionnel `moulinette dashboard --live` (`127.0.0.1` uniquement, protégé par jeton de session, `Host` et `Origin`).
- Corrections C : option `--sanitize` (`ASan + UBSan` en local, `UBSan trap` sous Bubblewrap, en distinguant « aucun problème observé » d'une preuve d'absence de problème), indices syntaxiques indicatifs et non bloquants pour C05 (`recursion_hint`), `c11/ex05` (`doop_hint`) et C06 (`main_signature_hint`), et vérification dans C10 de la ligne de compilation `cc -Wall -Wextra -Werror` et de la préservation du binaire par `make clean`.
- Isolation : filtre seccomp BPF (`x86_64`) pour `bwrap --seccomp` et nettoyage étendu aux processus de la même session (`sid == pgid`), sans test de charge ni OOM.
- CLI et organisation : autodétection d'exercice (avec refus explicite sur ambiguïté), `--module`, `--all`, `--watch`, `.gitignore` et `.github/workflows/tests.yml`.

---

# État v0.29.8-dev — cas C11 ciblés

Neuf cas non officiels ajoutés sur cinq exercices C11 à partir du sujet v8. Trois variantes erronées de confiance, qui réussissaient les anciens cas fonctionnels, sont rejetées par les nouveaux. Le parcours complet d'un tableau par ft_any est accepté au même titre que l'arrêt à la première correspondance. Les tableaux de pointeurs de fonctions de do-op ne sont toujours pas prouvés. Voir `docs/qualite-c11-v0.29.8-dev.md`.

La v0.29.7 a été validée sur l'Ubuntu utilisateur ; la v0.29.8 reste à y valider.

---

# État v0.29.7-dev — finitions et diagnostic indicatif de récursivité

`moulinette --version` affiche la version exécutée. Des explications supplémentaires couvrent les diagnostics de compilation reconnus : paramètre inutilisé, déclaration implicite et point-virgule attendu. Pour C05/ex01, ex03, ex04 et ex08, une analyse textuelle non bloquante indique un cycle possible accessible, directement ou via un auxiliaire, ou indique qu'aucun cycle n'a été repéré. Les messages rappellent que ce n'est pas une preuve : le résultat ne change jamais le statut de correction. L'itération n'est pas prouvée. Voir `docs/finitions-v0.29.7-dev.md`.

L'Ubuntu utilisateur a validé la v0.29.6 : 334 tests sans charge en 202,627 s, 4 cgroup réels en 3,087 s et la commande installée sur C05/ex06. La v0.29.7 reste à y valider. Aucun OOM ni saturation.

---

# État v0.29.6-dev — renforcement ciblé des corrections

21 cas fonctionnels supplémentaires sur 17 exercices des modules C05, C10, C11, C12 et C13. Le harnais générique accepte désormais des indices de cas à plusieurs chiffres. Cinq variantes erronées de confiance passent les anciens cas fonctionnels correspondants et sont rejetées par les nouveaux ; 109 exemples de référence ont réussi en Bubblewrap réel et style adapté. Les nouvelles exigences reposent sur les sujets fournis et les cas restent non exhaustifs. Voir `docs/qualite-corrections-v0.29.6-dev.md`.

La v0.29.5 a réussi sur Ubuntu utilisateur 332 tests sans charge en 181,974 s, 4 tests cgroup réels en 2,627 s, et une correction de C12/ex08 avec la commande installée. La v0.29.6 a réussi 334 tests sélectionnés sans charge en 159,479 s dans l'environnement de développement, quatre anciens témoins actifs exclus ; navigateur et installation isolée également testés. Elle reste à valider sur cet Ubuntu. Pas de code hostile, d'OOM ni de saturation.

---

# État v0.29.5-dev — délais et nettoyage des commandes de projet

Le moteur projet Bubblewrap lance chaque commande dans son propre groupe : arrêt du groupe et observation `/proc` avant de continuer, tant que le PID du chef n’est pas recyclé. Un délai ou une commande indisponible arrête la suite des cas, et ne lance pas Norminette. En mode local, le groupe externe est conservé ; le comportement reste non isolé. L'observation ne couvre pas les descendants détachés ni tous les cas d'arrêt brutal.

La réception du résultat cgroup a un délai global de 230 s pour le message après la demande ; 110 s pour le job, 90 s pour le style et 30 s de marge, sans garantie de durée totale globale. Les tests légers utilisent des témoins endormis et des simulations, sans OOM ni saturation. Détails et limites : `docs/securite-v0.29.5-dev.md`. Dans l'environnement de développement, 332 tests de la sélection sans charge ont réussi en 155,465 s (quatre témoins actifs exclus), ainsi que le test navigateur. Validation de cette version sur l'Ubuntu utilisateur à faire.

La v0.29.4 a réussi sur l'Ubuntu utilisateur 323 tests sans charge en 157,765 s, 4 tests cgroup réels en 2,352 s et les quatre téléchargements PDF. Voir le rapport séparé de validation Ubuntu.

---

# État v0.29.4-dev — téléchargement direct

Le tableau de bord propose deux liens de téléchargement direct par guide, Blanc et Océan : quatre PDF, intégrés dans la page autonome, utilisables sans JavaScript ni aperçu intégré. Les guides restent statiques, sans données personnelles. Leur génération reste `python3 tools/generer_guides_themes.py` avec ReportLab.

Vérifications en développement : 18 tests dashboard, 4 manuel, 10 diagnostics et guide ; téléchargements des quatre PDF avec et sans JavaScript sous Chromium, fichier local et écran mobile ; installation isolée et génération par la commande installée. Aucun test OOM ou de saturation. Sélection sans charge : 323 tests réussis en 143,069 s ; les quatre témoins actifs de limites ont été exclus. La suite complète et l'Ubuntu utilisateur ne sont pas validés pour cette version.

---

# État v0.29.3-dev — guides Blanc et Océan avec aperçu

Deux thèmes pour chacun des deux guides, décorations sur toutes les pages et aperçu local avant téléchargement. Les quatre PDF et leurs sources sont dans `docs/`, les variantes sont intégrées au tableau de bord. Le téléchargement reste proposé si le lecteur PDF intégré n'est pas pris en charge. Aucun résultat personnel n'est inclus dans les guides. Génération : `python3 tools/generer_guides_themes.py` avec ReportLab.

Vérifications ciblées dans l'environnement de développement : 18 tests dashboard, 4 manuel, 10 diagnostics/guide et test Chromium hors ligne (quatre téléchargements vérifiés), ainsi qu’une installation isolée vérifiant les quatre PDF. Aucun test de charge. La suite complète n'a pas été relancée pour cette modification ; validation sur l'Ubuntu utilisateur à faire. Les validations Ubuntu mentionnées ci-dessous concernent des versions antérieures.

---

# État v0.29.2-dev — guide corail et filigranes

Le guide du style C dispose d'un fond corail clair, d'arcs et de motifs géométriques ainsi que de quatre symboles de code en filigrane par page, dans une disposition variable reproductible. Les neuf pages conservent le texte de la v0.29.1 hors références de version, avec Liberation Serif et JetBrains Mono. Le manuel utilisateur conserve son fond Aurore ; les deux PDF sont embarqués dans le tableau de bord. Moteur et fonctionnalités inchangés.

Vérifications de développement : 18 tests dashboard, 4 tests manuel et 10 tests explications/guide réussis ; navigateur et deux téléchargements vérifiés ; comparaison des textes PDF et inspection de plusieurs rendus. La suite des 323 tests concerne la v0.29, non relancée entièrement pour ce changement de présentation. La v0.29.2 n'a pas été validée sur l'Ubuntu utilisateur.

---

# État v0.29.1-dev — guide de style écarlate

Le PDF du guide du style C a un fond écarlate sur ses neuf pages ; contenu identique hors références de version, et polices Liberation Serif et JetBrains Mono conservées. Le manuel utilisateur garde son fond Aurore. Les deux boutons du tableau de bord téléchargent leurs documents synchronisés. Le moteur et les fonctions de la v0.29 sont inchangés.

Vérification dans l'environnement de développement : **18 tests dashboard, 4 tests manuel, 10 tests explications/guide réussis**, test navigateur et téléchargements réussis. La suite sélectionnée de 323 tests concerne la v0.29 ; elle n'a pas été relancée en totalité pour ce changement de présentation. La v0.29.1 n'a pas été validée sur l'Ubuntu utilisateur.

---

# État v0.29-dev — tableau de bord explicatif et guide de style

La v0.28.3 a réussi **313 tests sans charge en 228,007 s** et **4 parcours de scope cgroup réel en 2,732 s** sur l'Ubuntu utilisateur, sans skip affiché. Le résultat ne valide ni toutes les limites sous charge ni la v0.29.

Le dashboard ajoute des explications ciblées aux diagnostics de compilation reconnus, sans lire les sources et sans prétendre que le prototype a été vérifié après un échec. Les corrections du même exercice sont comparées dans la limite des 50 dernières affichées : seuls les contrôles uniques présents dans les deux rapports sont comparés ; les contrôles non exécutés restent indéterminés.

Un guide de style C séparé, non officiel, fond pourpre et polices Liberation Serif / JetBrains Mono, est intégré au second bouton du tableau de bord ; le manuel utilisateur reste distinct et conserve son fond Aurore. Le guide résume les règles de la Norme version 4 associée à Norminette 3.3.59 et explicite l'adaptation `INVALID_HEADER`. Exemple C vérifié avec vraie Norminette ; seul INVALID_HEADER était signalé.

Le moteur de correction et le modèle de sécurité ne changent pas. **323 tests réussis en 142,978 s** dans la sélection sans les quatre témoins actifs de limites, sans skip affiché, ainsi que le test navigateur et l'installation dans un venv de test. Code de confiance uniquement ; pas d'OOM ni de saturation dans ces essais v.0.29. La version doit encore être testée sur l'Ubuntu utilisateur.

---

# État v0.28.3-dev — limites et nettoyage

Examen des limites CPU, mémoire, temps et tâches et de l'arrêt des descendants. Un état cgroup ambigu n'est plus considéré comme vide si `cgroup.events` manque alors que le répertoire existe. Neuf nouveaux tests légers contrôlent configurations simulées, cas d'état inconnu, timeout et SIGTERM. Voir `docs/securite-v0.28.3-dev.md` pour les résultats, les limites et les délais cumulés encore à revoir.

Suite sélectionnée sans les quatre anciens témoins actifs de limites : **313 tests réussis en 138,756 s** dans l'environnement de développement, Bubblewrap et Norminette 3.3.59, sans skip affiché. Aucun scope cgroup réel disponible ici, aucun OOM ni saturation dans cette sélection. Ces tests ne prouvent pas les limites sous charge ; v0.28.3 reste à valider sur l'Ubuntu utilisateur. La suite standard v0.28.2 a réussi **308 tests en 199,591 s** sur l'Ubuntu utilisateur, sans skip affiché.

---

# État v0.28.2-dev — reprise de la sécurité

Les 109 exercices gardent leurs parcours et tests fonctionnels non officiels, non exhaustifs. La pause sécurité est levée. Le montage explicite du venv Norminette a été retiré du bac de compilation/exécution des projets ; la vérification de style a lieu séparément sur la copie initiale du rendu. Un témoin fictif reproduit la visibilité dans l'ancien montage et vérifie le parcours corrigé ; les racines larges et configurations symboliques sont désormais refusées également par le moteur projet. Voir `docs/securite-v0.28.2-dev.md` pour le détail et les limites.

Le mode local n'est pas isolé ; Bubblewrap et les cgroups restent expérimentaux, pour code de confiance seulement. La sécurité n'est pas achevée. Aucun test OOM forcé ni test de scope cgroup réel dans cet environnement. Suite complète : **308 tests réussis en 143,615 s** dans l’environnement de développement ; test navigateur réussi. L'utilisateur a ensuite obtenu **308 tests réussis en 199,591 s** sur Ubuntu, sans skip affiché. La suite standard contient de courts témoins actifs de limites ; voir la précision historique dans `docs/securite-v0.28.3-dev.md`.

Le manuel Aurore a été actualisé pour cette version sans supprimer son contenu ; les copies historiques restent disponibles.

---

# État v0.28.1-dev — présentation du manuel

Le manuel conserve son contenu v0.28, avec les références de version actualisées. Toutes ses pages ont un fond Aurore ; le texte utilise Liberation Serif et les commandes JetBrains Mono. Les polices sont intégrées au PDF, et leurs fichiers et licences sont fournis pour la régénération. Le bouton du tableau de bord télécharge ce nouveau document. Les tests ciblés et le téléchargement en navigateur sont vérifiés ; les 304 tests complets se rapportent à la v0.28, dont le moteur est inchangé. La v0.28.1 n'a pas été testée sur l'Ubuntu utilisateur.

---

# État v0.28-dev — manuel utilisateur

La suite v0.28-dev a réussi 304 tests dans l'environnement de développement. Le tableau de bord intègre un manuel PDF de 13 pages : présentation, installation, utilisation, référence des commandes et options, GitHub de confiance, tableau de bord, dépannage et limites. Ce PDF est statique et ne contient pas l'historique personnel. La source est `docs/manuel-utilisateur.md` et le générateur optionnel est `tools/creer_manuel.py`. Les moteurs de correction et l'interface n'ont pas changé, sauf le bouton de téléchargement du manuel. La sécurité reste en pause.

---

# État v0.27.1-dev — ajustement d’interface

La case humour a été déplacée en haut, le titre et le paragraphe d’accroche retirés à la demande. Le PDF, les thèmes, l’historique et le moteur restent inchangés. La v0.27 a réussi 300 tests dans l’environnement de développement ; cette modification de présentation est vérifiée par les tests ciblés du tableau de bord et un navigateur réel. La v0.27.1 n’a pas encore été validée sur l’Ubuntu utilisateur.

---

# État v0.27-dev — tableau de bord

La v0.26.1-dev a été validée sur l'Ubuntu utilisateur : **296 tests réussis sans test ignoré affiché**. La v0.27-dev conserve le moteur de correction et ajoute une interface inspirée de Senthora : thèmes persistants ou aléatoires à l'ouverture, couleurs et libellés d'état, recherche, filtre par module et mise en page adaptable. L'historique et les scores restent issus des données locales réelles. Le PDF est volontairement inchangé en attendant sa discussion.

Les préférences de thème et d'humour utilisent le stockage local du navigateur ; elles sont distinctes de l'historique SQLite, et dépendent du navigateur et du chemin/URL de la page. Un stockage bloqué est signalé. Les scénarios navigateur (fichier local, persistance, aléatoire, statuts, filtres, détails, humour, mobile et stockage bloqué) ont été vérifiés avec Chromium ; cela ne prouve pas le comportement de tous les navigateurs.

La v0.27-dev n'a pas encore été validée sur l'Ubuntu utilisateur. Les contraintes et limites du moteur et de la sécurité ci-dessous restent applicables.

---

# État v0.26.1-dev — correctif de compatibilité Ubuntu

Les 109 exercices C 00 à C 13 disposent de parcours et de tests locaux non officiels et non exhaustifs. La sécurité reste en pause : code et dépôts de confiance uniquement.

## Retour Ubuntu sur la v0.26

La suite a exécuté 288 tests avec **16 échecs**. Parmi les 109 références, 13 exercices posaient problème : sept incomplets pour ambiguïté de protection de pile (C08/ex05, C10/ex00–03, C11/ex05, C13/ex07), et six échecs de compilation C12/ex10, ex11, ex12, ex14, ex16, ex17 sur les prototypes `int (*cmp)()`. Les trois autres échecs de la suite répétaient certains de ces problèmes. C00/ex00 et C12/ex08 passaient avec Bubblewrap et Norminette ; C12/ex08 passait aussi en scope cgroup réel. Ces résultats ne prouvent pas la sécurité.

## Correctif

La suite complète v0.26.1-dev a réussi **296 tests** dans l’environnement de développement, avec Bubblewrap et Norminette 3.3.59.

- Les sources et prototypes C12 sont compilés explicitement en C11, pour respecter les prototypes historiques du sujet. L'adaptation est signalée. La différence C23/C11 a été reproduite localement ; sans information sur le compilateur de l'utilisateur, l'explication exacte de son réglage par défaut reste à confirmer.
- Lorsque les objets multi-fichiers contiennent seulement des symboles de protection de pile ambigus parmi les symboles externes non autorisés, des objets alternatifs sont compilés avec `-fno-stack-protector`, puis réanalysés. Pour les projets compilés par le moteur, ces objets exacts sont liés et testés : leur protection de pile est désactivée. Si un symbole ambigu persiste ou si l'analyse échoue, le résultat reste incomplet. Une vraie fonction interdite est recherchée sur les objets d'origine **et** les objets alternatifs ; elle n'est pas ignorée.
- Pour les programmes produits par Makefile, le binaire réellement testé reste celui du Makefile avec ses protections ; la recompilation sert à l'inspection et est **indicative**, car ces objets alternatifs ne sont pas nécessairement ceux liés au binaire. Le rapport le précise. Les archives de bibliothèques ambiguës restent incomplètes : leur bibliothèque n'est pas remplacée silencieusement.
- Régressions : les 13 exercices signalés ont été testés en Bubblewrap et vraie Norminette avec une simulation de compilateur C23 et `-fstack-protector-all` ; contrôles supplémentaires sur les appels interdits d'origine et alternatifs, et sur une référence explicite persistante au symbole de protection.
- Tableau de bord et messages sont documentés ; la feuille de route et le message d'identifiant inconnu ont été mis à jour.

La version corrigée n'a **pas encore été essayée sur l'Ubuntu de l'utilisateur**. L'essai v0.26 cgroup réussi concerne uniquement C12/ex08 ; il ne démontre ni la sécurité, ni les limites sous charge. Pas de test OOM ni de saturation.

## Limites pédagogiques persistantes

Pas de preuve de récursivité/itération C 05 ou de tableau de fonctions de do-op ; vérifications Makefile, erreurs C10, appels externes et mémoire partielles. Les tests C06 supposent un retour 0 et ne vérifient pas séparément la signature de `main`. Les tests sont non officiels. Les sujets ont été intégrés manuellement ; pas d'import automatique.
