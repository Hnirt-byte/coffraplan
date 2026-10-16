"""Planche contact : pour chaque pièce D, la pièce sur la feuille de débit (gauche) et le gabarit (droite), même échelle."""
import sys, os, json
from playwright.sync_api import sync_playwright
from lib import open_app, OUT
ov = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
tag = sys.argv[2] if len(sys.argv) > 2 else 'def'
gm = sys.argv[3] if len(sys.argv) > 3 else 'band'
D = os.path.join(OUT, 'vis')
with sync_playwright() as pw:
    b, pg, errs = open_app(pw)
    n = pg.evaluate('''([ov,gm])=>{const d=T.can(T.mk('dalle',ov));el('iGabDal').value=gm;const G=dalGeo(d),GP=gabPieces(d,'roll');
      const defs='<defs><pattern id="gj" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="#999" stroke-width="0.4"/></pattern></defs>';
      const rows=GP.pieces.map(pc=>{const it=pc.it,P=G.P,Q=G.Q;
        const panel=`<svg viewBox="-60 -60 ${P+120} ${Q+120}" width="520" height="${520*(Q+120)/(P+120)}"><rect x="0" y="0" width="${P}" height="${Q}" fill="#fbf7ee" stroke="#888" stroke-width="3"/>`+
          G.sheets[pc.sheet].items.map(o=>`<path d="M${o.poly.map(([x,y])=>x+','+(Q-y)).join(' L')}Z" fill="${o===it?'#e2c38f':'#eee'}" stroke="#000" stroke-width="3"/><text x="${o.ox+o.w/2}" y="${Q-o.oy-o.h/2}" font-size="120">${o.pc.id}</text>`).join('')+
          `<circle cx="0" cy="${Q}" r="20"/></svg>`;
        const g=`<svg viewBox="0 0 ${pc.w} ${pc.h}" width="${Math.min(700,pc.w*0.5)}" height="${Math.min(700,pc.w*0.5)*pc.h/pc.w}" style="border:1px solid #ccc">${defs}${pc.svg}</svg>`;
        return `<div style="display:flex;gap:20px;align-items:flex-start;border-bottom:2px solid #333;padding:8px"><div><b>${pc.title} (${pc.kind})</b><br>${panel}</div>${g}</div>`});
      document.body.innerHTML='<div id=zz style="background:#fff;width:1300px">'+rows.join('')+'</div>';return GP.pieces.length}''', [ov, gm])
    rows = pg.locator('#zz > div')
    for i in range(n):
        rows.nth(i).screenshot(path=os.path.join(D, f'{tag}_cmp{i+1}.png'))
    print(n, errs[:2])
    b.close()
