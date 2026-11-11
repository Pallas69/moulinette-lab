# Vérification du candidat v0.29.8-dev

## Développement

- `python3 tools/test_sans_charge.py` : **345 tests réussis en 178,327 s**, aucun skip affiché ; les quatre témoins actifs de limites connus sont exclus. Les tests exécutent du code de confiance, sans OOM ni saturation.
- Trois tests ciblés vérifient les cinq exemples de référence, trois variantes erronées qui passaient les anciens cas fonctionnels et une variante de `ft_any` qui continue après avoir trouvé une correspondance.
- Installation isolée : la commande installée affiche `moulinette 0.29.8.dev0` depuis `/tmp` ; les quatre PDF sont présents. L'exemple C11/ex05 a réussi avec Bubblewrap et les cinq nouveaux cas `do-op`.
- Le test Chromium local couvre notamment les thèmes, états, 109 exercices, historique et quatre téléchargements de guides ; les variantes Blanc/Océan ont un texte identique, 13 pages pour le manuel et 9 pour le guide de style.

## Ubuntu utilisateur — à effectuer

La v0.29.7 a été validée sur cet Ubuntu ; cela ne valide pas automatiquement ce candidat. Après extraction de l'archive dans `~/Téléchargements/workspace_moulinette_arena/` :

```bash
source ~/.venvs/moulinette-lab-0283/bin/activate
cd ~/Téléchargements/workspace_moulinette_arena/moulinette-lab-v0.29.8-dev
python3 -m unittest discover -s tests -p 'test_c11_perfectionnement_light.py' -v
python3 -m pip install --upgrade .
cd /tmp
moulinette --version
moulinette check ~/Téléchargements/workspace_moulinette_arena/moulinette-lab-v0.29.8-dev/exemples/c11/ex05 --exercise c11/ex05 --experimental-cgroup-sandbox --no-history
```

Le dernier essai utilise uniquement l'exemple fourni de confiance, sans ajout dans l'historique. En cas de skip, d'échec ou de résultat incomplet, conserver les messages. Pour refaire toute la sélection sans charge, depuis la racine des sources : `python3 tools/test_sans_charge.py`. Ces vérifications ne constituent ni un audit de sécurité ni une évaluation officielle ; les limites sous charge restent non vérifiées.
