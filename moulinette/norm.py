"""Adaptateur limité à la sortie JSON de Norminette 3.3.59."""
import json
import re
import shutil

SUPPORTED_VERSION = "3.3.59"


def parse_norm_result(output, returncode):
    """N'ignore que INVALID_HEADER ; une réponse douteuse est non évaluée."""
    lines = output.decode("utf-8", "replace").splitlines()
    candidates = [line for line in lines if line.startswith('{"files":')]
    extra = [line for line in lines if line and not line.startswith('Setting locale to ') and not line.startswith('{"files":')]
    if len(candidates) != 1 or extra or returncode not in (0, 1):
        return "unavailable", "Sortie Norminette illisible ou inattendue ; aucun résultat de style n'est validé."
    try:
        data = json.loads(candidates[0])
        files = data["files"]
        if not isinstance(files, list) or len(files) != 1:
            raise ValueError("nombre de fichiers inattendu")
        f = files[0]
        if f["status"] not in ("OK", "Error") or not isinstance(f["errors"], list):
            raise ValueError("statut ou erreurs inattendus")
        ignored, errors, notices = [], [], []
        for item in f["errors"]:
            name, level, text = item["name"], item["level"], item["text"]
            if not all(isinstance(s, str) for s in (name, level, text)) or not isinstance(item.get("highlights", []), list):
                raise ValueError("diagnostic mal formé")
            if name == "INVALID_HEADER":
                ignored.append(item)
            elif level == "Error":
                h = item.get("highlights", [])
                pos = h[0] if h and isinstance(h[0], dict) else {}
                errors.append(f"{name} ligne {pos.get('lineno', '?')} col {pos.get('column', '?')}: {text}")
            elif level == "Notice":
                notices.append(f"{name}: {text}")
            else:
                raise ValueError("niveau inconnu")
        if returncode == 0 and f["status"] == "Error":
            raise ValueError("statut incohérent")
        if returncode == 1 and f["status"] == "OK" and not notices:
            raise ValueError("sortie anormale sans diagnostic")
        if f["status"] == "Error" and not (errors or ignored):
            raise ValueError("erreur non identifiée")
        suffix = f"Norminette {SUPPORTED_VERSION} ; INVALID_HEADER ignoré : {len(ignored)}."
        if notices:
            suffix += " Notices : " + "; ".join(notices)
        if errors:
            return "fail", suffix + " " + " ; ".join(errors)
        return "pass", "Style 42 adapté : " + suffix
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return "unavailable", "Données Norminette non reconnues ; aucun résultat de style n'est validé."


def check_norm(work, run, source_name="ft_putchar.c"):
    binary = shutil.which("norminette")
    if not binary:
        return "unavailable", "Norminette introuvable ; le style n'a pas été vérifié."
    code, out, err, timeout = run([binary, "--version"], work, 10)
    version_text = (out + b"\n" + err).decode("utf-8", "replace")
    match = re.search(r"\bnorminette\s+(\d+\.\d+\.\d+)\b", version_text, re.I)
    if timeout or code != 0 or not match or match.group(1) != SUPPORTED_VERSION:
        detected = match.group(1) if match else "inconnue"
        return "unavailable", f"Version détectée : {detected}. Seule la version {SUPPORTED_VERSION} est prise en charge ; style non vérifié."
    code, out, err, timeout = run([binary, "-f", "json", "--no-colors", source_name], work, 15)
    if timeout:
        return "unavailable", "Norminette a dépassé le délai ; style non vérifié."
    if len(out) >= 65536 or len(err) >= 65536:
        return "unavailable", "Sortie Norminette trop volumineuse ou tronquée ; style non vérifié."
    if err.strip():
        return "unavailable", "Norminette a produit une sortie d'erreur inattendue ; style non vérifié."
    return parse_norm_result(out, code)
