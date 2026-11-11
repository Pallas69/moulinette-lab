# Audit pour mise à jour des documents téléchargeables — v0.32.4-dev

Document destiné à une autre IA ou à une personne chargée des PDF. Cette version **ne modifie ni ne régénère les PDF** : elle contient les mêmes documents embarqués que la v0.31 reçue. Les textes et les noms sont encore ceux de la v0.29.8. Ne pas annoncer que les PDF décrivent déjà la v0.32.

## Inventaire vérifié

Le tableau de bord embarque les PDF hors ligne en data URI. Les quatre boutons déclenchent un téléchargement direct, sans aperçu :

| Document | Variante | Fichier source dans `moulinette/assets/` | Nom de téléchargement actuel | SHA-256 |
|---|---|---|---|---|
| Manuel | Blanc | `guide-utilisation-blanc.pdf` | `manuel-moulinette-lab-v0.29.8-blanc.pdf` | `2f24b82ace56848eabd07ee46f6bd12061f76974c80a2600a02152e52610ae71` |
| Manuel | Océan | `guide-utilisation-ocean.pdf` | `manuel-moulinette-lab-v0.29.8-ocean.pdf` | `b06350104b60a7ef62b5234f1556ac018f217a953ed9d05c3f134aaced0a6b63` |
| Style C | Blanc | `guide-style-c-blanc.pdf` | `guide-style-c-moulinette-lab-v0.29.8-blanc.pdf` | `bedd74f9611dffb1645ed75f02389b4b3b746d1ccbba1c6e81447cb87492ea2b` |
| Style C | Océan | `guide-style-c-ocean.pdf` | `guide-style-c-moulinette-lab-v0.29.8-ocean.pdf` | `37619e475e887d40d7e979937b4210492dcabdf649b241994a8c570102df1a28` |

Les copies `guide-utilisation.pdf` et `guide-style-c.pdf` correspondent aux variantes Océan. `moulinette/dashboard.py` construit les quatre liens et code la version de téléchargement en dur. `docs/manuel-utilisateur.md` et `docs/guide-style-c.md` sont les sources éditables ; `tools/generer_guides_themes.py` est l'orchestrateur, qui code également v0.29.8 en dur. L'ancien audit `docs/audit-documents-telechargeables-v0.31.md` reste utile, mais ses affirmations doivent être revérifiées ; la présente note prévaut pour la v0.32.4.

## Changements à documenter

1. **Installation et utilisation** : expliquer clairement le projet, l'installation dans un nouveau dossier, toutes les commandes et leurs options réellement prises en charge, les prérequis, les résultats et les limites. Tenir compte du chemin de travail utilisateur `~/Téléchargements/workspace_moulinette_arena/`. Ne pas indiquer qu'un fichier individuel sera forcément autodétecté : les noms ou chemins peuvent être ambigus et nécessiter `-e` ou `--exercise`.
2. **Commandes simplifiées déjà présentes en v0.31 et conservées en v0.32** : `moulinette` (tableau de bord), `moulinette CHEMIN` (équivalent de `moulinette check CHEMIN`), `-e`, `-m`, `-a`, `-s`, `-l`, `--cgroup`, `-w`, `-j`, `moulinette ui`, `moulinette list --piscine c|cpp|py|all`. Conserver les options longues. Sans mode explicite, Bubblewrap est choisi s'il est présent ; sinon la correction est refusée. `-l` est un mode local non isolé. L'option cgroup ne prend en charge que C.
3. **Piscines** : catalogue de 109 C, 45 C++ et 36 Python ; progression C → C++ → Python ; une seule carte de progression pour la piscine consultée ; dernier résultat par exercice ; déblocage permanent ; verrouillage limité à l'interface, corrections CLI anticipées conservées. Tests locaux non officiels, non exhaustifs, code de confiance uniquement. Ne pas inventer la version des sujets C++/Python ni promettre une conformité officielle.
4. **Atome et interface v0.32.4** : une orbite par électron en perspective 3D autour d’un noyau unique, derrière la carte de progression. Un électron bleu pour chaque exercice réussi au dernier essai, un rouge pour chaque exercice à revoir ; incomplets et non corrigés exclus. Zéro résultat admissible signifie zéro orbite. Périmètre : piscine consultée ou module choisi ; recherche sans effet sur le périmètre. Vitesses x1,5 par rapport à la v0.32.2 ; superposition et masquage par la carte possibles. Interrupteur d’humour à préférence locale et changement automatique toutes les 30 secondes lorsque l’onglet est visible et l’humour actif ; bouton manuel conservé. Constellation décorative du Capricorne en haut à gauche, étoiles et liens schématiques ; aucune lecture de notes personnelles ni requête. Mouvement réduit : image fixe. Après correction directe en mode live, la page se recharge ; une page statique ouverte peut nécessiter un rechargement.
5. **Guides** : mettre à jour la version et les noms de téléchargement ainsi que les en-têtes et noms générés. Conserver deux guides distincts, chaque guide en Blanc et Océan, téléchargement direct sans aperçu, Liberation Serif pour le texte et JetBrains Mono pour le code, arcs et motifs sur toutes les pages et filigranes `</>`, `$`, `&`, `#`, `*`. Conserver les licences des polices.
6. **Précisions de sécurité et limites** : aucune garantie contre du code hostile. Les moteurs C++/Python utilisent des contrôles distincts, ce n'est pas la Norminette C ; la prise en charge de `--sanitize` pour ces moteurs n'est pas établie. `dashboard --db` et `--live --db` ne garantissent **pas** l'isolation de l'historique : l'état des déblocages et la page live peuvent utiliser la base par défaut. Ne pas recommander cette option comme moyen de protéger la base réelle tant que le défaut n'est pas corrigé et testé.

## Vérifications à réaliser après correction documentaire

- Comparer la source et le PDF : version, commandes réellement présentes, chemin utilisateur, prérequis et avertissements ; vérifier les deux variantes et l'équivalence textuelle par document.
- Vérifier les quatre téléchargements directs, les noms, l'intégrité des fichiers et l'accès sans JavaScript, ainsi que les styles, polices, filigranes et pagination.
- Mettre à jour les tests qui attendent actuellement les noms v0.29.8, uniquement après régénération des PDF. Ne pas renommer les fichiers de téléchargement en v0.32 tant que les contenus restent v0.29.8.
- Effectuer uniquement des tests légers et non destructifs, sans OOM ni saturation, avec historique factice séparé. Ne pas présenter des annonces tierces comme des tests reproduits.
