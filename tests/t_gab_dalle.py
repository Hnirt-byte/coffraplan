"""Point 2 (v19) — campagne poussée : dalle de couverture, gabarits 1:1 ↔ feuilles CP À DÉCOUPER ↔ plan de pose.
Vérification géométrique indépendante (shapely) sur un grand nombre de configurations (voir gabcheck.py)."""
import json, os, sys, time
from lib import run, HERE, OUT, Suite
import gabcheck as GC

BM = lambda *L: [{'o': o, 'b': b, 'h': h, 'po': po} for (o, b, h, po) in L]
CFGS = [
    ('Ø6 défaut', {}, {}, 'band', 'roll', 914),
    ('Ø6 pièce entière', {}, {}, 'full', 'roll', 914),
    ('Ø6 A3', {}, {}, 'band', 'A3', 914),
    ('Ø6 A4', {}, {}, 'band', 'A4', 914),
    ('Ø6 entière rouleau 1067', {}, {}, 'full', 'roll', 1067),
    ('Ø6 rouleau 610', {}, {}, 'band', 'roll', 610),
    ('Ø2,0', {'dlD': 2.0}, {}, 'band', 'roll', 914),
    ('Ø2,4', {'dlD': 2.4}, {}, 'band', 'roll', 914),
    ('Ø2,4 entière', {'dlD': 2.4}, {}, 'full', 'roll', 914),
    ('Ø3,1', {'dlD': 3.1}, {}, 'band', 'roll', 914),
    ('Ø4,3', {'dlD': 4.3}, {}, 'band', 'roll', 914),
    ('Ø5,15 joints alignés', {'dlD': 5.15, 'dlJ': 'ali'}, {}, 'band', 'roll', 914),
    ('Ø7,5 décalés 3/panneau', {'dlD': 7.5, 'dlJ': 'dec', 'dlG': '3'}, {}, 'band', 'roll', 914),
    ('Ø8 1/panneau', {'dlD': 8, 'dlG': '1'}, {}, 'band', 'roll', 914),
    ('Ø9,2 entraxe 625', {'dlD': 9.2, 'dlE': 625}, {}, 'band', 'roll', 914),
    ('Ø10 entraxe 400 mini 300', {'dlD': 10, 'dlE': 400, 'dlMin': 300}, {}, 'band', 'roll', 914),
    ('Ø12', {'dlD': 12}, {}, 'band', 'roll', 914),
    ('Ø6 CP 2500×1525', {}, {'cpf': '2500x1525'}, 'band', 'roll', 914),
    ('Ø6,8 CP 3000×1500', {'dlD': 6.8}, {'cpf': '3000x1500'}, 'band', 'roll', 914),
    ('Ø6 trait de scie 0', {'dlK': 0}, {}, 'band', 'roll', 914),
    ('Ø6 trait de scie 8 mini 0', {'dlK': 8, 'dlMin': 0}, {}, 'band', 'roll', 914),
    ('Ø6 poutre centrale', {'dlPt': True}, {}, 'band', 'roll', 914),
    ('Ø8 poutre centrale', {'dlPt': True, 'dlD': 8}, {}, 'band', 'roll', 914),
    ('Ø8 2 poutres ±1500', {'dlPt': True, 'dlD': 8}, {'dlBm': BM((-1500, 300, 400, []), (1500, 300, 400, []))}, 'band', 'roll', 914),
    ('Ø9 poutre excentrée + poteaux', {'dlPt': True, 'dlD': 9}, {'dlBm': BM((700, 400, 500, [{'s': -1500, 'D': 400}, {'s': 1500, 'D': 400}]))}, 'band', 'roll', 914),
    ('Ø7 3 poutres entière', {'dlPt': True, 'dlD': 7}, {'dlBm': BM((-2000, 250, 400, []), (0, 250, 400, []), (1800, 250, 400, []))}, 'full', 'roll', 914),
    ('Ø6 poutre ∥ l', {'dlPt': True}, {'dlPdir': 'l'}, 'band', 'roll', 914),
    ('Ø6 rive', {'dlRv': True}, {}, 'band', 'roll', 914),
    # v2.0 : « arc générique » supprimé (gabarits tirés du plan de découpe uniquement, décision utilisateur) → configuration retirée
    ('rect 5000×4000', {'dlF': 'rect'}, {}, 'band', 'roll', 914),
    ('rect 5300×3700 poutre', {'dlF': 'rect', 'dlL': 5300, 'dlW': 3700, 'dlPt': True}, {}, 'band', 'roll', 914),
    ('carré 4100', {'dlF': 'carre', 'dlL': 4100}, {}, 'band', 'roll', 914),
]

# balayage pseudo-aléatoire (graine fixe → reproductible) : Ø, entraxe, format CP, joints, découpes / panneau, mini, trait de scie,
# poutres (0 à 3, position, largeur, poteaux), mode de gabarit, largeur de rouleau
import random
_rd = random.Random(19)
for k in range(60):
    D = round(_rd.uniform(2.2, 14.0), 2); R = D * 500
    ov = {'dlD': D, 'dlE': _rd.choice([300, 400, 417, 500, 600, 625, 750]), 'dlJ': _rd.choice(['auto', 'ali', 'dec']), 'dlG': _rd.choice(['1', '2', '3']),
          'dlMin': _rd.choice([0, 200, 300, 500, 700]), 'dlK': _rd.choice([0, 3, 4, 6])}
    ex = {'cpf': _rd.choice(['2500x1250', '2500x1250', '2500x1525', '3000x1500'])}
    nb = _rd.choice([0, 0, 1, 1, 2, 3]) if D >= 4 else 0
    if nb:
        ov['dlPt'] = True; L = []
        for j in range(nb):
            for _ in range(30):
                o = round(_rd.uniform(-0.6, 0.6) * R / 50) * 50
                if all(abs(o - x[0]) > 900 for x in L): break
            b = _rd.choice([200, 250, 300, 400]); po = [{'s': round(_rd.uniform(-0.5, 0.5) * R / 50) * 50, 'D': _rd.choice([300, 400])}] if _rd.random() < 0.3 else []
            L.append((o, b, _rd.choice([300, 400, 500]), po))
        ex['dlBm'] = BM(*sorted(L)); ex['dlPdir'] = _rd.choice(['L', 'l'])
    CFGS.append((f'aléa {k+1:02d} Ø{D}', ov, ex, _rd.choice(['band', 'band', 'full']), 'roll', _rd.choice([610, 841, 914, 914, 1067])))


def cfg_js(ov, extra, gm, mode, roll):
    st = {}
    if 'cpf' in extra:
        st['cp'] = {'j': {'t': 'filme', 'e': 18, 'f': extra['cpf']}, 'fi': {'t': 'filme', 'e': 18, 'f': extra['cpf']}, 'fs': {'t': 'filme', 'e': 18, 'f': extra['cpf']}}
    for k in ('dlBm', 'dlPdir'):
        if k in extra:
            st[k] = extra[k]
    return {'ov': ov, 'set': st, 'gm': gm, 'mode': mode, 'roll': roll}


class Pref:
    """Préfixe chaque contrôle par le nom de la configuration ; compte par configuration."""

    def __init__(s, suite, name):
        s.s, s.name, s.ok, s.ko = suite, name, 0, 0

    def check(s, c, label, detail=''):
        r = s.s.check(c, f'[{s.name}] {label}', detail)
        if r: s.ok += 1
        else: s.ko += 1
        return r


STATS = []


def t(s, pg):
    pg.add_script_tag(path=os.path.join(HERE, 'gabx.js'))
    for name, ov, extra, gm, mode, roll in CFGS:
        t0 = time.time()
        r = pg.evaluate('(c)=>GX.run(c)', cfg_js(ov, extra, gm, mode, roll))
        p = Pref(s, name)
        if not p.check(r['ok'], 'calepinage calculé', str(r.get('W'))[:300]):
            continue
        g = GC.Geo(r)
        GC.check_layout(p, g)
        marks = GC.check_cut_sheets(p, g)
        GC.check_plan(p, g)
        if gm == 'arc':
            # arc générique : un seul gabarit ; arc (commande A du chemin) au rayon de la dalle, corde et ordonnées relues
            import math, re
            gp = r['gab']['pieces']
            p.check(len(gp) == 1, 'arc générique : un gabarit')
            E = gp[0]['el']
            cut = [e for e in E['path'] if e['stroke'] == '#000' and e['sw'] >= 0.8]
            mA = re.findall(r'M([\d.\-]+),([\d.\-]+) A([\d.]+),([\d.]+) 0 0,1 ([\d.\-]+),([\d.\-]+)', cut[0]['d']) if cut else []
            if p.check(mA, 'arc générique : arc de découpe tracé'):
                x1, y1, rx, ry, x2, y2 = map(float, mA[0])
                p.check(abs(rx - g.R) < 0.01 and abs(ry - g.R) < 0.01, f'arc générique au rayon R {g.R:.0f} (lu {rx:.2f})')
                c = math.dist((x1, y1), (x2, y2)); yc = math.sqrt(g.R ** 2 - c ** 2 / 4)
                bad = 0; n = 0
                for t in E['text']:
                    v = GC.num(t['t'])
                    if t['fill'] == '#333' and v is not None:
                        xx = t['x'] - 1 - (x1 + x2) / 2; n += 1
                        bad += abs((math.sqrt(g.R ** 2 - xx ** 2) - yc) - v) > 0.06
                p.check(n > 3 and not bad, f'arc générique : {n} ordonnées depuis la corde exactes ({bad} fausses)')
        else:
            GC.check_gabarits(p, g, marks, mode)
        if gm != 'arc':
            import base64
            b64 = pg.evaluate('''()=>{const f=dxfPlanFile(GX.last);let s='';const u=f.bytes;for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return btoa(s)}''')
            fp = os.path.join(OUT, 'dalle_tmp.dxf'); open(fp, 'wb').write(base64.b64decode(b64))
            GC.check_dxf(p, g, fp, mode == 'roll' and roll == 914 and gm == 'band')
        STATS.append({'cfg': name, 'R': g.R, 'panneaux': len(r['items']), 'D': r['nD'], 'E': r['nE'],
                      'gabarits': len(r['gab'].get('pieces', [])), 'kinds': sorted({x['kind'] for x in r['gab'].get('pieces', [])}),
                      'contrôles': p.ok + p.ko, 'KO': p.ko, 'ms_app': r['ms'], 's': round(time.time() - t0, 1)})
    json.dump(STATS, open(os.path.join(OUT, 't_gab_dalle_stats.json'), 'w'), ensure_ascii=False, indent=1)
    for x in STATS:
        print(f"  {x['cfg']:<32} R{x['R']:>6.0f}  {x['panneaux']:>3} pann. {x['D']:>3} D {x['E']:>3} E  {x['gabarits']:>3} gab. {','.join(x['kinds']):<16} {x['contrôles']:>5} contrôles  {x['KO']:>3} KO  {x['s']}s")


if __name__ == '__main__':
    sys.exit(0 if run('t_gab_dalle', t) else 1)
