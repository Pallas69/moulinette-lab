# Résumé des évolutions : de `v0.29.9-dev` à `v0.30.08-dev`

Ce document récapitule l'ensemble des améliorations architecturales, fonctionnelles, visuelles et de sécurité apportées à **Moulinette Lab** depuis la version **`v0.29.9-dev`** jusqu'à la version actuelle (**`v0.30.08-dev`**).

---

## 1. Tableau de bord (`moulinette dashboard`) & Interface Utilisateur

### A. Correction interactive directe depuis la page (`#direct`)
- **En `v0.29.9-dev`** : le tableau de bord était purement statique ; il ne permettait pas de renseigner un fichier `.c` ni de lancer une correction depuis l'interface web.
- **Maintenant (`v0.30.01` → `v0.30.08`)** :
  - **Barre de recherche et de correction permanente (`#direct` / `#live-form`)** affichée sur le tableau de bord avec :
    - sélecteur d'exercice incluant **`Exercice : Détection auto`** par défaut ;
    - champ de saisie de chemin acceptant directement un **fichier `.c`** (ex. `/home/.../J02_0/ft_is_negative.c`) ou un **dossier** ;
    - choix du mode (`Bubblewrap expérimental` ou `Local non isolé`) ;
    - bouton **`Corriger ce fichier`** déclenchant immédiatement la correction depuis la page grâce au démon local en arrière-plan (`127.0.0.1` protégé par jeton cryptographique) et affichant la progression étape par étape en temps réel (`SSE`).
  - **Actualisation automatique de `dashboard.html`** à chaque correction (`CLI` comme interface web) sans avoir besoin de relancer manuellement `moulinette dashboard`.

### B. Suivi chirurgical des étapes, Diff d'octets et Norminette
- **En `v0.29.9-dev`** : les détails d'une correction affichaient uniquement une liste brute de messages texte.
- **Maintenant** :
  - **4 pastilles d'étapes réelles du moteur** : `01 · Fichiers`, `02 · Compilation`, `03 · Tests`, `04 · Norminette` (jamais affichées comme validées avant confirmation effective du moteur).
  - **Comparateur côte-à-côte (`Expected Output` vs `Your Output`)** dans `moulinette/dashboard_insights.py` rendant visibles les caractères invisibles (`\n`, `\0`, `\t`, octets hexadécimaux `\xHH`, espaces en fin de ligne `·`) sur les octets réellement capturés.
  - **Encadré de diagnostic Norminette structuré** avec extraction et surlignage du fichier, du numéro de ligne et de la colonne fautive (`ligne X · col Y`).
  - **Synthèse d'historique SQLite réel** : panneau `Progression par module` (`C00` à `C13`) et panneau `Activité enregistrée` (chronologie des 50 dernières tentatives), sans aucune garantie trompeuse (« 0 leak », « 0 segfault »).

### C. Direction artistique, Thèmes, Polices, Animations et Favicon
- **En `v0.29.9-dev`** : 5 thèmes (`Aurore`, `Night Owl`, `Océan`, `Forêt`, `Braise` + `Aléatoire`), 1 seule police, illustration statique autour du pourcentage, pas d'icône d'onglet (`favicon`).
- **Maintenant** :
  - **Icône d'onglet (`favicon` `</>`)** : badge carré arrondi en dégradé violet avec le symbole `</>` intégré en SVG hors ligne dans l'onglet du navigateur.
  - **11 thèmes hors ligne + mode aléatoire** : ajout de 6 thèmes inspirés de palettes Pinterest (`Sakura Nocturne`, `Cyberpunk Néon`, `Matcha Kyoto`, `Espresso Caramel`, `Fjord Polaire`, `Mirage Doré`).
  - **Sélecteur de 5 polices hors ligne (`#font`)** mémorisées dans `localStorage` : `DM Sans`, `Terminal Mono`, `Éditorial Serif`, `Néo-Grotesque`, `Humaniste`.
  - **Structure atomique animée (`#atom-svg`) derrière la carte de progression (`Votre progression`)** : noyau central lumineux, halo orbital et 3 orbites elliptiques croisées (`-30°`, `30°`, `90°`) sur lesquelles gravitent 6 électrons lumineux (`.atom-electron`) en continu.
  - **Animation d'arrière-plan (`#bg-matrix` & `#bg-terminal`)** : pluie de glyphes binaires/C sur canevas plein écran et journaux système/compilateur en filigrane d'arrière-plan.
  - **Égalisation géométrique des sections** (`1fr / 1fr`, `align-items: stretch`) et conservation des **105 traits d'humour** de la `v0.29.9-dev` et des **4 guides PDF** (`Manuel utilisateur` et `Guide du style C` en versions `Blanc` et `Océan`).

---

## 2. Moteur de correction C & Précision des contrôles

### A. Correction directe d'un fichier `.c` et neutralisation d'un `main()` de test (`v0.30.07`)
- **En `v0.29.9-dev`** : passer un chemin de fichier `.c` ou évaluer un fichier situé dans un dossier contenant d'autres exercices échouait (`Dossier introuvable` ou `Fichiers supplémentaires`), et laisser un `int main()` de test dans un exercice de fonction provoquait une erreur d'édition des liens (`multiple definition of 'main'`).
- **Maintenant** :
  - `detect_exercise` et `stage_submission_path` (`moulinette/cli.py`) détectent automatiquement l'exercice à partir du nom du fichier `.c` et isolent ce fichier (ainsi que ses `.h` compagnons éventuels) dans un espace temporaire propre.
  - Si un `main()` de test est présent dans un exercice de fonction, `checker.py`, `project_job.py` et `sandbox_runner.py` le neutralisent automatiquement (`-Dmain=__moulinette_student_main -Wno-unused-function -Wno-return-type`), affichent une note d'information (`Adaptation compilation`) et exécutent tous les tests fonctionnels ainsi que la Norminette.

### B. Allocateur à pages de garde matérielles (`moulinette/c_memguard.py`, `v0.30.04`)
- **En `v0.29.9-dev`** : le harnais C utilisait le `malloc`/`free` standard de la glibc ; un débordement d'un octet (`malloc(len)` au lieu de `malloc(len + 1)`), un oubli de `free` dans `C12` ou une lecture après `free` passait souvent inaperçu.
- **Maintenant** :
  - **Pages de garde `PROT_NONE` (`mmap` / `mprotect`)** : chaque allocation `malloc` est alignée à la fin d'une page mémoire suivie immédiatement d'une page `PROT_NONE`. Tout débordement d'un seul octet déclenche immédiatement `SIGSEGV`.
  - **Poison `0xA5` et quarantaine `free()`** : la mémoire fraîchement allouée est remplie avec `0xA5` (détectant l'oubli du `'\0'` terminal) et toute page libérée par `free()` passe en `PROT_NONE` (détectant immédiatement tout *use-after-free* ou *double-free*).
  - **Compteur de fuites (`ml_unfreed_count`) et chaînes constantes (`ml_ro_str`)** : vérification que `ft_list_clear` (`c12/ex06`) et `ft_list_remove_if` (`c12/ex12`) libèrent effectivement chaque maillon, et placement des chaînes d'entrée en page `PROT_READ` collée à une page `PROT_NONE`.

### C. Option `--sanitize`, diagnostics AST indicatifs et Makefiles `C10` (`v0.30.01` → `v0.30.04`)
- **Option `--sanitize`** : passe supplémentaire non bloquante avec `ASan + UBSan` en mode local et `UBSan trap` sous Bubblewrap.
- **Indices statiques non bloquants (`moulinette/recursion_hint.py`)** :
  - `C05` (`ex01`, `ex03`, `ex04`, `ex08`) : détection indicative des cycles d'appels ET signalement des mots-clés de boucle (`while`, `for`, `do`, `goto`).
  - `C06` (`ex00` à `ex03`) : vérification indicative de la signature de `main(int argc, char **argv)`.
  - `c11/ex05` (`do-op`) : détection indicative d'un tableau ou pointeur de fonctions.
- **Makefiles `C10`** (`ex00` à `ex03`) : vérification des drapeaux `-Wall -Wextra -Werror` lors de la compilation par `make` et vérification que `make clean` ne supprime pas le binaire.

---

## 3. Sécurité & Isolation (`sandbox_runner.py`, `seccomp_filter.py`, `project_job.py`)

- **Filtre noyau `seccomp-BPF` (`x86_64`)** (`moulinette/seccomp_filter.py`) transmis à `bwrap --seccomp`, bloquant 24 appels système sensibles (`ptrace`, `mount`, `umount2`, `pivot_root`, `chroot`, `bpf`, `perf_event_open`, `unshare`, `setns`, `kexec_load`, etc.) ainsi que l'ABI `x32` avec `EPERM`.
- **Nettoyage étendu des processus descendants** (`moulinette/project_job.py`) : balayage `/proc` par identifiant de session (`sid == pgid`) pour arrêter également les processus enfants ayant changé de groupe via `setpgid(0, 0)`.

---

## 4. CLI, Parallélisation & Organisation (`moulinette/cli.py`, `moulinette/pipeline.py`)

- **Commandes unifiées sous `moulinette`** (`~/.local/bin/moulinette`).
- **Autodétection de l'exercice** lorsque `--exercise` est omis (sur un fichier `.c` ou un dossier d'exercice).
- **Modes de lot `--module cXX` et `--all`** avec exécution parallèle **`-j` / `--jobs N`** (`1` à `8` travailleurs).
- **Mode `--watch`** séquentiel sans chevauchement avec arrêt propre (`Ctrl+C`).
- **Factorisation du pipeline** dans `moulinette/pipeline.py` (analyse `nm -u`, filtrage des canaris de pile, construction des rapports) et ajout de `.gitignore` et `.github/workflows/tests.yml`.
- **Suite de validation sans charge (`tools/test_sans_charge.py`)** passée de **334 tests** à **368 tests** (`100 % OK`).
