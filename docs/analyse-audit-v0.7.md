# Analyse de l'audit Antigravity v0.7

La v0.7 a passé 51 tests sans tests ignorés sur l'Ubuntu de l'utilisateur et corrigé l'exemple avec Norminette 3.3.59. Cet état n'établit ni une sécurité générale, ni une conformité officielle. Les constats ci-dessous sont confrontés au code plutôt qu'adoptés sans vérification.

## Corrigé ou réduit en v0.8

- **Sortie prématurée du programme (C-07)** : le code 73 seul ne démontre pas le retour au harnais. Un marqueur aléatoire de 16 octets est ajouté après le retour de la fonction et vérifié en plus des octets attendus ; un exemple `_exit(73)` est détecté. Le code utilisateur et le harnais partagent un processus : un adversaire peut chercher à observer ou reproduire ce marqueur. Ce n'est pas une preuve de sécurité ni un moyen de résister à un code hostile.
- **Montage `/proc` en exécution (C-09)** : supprimé à l'étape `test-ex00` ; `/dev` est toujours disponible. Une sonde contrôlée vérifie l'absence de `/proc/self/stat`. Cela ne corrige pas les risques du noyau ou l'exposition de `/proc` aux autres étapes.
- **Norminette (C-03)** : les deux seuls appels internes admis sont `--version` et `-f json --no-colors ft_putchar.c`. Le venv entier reste monté en lecture seule ; il doit être dédié et ne contenir aucun secret. Son contenu, les liens internes et une installation compromise ne sont pas sécurisés par cette validation. Réduire les montages et les limites nécessite une étude de compatibilité, notamment pipx et Python.
- **Inode de sortie (C-04)** : l'identité `(st_dev, st_ino)` du fichier créé est comparée à celle de la sortie après une commande réussie ; une substitution simulée est détectée. Le fichier peut encore être modifié ou remplacé plus tard par un autre processus ayant les mêmes droits. `RLIMIT_FSIZE` est par fichier et par processus, pas un quota d'ensemble. Le répertoire temporaire est supprimé en fin de correction ; un fichier vide peut subsister pendant l'étape en échec.
- **Dossier de rendu et fichiers supplémentaires (C-06)** : la vérification préalable `path.is_dir()` a été supprimée ; l'ouverture du dossier final utilise `O_DIRECTORY | O_NOFOLLOW`. Les fichiers supplémentaires arrêtent désormais la correction avant compilation. Les métadonnées du fichier sont comparées avant/après la lecture pour détecter certaines modifications, sans garantir un instantané atomique. Les chemins parents restent susceptibles d'être des liens symboliques ou de changer.
- **Diagnostic lib64 (C-08)** : `/lib64` n'est créé par doctor et selftest que si `/usr/lib64` existe, comme dans le correcteur. ARM64 n'a pas été testé. Les sondes restent séparées et ne reproduisent pas tous les montages du correcteur.

## Constats à nuancer

### C-01 — délai et `child-pid`

Un délai du programme de test est actuellement déclaré indisponible (`incomplete`, code 2) en mode expérimental : l'utilisateur ne sait pas si c'est une boucle de son code ou un problème de démarrage. Cela existe aussi en v0.6 : ce n'est donc pas une régression introduite en v0.7. L'ambiguïté constitue bien une limite fonctionnelle ; la v0.8 indique l'étape concernée mais ne la résout pas.

La seule présence de `child-pid` ne suffit pas à conclure que le programme a commencé à s'exécuter. Dans la source Bubblewrap 0.11.1, l'événement est écrit avant que le parent ne laisse le processus enfant poursuivre son démarrage : https://github.com/containers/bubblewrap/blob/v0.11.1/bubblewrap.c#L3198-L3213. Nous conservons donc le classement prudent au lieu de transformer automatiquement le timeout en faute de l'étudiant. Une preuve distincte et testée de démarrage effectif serait nécessaire pour distinguer les cas.

### C-02 — JSON mal formé

Dans la v0.7, `json.loads` est déjà dans un `try` qui intercepte `ValueError` ; `json.JSONDecodeError` en est une sous-classe. Le test `test_malformed_and_inconsistent_status_cannot_pass` couvre un JSON mal formé et exige `SandboxUnavailable`. Le crash affirmé dans l'audit n'est donc pas reproduit par ce scénario.

### C-07 — signal et symboles

Bubblewrap peut retourner une valeur comme 139 pour un signal, mais un programme peut aussi choisir explicitement ce code ; il ne faut pas présenter automatiquement la valeur comme preuve d'un signal. L'analyse `nm -u` est volontairement partielle, et un marqueur de harnais n'empêche pas les contournements d'un code hostile. Avant d'interdire des symboles définis, vérifier précisément les règles applicables au sujet et les symboles introduits par le compilateur pour éviter les faux positifs.

## Points encore ouverts

Absence de cgroups (`pids.max`, limites mémoire et CPU globales), de seccomp et d'audit de résistance à du code hostile ; noyau partagé ; descendants en mode local ; courses et altérations par le même UID ; venv Norminette monté entier ; sous-ensemble des règles seulement vérifié ; sondes non alignées sur tous les montages ; compatibilité d'autres linkers et architectures ; différenciation certaine des délais. La suggestion d'un filtre seccomp interdisant `execve` dès le démarrage n'est pas appliquée : sans architecture adaptée, elle empêcherait aussi le lancement initial du binaire. Un scope `systemd --user` exige une délégation et des contrôles effectifs qui ne sont pas garantis partout.

**Les deux modes restent réservés au code de confiance.** La v0.8 n'a pas été validée sur l'Ubuntu de l'utilisateur à ce stade.
