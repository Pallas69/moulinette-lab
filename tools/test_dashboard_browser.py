"""Essai navigateur optionnel (Playwright déjà installé, aucun réseau requis).

À lancer depuis la racine : python3 tools/test_dashboard_browser.py
PLAYWRIGHT_CHROMIUM_EXECUTABLE peut désigner un navigateur Chromium local.
Ce script ne fait pas partie de la suite unittest ordinaire.
"""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moulinette.dashboard import render_dashboard
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit('Playwright optionnel absent ; installer le navigateur de test séparément.')


def row(ex, result):
    return {'exercise': ex, 'result': result, 'source_label': 'exemple', 'created_at': '2026-01-01T10:20:00',
            'isolation': 'exemple', 'checks': [{'name': 'Compilation', 'status': 'pass', 'message': 'Exemple'}]}

r = [row('c00/ex00', 'passed'), row('c00/ex01', 'failed'), row('c02/ex00', 'incomplete')]
r[1]['checks'] = [{'name':'Compilation','status':'fail','message':"In function 'main':\nerror: unused variable 'alpha'\nIn function 'my_print_alpha':\nerror: control reaches end of non-void function"}]
previous = row('c00/ex01','passed')
history = {'count': 4, 'recent': r + [previous], 'latest': r}
with tempfile.TemporaryDirectory() as temp, sync_playwright() as p:
    path = Path(temp) / 'dashboard.html'
    path.write_text(render_dashboard(history), encoding='utf-8')
    launch_args = {'headless': True, 'args': ['--no-sandbox']}
    if os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
        launch_args['executable_path'] = os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
    browser = p.chromium.launch(**launch_args)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    errors, remote = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda request: remote.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
    page.goto(path.as_uri(), wait_until='load')
    assert page.locator('.hero #roastbox').count() == 1
    assert page.locator('.hero #humor').count() == 1
    assert 'Vos essais, vos progrès, votre rythme.' not in page.locator('body').inner_text()
    # Liens directs sans fenêtre ni scripts : vérifier les quatre téléchargements.
    assets = Path(__file__).resolve().parents[1] / 'moulinette/assets'
    for asset, filename in (('guide-utilisation','manuel-moulinette-lab'),('guide-style-c','guide-style-c-moulinette-lab')):
        for theme in ('blanc','ocean'):
            link = page.locator(f'a[data-document="{asset}"][data-theme="{theme}"]')
            assert link.is_visible()
            with page.expect_download() as pending:
                link.click()
            result=pending.value
            assert result.suggested_filename==filename+'-v0.32.8-'+theme+'.pdf'
            assert Path(result.path()).read_bytes()==(assets/(asset+'-'+theme+'.pdf')).read_bytes()
    assert page.locator('dialog').count()==0
    assert page.locator('.exercise').count() == 109
    assert page.locator('#theme').input_value() == 'aurora'
    assert page.locator('.exercise.ok-row').count() == 1
    assert page.locator('.exercise.bad-row').count() == 1
    assert page.locator('.exercise.pending-row').count() == 1
    assert page.locator('.exercise.neutral-row').count() == 106
    page.locator('.attempt summary').nth(1).click()
    assert 'La variable « alpha »' in page.locator('.attempt').nth(1).inner_text()
    assert 'void ft_print_alphabet(void);' in page.locator('.attempt').nth(1).inner_text()
    assert 'De réussi à échec : Compilation' in page.locator('.attempt').nth(1).inner_text()
    original = page.locator('body').evaluate('(e) => getComputedStyle(e).backgroundColor')
    badge_colors = [page.locator('.badge.' + c).first.evaluate('(e) => getComputedStyle(e).color') for c in ('ok', 'bad', 'pending', 'neutral')]
    assert len(set(badge_colors)) == 4
    page.select_option('#theme', 'ocean')
    assert page.locator('html').get_attribute('data-theme') == 'ocean'
    assert page.locator('body').evaluate('(e) => getComputedStyle(e).backgroundColor') != original
    assert [page.locator('.badge.' + c).first.evaluate('(e) => getComputedStyle(e).color') for c in ('ok', 'bad', 'pending', 'neutral')] == badge_colors
    page.reload(wait_until='load')
    assert page.locator('#theme').input_value() == 'ocean'
    assert page.locator('html').get_attribute('data-theme') == 'ocean'
    # Régénérer le même fichier puis l'ouvrir à nouveau ne doit pas perdre le thème.
    path.write_text(render_dashboard(history), encoding='utf-8')
    page.goto(path.as_uri(), wait_until='load')
    assert page.locator('html').get_attribute('data-theme') == 'ocean'
    page.select_option('#theme', 'random')
    for _ in range(6):
        previous = page.locator('html').get_attribute('data-theme')
        page.reload(wait_until='load')
        assert page.locator('#theme').input_value() == 'random'
        assert page.locator('html').get_attribute('data-theme') != previous
    page.select_option('#theme', 'forest')
    page.reload(wait_until='load')
    assert page.locator('#theme').input_value() == 'forest'
    assert page.locator('html').get_attribute('data-theme') == 'forest'
    page.select_option('#exercise-module', 'c12')
    assert page.locator('.exercise:visible').count() == 18
    page.fill('#exercise-search', 'ex08')
    assert page.locator('.exercise:visible').count() == 1
    assert 'c12/ex08' in page.locator('.exercise:visible').inner_text()
    page.fill('#exercise-search', 'aucun_exercice_comme_ca')
    assert page.locator('#no-results').is_visible()
    page.locator('.attempt summary').first.click()
    assert page.locator('.attempt').first.get_attribute('open') is not None
    page.locator('.humor-toggle').click()
    assert page.locator('#roastbox').is_hidden()
    page.reload(wait_until='load')
    assert page.locator('#roastbox').is_hidden()
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.locator('.guide-downloads a').count()==4
    for i in range(4): assert page.locator('.guide-downloads a').nth(i).is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
    assert not errors, errors
    assert not remote, remote
    context.close()
    # Les liens de téléchargement ne dépendent pas de JavaScript.
    nojs = browser.new_context(java_script_enabled=False)
    nojs_page = nojs.new_page(); nojs_page.goto(path.as_uri())
    for asset, filename in (('guide-utilisation','manuel-moulinette-lab'),('guide-style-c','guide-style-c-moulinette-lab')):
        for theme in ('blanc','ocean'):
            with nojs_page.expect_download() as pending:
                nojs_page.locator(f'a[data-document="{asset}"][data-theme="{theme}"]').click()
            result=pending.value
            assert result.suggested_filename==filename+'-v0.32.8-'+theme+'.pdf'
            assert Path(result.path()).read_bytes()==(assets/(asset+'-'+theme+'.pdf')).read_bytes()
    nojs.close()
    # Les navigateurs peuvent refuser l'accès au stockage : la page doit rester utilisable.
    blocked = browser.new_context()
    blocked.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('storage blocked') }})")
    badpage = blocked.new_page()
    badpage.goto(path.as_uri(), wait_until='load')
    assert 'indisponible' in badpage.locator('#theme-message').inner_text()
    badpage.select_option('#theme', 'ocean')
    assert badpage.locator('html').get_attribute('data-theme') == 'ocean'
    assert 'indisponible' in badpage.locator('#theme-message').inner_text()
    blocked.close()
    browser.close()
print('Navigateur : thèmes persistants/aléatoire, états, filtres, historique, humour, mobile, hors-ligne et stockage refusé : OK')
