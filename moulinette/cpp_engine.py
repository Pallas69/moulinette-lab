"""Moteur d'évaluation pour la Piscine C++ (Modules 00 à 08).

Réservé au code de confiance. Vérifie les fichiers, les contraintes C++98 du
sujet (absence de *alloc/free/*printf, using namespace, friend, STL avant le
Module 08, gardes d'inclusion), la compilation (-Wall -Wextra -Werror -std=c++98)
et des cas fonctionnels adaptés au sujet.
"""
import errno
import os
import re
import resource
import shutil
import signal
import stat
import tempfile
from pathlib import Path

from . import progress
from .cpp_catalog import CPP_EXERCISES
from .process_capture import run_bounded
from .safe_text import safe_text
from .seccomp_filter import seccomp_fd

MAX_FILE = 262144
MAX_FILES = 64
MAX_CAPTURE = 131072
TIMEOUT_COMPILE = 15
TIMEOUT_TEST = 3

FORBIDDEN_C_FUNCS = (
    "malloc", "calloc", "realloc", "free",
    "printf", "fprintf", "sprintf", "snprintf", "dprintf", "vprintf",
)
STL_CONTAINERS = (
    "vector", "list", "map", "set", "deque", "stack", "queue", "algorithm",
    "unordered_map", "unordered_set",
)


def _strip_comments_and_strings(text):
    """Retire commentaires C/C++ et littéraux chaînes/caractères pour l'analyse lexicale."""
    pattern = re.compile(
        r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        re.MULTILINE,
    )
    return pattern.sub(lambda m: " " if not m.group(0).startswith(('"', "'")) else '""', text)


def _find_cxx_compiler():
    """Retourne (path, label, is_fallback) ou (None, None, False)."""
    clangpp = shutil.which("clang++")
    if clangpp:
        return clangpp, "clang++", False
    for cand in ("g++", "c++"):
        found = shutil.which(cand)
        if found:
            return found, cand, True
    return None, None, False


def _run_cmd(cmd, cwd, timeout, sandbox=False, limited=False, extra_path=None, stdin_bytes=None):
    """Exécute une commande avec limites RLIMIT et, si demandé, Bubblewrap."""
    def setup_limits():
        if limited:
            resource.setrlimit(resource.RLIMIT_CPU, (3, 4))
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024 * 1024, 4 * 1024 * 1024))
        else:
            resource.setrlimit(resource.RLIMIT_CPU, (20, 22))
            resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024 * 1024, 1536 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024, 32 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    path_val = "/usr/local/bin:/usr/bin:/bin"
    if extra_path:
        path_val = f"{extra_path}:{path_val}"
    env = {"PATH": path_val, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}

    work_dir = Path(cwd).resolve()
    stdin_file = None
    pass_fds = ()
    try:
        if stdin_bytes is not None:
            stdin_file = tempfile.TemporaryFile()
            stdin_file.write(stdin_bytes)
            stdin_file.seek(0)
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
            cc_path = shutil.which("cc")
            gpp_path = shutil.which("g++") or shutil.which("clang++")
            bwrap_cmd += ["--dir", "/etc", "--dir", "/etc/alternatives"]
            if cc_path and Path(cc_path).resolve().is_relative_to("/usr"):
                bwrap_cmd += ["--symlink", str(Path(cc_path).resolve()), "/etc/alternatives/cc"]
            if gpp_path and Path(gpp_path).resolve().is_relative_to("/usr"):
                bwrap_cmd += ["--symlink", str(Path(gpp_path).resolve()), "/etc/alternatives/c++"]
            bwrap_cmd += [
                "--proc", "/proc", "--dev", "/dev",
                "--size", str(16 * 1024 * 1024), "--tmpfs", "/tmp",
                "--bind", str(work_dir), "/work",
            ]
            if extra_path:
                bwrap_cmd += ["--ro-bind", str(extra_path), "/tmp/ml-bin"]
                path_val = "/tmp/ml-bin:/usr/bin:/bin"
            else:
                path_val = "/usr/bin:/bin"
            rewritten = []
            for arg in cmd:
                s = str(arg)
                if s.startswith(str(work_dir) + "/"):
                    s = "/work/" + s[len(str(work_dir)) + 1:]
                elif s == str(work_dir):
                    s = "/work"
                rewritten.append(s)
            bwrap_cmd += [
                "--chdir", "/work", "--clearenv",
                "--setenv", "PATH", path_val,
                "--setenv", "LC_ALL", "C",
                "--", *rewritten,
            ]
            cmd_to_run = bwrap_cmd
        else:
            cmd_to_run = [str(x) for x in cmd]

        with seccomp_fd() as sfd:
            if sandbox and sfd is not None:
                cmd_to_run[1:1] = ["--seccomp", str(sfd)]
                pass_fds = (sfd,)
            return run_bounded(
                cmd_to_run, work_dir, timeout, env, setup_limits,
                pass_fds=pass_fds, max_stdout=MAX_CAPTURE, max_stderr=MAX_CAPTURE, stdin=stdin_file,
            )
    finally:
        if stdin_file is not None:
            stdin_file.close()


def _copy_submission_safe(src_dir, dst_dir):
    """Copie sécurisée des fichiers réguliers du dossier soumis."""
    try:
        dir_fd = os.open(src_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return None, f"Dossier local introuvable : {src_dir}"
        return None, "Le dossier soumis doit être un répertoire réel, pas un lien symbolique."
    copied = {}
    try:
        entries = sorted(os.listdir(dir_fd))
        if len(entries) > MAX_FILES:
            return None, f"Trop de fichiers dans le dossier ({len(entries)} > {MAX_FILES})."
        for name in entries:
            if name.startswith("."):
                continue
            if name.endswith((".o", ".a", ".so", ".gch")):
                return None, f"Fichier compilé interdit présent dans le rendu : {name}"
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    return None, f"Lien symbolique refusé : {name}"
                if exc.errno == errno.EISDIR:
                    continue
                return None, f"Ouverture impossible pour {name} : {exc}"
            with os.fdopen(fd, "rb") as f:
                info = os.fstat(f.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    return None, f"Fichier non régulier ou lien multiple refusé : {name}"
                if info.st_size > MAX_FILE:
                    return None, f"Fichier supérieur à 256 Kio : {name}"
                data = f.read(MAX_FILE + 1)
                if len(data) > MAX_FILE:
                    return None, f"Fichier supérieur à 256 Kio : {name}"
                copied[name] = data
                (dst_dir / name).write_bytes(data)
    finally:
        os.close(dir_fd)
    return copied, None


def _check_cpp_style_and_constraints(spec, files_map):
    """Vérifie les contraintes C++98 du sujet sur les sources et en-têtes."""
    issues = []
    allow_stl = spec.get("allow_stl", False)
    forbidden_extra = spec.get("forbidden_tokens", ())
    required_tokens = spec.get("required_tokens", ())
    all_cleaned = []

    for name, raw in sorted(files_map.items()):
        if not name.endswith((".cpp", ".hpp", ".h", ".cc", ".tpp", ".inl")):
            continue
        text = raw.decode("utf-8", "replace")
        cleaned = _strip_comments_and_strings(text)
        all_cleaned.append(cleaned)

        if re.search(r"\busing\s+namespace\b", cleaned):
            issues.append(f"{name} : mot-clé interdit 'using namespace' détecté.")
        if re.search(r"\bfriend\b", cleaned):
            issues.append(f"{name} : mot-clé interdit 'friend' détecté.")
        for fn in FORBIDDEN_C_FUNCS:
            if re.search(rf"\b{fn}\s*\(", cleaned):
                issues.append(f"{name} : fonction C interdite '{fn}()' détectée.")
        if not allow_stl:
            for hdr in STL_CONTAINERS:
                if re.search(rf"#\s*include\s*<\s*{hdr}\s*>", cleaned):
                    issues.append(f"{name} : conteneur/en-tête STL <{hdr}> interdit avant le Module 08.")
        for tok in forbidden_extra:
            if tok.startswith("<"):
                if re.search(rf"#\s*include\s*{re.escape(tok)}", cleaned):
                    issues.append(f"{name} : inclusion interdite {tok} détectée.")
            elif re.search(rf"\b{re.escape(tok)}\b", cleaned):
                issues.append(f"{name} : élément interdit '{tok}' détecté.")

        if name.endswith((".hpp", ".h")):
            has_ifndef = bool(re.search(r"#\s*ifndef\s+\w+", cleaned) and re.search(r"#\s*define\s+\w+", cleaned) and re.search(r"#\s*endif", cleaned))
            has_pragma = bool(re.search(r"#\s*pragma\s+once\b", cleaned))
            if not (has_ifndef or has_pragma):
                issues.append(f"{name} : garde d'inclusion (#ifndef/#define/#endif) absente.")

    combined = "\n".join(all_cleaned)
    for req in required_tokens:
        if req not in combined and not any(req in raw.decode("utf-8", "replace") for raw in files_map.values()):
            issues.append(f"Élément attendu par le sujet introuvable : '{req}'.")

    return issues


def _norm_ws(data):
    lines = [re.sub(rb"\s+", b" ", ln.strip()) for ln in data.strip().splitlines() if ln.strip()]
    return b"\n".join(lines)


def evaluate_cpp_exercise(path, exercise, sandbox=False, sanitize=False):
    """Évalue un exercice C++ de cpp00/ex00 à cpp08/ex04."""
    if exercise not in CPP_EXERCISES:
        raise ValueError(f"Exercice C++ inconnu : {exercise}")
    spec = CPP_EXERCISES[exercise]
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
            "exercise": "42/cpp/" + exercise,
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
        with tempfile.TemporaryDirectory(prefix="moulinette-cpp-") as tmp:
            tmp_path = Path(tmp)
            work = tmp_path / "work"
            work.mkdir()
            shim_dir = tmp_path / "bin"
            shim_dir.mkdir()

            copied, err = _copy_submission_safe(Path(path), work)
            if err:
                add("fail", "Fichiers attendus", err)
                return build_rep()

            # Vérification des fichiers requis
            req_files = list(spec.get("required_files", ()))
            flex_pairs = spec.get("flexible_pairs", ())
            chosen_pair = None
            if flex_pairs:
                for hp, cp in flex_pairs:
                    if hp in copied and cp in copied:
                        chosen_pair = (hp, cp)
                        break
                if not chosen_pair:
                    pair_desc = " ou ".join(f"({h}, {c})" for h, c in flex_pairs)
                    add("fail", "Fichiers attendus", f"Couple d'en-tête/source requis absent : attendu {pair_desc}.")
                    return build_rep()
            missing = [f for f in req_files if f not in copied]
            if missing:
                add("fail", "Fichiers attendus", "Fichiers requis absents : " + ", ".join(missing))
                return build_rep()
            if spec.get("require_cpp_sources") and not any(k.endswith(".cpp") for k in copied):
                add("fail", "Fichiers attendus", "Aucun fichier source .cpp trouvé dans le rendu.")
                return build_rep()

            add("pass", "Fichiers attendus", ", ".join(sorted(copied))[:400])

            # Contraintes de style C++98
            style_issues = _check_cpp_style_and_constraints(spec, copied)
            if style_issues:
                add("fail", "Norminette adaptée", " ; ".join(style_issues)[:3000])
                return build_rep()
            add("pass", "Norminette adaptée", "Contraintes C++98 vérifiées (pas de *alloc/free/*printf, using namespace, friend ni STL non autorisée ; gardes d'inclusion présentes).")

            # Compilateur C++
            cxx_path, cxx_label, is_fallback = _find_cxx_compiler()
            if not cxx_path:
                add("unavailable", "Compilateur", "Aucun compilateur C++ (clang++, g++, c++) trouvé sur le système.")
                return build_rep()
            if is_fallback:
                # Crée un lien clang++ -> g++/c++ pour les Makefiles qui appellent clang++
                (shim_dir / "clang++").symlink_to(Path(cxx_path).resolve())
                add("info", "Compilateur", f"clang++ absent sur l'hôte ; repli sur {cxx_label} avec -Wall -Wextra -Werror -std=c++98.")
            if sandbox and not shutil.which("bwrap"):
                add("unavailable", "Bubblewrap expérimental", "Bubblewrap (bwrap) introuvable ; aucun repli local automatique.")
                return build_rep()

            kind = spec["kind"]
            cxx_flags = ["-Wall", "-Wextra", "-Werror", "-std=c++98"]

            # Vérification Makefile si présent dans les fichiers requis
            if "Makefile" in req_files:
                mk_text = copied["Makefile"].decode("utf-8", "replace")
                for flag in ("-Wall", "-Wextra", "-Werror"):
                    if flag not in mk_text:
                        add("fail", "Compilation", f"Flag obligatoire {flag} absent du Makefile.")
                        return build_rep()
                make_bin = shutil.which("make")
                if not make_bin:
                    add("unavailable", "Compilation", "Outil 'make' introuvable sur le système.")
                    return build_rep()
                code, out, err_b, to = _run_cmd([make_bin, "all"], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                if to or code != 0:
                    add("fail", "Compilation", "Délai dépassé." if to else (err_b.decode("utf-8", "replace")[:2000] or out.decode("utf-8", "replace")[:2000] or "Échec de make all."))
                    return build_rep()
                add("pass", "Compilation", "Makefile compilé avec succès (-Wall -Wextra -Werror).")
            else:
                # Compilation directe des sources .cpp
                for fname, content in spec.get("support_files", {}).items():
                    (work / fname).write_text(content, encoding="utf-8")

            # Exécution selon le type d'exercice
            if kind == "makefile_program":
                bin_name = spec["binary"]
                bin_path = work / bin_name
                if not bin_path.is_file():
                    add("fail", "Compilation", f"Exécutable attendu '{bin_name}' non produit par le Makefile.")
                    return build_rep()
                cases = spec["cases"]
                progress.emit("plan", "tests", str(len(cases)))
                for label, args, expected in cases:
                    c, out, err_b, to = _run_cmd([str(bin_path), *args], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                    if to:
                        add("fail", f"Test {label}", "Délai dépassé.")
                        break
                    if c != 0 or out != expected:
                        add("fail", f"Test {label}", f"Attendu : {expected[:80]!r} ({len(expected)} octet(s)) ; obtenu : {out[:80]!r} ({len(out)} octet(s)) ; code : {c}.")
                    else:
                        add("pass", f"Test {label}", "Sortie conforme au sujet.")

            elif kind == "phonebook_program":
                # Trouve l'exécutable produit
                bins = [p for p in work.iterdir() if p.is_file() and os.access(p, os.X_OK) and not p.name.endswith((".cpp", ".hpp", ".h", ".o")) and p.name != "Makefile"]
                if not bins:
                    add("fail", "Compilation", "Aucun exécutable produit par le Makefile pour PhoneBook.")
                    return build_rep()
                exe = bins[0]
                progress.emit("plan", "tests", "2")
                stdin_data = (
                    b"ADD\nJean\nDupont\njdup\njdupont\n42 rue Paris\njean@42.fr\n0102030405\n01/01/2000\nPizza\nBleu\nDormir\n"
                    b"SEARCH\n0\nEXIT\n"
                )
                c, out, _, to = _run_cmd([str(exe)], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir, stdin_bytes=stdin_data)
                if to or c != 0 or b"Jean" not in out or b"|" not in out:
                    add("fail", "Test ADD / SEARCH / EXIT", f"Sortie PhoneBook inattendue ou code {c} : {out[:160]!r}")
                else:
                    add("pass", "Test ADD / SEARCH / EXIT", "Ajout, affichage tabulaire '|' et sortie EXIT validés.")
                stdin_trunc = (
                    b"ADD\nJeanBaptisteTresLong\nDupont\njdup\njdupont\n42 rue\njean@42.fr\n0102\n01/01\nPizza\nBleu\nSecret\n"
                    b"SEARCH\n0\nEXIT\n"
                )
                c2, out2, _, to2 = _run_cmd([str(exe)], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir, stdin_bytes=stdin_trunc)
                if to2 or c2 != 0 or b"JeanBapti." not in out2:
                    add("fail", "Test troncature 10 caractères", f"Troncature avec '.' à 10 caractères non détectée : {out2[:160]!r}")
                else:
                    add("pass", "Test troncature 10 caractères", "Troncature à 10 colonnes avec '.' validée.")

            elif kind == "account_harness":
                exe = work / "test_account"
                c, _, err_b, to = _run_cmd([cxx_path, *cxx_flags, "Account.class.cpp", "tests.cpp", "-o", str(exe)], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                if to or c != 0:
                    add("fail", "Compilation", err_b.decode("utf-8", "replace")[:2000] or "Échec de compilation avec tests.cpp.")
                    return build_rep()
                add("pass", "Compilation", "Account.class.cpp compilé et lié avec tests.cpp.")
                progress.emit("plan", "tests", "1")
                rc, out, _, rto = _run_cmd([str(exe)], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                if rto or rc != 0:
                    add("fail", "Test journal Account", f"Exécution échouée (code {rc}).")
                else:
                    lines = [re.sub(r"^\[[^\]]+\]\s*", "", ln.strip()) for ln in out.decode("utf-8", "replace").splitlines() if ln.strip()]
                    expected = spec["expected_lines"]
                    if lines[:len(expected)] == expected:
                        add("pass", "Test journal Account", f"Les {len(expected)} lignes d'opérations correspondent au journal de référence.")
                    else:
                        add("fail", "Test journal Account", f"Différence dans les logs Account (attendu {len(expected)} lignes, obtenu {len(lines)}).")

            elif kind == "replace_program":
                exe = work / "replace"
                if not exe.is_file():
                    bins = [p for p in work.iterdir() if p.is_file() and os.access(p, os.X_OK) and not p.name.endswith((".cpp", ".hpp", ".h", ".o")) and p.name != "Makefile"]
                    if bins:
                        exe = bins[0]
                if not exe.is_file():
                    add("fail", "Compilation", "Exécutable 'replace' introuvable après make.")
                    return build_rep()
                progress.emit("plan", "tests", "1")
                (work / "sample.txt").write_text("Hello world, world is great!\n", encoding="utf-8")
                c, _, _, to = _run_cmd([str(exe), "sample.txt", "world", "42"], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                rep_file = work / "sample.txt.replace"
                if to or c != 0 or not rep_file.is_file() or rep_file.read_text(encoding="utf-8", errors="replace") != "Hello 42, 42 is great!\n":
                    add("fail", "Test remplacement fichier", "Le fichier sample.txt.replace est absent ou son contenu est inexact.")
                else:
                    add("pass", "Test remplacement fichier", "sample.txt.replace généré avec les occurrences remplacées.")

            elif kind == "cato9tails_program":
                bins = [p for p in work.iterdir() if p.is_file() and os.access(p, os.X_OK) and not p.name.endswith((".cpp", ".hpp", ".h", ".o")) and p.name != "Makefile"]
                if not bins:
                    add("fail", "Compilation", "Exécutable cato9tails introuvable.")
                    return build_rep()
                exe = bins[0]
                progress.emit("plan", "tests", "1")
                (work / "f1.txt").write_bytes(b"Alpha\nBeta\n")
                c, out, _, to = _run_cmd([str(exe), "f1.txt"], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                if to or c != 0 or out != b"Alpha\nBeta\n":
                    add("fail", "Test lecture fichier", f"Attendu : b'Alpha\\nBeta\\n' (11 octet(s)) ; obtenu : {out[:60]!r} ({len(out)} octet(s)).")
                else:
                    add("pass", "Test lecture fichier", "Affichage du fichier conforme à cat.")

            elif kind == "mindopen_program":
                bins = [p for p in work.iterdir() if p.is_file() and os.access(p, os.X_OK) and not p.name.endswith((".cpp", ".hpp", ".h", ".o")) and p.name != "Makefile"]
                if not bins:
                    add("fail", "Compilation", "Exécutable Mindopen introuvable.")
                    return build_rep()
                exe = bins[0]
                progress.emit("plan", "tests", "1")
                (work / "prog.mo").write_text("++++++[>++++++++++<-]>+++++.", encoding="utf-8")
                c, out, _, to = _run_cmd([str(exe), "prog.mo"], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                if to or c != 0 or b"A" not in out:
                    add("fail", "Test programme Mindopen", f"Attendu 'A' sur stdout ; obtenu {out[:60]!r} (code {c}).")
                else:
                    add("pass", "Test programme Mindopen", "Exécution d'un programme Mindopen validée ('A').")

            elif kind == "rpn_program":
                bins = [p for p in work.iterdir() if p.is_file() and os.access(p, os.X_OK) and not p.name.endswith((".cpp", ".hpp", ".h", ".o")) and p.name != "Makefile"]
                if not bins:
                    add("fail", "Compilation", "Exécutable RPN introuvable.")
                    return build_rep()
                exe = bins[0]
                progress.emit("plan", "tests", "1")
                c, out, _, to = _run_cmd([str(exe), "3 + ((1 + 4) * 2) - 1"], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                if to or c != 0 or b"12" not in out:
                    add("fail", "Test expression RPN", f"Attendu résultat 12 ; obtenu {out[:120]!r} (code {c}).")
                else:
                    add("pass", "Test expression RPN", "Conversion postfixée et évaluation (12) validées.")

            elif kind == "makefile_and_harness":
                bins = [p for p in work.iterdir() if p.is_file() and os.access(p, os.X_OK) and not p.name.endswith((".cpp", ".hpp", ".h", ".o")) and p.name != "Makefile"]
                if not bins:
                    add("fail", "Compilation", "Aucun exécutable généré par le Makefile.")
                    return build_rep()
                exe = bins[0]
                progress.emit("plan", "tests", "1")
                c, out, _, to = _run_cmd([str(exe)], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                exp_sub = spec.get("expected_substr")
                if to or c != 0 or not out.strip() or (exp_sub and exp_sub not in out):
                    add("fail", "Test exécution", f"Sortie invalide ou code {c} : {out[:120]!r}")
                else:
                    add("pass", "Test exécution", "Exécution et sortie validées.")

            elif kind in ("fixed_harness", "harness_only", "student_main_only", "student_main_and_harness"):
                cpp_files = sorted(k for k in copied if k.endswith(".cpp"))
                if kind == "fixed_harness":
                    hdr_name, cpp_name = chosen_pair
                    harness_code = spec["harness"].replace("__FIXED_HEADER__", hdr_name)
                    (work / "__ml_harness.cpp").write_text(harness_code, encoding="utf-8")
                    exe = work / "test_bin"
                    c, _, err_b, to = _run_cmd([cxx_path, *cxx_flags, cpp_name, "__ml_harness.cpp", "-o", str(exe)], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                elif kind == "harness_only":
                    (work / "__ml_harness.cpp").write_text(spec["harness"], encoding="utf-8")
                    exe = work / "test_bin"
                    # Neutralise main étudiant éventuel dans ex01.cpp
                    objs = []
                    c, err_b, to = 0, b"", False
                    for src in cpp_files:
                        obj = src + ".o"
                        c, _, err_b, to = _run_cmd([cxx_path, *cxx_flags, "-Dmain=__ml_student_main", "-c", src, "-o", obj], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                        if to or c != 0:
                            break
                        objs.append(obj)
                    if not to and c == 0:
                        c, _, err_b, to = _run_cmd([cxx_path, *cxx_flags, "__ml_harness.cpp", *objs, "-o", str(exe)], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                elif kind == "student_main_only":
                    exe = work / "test_bin"
                    c, _, err_b, to = _run_cmd([cxx_path, *cxx_flags, *cpp_files, "-o", str(exe)], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                else:
                    # Compile d'abord le main de l'étudiant pour vérifier qu'il compile et tourne
                    student_exe = work / "student_bin"
                    c, _, err_b, to = _run_cmd([cxx_path, *cxx_flags, *cpp_files, "-o", str(student_exe)], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                    if not to and c == 0 and "harness" in spec:
                        (work / "__ml_harness.cpp").write_text(spec["harness"], encoding="utf-8")
                        non_main = [f for f in cpp_files if f != "main.cpp"]
                        exe = work / "test_bin"
                        c, _, err_b, to = _run_cmd([cxx_path, *cxx_flags, "__ml_harness.cpp", *non_main, "-o", str(exe)], work, TIMEOUT_COMPILE, sandbox=sandbox, extra_path=shim_dir)
                    else:
                        exe = student_exe

                if to or c != 0:
                    add("fail", "Compilation", "Délai dépassé." if to else (err_b.decode("utf-8", "replace")[:2000] or "Échec de compilation C++98."))
                    return build_rep()
                add("pass", "Compilation", f"Compilé avec {cxx_label} -Wall -Wextra -Werror -std=c++98.")

                progress.emit("plan", "tests", "1")
                rc, out, _, rto = _run_cmd([str(exe)], work, TIMEOUT_TEST, sandbox=sandbox, limited=True, extra_path=shim_dir)
                if rto or rc != 0:
                    add("fail", "Test fonctionnel", "Délai dépassé." if rto else f"Code de retour non nul ({rc}) ; sortie : {out[:120]!r}")
                else:
                    exp_exact = spec.get("expected_exact")
                    exp_sub = spec.get("expected_substr")
                    exp_cnt = spec.get("expected_count")
                    exp_file = spec.get("expected_file")
                    ok = True
                    if exp_exact is not None:
                        if spec.get("normalize_spaces"):
                            ok = _norm_ws(out) == _norm_ws(exp_exact)
                        else:
                            ok = out == exp_exact
                        if not ok:
                            add("fail", "Test fonctionnel", f"Attendu : {exp_exact[:100]!r} ({len(exp_exact)} octet(s)) ; obtenu : {out[:100]!r} ({len(out)} octet(s)).")
                    elif exp_cnt is not None:
                        needle, count = exp_cnt
                        if out.count(needle) < count:
                            ok = False
                            add("fail", "Test fonctionnel", f"Attendu au moins {count} occurrence(s) de {needle!r} ; obtenu {out.count(needle)}.")
                    elif exp_sub is not None and exp_sub not in out:
                        ok = False
                        add("fail", "Test fonctionnel", f"Sous-chaîne attendue {exp_sub!r} absente de la sortie {out[:120]!r}.")
                    elif not out.strip():
                        ok = False
                        add("fail", "Test fonctionnel", "Sortie vide.")
                    if ok and exp_file is not None:
                        fn, fsub = exp_file
                        fpath = work / fn
                        if not fpath.is_file() or (fsub and fsub not in fpath.read_bytes()):
                            ok = False
                            add("fail", "Test fichier généré", f"Fichier attendu '{fn}' absent ou incomplet.")
                    if ok:
                        add("pass", "Test fonctionnel", "Comportement et sortie conformes au sujet.")

    except Exception as exc:
        add("unavailable", "Exécution C++", f"Erreur interne ou environnement indisponible : {exc}")

    add(
        "info",
        "Limites",
        "Tests C++98 non officiels et non exhaustifs ; l'analyse statique des mots-clés et de la forme canonique de Coplien reste partielle. Code de confiance uniquement.",
    )
    return build_rep()
