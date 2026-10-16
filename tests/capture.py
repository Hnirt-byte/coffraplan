"""Capture des résumés de débit de tous les scénarios : python3 capture.py <app.html> <sortie.json>"""
import json, sys
from playwright.sync_api import sync_playwright
from lib import open_app

app, dst = sys.argv[1], sys.argv[2]
with sync_playwright() as pw:
    b, pg, errs = open_app(pw, app)
    res = pg.evaluate('''()=>{const o={};SCN.forEach(([k,f,ov,ex])=>{try{o[k]=T.sum(T.mk(f,ov,ex))}catch(e){o[k]={err:String(e)}}});return o}''')
    b.close()
json.dump(res, open(dst, 'w'), ensure_ascii=False, indent=1)
print(len(res), 'scénarios', [k for k, v in res.items() if 'err' in v], errs[:3])
