"""Rendre les noms Linux non-UTF-8 représentables dans les diagnostics."""

def safe_text(value):
    return value.encode('utf-8', 'backslashreplace').decode('utf-8')
