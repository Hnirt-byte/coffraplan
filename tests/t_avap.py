"""Avant / après : la version enregistrée dans git (AVAP_REF, défaut HEAD, ou fichier APP_OLD) et le fichier de travail
app/CoffraPlan.html reçoivent les mêmes entrées ; sorties métier comparées à l'identique. Écart voulu → l'expliquer ici.
Plans : 36 scénarios SCN + 13 formes × N plans aléatoires (générateur de t_audit, graine fixe).
Comparé : contrôles, débit (CP + bois), feuilles de plan (HTML), feuilles CP À DÉCOUPER, gabarits 1:1, DXF, CSV.
Différences neutralisées : le nom de l'application dans le pied des feuilles (« Plans Réservation Coffrage » → « CoffraPlan ») et le n° d'enregistrement 3D du bouton « Ouvrir en 3D » (compteur de session, dépend du nombre de plans déjà générés)."""
import os, json, hashlib, subprocess
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE, OUT, APP


def old_app():
    if os.environ.get('APP_OLD'):
        return os.environ['APP_OLD']
    ref = os.environ.get('AVAP_REF', 'HEAD')
    p = os.path.join(OUT, 'avant.html')
    with open(p, 'wb') as f:
        f.write(subprocess.check_output(['git', 'show', ref + ':app/CoffraPlan.html'], cwd=HERE))
    return p


V21 = old_app()
V22 = APP
N = int(os.environ.get('AVAP_N', '8'))

JS = r'''([kind,a,b])=>{
  if(typeof PRT!=='undefined')PRT.lay='compact'; // v2.5 : comparaison sur la mise en page historique (compacte)
  const d=kind==='scn'?T.mk(a[1],a[2]):AX.make(a,b);d.date='2026-10-10';
  const c=canon(migr(d)),g=c.forme==='voile'?voileGeo(c):null,W=checks(c,g),bad=badDims(W)||limErr(c).length>0;
  const H=s=>String(s==null?'':s).replace(/Plans Réservation Coffrage/g,'CoffraPlan').replace(/V3REG\.get\(\d+\)/g,'V3REG.get(#)').replace(/<div class="ps-hyp">[\s\S]*?<\/div>/g,'')
    .replace(/CP filmé bouleau/g,'CP filmé').replace(/CP FILMÉ BOULEAU/g,'CP FILMÉ').replace(/<div class="ps-ent">[\s\S]*?fabriquer aux cotes<\/div><\/div><\/div>/g,''); // v2.6 : désignation du CP filmé, bloc entreprise du cartouche // v2.5 : ligne d'hypothèses ajoutée au cartouche // compteur de session de la vue 3D
  const o={W:W.filter(x=>!/^Flèche du CP/.test(x[1])).map(x=>H(x.join(':'))),_fl:W.filter(x=>/^Flèche du CP/.test(x[1])).length,gen:H(gen(d))},inp=Object.assign({},d);delete inp.date;o._inp=inp;
  if(c.forme==='voile'&&c.constr!=='caisson'&&!bad){const M=manGeo(c,voileGeo(c));o._man=[M.nC,M.nM,M.Lin>M.hp,M.hp>M.Lin]} // explication des écarts voulus (v2.4)
  if(!bad){const R=debit(c,g);o.R=H(JSON.stringify(R)+JSON.stringify(R.bois||[]));
    try{o.cut=H(cpCutPages(c,R).map(p=>p.join('|')).join('#'))}catch(e){o.cut='ERR '+e.message}
    try{o.gab=H(gabHtml(c,'roll'))}catch(e){o.gab='ERR '+e.message}
    try{const f=dxfPlanFile(d);o.dxf=f.err||new TextDecoder('latin1').decode(f.bytes);
      // v2.4 : textes et titres du DXF retouchés → le contenu géométrique est comparé par calque (nombre d'entités hors TEXT)
      const L=o.dxf.split('\r\n'),st={};for(let i=0;i<L.length-3;i+=2){if(L[i].trim()==='0'&&/^(LINE|POLYLINE|CIRCLE|ARC|VERTEX)$/.test(L[i+1])&&L[i+2].trim()==='8'){const k=L[i+1]+'@'+L[i+3];st[k]=(st[k]||0)+1}}o.dxfGeo=JSON.stringify(Object.entries(st).sort())}catch(e){o.dxf='ERR '+e.message}
    try{o.csv=H(debitCSV([d]))}catch(e){o.csv='ERR '+e.message}}
  return o}'''


def h(v):
    return hashlib.sha1(json.dumps(v, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def collect(pw, app):
    b, pg, errs = open_app(pw, app)
    pg.add_script_tag(path=os.path.join(HERE, 'auditx.js'))
    scn = pg.evaluate('SCN')
    forms = pg.evaluate("[...el('iForme').options].map(o=>o.value)")
    res = {}
    for s in scn:
        res['scn ' + s[0]] = pg.evaluate(JS, ['scn', s, 0])
    for f in forms:
        for k in range(N):
            res[f'{f} #{k}'] = pg.evaluate(JS, ['aud', f, 5000 + k])
    b.close()
    return res, [e for e in errs if 'net::' not in e]


if __name__ == '__main__':
    import sys
    s = Suite('t_avap')
    with sync_playwright() as pw:
        A, ea = collect(pw, V21)
        B, eb = collect(pw, V22)
    s.check(not ea and not eb, 'aucune erreur JS (v2.1 / v2.2)', str(ea + eb)[:300])
    s.check(set(A) == set(B), f'mêmes plans comparés ({len(A)})')
    nk, vol = 0, {}
    for k in A:
        a0, b0 = A[k], B.get(k, {})
        # v2.4 — écarts voulus : (1) mannequin de voile sans renfort dans le sens du plus grand côté → 1 montant / 1 cerce ajouté ;
        # (2) forme spéciale : axe des poteaux par défaut 300 → 200 mm (entrée différente, valeur par défaut du formulaire)
        why = None
        ia, ib = a0.get('_inp', {}), b0.get('_inp', {})
        dk = sorted(x for x in set(ia) | set(ib) if ia.get(x) != ib.get(x))
        if dk == ['pR'] and ia.get('pR') == 300 and ib.get('pR') == 200:
            why = 'défaut axe des poteaux 300 → 200'
        ma, mb = a0.get('_man'), b0.get('_man')
        if ma and mb and ma != mb:
            if ma[1] == 0 and mb[1] == 1 and ma[2] and ma[0] == mb[0]: why = 'mannequin : 1 montant ajouté (largeur > hauteur)'
            elif ma[0] == 0 and mb[0] == 1 and ma[3] and ma[1] == mb[1]: why = 'mannequin : 1 cerce ajoutée (hauteur > largeur)'
        if (b0.get('_fl') or 0) > (a0.get('_fl') or 0):  # v2.6 : nouveau contrôle de flèche des joues (voulu)
            why = why or 'v2.6 : alerte de flèche du CP (nouveau contrôle, reprise dans les contrôles des feuilles)'
        for f in sorted((set(a0) | set(b0)) - {'_inp', '_man', '_fl'}):
            a, b = a0.get(f), b0.get(f)
            nk += 1
            if a != b and f == 'dxf' and a0.get('dxfGeo') == b0.get('dxfGeo') and not why:
                vol.setdefault('DXF : textes seuls (v2.4 : compatibles AutoCAD ; v2.6 : « CP filmé bouleau »), géométrie identique par calque', set()).add(k); continue
            if a != b and why:
                vol.setdefault(why, set()).add(k); continue
            s.check(a == b, f'[{k}] {f} identique avant / après', f'{h(a)[:8]} ≠ {h(b)[:8]}')
    for w, ks in vol.items():
        print(f'  écart voulu — {w} : {len(ks)} plan(s) ({", ".join(sorted(ks)[:6])}{"…" if len(ks) > 6 else ""})')
    print(f'  {len(A)} plans, {nk} sorties comparées')
    sys.exit(0 if s.report() else 1)
