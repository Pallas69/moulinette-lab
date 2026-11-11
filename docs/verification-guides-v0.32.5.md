# Vérification des guides — v0.32.5-dev

Les anciens audits v0.31 et v0.32.4 décrivent les PDF historiques v0.29.8 ; ils ne décrivent pas ces nouvelles versions. Les sources éditables sont `docs/manuel-utilisateur.md` et `docs/guide-style-c.md`. `tools/generer_guides_themes.py` produit les variantes Blanc et Océan, leurs copies dans `moulinette/assets/` et les copies Océan par défaut.

Le manuel couvre les commandes et options exposées par la CLI, les piscines, le tableau de bord, l'humour, l'atome et les limites de sécurité. Il avertit que `dashboard --db` ne garantit pas l'isolation, que les tests C++/Python sont partiels et que la prise en charge de `--sanitize` pour ces moteurs n'est pas établie. Le guide de style C reste distinct et conserve sa référence de Norminette 3.3.59. Ces documents ne garantissent pas la conformité officielle.

Les quatre PDF sont accessibles par téléchargement direct depuis les boutons de la page, y compris si JavaScript est désactivé. Les graphismes et les polices sont intégrés ; les licences des polices sont conservées. Vérifications ciblées à effectuer : intégrité et noms des quatre téléchargements, lecture PDF, égalité textuelle entre thèmes, version, choix des polices, rendu et absence de constellation dans la page. Aucun test de saturation ou témoin OOM n'est requis.
