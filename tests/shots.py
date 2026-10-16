"""Captures PNG de vues (contrôle visuel) : python3 shots.py dossier spec…   spec = scenario:kind (kind = m3 | m3x | plan | gab)"""
import sys, os
from playwright.sync_api import sync_playwright
from lib import open_app
dst = sys.argv[1]; os.makedirs(dst, exist_ok=True)
with sync_playwright() as pw:
    b, pg, e = open_app(pw)
    for spec in sys.argv[2:]:
        k, kind = spec.split(':')
        svg = pg.evaluate('''([k,kind])=>{const S=SCN.find(s=>s[0]===k),d0=T.mk(S[1],S[2],S[3]),d=T.can(d0),g=d.forme==='voile'?voileGeo(d):null,R=debit(d,g);
          if(kind==='m3')return montageSvg(d,R,false);if(kind==='m3x')return montageSvg(d,R,true);
          if(kind==='gab'){const G=gabPieces(d,'roll');const p=G.pieces[0];return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${p.w} ${p.h}" width="${Math.min(1400,p.w*1.2)}"><defs><pattern id="gj" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="#999" stroke-width="0.4"/></pattern></defs><rect width="100%" height="100%" fill="#fff"/>${p.svg}</svg>`}
          el('pvA').innerHTML=gen(d0);const n=+kind.replace('plan','')||0;return [...el('pvA').querySelectorAll('.ps')][n].outerHTML}''', [k, kind])
        p2 = b.new_page(viewport={'width': 1400, 'height': 1000})
        css = pg.evaluate('[...document.querySelectorAll("style")].map(s=>s.textContent).join("\\n")')
        p2.set_content(f'<html><head><style>{css} body{{background:#fff}}</style></head><body><div class="pv" style="width:1300px">{svg}</div></body></html>')
        p2.screenshot(path=os.path.join(dst, f'{k}_{kind}.png'), full_page=True); p2.close()
    b.close()
print('ok')
