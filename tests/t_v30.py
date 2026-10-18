"""v3.0 — exports 3D / BIM et gel avant bêta :
  1. IFC4 (36 scénarios + 10 plans aléatoires par forme) : relu par ifcopenshell sans erreur de schéma ; structure projet / site /
     bâtiment / niveau, un IfcElementAssembly par ouvrage nommé par son repère ; une pièce par pièce du débit (même repère, même
     nombre) ; volumes de CP et de bois = débit (± 1 %) ; jeu de propriétés « CoffraPlan » et quantités ; volume géométrique
     (ifcopenshell) = quantité déclarée (scénarios) ;
  2. glTF binaire, assemblé et éclaté : en-tête et blocs GLB, un nœud par ouvrage, un nœud par pièce nommé par son repère,
     couleurs de la palette, mètres et Y vers le haut, volume des maillages = volume IFC, éclaté plus étendu ;
  3. carte Export et vue 3D : boutons et téléchargements ;
  4. cotes d'implantation : axes X / Y de l'ouvrage et cotes signées en bleu sur les vues en plan ;
  5. version v3.0.
Écarts connus, hors comparaison au débit : poutrelles de la dalle (étaiement, hors débit) ; tubes carton et tube PVC (hors débit)."""
import base64, json, os, re, struct, sys, tempfile
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.element as ue, ifcopenshell.util.shape, ifcopenshell.validate
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE

N = int(os.environ.get('V30_N', '10'))
GEN = r'''async ([kind,a,b])=>{let d0;if(kind==='scn')d0=T.mk(a[1],a[2],a[3]);else{d0=AX.make(a,b);d0.date='2026-10-10';const dd=canon(migr(d0)),g=dd.forme==='voile'?voileGeo(dd):null;if(badDims(checks(dd,g))||limErr(dd).length)return null}
  const b64=u=>{let s='';for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return btoa(s)};
  const M=bimModel(d0,false),d=M.d,R=debit(d,d.forme==='voile'?voileGeo(d):null),rows=debitRows(d0),par=new Set(rows.filter(r=>rows.some(q=>q.tag===r.tag+'a')).map(r=>r.tag));
  const cp=R.filter(r=>['j','fi','fs'].includes(r.k)),vb=(R.bois||[]).reduce((s,x)=>{const m=String(x.n).match(/(\d+)\s*[×x]\s*(\d+)/);return s+(m?x.q*x.L*m[1]*m[2]:0)},0);
  const f=ifcFile(d0),o={ref:d.ref,ch:d.ch,ifc:b64(f.bytes),qt:Object.fromEntries(rows.filter(r=>!par.has(r.tag)).map(r=>[r.tag,+r.qt])),vcp:cp.reduce((s,r)=>s+r.m2*1e6*cpOf(d,r.k).e,0)/1e9,vb:vb/1e9,
    pal:Object.fromEntries(Object.entries(C3)),Zx:[Math.min(...M.pcs.map(p=>Math.min(...p.S.map(s=>bb3(s)[2])))),Math.max(...M.pcs.map(p=>Math.max(...p.S.map(s=>bb3(s)[5]))))]};
  if(kind==='scn'){o.glb=b64((await glbFile(d0,false)).bytes);o.glbx=b64((await glbFile(d0,true)).bytes)}return o}'''


def glb(raw):
    """GLB → (json, {nom de nœud: [volume m³, ...]}, boîte englobante)"""
    mg, ver, ln = struct.unpack('<III', raw[:12])
    jl, jt = struct.unpack('<II', raw[12:20]); js = json.loads(raw[20:20 + jl])
    bl, bt = struct.unpack('<II', raw[20 + jl:28 + jl]); bn = raw[28 + jl:28 + jl + bl]
    ok = mg == 0x46546C67 and ver == 2 and ln == len(raw) and jt == 0x4E4F534A and bt == 0x004E4942 and jl % 4 == 0 and bl == js['buffers'][0]['byteLength']
    vols, lo, hi = {}, [1e9] * 3, [-1e9] * 3
    for nd in js['nodes']:
        if 'mesh' not in nd:
            continue
        pr = js['meshes'][nd['mesh']]['primitives'][0]
        a = js['accessors'][pr['attributes']['POSITION']]; v = js['bufferViews'][a['bufferView']]
        P = struct.unpack_from('<%df' % (3 * a['count']), bn, v['byteOffset'])
        V = 0
        for i in range(0, len(P), 9):  # sommets non partagés : triangles consécutifs
            x1, y1, z1, x2, y2, z2, x3, y3, z3 = P[i:i + 9]
            V += (x1 * (y2 * z3 - z2 * y3) - y1 * (x2 * z3 - z2 * x3) + z1 * (x2 * y3 - y2 * x3)) / 6
        for k in range(3):
            lo[k] = min(lo[k], min(P[k::3])); hi[k] = max(hi[k], max(P[k::3]))
        vols.setdefault(nd['name'], []).append(abs(V))
    return ok, js, vols, (lo, hi)


def t(s):
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        ev = pg.evaluate
        pg.add_script_tag(path=os.path.join(HERE, 'auditx.js'))
        jobs = [('scn ' + x[0], ['scn', x, 0]) for x in ev('SCN')]
        jobs += [(f'{f} #{k}', ['aud', f, 7000 + k]) for f in ev("[...el('iForme').options].map(o=>o.value)") for k in range(N)]
        st = ifcopenshell.geom.settings()
        tmp = tempfile.mkdtemp()
        for name, arg in jobs:
            try:
                r = ev(GEN, arg)
            except Exception as ex:
                s.check(False, f'[{name}] export', str(ex)[:300]); continue
            if r is None:
                continue
            p = os.path.join(tmp, 'x.ifc'); open(p, 'wb').write(base64.b64decode(r['ifc']))
            f = ifcopenshell.open(p)
            log = ifcopenshell.validate.json_logger(); ifcopenshell.validate.validate(f, log, express_rules=False)
            s.check(not log.statements, f'[{name}] IFC4 conforme au schéma (ifcopenshell)', str([x['message'][:120] for x in log.statements[:2]]))
            sp = [len(f.by_type(c)) for c in ('IfcProject', 'IfcSite', 'IfcBuilding', 'IfcBuildingStorey', 'IfcElementAssembly')]
            asm = f.by_type('IfcElementAssembly')
            u = f.by_type('IfcSIUnit'); mm = any(x.UnitType == 'LENGTHUNIT' and x.Prefix == 'MILLI' for x in u)
            s.check(sp == [1, 1, 1, 1, 1] and asm[0].Name == r['ref'] and mm and asm[0].ContainedInStructure[0].RelatingStructure.is_a('IfcBuildingStorey'),
                    f'[{name}] projet / site / bâtiment / niveau, un ouvrage « {r["ref"]} », unités mm', str(sp))
            els = [e for e in f.by_type('IfcElement') if not e.is_a('IfcElementAssembly')]
            s.check(len(els) == len(asm[0].IsDecomposedBy[0].RelatedObjects), f'[{name}] toutes les pièces dans l\'ouvrage')
            cnt, vcp, vb, bad = {}, 0, 0, []
            for e in els:
                ps = ue.get_psets(e); cpp = ps.get('CoffraPlan', {}); q = [v for k, v in ps.items() if k.startswith('Qto_')]
                if not (cpp and set(cpp) >= {'Repère', 'Désignation', 'Dimensions', 'Épaisseur', 'Matériau', 'Chantier', 'Référence du plan'} and q and q[0].get('NetVolume', 0) > 0 and cpp['Référence du plan'] == r['ref']):
                    bad.append(e.Name); continue
                if cpp['Repère']:
                    cnt[cpp['Repère']] = cnt.get(cpp['Repère'], 0) + 1
                    s.check(e.Name == cpp['Repère'] == e.Tag, f'[{name}] pièce nommée par son repère', e.Name)
                gv = q[0].get('GrossVolume', q[0]['NetVolume'])
                if e.is_a('IfcPlate') or (e.is_a('IfcBuildingElementProxy') and e.ObjectType == 'Poche'):
                    vcp += gv
                elif e.is_a('IfcMember') and 'poutrelle' not in e.Name:
                    vb += gv
                if name.startswith('scn'):
                    try:
                        gvol = ifcopenshell.util.shape.get_volume(ifcopenshell.geom.create_shape(st, e).geometry)
                    except Exception as ex:
                        gvol = -1
                    if abs(gvol - q[0]['NetVolume']) > max(0.01 * q[0]['NetVolume'], 1e-6):
                        bad.append(f'{e.Name} géométrie {gvol:.6f} ≠ {q[0]["NetVolume"]:.6f} m³')
            s.check(not bad, f'[{name}] propriétés, quantités et géométrie de chaque pièce', str(bad[:4]))
            dq = [(t, n, cnt.get(t, 0)) for t, n in r['qt'].items() if n != cnt.get(t, 0)] + [(t, 0, n) for t, n in cnt.items() if t not in r['qt']]
            s.check(not dq, f'[{name}] une pièce IFC par pièce du débit (repère et nombre)', str(dq[:5]))
            s.check(abs(vcp - r['vcp']) <= max(0.01 * r['vcp'], 2e-5) and abs(vb - r['vb']) <= max(0.01 * r['vb'], 2e-5),
                    f'[{name}] volumes IFC = débit (CP {vcp:.4f} / {r["vcp"]:.4f} m³, bois {vb:.4f} / {r["vb"]:.4f} m³)')
            if 'glb' not in r:
                continue
            ok, js, vols, (lo, hi) = glb(base64.b64decode(r['glb']))
            okx, jsx, volx, (lox, hix) = glb(base64.b64decode(r['glbx']))
            s.check(ok and okx, f'[{name}] GLB : en-tête, blocs JSON et binaire')
            root = js['nodes'][js['scenes'][0]['nodes'][0]]
            s.check(len(js['scenes'][0]['nodes']) == 1 and root['name'].startswith(r['ref']) and len(root['children']) == len(els) and len(jsx['nodes']) == len(js['nodes']),
                    f'[{name}] glTF : un nœud par ouvrage, un nœud par pièce ({len(root.get("children", []))} / {len(els)} IFC)')
            nm = sorted(n['name'] for n in js['nodes'] if 'mesh' in n)
            s.check(nm == sorted(e.Name for e in els), f'[{name}] glTF : mêmes noms (repères) que l\'IFC')
            lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
            pal = [[lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5)] for h in r['pal'].values()]
            s.check(all(any(max(abs(x - y) for x, y in zip(m['pbrMetallicRoughness']['baseColorFactor'][:3], c)) < 1e-4 for c in pal) and m['doubleSided'] for m in js['materials']),
                    f'[{name}] glTF : couleurs de la palette ({len(js["materials"])} matériaux)')
            s.check(abs((hi[1] - lo[1]) - (r['Zx'][1] - r['Zx'][0]) / 1000) < 0.002, f'[{name}] glTF : mètres, Y vers le haut (hauteur {hi[1] - lo[1]:.3f} m)')
            iv = {}
            for e in els:
                iv.setdefault(e.Name, []).append([v for k, v in ue.get_psets(e).items() if k.startswith('Qto_')][0]['NetVolume'])
            dv = [k for k in iv if abs(sum(iv[k]) - sum(vols.get(k, [0]))) > max(0.012 * sum(iv[k]), 2e-6) or abs(sum(vols.get(k, [0])) - sum(volx.get(k, [0]))) > 1e-6 * max(1, len(vols.get(k, [])))]
            s.check(not dv, f'[{name}] glTF : volume des pièces = IFC, inchangé en éclaté', str(dv[:4]))
            s.check(all(hix[k] - lox[k] >= hi[k] - lo[k] - 1e-6 for k in range(3)) and any(hix[k] - lox[k] > hi[k] - lo[k] + 0.01 for k in range(3)) or len(els) < 2,
                    f'[{name}] glTF éclaté plus étendu que l\'assemblé')
        # ---- 3. carte Export et vue 3D ----
        ev("T.mk('special',{dBase:'circ',oPot:true,oFondSup:true});openExport()")
        for bt, ext in (('#exIfc', '.ifc'), ('#exGlb', '.glb')):
            with pg.expect_download() as dl:
                pg.click(bt)
            s.check(dl.value.suggested_filename == 'TEST_R01' + ext, f'carte Export : {bt} télécharge TEST_R01{ext}', dl.value.suggested_filename)
        pg.check('#exGx')
        with pg.expect_download() as dl:
            pg.click('#exGlb')
        s.check(dl.value.suggested_filename == 'TEST_R01_eclate.glb', 'carte Export : glTF éclaté (case cochée)', dl.value.suggested_filename)
        ev("closeModal();open3D()")
        with pg.expect_download() as dl:
            pg.click('#v3glb')
        s.check(dl.value.suggested_filename == 'TEST_R01.glb', 'vue 3D : bouton glTF', dl.value.suggested_filename)
        ev("close3D()")
        # ---- 4. cotes d'implantation (axes de l'ouvrage) ----
        for f, ov in (('rect_fond', {'dL': 1500, 'dl': 1100}), ('special', {'dBase': 'circ', 'oPot': True}), ('circ_fond', {})):
            r = ev("""([f,ov])=>{T.mk(f,ov);const t=document.createElement('template');t.innerHTML=gen(coll());const sv=[...t.content.querySelectorAll('svg')][0],tx=[...sv.querySelectorAll('text')];
              return {bul:tx.filter(x=>/^[XY]$/.test(x.textContent)&&x.getAttribute('fill')==='#1f5fbf').map(x=>x.textContent).sort().join(''),ax:sv.querySelectorAll('line[stroke="#1f5fbf"][stroke-dasharray]').length,
                cot:tx.filter(x=>/^[+−]\\d/.test(x.textContent)&&x.getAttribute('fill')==='#1f5fbf').map(x=>x.textContent)}}""", [f, ov])
            s.check(r['bul'] == 'XY' and r['ax'] >= 2, f'[{f}] vue en plan : axes X / Y de l\'ouvrage en bleu, repérés', str(r))
            s.check(len(r['cot']) >= 2 and any(c.startswith('+') for c in r['cot']) and any(c.startswith('−') for c in r['cot']), f'[{f}] cotes signées depuis les axes (bleu)', str(r['cot']))
        s.check(ev("document.getElementById('appVer').textContent") == 'v3.0', 'version affichée v3.0')
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_v30')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
