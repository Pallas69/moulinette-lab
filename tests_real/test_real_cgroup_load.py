"""Le témoin de charge de la v0.20 est désactivé, même avec l'ancien opt-in.

La validation réelle des limites mémoire reste ouverte et nécessite une VM
jetable ainsi qu'un protocole distinct revu avant toute exécution.
"""
import unittest

@unittest.skip('Témoin de charge désactivé : ne pas provoquer d’OOM sur la session utilisateur.')
class RealCgroupLoadTest(unittest.TestCase):
    def test_bounded_memory_and_cpu_load_in_real_user_scope(self):
        self.fail('Le témoin désactivé ne doit jamais être exécuté.')
