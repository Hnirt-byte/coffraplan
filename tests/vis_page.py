"""Capture haute résolution d'une page imprimée de gabarit (contrôle de lisibilité)."""
import sys, os, json
from playwright.sync_api import sync_playwright
from lib import open_app, OUT
ov = json.loads(sys.argv[1]); idx = [int(x) for x in sys.argv[2].split(',')]; tag = sys.argv[3]; gm = sys.argv[4] if len(sys.argv) > 4 else 'band'
with sync_playwright() as pw:
    b, pg, errs = open_app(pw)
    pg.evaluate('([ov,gm])=>{const d=T.can(T.mk("dalle",ov));el("iGabDal").value=gm;window._H=gabHtml(d,"roll")}', [ov, gm])
    pg.evaluate('()=>{document.open();document.write(_H.html);document.close()}')
    pg.wait_for_timeout(300)
    pg.evaluate('()=>{document.querySelectorAll("body > *:not(.pg)").forEach(e=>{if(!e.querySelector(".pg"))e.style.display="none"})}')
    for i in idx:
        pg.locator('.pg').nth(i - 1).screenshot(path=os.path.join(OUT, 'vis', f'{tag}_page{i}.png'))
    b.close()
