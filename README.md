# Moulinette Lab — v0.32.8-dev

Prototype pédagogique local, **non officiel et sans affiliation à 42**, pour autodidactes. Il propose un correcteur et des jeux de tests pour **190 exercices** répartis sur trois piscines dans l'ordre **1. Piscine C (`109` exercices)**, **2. Piscine C++ (`45` exercices)** et **3. Piscine Python (`36` exercices)**. Les résultats ne sont pas ceux de la moulinette officielle et un succès ne prouve pas une conformité complète.

## Nouveautés v0.32.8-dev — Espace d’en-tête réduit

- L'espace entre les documents PDF et le bloc d'apprentissage a été réduit sur ordinateur et sur mobile. La carte de progression et son atome gardent leur centrage ; le contenu et les fonctionnalités sont inchangés.
- Cette évolution visuelle ne constitue pas une nouvelle validation de sécurité. Usage de code de confiance uniquement.

## Historique v0.32.7-dev — Durcissement ciblé

- Fichier isolé et fichiers compagnons copiés avec lecture bornée et refus des liens finaux ; source trop volumineuse signalée au correcteur. Le fichier d’état du direct est remplacé atomiquement avec des permissions privées, sans suivre un lien final.
- La correction live termine avec un résultat incomplet en cas d'erreur de préparation. Les tests C++ avec entrée standard utilisent la capture bornée sans tampon intermédiaire illimité. Le worker Git dispose de ses modules manquants ; parcours réseau et Bubblewrap réels non revalidés ici.
- Revue interne et tests légers : voir `docs/securite-v0.32.7-dev.md`. Étape 3 non achevée, audit indépendant et limites en charge non vérifiés. Code de confiance uniquement.

## Historique v0.32.6-dev — Historique isolé et reset

- `dashboard --db` utilise la base sélectionnée pour les tentatives et les déblocages ; le mode `--live --db` y enregistre aussi les corrections du direct. Le tableau statique pour une base personnalisée possède un fichier distinct et ne se connecte pas au démon live par défaut. La commande `check` seule utilise toujours la base par défaut.
- `moulinette reset` cible la base locale, `moulinette reset --db CHEMIN` une base désignée : confirmation `RESET` requise (ou `--yes` explicite), sauvegarde SQLite vérifiée créée avant suppression. Après confirmation, tentatives et déblocages sont effacés ; sans reset explicite les déblocages demeurent permanents. Arrêter corrections et serveurs live au préalable. Une correction ultérieure peut réécrire dans la base.
- Guides actualisés ; C++/Python restent partiels et non officiels. Les tests légers ne prouvent pas la sécurité ; code de confiance uniquement, pas d'OOM ni de saturation.

## Historique v0.32.5-dev — Guides et interface

- Constellation décorative retirée. Atome et humour conservés.
- Manuel et guide de style C actualisés, chacun en variantes Blanc et Océan : accès direct aux quatre PDF dans le tableau de bord. Le contenu reste non officiel et ne garantit pas la conformité ; voir les limites et la notice des PDF.
- Correcteur inchangé. L'option `dashboard --db` ne garantit toujours pas l'isolation ; utiliser un `XDG_DATA_HOME` distinct pour un essai séparé.

## Historique v0.32.4-dev — Orbites et constellation (retirée en v0.32.5)

- Exactement une orbite et un électron pour chaque exercice dont le dernier résultat est réussi (bleu) ou à revoir (rouge). Aucun pour les résultats incomplets ou non corrigés : zéro résultat donne zéro orbite. Le périmètre est la piscine consultée ou le module sélectionné ; la recherche textuelle ne le modifie pas. Le noyau unique, le centrage et la vitesse ×1,5 sont conservés ; la carte peut masquer une partie du dessin et les orbites peuvent se superposer.
- En haut à gauche : constellation décorative du Capricorne composée d'étoiles et de liens schématiques, sans illustration animale ni données personnelles. Les positions sont inspirées des coordonnées sidérales publiées dans [Zodiac Stars](https://www.johnpratt.com/items/astronomy/zodiac/zodiac_stars.html) ; le tracé est approximatif et ne montre pas le ciel en temps réel. Mouvement réduit : image fixe ; aucun accès réseau nécessaire.
- Lorsque Canvas est indisponible, repli SVG 2D avec les mêmes comptes et couleurs. Humour, correcteur et PDF inchangés. Voir l'audit PDF actualisé ; limite connue `dashboard --db` toujours présente. Tests non officiels, code de confiance uniquement.

## Historique v0.32.3-dev — Électrons, humour et graphe (graphe remplacé en v0.32.4)

- Atome 3D centré : un électron bleu par exercice réussi et un rouge par exercice à revoir, selon la dernière tentative du périmètre (piscine consultée ou module sélectionné). Incomplets et non corrigés ne produisent pas d’électron ; les tentatives antérieures ne s’ajoutent pas. Le noyau demeure unique. Vitesses multipliées par 1,5 par rapport à la v0.32.2. Comme la carte de progression se trouve devant l’atome, des électrons peuvent être masqués ou se superposer.
- Interrupteur d’humour accessible, choix conservé si le stockage du navigateur fonctionne ; vannes changées automatiquement toutes les 30 secondes pendant que l’humour est activé et l’onglet visible. Bouton manuel conservé ; aucune répétition immédiate.
- Graphe animé décoratif de points et liens en haut à gauche, inspiré d’une vue graphique de notes. Il est généré localement à partir de données fictives : ne lit aucun coffre Obsidian, fichier ni donnée personnelle et ne fait aucune requête. Mouvement réduit : graphe fixe.
- Aucun changement du correcteur ou des PDF ; la limite connue `dashboard --db` subsiste. Tests non officiels, code de confiance uniquement.

## Historique v0.32.2-dev — Atome centré et simplifié (supplanté en v0.32.3)

- Atome classique en perspective 3D, centré derrière la carte de progression : un noyau unique et trois électrons sur trois orbites, sans légende. C’est une animation symbolique, pas une particule par exercice. La luminosité du noyau évolue avec le taux d’exercices réussis du périmètre sélectionné. La carte de progression affiche toujours les valeurs réelles. Les éléments peuvent être masqués par la carte.
- Commandes et guides inchangés. L’historique et le correcteur ne sont pas modifiés ; la limite `dashboard --db` subsiste.

## Historique v0.32.1-dev — Atome classique en 3D (supplanté en v0.32.2)

- Animation simplifiée : noyau central et trois orbites inclinées en perspective 3D, sans plasma, traînées ni légende sous l’atome. Les particules suivent les mêmes règles de dernier résultat et de périmètre que la v0.32. La carte peut masquer une partie de l’animation ; plusieurs particules peuvent se superposer.
- Aucun changement des commandes ou des PDF. Les limites connues de la v0.32, notamment pour `dashboard --db`, restent applicables. Les sujets C++/Python et la vidéo de référence ne sont pas vérifiés ici.

## Historique v0.32-dev — Atome évolutif

- Dans l’atome, un proton correspond à un exercice réussi au dernier essai, un neutron à un exercice à revoir et un électron à un exercice du périmètre. Les tentatives incomplètes ou absentes ne créent pas de nucléon. Aucun texte ni pastille d’analogie n’est affiché sous l’atome.
- Le périmètre est la piscine consultée, ou le module choisi dans le filtre. La recherche textuelle ne change pas ce périmètre. Les particules sont comptées individuellement : les électrons partageaient au plus 12 orbites en v0.32 (trois en v0.32.1), afin d’éviter une orbite coûteuse par exercice. Des particules peuvent se superposer ou être masquées par la carte.
- L’animation est calculée à partir des dernières tentatives enregistrées et de la page générée. La correction depuis la page en direct provoque un rechargement ; pour une page statique déjà ouverte, rouvrir ou recharger la page générée après correction si nécessaire. Le mouvement réduit affiche une image fixe.
- Les raccourcis de commande de la v0.31 sont conservés. Les quatre PDF restent ceux de la v0.29.8 ; les travaux nécessaires pour une autre IA sont décrits dans `docs/audit-documents-telechargeables-v0.32.md`.
- **Limite connue** : ne pas utiliser `dashboard --db` ou `dashboard --live --db` pour isoler l’historique : les déblocages ou la page en direct peuvent utiliser la base par défaut. Ce défaut hérité n’a pas été corrigé dans cette version ciblée.

## Commandes simplifiées (v0.31-dev, conservées en v0.32)

```bash
moulinette                          # ouvre le tableau de bord (= moulinette dashboard)
moulinette ~/rendu/ft_putchar.c     # corrige un fichier (exercice détecté, Bubblewrap par défaut)
moulinette ~/rendu/c01 -m c01       # tout un module (c00..c13, cpp00..cpp08, py00..py04)
moulinette ~/rendu -a               # tous les exercices cXX/exYY, cppXX/exYY, pyXX/exYY trouvés
moulinette ~/rendu/ex00 -e cpp00/ex00 -l   # exercice imposé, mode local non isolé
moulinette list --piscine cpp       # catalogue d'une piscine (c, cpp, py, all)
moulinette ui                       # alias de « dashboard »
```

| Raccourci | Équivalent historique (toujours accepté) |
|---|---|
| `moulinette <chemin>` | `moulinette check <chemin>` |
| `-e` | `--exercise` |
| `-m` / `-a` | `--module` / `--all` |
| `-s`, `--sandbox` | `--experimental-sandbox` |
| `-l`, `--local` | `--unsafe-local` |
| `--cgroup` | `--experimental-cgroup-sandbox` |
| `-w` | `--watch` |

Sans option de mode, Bubblewrap est utilisé s'il est installé ; sinon la correction est refusée. **Le mode local non isolé n'est jamais choisi implicitement** : il faut `-l`.

## Historique v0.31-dev — Atome et commandes (description historique, remplacée pour l’atome en v0.32)

- **Atome 3D purement visuel et évolutif** : suppression des pastilles « Protons / Neutrons / Électrons » et de la phrase d'analogie sous l'animation. L'analogie est portée par l'animation elle-même, recalculée à chaque génération de la page (donc après chaque correction) et à chaque changement de piscine consultée :
  - noyau : un nucléon par exercice corrigé (vert = réussi au dernier essai, ambre = à revoir), plafonné à 48 ; aucun nucléon fictif tant que rien n'est corrigé ; le noyau s'élargit avec le nombre de nucléons ;
  - électrons : la part d'électrons « allumés » (cyan lumineux avec traînée) suit la proportion d'exercices réussis sur le total de la piscine affichée ; les autres restent éteints (gris, traînée discrète) ;
  - halo du noyau : intensité et rayon proportionnels à la progression.
- **Commandes simplifiées** (voir ci-dessus), options longues historiques conservées.
- `moulinette dashboard --db FICHIER --output FICHIER.html` : option conservée, mais **isolation non garantie** ; voir la limite connue v0.32 ci-dessus.
- `moulinette list [--piscine c|cpp|py|all]`.
- Correction de messages CLI : titre du rapport selon la piscine (`42 C`, `42 C++`, `42 Python`), identifiants de rapport `42/cpp/…` et `42/py/…` dans les cas d'interruption ou de source GitHub indisponible (évitait une `KeyError` hors piscine C).

## Nouveautés v0.30.09-dev — Piscines C++ et Python, progression évolutive par piscine et animation 3D de l'atome

- **Ajout de la Piscine C++ (`cpp00/ex00` à `cpp08/ex04` — 45 exercices ; numéro de version non lisible dans le texte des PDF fournis, enregistré « 1.0 » par défaut)** (`moulinette/cpp_catalog.py` et `moulinette/cpp_engine.py`) :
  - Compilation en standard `C++98` avec `-Wall -Wextra -Werror -std=c++98` (`clang++` prioritaire s'il est disponible, repli explicite sur `g++` ou `c++`, et statut `unavailable` → `incomplete` si aucun compilateur C++ n'est présent).
  - Contrôles statiques adaptés aux sujets C++ : absence de `*alloc`/`free`/`*printf` non autorisés, absence de `using namespace` et `friend`, absence des conteneurs STL et de `<algorithm>` dans les modules `cpp00` à `cpp07` (autorisés à partir de `cpp08`), présence de gardes d'inclusion dans les en-têtes `.hpp`/`.h`, contrôle du `Makefile` (`all`, `clean`, `fclean`, `re`, absence de relink) et harnais de test C++ dédiés par exercice.
- **Ajout de la Piscine Python (`py00/ex00` à `py04/ex07` — 36 exercices ; numéro de version non lisible dans le texte des PDF fournis, enregistré « 1.0 » par défaut)** (`moulinette/py_catalog.py` et `moulinette/py_engine.py`) :
  - Vérification syntaxique et AST : interdiction systématique de `eval()` et vérification des fonctions/modules explicitement interdits par l'exercice (ex. `numpy.dot`/`matmul` dans `py01/ex04`, `pandas.DataFrame.duplicated`/`drop_duplicates` dans `py04/ex05`).
  - Exécution isolée hors réseau avec jeux de données synthétiques autonomes (CSV/PNG générés localement lorsque les jeux de données externes comme `athlete_events.csv`, `solar_system_census.csv` ou `42AI.png` ne sont pas fournis avec les sujets). Si `python3` ou une bibliothèque tierce requise (`numpy`, `pandas`, `matplotlib`, `scipy`) est absente, le contrôle est signalé comme **indisponible (`unavailable`)** et le verdict passe à **incomplet (`incomplete`)**, jamais en réussite et sans aucune installation automatique ni accès réseau.
- **Progression séquentielle des piscines (`1. Piscine C` → `2. Piscine C++` → `3. Piscine Python`)** (`moulinette/history.py`, `moulinette/dashboard_insights.py`, `moulinette/dashboard.py`) :
  - Une seule **case de progression évolutive** (`.progress-card`) est affichée sur le tableau de bord pour la piscine active (ou la piscine débloquée consultée).
  - Une piscine est terminée lorsque tous ses exercices ont pour dernière tentative enregistrée le statut `passed` (`réussi`), ce qui débloque automatiquement la piscine suivante et fait évoluer la carte vers le périmètre de la nouvelle piscine (`109` → `45` → `36`).
  - Tout déblocage est **permanent** (`table SQLite piscine_unlocks`) même si un exercice d'une piscine précédente repasse ultérieurement à `failed` (`à revoir`).
  - Ce verrouillage concerne **uniquement le tableau de bord** : la ligne de commande (`moulinette check`) peut corriger des exercices C++ ou Python à tout moment, et leurs résultats sont conservés et pris en compte dès le déblocage. Les piscines précédentes restent consultables en lecture (exercices, modules et historique).
- **Animation 3D de l'atome (`#atom-canvas` + repli `#atom-svg`) et analogie visuelle reliée aux compteurs réels** :
  - Rendu 3D sur canevas inspiré de la vidéo de référence : noyau énergétique concentrique rose/magenta/or avec filaments de plasma et grappe de nucléons 3D, orbites elliptiques 3D inclinées en perspective et électrons bleu-cyan glacé avec traînées lumineuses effilées (respectant `prefers-reduced-motion: reduce`, un onglet masqué et un plafond d'électrons animés pour préserver la fluidité).
  - Légende explicite d'**analogie visuelle** sous la carte : **Protons** = exercices réussis (`passed`), **Neutrons** = exercices à revoir (`failed`, sans présenter un neutron comme une particule physique chargée négativement), **Électrons** = total d'exercices de la piscine affichée (`109` en C, `45` en C++, `36` en Python), avec mise à jour synchronisée lors du filtrage par module ou du changement de piscine.

## Nouveautés v0.30.08-dev — Déclenchement direct depuis « Corriger ce fichier » et icône d'onglet `</>`

- **Déclenchement direct de la correction depuis le bouton « Corriger ce fichier » (`#live-submit`)** sur le tableau de bord ouvert par `moulinette dashboard` : démarrage automatique d'un démon local en arrière-plan (`127.0.0.1` protégé par jeton de session) permettant à la page `dashboard.html` d'exécuter directement la correction en temps réel (`SSE`) dès l'appui sur « Corriger ce fichier », avec rechargement automatique des statistiques à la fin de l'exécution.
- **Icône d'onglet du navigateur (`favicon` `</>`)** : badge carré arrondi en dégradé violet avec le symbole `</>` intégré en SVG Base64 hors ligne dans l'en-tête `<head>` de la page.
- **Intégration des 105 phrases d'humour** de la `v0.29.9-dev`.

## Nouveautés v0.30.07-dev — Correction directe d'un fichier `.c` isolé et neutralisation d'un `main()` de test

- **Prise en charge native d'un chemin de fichier `.c` dans `moulinette check` et `moulinette dashboard --live`** (`detect_exercise` + `stage_submission_path` dans `moulinette/cli.py`) : passer directement un fichier comme `moulinette check "/chemin/vers/ft_is_negative.c" --unsafe-local` (ou `--experimental-sandbox`) détecte automatiquement l'exercice correspondant (`c00/ex04`) et évalue ce fichier dans un répertoire de travail isolé (avec ses en-têtes compagnons éventuels), même s'il se trouve dans un dossier de travail contenant d'autres exercices ou binaires compilés.
- **Neutralisation automatique d'un `main()` de test laissé dans un exercice de fonction** (`moulinette/checker.py` et `moulinette/project_job.py`) : si l'étudiant a laissé une fonction `main()` de test dans un fichier d'exercice de fonction, le moteur la neutralise lors de la liaison avec le harnais (`-Dmain=__moulinette_student_main`), affiche une note d'information (`Adaptation compilation`) rappelant de retirer `main()` pour un rendu 42 strict, et exécute l'intégralité des tests fonctionnels et de la Norminette.

## Nouveautés v0.30.06-dev — Animation de structure atomique derrière la carte de progression

- **Structure atomique animée (`#atom-svg`) en arrière-plan de la carte de progression (`Votre progression`)** : trois orbites elliptiques croisées (`-30°`, `30°`, `90°`), halo orbital et noyau central lumineux avec 6 électrons (`.atom-electron`) en gravitation continue autour et derrière la carte de progression en pourcentage, prenant automatiquement les couleurs d'accentuation et de lueur du thème sélectionné.

## Nouveautés v0.30.05-dev — Barre de correction de fichier permanente sur le tableau de bord

- **Barre de recherche et de correction (`#live-form` / `#live-path`) affichée en permanence** sur le tableau de bord (`dashboard.html` comme `dashboard --live`), permettant de renseigner directement le chemin d'un fichier `.c` ou d'un dossier de rendu à corriger, avec option `Exercice : Détection auto` par défaut.

## Nouveautés v0.30.04-dev — Pages de garde mémoire, suivi `malloc`/`free`, pipeline unifié et `--jobs`

- **Protection mémoire par pages de garde (`mmap` / `mprotect` dans `moulinette/c_memguard.py`)** : chaque allocation `malloc` dans le harnais C est calée contre une page de garde `PROT_NONE` (détectant au premier octet tout débordement `off-by-one` comme `malloc(len)` au lieu de `malloc(len + 1)`), initialisée avec l'octet poison `0xA5` (détectant l'oubli du `'\0'` final ou d'initialisation de pointeur) et placée en quarantaine `PROT_NONE` lors de `free()` (détectant immédiatement les accès après libération *use-after-free* et les *double-free*).
- **Vérification de libération effective (`ml_unfreed_count`) et entrées constantes en lecture seule (`ml_ro_str`)** : `ft_strdup` reçoit une chaîne en page `PROT_READ` calée contre une page `PROT_NONE`, et `ft_list_clear` / `ft_list_remove_if` vérifient que tous les maillons `t_list` supprimés ont effectivement été passés à `free()`.
- **Signalement indicatif des boucles dans les fonctions récursives C05** : `recursion_hint` signale (toujours à titre indicatif et non bloquant) la présence de mots-clés d'itération (`while`, `for`, `do`, `goto`) dans `c05/ex01`, `c05/ex03` et `c05/ex04`.
- **Factorisation du pipeline (`moulinette/pipeline.py`) et parallélisation (`-j` / `--jobs`)** : unification de l'analyse `nm -u`, du filtrage des canaris de pile et de la construction des rapports entre `checker.py` et `project_engine.py`, et ajout de `-j` / `--jobs N` (1 à 8) pour paralléliser `--module` et `--all`.

## Nouveautés v0.30.03-dev — Animation d'arrière-plan, polices, égalisation et actualisation automatique

- **Animation de code en arrière-plan (`#bg-matrix` & `#bg-terminal`)** : défilement de glyphes Matrix/système sur canevas plein écran aux couleurs du thème actif et flux de journaux de compilation/liaison/isolation en filigrane d'arrière-plan, sans aucun extrait d'exercice de la Piscine.
- **Sélecteur de police hors ligne (`#font`)** : choix mémorisé dans `localStorage` entre `DM Sans`, `Terminal Mono`, `Éditorial Serif`, `Néo-Grotesque` et `Humaniste`.
- **Égalisation des sections et actualisation automatique** : alignement en largeur et en hauteur (`1fr / 1fr`, `align-items: stretch`) des cartes de statistiques, des panneaux de synthèse (`Progression par module` / `Activité enregistrée`) et des panneaux principaux (`42 · Piscine C` / `Dernières corrections`), régénération automatique de `dashboard.html` à chaque `moulinette check`, titre simplifié en « Votre progression » et mise à jour de la section « À savoir ».

## Nouveautés v0.30.02-dev — Animation de code C et nouveaux thèmes

- **Animation de code C intégrée au tableau de bord** : un terminal animé interactif (`#code-anim`) dans la section d'accueil saisit en direct des fonctions C de la Piscine (`ft_putchar`, `ft_strlen`, `ft_swap`, `ft_iterative_factorial`, `ft_putstr`) avec coloration syntaxique, curseur clignotant, trace d'exécution simulée et bouton `Extrait ↻` pour changer d'extrait, accompagné de jetons C orbitaux animés autour de l'anneau de progression (respectant `prefers-reduced-motion`).
- **Six nouveaux thèmes inspirés de palettes Pinterest** ajoutés aux cinq thèmes existants et au mode aléatoire : `Sakura Nocturne`, `Cyberpunk Néon`, `Matcha Kyoto`, `Espresso Caramel`, `Fjord Polaire` (`nordic`) et `Mirage Doré` (`sunset`).

## Améliorations ciblées v0.30.01-dev

- **Tableau de bord (`moulinette dashboard` / `--live`)** : le tableau de bord Senthora hors ligne est conservé intact avec ses thèmes (`Aurore`, `Night Owl`, `Océan`, `Forêt`, `Braise`, `Aléatoire`), la case d'humour et les quatre guides PDF Blanc/Océan. Les détails de correction ajoutent l'état des 4 étapes réelles du moteur (`01 · Fichiers`, `02 · Compilation`, `03 · Tests`, `04 · Norminette`), un comparateur côte-à-côte (`Expected Output` vs `Your Output`) avec caractères invisibles visibles (`\n`, `\0`, `\t`, espaces de fin de ligne `·`) lorsque les octets capturés sont présents dans le message, un surlignage des lignes fautives signalées par la Norminette, et deux visualisations d'historique basées uniquement sur la base SQLite réelle (`Progression par module` et `Activité enregistrée`), sans aucune mention trompeuse de type « 0 leak », « 0 segfault » ou « Norme 100 % ». Le mode optionnel `moulinette dashboard --live` ouvre un serveur local restreint à `127.0.0.1` protégé par jeton de session, `Host` et `Origin`, qui diffuse en direct (`SSE`) chaque étape au fur et à mesure de sa confirmation par le moteur.
- **Corrections C** :
  - Option `--sanitize` : repasse optionnelle non bloquante compilée avec `ASan + UBSan` en mode `--unsafe-local` ou `UBSan trap` sous `--experimental-sandbox` (où `RLIMIT_AS=256 Mo` et l'absence de `/proc` empêchent la mémoire fantôme d'ASan). Un succès indique uniquement « aucun problème observé sur les cas exécutés » et non une preuve d'absence de fuite ou de comportement indéfini ; l'indisponibilité de l'outil ne modifie pas le verdict habituel.
  - Diagnostics syntaxiques **indicatifs et non bloquants** (`status: info`) : conservation de l'indice de récursivité pour C05 (`ex01`, `ex03`, `ex04`, `ex08`), ajout d'un indice indicatif de tableau de pointeurs de fonctions pour `c11/ex05` (`do-op`) et d'un indice de signature de `main` pour `c06` (`ex00` à `ex03`), avec mention explicite des limites (macros, `typedef`, pointeurs de fonctions, compilation conditionnelle et branches non exécutées).
  - Contrôles `Makefile` C10 (`ex00` à `ex03`) : vérification que `make` invoque `cc` avec `-Wall`, `-Wextra` et `-Werror` (exigés par le chapitre I des sujets C10) et que `make clean` conserve le binaire compilé, sans imposer de règle `re` non demandée par le sujet C10.
- **Isolation** :
  - Filtre seccomp BPF classique (`x86_64`) transmis à `bwrap --seccomp` bloquant 24 appels système d'administration/noyau/montage/traçage (`ptrace`, `mount`, `umount2`, `pivot_root`, `chroot`, `bpf`, `perf_event_open`, `unshare`, `setns`, etc.) et l'ABI `x32` avec `EPERM`, sans désactiver aucune protection existante.
  - Nettoyage des descendants (`project_job.py`) étendu aux processus de la même session (`sid == pgid`) ayant changé de groupe (`setpgid(0, 0)`), vérifié par test léger, sans prétendre garantir l'arrêt de tous les processus détachés ni rendre sûr du code malveillant.
- **CLI et organisation** :
  - Autodétection de l'exercice lorsque `--exercise` est omis (refus explicite avec liste des candidats en cas d'ambiguïté), modes `--module cXX` et `--all`, et mode `--watch` sérialisé avec arrêt propre (`Ctrl+C`).
  - Ajout de `.gitignore` et `.github/workflows/tests.yml` (exécutant `python3 tools/test_sans_charge.py`).

## Perfectionnement ciblé des corrections v0.29.8-dev

Neuf cas fonctionnels non officiels complètent cinq exercices C11 : `ft_map` sur un élément, ordre des appels de `ft_any` avec correspondance, arguments et opérateurs de `do-op`, et tableaux vides ou à un élément pour les deux tris de chaînes. `ft_any` peut s'arrêter après une correspondance ou continuer dans l'ordre. Trois variantes de confiance détectées par les nouveaux cas avaient réussi les anciens cas fonctionnels correspondants. Voir `docs/qualite-c11-v0.29.8-dev.md`.

La v0.29.7 a été validée sur l'Ubuntu utilisateur : 342 tests sans charge, quatre tests cgroup réels et un exemple C05/ex08 avec diagnostic indicatif. La v0.29.8 reste à y valider. Aucun test OOM ou de saturation n'est nécessaire.

## Finitions v0.29.7-dev

La commande `moulinette --version` identifie la version de l'exécutable utilisé ; `command -v moulinette` indique son chemin. Le tableau de bord explique aussi les messages reconnus de paramètre inutilisé, déclaration implicite et point-virgule attendu, sans deviner les erreurs non reconnues.

Pour C05/ex01, ex03, ex04 et ex08, un **indice textuel non bloquant** signale un cycle possible d'appels entre fonctions locales, direct ou via une fonction auxiliaire. Ce n'est pas une preuve de récursivité ni une validation du sujet : macros, pointeurs de fonctions, code conditionnel ou appels non exécutés peuvent masquer ou simuler un cycle. L'absence d'indice ne provoque pas d'échec ; les contrôles fonctionnels et le style restent distincts.

La v0.29.6 a réussi sur l'Ubuntu utilisateur **334 tests sans charge en 202,627 s**, **4 tests cgroup réels en 3,087 s** et une correction C05/ex06 depuis la commande installée. La v0.29.7 reste à y valider. Aucun test OOM ni saturation n'est nécessaire.

## Renforcement ciblé des corrections v0.29.6-dev

Vingt-et-un cas fonctionnels non officiels ont été ajoutés sur 17 exercices C05, C10, C11, C12 et C13 : valeurs numériques, fichiers binaires de 5 Kio, entrée standard, ordre des callbacks, données transmises, comparateur non normalisé, recherche et profondeur d'arbre. Le harnais accepte désormais plus de dix cas distincts. Cinq variantes volontairement erronées, qui passaient les anciens cas fonctionnels, sont détectées par les nouveaux. Voir `docs/qualite-corrections-v0.29.6-dev.md`.

Dans l'environnement de développement, la sélection sans charge a réussi **334 tests en 159,479 s**, quatre témoins actifs exclus. Le navigateur et l'installation isolée ont aussi été vérifiés.

Ces ajouts ne prouvent toujours pas la récursivité ou l'itération, le tableau de pointeurs de do-op, tous les cas Makefile, la gestion mémoire ni la conformité officielle. La v0.29.5 a réussi sur l'Ubuntu utilisateur 332 tests sans charge et quatre tests cgroup réels ; la v0.29.6 a depuis été validée sur cet Ubuntu.

## Robustesse des programmes bloqués v0.29.5-dev

En mode Bubblewrap pour les projets, les commandes sont placées dans des groupes distincts : le groupe est arrêté et observé avant la suite. Un délai dépassé interrompt les tests suivants, sans démarrer la vérification de style. Les descendants qui changent de groupe et les arrêts brutaux restent des limites ; le mode local reste non isolé. La réception du résultat cgroup a un budget global de 230 s après l'envoi de la demande, au lieu d'un délai de 120 s par opération. Il ne s'agit pas d'une limite globale de la correction entière. Voir `docs/securite-v0.29.5-dev.md`.

La v0.29.4 a été validée sur l'Ubuntu utilisateur : 323 tests sans charge, quatre tests cgroup réels et quatre téléchargements de guides réussis. La v0.29.5 a été validée fonctionnellement sur cet Ubuntu ; code de confiance uniquement.

## Présentation v0.29.4-dev

Deux documents, chacun en **Blanc et Océan** : le tableau de bord affiche deux boutons de téléchargement direct par guide. Les quatre liens fonctionnent hors ligne, sans fenêtre d'aperçu ni JavaScript. Les PDF sont statiques et ne contiennent pas vos résultats personnels. Arcs et symboles décorent toutes les pages.

La v0.29.4 a réussi 323 tests sans charge sur l'Ubuntu utilisateur. Pour la v0.29.5, 332 tests de la sélection sans charge ont réussi en 155,465 s dans l'environnement de développement ; quatre témoins actifs de limites ont été exclus.

Les quatre PDF actuels se trouvent dans `docs/manuel-utilisateur-v0.29.8-{blanc,ocean}.pdf` et `docs/guide-style-c-v0.29.8-{blanc,ocean}.pdf` ; les fichiers sans suffixe correspondent à Océan. Pour les régénérer depuis les sources Markdown avec ReportLab installé : `python3 tools/generer_guides_themes.py`. Les scripts `creer_manuel.py` et `creer_guide_style.py` sont des moteurs internes. ReportLab n'est pas nécessaire pour utiliser le Lab.

## Présentation v0.29.2-dev

Le guide du style C adopte une teinte corail claire, avec des arcs, motifs et symboles de code en filigrane répartis différemment sur chaque page. Son texte, ses polices et sa structure sont conservés. Le manuel utilisateur garde son fond Aurore. Les deux boutons restent disponibles dans le tableau de bord.

## Présentation v0.29.1-dev

Le guide du style C adopte un fond écarlate ; son contenu et les polices restent inchangés, hormis la version indiquée. Le manuel utilisateur conserve son fond Aurore. Les deux PDF sont inclus et accessibles par leurs boutons respectifs. Le moteur et les fonctionnalités du tableau de bord restent identiques à la v0.29.

## Nouveautés v0.29-dev

Le tableau de bord explique certains diagnostics de compilation reconnus et rappelle le prototype disponible dans le catalogue sans prétendre l'avoir validé si la compilation a échoué. Il compare aussi les contrôles identifiés de façon unique avec la tentative précédente du même exercice parmi les 50 dernières affichées. Un contrôle non exécuté n'est pas supposé réussi ou échoué. Les explications sont indicatives, à partir des messages enregistrés, sans lecture de votre fichier actuel ; elles ne couvrent pas toutes les erreurs.

Un second bouton télécharge le **guide du style C** : fond pourpre, Liberation Serif et JetBrains Mono, règles pratiques, exemple et erreurs fréquentes. Guide non officiel : Norminette 3.3.59 et seul `INVALID_HEADER` ignoré en mode autodidacte. Les tests et le guide ne garantissent pas la conformité officielle. Le manuel utilisateur reste disponible séparément.

Sur l'Ubuntu utilisateur, la v0.28.3 a obtenu **313 tests sans charge en 228,007 s** et **4 tests de scope cgroup réel en 2,732 s**, tous OK ; cela ne valide pas la v0.29 sur cet Ubuntu ni les limites sous charge.

## Limites et nettoyage v0.28.3-dev

Les limites et le nettoyage cgroup ont été examinés, avec neuf tests légers supplémentaires. Un état `cgroup.events` absent ne suffit plus à déclarer vide un scope dont le répertoire existe encore. Sélection sans quatre anciens témoins actifs de limites : `python3 tools/test_sans_charge.py`. Les limites sous charge et le scope réel de cette version ne sont pas encore validés. Voir `docs/securite-v0.28.3-dev.md`.

La v0.28.2-dev a réussi **308 tests en 199,591 s** sur l'Ubuntu utilisateur, sans skip affiché. Ce résultat n'est pas une validation de sécurité ni du scope cgroup réel de la v0.28.3.

## Reprise de la sécurité v0.28.2-dev

Les projets en mode Bubblewrap n'exposent plus le venv Norminette par un montage explicite dans le bac de compilation/exécution. Le style est vérifié ensuite dans un bac séparé, sur la copie initiale du rendu. Cela ne protège pas contre le code hostile et le mode local n'est pas isolé. Un témoin fictif et la suite standard ont été exécutés : **308 tests réussis** dans l'environnement de développement puis 308 sur l'Ubuntu utilisateur. Pas de test OOM forcé ni de scope cgroup réel de cette version. Détails et limites : `docs/securite-v0.28.2-dev.md`.

## Nouveau : présentation du manuel v0.28.1-dev

Le manuel adopte le fond sombre Aurore sur toutes les pages, **Liberation Serif** pour le texte et **JetBrains Mono** pour les lignes de code. Ces polices sont intégrées au PDF et fournies avec leurs licences pour la régénération. En v0.28.2, le guide a été actualisé pour la modification de sécurité, tout en conservant son contenu pédagogique.

## Nouveau : manuel utilisateur v0.28-dev

Dans l'environnement de développement, la v0.28 a réussi **304 tests**. Le manuel est décrit dans `docs/manuel-utilisateur.md` ; pour la version actuelle et les commandes de régénération, voir la présentation actuelle ci-dessus.

## Ajustement v0.27.1-dev

La case humour est revenue en haut du tableau de bord et le texte d’accroche précédent a été retiré. Les thèmes, les résultats et le PDF restent inchangés. Les tests ciblés du tableau de bord et du navigateur ont été relancés ; le moteur de correction n’a pas changé.

## Nouveau : tableau de bord v0.27-dev

Le tableau de bord local a été repensé dans un style sombre inspiré de Senthora, sans reprendre son contenu ou son identité. Il conserve l'historique, les scores locaux, le manuel provisoire et les 109 exercices. Une recherche et un filtre par module facilitent la navigation ; chaque exercice affiche son état par une couleur **et un libellé** : réussi, à revoir, incomplet ou à découvrir.

En haut à droite, choisissez Aurore, Night Owl, Océan, Forêt ou Braise : le navigateur mémorise ce thème pour les prochaines ouvertures de la page locale. L'option **Aléatoire à l'ouverture** choisit un thème différent de celui utilisé précédemment chaque fois que la page est ouverte ou rechargée. Le choix est enregistré dans le stockage local du navigateur, séparément de l'historique SQLite : il dépend du navigateur et de l'adresse du fichier. Si le stockage est bloqué, la page le signale et le choix ne peut pas persister. Régénérez le tableau de bord à son chemin habituel avec `moulinette dashboard` pour retrouver ces préférences dans le même navigateur.

Le manuel PDF intégré a été remplacé en v0.28 ; il reste non officiel et adapté au mode autodidacte.

## Correctif v0.26.1-dev

Suite au test de la v0.26 sur Ubuntu (16 échecs de tests, concernant 13 exemples distincts), le moteur compile les sources C12 en C11 pour leurs prototypes historiques et traite l'ambiguïté de protection de pile par recompilation et nouvelle analyse. Pour un projet compilé par le moteur, les objets alternatifs inspectés sont liés et testés avec `-fno-stack-protector` ; la protection de pile de ces objets est donc désactivée. Pour un programme Makefile, le binaire d'origine reste testé et les objets alternatifs n'offrent qu'une **analyse indicative**, pas la preuve qu'ils sont ceux du binaire. Les appels interdits restent contrôlés ; si un symbole de pile reste ambigu, la correction reste incomplète. Voir `ETAT-CHANTIER.md`.

Les 13 parcours ont été testés avec Bubblewrap, vraie Norminette, et une simulation de compilateur passant par défaut en C23 et activant la protection de pile. La v0.26.1-dev a réussi les 296 tests standards sur l'Ubuntu utilisateur ; la v0.26 précédente a validé C12/ex08 en scope cgroup réel, pas la version entière.

## Avant tout : code de confiance seulement

**La sécurité est reprise mais n'est pas achevée.** Aucun mode n'est approprié pour un rendu ou un dépôt hostile : le mode local n'isole rien ; Bubblewrap et le mode cgroup restent expérimentaux et ne constituent pas une protection garantie. Pas de filtre seccomp, noyau partagé et limites incomplètement validées. Ne désactivez pas les protections système pour faire fonctionner le programme. Le témoin de charge CPU/OOM de la v0.20 est désactivé depuis la v0.21 : **ne l'exécutez pas depuis l'ancienne v0.20**. Voir `docs/securite-v0.28.3-dev.md`, `docs/securite-v0.28.2-dev.md`, `docs/securite-v0.23-dev.md` et `ETAT-CHANTIER.md`.

## Installer et lancer

Sur Ubuntu : Python 3.10+, compilateur `cc`, `make`, `ar`, `nm`, Bubblewrap récent et **Norminette 3.3.59 dans un environnement virtuel**, accessible dans `PATH`. Pour les outils système, les paquets courants sont `python3`, `python3-venv`, `build-essential`, `binutils` et `bubblewrap`. En cas d'outil absent ou d'isolation indisponible, la correction peut être incomplète ; elle ne se replie pas automatiquement sur le mode non isolé.

Extrayez l'archive dans un **nouveau dossier**, puis ouvrez un terminal à sa racine. Activez l'environnement virtuel qui fournit Norminette 3.3.59, puis installez le Lab avec `python -m pip install .`. Ensuite, exemples de confiance :

```bash
moulinette check ./exemples/ft_putchar --exercise c00/ex00 --experimental-sandbox
moulinette check ./exemples/c10/ex02 --exercise c10/ex02 --experimental-sandbox
moulinette check ./exemples/c12/ex08 --exercise c12/ex08 --experimental-sandbox
moulinette dashboard
```

Remplacez le chemin par votre propre dossier de rendu de confiance. À partir de C 01, les références se trouvent sous `exemples/cXX/exYY/`. Un dossier de rendu ne doit pas contenir de fichiers supplémentaires pour les exercices à fichiers imposés ; les projets autorisant des fichiers libres suivent leurs règles spécifiques. `--json` donne un rapport lisible par machine ; `--no-history` évite l'enregistrement. Codes de sortie : 0 = contrôles exécutés réussis, 1 = échec détecté, 2 = incomplet ou erreur d'utilisation.

Un mode `--experimental-cgroup-sandbox` existe si un scope systemd utilisateur approprié est disponible. La nouvelle branche multi-fichiers **n'a pas été validée en scope cgroup réel** dans l'environnement de développement ; C12/ex08 a réussi en scope réel sur l'Ubuntu utilisateur en v0.26 ; les versions 0.26.1 et 0.27 n'ont pas été retestées dans ce scope réel. Le mode `--unsafe-local` exécute avec vos droits, sans isolation ; il nécessite également du code de confiance.

## Exercices et sujets

| Module | Version du PDF fourni | Exercices |
|---|---:|---:|
| C 00 | 8 | 9 |
| C 01 | 6 | 9 |
| C 02 | 6 | 13 |
| C 03 | 5 | 6 |
| C 04 | 5 | 6 |
| C 05 | 7 | 9 |
| C 06 | 8 | 4 |
| C 07 | 6 | 6 |
| C 08 | 14 | 6 |
| C 09 | 5.0 | 3 |
| C 10 | 7.1 | 4 |
| C 11 | 8.0 | 8 |
| C 12 | 9.0 | 18 |
| C 13 | 6.0 | 8 |

Tous les identifiants ont un harnais et des tests de comportement. Le moteur prend en charge fichiers C multiples, en-têtes, scripts, bibliothèques, Makefiles et programmes ; les modalités dépendent de l'exercice. Les sujets PDF et Markdown fournis ont été analysés et leurs exigences intégrées au code : **aucun import automatique des sujets n'est disponible**. Les versions/numéros des paires concordent ; l'identité textuelle intégrale des PDF et Markdown n'a pas été démontrée.

La Norminette est adaptée au profil autodidacte : seule l'erreur `INVALID_HEADER` est ignorée. Les en-têtes institutionnels et les obligations intranet ne sont pas exigés. Le reste des diagnostics du style est conservé. `c09/ex01` ne rend qu'un Makefile : Norminette n'y est pas applicable.

### Limites pédagogiques importantes

- Les cas sont **non exhaustifs** ; les comportements hors sujet, les problèmes mémoire, les erreurs d'allocation et tous les cas limites ne sont pas couverts. Aucun outil n'effectue de vérification mémoire complète.
- Les contraintes de récursivité/itération de C 05 et l'obligation de tableau de pointeurs de fonctions de `c11/ex05` **ne sont pas démontrées** par les tests fonctionnels. Pour C 05/ex08, les 724 solutions distinctes et leur validité sont contrôlées, mais pas la récursivité.
- Pour C 06, la signature de `main` n'est pas vérifiée séparément et un retour 0 est une convention locale. Pour C 10, tests d'erreurs/options et Makefile restent partiels ; `all`, `clean`, `fclean` sont exécutés, et la suppression/reconstruction du programme est contrôlée, sans prouver toutes les dépendances ni le nettoyage de tous les objets. Signes `+` et `-` de `tail -c` ne sont pas exigés par le sujet.
- Les tests de listes C 12 et d'arbres C 13 vérifient des opérations et structures spécifiées, mais ne constituent pas une preuve exhaustive de gestion mémoire, d'identité des nœuds ou de tous les cas d'arbre. Les données de test et fonctions auxiliaires indiquées par les sujets sont fournies au harnais lorsque nécessaire.
- L'analyse `nm` des fonctions externes est partielle. Pour un Makefile qui ne laisse aucun objet inspectable, des objets peuvent être recompilés séparément : **ils ne sont pas nécessairement les objets liés**. La présence d'un appel interdit peut arrêter la correction ; cela n'établit pas la sécurité du code.

## Tableau de bord

`moulinette dashboard` crée une page HTML locale autonome et tente de l'ouvrir ; `dashboard --no-open` indique son chemin sans ouvrir le navigateur. Après chaque correction, relancez la commande pour actualiser la page statique. Elle affiche les 50 dernières corrections et, pour les 109 exercices, l'état de la dernière tentative. Les données réelles sont stockées dans `~/.local/share/moulinette-lab/` ou sous `$XDG_DATA_HOME` ; les diagnostics peuvent contenir des extraits de code et des chemins.

Le score local est le nombre de contrôles réussis divisé par les contrôles réussis et échoués exécutés ; les informations sont exclues. Un échec peut interrompre les autres contrôles ; si un contrôle est indisponible ou le résultat incomplet, le score est masqué. Ce n'est pas une note officielle. Le manuel utilisateur inclus est statique.

## Dépôt GitHub public de confiance

```bash
moulinette check https://github.com/PROPRIETAIRE/DEPOT --exercise c07/ex04 --subdir c07/ex04 --trust-github --experimental-sandbox
```

Utilisez uniquement un dépôt public HTTPS dont vous avez vérifié **tout le contenu utile**, y compris Makefiles et scripts : ils seront exécutés. `--ref` accepte une branche, un tag ou un SHA complet de 40 caractères. Sans `--subdir`, la racine est utilisée. Pas de SSH, dépôt privé, sous-module ou contenu Git LFS récupéré. Le clone utilise Bubblewrap avec réseau partagé et un tmpfs limité ; ce n'est pas une garantie contre un dépôt hostile. Une erreur ne déclenche pas de repli local. Le parcours multi-fichiers a été testé sur un dépôt public inspecté de confiance, pas en scope cgroup réel.

## Validation et tests

```bash
python3 tools/test_sans_charge.py
```

Dans l'environnement de développement de la v0.27-dev : **300 tests réussis** avec Bubblewrap et Norminette 3.3.59 ; les 109 références sont passées en Bubblewrap et style réel (sauf le Makefile seul, non applicable). Des variantes fonctionnellement incorrectes sont rejetées, notamment pour les listes, arbres et programmes récents. Le nombre de tests ignorés dépend des outils disponibles. Cette validation ne prouve ni la sécurité ni la conformité exhaustive. Les tests séparés `tests_real/` requièrent un scope systemd utilisateur et ne sont pas inclus dans cette validation.

Pour installer la commande dans un environnement virtuel : `python3 -m venv ~/.venvs/moulinette-lab`, puis `~/.venvs/moulinette-lab/bin/python -m pip install .` depuis la racine. Des outils de construction peuvent être nécessaires.
