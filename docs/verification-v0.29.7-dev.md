# Vérification du candidat v0.29.7-dev

## Résultats en développement

- Suite `python3 tools/test_sans_charge.py` : **342 tests réussis en 162,968 s**. Les quatre témoins actifs de limites connus sont exclus : ce n'est ni un test OOM ni un test de saturation. Les tests compilent et exécutent néanmoins du code de confiance.
- Les quatre exemples récursifs fournis de C05/ex01, ex03, ex04 et ex08 ont réussi depuis la commande installée, en Bubblewrap avec Norminette adaptée ; chacun affichait un cycle possible à titre d'information. Un exemple itératif de confiance pour ex01 a également réussi et affiché l'absence d'indice, sans être bloqué.
- Vérification automatisée de l'analyse textuelle : récursion mutuelle, auxiliaire accessible, fonction non accessible, commentaire, chaîne, macro, source illisible ou trop complexe et exercice sans diagnostic. Ce n'est pas une preuve d'exhaustivité.
- Installation dans un environnement virtuel distinct : `moulinette --version` a affiché `moulinette 0.29.7.dev0` depuis `/tmp` et les quatre PDF sont présents dans le paquet installé. L'installation isolée a utilisé les dépendances de construction de pip.
- Test Chromium local : 109 exercices, thèmes et persistance, couleurs d'état, historique, filtres, humour, mobile et les quatre téléchargements de PDF, sans requête réseau ni erreur JavaScript observée. Les variantes Blanc/Océan des deux guides ont le même texte : 13 pages pour le manuel et 9 pour le guide de style.

## Vérification sur l'Ubuntu utilisateur

La v0.29.6 a déjà été validée sur cet Ubuntu, mais **la v0.29.7 ne l'est pas encore**. À partir de l'archive extraite dans un nouveau dossier, et avec l'environnement virtuel de la Norminette activé :

```bash
source ~/.venvs/moulinette-lab-0283/bin/activate
cd ~/Téléchargements/moulinette-lab-v0.29.7-dev
python3 tools/test_sans_charge.py
python3 -m unittest discover -s tests_real -p 'test_real_cgroup.py' -v
python3 -m pip install --upgrade .
cd /tmp
moulinette --version
moulinette check ~/Téléchargements/moulinette-lab-v0.29.7-dev/exemples/c05/ex08 --exercise c05/ex08 --experimental-cgroup-sandbox --no-history
```

Le dernier exemple est fourni et de confiance. L'option `--no-history` évite d'ajouter un essai à l'historique. La ligne de récursivité est indicative : pour cet exemple un cycle possible doit être signalé, sans être compté comme un test réussi ou échoué. Les quatre tests cgroup réels vérifient des parcours fonctionnels, pas les limites sous charge ; le dernier contrôle teste aussi le passage du nouveau diagnostic dans le mode cgroup.

Si les résultats diffèrent, transmettre les messages affichés. Ne pas exécuter d'anciens témoins OOM ou de saturation. Les modes d'isolation restent expérimentaux et réservés au code de confiance ; les tests ne prouvent ni la sécurité ni la conformité officielle.
