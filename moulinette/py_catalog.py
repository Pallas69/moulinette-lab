"""Catalogue interne de la Piscine Python (Modules 00 à 04, 36 exercices)."""


def _pspec(module, ex, title, source, required_files, test_script, **extra):
    d = {
        "piscine": "py",
        "module": module,
        "exercise": f"{module}/{ex}",
        "title": title,
        "source": source,
        "required_files": tuple(required_files),
        "test_script": test_script,
        "subject_version": "1.0",
        "required_modules": (),
        "forbidden_calls": (),
        "forbidden_imports": (),
        "forbid_while": False,
    }
    d.update(extra)
    return d


PY_EXERCISES = {
    # Module 00 (11 exercices : ex00 à ex10)
    "py00/ex00": _pspec(
        "py00", "ex00", "$PATH", "answers.txt", ("answers.txt", "requirements.txt"),
        r'''from pathlib import Path
txt = Path("answers.txt").read_text(encoding="utf-8").lower()
for token in ("list", "show", "numpy", "freeze"):
    assert token in txt, f"Commande ou terme attendu absent de answers.txt : {token}"
assert Path("requirements.txt").is_file(), "requirements.txt absent"
print("OK")
''',
    ),
    "py00/ex01": _pspec(
        "py00", "ex01", "Rev Alpha", "exec.py", ("exec.py",),
        r'''import subprocess, sys
r1 = subprocess.run([sys.executable, "exec.py", "Hello World!"], capture_output=True, text=True, check=True)
assert r1.stdout == "!DLROw OLLEh\n", f"Obtenu : {r1.stdout!r}"
r2 = subprocess.run([sys.executable, "exec.py", "Hello", "my Friend"], capture_output=True, text=True, check=True)
assert r2.stdout == "DNEIRf YM OLLEh\n", f"Obtenu : {r2.stdout!r}"
r3 = subprocess.run([sys.executable, "exec.py"], capture_output=True, text=True, check=True)
assert r3.stdout == "", f"Sans argument attendu vide, obtenu : {r3.stdout!r}"
print("OK")
''',
    ),
    "py00/ex02": _pspec(
        "py00", "ex02", "Odd or Even", "whois.py", ("whois.py",),
        r'''import subprocess, sys
for arg, exp in [("12", "I'm Even.\n"), ("3", "I'm Odd.\n"), ("0", "I'm Zero.\n"), ("Hello", "ERROR\n")]:
    r = subprocess.run([sys.executable, "whois.py", arg], capture_output=True, text=True)
    assert r.stdout == exp, f"Pour {arg}: attendu {exp!r}, obtenu {r.stdout!r}"
r_many = subprocess.run([sys.executable, "whois.py", "1", "2"], capture_output=True, text=True)
assert "ERROR" in r_many.stdout, f"Attendu ERROR pour 2 args, obtenu {r_many.stdout!r}"
print("OK")
''',
    ),
    "py00/ex03": _pspec(
        "py00", "ex03", "Text Analyzer", "count.py", ("count.py",),
        r'''import io, contextlib
from count import text_analyzer
assert text_analyzer.__doc__ and len(text_analyzer.__doc__.strip()) > 5, "Docstring manquante sur text_analyzer"
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    text_analyzer("Python 2.0, released 2000, introduced features like List comprehensions and a garbage collection system capable of collecting reference cycles.")
out = buf.getvalue()
for piece in ("143", "2 upper", "113 lower", "4 punctuation", "18 space"):
    assert piece in out, f"Attendu {piece!r} dans {out!r}"
print("OK")
''',
    ),
    "py00/ex04": _pspec(
        "py00", "ex04", "Elementary operations", "operations.py", ("operations.py",),
        r'''import subprocess, sys
r = subprocess.run([sys.executable, "operations.py", "10", "3"], capture_output=True, text=True)
for expected in ("13", "7", "30", "3.333", "1"):
    assert expected in r.stdout, f"Attendu {expected} dans {r.stdout!r}"
rz = subprocess.run([sys.executable, "operations.py", "42", "0"], capture_output=True, text=True)
assert "ERROR (div by zero)" in rz.stdout and "ERROR (modulo by zero)" in rz.stdout, f"Obtenu : {rz.stdout!r}"
print("OK")
''',
    ),
    "py00/ex05": _pspec(
        "py00", "ex05", "Formatting (Katas)", "kata00.py",
        ("kata00.py", "kata01.py", "kata02.py", "kata03.py", "kata04.py"),
        r'''import subprocess, sys
r0 = subprocess.run([sys.executable, "kata00.py"], capture_output=True, text=True, check=True)
assert r0.stdout.strip() == "The 3 numbers are: 19, 42, 21", f"kata00: {r0.stdout!r}"
r1 = subprocess.run([sys.executable, "kata01.py"], capture_output=True, text=True, check=True)
assert "Python was created by Guido van Rossum" in r1.stdout, f"kata01: {r1.stdout!r}"
r2 = subprocess.run([sys.executable, "kata02.py"], capture_output=True, text=True, check=True)
assert r2.stdout.strip() == "09/25/2019 03:30", f"kata02: {r2.stdout!r}"
r3 = subprocess.run([sys.executable, "kata03.py"], capture_output=True, text=True, check=True)
assert r3.stdout == "-" * 26 + "The right format" and len(r3.stdout) == 42, f"kata03: {r3.stdout!r}"
r4 = subprocess.run([sys.executable, "kata04.py"], capture_output=True, text=True, check=True)
assert r4.stdout.strip() == "module_00, ex_04 : 132.42, 1.00e+04, 1.23e+04", f"kata04: {r4.stdout!r}"
print("OK")
''',
    ),
    "py00/ex06": _pspec(
        "py00", "ex06", "Cooking / Cookbook", "recipe.py", ("recipe.py",),
        r'''import subprocess, sys
import recipe
assert hasattr(recipe, "cookbook") and isinstance(recipe.cookbook, dict), "Dictionnaire cookbook manquant"
for k in ("sandwich", "cake", "salad"):
    assert k in recipe.cookbook, f"Recette {k} absente de cookbook"
r = subprocess.run([sys.executable, "recipe.py"], input="4\n5\n", capture_output=True, text=True, timeout=3)
assert r.returncode == 0 and ("sandwich" in r.stdout.lower() or "cookbook" in r.stdout.lower()), f"Sortie menu : {r.stdout!r}"
print("OK")
''',
    ),
    "py00/ex07": _pspec(
        "py00", "ex07", "Filterwords", "filterwords.py", ("filterwords.py",),
        r'''import subprocess, sys
r1 = subprocess.run([sys.executable, "filterwords.py", "Hello, my friend", "3"], capture_output=True, text=True)
assert r1.stdout.strip() == "['Hello', 'friend']", f"Obtenu : {r1.stdout!r}"
r2 = subprocess.run([sys.executable, "filterwords.py", "300", "3"], capture_output=True, text=True)
assert r2.stdout.strip() in ("[]", "ERROR"), f"Obtenu : {r2.stdout!r}"
r3 = subprocess.run([sys.executable, "filterwords.py", "Hello", "not_an_int"], capture_output=True, text=True)
assert "ERROR" in r3.stdout, f"Attendu ERROR, obtenu : {r3.stdout!r}"
print("OK")
''',
        forbidden_calls=("filter",),
    ),
    "py00/ex08": _pspec(
        "py00", "ex08", "Morse code (SOS)", "sos.py", ("sos.py",),
        r'''import subprocess, sys
r1 = subprocess.run([sys.executable, "sos.py", "SOS"], capture_output=True, text=True)
assert r1.stdout.strip() == "... --- ...", f"Obtenu : {r1.stdout!r}"
r2 = subprocess.run([sys.executable, "sos.py", "SOS!"], capture_output=True, text=True)
assert "ERROR" in r2.stdout, f"Attendu ERROR sur '!', obtenu : {r2.stdout!r}"
print("OK")
''',
    ),
    "py00/ex09": _pspec(
        "py00", "ex09", "Guessing game", "guess.py", ("guess.py",),
        r'''import subprocess, sys
r = subprocess.run([sys.executable, "guess.py"], input="exit\n", capture_output=True, text=True, timeout=3)
assert r.returncode == 0 and "Goodbye!" in r.stdout, f"Obtenu : {r.stdout!r}"
print("OK")
''',
    ),
    "py00/ex10": _pspec(
        "py00", "ex10", "Loading bar!", "loading.py", ("loading.py",),
        r'''import inspect
from loading import ft_progress
assert inspect.isgeneratorfunction(ft_progress), "ft_progress doit être un générateur utilisant yield"
res = list(ft_progress(range(10)))
assert res == list(range(10)), f"Attendu 0..9, obtenu {res}"
print("OK")
''',
        forbidden_imports=("tqdm",),
    ),

    # Module 01 (6 exercices : ex00 à ex05)
    "py01/ex00": _pspec(
        "py01", "ex00", "Book and Recipe", "book.py", ("book.py", "recipe.py", "test.py"),
        r'''from recipe import Recipe
from book import Book
r = Recipe("Tourte", 3, 25, ["pate", "pommes"], "Une bonne tourte", "dessert")
assert "Tourte" in str(r)
b = Book("MonLivre")
b.add_recipe(r)
assert b.get_recipe_by_name("Tourte") == r
assert r in b.get_recipes_by_types("dessert")
print("OK")
''',
    ),
    "py01/ex01": _pspec(
        "py01", "ex01", "Family Tree (GotCharacter / Stark)", "game.py", ("game.py",),
        r'''import io, contextlib
from game import GotCharacter, Stark
arya = Stark("Arya")
assert isinstance(arya, GotCharacter)
assert arya.first_name == "Arya" and arya.is_alive is True
assert arya.family_name == "Stark" and arya.house_words == "Winter is Coming"
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    arya.print_house_words()
assert buf.getvalue().strip() == "Winter is Coming"
arya.die()
assert arya.is_alive is False
print("OK")
''',
    ),
    "py01/ex02": _pspec(
        "py01", "ex02", "The Vector", "vector.py", ("vector.py", "test.py"),
        r'''from vector import Vector
v1 = Vector([[0.0], [1.0], [2.0], [3.0]])
assert v1.shape == (4, 1)
v2 = v1 * 5
assert v2.values == [[0.0], [5.0], [10.0], [15.0]]
vt = v1.T()
assert vt.shape == (1, 4)
v_range = Vector((10, 13))
assert v_range.values == [[10.0], [11.0], [12.0]]
assert v1.dot(v1) == 14.0
print("OK")
''',
        forbidden_imports=("numpy",),
    ),
    "py01/ex03": _pspec(
        "py01", "ex03", "Generator", "generator.py", ("generator.py",),
        r'''import inspect
from generator import generator
assert inspect.isgeneratorfunction(generator), "generator doit utiliser yield"
txt = "Le Lorem Ipsum est simplement du faux texte."
assert list(generator(txt, sep=" ")) == ["Le", "Lorem", "Ipsum", "est", "simplement", "du", "faux", "texte."]
assert list(generator(txt, sep=" ", option="ordered")) == ["Ipsum", "Le", "Lorem", "du", "est", "faux", "simplement", "texte."]
assert list(generator("a b a c b", sep=" ", option="unique")) == ["a", "b", "c"]
assert list(generator(1.0, sep=".")) == ["ERROR"]
print("OK")
''',
        forbidden_calls=("shuffle", "sample"),
    ),
    "py01/ex04": _pspec(
        "py01", "ex04", "Evaluator", "eval.py", ("eval.py",),
        r'''from eval import Evaluator
words = ["Le", "Lorem", "Ipsum", "est", "simple"]
coefs = [1.0, 2.0, 1.0, 4.0, 0.5]
assert Evaluator.zip_evaluate(coefs, words) == 32.0
assert Evaluator.enumerate_evaluate(coefs, words) == 32.0
assert Evaluator.zip_evaluate([1.0], words) == -1
assert Evaluator.enumerate_evaluate([1.0], words) == -1
print("OK")
''',
        forbid_while=True,
    ),
    "py01/ex05": _pspec(
        "py01", "ex05", "The Bank", "the_bank.py", ("the_bank.py",),
        r'''from the_bank import Account, Bank
bank = Bank()
a1 = Account("William John", zip="100-064", value=6460.0, ref="58ba2b9954cd278eda8a84147ca73c87", info=None)
a2 = Account("Jane", zip="911-745", value=1000.0, ref="1044618427ff2782f0bbece0abd05f31", info=None)
bank.add(a1)
bank.add(a2)
assert bank.transfer("William John", "Jane", 500.0) is True
assert a2.value == 1500.0
corrupted = Account("Bob", zip="123", value=100.0, b_bad=1)
bank.add(corrupted)
assert bank.transfer("William John", "Bob", 10.0) is False
assert bank.fix_account("Bob") is True
assert bank.transfer("William John", "Bob", 10.0) is True
print("OK")
''',
    ),

    # Module 02 (6 exercices : ex00 à ex05)
    "py02/ex00": _pspec(
        "py02", "ex00", "Map, Filter, Reduce", "ft_map.py",
        ("ft_map.py", "ft_filter.py", "ft_reduce.py"),
        r'''from ft_map import ft_map
from ft_filter import ft_filter
from ft_reduce import ft_reduce
x = [1, 2, 3, 4, 5]
assert list(ft_map(lambda t: t + 1, x)) == [2, 3, 4, 5, 6]
assert list(ft_filter(lambda t: not (t % 2), x)) == [2, 4]
assert ft_reduce(lambda u, v: u + v, ["H", "e", "l", "l", "o"]) == "Hello"
print("OK")
''',
        forbidden_calls=("map", "filter", "reduce"),
    ),
    "py02/ex01": _pspec(
        "py02", "ex01", "Args and Kwargs (what_are_the_vars)", "main.py", ("main.py",),
        r'''import main
obj = main.what_are_the_vars(7)
assert getattr(obj, "var_0") == 7
obj2 = main.what_are_the_vars(None, [])
assert getattr(obj2, "var_0") is None and getattr(obj2, "var_1") == []
obj3 = main.what_are_the_vars(42, a=10, var_0="world")
assert obj3 is None
print("OK")
''',
    ),
    "py02/ex02": _pspec(
        "py02", "ex02", "Logger (@log)", "logger.py", ("logger.py",),
        r'''from pathlib import Path
import logger
@logger.log
def sample_task(x):
    return x * 2
assert sample_task(21) == 42
log_path = Path("machine.log")
assert log_path.is_file(), "Fichier machine.log non créé par le décorateur @log"
content = log_path.read_text(encoding="utf-8")
assert "Running:" in content and "exec-time" in content, f"Format machine.log invalide : {content!r}"
print("OK")
''',
    ),
    "py02/ex03": _pspec(
        "py02", "ex03", "CsvReader (Context Manager)", "csvreader.py", ("csvreader.py",),
        r'''from pathlib import Path
from csvreader import CsvReader
Path("good.csv").write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
Path("bad.csv").write_text("name,age\nAlice,30\nBob\n", encoding="utf-8")
with CsvReader("good.csv", header=True) as f:
    assert f is not None
    assert f.getheader() == ["name", "age"]
    assert f.getdata() == [["Alice", "30"], ["Bob", "25"]]
with CsvReader("bad.csv", header=True) as f:
    assert f is None
with CsvReader("missing_file.csv") as f:
    assert f is None
print("OK")
''',
    ),
    "py02/ex04": _pspec(
        "py02", "ex04", "ai42 Package", "build.sh", ("build.sh",),
        r'''from pathlib import Path
import importlib
assert Path("build.sh").is_file()
mod_pb = importlib.import_module("ai42.progressbar")
mod_lg = importlib.import_module("ai42.logging.log")
assert hasattr(mod_pb, "ft_progress") or hasattr(mod_pb, "progressbar")
assert hasattr(mod_lg, "log")
print("OK")
''',
    ),
    "py02/ex05": _pspec(
        "py02", "ex05", "TinyStatistician", "TinyStatistician.py", ("TinyStatistician.py",),
        r'''from TinyStatistician import TinyStatistician
tstat = TinyStatistician()
a = [1, 42, 300, 10, 59]
assert tstat.mean([]) is None
assert abs(tstat.mean(a) - 82.4) < 1e-6
assert abs(tstat.median(a) - 42.0) < 1e-6
assert tstat.quartiles(a, 25) == 10.0 and tstat.quartiles(a, 75) == 59.0
assert abs(tstat.var(a) - 12279.439999999999) < 1e-3
assert abs(tstat.std(a) - 110.81263465868862) < 1e-3
print("OK")
''',
    ),

    # Module 03 (5 exercices : ex00 à ex04 — Numpy)
    "py03/ex00": _pspec(
        "py03", "ex00", "NumPyCreator", "NumPyCreator.py", ("NumPyCreator.py",),
        r'''import numpy as np
import NumPyCreator as mod
cls = getattr(mod, "NumPyCreator", None) or getattr(mod, "NumpyCreator", None)
assert cls is not None, "Classe NumPyCreator introuvable"
npc = cls()
a = npc.from_list([[1, 2, 3], [6, 3, 4]])
assert isinstance(a, np.ndarray) and a.shape == (2, 3)
assert npc.from_list([[1, 2, 3], [6, 4]]) is None
assert npc.from_list(((1, 2), (3, 4))) is None
assert isinstance(npc.from_tuple(("a", "b", "c")), np.ndarray)
assert npc.from_tuple(["a", "b"]) is None
assert np.array_equal(npc.from_iterable(range(5)), np.arange(5))
assert npc.from_shape((3, 5)).shape == (3, 5)
assert npc.random((3, 5)).shape == (3, 5)
assert np.array_equal(npc.identity(4), np.eye(4))
print("OK")
''',
        required_modules=("numpy",),
    ),
    "py03/ex01": _pspec(
        "py03", "ex01", "ImageProcessor", "ImageProcessor.py", ("ImageProcessor.py",),
        r'''import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
from ImageProcessor import ImageProcessor
imp = ImageProcessor()
assert imp.load("non_existing.png") is None
img = np.zeros((10, 12, 3), dtype=np.float32)
mpimg.imsave("sample_test.png", img)
loaded = imp.load("sample_test.png")
assert isinstance(loaded, np.ndarray) and loaded.shape[:2] == (10, 12)
print("OK")
''',
        required_modules=("numpy", "matplotlib"),
    ),
    "py03/ex02": _pspec(
        "py03", "ex02", "ScrapBooker", "ScrapBooker.py", ("ScrapBooker.py",),
        r'''import numpy as np
from ScrapBooker import ScrapBooker
spb = ScrapBooker()
arr1 = np.arange(0, 25).reshape(5, 5)
cropped = spb.crop(arr1, (3, 1), (1, 0))
assert np.array_equal(cropped, np.array([[5], [10], [15]]))
assert spb.crop(arr1, (10, 10), (0, 0)) is None
arr3 = np.array([[1, 2, 3], [1, 2, 3], [1, 2, 3]])
jux = spb.juxtapose(arr3, 2, 1)
assert jux.shape == (3, 6)
mos = spb.mosaic(arr3, (2, 2))
assert mos.shape == (6, 6)
print("OK")
''',
        required_modules=("numpy",),
    ),
    "py03/ex03": _pspec(
        "py03", "ex03", "ColorFilter", "ColorFilter.py", ("ColorFilter.py",),
        r'''import numpy as np
from ColorFilter import ColorFilter
cf = ColorFilter()
arr = np.linspace(0.0, 1.0, 12, dtype=np.float32).reshape(2, 2, 3)
inv = cf.invert(arr)
assert isinstance(inv, np.ndarray) and np.allclose(inv, 1.0 - arr)
b = cf.to_blue(arr)
assert b.shape == arr.shape and np.all(b[:, :, :2] == 0)
g = cf.to_green(arr)
assert g.shape == arr.shape and np.all(g[:, :, 0] == 0) and np.all(g[:, :, 2] == 0)
r = cf.to_red(arr)
assert r.shape == arr.shape and np.all(r[:, :, 1:] == 0)
cel = cf.to_celluloid(arr)
assert isinstance(cel, np.ndarray) and cel.shape == arr.shape
gm = cf.to_grayscale(arr, "m")
assert isinstance(gm, np.ndarray) and gm.shape == arr.shape
print("OK")
''',
        required_modules=("numpy",),
    ),
    "py03/ex04": _pspec(
        "py03", "ex04", "K-means Clustering", "Kmeans.py", ("Kmeans.py",),
        r'''import numpy as np
from Kmeans import KmeansClustering
X = np.array([
    [1.0, 1.0, 1.0], [1.1, 0.9, 1.0],
    [10.0, 10.0, 10.0], [10.2, 9.8, 10.1],
], dtype=float)
km = KmeansClustering(max_iter=10, ncentroid=2)
km.fit(X)
preds = km.predict(X)
assert isinstance(preds, np.ndarray) and len(preds) == 4
print("OK")
''',
        required_modules=("numpy",),
    ),

    # Module 04 (8 exercices : ex00 à ex07 — Pandas)
    "py04/ex00": _pspec(
        "py04", "ex00", "FileLoader", "FileLoader.py", ("FileLoader.py",),
        r'''from pathlib import Path
import pandas as pd
from FileLoader import FileLoader
Path("sample.csv").write_text("Name,Sex,Age\nAlice,F,20\nBob,M,25\n", encoding="utf-8")
fl = FileLoader()
df = fl.load("sample.csv")
assert isinstance(df, pd.DataFrame) and df.shape == (2, 3)
fl.display(df, 1)
fl.display(df, -1)
print("OK")
''',
        required_modules=("pandas",),
    ),
    "py04/ex01": _pspec(
        "py04", "ex01", "YoungestFellah", "YoungestFellah.py", ("FileLoader.py", "YoungestFellah.py"),
        r'''import pandas as pd
from YoungestFellah import youngest_fellah
df = pd.DataFrame({
    "Name": ["A", "B", "C", "D"],
    "Sex": ["F", "F", "M", "M"],
    "Age": [13.0, 22.0, 14.0, 29.0],
    "Year": [2004, 2004, 2004, 2004],
})
res = youngest_fellah(df, 2004)
assert isinstance(res, dict) and 13.0 in res.values() and 14.0 in res.values()
print("OK")
''',
        required_modules=("pandas",),
    ),
    "py04/ex02": _pspec(
        "py04", "ex02", "ProportionBySport", "ProportionBySport.py", ("FileLoader.py", "ProportionBySport.py"),
        r'''import pandas as pd
from ProportionBySport import proportion_by_sport
df = pd.DataFrame({
    "ID": [1, 1, 2, 3, 4],
    "Sex": ["F", "F", "F", "F", "M"],
    "Year": [2004, 2004, 2004, 2004, 2004],
    "Sport": ["Tennis", "Tennis", "Basketball", "Swimming", "Tennis"],
})
p = proportion_by_sport(df, 2004, "Tennis", "F")
assert abs(p - (1.0 / 3.0)) < 1e-6
print("OK")
''',
        required_modules=("pandas",),
    ),
    "py04/ex03": _pspec(
        "py04", "ex03", "HowManyMedals", "HowManyMedals.py", ("FileLoader.py", "HowManyMedals.py"),
        r'''import pandas as pd
from HowManyMedals import how_many_medals
df = pd.DataFrame({
    "Name": ["Kjetil", "Kjetil", "Kjetil"],
    "Year": [1992, 1992, 1994],
    "Medal": ["Gold", "Bronze", None],
})
res = how_many_medals(df, "Kjetil")
assert res[1992] == {"G": 1, "S": 0, "B": 1}
assert res[1994] == {"G": 0, "S": 0, "B": 0}
print("OK")
''',
        required_modules=("pandas",),
    ),
    "py04/ex04": _pspec(
        "py04", "ex04", "SpatioTemporalData", "SpatioTemporalData.py", ("FileLoader.py", "SpatioTemporalData.py"),
        r'''import pandas as pd
from SpatioTemporalData import SpatioTemporalData
df = pd.DataFrame({
    "Year": [1896, 1900, 1924, 2004],
    "City": ["Athina", "Paris", "Paris", "Athina"],
})
sp = SpatioTemporalData(df)
assert sp.where(1896) == ["Athina"]
assert sorted(sp.when("Paris")) == [1900, 1924]
print("OK")
''',
        required_modules=("pandas",),
    ),
    "py04/ex05": _pspec(
        "py04", "ex05", "HowManyMedalsByCountry", "HowManyMedalsByCountry.py",
        ("FileLoader.py", "HowManyMedalsByCountry.py"),
        r'''import pandas as pd
from HowManyMedalsByCountry import how_many_medals_by_country
df = pd.DataFrame({
    "Team": ["France", "France", "France"],
    "Year": [2000, 2000, 2000],
    "Sport": ["Basketball", "Basketball", "Judo"],
    "Event": ["Men Basketball", "Men Basketball", "Judo 81kg"],
    "Medal": ["Silver", "Silver", "Gold"],
})
res = how_many_medals_by_country(df, "France")
assert res[2000]["G"] == 1 and res[2000]["S"] == 1 and res[2000]["B"] == 0
print("OK")
''',
        required_modules=("pandas",),
    ),
    "py04/ex06": _pspec(
        "py04", "ex06", "MyPlotLib", "MyPlotLib.py", ("MyPlotLib.py",),
        r'''import matplotlib
matplotlib.use("Agg")
import pandas as pd
from MyPlotLib import MyPlotLib
df = pd.DataFrame({"Height": [170.0, 180.0, 175.0], "Weight": [65.0, 80.0, 72.0]})
mpl = MyPlotLib()
for method in ("histogram", "density", "pair_plot", "box_plot"):
    assert hasattr(mpl, method), f"Méthode {method} absente de MyPlotLib"
mpl.histogram(df, ["Height", "Weight"])
mpl.box_plot(df, ["Height", "Weight"])
print("OK")
''',
        required_modules=("pandas", "matplotlib"),
    ),
    "py04/ex07": _pspec(
        "py04", "ex07", "Komparator", "Komparator.py", ("Komparator.py",),
        r'''import matplotlib
matplotlib.use("Agg")
import pandas as pd
from Komparator import Komparator
df = pd.DataFrame({"Sex": ["M", "F", "M", "F"], "Height": [180.0, 165.0, 175.0, 170.0]})
kmp = Komparator(df)
for method in ("compare_box_plots", "density", "compare_histograms"):
    assert hasattr(kmp, method), f"Méthode {method} absente de Komparator"
kmp.compare_box_plots("Sex", "Height")
kmp.compare_histograms("Sex", "Height")
print("OK")
''',
        required_modules=("pandas", "matplotlib"),
    ),
}
