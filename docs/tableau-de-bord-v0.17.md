# Première tranche du tableau de bord local — v0.17

## Périmètre

La commande `python3 -m moulinette dashboard` génère une page HTML autonome à partir d'une base SQLite locale et tente de l'ouvrir dans le navigateur. `--no-open` laisse le fichier sur place sans lancer de navigateur. La page est un instantané : après chaque nouvelle correction, il faut relancer la commande pour la régénérer. Elle ne nécessite pas de connexion réseau.

À partir de cette version, chaque `check` enregistre dans la base : l'identifiant de l'exercice, la date UTC, le nom du dossier de rendu (pas son chemin complet comme étiquette), le mode, le verdict et les diagnostics limités. Les diagnostics d'un compilateur peuvent eux-mêmes contenir des extraits de code ou des chemins. Ils sont personnels ; ne pas partager l'historique sans vérification. `check --no-history` désactive cet enregistrement. Les corrections antérieures ne sont pas automatiquement importées. Un échec d'enregistrement est annoncé sur stderr et ne change pas le verdict, notamment en mode `--json`.

La base `history.sqlite3` et `dashboard.html` sont sous `$XDG_DATA_HOME/moulinette-lab/` si `XDG_DATA_HOME` est absolu, sinon `~/.local/share/moulinette-lab/`. Répertoire créé avec mode 0700 et fichiers nouveaux avec 0600 ; les permissions de dossiers préexistants ne sont pas modifiées. Le contenu n'est pas une frontière de sécurité contre le même utilisateur.

## Lecture des chiffres

- **Progression** : nombre d'exercices dont la dernière tentative est `passed`, sur les neuf exercices C 00 actuellement connus.
- **Score** : `100 × pass / (pass + fail)`, arrondi, avec même poids pour chaque contrôle exécuté ; `info` est exclu. Un échec peut arrêter la correction avant certains contrôles. Aucun score n'est affiché si le verdict est incomplet, si un contrôle est indisponible ou s'il n'y a aucun contrôle comptable. Ce n'est ni une note officielle, ni une mesure comparable entre exercices ayant des contrôles différents.
- **Historique** : 50 tentatives les plus récentes dans la page ; la base conserve aussi les précédentes.

Les valeurs proviennent de l'historique réel, pas de la maquette. Diagnostics et noms sont échappés pour la page. Le bouton d'humour fonctionne sans réseau ; son choix est conservé par le navigateur quand le stockage local est disponible. Le manuel PDF intégré est provisoire et utilise la police DM Sans. Source et licence OFL 1.1 : `moulinette/assets/DM-SANS-OFL.txt` ; polices du projet Google Fonts `dm-fonts`.

## Validation

Les tests automatisés vérifient stockage, limites, états, score, échappement HTML, choix `--no-history`, résultat JSON, panne d'écriture et intégration réelle Bubblewrap/Norminette. La génération et le chargement des ressources ont aussi été testés après installation du paquet wheel. Un essai Chromium local sur une correction réelle a vérifié ouverture des détails, option d'humour persistante, téléchargement PDF, petit écran sans débordement et absence de requête HTTP. Le cgroup réel du moteur v0.17 n'a pas été retesté dans l'environnement assistant, dépourvu de bus systemd utilisateur ; la base moteur est la v0.16 dont le scénario de scope réel a été validé sur l'Ubuntu utilisateur.
