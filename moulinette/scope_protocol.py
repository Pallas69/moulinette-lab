"""Canal de contrôle interne, futur lanceur cgroup — non relié à check.

Un message est une longueur réseau sur 4 octets suivie d'un objet JSON UTF-8.
Ce protocole ne prouve pas l'identité du pair ni la sécurité du scope. Un délai
sur le socket est indispensable ; toute erreur doit bloquer l'évaluation.
"""
import json
import socket
import struct
import time

MAX_MESSAGE = 65536

class ScopeProtocolError(Exception):
    """Message indéterminé ou non valide : ne pas poursuivre l'évaluation."""


def _read_exact(sock, length, deadline=None):
    data = bytearray()
    while len(data) < length:
        try:
            if deadline is not None:
                remaining=deadline-time.monotonic()
                if remaining<=0: raise ScopeProtocolError('Délai global de réception dépassé.')
                sock.settimeout(remaining)
            chunk = sock.recv(length - len(data))
        except OSError as exc:
            raise ScopeProtocolError('Canal interrompu ou délai dépassé.') from exc
        if not chunk:
            raise ScopeProtocolError('Canal fermé avant la fin du message.')
        data.extend(chunk)
    return bytes(data)


def send_object(sock, data):
    if not isinstance(data, dict):
        raise ScopeProtocolError('Un objet JSON est requis.')
    try:
        content = json.dumps(data, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if not 0 < len(content) <= MAX_MESSAGE:
            raise ScopeProtocolError('Message trop volumineux.')
        sock.sendall(struct.pack('!I', len(content)) + content)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise ScopeProtocolError('Impossible de transmettre le message.') from exc


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('clé JSON dupliquée')
        result[key] = value
    return result


def receive_object(sock, *, deadline=None):
    try:
        length = struct.unpack('!I', _read_exact(sock, 4, deadline))[0]
        if not 0 < length <= MAX_MESSAGE:
            raise ScopeProtocolError('Longueur de message invalide.')
        raw = _read_exact(sock, length, deadline)
        def reject_constant(value):
            raise ValueError('constante non standard')
        message = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object, parse_constant=reject_constant)
        if not isinstance(message, dict):
            raise ValueError('objet JSON attendu')
        return message
    except (ValueError, TypeError, UnicodeError, struct.error) as exc:
        raise ScopeProtocolError('Message de contrôle invalide.') from exc
