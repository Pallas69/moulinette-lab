# GitHub public de confiance — première tranche v0.18

## Périmètre et utilisation

La commande `check` accepte une URL `https://github.com/proprietaire/depot` (suffixe `.git` facultatif). La récupération n'est tentée qu'après confirmation par `--trust-github` et choix explicite d'un mode de correction. Exemple :

```bash
python3 -m moulinette check https://github.com/PROPRIETAIRE/DEPOT \
  --exercise c00/ex00 --trust-github --experimental-cgroup-sandbox \
  --ref main --subdir c00/ex00
```

N'utilisez cette commande que pour un dépôt public que vous avez vérifié et auquel vous faites confiance. `--ref` accepte une branche, un tag ou un SHA complet de 40 caractères, pas un SHA abrégé ; `HEAD` ou son absence choisit la branche par défaut. Les noms de références contenant des caractères spéciaux non pris en charge sont refusés. `--subdir` doit être relatif et ne pas traverser de lien symbolique, de `..` ou de `.git`. Le répertoire sélectionné suit les mêmes règles que le rendu local. Les dépôts privés, SSH, LFS et sous-modules ne sont pas pris en charge.

Le rapport JSON ajoute `source` avec URL canonique, référence demandée, commit réellement évalué et sous-dossier. Un résumé comportant le dépôt et le SHA complet est conservé dans l'historique, sous réserve de `--no-history` ; le sous-dossier est tronqué si l'étiquette dépasse 255 caractères. Le format des corrections locales et le schéma SQLite v0.17 restent utilisables. Les corrections de la v0.17 déjà enregistrées restent présentes dans l'historique.

## Fonctionnement et limites

Git est lancé en argument vectoriel, sans shell, et ne reçoit pas la configuration Git globale, les credentials ou les variables de proxy utilisateur. Seul le protocole HTTPS est autorisé, les redirections sont refusées, l'interaction désactivée, les hooks désactivés et les sous-modules non initialisés. Pour chaque commande Git : délai de 45 secondes, CPU 45 secondes, mémoire virtuelle 1 Gio et taille maximale par fichier 64 Mio. Ces limites sont partielles : elles ne bornent pas l'espace total, ni tous les descendants dans toutes les circonstances ; une interruption brutale peut laisser des fichiers temporaires. L'exécution et le réseau de Git se déroulent sur l'hôte avant l'isolation expérimentale du moteur, avec les droits de l'utilisateur. Le système et Git restent exposés aux données téléchargées. Ne pas utiliser pour un dépôt ou du code hostile ; le filtrage d'URL n'est pas une sandbox ni une preuve de sécurité. Git doit être dans `/usr`, les proxies et redirections ne sont pas pris en charge.

Un répertoire temporaire privé est créé et normalement supprimé après correction ou erreur. Le rendu préparé comprend une copie bornée du fichier attendu et des entrées témoins pour les autres noms, pour que le correcteur détecte les fichiers supplémentaires ; leurs contenus ne sont pas copiés. Le dossier Git interne racine `.git` est exclu de cet inventaire. Les liens source restent refusés. Une erreur Git ou de chemin rend le résultat incomplet sans lancer le correcteur, ni basculer vers une autre méthode. Cette méthode n'est pas un instantané atomique face à un processus malveillant utilisant le même compte.

## Vérifications réalisées

- Dix-neuf tests unitaires/intégration déterministes pour validation d'URL et chemins, référence, métadonnées, nettoyage, refus sans accord, erreurs, sous-dossier, liens, fichiers supplémentaires, taille, JSON, historique, option de confidentialité et dispatch cgroup simulé.
- Accès réseau réel distinct à `Tednoob17/mini-moulinette` : HEAD, branche `main` et commit `c0debfed043857ffc6c2629c897f59bec4bf9c4a`, puis correction du fichier de test dans `mini-moul/tests/C00/ex00`. La compilation échoue comme attendu car ce fichier est un harnais référençant un rendu extérieur, non un rendu autonome.
- Autre vérification réseau de bout en bout, sur `ChuOkupai/piscine42`, commit `cc5e12c0776839a33ef12658192a0f46abdcf095`, sous-dossier `c00/ex00` : source préalablement lue et comparée octet par octet au fichier téléchargé avant correction ; compilation, tests ex00 et Norminette 3.3.59 réussis sous Bubblewrap réel. Cet exemple précis et ces essais ne valident pas tous les dépôts GitHub.
- Suite complète de 187 tests sans skip dans l'environnement de développement : Bubblewrap et Norminette réels ; cgroup simulé. Le cgroup réel de ce nouveau parcours n'a pas été exercé ici faute de bus systemd utilisateur. Étape sécurité non terminée.
