"""Moteur d'évaluation pour la Piscine Python (Modules 00 à 04).

Réservé au code de confiance. Vérifie la présence des fichiers, l'absence de
eval() et des fonctions interdites via l'AST Python, la disponibilité des
bibliothèques requises (sans jamais rien installer automatiquement ni accéder
au réseau), et exécute les tests fonctionnels adaptés au sujet.
"""
import ast
import os
import resource
import shutil
import stat
import tempfile
from pathlib import Path

from . import progress
from .process_capture import run_bounded
from .py_catalog import PY_EXERCISES
from .safe_text import safe_text
from .seccomp_filter import seccomp_fd

MAX_FILE = 262144
MAX_FILES = 64
MAX_CAPTURE = 131072
TIMEOUT_TEST = 8


def _copy_py_submission_safe(src_dir, dst_dir):
    """Copie sécurisée des fichiers réguliers (et sous-dossiers pour py02/ex04)."""
    root = Path(src_dir)
    try:
        st = root.lstat()
    except OSError:
        return None, f"Dossier local introuvable : {src_dir}"
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
        return None, "Le dossier soumis doit être un répertoire réel, pas un lien symbolique."
    copied = {}
    count = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for d in dirs:
            p = Path(base) / d
            if p.is_symlink():
                return None, f"Lien symbolique de dossier refusé : {d}"
        for name in sorted(files):
            if name.startswith(".") or name.endswith((".pyc", ".pyo")):
                continue
            item = Path(base) / name
            rel = item.relative_to(root).as_posix()
            count += 1
            if count > MAX_FILES:
                return None, f"Trop de fichiers dans le dossier ({count} > {MAX_FILES})."
            try:
                info = item.lstat()
            except OSError as exc:
                return None, f"Lecture impossible pour {rel} : {exc}"
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                return None, f"Fichier non régulier ou lien symbolique refusé : {rel}"
            if info.st_size > MAX_FILE:
                return None, f"Fichier supérieur à 256 Kio : {rel}"
            data = item.read_bytes()
            if len(data) > MAX_FILE:
                return None, f"Fichier supérieur à 256 Kio : {rel}"
            copied[rel] = data
            target = dst_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return copied, None


def _check_python_ast_and_style(spec, copied):
    """Vérifie la syntaxe Python, l'interdiction absolue de eval() et les règles par exercice."""
    issues = []
    style_notes = []
    forbidden_calls = set(spec.get("forbidden_calls", ())) | {"eval"}
    forbidden_imports = set(spec.get("forbidden_imports", ()))
    forbid_while = bool(spec.get("forbid_while", False))

    for rel, raw in sorted(copied.items()):
        if not rel.endswith(".py"):
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(f"{rel} : encodage UTF-8 invalide.")
            continue
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError as exc:
            issues.append(f"{rel} : erreur de syntaxe ligne {exc.lineno} ({exc.msg}).")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn_name = None
                if isinstance(node.func, ast.Name):
                    fn_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    fn_name = node.func.attr
                if fn_name in forbidden_calls:
                    issues.append(f"{rel} : appel à la fonction interdite '{fn_name}()' ligne {getattr(node, 'lineno', '?')}.")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in forbidden_imports or alias.name in forbidden_imports:
                        issues.append(f"{rel} : import interdit '{alias.name}' ligne {getattr(node, 'lineno', '?')}.")
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if mod in forbidden_imports:
                    issues.append(f"{rel} : import interdit depuis '{node.module}' ligne {getattr(node, 'lineno', '?')}.")
                for alias in node.names:
                    if alias.name in forbidden_calls or alias.name in forbidden_imports:
                        issues.append(f"{rel} : import interdit '{alias.name}' ligne {getattr(node, 'lineno', '?')}.")
            elif forbid_while and isinstance(node, ast.While):
                issues.append(f"{rel} : boucle 'while' interdite par le sujet ligne {getattr(node, 'lineno', '?')}.")

        for idx, line in enumerate(text.splitlines(), 1):
            if len(line) > 100:
                style_notes.append(f"{rel}:L{idx} > 100 caractères")

    return issues, style_notes


def _run_py(cmd, cwd, timeout, sandbox=False, extra_pythonpath=None):
    """Exécute python3 sous limites RLIMIT et, si demandé, dans Bubblewrap."""
    def setup_limits():
        resource.setrlimit(resource.RLIMIT_CPU, (5, 6))
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    if extra_pythonpath:
        env["PYTHONPATH"] = str(extra_pythonpath)

    work_dir = Path(cwd).resolve()
    if sandbox:
        bwrap = shutil.which("bwrap")
        if not bwrap:
            raise RuntimeError("Bubblewrap (bwrap) introuvable.")
        bwrap_cmd = [
            bwrap, "--unshare-all", "--die-with-parent", "--new-session",
            "--ro-bind", "/usr", "/usr",
            "--symlink", "usr/bin", "/bin",
            "--symlink", "usr/lib", "/lib",
        ]
        if Path("/usr/lib64").exists():
            bwrap_cmd += ["--symlink", "usr/lib64", "/lib64"]
        bwrap_cmd += [
            "--proc", "/proc", "--dev", "/dev",
            "--size", str(16 * 1024 * 1024), "--tmpfs", "/tmp",
            "--bind", str(work_dir), "/work",
        ]
        pypath = "/work"
        if extra_pythonpath:
            bwrap_cmd += ["--ro-bind", str(Path(extra_pythonpath).resolve()), "/opt/ml-pydeps"]
            pypath = "/opt/ml-pydeps:/work"
        bwrap_cmd += [
            "--chdir", "/work", "--clearenv",
            "--setenv", "PATH", "/usr/bin:/bin",
            "--setenv", "LC_ALL", "C.UTF-8",
            "--setenv", "PYTHONPATH", pypath,
            "--", *cmd,
        ]
        cmd_to_run = bwrap_cmd
    else:
        cmd_to_run = list(cmd)
        env["PYTHONPATH"] = f"{extra_pythonpath}:{work_dir}" if extra_pythonpath else str(work_dir)

    with seccomp_fd() as sfd:
        pass_fds = ()
        if sandbox and sfd is not None:
            cmd_to_run[1:1] = ["--seccomp", str(sfd)]
            pass_fds = (sfd,)
        return run_bounded(
            cmd_to_run, work_dir, timeout, env, setup_limits,
            pass_fds=pass_fds, max_stdout=MAX_CAPTURE, max_stderr=MAX_CAPTURE,
        )


def evaluate_py_exercise(path, exercise, sandbox=False, sanitize=False):
    """Évalue un exercice Python de py00/ex00 à py04/ex07."""
    if exercise not in PY_EXERCISES:
        raise ValueError(f"Exercice Python inconnu : {exercise}")
    spec = PY_EXERCISES[exercise]
    checks = []

    def add(status, name, message):
        s, n, m = status, safe_text(name), safe_text(message)
        checks.append({"status": s, "name": n, "message": m})
        progress.emit(s, n, m)

    def build_rep():
        status = (
            "failed" if any(x["status"] == "fail" for x in checks)
            else "incomplete" if any(x["status"] == "unavailable" for x in checks)
            else "passed"
        )
        return {
            "exercise": "42/py/" + exercise,
            "subject_version": spec.get("subject_version", "1.0"),
            "profile": "42-autodidacte",
            "isolation": (
                "Bubblewrap expérimental — code de confiance uniquement"
                if sandbox else "aucune — mode local non sécurisé"
            ),
            "checks": checks,
            "result": status,
        }

    try:
        with tempfile.TemporaryDirectory(prefix="moulinette-py-") as tmp:
            work = Path(tmp) / "work"
            work.mkdir()

            copied, err = _copy_py_submission_safe(Path(path), work)
            if err:
                add("fail", "Fichiers attendus", err)
                return build_rep()

            req_files = list(spec.get("required_files", ()))
            missing = [f for f in req_files if f not in copied]
            if missing:
                add("fail", "Fichiers attendus", "Fichiers requis absents : " + ", ".join(missing))
                return build_rep()

            add("pass", "Fichiers attendus", ", ".join(sorted(copied))[:400])

            # Analyse AST et contraintes
            ast_issues, style_notes = _check_python_ast_and_style(spec, copied)
            if ast_issues:
                add("fail", "Norminette adaptée", " ; ".join(ast_issues)[:3000])
                return build_rep()
            style_msg = "Syntaxe AST valide ; aucun appel interdit (eval, etc.) détecté."
            if style_notes:
                style_msg += f" Remarque PEP 8 indicative : {len(style_notes)} ligne(s) > 100 caractères."
            add("pass", "Norminette adaptée", style_msg)

            py_bin = shutil.which("python3")
            if not py_bin:
                add("unavailable", "Compilateur", "Interpréteur python3 introuvable sur le système.")
                return build_rep()
            if sandbox and not shutil.which("bwrap"):
                add("unavailable", "Bubblewrap expérimental", "Bubblewrap (bwrap) introuvable ; aucun repli local automatique.")
                return build_rep()

            extra_py = os.environ.get("MOULINETTE_PY_EXTRA_PATH") or None

            # Vérification de la disponibilité des bibliothèques tierces requises
            req_mods = spec.get("required_modules", ())
            if req_mods:
                probe_code = "import " + ", ".join(req_mods)
                c, _, _, to = _run_py([py_bin, "-B", "-c", probe_code], work, 5, sandbox=sandbox, extra_pythonpath=extra_py)
                if to or c != 0:
                    missing_mods = []
                    for m in req_mods:
                        mc, _, _, mto = _run_py([py_bin, "-B", "-c", f"import {m}"], work, 5, sandbox=sandbox, extra_pythonpath=extra_py)
                        if mto or mc != 0:
                            missing_mods.append(m)
                    mods_str = ", ".join(missing_mods or req_mods)
                    add(
                        "unavailable",
                        "Compilation",
                        f"Indisponible : bibliothèque(s) Python requise(s) ({mods_str}) non installée(s) dans cet environnement. Aucune installation automatique ni connexion réseau n'est effectuée.",
                    )
                    return build_rep()
            add("pass", "Compilation", "Environnement Python 3 et dépendances requises disponibles.")

            # Exécution du script de test
            progress.emit("plan", "tests", "1")
            (work / "__ml_py_test.py").write_text(spec["test_script"], encoding="utf-8")
            rc, out, err_b, rto = _run_py([py_bin, "-B", "__ml_py_test.py"], work, TIMEOUT_TEST, sandbox=sandbox, extra_pythonpath=extra_py)
            if rto:
                add("fail", "Test fonctionnel", f"Délai dépassé ({TIMEOUT_TEST}s).")
            elif rc != 0:
                err_txt = err_b.decode("utf-8", "replace").strip()[-1200:] or out.decode("utf-8", "replace").strip()[-1200:]
                add("fail", "Test fonctionnel", f"Échec du test Python (code {rc}) : {err_txt}")
            else:
                add("pass", "Test fonctionnel", "Comportement et résultats conformes au sujet.")

    except Exception as exc:
        add("unavailable", "Exécution Python", f"Erreur interne ou environnement indisponible : {exc}")

    add(
        "info",
        "Limites",
        "Tests Python non officiels et non exhaustifs ; PEP 8 est recommandé par le sujet mais non bloquant ; aucune dépendance n'est installée automatiquement. Code de confiance uniquement.",
    )
    return build_rep()
