# Audit — Documents téléchargeables depuis le tableau de bord (v0.29.8 → v0.31-dev)

Document destiné à une autre IA (ou à un développeur) chargée de **mettre à jour les PDF téléchargeables** de Moulinette Lab pour qu'ils reflètent la v0.31-dev. Chaque point indique le fichier, la ligne, l'état actuel et le contenu attendu. Ne rien inventer au-delà des faits listés en section 6 ; vérifier dans le code en cas de doute.

---

## 1. Inventaire : ce qui est téléchargeable depuis la page

La section « Documents PDF » du tableau de bord (`moulinette/dashboard.py`, boucle `for label, stem, filebase in (...)`, vers la ligne 487) propose **2 documents × 2 thèmes = 4 PDF**, intégrés en `data:application/pdf;base64,...` dans `dashboard.html` (aucun accès réseau) :

| Bouton | Fichier embarqué (`moulinette/assets/`) | Nom proposé au téléchargement | Source éditable | Générateur |
|---|---|---|---|---|
| Manuel utilisateur · Blanc | `guide-utilisation-blanc.pdf` | `manuel-moulinette-lab-v0.29.8-blanc.pdf` | `docs/manuel-utilisateur.md` | `tools/creer_manuel.py` |
| Manuel utilisateur · Océan | `guide-utilisation-ocean.pdf` (copie : `guide-utilisation.pdf`) | `manuel-moulinette-lab-v0.29.8-ocean.pdf` | idem | idem |
| Guide du style C · Blanc | `guide-style-c-blanc.pdf` | `guide-style-c-moulinette-lab-v0.29.8-blanc.pdf` | `docs/guide-style-c.md` | `tools/creer_guide_style.py` |
| Guide du style C · Océan | `guide-style-c-ocean.pdf` (copie : `guide-style-c.pdf`) | `guide-style-c-moulinette-lab-v0.29.8-ocean.pdf` | idem | idem |

Orchestrateur des 4 variantes : `tools/generer_guides_themes.py` (nécessite **ReportLab**, absent de la machine actuelle ; polices fournies dans `moulinette/assets/` : Liberation Serif, JetBrains Mono, DM Sans, avec licences). Copies d'archive versionnées dans `docs/manuel-utilisateur-v0.29.8-{blanc,ocean}.pdf` et `docs/guide-style-c-v0.29.8-{blanc,ocean}.pdf`.

---

## 2. Constat principal

> [!IMPORTANT]
> **Les 4 PDF embarqués sont identiques octet pour octet à ceux de la v0.29.8** (sommes MD5 identiques entre `moulinette-lab-v0.29.8-dev/moulinette/assets/` et `moulinette-lab-v0.31-dev/moulinette/assets/`). Aucune évolution de v0.29.9 à v0.31 n'apparaît dans les documents téléchargés par l'utilisateur.

| Fichier | MD5 (v0.29.8 = v0.31) |
|---|---|
| `guide-utilisation-blanc.pdf` | `4a7e6a4138999ad5708e49507ed86c27` |
| `guide-utilisation-ocean.pdf` / `guide-utilisation.pdf` | `4fc46614c1764cd1604d033d6894e8f2` |
| `guide-style-c-blanc.pdf` | `40d2791bff49804b6f3fd3e1b10126d5` |
| `guide-style-c-ocean.pdf` / `guide-style-c.pdf` | `16dcc167b2354e42baca0a43b5f6861d` |

Autres constats :
- `docs/manuel-utilisateur.md` a été **partiellement** modifié en v0.30.01–v0.30.03 (thèmes, options `--module/--all/--jobs/--watch/--sanitize`, `dashboard --live`), mais **les PDF n'ont jamais été régénérés**, et la source contient maintenant des affirmations **fausses** (voir section 3).
- `docs/guide-style-c.md` n'a pas été modifié depuis la v0.29.8.
- Version **codée en dur** à trois endroits : `moulinette/dashboard.py` (`filename = filebase + '-v0.29.8-' + theme + '.pdf'`), `tools/generer_guides_themes.py` (en-tête de page `'  ·  v0.29.8-dev'` et noms de sortie `-v0.29.8-`), en-têtes des deux Markdown (`VERSION 0.29.8-DEV`).

---

## 3. Modifications à apporter à `docs/manuel-utilisateur.md`

Numéros de ligne relevés sur la v0.31-dev.

### 3.1 Affirmations devenues fausses (priorité haute)

| Ligne | Texte actuel | Correction attendue |
|---|---|---|
| 3 | `GUIDE UTILISATEUR · VERSION 0.29.8-DEV` | `VERSION 0.31-DEV` |
| 7 | « … sur les exercices C de la Piscine. » | « … sur les exercices des piscines C, C++ et Python. » |
| 23 | « Le catalogue comprend **109 exercices**, de C00 à C13. » | 190 exercices : C (109, C00–C13), C++ (45, CPP00–CPP08), Python (36, module00–module04). Préciser les types de rendus C++ (Makefile, `.cpp`, `.hpp`) et Python (`.py`, `answers.txt`, `requirements.txt`…). |
| 84–93 | Archive / dossier / version `v0.29.8-dev`, `0.29.8.dev0` | `moulinette-lab-v0.31-dev`, `0.31.0.dev0` |
| 120–145 | Exemples avec `moulinette check … --exercise … --experimental-sandbox` | Donner d'abord la forme courte : `moulinette ./exemples/c10/ex02` (Bubblewrap par défaut). Garder une mention de la forme longue (toujours valide). |
| 147 | « Le chemin est un **dossier**, pas directement le fichier C. » | **Faux depuis v0.30.07** : un fichier isolé est accepté (`moulinette ~/rendu/ft_is_negative.c`) ; l'exercice est détecté, et le fichier est copié seul dans un dossier de travail avec ses en-têtes compagnons. Un `main()` de test laissé dans un exercice de fonction C est neutralisé (note « Adaptation compilation »). |
| 155 | « relancez cette commande : la page est **statique** et ne se met pas à jour seule. » | **Faux depuis v0.30.03** : chaque `moulinette check` régénère `dashboard.html` ; la page servie par le démon local se recharge quand l'historique change ; le bouton « Corriger ce fichier » lance la correction depuis la page (v0.30.08). |
| 170–174 | « Choisir un mode : un seul à la fois » + 3 options longues | Sans option : **Bubblewrap par défaut s'il est installé**, sinon refus. Le mode local non isolé n'est **jamais** implicite (`-l`). Tableau des alias : `-s/--sandbox` = `--experimental-sandbox`, `-l/--local` = `--unsafe-local`, `--cgroup` = `--experimental-cgroup-sandbox` (**C uniquement** : pour C++/Python le rapport est « incomplet »). |
| 216 | « Le tableau de bord affiche les **109 exercices** » | Parcours séquentiel C → C++ → Python, carte de progression unique pour la piscine en cours, déblocage (voir 6.3). |
| 227 (fin) | « Un aperçu animé de code C dans l'entête illustre des extraits classiques de la Piscine » | **Supprimé en v0.30.03** à la demande de l'utilisateur. Remplacer par : animation Matrix + terminal en arrière-plan (sans extrait d'exercice), atome 3D derrière la carte de progression, sélecteur de police (5 choix). |
| 258 | « requis sauf avec `--all` qui parcourt `exemples/` par défaut » | **Non vérifié / inexact** : `path` est un argument positionnel obligatoire de `check`. Écrire « obligatoire ». |
| 259–261 | `--exercise cXX/exYY`, `--module cXX` | `-e/--exercise` (`c00/ex00`, `cpp00/ex00`, `py00/ex00`), `-m/--module` (`c00..c13`, `cpp00..cpp08`, `py00..py04`), `-a/--all`. |
| 265 | « choisir explicitement **un seul** mode » | Voir ligne 170 : mode par défaut Bubblewrap ; modes toujours mutuellement exclusifs. |
| 331 | `cd ~/Téléchargements/moulinette-lab-v0.29.8-dev` | `…-v0.31-dev` |
| 351 | « Régénérez-la après chaque correction. » | Plus nécessaire (voir ligne 155). |
| 357–365 | Section 09 limitée aux 14 sujets C | Ajouter C++ (`cpp00` 3, `cpp01` 11, `cpp02` 4, `cpp03` 5, `cpp04` 5, `cpp05` 6, `cpp06` 3, `cpp07` 3, `cpp08` 5 = 45) et Python (`py00` 11, `py01` 6, `py02` 6, `py03` 5, `py04` 8 = 36). **Ne pas inventer de numéro de version de sujet** : aucune version n'est lisible dans le texte des PDF C++/Python fournis ; le catalogue enregistre « 1.0 » par défaut. Signaler que les Markdown CPP07/CPP08 fournis contiennent des artefacts de conversion et que les PDF font foi. |
| 393 | Historique de tests s'arrêtant à v0.29.8 | Ajouter : v0.30.09 et v0.31 — 372+ tests sans charge réussis dans l'environnement de développement ; pas encore validées sur l'Ubuntu utilisateur. |

### 3.2 Contenus absents à ajouter

1. **Commandes simplifiées (v0.31)** dans « 03 · Première utilisation » et « 07 · Commandes » :
   ```bash
   moulinette                          # ouvre le tableau de bord
   moulinette ~/rendu/ft_putchar.c     # corrige un fichier (Bubblewrap par défaut)
   moulinette ~/rendu/c01 -m c01       # un module
   moulinette ~/rendu -a               # tous les exercices trouvés
   moulinette ~/rendu/ex00 -e cpp00/ex00 -l
   moulinette list --piscine cpp       # c, cpp, py, all
   moulinette ui                       # alias de dashboard
   moulinette dashboard --db COPIE.sqlite3 --output page.html --no-open
   ```
2. **Prérequis C++ / Python** dans « 02 · Installation » : compilateur C++ (`clang++` prioritaire, sinon `g++` ou `c++`) ; `python3` ; bibliothèques optionnelles par exercice (`numpy` pour `py03`, `pandas` pour `py04`, `matplotlib`/`scipy` selon l'exercice). Leur absence donne « indisponible » → résultat « incomplet », **jamais** une réussite. Le Lab **n'installe rien** et n'accède pas au réseau pendant une correction.
3. **Contrôles C++** : compilation `-Wall -Wextra -Werror -std=c++98` ; interdits vérifiés (`*alloc`, `free`, `*printf`, `using namespace`, `friend`, STL et `<algorithm>` avant `cpp08`) ; gardes d'inclusion ; règles Makefile (`all`, `clean`, `fclean`, `re`, absence de relink) ; harnais de test par exercice.
4. **Contrôles Python** : analyse AST (`eval()` toujours interdit + fonctions/imports interdits propres à l'exercice) ; jeux de données synthétiques générés localement quand les fichiers externes (`athlete_events.csv`, `solar_system_census.csv`, `42AI.png`) ne sont pas fournis — donc tests **non équivalents** aux données réelles.
5. **Tableau de bord** : parcours C → C++ → Python, carte de progression unique, verrouillage limité à la page (voir 6.3) ; panneau « Corriger un fichier ou un dossier » avec bouton « Corriger ce fichier » (démon local `127.0.0.1` à jeton, démarré automatiquement par `moulinette dashboard`) ; atome 3D évolutif (voir 6.4) ; animation Matrix/terminal ; sélecteur de police ; icône d'onglet `</>` ; 105 phrases d'humour.
6. **Options C ajoutées depuis v0.30.01** déjà partiellement listées : vérifier `--sanitize`, `-j/--jobs`, `-w/--watch`, et ajouter les pages de garde mémoire (`c_memguard.py`, v0.30.04) dans les limites pédagogiques, sans prétendre à un contrôle mémoire complet.

---

## 4. Modifications à apporter à `docs/guide-style-c.md`

| Ligne | Actuel | Attendu |
|---|---|---|
| 3 | `GUIDE PRATIQUE · VERSION 0.29.8-DEV` | `VERSION 0.31-DEV` |
| Section « 01 · Le profil du Lab » | Ne précise pas le périmètre | Ajouter un encadré : « Ce guide couvre **uniquement le C** (Norminette 3.3.59, seul `INVALID_HEADER` ignoré). Les piscines C++ et Python ont des contrôles différents, décrits dans le manuel utilisateur. » |

Option (à décider avec l'utilisateur, ne pas faire sans accord) : ajouter un 3ᵉ document « Guide du style C++ et Python ». Faits utilisables :
- C++ : contraintes listées en 3.2 (point 3), C++98.
- Python : les sujets indiquent que **PEP 8 est recommandé mais non obligatoire** et suggèrent `pycodestyle`. Le Lab **ne lance pas** `pycodestyle`/`flake8` ; il n'effectue que les contrôles AST décrits en 3.2 (point 4).

> [!WARNING]
> Dans le code, le contrôle de style C++ et Python s'affiche sous le nom **« Norminette adaptée »** (`moulinette/cpp_engine.py` ≈ l. 326–328, `moulinette/py_engine.py` ≈ l. 232–237), alors que la Norminette n'est pas exécutée. Un guide ne doit pas reprendre ce libellé pour C++/Python. Le renommer (ex. « Contraintes C++98 », « Contraintes Python ») est recommandé, mais cela modifie la comparaison avec les tentatives précédentes dans l'historique : à faire avec un test dédié.

---

## 5. Modifications de code / outillage nécessaires pour publier les nouveaux PDF

1. `tools/generer_guides_themes.py` : remplacer `v0.29.8-dev` (en-tête de page) et `-v0.29.8-` (noms de fichiers produits) par la nouvelle version — idéalement lue depuis `moulinette.__version__` pour éviter de recommencer.
2. `moulinette/dashboard.py` : `filename = filebase + '-v0.29.8-' + theme + '.pdf'` → dériver de `__version__` (ex. `0.31.0.dev0` → `v0.31`).
3. Régénérer puis copier les 4 PDF dans `moulinette/assets/` (`guide-utilisation-{blanc,ocean}.pdf`, `guide-style-c-{blanc,ocean}.pdf`, plus les copies sans suffixe = Océan) et archiver dans `docs/…-v0.31-{blanc,ocean}.pdf`.
4. Tests à adapter :
   - `tests/test_manual_v028.py` lit `docs/manuel-utilisateur-v0.29.8.pdf` (polices intégrées) → nouveau nom de fichier.
   - `test_editable_source_covers_commands_and_modes` exige dans le Markdown les termes `--experimental-sandbox`, `--unsafe-local`, `--experimental-cgroup-sandbox`, `109`, etc. : **conserver** ces formes longues (elles restent valides) en plus des raccourcis ; ajouter `190`, `-l`, `-s`, `moulinette list`.
   - `test_documented_options_match_cli_help` : les options longues apparaissent toujours dans `moulinette check --help` (vérifié en v0.31).
   - Les tests du tableau de bord vérifiant les 4 boutons et la taille des PDF intégrés.
5. Contrôle final : `python3 tools/test_sans_charge.py`, puis ouvrir la page et télécharger les 4 PDF (avec et sans JavaScript).

Commandes (ReportLab installé dans un environnement dédié, **avec l'accord de l'utilisateur** car cela nécessite le réseau) :
```bash
python3 -m venv ~/.venvs/ml-docs && ~/.venvs/ml-docs/bin/pip install reportlab
~/.venvs/ml-docs/bin/python tools/generer_guides_themes.py
```

---

## 6. Référentiel des faits v0.31-dev (source de vérité pour la rédaction)

### 6.1 Catalogue
- C : 109 (`c00/ex00`…`c13/ex07`) · C++ : 45 (`cpp00/ex00`…`cpp08/ex04`) · Python : 36 (`py00/ex00`…`py04/ex07`) · total 190.
- Identifiants de rapport : `42/c/…`, `42/cpp/…`, `42/py/…`.

### 6.2 Commandes et modes
- `moulinette` seul → tableau de bord ; `moulinette <chemin> [options]` = `moulinette check <chemin> [options]` ; `ui` = `dashboard` ; `list [--piscine c|cpp|py|all]`.
- Courtes : `-e -m -a -l -s -w -j` ; `--cgroup`. Longues historiques inchangées.
- Mode par défaut : Bubblewrap si `bwrap` est présent (message sur stderr), sinon refus (code 2) ; le mode local n'est jamais implicite.
- Fichiers acceptés directement : `.c`, `.cpp`, `.hpp`, `.py`, `.txt`, `.sh` (autodétection, refus en cas d'ambiguïté).
- `dashboard --db FICHIER --output FICHIER` : génère depuis une autre base (ex. copie) sans toucher la base réelle.
- Codes de sortie de `check` : 0 réussi, 1 échec, 2 incomplet/erreur.

### 6.3 Progression des piscines
- Ordre : C → C++ → Python. Une piscine est terminée quand **tous** ses exercices ont pour dernière tentative « réussi ».
- La suivante est alors débloquée **définitivement** (table SQLite `piscine_unlocks`, ajoutée sans modifier `attempts`), même si un exercice précédent repasse « à revoir ».
- Verrou **uniquement sur la page** ; la CLI corrige tout, à tout moment ; résultats anticipés conservés et affichés au déblocage.
- Une seule carte de progression, pour la piscine en cours ; les piscines débloquées restent consultables (exercices, modules, historique).

### 6.4 Atome 3D (v0.31)
- Aucune légende textuelle : pas de pastilles Protons/Neutrons/Électrons, pas de phrase d'analogie.
- L'animation se recalcule à chaque génération de la page (donc après chaque correction) et au changement de piscine consultée : un nucléon par exercice corrigé (vert = réussi, ambre = à revoir, max 48, aucun nucléon tant que rien n'est corrigé) ; électrons allumés au prorata réussis / total ; halo proportionnel à la progression ; jusqu'à 18 orbites (24 quand un module est filtré) pour la fluidité.
- Respecte `prefers-reduced-motion` ; repli SVG si le canevas est indisponible.

### 6.5 À ne pas écrire
- Pas de « 0 leak », « 0 segfault », « Norme 100 % », ni de conformité officielle.
- Pas de numéro de version pour les sujets C++/Python.
- Ne pas présenter Bubblewrap comme une protection contre du code hostile.
- Ne pas écrire que la Norminette est exécutée sur C++/Python.
