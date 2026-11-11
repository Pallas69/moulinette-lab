"""Notification optionnelle de la progression d'une correction.

Aucun effet tant qu'aucun écouteur n'est installé : la correction, les
rapports et l'historique restent identiques. Un écouteur reçoit chaque contrôle
au moment où le moteur l'enregistre. Ce mécanisme n'ajoute aucune isolation.
"""
import threading
from contextlib import contextmanager

_state = threading.local()


def emit(status, name, message):
    """Transmet un contrôle à l'écouteur du thread courant, s'il existe."""
    listener = getattr(_state, 'listener', None)
    if listener is None:
        return
    try:
        listener(status, name, message)
    except Exception:  # un affichage défaillant ne doit jamais fausser une correction
        pass


def plan(stage, total):
    """Annonce le nombre d'éléments prévus pour une étape (barre de progression)."""
    emit('plan', stage, str(int(total)))


@contextmanager
def listening(callback):
    previous = getattr(_state, 'listener', None)
    _state.listener = callback
    try:
        yield
    finally:
        _state.listener = previous
