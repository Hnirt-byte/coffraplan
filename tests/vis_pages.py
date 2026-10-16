"""Captures des pages imprimées d'un gabarit (form + ov), mode."""
import sys, os, json
from playwright.sync_api import sync_playwright
from lib import open_app, OUT
f = sys.argv[1]; ov = json.loads(sys.argv[2]); mode = sys.argv[3]; tag = sys.argv[4]; idx = [int(x) for x in sys.argv[5].split(',')]
with sync_playwright() as pw:
    b, pg, errs = open_app(pw)
    n = pg.evaluate('([f,ov,mode])=>{const d=T.can(T.mk(f,ov));window._H=gabHtml(d,mode);return _H.n}', [f, ov, mode])
    print('pages', n)
    pg.evaluate('()=>{document.open();document.write(_H.html);document.close()}'); pg.wait_for_timeout(300)
    pg.evaluate('()=>{const b=document.querySelector(".bar");if(b)b.style.display="none";document.querySelector(".wrap").style.zoom=0.5}')
    for i in idx:
        if i <= n: pg.locator('.pg').nth(i - 1).screenshot(path=os.path.join(OUT, 'vis', f'{tag}_p{i}.png'))
    b.close()
