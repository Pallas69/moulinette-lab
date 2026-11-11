# Fiche de travail — 42 C Piscine C 00, exercice 00

**Source :** PDF fourni par l'utilisateur, « C Piscine C 00 », version 8, page imprimée 7 (8e page du PDF). Cette fiche est un résumé de travail, pas une conversion complète du document.

- Exercice : `ft_putchar` ; dossier de rendu : `ex00/`.
- Fichier attendu : `ft_putchar.c`.
- Fonction autorisée : `write`.
- Prototype : `void ft_putchar(char c);`.
- Comportement : afficher le caractère reçu ; le sujet donne l'exemple `write(1, &c, 1);`.
- Compilation générale du sujet : `cc -Wall -Wextra -Werror`.
- Adaptation autodidacte : en-tête institutionnel non exigé ; Norminette 3.3.59 est prise en charge en filtrant uniquement le diagnostic INVALID_HEADER.

Le prototype teste des octets représentatifs et 256 octets successifs sur les plateformes à octets de 8 bits, mais ne reproduit pas les tests privés de 42. La vérification des fonctions externes par symboles n'est pas exhaustive.
