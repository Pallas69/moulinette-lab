"""Essai léger hors ligne de l'atome avec historique synthétique, sans données personnelles.
Nécessite Playwright et Chromium déjà installés ; aucune installation réseau.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moulinette.dashboard import render_dashboard
from moulinette.exercise_catalog import EXERCISES
from playwright.sync_api import sync_playwright


def row(ex, result):
    return {'exercise': ex, 'result': result, 'source_label': 'exemple',
            'created_at': '2026-01-01T10:20:00', 'isolation': 'exemple', 'checks': []}


def html_page(rows):
    history = {'count': len(rows), 'recent': rows[:50], 'latest': rows}
    with patch('moulinette.dashboard.read_unlocked_piscines', return_value={'c','cpp','py'}):
        html = render_dashboard(history)
    # Instrumentation du seul HTML de test : aucun changement de l'interface livrée.
    target = "const atomState = {protons: 0, neutrons: 0, electrons: 0, results: [], orbits: [], nucleons: [], stars: []};"
    assert html.count(target) == 1
    return html.replace(target, target + ' window.__testAtomState = atomState;')


def state(page):
    return page.evaluate('''() => ({p: __testAtomState.protons, n: __testAtomState.neutrons,
      e: __testAtomState.electrons, renderedP: __testAtomState.nucleons.filter(n => n.isProton).length,
      renderedN: __testAtomState.nucleons.filter(n => !n.isProton).length,
      renderedE: __testAtomState.orbits.reduce((a,o) => a + o.particleCount, 0),
      orbits: __testAtomState.orbits.length,
      each: __testAtomState.orbits.map(o => [o.particleCount, o.particles.length]),
      blues: __testAtomState.orbits.flatMap(o => o.particles).filter(x => x === 'passed').length,
      reds: __testAtomState.orbits.flatMap(o => o.particles).filter(x => x === 'failed').length,
      speeds: __testAtomState.orbits.map(o => o.speed)})''')


def check(page, p, n, e):
    s = state(page)
    assert (s['p'], s['n'], s['e']) == (p, n, e), s
    assert (s['renderedP'], s['renderedN'], s['renderedE']) == (0, 0, p+n), s
    assert (s['blues'], s['reds']) == (p, n), s
    for got, expected in zip(s['speeds'], [0.33, -0.405, 0.48]):
        assert abs(got - expected) < 1e-9, s
    assert s['orbits'] == p+n, s
    assert all(pair == [1, 1] for pair in s['each']), s
    assert page.locator('#hero-art').get_attribute('data-animated-orbits') == str(p+n)
    assert page.locator('#hero-art').get_attribute('data-animated-electrons') == str(p+n)

rows = [row('c00/ex00','passed'), row('c00/ex01','failed'), row('c00/ex02','incomplete'),
        row('c01/ex00','passed'), row('cpp00/ex00','failed'), row('py00/ex00','passed')]
with tempfile.TemporaryDirectory(prefix='moulinette-atom-test-') as d, sync_playwright() as p:
    pagefile = Path(d) / 'dashboard.html'
    pagefile.write_text(html_page(rows), encoding='utf-8')
    args = {'headless': True, 'args': ['--no-sandbox']}
    if os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
        args['executable_path'] = os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
    browser = p.chromium.launch(**args)
    for reduced in ('no-preference', 'reduce'):
        context = browser.new_context(reduced_motion=reduced, viewport={'width': 1100, 'height': 800})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(pagefile.as_uri(), wait_until='load')
        page.locator('[data-piscine-select="c"]').click()
        check(page, 2, 1, 109)
        assert page.locator('#atom-canvas').is_visible()
        canvas = page.locator('#atom-canvas').bounding_box()
        card = page.locator('#progress-card').bounding_box()
        assert abs((canvas['x'] + canvas['width']/2) - (card['x'] + card['width']/2)) < 2
        assert abs((canvas['y'] + canvas['height']/2) - (card['y'] + card['height']/2)) < 2
        for text in ('Protons (Réussis)', 'Neutrons (À revoir)', 'Électrons (Total)', 'Analogie visuelle'):
            assert text not in page.locator('body').inner_text()
        page.set_viewport_size({'width': 390, 'height': 844})
        canvas = page.locator('#atom-canvas').bounding_box()
        card = page.locator('#progress-card').bounding_box()
        assert abs((canvas['x'] + canvas['width']/2) - (card['x'] + card['width']/2)) < 2
        assert abs((canvas['y'] + canvas['height']/2) - (card['y'] + card['height']/2)) < 2
        page.set_viewport_size({'width': 1100, 'height': 800})
        page.select_option('#exercise-module', 'c00')
        check(page, 1, 1, 9)
        assert page.locator('#hero-art').get_attribute('data-atom-scope') == 'c00'
        page.fill('#exercise-search', 'ex00')
        check(page, 1, 1, 9)  # la recherche n'altère pas le périmètre
        page.select_option('#exercise-module', 'c01')
        check(page, 1, 0, 9)
        page.select_option('#exercise-module', 'c02')
        check(page, 0, 0, 13)
        page.select_option('#exercise-module', '')
        check(page, 2, 1, 109)
        page.locator('[data-piscine-select="cpp"]').click()
        check(page, 0, 1, 45)
        page.select_option('#exercise-module', 'cpp00')
        check(page, 0, 1, 3)
        page.locator('[data-piscine-select="py"]').click()
        check(page, 1, 0, 36)
        page.select_option('#exercise-module', 'py00')
        check(page, 1, 0, 11)
        assert not errors, errors
        context.close()
    # Aucun essai enregistré, et non un simple filtre vide.
    empty = Path(d) / 'empty-dashboard.html'; empty.write_text(html_page([]), encoding='utf-8')
    context = browser.new_context(reduced_motion='reduce')
    page = context.new_page(); page.goto(empty.as_uri())
    page.locator('[data-piscine-select="c"]').click(); check(page, 0, 0, 109)
    assert page.locator('#atom-svg .atom-shell').count() == 0
    assert page.locator('#atom-svg .atom-electron').count() == 0
    context.close()
    # Repli SVG 2D si Canvas ne fournit pas de contexte : comptes et filtres restent corrects.
    context = browser.new_context(reduced_motion='reduce')
    context.add_init_script("""(() => { const old = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(...args) {
        return this.id === 'atom-canvas' ? null : old.apply(this,args);
      }; })();""")
    page = context.new_page(); page.goto(pagefile.as_uri())
    page.locator('[data-piscine-select="c"]').click()
    assert page.locator('#atom-svg .atom-shell').count() == 3
    assert page.locator('#atom-svg .atom-electron').count() == 3
    assert page.locator('#atom-svg circle[fill="#3cbbff"]').count() == 2
    assert page.locator('#atom-svg circle[fill="#ff5f70"]').count() == 1
    page.select_option('#exercise-module','c02')
    assert page.locator('#atom-svg .atom-shell').count() == 0
    context.close()
    # État maximal et régression lors d'une régénération de la page.
    context = browser.new_context(reduced_motion='reduce')
    page = context.new_page()
    allpass = [row(ex, 'passed') for ex in EXERCISES]
    pagefile.write_text(html_page(allpass), encoding='utf-8')
    page.goto(pagefile.as_uri()); page.locator('[data-piscine-select="c"]').click(); check(page, 109, 0, 109)
    allpass[0]['result'] = 'failed'
    allpass[1]['result'] = 'incomplete'
    pagefile.write_text(html_page(allpass), encoding='utf-8')
    page.reload(); page.locator('[data-piscine-select="c"]').click(); check(page, 107, 1, 109)
    context.close()
    browser.close()
print('Atome 3D : une orbite par électron, couleurs, vitesse x1,5, périmètre et mouvement réduit : OK')
