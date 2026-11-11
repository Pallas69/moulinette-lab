"""Commandes du prototype. Exécution locale explicitement non isolée."""
import argparse
import contextlib
import json
import os
import shutil
import stat
import sys
import tempfile
import time
from pathlib import Path
from .checker import check_ex00, check_ex01, check_exercise, MAX_FILE
from . import __version__
from .exercise_catalog import ALL_EXERCISES, canonical_exercise, EXERCISES, piscine_of
from .sandbox_doctor import diagnose
from .sandbox_selftest import selftest
from .cgroup_selftest import cgroup_selftest
from .cgroup_launcher import launch as launch_cgroup, _termination_signals
from .history import HistoryError, store_attempt, reset_history, data_directory
from .dashboard import write_dashboard
from .github_source import GitHubSourceError
from .github_bounded import bounded_public_repository as trusted_public_repository


def detect_exercise(path_str):
    """Détecte l'exercice d'un fichier ou dossier local s'il est non ambigu, sinon renvoie (None, raison)."""
    if '://' in path_str or path_str.startswith('git@'):
        return None, "Précisez --exercise pour un dépôt distant."
    target = Path(path_str).expanduser()
    is_single_file = False
    try:
        st = target.lstat()
        if stat.S_ISREG(st.st_mode):
            is_single_file = True
    except OSError:
        if target.suffix in ('.c', '.h', '.cpp', '.hpp', '.py', '.txt', '.sh') or target.name == 'Makefile':
            is_single_file = True
    if is_single_file:
        entries = {target.name}
        folder = target.parent
    else:
        folder = target
        try:
            entries = {e.name for e in os.scandir(folder) if not e.name.startswith('.') and e.is_file(follow_symlinks=False)}
        except OSError:
            entries = set()
    parts = folder.resolve().parts if folder.exists() else folder.parts
    cand_path = None
    if len(parts) >= 3:
        cand_path = canonical_exercise(f"{parts[-3]}/{parts[-2]}/{parts[-1]}")
    if cand_path is None and len(parts) >= 2:
        cand_path = canonical_exercise(f"{parts[-2]}/{parts[-1]}")
    c_matches = sorted(ex for ex, spec in EXERCISES.items() if spec['source'] in entries)
    other_matches = sorted(
        ex for ex, spec in ALL_EXERCISES.items()
        if ex not in EXERCISES
        and spec.get('source') not in ('Makefile', 'main.cpp', 'main.py', 'FileLoader.py', 'whatever.cpp', 'iter.cpp')
        and spec.get('source') in entries
    )
    file_matches = sorted(set(c_matches) | set(other_matches))
    if cand_path is not None:
        if cand_path not in EXERCISES:
            return cand_path, None
        if not c_matches or cand_path in c_matches:
            return cand_path, None
        return None, f"Autodétection ambiguë entre le chemin ({cand_path}) et les fichiers présents ({', '.join(c_matches)}) ; précisez --exercise."
    if len(file_matches) == 1:
        return file_matches[0], None
    if len(file_matches) > 1:
        return None, f"Autodétection ambiguë pour ce dossier (candidats : {', '.join(file_matches)}) ; précisez --exercise."
    return None, "Impossible de détecter l’exercice automatiquement ; précisez --exercise, --module ou --all."


@contextlib.contextmanager
def stage_submission_path(path, ex_id):
    """Si path désigne un fichier régulier, l'isole dans un dossier temporaire avec ses en-têtes compagnons éventuels."""
    target = Path(path).expanduser()
    try:
        st = target.lstat()
    except OSError:
        yield target
        return
    if not stat.S_ISREG(st.st_mode):
        yield target
        return
    spec = ALL_EXERCISES.get(ex_id, {})
    proj = spec.get('project', {})
    expected = {spec.get('source', target.name)} | set(proj.get('files', ())) | set(spec.get('required_files', ()))
    for pair in spec.get('flexible_pairs', ()):
        expected.update(pair)
    with tempfile.TemporaryDirectory(prefix="moulinette-single-") as tmp:
        work = Path(tmp)
        dest_main = work / target.name
        dest_main.parent.mkdir(parents=True, exist_ok=True)
        def copy_bounded(source, destination):
            # Lire depuis le descripteur vérifié, jamais via un lien final.
            fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
            with os.fdopen(fd, 'rb') as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise OSError('Fichier non régulier ou lié plusieurs fois : ' + str(source))
                # Un octet de trop est conservé pour que le correcteur refuse la source.
                destination.write_bytes(handle.read(MAX_FILE + 1))

        copy_bounded(target, dest_main)
        parent = target.parent
        for name in expected:
            if not name or name == target.name:
                continue
            cand = parent / name
            try:
                cst = cand.lstat()
                if stat.S_ISREG(cst.st_mode):
                    dest = work / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    copy_bounded(cand, dest)
            except OSError:
                continue
        yield work


def discover_batch(base_path, module=None):
    """Trouve les sous-dossiers d'exercices présents pour --module ou --all."""
    root = Path(base_path)
    if not root.is_dir():
        return None, f"Dossier introuvable : {base_path}"
    if module is not None:
        mod = module.strip().lower().replace(' ', '')
        if mod in ('c++', 'cpp'):
            candidates = sorted(ex for ex in ALL_EXERCISES if ex.startswith('cpp'))
        elif mod in ('py', 'python'):
            candidates = sorted(ex for ex in ALL_EXERCISES if ex.startswith('py'))
        elif mod == 'c':
            candidates = sorted(EXERCISES)
        else:
            candidates = sorted(ex for ex in ALL_EXERCISES if ex.startswith(mod + '/'))
        if not candidates:
            return None, f"Module inconnu : {module}. Utilisez c00 à c13, cpp00 à cpp08 ou py00 à py04."
        found = []
        for ex in candidates:
            sub = ex.split('/')[1]
            if (root / ex).is_dir():
                found.append((ex, root / ex))
            elif mod not in ('c', 'cpp', 'c++', 'py', 'python') and (root / sub).is_dir():
                found.append((ex, root / sub))
        if not found:
            return None, f"Aucun sous-dossier d’exercice trouvé pour {mod.upper()} dans {base_path}."
        return found, None
    found = [(ex, root / ex) for ex in sorted(ALL_EXERCISES) if (root / ex).is_dir()]
    if not found:
        return None, f"Aucun sous-dossier cXX/exYY, cppXX/exYY ou pyXX/exYY trouvé dans {base_path}."
    return found, None


def _snapshot_mtimes(paths):
    state = {}
    for base in paths:
        try:
            bp = Path(base)
            st_base = bp.lstat()
            if stat.S_ISREG(st_base.st_mode):
                state[str(bp)] = (st_base.st_mtime_ns, st_base.st_size)
                continue
            for root, _, files in os.walk(base, followlinks=False):
                for name in files:
                    if name.startswith('.'):
                        continue
                    p = Path(root) / name
                    try:
                        st = p.lstat()
                        state[str(p)] = (st.st_mtime_ns, st.st_size)
                    except OSError:
                        continue
        except OSError:
            continue
    return state


_SUBCOMMANDS = ("check", "dashboard", "ui", "list", "sandbox", "reset")


def main(argv=None):
    try:
        with _termination_signals():
            return _main(argv)
    except KeyboardInterrupt:
        # En dehors de l'évaluation, une sortie JSON partielle peut déjà exister.
        print('Commande interrompue ; sortie et nettoyage non confirmés.', file=sys.stderr)
        return 2


def _main(argv=None):
    parser = argparse.ArgumentParser(prog="moulinette", description="Prototype de correction pour autodidactes")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Évaluer un dossier local")
    check.add_argument("path", help="Dossier local ou URL d’un dépôt GitHub public de confiance")
    target_grp = check.add_mutually_exclusive_group()
    target_grp.add_argument("-e", "--exercise", help="Identifiant, par exemple c00/ex00, cpp00/ex00 ou py00/ex00 (autodétecté si omis et sans ambiguïté)")
    target_grp.add_argument("-m", "--module", help="Évaluer tous les exercices présents d’un module (c00..c13, cpp00..cpp08, py00..py04)")
    target_grp.add_argument("-a", "--all", action="store_true", help="Évaluer tous les exercices cXX/exYY, cppXX/exYY et pyXX/exYY présents dans le dossier")
    modes = check.add_mutually_exclusive_group()
    modes.add_argument("-l", "--local", "--unsafe-local", dest="unsafe_local", action="store_true", help="Exécution locale NON isolée, code de confiance uniquement (alias historique : --unsafe-local)")
    modes.add_argument("-s", "--sandbox", "--experimental-sandbox", dest="experimental_sandbox", action="store_true", help="Bubblewrap expérimental, code de confiance uniquement (mode par défaut si bwrap est installé ; alias historique : --experimental-sandbox)")
    modes.add_argument("--cgroup", "--experimental-cgroup-sandbox", dest="experimental_cgroup_sandbox", action="store_true", help="Bubblewrap et cgroup expérimentaux, exercices C uniquement (alias historique : --experimental-cgroup-sandbox)")
    check.add_argument("--sanitize", action="store_true", help="Exécuter une passe sanitizer optionnelle (ASan/UBSan en local, UBSan trap en sandbox)")
    check.add_argument("-j", "--jobs", type=int, default=1, help="Nombre de travailleurs parallèles pour --module / --all (1 à 8, défaut : 1)")
    check.add_argument("-w", "--watch", action="store_true", help="Relancer séquentiellement la correction à chaque modification de fichier")
    check.add_argument("--watch-interval", type=float, default=0.5, help="Intervalle de scrutation en secondes pour --watch (défaut : 0.5)")
    check.add_argument("--max-iterations", type=int, default=0, help=argparse.SUPPRESS)
    check.add_argument("--json", action="store_true", help="Afficher un rapport JSON")
    check.add_argument("--no-history", action="store_true", help="Ne pas enregistrer cette correction dans l’historique local")
    check.add_argument("--trust-github", action="store_true", help="Confirmer que le dépôt GitHub public est de confiance (Git utilise le réseau sur l’hôte)")
    check.add_argument("--ref", help="Branche, tag ou SHA complet du dépôt GitHub (défaut : HEAD)")
    check.add_argument("--subdir", help="Sous-dossier relatif du dépôt contenant le rendu")
    dashboard = sub.add_parser("dashboard", aliases=["ui"], help="Générer et ouvrir le tableau de bord local (alias : ui)")
    dashboard.add_argument("--no-open", action="store_true", help="Générer la page sans lancer le navigateur")
    dashboard.add_argument("--open", action="store_true", help="Forcer l'ouverture dans le navigateur")
    dashboard.add_argument("--live", action="store_true", help="Lancer le serveur local temps réel (127.0.0.1 uniquement)")
    dashboard.add_argument("--port", type=int, default=0, help="Port local pour --live (0 = automatique)")
    dashboard.add_argument("--db", help="Chemin vers une base SQLite d'historique spécifique")
    dashboard.add_argument("--output", help="Chemin du fichier HTML de sortie")
    list_cmd = sub.add_parser("list", help="Lister les exercices disponibles par piscine")
    list_cmd.add_argument("--piscine", choices=["c", "cpp", "py", "all"], default="all", help="Filtrer par piscine (c, cpp, py, all)")
    reset = sub.add_parser("reset", help="Sauvegarder puis effacer corrections et déblocages après confirmation")
    reset.add_argument("--db", help="Base SQLite ciblée (défaut : historique local)")
    reset.add_argument("--yes", action="store_true", help="Confirmer explicitement le reset sans question interactive")
    sandbox = sub.add_parser("sandbox", help="Diagnostiquer les prérequis de l’isolation future")
    sand_sub = sandbox.add_subparsers(dest="sandbox_command", required=True)
    doctor = sand_sub.add_parser("doctor", help="Lancer une sonde locale sans code étudiant")
    doctor.add_argument("--json", action="store_true", help="Afficher le rapport JSON")
    experiment = sand_sub.add_parser("selftest", help="Compiler et exécuter un témoin fixe dans Bubblewrap")
    experiment.add_argument("--json", action="store_true", help="Afficher le rapport JSON")
    cgroup_probe = sand_sub.add_parser("cgroup-selftest", help="Tester un scope cgroup avec des témoins limités")
    cgroup_probe.add_argument("--json", action="store_true", help="Afficher le rapport JSON")
    argv = list(sys.argv[1:] if argv is None else argv)
    # Raccourcis : « moulinette » seul ouvre le tableau de bord, et
    # « moulinette <chemin> [options] » équivaut à « moulinette check <chemin> [options] ».
    if not argv:
        argv = ["dashboard"]
    elif argv[0] not in _SUBCOMMANDS and not argv[0].startswith("-"):
        argv = ["check"] + argv
    args = parser.parse_args(argv)
    if args.command == "ui":
        args.command = "dashboard"
    if args.command == "reset":
        target = Path(args.db).expanduser().absolute() if args.db else data_directory() / 'history.sqlite3'
        print("Arrêtez toute correction et tout serveur live avant le reset.")
        print(f"Base ciblée : {target}")
        print("Cette opération efface les corrections ET les déblocages de cette base ; une sauvegarde sera créée.")
        if not args.yes:
            try:
                answer = input("Tapez RESET pour confirmer : ")
            except EOFError:
                answer = ''
            if answer != 'RESET':
                print("Réinitialisation annulée ; aucune donnée supprimée.")
                return 2
        try:
            backup = reset_history(db_path=args.db)
        except (HistoryError, OSError, ValueError) as exc:
            print(f"Réinitialisation impossible : {exc}", file=sys.stderr)
            return 2
        print(f"Réinitialisation effectuée. Sauvegarde : {backup}")
        print("Régénérez le tableau de bord pour voir le résultat.")
        return 0
    if args.command == "sandbox":
        report = {"doctor": diagnose, "selftest": selftest, "cgroup-selftest": cgroup_selftest}[args.sandbox_command]()
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print("Moulinette Lab — " + {"doctor": "diagnostic Bubblewrap", "selftest": "témoins Bubblewrap", "cgroup-selftest": "témoins cgroup"}[args.sandbox_command] + "\n")
            symbols = {"pass": "✓", "fail": "✗", "unavailable": "—"}
            for item in report["checks"]:
                print(f"{symbols[item['status']]} {item['name']}: {item['message']}")
            print("\nINCOMPLET : ces sondes ne valident pas la sécurité du correcteur pour du code non fiable.")
        return 1 if any(x["status"] == "fail" for x in report["checks"]) else 2
    if args.command == "list":
        from .exercise_catalog import EXERCISES, CPP_EXERCISES, PY_EXERCISES
        groups = []
        if args.piscine in ("c", "all"):
            groups.append(("1. Piscine C", EXERCISES))
        if args.piscine in ("cpp", "all"):
            groups.append(("2. Piscine C++", CPP_EXERCISES))
        if args.piscine in ("py", "all"):
            groups.append(("3. Piscine Python", PY_EXERCISES))
        for title, items in groups:
            print(f"=== {title} ({len(items)} exercices) ===")
            for ex_id, meta in items.items():
                files = meta.get('required_files') or ([meta['source']] if isinstance(meta.get('source'), str) else meta.get('source') or ())
                label = meta.get('title') or ''
                print(f"  {ex_id:<12} {', '.join(files):<38} {label}".rstrip())
        return 0
    if args.command == "dashboard":
        if args.live:
            from .live import serve
            try:
                return serve(port=args.port, open_browser=not args.no_open, db_path=args.db, output_path=args.output)
            except (HistoryError, OSError, ValueError) as exc:
                print(f"Tableau de bord en direct indisponible : {exc}", file=sys.stderr)
                return 2
        if 'unittest' not in sys.modules and not args.db and not args.output:
            try:
                from .live import ensure_live_daemon
                ensure_live_daemon()
            except Exception:
                pass
        try:
            page = write_dashboard(output_path=args.output, db_path=args.db)
        except (HistoryError, OSError, ValueError) as exc:
            print(f"Tableau de bord indisponible : {exc}", file=sys.stderr)
            return 2
        print(f"Tableau de bord local : {page}")
        if not args.no_open:
            import webbrowser
            try:
                if not webbrowser.open(page.as_uri(), new=2):
                    print("Navigateur non ouvert automatiquement ; ouvrez le fichier indiqué.", file=sys.stderr)
            except (OSError, webbrowser.Error) as exc:
                print(f"Navigateur non ouvert automatiquement : {exc}. Ouvrez le fichier indiqué.", file=sys.stderr)
        return 0
    if not (args.unsafe_local or args.experimental_sandbox or args.experimental_cgroup_sandbox):
        # Le mode local non isolé n'est jamais choisi implicitement : sans option,
        # Bubblewrap est utilisé s'il est installé, sinon la correction est refusée.
        if shutil.which("bwrap"):
            args.experimental_sandbox = True
            if not args.json:
                print("Mode par défaut : Bubblewrap expérimental (-l pour le mode local non isolé).", file=sys.stderr)
        else:
            print("Arrêt : Bubblewrap (bwrap) est introuvable et le mode local non isolé n'est jamais activé par défaut. "
                  "Ajoutez -l (--local) pour du code de confiance uniquement. Ce prototype n'est pas sécurisé contre du code malveillant.", file=sys.stderr)
            return 2
    remote = '://' in args.path or args.path.startswith('git@')
    if remote and not args.trust_github:
        print("Arrêt : pour récupérer un dépôt GitHub public de confiance, ajoutez --trust-github. Git utilisera le réseau sur l’hôte ; l’isolation reste incomplète.", file=sys.stderr)
        return 2
    if not remote and (args.trust_github or args.ref is not None or args.subdir is not None):
        print("--trust-github, --ref et --subdir sont réservés aux dépôts GitHub.", file=sys.stderr)
        return 2
    if remote and (args.module or args.all or args.watch):
        print("--module, --all et --watch portent uniquement sur un dossier local.", file=sys.stderr)
        return 2

    def _evaluate_single(path, ex_id):
        with stage_submission_path(path, ex_id) as staged:
            if args.experimental_cgroup_sandbox:
                pisc = piscine_of(ex_id) or 'c'
                spec_obj = ALL_EXERCISES.get(ex_id, {})
                if pisc != 'c':
                    return {
                        'exercise': f'42/{pisc}/{ex_id}',
                        'subject_version': spec_obj.get('subject_version', '1.0'),
                        'profile': '42-autodidacte',
                        'isolation': 'Bubblewrap et cgroup expérimentaux — code de confiance uniquement',
                        'checks': [{'name': 'Cgroup expérimental', 'status': 'unavailable',
                                    'message': 'Le mode --experimental-cgroup-sandbox est réservé aux exercices C ; utilisez --experimental-sandbox ou --unsafe-local pour C++ et Python.'}],
                        'result': 'incomplete',
                    }
                result, error = launch_cgroup(str(staged), ex_id)
                if error:
                    result = {'exercise': '42/c/' + ex_id, 'subject_version': spec_obj.get('subject_version','8'), 'profile': '42-autodidacte',
                              'isolation': 'Bubblewrap et cgroup expérimentaux — code de confiance uniquement',
                              'checks': [{'name': 'Cgroup expérimental', 'status': 'unavailable', 'message': error}],
                              'result': 'incomplete'}
                return result
            kw = {'sanitize': True} if args.sanitize else {}
            if ex_id == 'c00/ex00':
                return check_ex00(Path(staged), sandbox=True, **kw) if args.experimental_sandbox else check_ex00(Path(staged), **kw)
            if ex_id == 'c00/ex01':
                return check_ex01(Path(staged), sandbox=True, **kw) if args.experimental_sandbox else check_ex01(Path(staged), **kw)
            return check_exercise(Path(staged), ex_id, sandbox=bool(args.experimental_sandbox), **kw)

    def evaluate_single(path, ex_id):
        try:
            return _evaluate_single(path, ex_id)
        except OSError as exc:
            return {'exercise': f'42/{piscine_of(ex_id) or "c"}/{ex_id}',
                    'subject_version': ALL_EXERCISES.get(ex_id, {}).get('subject_version', '1.0'),
                    'profile': '42-autodidacte', 'isolation': 'Préparation de la source impossible',
                    'checks': [{'name': 'Préparation', 'status': 'unavailable',
                                'message': str(exc)[:300]}], 'result': 'incomplete'}

    def record_history(report, source_path):
        if not args.no_history:
            try:
                store_attempt(report, str(source_path))
                try:
                    write_dashboard()
                except (HistoryError, OSError, ValueError):
                    pass
            except KeyboardInterrupt:
                report = dict(report)
                report['checks'] = [{'name':'Interruption historique','status':'unavailable',
                                     'message':'Interruption pendant l’historique ; état de son enregistrement inconnu.'}]
                report['result'] = 'incomplete'
            except (HistoryError, OSError, ValueError) as exc:
                print(f"Historique non enregistré : {exc}", file=sys.stderr)
        return report

    if args.module or args.all:
        items, err = discover_batch(args.path, args.module if args.module else None)
        if err:
            print(err, file=sys.stderr)
            return 2

        def run_batch_once():
            from concurrent.futures import ThreadPoolExecutor
            reports = []
            counts = {'passed': 0, 'failed': 0, 'incomplete': 0}
            workers = max(1, min(8, int(getattr(args, 'jobs', 1) or 1)))
            if workers > 1 and not args.experimental_cgroup_sandbox and len(items) > 1:
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    raw_reports = list(pool.map(lambda it: evaluate_single(it[1], it[0]), items))
            else:
                raw_reports = [evaluate_single(folder, ex_id) for ex_id, folder in items]
            for (ex_id, folder), raw_rep in zip(items, raw_reports):
                rep = record_history(raw_rep, folder)
                reports.append(rep)
                counts[rep['result']] = counts.get(rep['result'], 0) + 1
            overall = 'failed' if counts['failed'] else ('incomplete' if counts['incomplete'] else 'passed')
            if args.json:
                print(json.dumps({'mode': 'module' if args.module else 'all', 'results': reports,
                                  'summary': counts, 'result': overall}, ensure_ascii=False, indent=2))
            else:
                symbols = {'passed': '✓', 'failed': '✗', 'incomplete': '—'}
                for rep in reports:
                    ex_short = rep['exercise'].split('/', 2)[-1] if rep['exercise'].startswith('42/') else rep['exercise']
                    print(f"{symbols[rep['result']]} {ex_short}: {rep['result']}")
                print(f"\nSynthèse ({len(reports)} exercice(s)) : {counts['passed']} réussi(s), {counts['failed']} échec(s), {counts['incomplete']} incomplet(s).")
            return {"passed": 0, "failed": 1, "incomplete": 2}[overall]

        if not args.watch:
            return run_batch_once()
        watched_dirs = [folder for _, folder in items]
        return _watch_loop(run_batch_once, watched_dirs, args.watch_interval, args.max_iterations)

    if args.exercise is not None:
        exercise_id = canonical_exercise(args.exercise)
        if exercise_id is None:
            print("Exercice non pris en charge : consultez « moulinette list » (C 00 à C 13, C++ 00 à 08, Python 00 à 04).", file=sys.stderr)
            return 2
    else:
        exercise_id, err = detect_exercise(args.path)
        if err:
            print(err, file=sys.stderr)
            return 2

    def run_single_once():
        try:
            if remote:
                try:
                    with trusted_public_repository(args.path, exercise_id, ref=args.ref, subdir=args.subdir) as (folder, provenance):
                        report = evaluate_single(folder, exercise_id)
                        report['source'] = provenance
                except GitHubSourceError as exc:
                    report = {'exercise': f'42/{piscine_of(exercise_id) or "c"}/' + exercise_id, 'subject_version': ALL_EXERCISES[exercise_id].get('subject_version','8'), 'profile': '42-autodidacte',
                              'isolation': 'Récupération Git bornée indisponible ; aucune correction lancée',
                              'checks': [{'name': 'Source GitHub', 'status': 'unavailable', 'message': str(exc)}],
                              'result': 'incomplete'}
            else:
                report = evaluate_single(Path(args.path), exercise_id)
        except KeyboardInterrupt as exc:
            message = 'Correction interrompue ; nettoyage demandé mais non garanti.'
            cleanup = getattr(exc, '_moulinette_cleanup_error', None)
            if cleanup:
                message += ' ' + cleanup
            report = {'exercise': f'42/{piscine_of(exercise_id) or "c"}/' + exercise_id, 'subject_version':ALL_EXERCISES[exercise_id].get('subject_version','8'), 'profile':'42-autodidacte',
                      'isolation':'Interruption pendant une opération expérimentale',
                      'checks':[{'name':'Interruption','status':'unavailable','message':message}],
                      'result':'incomplete'}
        report = record_history(report, args.path)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            _plabel = {'c': 'C', 'cpp': 'C++', 'py': 'Python'}.get(piscine_of(exercise_id) or 'c', 'C')
            print(f"Moulinette Lab — 42 {_plabel} / {exercise_id.split('/')[0].upper()} / {exercise_id.split('/')[-1]} · mode autodidacte")
            if args.experimental_cgroup_sandbox:
                print("ATTENTION : Bubblewrap et cgroup expérimentaux, code de confiance uniquement ; protection incomplète.\n")
            else:
                print(("ATTENTION : Bubblewrap expérimental, code de confiance uniquement ; protection incomplète." if args.experimental_sandbox else "ATTENTION : exécution locale non isolée ; réservée au code de confiance.") + "\n")
            if 'source' in report:
                src = report['source']
                print(f"Source GitHub : {src['url']} · commit {src['commit']} · dossier {src['subdir']}\n")
            if 'cgroup_limits' in report:
                lim = report['cgroup_limits']
                print(f"Cgroup vérifié : {lim['pids_max']} tâches max ; {lim['memory_max']} octets mémoire ; swap max {lim['swap_max']} ; CPU {lim['cpu_quota']}/{lim['cpu_period']}.\n")
            symbols = {"pass": "✓", "fail": "✗", "unavailable": "—", "info": "i"}
            for item in report["checks"]:
                print(f"{symbols[item['status']]} {item['name']}: {item['message']}")
            print("\nRésultat : " + {"failed": "échec", "incomplete": "incomplet", "passed": "réussi"}[report["result"]])
            print("Un test réussi ne garantit pas l'absence de défauts ni un résultat officiel 42.")
        return {"passed": 0, "failed": 1, "incomplete": 2}[report["result"]]

    if not args.watch:
        return run_single_once()
    return _watch_loop(run_single_once, [Path(args.path)], args.watch_interval, args.max_iterations)


def _watch_loop(step_fn, watched_dirs, interval, max_iterations=0):
    """Exécute step_fn puis surveille séquentiellement les modifications sans chevauchement."""
    interval = max(0.05, float(interval))
    runs = 0
    try:
        prev = _snapshot_mtimes(watched_dirs)
        last_code = step_fn()
        runs += 1
        while max_iterations <= 0 or runs < max_iterations:
            time.sleep(interval)
            curr = _snapshot_mtimes(watched_dirs)
            if curr != prev:
                prev = curr
                last_code = step_fn()
                runs += 1
        return last_code
    except KeyboardInterrupt:
        print("Surveillance arrêtée proprement.", file=sys.stderr)
        return 0
