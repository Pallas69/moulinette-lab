# Validation — v0.32.8-dev

## Mise en page

La zone d'apprentissage est alignée en haut de la grille et les marges hautes sont réduites ; la zone de la carte et de l'atome est moins haute. Une marge basse est conservée pour ne pas faire chevaucher l'atome et les cartes de statistiques. La carte reste centrée sur l'atome. Aucun changement de logique des électrons, de l'humour, de l'historique ou des correcteurs.

Avec un historique fictif vide et le même environnement Chromium, l'espace entre le bas des documents PDF et le haut de « Votre espace d'apprentissage » est passé de 167,5 à 43 px à 1440 px de large, et de 68 à 43 px à 390 px. Les mesures varient selon les polices et le navigateur. Un espacement raisonnable est conservé, il n'est pas strictement nul.

Tests navigateur `tools/test_espace_v0328_browser.py` : largeurs 1440, 1100, 390 et 320 px, avec et sans JavaScript sur mobile ; espacement, centrage de l'atome, absence de chevauchement de ses limites avec les statistiques, quatre liens PDF et phrase plus longue vérifiés. Aux largeurs 1100 et 320 px, de légers débordements horizontaux préexistants ont été observés dans la barre de navigation et le SVG respectivement, identiques à la v0.32.7 ; ils ne sont pas corrigés dans cette modification ciblée. Les essais de l'atome, de l'humour, du reset factice et du tableau de bord (dont téléchargements sans JavaScript) ont également réussi. Le test général du tableau de bord a d'abord subi un arrêt de l'onglet Chromium, puis réussi lors d'une relance distincte ; la cause exacte n'a pas été établie. Lecture des quatre guides PDF et comparaison de leurs variantes réussies.

Suite sans charge : 392 tests exécutés, dont 70 ignorés, aucun échec ; six témoins actifs restent exclus. Aucun test OOM ni de saturation. Les essais n'établissent pas de nouvelle validation de sécurité : voir `securite-v0.32.7-dev.md` ; code de confiance uniquement. Les tests ne remplacent pas une vérification sur l'Ubuntu utilisateur.
