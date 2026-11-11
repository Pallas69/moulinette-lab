# Finitions ciblées — v0.29.7-dev

## Version et diagnostics

`moulinette --version` affiche la version de la commande exécutée ; `command -v moulinette` permet de voir son chemin. Les explications du tableau de bord, indicatives et basées uniquement sur les messages de compilation enregistrés, reconnaissent également certains messages GCC de paramètre inutilisé, fonction implicitement déclarée et point-virgule attendu. Elles ne couvrent pas tous les compilateurs ou diagnostics et ne lisent pas le fichier actuel.

## Récursivité indicative

Le sujet C05 v7 demande la récursivité pour ex01, ex03, ex04 et ex08. Conformément au choix de l'utilisateur, le Lab affiche une information non bloquante pour ces quatre exercices si leur source compile. L'analyse retire commentaires, chaînes et directives préprocesseur, reconnaît certaines définitions locales et suit les appels textuels accessibles depuis la fonction attendue. Elle peut repérer un cycle direct ou indirect, y compris `ft_ten_queens_puzzle` vers un auxiliaire qui s'appelle lui-même. Le diagnostic est enregistré dans l'historique et affiché au tableau de bord comme information.

**Ce n'est pas une preuve.** Une macro ou un pointeur de fonction peut masquer un appel ; une branche conditionnelle, du code mort, une déclaration complexe ou un nom ambigu peuvent simuler un cycle. Une définition non reconnue ou une source illisible est signalée comme indéterminée. L'absence ou la présence d'un indice ne change jamais le statut, ni le score. Une vérification humaine reste nécessaire. L'itération des exercices correspondants et le tableau de fonctions de do-op ne sont pas établis.

## Sécurité et portée

Les protections et leurs limites de la v0.29.5 sont conservées : code de confiance uniquement, pas d'OOM ni de saturation dans les tests légers. La validité fonctionnelle est limitée aux cas testés et non officielle. Les corrections, l'interface, l'historique et les deux guides Blanc/Océan restent séparés et disponibles hors ligne. La v0.29.7 reste à valider sur l'Ubuntu utilisateur ; la validation v0.29.6 ne la valide pas automatiquement.
