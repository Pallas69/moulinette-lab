import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette import live, progress
from moulinette.dashboard import render_dashboard
from moulinette.dashboard_insights import parse_diff, parse_norm, stage_of, summarize_stages
from moulinette.live import make_handler
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent.parent


class ParsingTests(unittest.TestCase):
    def test_stage_classification_and_summary(self):
        self.assertEqual(stage_of('Fichiers attendus'), 'files')
        self.assertEqual(stage_of('Norminette adaptée'), 'norm')
        self.assertEqual(stage_of('Compilation'), 'build')
        self.assertEqual(stage_of('Fonctions externes'), 'build')
        self.assertEqual(stage_of('Test zéro'), 'tests')
        self.assertEqual(stage_of('Limites'), 'meta')
        stages = {s['key']: s for s in summarize_stages([
            {'name': 'Fichiers attendus', 'status': 'pass'},
            {'name': 'Compilation', 'status': 'pass'},
            {'name': 'Test cas 1', 'status': 'fail'},
            {'name': 'Norminette adaptée', 'status': 'pass'},
        ])}
        self.assertEqual(stages['files']['cls'], 'ok')
        self.assertEqual(stages['build']['cls'], 'ok')
        self.assertEqual(stages['tests']['cls'], 'bad')
        self.assertEqual(stages['norm']['cls'], 'ok')

    def test_diff_extracts_literal_bytes_with_invisible_characters(self):
        msg = "Attendu : b'ab\\n\\x00' (4 octet(s)) ; obtenu : b'ab  ' (4 octet(s)) ; code : 0."
        d = parse_diff(msg)
        self.assertEqual(d['expected'], [97, 98, 10, 0])
        self.assertEqual(d['actual'], [97, 98, 32, 32])
        self.assertFalse(d['truncated'])

    def test_diff_flags_truncation_and_project_format(self):
        d = parse_diff("Attendu b'abc', obtenu b'', code 0. ")
        self.assertEqual(d['actual'], [])
        d = parse_diff("Attendu : b'a' (500 octet(s)) ; obtenu : b'a' (3 octet(s)) ; code : 0.")
        self.assertTrue(d['truncated'])

    def test_diff_never_evaluates_code(self):
        self.assertIsNone(parse_diff("Attendu : b'a' + __import__('os') ; obtenu : 1"))
        self.assertIsNone(parse_diff("Délai dépassé."))

    def test_norm_items_with_line_numbers_and_project_files(self):
        msg = ("a.c : Norminette 3.3.59 ; INVALID_HEADER ignoré : 1. SPACE_BEFORE_FUNC ligne 3 col 4: espace ; "
               "b.c : Norminette 3.3.59 ; TOO_MANY_LINES ligne 30 col 1: trop long")
        items = parse_norm(msg, 'x.c')
        self.assertEqual([(i['file'], i['code'], i['line']) for i in items],
                         [('a.c', 'SPACE_BEFORE_FUNC', 3), ('b.c', 'TOO_MANY_LINES', 30)])
        single = parse_norm('Norminette 3.3.59 ; INVALID_HEADER ignoré : 1. BAD ligne 2 col 1: t', 'ft_putchar.c')
        self.assertEqual(single[0]['file'], 'ft_putchar.c')

    def test_progress_is_inert_without_listener_and_isolated_on_error(self):
        progress.emit('pass', 'x', 'y')
        def boom(*a): raise RuntimeError('affichage')
        with progress.listening(boom):
            progress.emit('pass', 'x', 'y')

    def test_senthora_dashboard_renders_stages_diff_and_norm_highlights(self):
        attempt = {
            'exercise': 'c00/ex00',
            'created_at': '2026-01-01T12:00:00',
            'source_label': 'rendu',
            'isolation': 'Bubblewrap',
            'result': 'failed',
            'checks': [
                {'name': 'Fichiers attendus', 'status': 'pass', 'message': 'ft_putchar.c uniquement.'},
                {'name': 'Compilation', 'status': 'pass', 'message': 'ok'},
                {'name': 'Test lettre', 'status': 'fail',
                 'message': "Attendu : b'a\\n\\x00' (3 octet(s)) ; obtenu : b'a  ' (3 octet(s)) ; code : 0."},
                {'name': 'Norminette adaptée', 'status': 'fail',
                 'message': 'Norminette 3.3.59 ; INVALID_HEADER ignoré : 1. SPACE_BEFORE_FUNC ligne 4 col 6: espace'},
            ],
        }
        page = render_dashboard({'count': 1, 'recent': [attempt], 'latest': [attempt]})
        self.assertIn('class="attempt-stages"', page)
        self.assertIn('01 · Fichiers', page)
        self.assertIn('02 · Compilation', page)
        self.assertIn('03 · Tests', page)
        self.assertIn('04 · Norminette', page)
        self.assertIn('Progression par module', page)
        self.assertIn('Activité enregistrée', page)
        self.assertNotIn('0 leak', page.lower())
        self.assertNotIn('0 segfault', page.lower())
        self.assertIn('class="diff-box"', page)
        self.assertIn('Expected Output', page)
        self.assertIn('Your Output', page)
        self.assertIn('\\n', page)
        self.assertIn('\\0', page)
        self.assertIn('g-trail', page)
        self.assertIn('class="norm-box"', page)
        self.assertIn('ligne 4 · col 6', page)
        self.assertIn('SPACE_BEFORE_FUNC', page)


class ServerTests(unittest.TestCase):
    token = 'tok-test'

    def setUp(self):
        self.state = {'runs': {}, 'active': None, 'lock': threading.Lock()}
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.token, self.state))
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'XDG_DATA_HOME': self.tmp.name}); env.start(); self.addCleanup(env.stop)

    def request(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=60)
        try:
            h = dict(headers or {})
            data = json.dumps(body).encode() if body is not None else None
            c.request(method, path, body=data, headers=h)
            r = c.getresponse()
            return r.status, r.read(), r
        finally:
            c.close()

    def test_page_requires_token_and_serves_senthora_dashboard(self):
        self.assertEqual(self.request('GET', '/')[0], 403)
        status, body, _ = self.request('GET', '/?t=' + self.token)
        self.assertEqual(status, 200)
        self.assertIn(b'MOULINETTE', body)
        self.assertIn(b'id="roastbox"', body)

    def test_rebinding_host_refused(self):
        status, _, _ = self.request('GET', '/?t=' + self.token, headers={'Host': 'evil.example:%d' % self.port})
        self.assertEqual(status, 403)

    def test_api_requires_token_and_origin(self):
        self.assertEqual(self.request('GET', '/api/exercises')[0], 403)
        self.assertEqual(self.request('GET', '/api/exercises', headers={'X-Moulinette-Token': self.token})[0], 200)
        status, _, _ = self.request('POST', '/api/run', {'exercise': 'c00/ex00'}, {'X-Moulinette-Token': 'x'})
        self.assertEqual(status, 403)
        status, _, _ = self.request('POST', '/api/run', {'exercise': 'c00/ex00', 'path': '.'},
                                    {'X-Moulinette-Token': self.token, 'Origin': 'http://evil.example'})
        self.assertEqual(status, 403)

    def test_input_validation(self):
        h = {'X-Moulinette-Token': self.token}
        for body in ({'exercise': 'nope', 'path': '.'},
                     {'exercise': 'c00/ex00', 'path': 'https://github.com/a/b'},
                     {'exercise': 'c00/ex00', 'path': '/inexistant-xyz'},
                     {'exercise': 'c00/ex00', 'path': '.', 'mode': 'local'},
                     {'exercise': 'c00/ex00', 'path': '.', 'mode': 'cgroup'}):
            self.assertEqual(self.request('POST', '/api/run', body, h)[0], 400, body)

    def stream(self, run):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=120)
        try:
            c.request('GET', '/api/events?t=%s&run=%s' % (self.token, run))
            r = c.getresponse()
            events = []
            for line in r.read().decode().split('\n'):
                if line.startswith('data: '):
                    events.append(json.loads(line[6:]))
            return events
        finally:
            c.close()

    def run_example(self, exercise, folder, mode='local'):
        body = {'exercise': exercise, 'path': str(folder), 'mode': mode, 'confirm_unsafe': True}
        status, raw, _ = self.request('POST', '/api/run', body, {'X-Moulinette-Token': self.token})
        self.assertEqual(status, 202, raw)
        return self.stream(json.loads(raw)['run'])

    def test_live_stream_of_reference_example(self):
        events = self.run_example('c00/ex00', ROOT / 'exemples' / 'ft_putchar')
        types = [e['type'] for e in events]
        self.assertEqual(types[0], 'start'); self.assertEqual(types[-1], 'done')
        self.assertIn('check', types)
        self.assertEqual([e['seq'] for e in events], list(range(len(events))))
        self.assertIn('ft_putchar.c', events[0]['sources'])
        stages = {e['stage'] for e in events if e['type'] == 'check'}
        self.assertTrue({'files', 'build', 'tests'} <= stages)
        plan = [e for e in events if e['type'] == 'plan']
        self.assertTrue(plan and plan[0]['stage'] == 'tests')
        tests = [e for e in events if e['type'] == 'check' and e['name'].startswith('Test ')]
        self.assertEqual(len(tests), plan[0]['total'])
        ts = [e['t'] for e in events]; self.assertEqual(ts, sorted(ts))

    def test_wrong_output_yields_visible_diff(self):
        d = Path(self.tmp.name) / 'rendu'; d.mkdir()
        (d / 'ft_putchar.c').write_text('#include <unistd.h>\n\nvoid\tft_putchar(char c)\n{\n\twrite(1, &c, 1);\n\twrite(1, " ", 1);\n}\n')
        events = self.run_example('c00/ex00', d)
        fails = [e for e in events if e['type'] == 'check' and e['status'] == 'fail' and e['stage'] == 'tests']
        self.assertTrue(fails)
        self.assertIn('diff', fails[0])
        self.assertEqual(fails[0]['diff']['actual'][-1], 32)
        self.assertEqual(events[-1]['result'], 'failed')

    def test_norm_fault_has_line_number_when_norminette_available(self):
        import shutil
        if not shutil.which('norminette'):
            self.skipTest('Norminette indisponible')
        d = Path(self.tmp.name) / 'rendu'; d.mkdir()
        (d / 'ft_putchar.c').write_text('#include <unistd.h>\nvoid ft_putchar(char c){write(1,&c,1);}\n')
        events = self.run_example('c00/ex00', d)
        norm = [e for e in events if e['type'] == 'check' and e['stage'] == 'norm' and e['status'] == 'fail']
        self.assertTrue(norm and norm[0]['norm'])
        self.assertTrue(all(isinstance(i['line'], int) for i in norm[0]['norm']))

    def test_single_active_run(self):
        run = live.Run('busy'); self.state['active'] = run
        body = {'exercise': 'c00/ex00', 'path': str(ROOT / 'exemples' / 'ft_putchar'), 'mode': 'local', 'confirm_unsafe': True}
        status, _, _ = self.request('POST', '/api/run', body, {'X-Moulinette-Token': self.token})
        self.assertEqual(status, 409)


class EngineUnchangedTests(unittest.TestCase):
    def test_reports_are_identical_with_and_without_listener(self):
        from moulinette.checker import check_exercise
        folder = ROOT / 'exemples' / 'ft_putchar'
        a = check_exercise(folder, 'c00/ex00', sandbox=False)
        seen = []
        with progress.listening(lambda *x: seen.append(x)):
            b = check_exercise(folder, 'c00/ex00', sandbox=False)
        self.assertEqual(a, b)
        self.assertEqual(len([s for s in seen if s[0] != 'plan']), len(b['checks']))


class ImprovementV03001LightTests(unittest.TestCase):
    def test_doop_and_main_signature_hints_are_indicative(self):
        from moulinette.recursion_hint import doop_hint, main_signature_hint
        msg_found = doop_hint({'do_op.c': 'int (*fn[5])(int, int);'})
        self.assertIn('tableau de pointeurs de fonctions repérée', msg_found)
        self.assertIn('pas une preuve', msg_found)
        msg_typedef = doop_hint({'do_op.h': 'typedef int (*t_op)(int, int);', 'do_op.c': 't_op ops[5];'})
        self.assertIn('tableau de pointeurs de fonctions repérée', msg_typedef)
        msg_none = doop_hint({'do_op.c': 'int main(void) { return 0; }'})
        self.assertIn('Aucun tableau explicite', msg_none)
        self.assertIn('non bloquante', msg_none)
        self.assertIn('int main(int, char **)', main_signature_hint('int main(int argc, char **argv) { return 0; }'))
        self.assertIn('sans (argc, argv)', main_signature_hint('int main(void) { return 0; }'))

    def test_optional_sanitize_distinguishes_observed_from_proven_and_detects_ub(self):
        import shutil
        if not shutil.which('cc') or not shutil.which('nm'):
            self.skipTest('cc et nm requis')
        from moulinette.checker import check_exercise
        good = check_exercise(ROOT / 'exemples' / 'ft_putchar', 'c00/ex00', sandbox=False, sanitize=True)
        san = next(c for c in good['checks'] if c['name'] == 'Sanitizer (optionnel)')
        self.assertEqual(san['status'], 'info')
        self.assertIn('Aucun problème observé', san['message'])
        self.assertIn('ne prouve pas', san['message'])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'ft_putchar.c').write_text(
                '#include <unistd.h>\nvoid\tft_putchar(char c)\n{\n\tint\tx;\n\n\tx = 2147483647;\n\tx = x + (c != 0);\n\t(void)x;\n\twrite(1, &c, 1);\n}\n'
            )
            bad = check_exercise(p, 'c00/ex00', sandbox=False, sanitize=True)
        san_bad = next(c for c in bad['checks'] if c['name'] == 'Sanitizer (optionnel)')
        self.assertEqual(san_bad['status'], 'fail')
        self.assertEqual(bad['result'], 'failed')

    def test_seccomp_filter_bytes_and_session_descendant_cleanup(self):
        import sys
        from moulinette.seccomp_filter import seccomp_bpf_bytes
        from moulinette import project_job
        self.assertIsNone(seccomp_bpf_bytes('aarch64'))
        bpf = seccomp_bpf_bytes('x86_64')
        self.assertIsNotNone(bpf)
        self.assertEqual(len(bpf) % 8, 0)
        if sys.platform.startswith('linux') and hasattr(os, 'fork'):
            script = (
                'import os, time\n'
                'p = os.fork()\n'
                'if not p:\n'
                ' os.setpgid(0, 0)\n'
                ' time.sleep(2)\n'
                ' os._exit(0)\n'
                'os.write(1, (str(p) + "\\n").encode())\n'
                'os._exit(0)\n'
            )
            with tempfile.TemporaryDirectory() as t, patch.object(project_job, 'ISOLATED_JOB', True):
                res = project_job.execute([sys.executable, '-c', script], t, timeout=1)
            child_pid = int(res['out'].strip())
            self.assertFalse((Path('/proc') / str(child_pid)).exists())

    def test_cli_autodetect_ambiguity_module_and_watch(self):
        import contextlib, io
        from moulinette import cli
        from moulinette.cli import detect_exercise
        ex_id, err = detect_exercise(str(ROOT / 'exemples' / 'ft_putchar'))
        self.assertEqual((ex_id, err), ('c00/ex00', None))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'ft_putstr.c').write_text('void ft_putstr(char *s) { (void)s; }\n')
            ex_id, err = detect_exercise(str(p))
            self.assertIsNone(ex_id)
            self.assertIn('c01/ex05', err)
            self.assertIn('c04/ex01', err)
        out = io.StringIO()
        fake = {'exercise': '42/c/c00/ex00', 'result': 'passed', 'checks': [], 'isolation': 'local'}
        with tempfile.TemporaryDirectory() as d:
            mod_dir = Path(d) / 'c00' / 'ex00'
            mod_dir.mkdir(parents=True)
            (mod_dir / 'ft_putchar.c').write_text('void ft_putchar(char c) { (void)c; }\n')
            with patch('moulinette.cli.check_ex00', return_value=fake), contextlib.redirect_stdout(out):
                rc = cli.main(['check', d, '--module', 'c00', '--unsafe-local', '--no-history', '--json'])
            self.assertEqual(rc, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload['summary']['passed'], 1)
            calls = []
            def step_check(*a, **kw):
                calls.append(1)
                (mod_dir / 'ft_putchar.c').write_text(f'/* {len(calls)} */\n')
                return fake
            with patch('moulinette.cli.check_ex00', side_effect=step_check), contextlib.redirect_stdout(io.StringIO()):
                rc_w = cli.main(['check', str(mod_dir), '--unsafe-local', '--no-history', '--watch', '--watch-interval', '0.05', '--max-iterations', '2'])
            self.assertEqual(rc_w, 0)
            self.assertEqual(len(calls), 2)

    def test_memguard_catches_overflow_ro_mutation_and_list_leak_or_uaf(self):
        import shutil
        from moulinette.checker import check_exercise
        if not shutil.which('cc') or not shutil.which('nm') or not shutil.which('norminette'):
            self.skipTest('cc, nm et norminette requis')
        # 1. Reference c07/ex00 and c12/ex06 pass with guard pages and leak tracking
        ref_dup = check_exercise(ROOT / 'exemples' / 'c07' / 'ex00', 'c07/ex00', sandbox=False)
        self.assertEqual(ref_dup['result'], 'passed', ref_dup)
        ref_clr = check_exercise(ROOT / 'exemples' / 'c12' / 'ex06', 'c12/ex06', sandbox=False)
        self.assertEqual(ref_clr['result'], 'passed', ref_clr)
        # 2. Off-by-one malloc(len) without +1 in ft_strdup hits PROT_NONE guard page
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'ft_strdup.c').write_text(
                '#include <stdlib.h>\n'
                'char\t*ft_strdup(char *src)\n{\n\tint\t\ti;\n\tchar\t*p;\n\n'
                '\ti = 0;\n\twhile (src[i])\n\t\ti++;\n'
                '\tp = malloc(i);\n\tif (!p)\n\t\treturn (0);\n'
                '\ti = 0;\n\twhile (src[i])\n\t{\n\t\tp[i] = src[i];\n\t\ti++;\n\t}\n'
                '\tp[i] = 0;\n\treturn (p);\n}\n'
            )
            bad_dup = check_exercise(p, 'c07/ex00', sandbox=False)
        self.assertEqual(bad_dup['result'], 'failed')
        # 3. ft_list_clear that calls callback without freeing the t_list node is caught by ml_unfreed_count()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            shutil.copyfile(ROOT / 'exemples' / 'c12' / 'ex06' / 'ft_list.h', p / 'ft_list.h')
            (p / 'ft_list_clear.c').write_text(
                '#include "ft_list.h"\n'
                'void\tft_list_clear(t_list *p, void (*f)(void *))\n{\n'
                '\twhile (p)\n\t{\n\t\tf(p->data);\n\t\tp = p->next;\n\t}\n}\n'
            )
            bad_clr = check_exercise(p, 'c12/ex06', sandbox=False)
        self.assertEqual(bad_clr['result'], 'failed')

    def test_recursion_loop_keyword_hint_pipeline_and_parallel_jobs(self):
        import contextlib, io
        from moulinette import cli
        from moulinette.recursion_hint import recursion_hint
        from moulinette.pipeline import build_report, classify_external_symbols, parse_nm_undefined
        # 1. Iterative keyword inside recursive target function is flagged indicatively
        msg = recursion_hint(
            'c05/ex01',
            'int ft_recursive_factorial(int n) { while (n > 1) return ft_recursive_factorial(n - 1); return 1; }'
        )
        self.assertIn('while', msg)
        self.assertIn('cycle possible', msg)
        # 2. Shared pipeline helpers
        self.assertEqual(parse_nm_undefined(b'                 U write\n'), ['write'])
        self.assertIsNone(parse_nm_undefined(b'                 U write@GLIBC_2.2.5\n'))
        prohibited, canaries = classify_external_symbols(['write', 'printf', '__stack_chk_fail'], {'write'})
        self.assertEqual(prohibited, ['printf'])
        self.assertEqual(canaries, {'__stack_chk_fail'})
        rep = build_report('c00/ex00', {'subject_version': '8'}, False, [{'status': 'pass'}])
        self.assertEqual(rep['result'], 'passed')
        # 3. Parallel --jobs 2 on --module
        out = io.StringIO()
        fake = {'exercise': '42/c/c00/ex00', 'result': 'passed', 'checks': [], 'isolation': 'local'}
        with tempfile.TemporaryDirectory() as d:
            for sub, fn in (('ex00', 'ft_putchar.c'), ('ex01', 'ft_print_alphabet.c')):
                ex_dir = Path(d) / 'c00' / sub
                ex_dir.mkdir(parents=True)
                (ex_dir / fn).write_text('void f(void) {}\n')
            with patch('moulinette.cli.check_ex00', return_value=fake), \
                 patch('moulinette.cli.check_ex01', return_value=fake), \
                 contextlib.redirect_stdout(out):
                rc = cli.main(['check', d, '--module', 'c00', '--jobs', '2', '--unsafe-local', '--no-history', '--json'])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue())['summary']['passed'], 2)

    def test_direct_c_file_path_in_mixed_folder_and_student_main(self):
        import contextlib, io, shutil
        from moulinette import cli
        from moulinette.cli import detect_exercise
        if not shutil.which('cc') or not shutil.which('nm') or not shutil.which('norminette'):
            self.skipTest('cc, nm et norminette requis')
        with tempfile.TemporaryDirectory() as d:
            mixed = Path(d)
            (mixed / 'ft_print_alphabet.c').write_text('void ft_print_alphabet(void) {}\n')
            (mixed / 'compil').write_bytes(b'\x7fELF')
            target = mixed / 'ft_is_negative.c'
            target.write_text(
                '#include <unistd.h>\n\n'
                'void\tft_is_negative(int n)\n{\n\tif (n >= 0)\n\t\twrite(1, "P", 1);\n\telse\n\t\twrite(1, "N", 1);\n}\n\n'
                'int\tmain(void)\n{\n\tft_is_negative(-3);\n\treturn (0);\n}\n'
            )
            ex_id, err = detect_exercise(str(target))
            self.assertEqual((ex_id, err), ('c00/ex04', None))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cli.main(['check', str(target), '--unsafe-local', '--no-history', '--json'])
            self.assertEqual(rc, 0)
            rep = json.loads(buf.getvalue())
            self.assertEqual(rep['exercise'], '42/c/c00/ex04')
            self.assertEqual(rep['result'], 'passed')
            self.assertTrue(any(c['name'] == 'Adaptation compilation' and 'main()' in c['message'] for c in rep['checks']))


if __name__ == '__main__':
    unittest.main()
