"""v2.1 — Forme spéciale, poteaux : traversent la base et le fond sup. (du dessous de la boîte au dessus du fond sup. / en tête),
fonds percés (débit, feuille CP À DÉCOUPER, gabarit, DXF, 3D), conflit avec la forme concentrique seulement si le poteau coupe
sa PAROI. Plus de messages de hauteur de poteau."""
import math, json
from lib import run

JS = r'''(c)=>{const d0=T.mk('special',c.ov),d=T.can(d0),Z=specGeo(d),W=checks(d,null),R=debit(d,null),sc=model3(d,R);
  const tubes=sc.solids.filter(o=>o.nm==='tube carton').map(o=>bb3(o));
  const fonds=R.filter(r=>/^(Base|Fond sup)/.test(r.n)).map(r=>({n:r.n,txt:r.txt||'',note:r.note||'',drill:r.drill||null}));
  const N=cutNest(d,R).N,items=Object.values(N).flatMap(n=>n.sheets.flat()).filter(p=>/^(Base|Fond sup)/.test(p.line&&p.line.n||'')).map(p=>({tag:p.tag,poly:p.poly,drill:p.drill}));
  const pages=cpCutPages(d,R).map(p=>p[2]).join(''),nDrawn=(pages.match(/class="cpdrill"/g)||[]).length;
  const GP=gabPieces(d,'roll'),gd=GP.pieces?GP.pieces.map(p=>({id:p.id,n:(p.svg.match(/class="gdrill"/g)||[]).length,
     c:[...p.svg.matchAll(/class="gdrill" cx="([\d.\-]+)" cy="([\d.\-]+)" r="([\d.]+)"/g)].map(m=>[+m[1],+m[2],+m[3]]),
     arc:[...p.svg.matchAll(/class="garc" points="([^"]+)"/g)].map(m=>m[1].trim().split(/\s+/).map(q=>q.split(',').map(Number)))})):[];
  let dxf=0;try{const f=dxfPlanFile(d0);dxf=(new TextDecoder('latin1').decode(f.bytes).match(/\nCP_PERCAGES\r?\n/g)||[]).length}catch(e){dxf=-1}
  const ov=overlap3(sc,0.5,6).filter(x=>/tube/.test(x.a+x.b));
  const sec=gen(d0);
  return{W,pH:d.pH,zPt:Z.zPt,zi:Z.zi,zb:Z.zb,h:d.h,pD:d.pD,pJ:d.pJ,pR:d.pR,A:potAngles(d),tubes,fonds,items,nDrawn,gd,dxf,ov,conc:d.conc?[concW1(d),concW1(d)+d.ep]:null,sup:Z.sup}}'''

CASES = [
    ('circ, poteaux dans la forme concentrique', {'dBase': 'circ', 'oConc': True, 'oFondSup': True, 'oPot': True, 'oPR': 200, 'oPD': 200}, 'none'),
    ('circ, poteaux hors de la forme concentrique', {'dBase': 'circ', 'dD': 1600, 'oConc': True, 'oDint': 600, 'oFondSup': True, 'oPot': True, 'oPR': 550, 'oPD': 200}, 'none'),
    ('circ, poteaux à cheval sur la paroi concentrique', {'dBase': 'circ', 'oConc': True, 'oFondSup': True, 'oPot': True, 'oPR': 390, 'oPD': 120}, 'conflict'),
    ('circ, poteaux tangents à l\'extérieur de la paroi', {'dBase': 'circ', 'dD': 1400, 'oConc': True, 'oFondSup': True, 'oPot': True, 'oPR': 460, 'oPD': 120}, 'none'),
    ('rect, fond sup. en tête', {'dBase': 'rect', 'oFondSup': True, 'oPot': True, 'oPR': 300, 'oPD': 200}, 'none'),
    ('rect, fond sup. abaissé à 250', {'dBase': 'rect', 'dh': 400, 'oFondSup': True, 'oFSN': 250, 'oPot': True, 'oPR': 300, 'oPD': 160}, 'none'),
    ('rect, sans fond sup.', {'dBase': 'rect', 'oFondSup': False, 'oPot': True, 'oPR': 300, 'oPD': 200}, 'none'),
    ('circ, poteaux courts (h 150 depuis le dessous)', {'dBase': 'circ', 'oFondSup': True, 'oPot': True, 'oPR': 250, 'oPD': 150, 'oPH': 150}, 'none'),
    ('circ, 5 poteaux angles personnalisés', {'dBase': 'circ', 'dD': 1500, 'oFondSup': True, 'oPot': True, 'oPR': 500, 'oPD': 180, 'oPDisp': 'custom', 'oPAngles': '0, 60, 150, 200, 300'}, 'none'),
    ('circ grand Ø 3000 (fond en morceaux)', {'dBase': 'circ', 'dD': 3000, 'oFondSup': True, 'oPot': True, 'oPN': 4, 'oPR': 1000, 'oPD': 300}, 'none'),
]


def t(s, pg):
    for nm, ov, exp in CASES:
        r = pg.evaluate(JS, {'ov': ov})
        W = [m for _, m in r['W']]
        s.check(not any('hauteur intérieure' in m or 'entrent dans le fond' in m or 'font foi' in m for m in W), f'[{nm}] plus de message de hauteur / nombre de poteaux', str(W))
        conf = [m for m in W if 'concentrique' in m and 'Poteau' in m]
        s.check(bool(conf) == (exp == 'conflict'), f"[{nm}] conflit avec la forme concentrique {'signalé' if exp == 'conflict' else 'non signalé'}", str(conf))
        # hauteur : du dessous de la boîte (0) au dessus du fond sup. (ou en tête), sauf h saisie
        top = ov.get('oPH') or r['zPt']
        s.check(abs(r['pH'] - top) < 0.01, f"[{nm}] tête des poteaux à {top} (dessus du fond sup. / en tête)", str(r['pH']))
        s.check(r['tubes'] and all(abs(b[2]) < 0.6 and abs(b[5] - top) < 0.6 for b in r['tubes']), f'[{nm}] 3D : tubes du dessous de la boîte (0) à {top}', str([[round(x) for x in b] for b in r['tubes']][:2]))
        bad = [x for x in r['ov'] if not (exp == 'conflict' and 'concentrique' in x['a'] + x['b'])]
        s.check(not bad, f'[{nm}] 3D : tubes dans les perçages, aucune interpénétration (hors conflit signalé)', str(bad[:2]))
        if exp == 'conflict':
            s.check(any('concentrique' in x['a'] + x['b'] for x in r['ov']), f'[{nm}] 3D : le conflit signalé existe bien (tube / paroi concentrique)')
        n = len(r['A']); Dp = r['pD'] + r['pJ']
        base = [f for f in r['fonds'] if f['n'].startswith('Base')]
        sup = [f for f in r['fonds'] if f['n'].startswith('Fond sup')]
        s.check(base and base[0]['drill'] and len(base[0]['drill']) == n and f'percé {n} × Ø{round(Dp)}' in base[0]['note'], f'[{nm}] base percée {n} × Ø{Dp:.0f} (débit)', json.dumps(base)[:300])
        if r['sup']:
            should = top > r['zi'] + 0.5
            s.check(bool(sup and sup[0]['drill']) == should, f"[{nm}] fond sup. {'percé' if should else 'non percé'} (tête des poteaux {top} / dessous du fond sup. {r['zi']:.0f})")
        # perçages : positions (depuis le centre de la pièce = centre de la boîte), y compris fond en morceaux
        for it in [i for i in r['items'] if i['drill']]:
            pass
        allD = [q for i in r['items'] for q in (i['drill'] or [])]
        nF = len([f for f in r['fonds'] if f['drill']])
        # un perçage à cheval sur un joint de fond appartient aux deux morceaux (demi-perçage de chaque côté)
        ids = {(q['i'], fi) for fi, i in enumerate(r['items']) for q in (i['drill'] or [])}
        s.check(len(allD) >= n * nF and len({q['i'] for q in allD}) == n, f'[{nm}] perçages reportés sur les pièces imbriquées ({len(allD)} pour {n} × {nF})')
        s.check(r['nDrawn'] == len(allD), f'[{nm}] perçages dessinés sur la feuille CP À DÉCOUPER ({r["nDrawn"]})')
        for i in r['items']:
            if not i['drill']:
                continue
            P = i['poly']; xs = [p[0] for p in P]; ys = [p[1] for p in P]
            s.check(all(min(xs) - q['D'] / 2 <= q['x'] <= max(xs) + q['D'] / 2 and min(ys) - q['D'] / 2 <= q['y'] <= max(ys) + q['D'] / 2 for q in i['drill']), f"[{nm}] {i['tag']} : perçages sur la pièce")
        # gabarit des fonds circulaires : perçages au bon rayon et au bon angle depuis le centre du disque
        for g in r['gd']:
            if not g['c']:
                continue
            closed = [a for a in g['arc'] if math.dist(a[0], a[-1]) < 0.5]
            if not closed:
                continue
            P = closed[0]; cx = sum(p[0] for p in P[:-1]) / (len(P) - 1); cy = sum(p[1] for p in P[:-1]) / (len(P) - 1)
            rr = [math.hypot(x - cx, y - cy) for x, y, _ in g['c']]
            s.check(all(abs(v - r['pR']) < 0.6 for v in rr), f"[{nm}] gabarit {g['id']} : perçages à {r['pR']} mm du centre ({[round(v, 1) for v in rr]})")
            s.check(all(abs(rad - Dp / 2) < 0.01 for _, _, rad in g['c']), f"[{nm}] gabarit {g['id']} : perçages Ø{Dp:.0f}")
            # angles relatifs entre poteaux identiques au plan (le gabarit peut être tourné de 90° par l'imbrication)
            ang = [math.degrees(math.atan2(-(y - cy), x - cx)) % 360 for x, y, _ in g['c']]   # SVG y vers le bas → vue de dessus
            rel = sorted(round((a - ang[0]) % 360, 1) for a in ang)
            exp_rel = sorted(round((a - r['A'][0]) % 360 * -1 % 360, 1) for a in r['A'])  # angles du plan : sens horaire
            s.check(all(min(abs(x - y), 360 - abs(x - y)) < 0.5 for x, y in zip(rel, exp_rel)), f"[{nm}] gabarit {g['id']} : écarts angulaires des perçages = plan", f'{rel} / {exp_rel}')
        s.check(r['dxf'] == len(allD), f'[{nm}] DXF : {len(allD)} perçages (calque CP_PERCAGES)', str(r['dxf']))
    # migration : h poteau saisie en v19 (au-dessus de la base) → hauteur depuis le dessous (même niveau de tête)
    r = pg.evaluate('''()=>{const d=T.mk('special',{dBase:'circ',oFondSup:true,oPot:true,oPR:250,oPD:150,oPH:200});d.v=11;const m=migr(d);return [m.v,m.pH,d.cp.fi.e]}''')
    s.check(r[0] == 12 and abs(r[1] - (200 + r[2])) < 1e-6, f'migration v11 → v12 : h poteau {r[1]} = 200 + base {r[2]}', str(r))
    r = pg.evaluate('''()=>{const d=T.mk('special',{dBase:'circ',oFondSup:true,oPot:true,oPR:250,oPD:150,oPH:200});return [d.v,migr(d).pH]}''')
    s.check(r == [12, 200], 'plan v12 : h poteau inchangée au chargement', str(r))
    # angles personnalisés : nombre de poteaux = nombre d'angles, champ « Nombre » masqué
    r = pg.evaluate('''()=>{const d=T.mk('special',{dBase:'circ',oPot:true,oPDisp:'custom',oPAngles:'10, 100, 200'});return [d.pN,el('zPN').style.display]}''')
    s.check(r == [3, 'none'], 'angles personnalisés : nombre = nombre d\'angles, champ masqué', str(r))


if __name__ == '__main__':
    import sys
    sys.exit(0 if run('t_special', t) else 1)
