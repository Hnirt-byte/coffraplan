"""Captures visuelles : feuilles CP À DÉCOUPER + gabarits 1:1 d'une dalle (contrôle à l'œil)."""
import sys, os, json
from playwright.sync_api import sync_playwright
from lib import open_app, OUT
ov = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
tag = sys.argv[2] if len(sys.argv) > 2 else 'def'
gm = sys.argv[3] if len(sys.argv) > 3 else 'band'
D = os.path.join(OUT, 'vis'); os.makedirs(D, exist_ok=True)
with sync_playwright() as pw:
    b, pg, errs = open_app(pw)
    info = pg.evaluate('''([ov,gm])=>{const d=T.can(T.mk('dalle',ov));el('iGabDal').value=gm;const G=dalGeo(d);window._d=d;
      const cut=dalCutPages(d,G);const H=gabHtml(d,'roll');window._H=H;window._cut=cut;
      return {n:cut.length,R:G.shL.R,P:G.P,Q:G.Q,sheets:G.sheets.map(s=>s.items.map(it=>it.pc.id+(it.rot?'r':''))),gab:(H.html?1:0)}}''', [ov, gm])
    print(json.dumps(info))
    for i in range(info['n']):
        pg.evaluate('(i)=>{document.body.innerHTML=`<div id=zz style="background:#fff;width:1500px">${_cut[i]}</div>`;const s=document.querySelector("#zz svg");s.setAttribute("width",1500);s.setAttribute("height",780)}', i)
        pg.locator('#zz').screenshot(path=os.path.join(D, f'{tag}_cut{i+1}.png'))
    pg.evaluate('()=>{document.open();document.write(_H.html);document.close()}')
    pg.wait_for_timeout(300)
    n = pg.evaluate('document.querySelectorAll(".pg").length')
    for i in range(n):
        el = pg.locator('.pg').nth(i)
        el.screenshot(path=os.path.join(D, f'{tag}_gab{i+1}.png'))
    print('gab pages', n)
    b.close()
