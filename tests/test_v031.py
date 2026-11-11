"""Tests légers v0.31-dev : commandes simplifiées et atome évolutif sans légende."""
import contextlib, io, unittest
from pathlib import Path
from unittest.mock import patch
from moulinette import cli
from moulinette.dashboard import render_dashboard

ROOT = Path(__file__).resolve().parents[1]


class SimplifiedCommandsTests(unittest.TestCase):
    def _run(self, argv, which='/usr/bin/bwrap'):
        report = {'result': 'passed', 'checks': [], 'exercise': '42/c/c01/ex00'}
        with patch('moulinette.cli.check_exercise', return_value=report) as chk, \
             patch('moulinette.cli.shutil.which', return_value=which), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = cli.main(argv)
        return code, chk, err.getvalue()

    def test_path_shortcut_defaults_to_bubblewrap(self):
        code, chk, err = self._run([str(ROOT / 'exemples/c01/ex00'), '--no-history'])
        self.assertEqual(code, 0)
        self.assertEqual(chk.call_args.args[1], 'c01/ex00')
        self.assertTrue(chk.call_args.kwargs['sandbox'])
        self.assertIn('Bubblewrap', err)

    def test_short_local_and_exercise_flags(self):
        code, chk, _ = self._run([str(ROOT / 'exemples/c01/ex00'), '-l', '-e', 'c01/ex00', '--no-history'])
        self.assertEqual(code, 0)
        self.assertFalse(chk.call_args.kwargs['sandbox'])

    def test_historic_long_flags_still_work(self):
        code, chk, _ = self._run(['check', str(ROOT / 'exemples/c01/ex00'), '--exercise', 'c01/ex00',
                                  '--experimental-sandbox', '--no-history'])
        self.assertEqual(code, 0)
        self.assertTrue(chk.call_args.kwargs['sandbox'])

    def test_no_bwrap_and_no_mode_is_refused(self):
        code, chk, err = self._run([str(ROOT / 'exemples/c01/ex00'), '--no-history'], which=None)
        self.assertEqual(code, 2)
        chk.assert_not_called()
        self.assertIn('-l', err)

    def test_list_command(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(['list', '--piscine', 'py']), 0)
        self.assertIn('3. Piscine Python (36 exercices)', out.getvalue())


class AtomWithoutLegendTests(unittest.TestCase):
    def test_atom_has_no_text_legend_but_keeps_counters(self):
        html = render_dashboard({'count': 0, 'recent': [], 'latest': []}, live_mode=False)
        self.assertIn('id="atom-canvas"', html)
        self.assertIn('data-protons="0"', html)
        self.assertIn('data-electrons="109"', html)
        for gone in ('atom-metrics', 'Protons (Réussis)', 'Neutrons (À revoir)', 'Électrons (Total)', 'Analogie visuelle'):
            self.assertNotIn(gone, html)


if __name__ == '__main__':
    unittest.main()
