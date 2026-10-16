"""Point 1 (v19) — suppression de la forme « Puisard avec fond » (doublon) et migration des plans existants.
Le débit d'un ancien puisard migré doit être identique à celui calculé par la v18."""
import json
from playwright.sync_api import sync_playwright
import os
from lib import run, open_app, HERE

V18 = os.path.join(HERE, 'ref', 'v18.html')  # référence figée : débit de la v18
# anciens plans « puisard » tels qu'enregistrés par la v18 (carré, rectangulaire, avec feuillure)
OLD = [
    {'L': 800, 'l': 800, 'h': 900},
    {'L': 1200, 'l': 700, 'h': 600},
    {'L': 600, 'l': 600, 'h': 500, 'feuil': True, 'fL': 70, 'fH': 70, 'fNiv': 0},
]
MK = r'''(o)=>{el('iForme').value=o.f;updF();const d=coll();Object.assign(d,o.v);d.date='2026-10-10';d.ch='TEST';d.ref='R01';return d}'''
SUM = r'''(d)=>{const c=canon(migr(d)),R=debit(c,null),r=x=>Math.round(x*10)/10;
  return {forme:c.forme,l:c.l,cp:R.map(x=>[x.n,x.q,r(x.a||0),r(x.b||0),Math.round(x.m2*1000)]),bois:(R.bois||[]).map(b=>[b.n,b.q,r(b.L)])}}'''


def v18_plans():
    with sync_playwright() as pw:
        b, pg, _ = open_app(pw, V18)
        out = []
        for o in OLD:
            d = pg.evaluate(MK, {'f': 'puisard', 'v': o})
            out.append((d, pg.evaluate(SUM, d)))
        b.close()
    return out


def t(s, pg):
    opts = pg.evaluate("[...el('iForme').options].map(o=>o.value)")
    s.check('puisard' not in opts, 'forme « puisard » absente du sélecteur', str(opts))
    s.check('carre_fond' in opts and 'rect_fond' in opts, 'carré avec fond et réservation avec fond toujours proposés')
    s.check(pg.evaluate("!RECT.includes('puisard')&&!FOND.includes('puisard')&&!('puisard' in TM)&&!LIB_STD.some(m=>m[1]==='puisard')"), 'plus aucune référence active à « puisard » (listes, titres, bibliothèque)')
    s.check(pg.evaluate("pieceTagsSelfTest()"), 'auto-test des repères (liste de formes mise à jour)')
    for d18, ref in V18P:
        sq = d18['L'] == d18['l']
        want = 'carre_fond' if sq else 'rect_fond'
        got = pg.evaluate(SUM, d18)
        s.check(got['forme'] == want, f"puisard {d18['L']}×{d18['l']} migré en {want}", got['forme'])
        s.check(got['cp'] == ref['cp'] and got['bois'] == ref['bois'], f"puisard {d18['L']}×{d18['l']} : débit identique à la v18", json.dumps([got, ref])[:400])
        # chargement dans le formulaire (setForm migre) puis relecture : la forme et les cotes sont conservées
        r = pg.evaluate("(d)=>{setForm(d);const e=coll();return [e.forme,e.L,e.l,e.h,!!e.feuil]}", d18)
        s.check(r[0] == want and r[1] == d18['L'] and r[2] == d18['l'] and r[3] == d18['h'] and r[4] == bool(d18.get('feuil')),
                f"puisard {d18['L']}×{d18['l']} rechargé dans le formulaire", str(r))
    # plans enregistrés dans le navigateur (localStorage) et import JSON : migrés au chargement
    d18 = V18P[1][0]
    r = pg.evaluate("(d)=>{localStorage.setItem('resa3',JSON.stringify([d]));const L=ldP();return L[0].forme}", d18)
    s.check(r == 'rect_fond', 'plan enregistré (navigateur) migré au chargement', r)
    r = pg.evaluate("(d)=>{const h=gen(d);return /RESERVATION DALLE AVEC FOND/.test(h)&&!/undefined/.test(h.replace(/<script[\\s\\S]*?<\\/script>/g,''))}", d18)
    s.check(r, 'plan généré depuis un ancien puisard : titre correct, pas de « undefined »')


if __name__ == '__main__':
    import sys
    V18P = v18_plans()
    sys.exit(0 if run('t_forme', t) else 1)
