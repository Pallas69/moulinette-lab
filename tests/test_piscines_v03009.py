"""Tests légers de la v0.30.09-dev : Piscines C++, Python, progression C->C++->Python et atome 3D."""
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette import cli
from moulinette.checker import check_exercise
from moulinette.dashboard import render_dashboard, write_dashboard
from moulinette.exercise_catalog import (
    ALL_EXERCISES,
    canonical_exercise,
    CPP_EXERCISES,
    EXERCISES,
    PISCINE_ORDER,
    PY_EXERCISES,
    piscine_of,
)
from moulinette.history import read_history, read_unlocked_piscines, store_attempt


class PiscinesV03009Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {"XDG_DATA_HOME": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)

    def test_catalog_counts_and_disambiguated_ids(self):
        self.assertEqual(len(EXERCISES), 109)
        self.assertEqual(len(CPP_EXERCISES), 45)
        self.assertEqual(len(PY_EXERCISES), 36)
        self.assertEqual(len(ALL_EXERCISES), 190)
        self.assertEqual(PISCINE_ORDER, ("c", "cpp", "py"))

        self.assertEqual(canonical_exercise("c00/ex00"), "c00/ex00")
        self.assertEqual(canonical_exercise("42/c/c00/ex00"), "c00/ex00")
        self.assertEqual(canonical_exercise("cpp00/ex00"), "cpp00/ex00")
        self.assertEqual(canonical_exercise("42/cpp/cpp00/ex00"), "cpp00/ex00")
        self.assertEqual(canonical_exercise("c++/cpp00/ex00"), "cpp00/ex00")
        self.assertEqual(canonical_exercise("py00/ex00"), "py00/ex00")
        self.assertEqual(canonical_exercise("42/py/py00/ex00"), "py00/ex00")
        self.assertEqual(canonical_exercise("python/py00/ex00"), "py00/ex00")

        self.assertEqual(piscine_of("c00/ex00"), "c")
        self.assertEqual(piscine_of("cpp00/ex00"), "cpp")
        self.assertEqual(piscine_of("py00/ex00"), "py")

    def test_cpp_exercises_pass_fail_constraints_and_missing_compiler(self):
        if not (shutil.which("clang++") or shutil.which("g++") or shutil.which("c++")):
            self.skipTest("Compilateur C++ requis")

        # 1. cpp00/ex00 Megaphone valide
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "Makefile").write_text(
                "NAME = megaphone\nCXX = clang++\nCXXFLAGS = -Wall -Wextra -Werror -std=c++98\n"
                "all: $(NAME)\n$(NAME): megaphone.cpp\n\t$(CXX) $(CXXFLAGS) megaphone.cpp -o $(NAME)\n"
                "clean:\n\trm -f *.o\nfclean: clean\n\trm -f $(NAME)\nre: fclean all\n",
                encoding="utf-8",
            )
            (p / "megaphone.cpp").write_text(
                "#include <iostream>\n#include <cctype>\n"
                "int main(int argc, char **argv) {\n"
                "    if (argc == 1) { std::cout << \"* LOUD AND UNBEARABLE FEEDBACK NOISE *\" << std::endl; return 0; }\n"
                "    for (int i = 1; i < argc; ++i)\n"
                "        for (int j = 0; argv[i][j]; ++j)\n"
                "            std::cout << (char)std::toupper((unsigned char)argv[i][j]);\n"
                "    std::cout << std::endl;\n"
                "    return 0;\n}\n",
                encoding="utf-8",
            )
            rep = check_exercise(p, "cpp00/ex00", sandbox=False)
            self.assertEqual(rep["result"], "passed", rep)
            self.assertEqual(rep["exercise"], "42/cpp/cpp00/ex00")

            # Interdiction de 'using namespace std;' et 'printf'
            (p / "megaphone.cpp").write_text(
                "#include <iostream>\n#include <cstdio>\nusing namespace std;\n"
                "int main() { printf(\"hi\\n\"); return 0; }\n",
                encoding="utf-8",
            )
            bad_rep = check_exercise(p, "cpp00/ex00", sandbox=False)
            self.assertEqual(bad_rep["result"], "failed")
            norm_msgs = " ".join(c["message"] for c in bad_rep["checks"] if c["name"] == "Norminette adaptée")
            self.assertIn("using namespace", norm_msgs)
            self.assertIn("printf", norm_msgs)

            # Indisponibilité du compilateur -> incomplete (jamais passed)
            with patch("moulinette.cpp_engine._find_cxx_compiler", return_value=(None, None, False)):
                (p / "megaphone.cpp").write_text(
                    "#include <iostream>\nint main() { return 0; }\n",
                    encoding="utf-8",
                )
                unav_rep = check_exercise(p, "cpp00/ex00", sandbox=False)
                self.assertEqual(unav_rep["result"], "incomplete")
                self.assertTrue(any(c["status"] == "unavailable" for c in unav_rep["checks"]))

        # 2. cpp07/ex02 Array<T> template et interdiction STL avant cpp08
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "Makefile").write_text("CXXFLAGS = -Wall -Wextra -Werror\nall:\n\t@true\n", encoding="utf-8")
            (p / "Array.hpp").write_text(
                "#ifndef ARRAY_HPP\n#define ARRAY_HPP\n#include <exception>\n"
                "template <typename T>\nclass Array {\n"
                "    T *_data; unsigned int _n;\npublic:\n"
                "    Array() : _data(0), _n(0) {}\n"
                "    Array(unsigned int n) : _data(new T[n]()), _n(n) {}\n"
                "    Array(Array const &o) : _data(new T[o._n]()), _n(o._n) { for (unsigned int i=0;i<_n;++i) _data[i]=o._data[i]; }\n"
                "    Array &operator=(Array const &o) { if (this!=&o){ delete[] _data; _n=o._n; _data=new T[_n](); for(unsigned int i=0;i<_n;++i) _data[i]=o._data[i]; } return *this; }\n"
                "    ~Array() { delete[] _data; }\n"
                "    unsigned int size() const { return _n; }\n"
                "    T &operator[](unsigned int i) { if (i >= _n) throw std::exception(); return _data[i]; }\n"
                "    T const &operator[](unsigned int i) const { if (i >= _n) throw std::exception(); return _data[i]; }\n"
                "};\n#endif\n",
                encoding="utf-8",
            )
            (p / "main.cpp").write_text("#include \"Array.hpp\"\nint main() { Array<int> a(2); return 0; }\n", encoding="utf-8")
            rep_arr = check_exercise(p, "cpp07/ex02", sandbox=False)
            self.assertEqual(rep_arr["result"], "passed", rep_arr)

            # Si <vector> est inclus dans cpp07/ex02 -> refusé
            (p / "main.cpp").write_text("#include <vector>\n#include \"Array.hpp\"\nint main() { return 0; }\n", encoding="utf-8")
            bad_stl = check_exercise(p, "cpp07/ex02", sandbox=False)
            self.assertEqual(bad_stl["result"], "failed")

        # 3. cpp08/ex01 Span (STL autorisée dans cpp08)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "span.hpp").write_text(
                "#ifndef SPAN_HPP\n#define SPAN_HPP\n#include <vector>\n#include <algorithm>\n#include <stdexcept>\n"
                "class Span {\n    unsigned int _n;\n    std::vector<int> _v;\npublic:\n"
                "    Span(unsigned int n = 0);\n    Span(Span const &o);\n    Span &operator=(Span const &o);\n    ~Span();\n"
                "    void addNumber(int x);\n    int shortestSpan() const;\n    int longestSpan() const;\n};\n#endif\n",
                encoding="utf-8",
            )
            (p / "span.cpp").write_text(
                "#include \"span.hpp\"\n"
                "Span::Span(unsigned int n) : _n(n) {}\n"
                "Span::Span(Span const &o) : _n(o._n), _v(o._v) {}\n"
                "Span &Span::operator=(Span const &o) { _n = o._n; _v = o._v; return *this; }\n"
                "Span::~Span() {}\n"
                "void Span::addNumber(int x) { if (_v.size() >= _n) throw std::runtime_error(\"full\"); _v.push_back(x); }\n"
                "int Span::shortestSpan() const {\n"
                "    if (_v.size() < 2) throw std::runtime_error(\"short\");\n"
                "    std::vector<int> s(_v); std::sort(s.begin(), s.end());\n"
                "    int best = s[1] - s[0];\n"
                "    for (size_t i = 1; i < s.size(); ++i) if (s[i] - s[i - 1] < best) best = s[i] - s[i - 1];\n"
                "    return best;\n}\n"
                "int Span::longestSpan() const {\n"
                "    if (_v.size() < 2) throw std::runtime_error(\"short\");\n"
                "    return *std::max_element(_v.begin(), _v.end()) - *std::min_element(_v.begin(), _v.end());\n}\n",
                encoding="utf-8",
            )
            (p / "main.cpp").write_text("#include \"span.hpp\"\nint main() { return 0; }\n", encoding="utf-8")
            rep_span = check_exercise(p, "cpp08/ex01", sandbox=False)
            self.assertEqual(rep_span["result"], "passed", rep_span)

    def test_python_exercises_pass_fail_ast_and_missing_libraries(self):
        # 1. py00/ex01 exec.py valide + rejet de eval()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "exec.py").write_text(
                "import sys\nif len(sys.argv) > 1:\n    print(' '.join(sys.argv[1:])[::-1].swapcase())\n",
                encoding="utf-8",
            )
            rep = check_exercise(p, "py00/ex01", sandbox=False)
            self.assertEqual(rep["result"], "passed", rep)
            self.assertEqual(rep["exercise"], "42/py/py00/ex01")

            (p / "exec.py").write_text("import sys\neval('1+1')\n", encoding="utf-8")
            bad_eval = check_exercise(p, "py00/ex01", sandbox=False)
            self.assertEqual(bad_eval["result"], "failed")
            self.assertIn("eval", bad_eval["checks"][1]["message"])

        # 2. py01/ex04 Evaluator (interdiction de while)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "eval.py").write_text(
                "class Evaluator:\n"
                "    @staticmethod\n"
                "    def zip_evaluate(coefs, words):\n"
                "        if len(coefs) != len(words): return -1\n"
                "        return sum(c * len(w) for c, w in zip(coefs, words))\n"
                "    @staticmethod\n"
                "    def enumerate_evaluate(coefs, words):\n"
                "        if len(coefs) != len(words): return -1\n"
                "        return sum(coefs[i] * len(w) for i, w in enumerate(words))\n",
                encoding="utf-8",
            )
            rep_ev = check_exercise(p, "py01/ex04", sandbox=False)
            self.assertEqual(rep_ev["result"], "passed", rep_ev)

            (p / "eval.py").write_text(
                "class Evaluator:\n    @staticmethod\n    def zip_evaluate(c, w):\n        while False: pass\n        return -1\n",
                encoding="utf-8",
            )
            bad_while = check_exercise(p, "py01/ex04", sandbox=False)
            self.assertEqual(bad_while["result"], "failed")
            self.assertIn("while", bad_while["checks"][1]["message"])

        # 3. py03/ex00 NumPyCreator : vérifier aussi l'absence de NumPy.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "NumPyCreator.py").write_text(
                "import numpy as np\n"
                "class NumPyCreator:\n"
                "    def from_list(self, lst, dtype=None):\n"
                "        if not isinstance(lst, list): return None\n"
                "        if any(isinstance(x, list) for x in lst):\n"
                "            if not all(isinstance(x, list) and len(x) == len(lst[0]) for x in lst): return None\n"
                "        return np.array(lst, dtype=dtype)\n"
                "    def from_tuple(self, tpl, dtype=None):\n"
                "        if not isinstance(tpl, tuple): return None\n"
                "        return np.array(tpl, dtype=dtype)\n"
                "    def from_iterable(self, itr, dtype=None):\n"
                "        return np.fromiter(itr, dtype=dtype or int)\n"
                "    def from_shape(self, shape, value=0, dtype=None):\n"
                "        return np.full(shape, value, dtype=dtype)\n"
                "    def random(self, shape):\n"
                "        return np.random.random(shape)\n"
                "    def identity(self, n, dtype=None):\n"
                "        return np.identity(n, dtype=dtype)\n",
                encoding="utf-8",
            )
            with patch('moulinette.py_engine._run_py', return_value=(1, b'', b'', False)):
                rep_np_missing = check_exercise(p, "py03/ex00", sandbox=False)
            self.assertEqual(rep_np_missing["result"], "incomplete", rep_np_missing)
            self.assertTrue(any(c["status"] == "unavailable" and "numpy" in c["message"]
                                for c in rep_np_missing["checks"]))

            from moulinette.py_engine import _run_py
            py_bin = shutil.which('python3')
            self.assertIsNotNone(py_bin, 'python3 requis pour ce test')
            probe, _, _, timed = _run_py([py_bin, '-B', '-c', 'import numpy'], p, 5,
                                         extra_pythonpath=os.environ.get('MOULINETTE_PY_EXTRA_PATH') or None)
            rep_np = check_exercise(p, "py03/ex00", sandbox=False)
            if probe == 0 and not timed:
                self.assertEqual(rep_np["result"], "passed", rep_np)
            else:
                self.assertEqual(rep_np["result"], "incomplete", rep_np)
                self.assertTrue(any(c["status"] == "unavailable" and "numpy" in c["message"]
                                    for c in rep_np["checks"]))

        # 4. py04/ex00 FileLoader : si pandas est absent -> 'incomplete' (status 'unavailable'), jamais 'passed'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "FileLoader.py").write_text(
                "import pandas as pd\n"
                "class FileLoader:\n"
                "    def load(self, path):\n"
                "        df = pd.read_csv(path)\n"
                "        print(f'Loading dataset of dimensions {df.shape[0]} x {df.shape[1]}')\n"
                "        return df\n"
                "    def display(self, df, n):\n"
                "        print(df.head(n) if n >= 0 else df.tail(-n))\n",
                encoding="utf-8",
            )
            # Ne pas supposer que pandas est absent de la machine de test.
            with patch('moulinette.py_engine._run_py', return_value=(1, b'', b'', False)):
                rep_pd = check_exercise(p, "py04/ex00", sandbox=False)
            self.assertEqual(rep_pd["result"], "incomplete", rep_pd)
            self.assertTrue(any(c["status"] == "unavailable" and "pandas" in c["message"] for c in rep_pd["checks"]))

            # Et avec un module pandas léger fourni via MOULINETTE_PY_EXTRA_PATH -> 'passed'
            with tempfile.TemporaryDirectory() as stub_dir:
                (Path(stub_dir) / "pandas.py").write_text(
                    "class DataFrame:\n"
                    "    def __init__(self, rows):\n"
                    "        self._rows = rows\n"
                    "        self.shape = (len(rows), len(rows[0]) if rows else 0)\n"
                    "    def head(self, n): return self._rows[:n]\n"
                    "    def tail(self, n): return self._rows[-n:]\n"
                    "def read_csv(path):\n"
                    "    lines = [l.split(',') for l in open(path, encoding='utf-8').read().strip().splitlines()]\n"
                    "    return DataFrame(lines[1:])\n",
                    encoding="utf-8",
                )
                with patch.dict(os.environ, {"MOULINETTE_PY_EXTRA_PATH": stub_dir}):
                    rep_pd_ok = check_exercise(p, "py04/ex00", sandbox=False)
                    self.assertEqual(rep_pd_ok["result"], "passed", rep_pd_ok)

    def test_progression_order_permanent_unlock_cli_early_checks_and_atom_counters(self):
        ok_check = [{"name": "Test", "status": "pass", "message": "ok"}]
        bad_check = [{"name": "Test", "status": "fail", "message": "ko"}]
        inc_check = [{"name": "Test", "status": "unavailable", "message": "missing"}]

        # 1. Correction CLI anticipée d'un exercice C++ et Python avant déblocage sur le dashboard
        store_attempt({"exercise": "42/cpp/cpp00/ex00", "result": "passed", "checks": ok_check, "isolation": "local"}, "/cli/megaphone")
        store_attempt({"exercise": "42/cpp/cpp00/ex01", "result": "failed", "checks": bad_check, "isolation": "local"}, "/cli/phonebook")
        store_attempt({"exercise": "42/py/py00/ex01", "result": "passed", "checks": ok_check, "isolation": "local"}, "/cli/exec")

        # 2. En Piscine C : 2 réussis (protons=2), 1 à revoir (neutrons=1), 1 incomplet (ignoré dans protons/neutrons)
        store_attempt({"exercise": "42/c/c00/ex00", "result": "passed", "checks": ok_check, "isolation": "local"}, "/c/ex00")
        store_attempt({"exercise": "42/c/c00/ex01", "result": "passed", "checks": ok_check, "isolation": "local"}, "/c/ex01")
        store_attempt({"exercise": "42/c/c00/ex02", "result": "failed", "checks": bad_check, "isolation": "local"}, "/c/ex02")
        store_attempt({"exercise": "42/c/c00/ex03", "result": "incomplete", "checks": inc_check, "isolation": "local"}, "/c/ex03")

        hist = read_history()
        unlocked = read_unlocked_piscines(hist)
        self.assertEqual(unlocked, {"c"})

        html_c = render_dashboard(hist)
        self.assertIn('data-active-piscine="c"', html_c)
        self.assertIn('data-protons="2"', html_c)
        self.assertIn('data-neutrons="1"', html_c)
        self.assertIn('data-electrons="109"', html_c)
        self.assertIn("2 exercices sur 109 réussis", html_c)
        self.assertIn('id="atom-canvas"', html_c)
        self.assertIn('id="atom-svg"', html_c)
        self.assertNotIn("Analogie visuelle", html_c)  # v0.31 : plus de légende textuelle sous l’atome

        # 3. Validation des 109 exercices de la Piscine C -> déblocage automatique de la Piscine C++
        for ex in sorted(EXERCISES):
            store_attempt({"exercise": "42/c/" + ex, "result": "passed", "checks": ok_check, "isolation": "local"}, "/c/" + ex)

        hist_cpp = read_history()
        unlocked_cpp = read_unlocked_piscines(hist_cpp)
        self.assertEqual(unlocked_cpp, {"c", "cpp"})

        html_cpp = render_dashboard(hist_cpp)
        # La case évolutive affiche désormais la Piscine C++ (avec l'état réel de cpp00/ex00 et cpp00/ex01 corrigés en CLI !)
        self.assertIn('data-active-piscine="cpp"', html_cpp)
        self.assertIn('data-protons="1"', html_cpp)
        self.assertIn('data-neutrons="1"', html_cpp)
        self.assertIn('data-electrons="45"', html_cpp)
        self.assertIn("1 exercice sur 45 réussis", html_cpp)
        self.assertIn("1 <span>/ 45</span>", html_cpp)

        # 4. Déblocage permanent : même si c00/ex00 repasse à 'failed' ('à revoir'), la Piscine C++ reste débloquée !
        store_attempt({"exercise": "42/c/c00/ex00", "result": "failed", "checks": bad_check, "isolation": "local"}, "/c/regression")
        hist_reg = read_history()
        self.assertEqual(read_unlocked_piscines(hist_reg), {"c", "cpp"})
        html_reg = render_dashboard(hist_reg)
        self.assertIn('data-active-piscine="cpp"', html_reg)

        # 5. Validation des 45 exercices de la Piscine C++ -> déblocage automatique de la Piscine Python (36 exercices)
        for ex in sorted(CPP_EXERCISES):
            store_attempt({"exercise": "42/cpp/" + ex, "result": "passed", "checks": ok_check, "isolation": "local"}, "/cpp/" + ex)

        hist_py = read_history()
        self.assertEqual(read_unlocked_piscines(hist_py), {"c", "cpp", "py"})
        html_py = render_dashboard(hist_py)
        self.assertIn('data-active-piscine="py"', html_py)
        self.assertIn('data-protons="1"', html_py)
        self.assertIn('data-neutrons="0"', html_py)
        self.assertIn('data-electrons="36"', html_py)
        self.assertIn("1 exercice sur 36 réussis", html_py)
        self.assertIn("1 <span>/ 36</span>", html_py)


if __name__ == "__main__":
    unittest.main()
