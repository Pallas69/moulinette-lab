"""Essai léger hors ligne : interrupteur, intervalle d'humour et absence de constellation."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moulinette.dashboard import render_dashboard
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='ml-ui-test-') as tmp:
    path = Path(tmp) / 'dashboard.html'
    with patch('moulinette.dashboard.read_unlocked_piscines', return_value={'c'}):
        path.write_text(render_dashboard({'count':0, 'recent':[], 'latest':[]}), encoding='utf-8')
    with sync_playwright() as p:
        args = {'headless':True, 'args':['--no-sandbox']}
        if os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
            args['executable_path'] = os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
        browser = p.chromium.launch(**args)
        context = browser.new_context(viewport={'width': 1200, 'height': 800}, reduced_motion='reduce')
        context.add_init_script('''(() => { const old = window.setInterval; window.setInterval = function(fn,ms) {
          if (ms === 30000) { window.__testHumorTick = fn; window.__humorIntervalMs = ms; return 98765; }
          return old.apply(this,arguments); }; })();''')
        page = context.new_page(); errors=[]; remote=[]
        page.on('pageerror', lambda e:errors.append(str(e)))
        page.on('request', lambda r:remote.append(r.url) if r.url.startswith(('http:', 'https:')) else None)
        page.goto(path.as_uri(), wait_until='load')
        assert page.locator('#humor').is_checked()
        assert page.locator('#humor').get_attribute('role') == 'switch'
        assert page.evaluate('window.__humorIntervalMs') == 30000
        before = page.locator('#roast').inner_text()
        page.evaluate('window.__testHumorTick()')
        after = page.locator('#roast').inner_text()
        assert before != after
        page.locator('.humor-toggle').click()
        assert not page.locator('#humor').is_checked()
        assert page.locator('#roastbox').is_hidden()
        page.evaluate('window.__testHumorTick()')
        assert page.locator('#roast').text_content() == after
        page.reload(wait_until='load')
        assert not page.locator('#humor').is_checked()
        assert page.locator('#roastbox').is_hidden()
        page.locator('.humor-toggle').click()
        assert page.locator('#humor').is_checked() and page.locator('#roastbox').is_visible()
        before = page.locator('#roast').inner_text()
        page.locator('#next').click()
        assert before != page.locator('#roast').inner_text()
        assert page.locator('#bg-graph').count() == 0
        assert not errors, errors
        assert not remote, remote
        context.close()
        browser.close()
print('Humour : interrupteur, persistance, changement à 30 s et bouton manuel ; absence de constellation : OK')
