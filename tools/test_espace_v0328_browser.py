"""Contrôle léger de l'espace du bandeau sur ordinateur et mobile."""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from moulinette.dashboard import render_dashboard
from playwright.sync_api import sync_playwright

rows=[{'exercise':'c00/ex00','result':'passed','source_label':'exemple','created_at':'2026-01-01T00:00:00','isolation':'fictif','checks':[]}]
with tempfile.TemporaryDirectory(prefix='ml-space-browser-') as temp, sync_playwright() as pw:
    path=Path(temp)/'dashboard.html';path.write_text(render_dashboard({'count':1,'latest':rows,'recent':rows}),encoding='utf-8')
    args={'headless':True,'args':['--no-sandbox']}
    if os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):args['executable_path']=os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
    browser=pw.chromium.launch(**args)
    for width,js in ((1440,True),(1100,True),(390,True),(320,True),(390,False)):
        ctx=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce',java_script_enabled=js)
        page=ctx.new_page();errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
        page.goto(path.as_uri(),wait_until='load')
        page.locator('.kicker').wait_for();page.evaluate('document.fonts.ready')
        guide=page.locator('.guide-downloads').bounding_box();message=page.locator('.theme-message').bounding_box();label=page.locator('.kicker').bounding_box();hero=page.locator('.hero').bounding_box();box=page.locator('#roastbox').bounding_box()
        gap=label['y']-(guide['y']+guide['height'])
        assert 0 <= gap <= 60,(width,js,gap)
        assert label['y'] >= message['y']+message['height']-1,(width,js)
        assert box['y'] >= label['y']+label['height']-1,(width,js)
        assert page.locator('a[data-document][data-theme]').count()==4
        # Débordements hérités à 1100 px (barre) et 320 px (SVG), inchangés.
        overflow = page.evaluate('document.documentElement.scrollWidth - window.innerWidth')
        assert overflow <= (30 if width == 320 else 14 if width == 1100 else 1),(width,js,overflow)
        assert not errors,errors
        if js:
            page.locator('#roast').evaluate("e => e.textContent='Une phrase de test plus longue, afin de vérifier que les éléments continuent à se placer correctement sur plusieurs lignes sans se chevaucher.'")
            art=page.locator('#hero-art').bounding_box();card=page.locator('#progress-card').bounding_box();canvas=page.locator('#atom-canvas').bounding_box()
            assert abs((canvas['x']+canvas['width']/2)-(card['x']+card['width']/2)) < 2,(width,'x')
            assert abs((canvas['y']+canvas['height']/2)-(card['y']+card['height']/2)) < 2,(width,'y')
            stats=page.locator('.stats').bounding_box()
            assert canvas['y']+canvas['height'] <= stats['y']+1,(width,'atom/stats')
            if width<=720:
                actions=page.locator('.hero-actions').bounding_box()
                assert art['y'] >= actions['y']+actions['height']-1,(width,'overlap')
        print(f'{width}px, JavaScript={js}: espace après PDF {gap:.1f}px, pas de chevauchement : OK')
        ctx.close()
    browser.close()
