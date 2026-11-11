"""Le témoin OOM expérimental ne doit plus pouvoir être lancé, même en opt-in."""
import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch
from moulinette import cgroup_load_probe

class DisabledProbeTests(unittest.TestCase):
    def test_witness_fails_closed_even_if_requested(self):
        output=io.StringIO()
        with patch.dict(os.environ,{'ML_TEST_CGROUP_LOAD':'1'}), patch('os.fork',side_effect=AssertionError('aucune charge autorisée')),contextlib.redirect_stdout(output):
            cgroup_load_probe.witness_main()
        result=json.loads(output.getvalue())
        self.assertEqual(result['status'],'unavailable')
        self.assertIn('désactiv',result['message'])

if __name__=='__main__':unittest.main()
