# Demande de revue indépendante — v0.21-dev

Examiner l'archive précise v0.21-dev et indiquer d'abord son empreinte SHA-256. Ne pas exécuter de témoin OOM ; la v0.21 le désactive. Ne pas affirmer une protection contre le code hostile.

Vérifier dans le code et les tests, avec chemins et lignes :
1. Désactivation complète des anciens témoins de charge, y compris si `ML_TEST_CGROUP_LOAD=1` ; absence de nouvelles allocations OOM intentionnelles. Confirmer que la limite mémoire en charge n'est pas présentée comme testée.
2. Chemin CLI GitHub, montage sélectif des modules, partage réseau, tmpfs, limites CPU imbriquées, passation des paramètres, absence de repli, validation des réponses et données conservées hors tmpfs.
3. Traitement de `KeyboardInterrupt` et de l'échec de nettoyage ; arrêt du scope dans les chemins d'échec et impossibilité de confirmer son état si son chemin n'est pas connu. Descendants détachés et signaux brutaux.
4. Base SQLite et dashboard : liens symboliques et liens physiques statiques, éléments préexistants, fenêtres TOCTOU, permissions, nettoyage des temporaires. Ne pas supposer qu'un `os.replace` suit le lien de destination.
5. Validation des contrôles obligatoires et doublons, tout en conservant les avertissements légitimes répétés ; limites contre un adversaire de même UID.
6. Cas d'erreur et interruptions pendant les étapes de compilation Bubblewrap, notamment fichiers temporaires laissés si l'arrêt est brutal.

Pour chaque constat, distinguer : reproduit / raisonnement plausible / simple hypothèse ; indiquer prérequis, impact, test non dangereux et correction proposée. Signaler les points réellement ouverts, les éventuelles régressions fonctionnelles et les descriptions d'une autre version. Pas de modification, de test de charge, d'installation ni de suppression de fichiers utilisateur sans autorisation explicite.
