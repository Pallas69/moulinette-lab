"""Vérification navigateur légère du reset et du repli à zéro sur données factices."""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from moulinette.history import store_attempt, read_history, reset_history
from moulinette.dashboard import write_dashboard
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory(prefix='ml-reset-browser-') as tmp:
    os.environ['XDG_DATA_HOME']=tmp
    for ex,result in [('c00/ex00','passed'),('c00/ex01','failed')]:
        store_attempt({'exercise':ex,'result':result,'checks':[],'isolation':'fictif'},'/test')
    html=write_dashboard(output_path=Path(tmp)/'dashboard.html')
    with sync_playwright() as pw:
        args={'headless':True,'args':['--no-sandbox']}
        if os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
            args['executable_path']=os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
        browser=pw.chromium.launch(**args);context=browser.new_context(reduced_motion='reduce')
        page=context.new_page();page.goto(html.as_uri())
        assert page.locator('#hero-art').get_attribute('data-animated-electrons')=='2'
        assert page.locator('#hero-art').get_attribute('data-animated-orbits')=='2'
        backup=reset_history()
        assert read_history()['count']==0 and read_history(db_path=backup)['count']==2
        write_dashboard(output_path=html);page.reload()
        assert page.locator('#hero-art').get_attribute('data-animated-electrons')=='0'
        assert page.locator('#hero-art').get_attribute('data-animated-orbits')=='0'
        assert page.locator('#atom-svg .atom-shell').count()==0
        assert page.locator('#atom-svg .atom-electron').count()==0
        context.close();browser.close()
print('Reset navigateur : 2 orbites/électrons avant, 0 après, sauvegarde de 2 résultats : OK')
