"""Zoom sur une zone d'un gabarit (unités mm) : python3 vis_zoom.py '<ov>' <id> x y w h <tag> [gm] [index]"""
import sys, os, json
from playwright.sync_api import sync_playwright
from lib import open_app, OUT
ov = json.loads(sys.argv[1]); iid = sys.argv[2]; x, y, w, h = map(float, sys.argv[3:7]); tag = sys.argv[7]; gm = sys.argv[8] if len(sys.argv) > 8 else 'band'; k = int(sys.argv[9]) if len(sys.argv) > 9 else 0
with sync_playwright() as pw:
    b, pg, errs = open_app(pw)
    info = pg.evaluate('''([ov,gm,iid,x,y,w,h,k])=>{const d=T.can(T.mk("dalle",ov));el("iGabDal").value=gm;const GP=gabPieces(d,"roll"),pc=GP.pieces.filter(p=>p.id===iid)[k];
      const defs='<defs><pattern id="gj" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="#999" stroke-width="0.4"/></pattern></defs>';
      document.body.innerHTML=`<div id=zz style="background:#fff;display:inline-block"><svg viewBox="${x} ${y} ${w} ${h}" width="${w*4}" height="${h*4}">${defs}${pc.svg}</svg></div>`;return [pc.w,pc.h,pc.title]}''', [ov, gm, iid, x, y, w, h, k])
    print(info)
    pg.locator('#zz').screenshot(path=os.path.join(OUT, 'vis', f'{tag}.png'))
    b.close()
