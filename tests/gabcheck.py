"""Vérification géométrique INDÉPENDANTE dalle de couverture : calepinage → feuilles CP À DÉCOUPER → plan de pose → gabarits 1:1.
Géométrie attendue recalculée avec shapely à partir des seules cellules du calepinage et du placement des pièces sur les panneaux.
Chaque dessin est relu tel qu'il est tracé (coordonnées SVG, textes affichés) puis ramené en mm."""
import math, re
from shapely.geometry import Point, box, Polygon, LineString, MultiLineString, GeometryCollection
from shapely import affinity
from shapely.ops import unary_union

DC, GREY, WS = '#c0392b', '#666', '#5a3e1b'
TOL = 0.6          # mm : position d'un point / d'un repère
TOL_R = 0.3        # mm : écart au rayon d'un arc tracé


def num(t):
    t = t.replace(' ', '').replace('\xa0', '').replace(' ', '').replace(',', '.')
    m = re.match(r'^[@]?(-?\d+(?:\.\d+)?)$', t)
    return float(m.group(1)) if m else None


def path_polys(d):
    out = []
    for part in re.split(r'[Mm]', d):
        nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?(?:e-?\d+)?', part)]
        if len(nums) >= 6:
            out.append(list(zip(nums[0::2], nums[1::2])))
    return out


class Geo:
    """Géométrie attendue d'une configuration (repère du calepinage, puis panneau)."""

    def __init__(s, r):
        s.r, s.P, s.Q, s.kerf = r, r['P'], r['Q'], r['kerf']
        sh = r['sh']
        s.circ = sh['t'] == 'circ'
        s.R = sh['R']
        s.shape = Point(0, 0).buffer(s.R, quad_segs=2048) if s.circ else box(-sh['A'] / 2, -sh['B'] / 2, sh['A'] / 2, sh['B'] / 2)
        s.ring = LineString(list(Point(0, 0).buffer(s.R, quad_segs=2048).exterior.coords)) if s.circ else None
        s.items = {}
        for si, sheet in enumerate(r['items']):
            for it in sheet:
                loc = box(*it['cell']).intersection(s.shape)
                x1, y1, x2, y2 = loc.bounds
                M = [-1, 0, 0, -1, it['ox'] + x2, it['oy'] + y2] if it['rot'] else [1, 0, 0, 1, it['ox'] - x1, it['oy'] - y1]
                Mi = [-1, 0, 0, -1, it['ox'] + x2, it['oy'] + y2] if it['rot'] else [1, 0, 0, 1, x1 - it['ox'], y1 - it['oy']]
                pan = affinity.affine_transform(loc, M)
                arcs = []
                if s.circ:
                    a = s.ring.intersection(box(*it['cell']))
                    geoms = [a] if isinstance(a, LineString) else list(getattr(a, 'geoms', []))
                    for g in geoms:
                        if isinstance(g, LineString) and g.length > 1.0:
                            arcs.append(affinity.affine_transform(g, M))
                    arcs = merge_lines(arcs)
                s.items[it['id']] = dict(si=si, it=it, loc=loc, pan=pan, M=M, Mi=Mi, arcs=arcs, w=x2 - x1, h=y2 - y1)

    def to_loc(s, iid, p):
        a, b, d, e, xo, yo = s.items[iid]['Mi']
        return (a * p[0] + b * p[1] + xo, d * p[0] + e * p[1] + yo)

    def on_circle(s, iid, p):
        q = s.to_loc(iid, p)
        return abs(math.hypot(*q) - s.R)


def merge_lines(L):
    from shapely.ops import linemerge
    if not L:
        return []
    m = linemerge(MultiLineString([list(l.coords) for l in L]))
    return [m] if isinstance(m, LineString) else list(m.geoms)


def hausdorff(a, b):
    return a.hausdorff_distance(b)


# ---------------------------------------------------------------- calepinage et panneaux
def check_layout(s, g):
    r = g.r
    # 1) couverture : pièces (E + D) = forme ∩ bandes (zones hors poutres), sans recouvrement
    zones = unary_union([box(-1e6, z[0], 1e6, z[1]) for z in r['zones']])
    target = g.shape.intersection(zones)
    pcs = [box(*p['cell']).intersection(g.shape) for p in r['all']]
    pcs = [p for p in pcs if p.area > 1]
    U = unary_union(pcs)
    s.check(abs(U.area - target.area) / target.area < 2e-4, f"calepinage : pièces = surface à coffrer hors poutres (écart {abs(U.area-target.area)/1e6:.4f} m²)")
    s.check(abs(sum(p.area for p in pcs) - U.area) < 50, 'calepinage : aucune pièce ne se recouvre')
    nD = sum(1 for p in r['all'] if not p['full'])
    s.check(nD == sum(len(x) for x in r['items']), f"toutes les pièces D ({nD}) sont sur un panneau à découper")
    # 1 bis) lignes du débit (CSV / XLSX / dossier) : nombre de planches E et D, panneaux, surface des pièces D
    E = [x for x in r['deb'] if x['n'].startswith('Planches entières')]
    D = [x for x in r['deb'] if x['n'].startswith('Planches découpées')]
    nE = sum(1 for p in r['all'] if p['full'])
    s.check((E[0]['q'] if E else 0) == nE, f"débit : {nE} planches entières E", str(E))
    if nD:
        aD = sum(g.items[it['id']]['loc'].area for sh in r['items'] for it in sh) / 1e6
        s.check(D and D[0]['q'] == nD and f"sur {len(r['items'])} panneau" in D[0]['txt'] and abs(D[0]['m2'] - aD) < 0.002,
                f"débit : {nD} planches D sur {len(r['items'])} panneaux, {aD:.3f} m²", str(D))
    # 2) chaque panneau : pièces dans le panneau, écart ≥ trait de scie
    for si, sheet in enumerate(r['items']):
        P = [g.items[it['id']]['pan'] for it in sheet]
        inside = all(p.within(box(-0.5, -0.5, g.P + 0.5, g.Q + 0.5)) for p in P)
        s.check(inside, f"panneau {si+1} : pièces dans le panneau {g.P}×{g.Q}")
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                dd = P[i].distance(P[j])
                s.check(dd >= g.kerf - 0.05, f"panneau {si+1} : {sheet[i]['id']} / {sheet[j]['id']} séparées d'au moins le trait de scie ({dd:.1f} ≥ {g.kerf})")


# ---------------------------------------------------------------- feuille CP À DÉCOUPER
def quadrant(E, k):
    ox, oy = (k % 2) * 500, 4 + (k // 2) * 236
    inb = lambda x, y: ox <= x <= ox + 500 and oy <= y <= oy + 248
    return {
        'rect': [e for e in E['rect'] if inb(e['x'] + e['w'] / 2, e['y'] + e['h'] / 2)],
        'path': [e for e in E['path'] if path_polys(e['d']) and inb(*path_polys(e['d'])[0][0])],
        'circle': [e for e in E['circle'] if inb(e['x'], e['y'])],
        'line': [e for e in E['line'] if inb((e['x1'] + e['x2']) / 2, (e['y1'] + e['y2']) / 2)],
        'text': [e for e in E['text'] if inb(e['x'], e['y'])],
    }, (ox, oy)


def check_cut_sheets(s, g):
    """Retourne {id pièce: [repères (X, Y, ref, val) en mm panneau]} lus sur la feuille de débit."""
    r, N = g.r, len(g.r['items'])
    marks = {}
    sheets = r['items']
    s.check(len(r['cut']) == (N + 3) // 4, f"feuilles CP À DÉCOUPER : {len(r['cut'])} page(s) pour {N} panneau(x)")
    for si, sheet in enumerate(sheets):
        E = r['cut'][si // 4]
        q, (ox, oy) = quadrant(E, si % 4)
        pr = [e for e in q['rect'] if e['fill'] == '#fbf7ee']
        if not s.check(len(pr) == 1, f"panneau {si+1} : cadre du panneau dessiné"):
            continue
        pr = pr[0]
        sc = pr['w'] / g.P
        s.check(abs(pr['h'] / g.Q - sc) < 1e-6, f"panneau {si+1} : panneau à l'échelle (proportions {g.P}×{g.Q})")
        x0, yb, xr, y0 = pr['x'], pr['y'] + pr['h'], pr['x'] + pr['w'], pr['y']
        mm = lambda x, y: ((x - x0) / sc, (yb - y) / sc)
        # titre : n° de panneau, pièces, retournées
        ttl = [t['t'] for t in q['text'] if t['t'].startswith('PANNEAU ')]
        exp = f"PANNEAU {si+1} / {N} → " + ' + '.join(it['id'] + (' (retourné)' if it['rot'] else '') for it in sheet)
        s.check(ttl and ttl[0] == exp, f"panneau {si+1} : titre « {exp} »", str(ttl[:1]))
        # contours des pièces
        drawn = [Polygon([mm(*p) for p in path_polys(e['d'])[0]]) for e in q['path'] if e['fill'] == '#e2c38f']
        s.check(len(drawn) == len(sheet), f"panneau {si+1} : {len(drawn)} pièce(s) dessinée(s) = {len(sheet)}")
        for it in sheet:
            I = g.items[it['id']]
            best = min(drawn, key=lambda p: hausdorff(p, I['pan'])) if drawn else None
            hd = hausdorff(best, I['pan']) if best is not None else 1e9
            s.check(hd < 1.0, f"{it['id']} : contour de la feuille de débit = pièce attendue (écart max {hd:.2f} mm)")
            # libellés : repère + cotes hors-tout
            lab = [t for t in q['text'] if t['t'] == it['id']]
            dims = f"{round(I['w'])} × {round(I['h'])}"
            s.check(lab, f"{it['id']} : repère inscrit sur la feuille de débit")
            s.check(any(t['t'] == dims for t in q['text']), f"{it['id']} : cotes hors-tout {dims} inscrites", str([t['t'] for t in q['text'] if '×' in t['t']]))
            if lab:
                p = Point(mm(lab[0]['x'], lab[0]['y']))
                own = I['pan'].buffer(80)
                s.check(own.contains(p), f"{it['id']} : repère placé sur sa pièce")
        # coupes droites attendues (côtés droits hors bords du panneau et hors arc)
        vx, hy = set(), set()
        for it in sheet:
            I = g.items[it['id']]
            c = list(I['pan'].exterior.coords)
            for a, b in zip(c, c[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L < 5:
                    continue
                if g.circ and g.on_circle(it['id'], a) < 0.6 and g.on_circle(it['id'], b) < 0.6 and g.on_circle(it['id'], ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)) < 0.6:
                    continue   # arête d'arc (une corde entre deux points du cercle est une coupe droite)
                if abs(a[0] - b[0]) < 0.5 and 1 < a[0] < g.P - 1:
                    vx.add(round(a[0]))
                if abs(a[1] - b[1]) < 0.5 and 1 < a[1] < g.Q - 1:
                    hy.add(round(a[1]))
        red = [t for t in q['text'] if t['fill'] == DC and num(t['t']) is not None]
        below = {num(t['t']) for t in red if t['y'] > yb + 5}
        right = {num(t['t']) for t in red if t['x'] > xr + 5 and t['an'] == 'start'}
        miss_v = [v for v in vx if not any(abs(v - b) <= 1 for b in below)]
        miss_h = [v for v in hy if not any(abs(v - b) <= 1 for b in right)]
        s.check(not miss_v, f"panneau {si+1} : toutes les coupes verticales cotées depuis ● {sorted(vx)}", f"manquent {miss_v}, lues {sorted(below)}")
        s.check(not miss_h, f"panneau {si+1} : toutes les coupes horizontales cotées depuis ● {sorted(hy)}", f"manquent {miss_h}, lues {sorted(right)}")
        ph_v = [b for b in below if not any(abs(v - b) <= 1 for v in vx)]
        ph_h = [b for b in right if not any(abs(v - b) <= 1 for v in hy)]
        s.check(not ph_v and not ph_h, f"panneau {si+1} : aucune cote de coupe fantôme", f"x {ph_v} y {ph_h}")
        if not g.circ:
            continue
        # repères de traçage des arcs
        pts = [c for c in q['circle'] if abs(c['r'] - 1.6) < 1e-6 and c['fill'] == DC]
        lines = [l for l in q['line'] if l['stroke'] == DC and abs(l['sw'] - 0.6) < 1e-6]
        greys = {num(t['t']) for t in q['text'] if t['fill'] == GREY and num(t['t']) is not None}
        for c in pts:
            P = mm(c['x'], c['y'])
            # pièce dont l'arc passe par ce repère
            cands = [(I['arcs'] and min(a.distance(Point(P)) for a in I['arcs']), iid) for iid, I in g.items.items() if I['si'] == si and I['arcs']]
            cands = [x for x in cands if x[0] is not None]
            dmin, iid = min(cands) if cands else (1e9, None)
            if not s.check(dmin < TOL, f"panneau {si+1} : repère ({P[0]:.0f}, {P[1]:.0f}) sur l'arc d'une pièce (écart {dmin:.2f} mm)"):
                continue
            # ligne de mesure : de ce point jusqu'au bord de référence
            ln = [l for l in lines if (abs(l['x2'] - c['x']) < 0.02 and abs(l['y2'] - c['y']) < 0.02)]
            ref, val = None, None
            if ln and math.hypot(ln[0]['x2'] - ln[0]['x1'], ln[0]['y2'] - ln[0]['y1']) < 0.05:
                ln = []   # ligne de longueur nulle : repère SUR le bord (cote 0)
            if ln:
                l = ln[0]
                vert = abs(l['x1'] - l['x2']) < 0.02   # ligne verticale → bord bas / haut ; horizontale → bord gauche / droit
                if vert and abs(l['y1'] - yb) < 0.02: ref, val = 'b', P[1]
                elif vert and abs(l['y1'] - y0) < 0.02: ref, val = 't', g.Q - P[1]
                elif not vert and abs(l['x1'] - x0) < 0.02: ref, val = 'l', P[0]
                elif not vert and abs(l['x1'] - xr) < 0.02: ref, val = 'r', g.P - P[0]
            else:
                # point sur le bord : cote nulle
                on = [e for e, v in (('b', P[1]), ('t', g.Q - P[1]), ('l', P[0]), ('r', g.P - P[0])) if abs(v) < 0.6]
                if on:
                    ref, val = '*' + ''.join(on), 0.0   # bord(s) possibles : la cote est nulle quel que soit le bord de référence
            if not s.check(ref is not None, f"{iid} : repère ({P[0]:.0f}, {P[1]:.0f}) relié à un bord du panneau"):
                continue
            station = P[0] if ref in ('b', 't') else P[1]
            if ref.startswith('*'):
                station = P[0] if any(abs(round(P[0]) - v) <= 1 for v in greys) else P[1]
            if val >= 0.5:
                near = [t for t in q['text'] if t['fill'] == DC and num(t['t']) is not None and abs(num(t['t']) - round(val)) <= 1 and math.hypot(t['x'] - c['x'], t['y'] - c['y']) < 40]
                s.check(near, f"{iid} : cote d'équerre {round(val)} inscrite près du repère")
            s.check(any(abs(round(station) - v) <= 1 for v in greys), f"{iid} : position {round(station)} du repère le long du {ref} inscrite (gris)")
            marks.setdefault(iid, []).append((P[0], P[1], ref, val))
        # chaque arc : extrémités repérées, pas ≤ 520 mm
        for it in sheet:
            I = g.items[it['id']]
            for a in I['arcs']:
                M = marks.get(it['id'], [])
                ends = [a.coords[0], a.coords[-1]]
                ok_end = all(any(math.hypot(m[0] - e[0], m[1] - e[1]) < 1.0 for m in M) for e in ends)
                s.check(ok_end, f"{it['id']} : les deux extrémités de l'arc sont repérées sur la feuille de débit", f"{ends} / {[(round(m[0]), round(m[1])) for m in M]}")
                pos = sorted(a.project(Point(m[0], m[1])) for m in M if a.distance(Point(m[0], m[1])) < TOL)
                gaps = [b - x for x, b in zip(pos, pos[1:])]
                # traçage à la latte : repères rapprochés le long de l'arc et flèche entre deux repères voisins limitée
                sag = max([g.R - math.sqrt(max(g.R ** 2 - (2 * g.R * math.sin(x / 2 / g.R)) ** 2 / 4, 0)) for x in gaps] or [0])
                s.check(pos and max(gaps or [0]) <= 600 and sag <= 20, f"{it['id']} : repères d'arc ≤ 600 mm le long de l'arc et flèche entre repères ≤ 20 mm (max {max(gaps or [0]):.0f} mm, flèche {sag:.1f} mm)")
    return marks


# ---------------------------------------------------------------- plan de pose
def check_plan(s, g):
    r, E = g.r, g.r['plan']
    T = (lambda x, y: (y, x)) if r['rot'] else (lambda x, y: (x, y))
    if g.circ:
        c = [e for e in E['circle'] if e['fill'] == '#fafafa']
        if not s.check(c, 'plan de pose : contour de la dalle'):
            return
        c = c[0]; sc = c['r'] / g.R; cx, cy = c['x'], c['y']
    else:
        rc = [e for e in E['rect'] if e['fill'] == '#fafafa']
        if not s.check(rc, 'plan de pose : contour de la dalle'):
            return
        rc = rc[0]; A, B = (r['sh']['B'], r['sh']['A']) if r['rot'] else (r['sh']['A'], r['sh']['B'])
        sc = rc['w'] / A; cx, cy = rc['x'] + rc['w'] / 2, rc['y'] + rc['h'] / 2
    mm = lambda x, y: ((x - cx) / sc, (cy - y) / sc)
    exp = {}
    for p in r['all']:
        loc = box(*p['cell']).intersection(g.shape)
        if loc.area < 1:
            continue
        exp[p['id']] = affinity.affine_transform(loc, [0, 1, 1, 0, 0, 0]) if r['rot'] else loc
    drawn = [Polygon([mm(*q) for q in path_polys(e['d'])[0]]) for e in E['path'] if e['fill'] in ('#e2c38f', '#efe3c8')]
    s.check(len(drawn) == len(exp), f"plan de pose : {len(drawn)} planches dessinées = {len(exp)}")
    bad = [k for k, P in exp.items() if min((hausdorff(P, d) for d in drawn), default=1e9) > 2.0 / sc * 0.01 + 3]
    s.check(not bad, 'plan de pose : chaque planche à sa place (contour = calepinage)', str(bad[:5]))
    for t in E['text']:
        if t['t'] in exp and t['fw'] == '800':
            p = Point(mm(t['x'], t['y'] - 2))
            owner = min(exp, key=lambda k: exp[k].distance(p))
            s.check(owner == t['t'], f"plan de pose : repère {t['t']} posé sur la planche {t['t']}", f"posé sur {owner}")


# ---------------------------------------------------------------- gabarits 1:1
def map_band(s, pc, E):
    """Repère du gabarit (bande / pièce entière) relu sur ses graduations grises : x_svg → X panneau, y_svg → Y panneau."""
    lab = [t for t in E['text'] if t['fill'] == '#888' and num(t['t']) is not None]
    ticks = [l for l in E['line'] if l['stroke'] == '#888']
    xs, ys = [], []
    for t in lab:
        if t['an'] == 'middle':
            tk = [l for l in ticks if abs(l['x1'] - l['x2']) < 1e-6 and abs(l['x1'] - t['x']) < 0.02]
            if tk: xs.append((tk[0]['x1'], num(t['t'])))
        elif t['an'] == 'end':
            tk = [l for l in ticks if abs(l['y1'] - l['y2']) < 1e-6 and abs(l['y1'] - (t['y'] - 1.2)) < 0.02]
            if tk: ys.append((tk[0]['y1'], num(t['t'])))
    if not xs or not ys:
        return None, 'graduations absentes'
    ax = (xs[-1][1] - xs[0][1]) / (xs[-1][0] - xs[0][0]) if len(xs) > 1 else 1.0
    ay = (ys[-1][1] - ys[0][1]) / (ys[-1][0] - ys[0][0]) if len(ys) > 1 else -1.0
    s.check(abs(ax - 1) < 1e-4 and abs(ay + 1) < 1e-4, f"{pc['id']} : gabarit à l'échelle 1:1 (graduations : {ax:.5f} / {-ay:.5f})")
    bx = xs[0][1] - xs[0][0]; by = ys[0][1] + ys[0][0]
    return (lambda x, y: (x + bx, by - y)), None


def map_chord(s, pc, E):
    ab = sorted([c for c in E['circle'] if 'gab-ab' in c['cls']], key=lambda c: c['x'])
    tx = {}
    for t in E['text']:
        m = re.match(r'^([AB]) : X (-?[\d,]+) · Y (-?[\d,]+)', t['t'])
        if m: tx[m.group(1)] = (num(m.group(2)), num(m.group(3)))
    if len(ab) != 2 or len(tx) != 2:
        return None, 'A / B absents'
    A, B = tx['A'], tx['B']
    a, b = (ab[0]['x'], ab[0]['y']), (ab[1]['x'], ab[1]['y'])
    dS, dP = math.hypot(b[0] - a[0], b[1] - a[1]), math.hypot(B[0] - A[0], B[1] - A[1])
    s.check(abs(dS - dP) < 1.0, f"{pc['id']} : corde AB 1:1 (gabarit {dS:.1f} mm = cotes {dP:.1f} mm)")
    # repère rigide : (a → A, b → B) ; le gabarit est vu côté face (y SVG vers le bas, Y panneau vers le haut → symétrie)
    us, up = ((b[0] - a[0]) / dS, (b[1] - a[1]) / dS), ((B[0] - A[0]) / dP, (B[1] - A[1]) / dP)
    vs, vp = (-us[1], us[0]), (-up[1], up[0])

    def f(x, y):
        u = (x - a[0]) * us[0] + (y - a[1]) * us[1]
        v = (x - a[0]) * vs[0] + (y - a[1]) * vs[1]
        return (A[0] + u * up[0] - v * vp[0], A[1] + u * up[1] - v * vp[1])
    return f, None


def check_gabarits(s, g, sheet_marks, mode):
    r = g.r
    if not g.circ:
        s.check(r['gab'].get('msg') and 'aucune pièce cintrée' in r['gab']['msg'], 'dalle rectangulaire : pas de gabarit (coupes droites)')
        return
    G = r['gab']
    if not s.check('pieces' in G, 'gabarits disponibles', G.get('msg', '')):
        return
    with_arc = [iid for iid, I in g.items.items() if I['arcs']]
    ids = sorted({p['id'] for p in G['pieces']})
    s.check(ids == sorted(with_arc), f"gabarit(s) pour chaque pièce D cintrée ({len(ids)} / {len(with_arc)})", f"en trop {sorted(set(ids)-set(with_arc))} manquants {sorted(set(with_arc)-set(ids))}")
    N = len(r['items'])
    drawn_by, marks_by = {}, {}
    for pc in G['pieces']:
        iid = pc['id']
        if iid not in g.items:
            continue
        I, E = g.items[iid], pc['el']
        tre = rf"^PIÈCE {iid}{' \\(retournée\\)' if I['it']['rot'] else ''}( — ARC \d+/\d+)?( — PARTIE \d+/\d+)? — PANNEAU {I['si']+1} / {N}$"
        s.check(re.match(tre, pc['title']) is not None, f"{iid} : titre du gabarit = feuille de débit", pc['title'])
        f, err = (map_chord if pc['kind'] == 'chord' else map_band)(s, pc, E)
        if not s.check(f is not None, f"{iid} : repère du gabarit lisible ({pc['kind']})", err or ''):
            continue
        arcs = [l for l in E['polyline'] if 'garc' in l['cls']]
        if not s.check(arcs, f"{iid} : arc de découpe tracé"):
            continue
        dr = [LineString([f(*p) for p in a['pts']]) for a in arcs]
        drawn_by.setdefault(iid, []).extend(dr)
        dev = max(g.on_circle(iid, p) for l in dr for p in l.coords)
        s.check(dev < TOL_R, f"{iid} ({pc['kind']}{' '+pc['title'].split(' — ')[1] if pc['title'].count(' — ')>1 else ''}) : arc du gabarit posé (A sur A, B sur B / graduations) = arc de la pièce, rayon R {g.R:.0f} (écart max {dev:.2f} mm)")
        frame = None
        if pc['kind'] != 'chord':
            fr = [e for e in E['rect'] if e['stroke'] == '#999' and e['da']]
            if fr:
                q = fr[0]; p1, p2 = f(q['x'], q['y']), f(q['x'] + q['w'], q['y'] + q['h'])
                frame = box(min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1]))
        else:
            W, Hh = pc['w'], pc['h'] - 36
            frame = Polygon([f(0, 0), f(W, 0), f(W, Hh), f(0, Hh)])
        # hachures = matière à conserver (pièce ∩ cadre du gabarit), du bon côté de l'arc
        ht = [e for e in E['path'] if e['fill'] == 'url(#gj)']
        if s.check(ht, f"{iid} : partie à conserver hachurée"):
            H = Polygon([f(*p) for p in path_polys(ht[0]['d'])[0]]).buffer(0)
            ref = I['pan'].intersection(frame)
            hd = hausdorff(H, ref) if not ref.is_empty else 1e9
            s.check(hd < 1.5, f"{iid} : hachures = pièce du débit, du bon côté de l'arc (écart {hd:.1f} mm)")
        # repères ● rouges : mêmes points et mêmes cotes que la feuille de débit
        gm = [c for c in E['circle'] if 'gmk' in c['cls']]
        sm = sheet_marks.get(iid, [])
        for c in gm:
            P = f(c['x'], c['y'])
            near = min(sm, key=lambda m: math.hypot(m[0] - P[0], m[1] - P[1])) if sm else None
            dd = math.hypot(near[0] - P[0], near[1] - P[1]) if near else 1e9
            if not s.check(dd < TOL, f"{iid} : repère gabarit ({P[0]:.0f}, {P[1]:.0f}) au même point que sur la feuille de débit (écart {dd:.2f})"):
                continue
            marks_by.setdefault(iid, set()).add(sm.index(near))
            s.check(c['data'].get('ref') == near[2] or (near[2].startswith('*') and c['data'].get('ref') in near[2]), f"{iid} : même bord de référence ({c['data'].get('ref')} / {near[2]})")
            tv = [t for t in E['text'] if t['fill'] == DC and num(t['t']) is not None and math.hypot(t['x'] - c['x'], t['y'] - c['y']) < 12]
            if near[3] >= 0.5:
                s.check(any(abs(num(t['t']) - round(near[3])) <= 1 for t in tv), f"{iid} : cote {round(near[3])} inscrite au repère du gabarit", str([t['t'] for t in tv]))
            rf = c['data'].get('ref')
            st = near[0] if rf in ('b', 't') else near[1]
            gv = [t for t in E['text'] if t['fill'] == GREY and t['t'].startswith('@') and math.hypot(t['x'] - c['x'], t['y'] - c['y']) < 14]
            s.check(any(abs(num(t['t']) - round(st)) <= 1 for t in gv), f"{iid} : position @{round(st)} inscrite au repère du gabarit")
        # coin ● du panneau visible si le cadre le contient
        if pc['kind'] != 'chord' and frame is not None and frame.buffer(0.5).contains(Point(0, 0)):
            s.check(any(abs(c['r'] - 2.5) < 1e-6 and math.hypot(*f(c['x'], c['y'])) < 0.6 for c in E['circle']), f"{iid} : coin ● du panneau marqué sur le gabarit")
    # par pièce : tous ses arcs entièrement couverts par ses gabarits ; tous les repères de la feuille de débit repris
    for iid in with_arc:
        I, dr = g.items[iid], drawn_by.get(iid, [])
        for a in I['arcs']:
            cov = unary_union([l.buffer(TOL) for l in dr]).intersection(a).length if dr else 0
            s.check(cov >= a.length - 1.0, f"{iid} : arc de {a.length:.0f} mm entièrement reporté sur le(s) gabarit(s) ({cov:.0f} mm)")
        sm = sheet_marks.get(iid, [])
        s.check(len(marks_by.get(iid, ())) == len(sm), f"{iid} : les {len(sm)} repères de la feuille de débit sont tous sur le(s) gabarit(s) ({len(marks_by.get(iid, ()))})")
    # pages imprimées : 1 unité = 1 mm, aucune mise à l'échelle
    pg = r['pages']
    if pg:
        for p in pg['list']:
            vb = [float(x) for x in p['vb'].split()]
            ok = p['w'].endswith('mm') and abs(float(p['w'][:-2]) - vb[2]) < 1e-6 and abs(float(p['h'][:-2]) - vb[3]) < 1e-6
            s.check(ok and 'scale' not in (p['tr'] or ''), f"page {p['piece']} : imprimée 1:1 (mm, sans mise à l'échelle)", str(p))
            s.check(re.fullmatch(r'translate\([\d.\-]+,[\d.\-]+\)( rotate\(90\))?', p['tr'] or '') is not None, f"page {p['piece']} : pièce seulement déplacée / tournée de 90°", p['tr'])
        ids = {p['piece'] for p in pg['list']}
        s.check(ids == {p['id'] for p in G['pieces']}, f"pages : chaque gabarit imprimé ({len(pg['list'])} page(s) pour {len(G['pieces'])} gabarit(s))", str(set(p['id'] for p in G['pieces']) ^ ids))


# ---------------------------------------------------------------- DXF (plan) : panneaux de platelage et gabarits
def check_dxf(s, g, path, roll_mode=True):
    import ezdxf
    doc = ezdxf.readfile(path)
    ms = list(doc.modelspace())
    pts = lambda e: [tuple(v.dxf.location)[:2] for v in e.vertices] if e.dxftype() == 'POLYLINE' else [tuple(p)[:2] for p in e.get_points()]
    pans = [Polygon(pts(e)) for e in ms if e.dxf.layer == 'CP_PANNEAUX' and e.dxftype() in ('POLYLINE', 'LWPOLYLINE')]
    plat = [Polygon(pts(e)) for e in ms if e.dxf.layer == 'CP_PLATELAGE' and e.dxftype() in ('POLYLINE', 'LWPOLYLINE')]
    txt = [(e.dxf.text, e.dxf.insert[0], e.dxf.insert[1]) for e in ms if e.dxftype() == 'TEXT' and e.dxf.layer == 'CP_TEXTES']
    N = len(g.r['items'])
    seen = 0
    for k, sheet in enumerate(g.r['items']):
        lab = [t for t in txt if re.search(rf'platelage {k+1} \(', t[0])]
        if not s.check(len(lab) == 1, f"DXF : panneau de platelage {k+1} présent"):
            continue
        ids = re.search(r'\(([^)]*)\)', lab[0][0]).group(1).split(' + ')
        s.check(ids == [it['id'] for it in sheet], f"DXF : panneau {k+1} = {' + '.join(it['id'] for it in sheet)}", lab[0][0])
        # cadre du panneau : celui dont le coin haut-gauche est juste sous le libellé
        P = min(pans, key=lambda q: math.hypot(q.bounds[0] - lab[0][1], q.bounds[3] + 30 - lab[0][2]))
        x0, y0 = P.bounds[0], P.bounds[1]
        s.check(abs(P.bounds[2] - x0 - g.P) < 0.5 and abs(P.bounds[3] - y0 - g.Q) < 0.5, f"DXF : panneau {k+1} {g.P}×{g.Q}")
        inside = [affinity.translate(q, -x0, -y0) for q in plat if P.buffer(1).contains(q)]
        for it in sheet:
            I = g.items[it['id']]
            hd = min((hausdorff(q, I['pan']) for q in inside), default=1e9)
            s.check(hd < 1.0, f"DXF : {it['id']} au même endroit et de même forme que sur la feuille de débit (écart {hd:.2f} mm)")
            seen += 1
    # gabarits : arcs du calque GABARIT_DECOUPE au rayon R
    if g.circ:
        arcs = [pts(e) for e in ms if e.dxf.layer == 'GABARIT_DECOUPE' and e.dxftype() in ('POLYLINE', 'LWPOLYLINE')]
        bad, n = 0, 0
        for P in arcs:
            if len(P) < 3:
                n += 1
                continue
            # cercle de rayon R imposé, centre ajusté (Gauss-Newton) : écart maxi des sommets ≤ 0,1 mm (bien conditionné même pour un arc court)
            n += 1
            bad += circ_fixed_dev(P, g.R) > 0.1
        s.check(n >= len(g.r["gab"].get("pieces", [])) and n and not bad, f"DXF : {n} arcs de gabarit (= {len(g.r['gab'].get('pieces', []))} gabarits) au rayon R {g.R:.0f} ({bad} faux)")


def circ_fixed_dev(P, R):
    """Écart maxi des points à un cercle de rayon R imposé dont le centre est ajusté (moindres carrés, Gauss-Newton)."""
    import numpy as np
    pts = np.array(P, float)
    m = pts.mean(axis=0)
    # départ : centre du côté concave (cercle par 3 points), sinon décalage perpendiculaire
    a, b, c = pts[0], pts[len(pts) // 2], pts[-1]
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) > 1e-9:
        A, B, C = a @ a, b @ b, c @ c
        ctr = np.array([(A * (b[1] - c[1]) + B * (c[1] - a[1]) + C * (a[1] - b[1])) / d, (A * (c[0] - b[0]) + B * (a[0] - c[0]) + C * (b[0] - a[0])) / d])
    else:
        ctr = m + np.array([0, R])
    for _ in range(50):
        v = pts - ctr; dist = np.linalg.norm(v, axis=1); res = dist - R
        J = -v / dist[:, None]
        step, *_ = np.linalg.lstsq(J, -res, rcond=None)
        ctr = ctr + step
        if np.linalg.norm(step) < 1e-9:
            break
    return float(np.max(np.abs(np.linalg.norm(pts - ctr, axis=1) - R)))
