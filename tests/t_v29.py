"""v2.9 — retours terrain : pied de feuille aligné, vues prioritaires (colonnes fixes, vues recadrées), 2 panneaux maxi par
feuille de découpe, feuille INFORMATIONS sans vignette, éclaté sans contact, perçages des poteaux en 3D, rendu 3D enrichi."""
import os
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE

PRINT = """([f,ov,fmt])=>{window.print=()=>{};PRT.fmt=fmt;applyPage();PRT.lay='full';PRT.cp=PRT.mt=PRT.fa=true;P.length=0;T.mk(f,ov);printAll();
  const ps=[...document.querySelectorAll('#pvA .ps')],r=e=>e.getBoundingClientRect(),out=ps.map(p=>{const ft=p.querySelector('.ps-foot'),w2=p.querySelector('.ps-bd > .ps-w2'),sd=w2&&p.querySelector('.ps-bd > .ps-tall');
    return {t:(p.querySelector('.ps-rf')||{}).textContent||'',port:p.classList.contains('portrait'),footOut:!!ft&&ft.parentElement===p,footW:ft?r(ft).width/r(p).width:0,
      wrap:ft?[...ft.querySelectorAll('.lg>span')].filter(s=>r(s).height>14).length:0,w2:w2?r(w2).width/r(p).width:null,sd:sd?r(sd).width/r(p).width:null,
      pan:[...p.querySelectorAll('svg text')].filter(t=>/^PANNEAU \\d+ ?\\/ ?\\d+/.test(t.textContent)).length,svgs:p.querySelectorAll('.ps-c > svg').length,
      cl:[...p.querySelectorAll('.ps-cl')].map(x=>x.textContent)}});document.body.classList.remove('pm');return out}"""
FORMS = [('rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400, 'oGs': True, 'oRenX': True}), ('voile', {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10}),
         ('special', {'dBase': 'circ', 'oPot': True, 'oConc': True, 'oFondSup': True}), ('dalle', {'dlPt': True}), ('goulotte', {}), ('poutre', {}), ('para', {})]


def t(s):
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500, height=1000)
        ev = pg.evaluate
        pg.add_script_tag(path=os.path.join(HERE, 'auditx.js'))
        # ---- feuilles imprimées, toutes formes, A3 et A4 ----
        for fmt in ('A3', 'A4'):
            for f, ov in FORMS:
                S = ev(PRINT, [f, ov, fmt])
                L = [x for x in S if not x['port']]
                s.check(all(x['footOut'] and x['footW'] > 0.97 for x in S), f'[{f} {fmt}] pied de feuille hors grille, pleine largeur ({len(S)} feuilles)', str([round(x['footW'], 2) for x in S]))
                s.check(all(x['wrap'] == 0 for x in S), f'[{f} {fmt}] légende sur une ligne (aucun libellé coupé)')
                w = [x for x in L if x['w2'] is not None]
                s.check(all(x['w2'] >= 0.68 and x['sd'] <= 0.31 for x in w), f'[{f} {fmt}] feuilles vue + tableau : vue ≥ 68 % de la largeur, tableau ≤ 31 %', str([(round(x['w2'], 2), round(x['sd'], 2)) for x in w][:4]))
                cut = [x for x in L if 'CP À DÉCOUPER' in x['t']]
                s.check(all(x['pan'] <= 2 for x in cut), f'[{f} {fmt}] CP à découper : 2 panneaux maxi par feuille', str([x['pan'] for x in cut]))
                inf = [x for x in L if 'INFORMATIONS' in x['t'] and 'FEUILLE 1b' not in x['t']]
                s.check(all(x['svgs'] == 0 and x['cl'] == ['Informations', 'Hypothèses', 'Débit · traçage · contrôles'] for x in inf), f'[{f} {fmt}] feuille INFORMATIONS : 3 colonnes de texte, sans vignette du plan', str([x['cl'] for x in inf]))
        rc = ev("""()=>{window.print=()=>{};P.length=0;T.mk('dalle',{dlPt:true});el('iCh').value='T29';EI=-1;addP(true,true);showChantier();
          const n=[...document.querySelectorAll('#pvA .ps')].filter(p=>/CP À DÉCOUPER/.test(p.textContent)).map(p=>[...p.querySelectorAll('svg text')].filter(t=>/^PANNEAU \\d+ ?\\/ ?\\d+/.test(t.textContent)).length);VIEW='plan';return n}""")
        s.check(rc and max(rc) <= 2, f'récapitulatif chantier : CP à découper, 2 panneaux maxi par feuille {rc}')
        crop = ev("""()=>{T.mk('rect_fond',{dL:1200,dl:800,dh:400});prev();const v=[...document.querySelectorAll('#pvA .ps-c > svg')].filter(x=>x.dataset.fit);return v.length}""")
        s.check(crop >= 2, f'vues recadrées sur leur dessin ({crop} vues)')
        # ---- éclaté : aucune pièce à moins de 3 mm d'une autre, toutes formes ----
        near = ev("""()=>SCN.flatMap(S=>{const d=T.can(T.mk(S[1],S[2],S[3])),g=d.forme==='voile'?voileGeo(d):null;if(badDims(checks(d,g)))return[];const sc=model3(d,debit(d,g)),E=explode3(sc,1,null,exVec3(sc,camIso(d)));
          const L=E.solids.filter(o=>o.role!=='ctx'),o=[];for(let i=0;i<L.length;i++)for(let j=i+1;j<L.length;j++){if(L[i].rg&&L[i].rg===L[j].rg)continue;if(overlap3({solids:[L[i],L[j]]},-3,5).length)o.push(S[0]+':'+L[i].nm+'/'+L[j].nm)}return o})""")
        s.check(not near, f'éclaté complet : aucune pièce à moins de 3 mm d\'une autre (36 scénarios) — {near[:5]}')
        dz = ev("""()=>{const S=SCN.find(s=>s[0]==='dalle_circ_pt'),d=T.can(T.mk(S[1],S[2],S[3])),sc=model3(d,debit(d,null)),E=explode3(sc,1,null,exVec3(sc,camIso(d))).solids;
          const z=(nm,f)=>f(...E.filter(o=>o.nm===nm).flatMap(o=>o.F.flat().map(p=>p[2])));return [z('joue de poutre',Math.max),z('poutrelle',Math.min)]}""")
        s.check(dz[0] < dz[1], f'dalle en éclaté : joues de poutre sous les poutrelles (haut des joues {dz[0]:.0f} < bas des poutrelles {dz[1]:.0f})')
        # ---- 3D : perçages des poteaux dans la base et le fond supérieur ----
        ev("()=>{T.mk('special',{dBase:'circ',oPot:true,oConc:true,oFondSup:true});open3D()}")
        pg.wait_for_function("V3D.gl===true", timeout=20000); pg.wait_for_timeout(200)
        h = ev("""()=>{const n=potAngles(canon(coll())).length,G=[...new Set(GL3.objs.filter(g=>g&&/fond (inf|sup)/.test(g.o.nm)))];return [n,G.map(g=>[g.o.nm,(g.mesh.geometry.parameters&&g.mesh.geometry.parameters.shapes?[].concat(g.mesh.geometry.parameters.shapes).reduce((a,s)=>a+s.holes.length,0):-1)])]}""")
        s.check(h[0] > 0 and all(x[1] >= h[0] - (1 if 'sup' in x[0] else 0) for x in h[1]) and len(h[1]) == 2, f'base et fond sup. percés au droit des {h[0]} poteaux (perçages modélisés : {h[1]})')
        ev("v3Preset('dessus')"); pg.wait_for_timeout(600)
        px = ev("""()=>{const d=canon(coll()),a=potAngles(d)[0]*Math.PI/180,p=[d.pR*Math.cos(a),-d.pR*Math.sin(a),d.h+10],T=GL3.T,v=new T.Vector3(...p).project(GL3.cam),c=document.querySelector('#v3c canvas');
          const x=(v.x+1)/2*c.clientWidth,y=(1-v.y)/2*c.clientHeight,g=document.createElement('canvas');g.width=c.width;g.height=c.height;const k=c.width/c.clientWidth,x2=g.getContext('2d');x2.drawImage(c,0,0);return [...x2.getImageData(Math.round(x*k),Math.round(y*k),1,1).data].slice(0,3)}""")
        fs = ev("[parseInt(C3.fs.slice(1,3),16),parseInt(C3.fs.slice(3,5),16),parseInt(C3.fs.slice(5,7),16)]")
        s.check(abs(px[0] - fs[0]) + abs(px[1] - fs[1]) + abs(px[2] - fs[2]) > 90, f'vue de dessus : au droit d\'un poteau on voit le trou (pixel {px}, fond sup. {fs})')
        # ---- rendu 3D enrichi ----
        r = ev("""()=>{const g=GL3.objs.filter(Boolean),m=g.map(x=>[].concat(x.mesh.material)[0]);return {tex:m.filter(x=>x.map).length,n:g.length,ply:g.filter(x=>x.mesh.geometry.groups&&x.mesh.geometry.groups.length>1).length,grid:!!GL3.grid,lights:GL3.scene.children.filter(o=>o.isLight).length}}""")
        s.check(r['tex'] > 0.6 * r['n'] and r['ply'] > 0 and r['grid'] and r['lights'] >= 3, f'matières (grain du bois sur CP et bois, plis sur les chants), sol quadrillé, 3 lumières — {r}')
        ev("v3Preset('iso')"); pg.wait_for_timeout(50)
        mid = ev("[V3D.az,V3D.el]"); pg.wait_for_timeout(600); end = ev("[V3D.az,V3D.el,V3D.pr.iso[1]]")
        s.check(abs(end[1] - end[2]) < 0.01 and abs(mid[1] - end[2]) > 0.5, f'vues prédéfinies : transition animée puis position exacte ({mid[1]:.1f}° → {end[1]:.1f}°)')
        lb = ev("V3D.last.lbl[0]"); box = ev("(()=>{const r=el('v3c').getBoundingClientRect();return [r.left,r.top]})()")
        pg.mouse.move(box[0] + lb['x'], box[1] + lb['y']); pg.wait_for_timeout(200)
        s.check(ev("GL3.hov") is not None, 'survol d\'une pièce : mise en évidence')
        ev("close3D()")
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    import sys
    s = Suite('t_v29')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
