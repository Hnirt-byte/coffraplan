"""Avant / après (v2.9 : feuilles et CP à découper comparés sur l'ensemble des lignes de tableaux et des textes des dessins — cotes,
repères, positions — et non plus sur le balisage, la mise en page ayant changé) : la version enregistrée dans git (AVAP_REF, défaut HEAD, ou fichier APP_OLD) et le fichier de travail
app/CoffraPlan.html reçoivent les mêmes entrées ; sorties métier comparées à l'identique. Écart voulu → l'expliquer ici.
Plans : 36 scénarios SCN + 13 formes × N plans aléatoires (générateur de t_audit, graine fixe).
Comparé : contrôles, débit (CP + bois), feuilles de plan (HTML), feuilles CP À DÉCOUPER, gabarits 1:1, DXF, CSV.
v2.10 : écarts voulus — perçage des fonds Ø poteau + 0 mm par défaut, platelage de dalle soulevé en vue éclatée.
v3.0 : écart voulu — cotes d'implantation sur les vues en plan (axes X / Y, cotes signées, poteaux), feuilles et DXF ; débit, CSV, découpe, gabarits inchangés.
Différences neutralisées : le nom de l'application dans le pied des feuilles (« Plans Réservation Coffrage » → « CoffraPlan ») et le n° d'enregistrement 3D du bouton « Ouvrir en 3D » (compteur de session, dépend du nombre de plans déjà générés)."""
import os, json, hashlib, re, subprocess
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
  // v2.9 : mise en page des feuilles revue (pied hors grille, 2 panneaux CP par feuille, vues recadrées) → contenu comparé en texte
  const TXT=h=>{const b=document.createElement('div');b.innerHTML=h;return [...b.querySelectorAll('.ps-c tr, .ps-c svg text')].map(c=>c.textContent.replace(/\s+/g,' ').trim()).sort().join('|')}; // lignes de tableaux + textes des dessins, sans ordre
  const o={W:W.filter(x=>!/^Flèche du CP/.test(x[1])).map(x=>H(x.join(':'))),_fl:W.filter(x=>/^Flèche du CP/.test(x[1])).length,gen:TXT(H(gen(d)))},inp=Object.assign({},d);delete inp.date;o._inp=inp;
  if(c.forme==='voile'&&c.constr!=='caisson'&&!bad){const M=manGeo(c,voileGeo(c));o._man=[M.nC,M.nM,M.Lin>M.hp,M.hp>M.Lin]} // explication des écarts voulus (v2.4)
  if(!bad){const R=debit(c,g);try{const M3=model3(c,R);o._np=M3.solids.filter(x=>x.nm==='poche').length;o._nt=new Set(M3.solids.map(x=>x.tag).filter(Boolean)).size}catch(e){} // v2.7 : poches en caisson CP (1 → 4 solides)
o.R=H(JSON.stringify(R)+JSON.stringify(R.bois||[]));
    try{o.cut=TXT(H(cpCutPages(c,R).map(p=>`<div class="ps-c">${p[1]}${p[2]}${p[3]}</div>`).join('')))}catch(e){o.cut='ERR '+e.message}
    try{o.gab=H(gabHtml(c,'roll'))}catch(e){o.gab='ERR '+e.message}
    try{const f=dxfPlanFile(d);o.dxf=f.err||new TextDecoder('latin1').decode(f.bytes);
      // v2.4 : textes et titres du DXF retouchés → le contenu géométrique est comparé par calque (nombre d'entités hors TEXT)
      const L=o.dxf.split('\r\n'),st={};for(let i=0;i<L.length-3;i+=2){if(L[i].trim()==='0'&&/^(LINE|POLYLINE|CIRCLE|ARC|VERTEX)$/.test(L[i+1])&&L[i+2].trim()==='8'){const k=L[i+1]+'@'+L[i+3];st[k]=(st[k]||0)+1}}o.dxfGeo=JSON.stringify(Object.entries(st).sort())}catch(e){o.dxf='ERR '+e.message}
    try{o.csv=H(debitCSV([d]))}catch(e){o.csv='ERR '+e.message}}
  return o}'''


IMPL = re.compile(r'^([+−-]\d[\d ,.]*|0|[XY]|Implantation des poteaux \(axes X / Y\)|P\d+ +x \S+ +y \S+)$')


def impl_only(a0, b0):
    """v3.0 : seules les cotes d'implantation diffèrent (vue en plan : L/2 et l/2 remplacées, axes X / Y, cotes signées, poteaux)"""
    import collections
    ga, gb = collections.Counter(a0['gen'].split('|')), collections.Counter(b0['gen'].split('|'))
    if not all(re.match(r'^[lL]/2: ', x) for x in ga - gb) or not all(IMPL.match(x) for x in gb - ga):
        return False
    try:
        da, db = dict(map(tuple, json.loads(a0['dxfGeo']))), dict(map(tuple, json.loads(b0['dxfGeo'])))
    except Exception:
        return a0.get('dxfGeo') == b0.get('dxfGeo')
    return all(db.get(x, 0) >= da.get(x, 0) and (db.get(x, 0) == da.get(x, 0) or x.split('@')[-1].startswith('VUES_')) for x in set(da) | set(db))


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
        if dk == ['pJ'] and ia.get('pJ') == 10 and ib.get('pJ') == 0:  # v2.10 : demande de Kévin
            why = 'v2.10 : perçage des fonds Ø poteau + 0 mm par défaut (au lieu de + 10 mm)'
        ma, mb = a0.get('_man'), b0.get('_man')
        if ma and mb and ma != mb:
            if ma[1] == 0 and mb[1] == 1 and ma[2] and ma[0] == mb[0]: why = 'mannequin : 1 montant ajouté (largeur > hauteur)'
            elif ma[0] == 0 and mb[0] == 1 and ma[3] and ma[1] == mb[1]: why = 'mannequin : 1 cerce ajoutée (hauteur > largeur)'
        if a0.get('_np') != b0.get('_np') and b0.get('_np') == 4 * (a0.get('_np') or 0):
            why = why or 'v2.7 : poches en caisson CP en 3D (feuille de montage, vue 3D du DXF)'
        if (b0.get('_nt') or 0) > (a0.get('_nt') or 0):  # v2.8 : repères 3D complétés → étiquettes de la feuille de montage
            why = why or 'v2.8 : repères complétés en 3D (étiquettes de la feuille de montage)'
        if (b0.get('_fl') or 0) > (a0.get('_fl') or 0):  # v2.6 : nouveau contrôle de flèche des joues (voulu)
            why = why or 'v2.6 : alerte de flèche du CP (nouveau contrôle, reprise dans les contrôles des feuilles)'
        for f in sorted((set(a0) | set(b0)) - {'_inp', '_man', '_fl', '_np', '_nt'}):
            a, b = a0.get(f), b0.get(f)
            nk += 1
            if a != b and f in ('gen', 'dxf', 'dxfGeo') and not why and all(a0.get(x) == b0.get(x) for x in ('R', 'W', 'csv', 'cut', 'gab')) and impl_only(a0, b0):
                vol.setdefault('v3.0 : cotes d\'implantation sur la vue en plan (L/2, l/2 → cotes signées depuis les axes, bulles X / Y, tableau des poteaux ; DXF : mêmes traits et textes en plus)', set()).add(k); continue
            if a != b and f == 'dxf' and a0.get('dxfGeo') == b0.get('dxfGeo') and not why:
                vol.setdefault('DXF : textes seuls (v2.4 : compatibles AutoCAD ; v2.6 : « CP filmé bouleau »), géométrie identique par calque', set()).add(k); continue
            if a != b and f in ('gen', 'cut') and not why and isinstance(a, str) and isinstance(b, str):
                import collections
                lost = collections.Counter(a.split('|')) - collections.Counter(b.split('|'))
                if not lost:  # v2.9 : rien de perdu, étiquettes en plus
                    vol.setdefault('v2.9 : panneaux dessinés plus grands (2 par feuille) → étiquettes supplémentaires, aucune perdue', set()).add(k); continue
                note = [x for x in lost if x.endswith('— platelage masqué')]
                if f == 'gen' and ia.get('forme') == 'dalle' and a0.get('R') == b0.get('R') and a0.get('W') == b0.get('W') and len(note) == 1 and sum(lost.values()) <= 5 and all(len(x) <= 12 for x in lost if x not in note):
                    # v2.10 : en vue éclatée, le platelage s'élève au lieu d'être masqué → note retirée, repères du platelage ajoutés, ≤ 4 étiquettes déplacées
                    vol.setdefault('v2.10 : dalle — platelage soulevé en vue éclatée (note « platelage masqué » retirée, repères du platelage ajoutés)', set()).add(k); continue
                if a0.get('R') == b0.get('R') and a0.get('W') == b0.get('W') and sum(lost.values()) <= 4 and all(len(x) <= 3 for x in lost):
                    # même débit, mêmes contrôles ; seules quelques étiquettes courtes (repère, numéro) déplacées par le placement automatique
                    vol.setdefault('v2.9 : placement des étiquettes revu sur les dessins agrandis (≤ 4 étiquettes courtes déplacées, débit identique)', set()).add(k + ' ' + f + ' −' + ','.join(lost)); continue
            if a != b and why:
                vol.setdefault(why, set()).add(k); continue
            s.check(a == b, f'[{k}] {f} identique avant / après', f'{h(a)[:8]} ≠ {h(b)[:8]}')
    for w, ks in vol.items():
        print(f'  écart voulu — {w} : {len(ks)} plan(s) ({", ".join(sorted(ks)[:6])}{"…" if len(ks) > 6 else ""})')
    print(f'  {len(A)} plans, {nk} sorties comparées')
    sys.exit(0 if s.report() else 1)
