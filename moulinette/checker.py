"""Évaluation prototype : 42 C Piscine C 00 à C 13.

Le runner local n'est PAS une sandbox. Réservé au code de confiance.
"""
import os
import errno
import re
import secrets
import resource
import shutil
import signal
import stat
import tempfile
from pathlib import Path
from .norm import check_norm
from .exercise_catalog import EXERCISES
from .sandbox_runner import ExperimentalRunner, SandboxUnavailable
from .process_capture import run_bounded, exception_with_cleanup
from .safe_text import safe_text
from .recursion_hint import recursion_hint, main_signature_hint
from .pipeline import build_report, classify_external_symbols, parse_nm_undefined
from . import progress

MAX_FILE = 262144
TIMEOUT_COMPILE = 10
TIMEOUT_TEST = 1
MAX_CAPTURE = 131072


def check_ex00(path, sandbox=False, sanitize=False):
    return check_exercise(path, 'c00/ex00', sandbox=sandbox, sanitize=sanitize)


def check_ex01(path, sandbox=False, sanitize=False):
    return check_exercise(path, 'c00/ex01', sandbox=sandbox, sanitize=sanitize)


def _run(cmd, cwd, timeout, limited=False, pass_fds=()):
    """Des limites utiles, mais ni isolation ni sécurité garantie."""
    def setup_limits():
        if limited:
            resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        else:
            resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
            resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    return run_bounded(cmd, cwd, timeout, env, setup_limits, pass_fds=pass_fds,
                       max_stdout=MAX_CAPTURE, max_stderr=MAX_CAPTURE)


def _run_sanitize_local(cmd, cwd, timeout):
    """Exécution locale pour ASan/UBSan (sans RLIMIT_AS incompatible avec la mémoire fantôme d'ASan)."""
    def setup_limits():
        resource.setrlimit(resource.RLIMIT_CPU, (4, 5))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
           "ASAN_OPTIONS": "detect_leaks=1:abort_on_error=1",
           "UBSAN_OPTIONS": "print_stacktrace=1:halt_on_error=1"}
    return run_bounded(cmd, cwd, timeout, env, setup_limits, max_stdout=MAX_CAPTURE, max_stderr=MAX_CAPTURE)


def _exit_message(code):
    if code < 0:
        try: return f"{code} ({signal.Signals(-code).name})"
        except ValueError: return f"{code} (signal {-code})"
    return str(code)


def check_exercise(path, exercise, sandbox=False, sanitize=False):
    from .cpp_catalog import CPP_EXERCISES
    from .py_catalog import PY_EXERCISES
    if exercise in CPP_EXERCISES:
        from .cpp_engine import evaluate_cpp_exercise
        return evaluate_cpp_exercise(path, exercise, sandbox=sandbox, sanitize=sanitize)
    if exercise in PY_EXERCISES:
        from .py_engine import evaluate_py_exercise
        return evaluate_py_exercise(path, exercise, sandbox=sandbox, sanitize=sanitize)
    if exercise not in EXERCISES:
        raise ValueError('Exercice non pris en charge.')
    spec = EXERCISES[exercise]
    if 'project' in spec:
        from .project_engine import evaluate_project
        return evaluate_project(path,exercise,spec,sandbox=sandbox,sanitize=sanitize)
    source_name = spec['source']
    executable = spec['executable']
    checks = []
    def add(status, name, message):
        s, n, m = status, safe_text(name), safe_text(message)
        checks.append({"status": s, "name": n, "message": m}); progress.emit(s, n, m)
    def result():
        return build_report(exercise, spec, sandbox, checks)
    try:
        runner = ExperimentalRunner(_run, exercise=exercise) if sandbox else _run
        # Ancrer l'inventaire et l'ouverture sur le même répertoire ouvert :
        # un renommage du chemin ne doit pas changer le fichier lu ensuite.
        # Les composants parents restent susceptibles de liens ou de courses.
        try:
            dir_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                add("fail", "Dossier", f"Dossier local introuvable : {path}"); return result()
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                add("fail", "Dossier", "Le dossier final doit être un répertoire réel, pas un lien symbolique."); return result()
            raise
        try:
            entries = sorted(os.listdir(dir_fd))
            extras = [x for x in entries if x != source_name]
            add("fail" if extras else "pass", "Fichiers supplémentaires" if extras else "Fichiers attendus", ", ".join(extras) if extras else source_name + " uniquement.")
            if extras:
                return result()
            try:
                fd = os.open(source_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
            except FileNotFoundError:
                add("fail", "Fichier attendu", source_name + " absent."); return result()
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    add("fail", "Fichier attendu", "Lien symbolique refusé pour " + source_name + "."); return result()
                raise
            with os.fdopen(fd, 'rb') as source_file:
                info = os.fstat(source_file.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    add("fail", "Fichier attendu", "Fichier non régulier ou lien physique refusé."); return result()
                if info.st_size > MAX_FILE:
                    add("fail", "Taille du fichier", "Fichier supérieur à 256 Kio."); return result()
                contents = source_file.read(MAX_FILE + 1)
                after = os.fstat(source_file.fileno())
                # Détection indicative : ne garantit pas un instantané atomique.
                before_sig = (info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                after_sig = (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                if before_sig != after_sig or len(contents) != after.st_size:
                    add("unavailable", "Lecture du fichier", "Fichier modifié pendant sa lecture ; correction arrêtée."); return result()
        finally:
            os.close(dir_fd)
        if len(contents) > MAX_FILE:
            add("fail", "Taille du fichier", "Fichier supérieur à 256 Kio."); return result()
        cc = shutil.which("cc")
        if not cc:
            add("unavailable", "Compilateur", "cc introuvable ; installer un compilateur C."); return result()
        with tempfile.TemporaryDirectory(prefix="moulinette-") as tmp:
            work = Path(tmp)
            (work / source_name).write_bytes(contents)
            marker = secrets.token_bytes(16)
            harness = spec['harness'].replace('MARKER_BYTES', ', '.join(str(b) for b in marker))
            (work / "harness.c").write_text(harness, encoding="utf-8")
            (work / "proto_check.c").write_text(spec["prototype"], encoding="utf-8")
            # On teste les mêmes octets que l'objet compilé et inspecté ; pas de recompilation dans le harnais.
            object_name = "submission.o"
            code, out, err, timed_out = runner([cc, "-Wall", "-Wextra", "-Werror", "-fno-builtin", "-c", source_name, "-o", object_name], work, TIMEOUT_COMPILE)
            if code != 0 or timed_out:
                add("fail", "Compilation", "Délai dépassé." if timed_out else (err.decode('utf-8', 'replace')[:3000] or 'Échec de compilation.')); return result()
            add("pass", "Compilation", "cc -Wall -Wextra -Werror ; -fno-builtin ajouté pour l'analyse.")
            hint = recursion_hint(exercise, contents)
            if hint is not None:
                add("info", "Récursivité (indicative)", hint)
            nm = shutil.which("nm")
            if not nm:
                add("unavailable", "Fonctions externes", "nm indisponible ; restrictions non vérifiées.")
                return result()
            else:
                def read_symbols(filename):
                    code, out, err, timed_out = runner([nm, "-u", filename], work, 5)
                    if code != 0 or timed_out or err.strip() or len(out) >= MAX_CAPTURE: return None
                    return parse_nm_undefined(out)
                syms = read_symbols(object_name)
                if syms is None:
                    add("unavailable", "Fonctions externes", "Analyse des symboles impossible, tronquée ou de format non reconnu.")
                    return result()
                else:
                    allowed_fns = spec.get('allowed_functions', {'write'})
                    prohibited, canary_hits = classify_external_symbols(syms, allowed_fns)
                    if canary_hits and not prohibited:
                        alternate = "submission-nocanary.o"
                        code, out, err, timed_out = runner([cc, "-Wall", "-Wextra", "-Werror", "-fno-builtin", "-fno-stack-protector", "-c", source_name, "-o", alternate], work, TIMEOUT_COMPILE)
                        if code == 0 and not timed_out:
                            alternate_symbols = read_symbols(alternate)
                            if alternate_symbols is not None:
                                object_name, syms = alternate, alternate_symbols
                                add("info", "Adaptation compilation", "Objet recompilé avec -fno-stack-protector : protection de pile désactivée pour le rendu testé. Code de confiance uniquement.")
                            else:
                                add("info", "Recompilation", "Contrôle des symboles de l'objet alternatif impossible ; objet initial conservé.")
                        else:
                            add("info", "Recompilation", "Recompilation alternative impossible ; objet initial conservé.")
                        prohibited, canary_hits = classify_external_symbols(syms, allowed_fns)
                    if prohibited:
                        add("fail", "Fonctions externes", "Symboles non autorisés détectés : " + ", ".join(prohibited)); return result()
                    elif canary_hits:
                        add("unavailable", "Fonctions externes", "Symboles de protection de pile présents ; origine non vérifiée : " + ", ".join(sorted(canary_hits)) + ". Analyse partielle."); return result()
                    else:
                        add("info", "Fonctions externes", "Aucun symbole externe interdit détecté ; cette analyse est partielle, pas une garantie.")
            is_program = spec.get('kind') == 'program'
            if not is_program:
                code, out, err, timed_out = runner([cc, "-Wall", "-Wextra", "-Werror", "-std=c11", "-c", "proto_check.c", "-o", "proto_check.o"], work, TIMEOUT_COMPILE)
                if code != 0 or timed_out:
                    add("fail", "Prototype", "Délai dépassé." if timed_out else (err.decode('utf-8', 'replace')[:3000] or 'Prototype invalide.')); return result()
            link = [cc, "-Wall", "-Wextra", "-Werror", "-std=c11"] + ([] if is_program else ["harness.c"]) + [object_name, "-o", executable]
            code, out, err, timed_out = runner(link, work, TIMEOUT_COMPILE)
            has_student_main = False
            if code != 0 and not timed_out and not is_program and b'multiple definition of' in err and b'main' in err:
                nomain_obj = "submission-nomain.o"
                nomain_flags = ["-Wall", "-Wextra", "-Werror", "-fno-builtin", "-Dmain=__moulinette_student_main", "-Wno-unused-function", "-Wno-return-type"]
                if object_name == "submission-nocanary.o":
                    nomain_flags.append("-fno-stack-protector")
                c2, _, _, t2 = runner([cc, *nomain_flags, "-c", source_name, "-o", nomain_obj], work, TIMEOUT_COMPILE)
                if c2 == 0 and not t2:
                    object_name = nomain_obj
                    has_student_main = True
                    link = [cc, "-Wall", "-Wextra", "-Werror", "-std=c11", "harness.c", object_name, "-o", executable]
                    code, out, err, timed_out = runner(link, work, TIMEOUT_COMPILE)
                    if code == 0 and not timed_out:
                        add("info", "Adaptation compilation", "Fonction main() de test détectée dans le fichier et neutralisée pour lier le harnais (retirez main() pour un rendu 42 strict).")
            if code != 0 or timed_out:
                if b'ML_INT_PLATFORM_UNSUPPORTED' in err:
                    add("unavailable", "Plateforme", "Le modèle des entiers du compilateur ne correspond pas à celui pris en charge ; exercice non évalué."); return result()
                add("fail", "Édition des liens", "Délai dépassé." if timed_out else (err.decode('utf-8', 'replace')[:3000] or 'Liaison impossible.')); return result()
            add("pass", "Prototype et liaison", ("Programme lié à l'objet réellement évalué ; signature de main non vérifiée séparément." if is_program else "Contrôle du type et liaison à l'objet réellement évalué."))
            if is_program:
                sig_note = main_signature_hint(contents)
                add("info", "Convention de test", "Programme exécuté avec arguments ; sortie exacte et retour 0 attendus. Signature de main non vérifiée séparément." + (" " + sig_note if sig_note else ""))
            if exercise in ('c00/ex01', 'c00/ex02', 'c00/ex03'):
                add("info", "Convention de test", "Sortie exacte attendue, sans caractère supplémentaire ni saut de ligne ; convention non officielle.")
            if exercise == 'c00/ex04':
                add("info", "Convention de test", "INT_MIN et INT_MAX issus de <limits.h> ; sortie exacte sans caractère supplémentaire.")
            if exercise in ('c00/ex05', 'c00/ex06', 'c00/ex07', 'c00/ex08'):
                add("info", "Convention de test", "Sortie exacte et séparateurs conformes aux exemples du sujet ; pas de saut de ligne ajouté. Tests non officiels.")
            all_cases = spec['cases']
            progress.emit("plan", "tests", str(len(all_cases)))
            for label, argument, expected in all_cases:
                test_timeout = spec.get('timeout', TIMEOUT_TEST)
                cmd = [str(work / executable)] + (list(argument) if is_program else [argument])
                code, out, err, timed_out = runner(cmd, work, test_timeout, limited=True)
                if is_program:
                    if expected == b'__PROGRAM_NAME__':
                        expected = (('/work/' + executable) if sandbox else str(work / executable)).encode() + b'\n'
                    if timed_out:
                        add("fail", "Test " + label, f"Délai dépassé ({test_timeout} seconde(s)) ; tests restants annulés."); break
                    elif code != 0 or out != expected:
                        add("fail", "Test " + label, f"Attendu : {expected[:80]!r} ({len(expected)} octet(s)) ; obtenu : {out[:80]!r} ({len(out)} octet(s)) ; code : {_exit_message(code)}.")
                    else:
                        add("pass", "Test " + label, "Sortie attendue et retour normal (0).")
                elif timed_out:
                    add("fail", "Test " + label, f"Délai dépassé ({test_timeout} seconde(s)) ; tests restants annulés."); break
                elif code != 73 or out != expected + marker:
                    marker_seen = out.endswith(marker)
                    actual = out[:-len(marker)] if marker_seen else out
                    note = " Sortie détectée sur stderr." if not actual and err else ""
                    if not marker_seen:
                        note += " Marqueur de fin du harnais absent."
                    add("fail", "Test " + label, f"Attendu : {expected[:32]!r} ({len(expected)} octet(s)) ; obtenu : {actual[:32]!r} ({len(actual)} octet(s)) ; code de sortie : {_exit_message(code)}.{note}")
                else:
                    add("pass", "Test " + label, "Sortie attendue sur stdout et marqueur de fin du harnais reçu.")
                if err:
                    add("info", "Sortie stderr", f"Sortie supplémentaire détectée pendant le test {label} (avertissement, pas une règle du sujet).")
            if sanitize and not any(x["status"] in ("fail", "unavailable") for x in checks):
                san_exec = executable + "-san"
                san_flags = (["-fsanitize=undefined", "-fsanitize-undefined-trap-on-error"] if sandbox
                             else ["-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-g"])
                extra_c = ["-Dmain=__moulinette_student_main", "-Wno-unused-function", "-Wno-return-type"] if has_student_main else []
                c_code, _, _, c_to = runner([cc, "-Wall", "-Wextra", "-Werror", "-fno-builtin", *extra_c, *san_flags, "-c", source_name, "-o", "submission-san.o"], work, TIMEOUT_COMPILE)
                l_args = [cc, "-Wall", "-Wextra", "-Werror", "-std=c11", *([] if sandbox and is_program else san_flags), *([] if is_program else ["harness.c"]), "submission-san.o", "-o", san_exec]
                l_code, _, _, l_to = (runner(l_args, work, TIMEOUT_COMPILE) if c_code == 0 and not c_to else (1, b'', b'', False))
                if c_code != 0 or c_to or l_code != 0 or l_to:
                    add("info", "Sanitizer (optionnel)", "Outil sanitizer indisponible dans cet environnement ; le résultat habituel est inchangé.")
                else:
                    san_failed = None
                    for label, argument, _ in all_cases:
                        test_timeout = max(2, spec.get('timeout', TIMEOUT_TEST) * 2)
                        s_cmd = [str(work / san_exec)] + (list(argument) if is_program else [argument])
                        s_code, _, s_err, s_to = (runner(s_cmd, work, test_timeout, limited=True) if sandbox else _run_sanitize_local(s_cmd, work, test_timeout))
                        expected_code = 0 if is_program else 73
                        if s_to or s_code != expected_code:
                            detail = s_err.decode('utf-8', 'replace').strip()[:1000] or f"code {_exit_message(s_code)}"
                            san_failed = f"Anomalie signalée sur « {label} » ({detail})."
                            break
                    if san_failed:
                        add("fail", "Sanitizer (optionnel)", san_failed)
                    else:
                        mode_lbl = "UBSan trap sous Bubblewrap (ASan non activable sous RLIMIT_AS=256M)" if sandbox else "ASan + UBSan en mode local"
                        add("info", "Sanitizer (optionnel)", f"Aucun problème observé sur les cas exécutés ({mode_lbl}) : analyse partielle, ne prouve pas l’absence de fuite mémoire ou de comportement indéfini.")
            norm_status, norm_message = check_norm(work, runner) if exercise == 'c00/ex00' else check_norm(work, runner, source_name)
            add(norm_status, "Norminette adaptée", norm_message)
    except SandboxUnavailable as exc:
        add("unavailable", "Bubblewrap expérimental", exception_with_cleanup(exc))
    except (OSError, ValueError) as exc:
        add("unavailable", "Exécution", f"Impossible d'accéder aux fichiers ou de lancer un outil : {exception_with_cleanup(exc)}")
    limits=("Bubblewrap expérimental : code de confiance seulement, filtre seccomp partiel (x86_64), pas de cgroups ni protection complète." if sandbox else "Mode non isolé.") + " Restrictions des appels et prototype : contrôles partiels. " + ("Sanitizer optionnel partiel sur les seuls cas exécutés." if sanitize else "Pas de contrôle mémoire par défaut.")
    if exercise.startswith("c05/"):
        limits += " La récursivité et l’itération ne sont pas démontrées ; le diagnostic de récursivité éventuel est indicatif et non bloquant."
    add("info", "Limites", limits)
    return result()
