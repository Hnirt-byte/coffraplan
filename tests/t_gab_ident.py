"""v2.0 — Gabarits 1:1 ↔ feuilles CP À DÉCOUPER (toutes formes à pièces imbriquées : voile, caisson, fond circulaire, spéciale,
goulotte). Contrôle d'IDENTITÉ relu dans les dessins :
  • chaque pièce cintrée de la feuille de débit a un gabarit (même repère), à la même position depuis le coin ● du panneau ;
    aucune pièce à coupes droites n'a de gabarit ; aucun gabarit orphelin ;
  • contour du gabarit = contour de la pièce sur la feuille (même orientation), à la précision du dessin de la feuille ;
  • arcs du gabarit = cercles exacts (≤ 0,05 mm), rayons = rayons de l'ouvrage recalculés ici depuis la saisie ;
  • impression : 1 unité = 1 mm, feuilles à assembler qui couvrent tout le gabarit avec un recouvrement de 20 mm et des croix."""
import math, re, json
from shapely.geometry import Polygon, LineString, box
from shapely import affinity
from lib import run, HERE
import os
import gabcheck as GC

JS = r'''(c)=>{const d=T.can(T.mk(c.f,c.ov||{},c.ex?()=>eval(c.ex):undefined));Object.assign(d,c.set||{});const g=d.forme==='voile'?voileGeo(d):null,R=debit(d,g);
  const pages=cpCutPages(d,R).map(p=>{const box=document.createElement('div');box.innerHTML=p[3]||'';
    const rows=[];let pan=null;box.querySelectorAll('.sub,tr').forEach(e=>{if(e.classList.contains('sub')){const m=e.textContent.match(/^Panneau (\d+)/);if(m)pan=+m[1]}else{const td=[...e.querySelectorAll('td')].map(x=>x.textContent);rows.push([pan].concat(td))}});
    return{title:p[0],sub:p[1],el:GX.els(p[2]),rows}});
  const GP=gabPieces(d,c.mode||'roll'),gab=GP.msg?{msg:GP.msg}:{pieces:GP.pieces.filter(p=>p.kind==='nest').map(p=>({id:p.id,tag:p.tag,title:p.title,w:p.w,h:p.h,frame:p.frame,el:GX.els(p.svg)}))};
  let pg=null;const H=gabHtml(d,c.mode||'roll');if(H.html){const dc=new DOMParser().parseFromString(H.html,'text/html');
    pg=[...dc.querySelectorAll('.pg svg')].map(s=>({w:s.getAttribute('width'),h:s.getAttribute('height'),vb:s.getAttribute('viewBox'),piece:s.dataset.piece,tile:s.dataset.tile,win:s.dataset.win,
      tr:(s.querySelector(':scope > g')||{getAttribute:()=>''}).getAttribute('transform'),crosses:s.querySelectorAll('.gcross').length,clip:(s.querySelector('clipPath rect')||{getAttribute:()=>0}).getAttribute('width')}))}
  const sh=d.forme==='goulotte'?gouGeo(d):null;
  return{d:{forme:d.forme,ep:d.ep,epF:d.epF,epS:d.epS,L:d.L,l:d.l,h:d.h,DcuveM:d.DcuveM,dRef:d.dRef,joues:d.joues,constr:d.constr,Dext:d.Dext,Dint:d.Dint,D:d.D,base:d.base,gD:d.gD,gB:d.gB,gDref:d.gDref,gJE:d.gJE,gJI:d.gJI,nb:d.nb},
    pages,gab,pg,roll:+S('iRoll','914'),gou:sh&&sh.ok?{r1:sh.r1,r2:sh.r2}:null}}'''

CASES = [
    ('voile mannequin', 'voile', {}, None),
    ('voile mannequin joues radiales', 'voile', {'dJoues': 'rad'}, None),
    ('voile L3000 Ø12', 'voile', {'dL': 3000, 'dDcuve': 12, 'dh': 2500}, None),
    ('voile L3000 radiales', 'voile', {'dL': 3000, 'dDcuve': 12, 'dh': 2500, 'dJoues': 'rad'}, None),
    ('voile L2400 Ø6 parement ext.', 'voile', {'dL': 2400, 'dDcuve': 6, 'dRef': 'ext', 'dl': 300}, None),
    ('voile × 3 exemplaires', 'voile', {'dL': 1800, 'dDcuve': 9, 'iNb': 3}, None),
    ('caisson ouvert', 'voile', {'oConstr': 'caisson', 'oRenV': True}, None),
    ('caisson fermé', 'voile', {'oConstr': 'caisson', 'oRenV': True, 'oFerme': True}, None),
    ('caisson fermé L3000', 'voile', {'oConstr': 'caisson', 'oRenV': True, 'oFerme': True, 'dL': 3000, 'dl': 400, 'dh': 1500}, None),
    ('caisson radial', 'voile', {'oConstr': 'caisson', 'oRenV': True, 'dJoues': 'rad', 'dL': 2000, 'dl': 300}, None),
    ('fond circulaire', 'circ_fond', {'oRenX': True}, None),
    ('fond circulaire Ø3000/1200', 'circ_fond', {'dDext': 3000, 'dDint': 1200}, None),
    ('fond circulaire plein Ø1100', 'circ_fond', {'dDext': 1100, 'dDint': 0}, None),
    ('fond circulaire × 2', 'circ_fond', {'dDext': 2000, 'dDint': 600, 'iNb': 2}, None),
    ('spéciale circulaire concentrique', 'special', {'dBase': 'circ', 'oConc': True, 'oFondSup': True}, None),
    ('spéciale circulaire Ø1800', 'special', {'dBase': 'circ', 'dD': 1800, 'oFondSup': True}, None),
    ('goulotte tour complet', 'goulotte', {}, None),
    ('goulotte angle 120°', 'goulotte', {'gEt': 'angle', 'gAng': 120, 'gJE': True}, None),
    ('goulotte Ø3 m b 300', 'goulotte', {'gD': 3, 'gB': 300}, None),
    ('goulotte Ø14 m', 'goulotte', {'gD': 14}, None),
    ('rectangulaire (aucun gabarit)', 'rect_fond', {'dL': 1500, 'dl': 1100, 'dh': 600}, None),
]
MODES = ['roll', 'A3', 'A4']


def fmt_wh(title):
    m = re.search(r'(\d{3,4}) × (\d{3,4})', title)
    return (int(m.group(1)), int(m.group(2))) if m else None


def cut_pieces(s, r, name):
    """Pièces lues sur les feuilles CP À DÉCOUPER : [(groupe, panneau, nb panneaux, repère court, polygone panneau)] + tableaux."""
    out, tables = [], []
    for pi, pgx in enumerate(r['pages']):
        E, F = pgx['el'], fmt_wh(pgx['title'])
        grp = pgx['title']
        rects = [e for e in E['rect'] if e['fill'] == '#f2efe9']
        for rc in rects:
            W, H = (max(F), min(F)) if rc['w'] >= rc['h'] else (min(F), max(F))
            sc = rc['w'] / W
            if not s.check(abs(rc['h'] / H - sc) < 1e-3, f"[{name}] panneau à l'échelle sur la feuille"):
                continue
            ttl = [t for t in E['text'] if t['t'].startswith('PANNEAU ') and abs(t['y'] - (rc['y'] - 13)) < 0.6 and t['x'] < rc['x']]
            ttl = max(ttl, key=lambda t: t['x']) if ttl else None
            m = re.match(r'PANNEAU (\d+)/(\d+)', ttl['t']) if ttl else None
            if not s.check(m, f"[{name}] numéro du panneau lu"):
                continue
            pn, pN = int(m.group(1)), int(m.group(2))
            mm = lambda x, y: ((x - rc['x']) / sc, (rc['y'] + rc['h'] - y) / sc)
            inside = lambda x, y: rc['x'] - 1 <= x <= rc['x'] + rc['w'] + 1 and rc['y'] - 1 <= y <= rc['y'] + rc['h'] + 1
            labs = [t for t in E['text'] if t['fill'] == '#1a2035' and t['fw'] == '700' and inside(t['x'], t['y'])]
            for e in E['path']:
                if e['fill'] in ('url(#hb)', 'none') or not e['fill']:
                    continue
                P = GC.path_polys(e['d'])
                if not P or not inside(*P[0][0]):
                    continue
                poly = Polygon([mm(*q) for q in P[0]])
                hole = Polygon([mm(*q) for q in P[1]]) if len(P) > 1 else None
                lab = [t for t in labs if (poly if hole is None else poly.difference(hole)).buffer(2 / sc).contains(GC.Point(mm(t['x'], t['y'] - 2)))]
                out.append({'grp': grp, 'pn': pn, 'pN': pN, 'tag': lab[0]['t'] if lab else None, 'poly': poly, 'hole': hole, 'nv': len(P[0]), 'sc': sc})
        tables += [(grp,) + tuple(x) for x in pgx['rows']]
    return out, tables


def curved(pc):
    """Pièce cintrée : un côté au moins formé de nombreux sommets presque alignés (arc discrétisé)."""
    return pc['nv'] > 8 or (pc['hole'] is not None)


def radii_expected(d, gou):
    f, ep = d['forme'], d['ep'] or 0
    R = set()
    if f == 'voile':
        Rc = d['DcuveM'] * 500
        Ri, Re = (Rc, Rc + d['l']) if d['dRef'] == 'int' else (Rc - d['l'], Rc)
        R |= {Ri, Re, Ri + ep, Re - ep}
        return R, True     # évidements des cerces : rayons intermédiaires (bande) acceptés
    if f == 'circ_fond':
        R |= {d['Dext'] / 2 - ep}
        if d['Dint'] and d['Dint'] > 0:
            R |= {d['Dint'] / 2 + ep}
        return R, False
    if f == 'goulotte' and gou:
        return {gou['r1'], gou['r2']}, False
    return set(), True


def t(s, pg):
    pg.add_script_tag(path=os.path.join(HERE, 'gabx.js'))
    for name, f, ov, ex in CASES:
        for mode in MODES:
            nm = f'{name} · {mode}'
            r = pg.evaluate(JS, {'f': f, 'ov': ov, 'mode': mode})
            cut, tables = cut_pieces(s, r, nm)
            G = r['gab']
            cur = [c for c in cut if curved(c)]
            if not cur:
                s.check('msg' in G or not G.get('pieces'), f"[{nm}] aucune pièce cintrée → aucun gabarit")
                continue
            if not s.check('pieces' in G and G['pieces'], f"[{nm}] gabarits présents", G.get('msg', '')):
                continue
            s.check(all(c['tag'] for c in cur), f"[{nm}] chaque pièce cintrée de la feuille porte son repère")
            # ---- positions annoncées par chaque gabarit
            gpos = []
            for gp in G['pieces']:
                txt = ' ; '.join(t_['t'] for t_ in gp['el']['text'])
                for m in re.finditer(r'(?:([^;]*?) — )?panneau (\d+)/(\d+) : X (-?[\d,]+) · Y (-?[\d,]+)', txt):
                    gpos.append((gp, int(m.group(2)), int(m.group(3)), GC.num(m.group(4)), GC.num(m.group(5)), (m.group(1) or '').strip()))
            # ---- complétude : chaque pièce cintrée de la feuille ↔ une position d'un gabarit de même repère
            used = set()
            for c in cur:
                B = c['poly'].bounds
                hit = [i for i, (gp, pn, pN, X, Y, ref) in enumerate(gpos) if gp['tag'] == c['tag'] and pn == c['pn'] and pN == c['pN'] and abs(X - B[0]) <= 1.6 and abs(Y - B[1]) <= 1.6 and i not in used
                       and (not ref or ref.split(' (')[0].upper() in c['grp'].upper())]
                if not s.check(hit, f"[{nm}] {c['tag']} (panneau {c['pn']}/{c['pN']}, X {B[0]:.0f} · Y {B[1]:.0f}) : gabarit à cette position"):
                    continue
                used.add(hit[0])
                gp = gpos[hit[0]][0]
                # ---- identité géométrique : contour du gabarit (cadre ramené à la position) = contour de la pièce sur la feuille
                fr, E = gp['frame'], gp['el']
                toP = lambda x, y: (x - fr['x'] + gpos[hit[0]][3], fr['y'] + fr['h'] - y + gpos[hit[0]][4])
                ht = [e for e in E['path'] if 'ghatch' in e['cls']]
                if s.check(ht, f"[{nm}] {c['tag']} : contour hachuré sur le gabarit"):
                    PP = GC.path_polys(ht[0]['d'])
                    gpoly = Polygon([toP(*q) for q in PP[0]])
                    tol = 0.8 + 0.06 / c['sc']   # précision du dessin de la feuille (1/10 px) + sommets du polygone de débit
                    hd = GC.hausdorff(gpoly, c['poly'])
                    s.check(hd <= tol, f"[{nm}] {c['tag']} : contour du gabarit = pièce de la feuille, même orientation (écart {hd:.2f} ≤ {tol:.2f} mm)")
                    if c['hole'] is not None:
                        s.check(len(PP) > 1 and GC.hausdorff(Polygon([toP(*q) for q in PP[1]]), c['hole']) <= tol, f"[{nm}] {c['tag']} : évidement du gabarit = évidement de la feuille")
                    # cadre = encombrement de la pièce
                    s.check(abs(fr['w'] - (B[2] - B[0])) <= 1.6 and abs(fr['h'] - (B[3] - B[1])) <= 1.6, f"[{nm}] {c['tag']} : cadre {fr['w']:.0f} × {fr['h']:.0f} = encombrement sur la feuille {B[2]-B[0]:.0f} × {B[3]-B[1]:.0f}")
                # tableau de la feuille : même position
                rowok = [x for x in tables if x[0] == c['grp'] and x[1] == c['pn'] and x[2].endswith('-' + c['tag']) and re.search(rf"X {round(gpos[hit[0]][3])} · Y {round(gpos[hit[0]][4])}$", x[4])]
                s.check(rowok, f"[{nm}] {c['tag']} : position du gabarit = tableau de la feuille CP À DÉCOUPER")
            s.check(len(used) == len(gpos), f"[{nm}] aucune position de gabarit orpheline ({len(gpos) - len(used)})")
            straight_tags = {c['tag'] for c in cut if not curved(c)}
            s.check(not (straight_tags & {gp['tag'] for gp in G['pieces']}), f"[{nm}] aucun gabarit pour une pièce à coupes droites", str(straight_tags & {gp['tag'] for gp in G['pieces']}))
            # ---- arcs exacts et rayons de l'ouvrage
            Rexp, loose = radii_expected(r['d'], r['gou'])
            for gp in G['pieces']:
                for a in [e for e in gp['el']['polyline'] if 'garc' in e['cls']]:
                    P = a['pts']
                    c3 = GC_circ(P)
                    if not c3:
                        continue
                    dev = max(abs(math.hypot(x - c3[0], y - c3[1]) - c3[2]) for x, y in P)
                    s.check(dev <= 0.05, f"[{nm}] {gp['id']} : arc tracé = cercle exact (écart {dev:.3f} mm)")
                    if Rexp:
                        near = min(abs(c3[2] - x) for x in Rexp)
                        s.check(near <= 0.3 or loose, f"[{nm}] {gp['id']} : rayon {c3[2]:.1f} = rayon de l'ouvrage {sorted(round(x, 1) for x in Rexp)}")
                        if not loose:
                            continue
                        # voile : rayon d'un des parements (± CP) ou d'un évidement de cerce (rayon intermédiaire)
                        s.check(min(Rexp) - 1 <= c3[2] <= max(Rexp) + 1, f"[{nm}] {gp['id']} : rayon {c3[2]:.1f} entre les parements")
            # ---- impression
            if s.check(r['pg'], f"[{nm}] pages d'impression"):
                byp = {}
                for p in r['pg']:
                    vb = [float(x) for x in p['vb'].split()]
                    s.check(p['w'].endswith('mm') and abs(float(p['w'][:-2]) - vb[2]) < 1e-6 and abs(float(p['h'][:-2]) - vb[3]) < 1e-6, f"[{nm}] page {p['piece']} {p['tile']} : 1 unité = 1 mm")
                    s.check(re.fullmatch(r'translate\([\d.\-]+,[\d.\-]+\)( rotate\(90\))?', p['tr'] or '') is not None, f"[{nm}] page {p['piece']} : pièce seulement déplacée / tournée de 90°", p['tr'])
                    pw = float(p['w'][:-2]); W_ = [float(x) for x in p['win'].split(',')]
                    tw, th = W_[2] - W_[0], W_[3] - W_[1]
                    s.check((th if p['tr'].endswith('rotate(90)') else tw) <= pw - 2 * 8 + 1e-6, f"[{nm}] page {p['piece']} {p['tile']} : feuille dans la largeur utile")
                    byp.setdefault(p['piece'], []).append((W_, p))
                for gp in G['pieces']:
                    tl = byp.get(gp['id'], [])
                    if not s.check(tl, f"[{nm}] {gp['id']} : imprimé"):
                        continue
                    # couverture complète du gabarit et recouvrement entre feuilles voisines
                    from shapely.ops import unary_union
                    U = unary_union([box(*w) for w, _ in tl if True])
                    full = box(0, 0, gp['w'], gp['h'])
                    s.check(full.difference(U.buffer(0.02)).area < 1, f"[{nm}] {gp['id']} : feuilles couvrant tout le gabarit ({len(tl)} feuille(s))")
                    if len(tl) > 1:
                        ov = min(box(*a[0]).intersection(box(*b[0])).bounds[2] - box(*a[0]).intersection(box(*b[0])).bounds[0] if abs(a[0][1] - b[0][1]) < 1e-6 else box(*a[0]).intersection(box(*b[0])).bounds[3] - box(*a[0]).intersection(box(*b[0])).bounds[1]
                                 for i, a in enumerate(tl) for b in tl[i + 1:] if box(*a[0]).intersection(box(*b[0])).area > 1)
                        s.check(abs(ov - 20) < 0.01, f"[{nm}] {gp['id']} : recouvrement de 20 mm entre feuilles voisines ({ov:.2f})")
                        s.check(all(p['crosses'] > 0 for _, p in tl), f"[{nm}] {gp['id']} : croix d'assemblage sur chaque feuille")


def GC_circ(P):
    """Cercle des moindres carrés (Kåsa) sur tous les points tracés : robuste à l'arrondi des coordonnées SVG (0,01 mm)."""
    if len(P) < 3:
        return None
    import numpy as np
    A = np.array([[x, y, 1.0] for x, y in P]); b = np.array([-(x * x + y * y) for x, y in P])
    mx, my = sum(x for x, _ in P) / len(P), sum(y for _, y in P) / len(P)
    A[:, 0] -= mx; A[:, 1] -= my; b = np.array([-((x - mx) ** 2 + (y - my) ** 2) for x, y in P])
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = -sol[0] / 2, -sol[1] / 2
    r = math.sqrt(max(cx * cx + cy * cy - sol[2], 0))
    return (cx + mx, cy + my, r)


if __name__ == '__main__':
    import sys
    sys.exit(0 if run('t_gab_ident', t) else 1)
