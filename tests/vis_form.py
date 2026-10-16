"""Captures : feuilles CP À DÉCOUPER (plan) + gabarits 1:1 d'un scénario SCN."""
import sys, os, json
from playwright.sync_api import sync_playwright
from lib import open_app, OUT
k = sys.argv[1]
D = os.path.join(OUT, 'vis')
with sync_playwright() as pw:
    b, pg, errs = open_app(pw)
    n = pg.evaluate('''(k)=>{const S=SCN.find(s=>s[0]===k),d=T.can(T.mk(S[1],S[2],S[3])),g=d.forme==='voile'?voileGeo(d):null,R=debit(d,g);
      const pages=cpCutPages(d,R);const GP=gabPieces(d,'roll');
      const defs='<defs><pattern id="gj" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="#999" stroke-width="0.4"/></pattern></defs>';
      const cut=pages.map(p=>`<div style="border-bottom:3px solid #333">${p[0]||''}${p[1]||''}${p[2]||''}${p[3]||''}</div>`).join('');
      const gab=(GP.pieces||[]).map(pc=>`<div><b>${pc.title}</b><br><svg viewBox="0 0 ${pc.w} ${pc.h}" width="${Math.min(1200,pc.w*0.6)}">${defs}${pc.svg}</svg></div>`).join('');
      document.body.innerHTML=`<div id=c1 style="background:#fff;width:1300px">${cut}</div><div id=c2 style="background:#fff;width:1300px">${gab}</div>`;return [pages.length,(GP.pieces||[]).length,GP.msg||'']}''', k)
    print(n)
    pg.locator('#c1').screenshot(path=os.path.join(D, f'f_{k}_cut.png'))
    pg.locator('#c2').screenshot(path=os.path.join(D, f'f_{k}_gab.png'))
    b.close()
