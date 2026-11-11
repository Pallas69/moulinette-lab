"""Vérifications des PDF livrés ; nécessite pypdf, dépendance optionnelle de maintenance."""
from pathlib import Path
import sys
from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
specs = [('manuel-utilisateur','guide-utilisation'),('guide-style-c','guide-style-c')]
for doc, asset in specs:
    texts=[]
    for theme in ('blanc','ocean'):
        path=root/'docs'/f'{doc}-v0.32.8-{theme}.pdf'
        embedded=root/'moulinette/assets'/f'{asset}-{theme}.pdf'
        assert path.read_bytes() == embedded.read_bytes()
        reader=PdfReader(path)
        assert not reader.is_encrypted and len(reader.pages)>1
        texts.append('\n'.join(page.extract_text() for page in reader.pages))
        assert '0.32.8' in texts[-1]
        assert b'LiberationSerif' in path.read_bytes() and b'JetBrainsMono' in path.read_bytes()
        for page in reader.pages:
            assert len(page.extract_text().strip()) > 100
    assert texts[0] == texts[1]
    if doc=='manuel-utilisateur':
        for term in ('moulinette reset','--watch-interval','--trust-github','--cgroup','--no-history','XDG_DATA_HOME','0.32.8.dev0','190','30 secondes','Python','C++'):
            assert term in texts[0], term
        assert 'constellation' not in texts[0].lower()
    else:
        for term in ('3.3.59','INVALID_HEADER','Norminette','récursivité','non officiels'):
            assert term in texts[0], term
    assert (root/'moulinette/assets'/f'{asset}.pdf').read_bytes() == (root/'moulinette/assets'/f'{asset}-ocean.pdf').read_bytes()
print('PDF : ouverture, variantes, textes, polices et fichiers embarqués : OK')
