"""Capture du plan complet (feuilles) d'une saisie : python3 vis_plan.py forme '<ov json>' tag [max_feuilles]"""
import sys, os, json
from playwright.sync_api import sync_playwright
from lib import open_app, OUT
f = sys.argv[1]; ov = json.loads(sys.argv[2]); tag = sys.argv[3]; mx = int(sys.argv[4]) if len(sys.argv) > 4 else 3
with sync_playwright() as pw:
    b, pg, errs = open_app(pw, width=1300)
    W = pg.evaluate('([f,ov])=>{const d=T.mk(f,ov);const c=T.can(d);const W=checks(c,c.forme==="voile"?voileGeo(c):null);el("pvA").innerHTML=gen(d);return W}', [f, ov])
    print(json.dumps(W, ensure_ascii=False))
    n = pg.evaluate('document.querySelectorAll("#pvA .ps").length')
    for i in range(min(n, mx)):
        pg.locator('#pvA .ps').nth(i).screenshot(path=os.path.join(OUT, 'vis', f'{tag}_{i+1}.png'))
    print('feuilles', n)
    b.close()
