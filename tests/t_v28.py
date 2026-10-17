"""v2.8 — vue 3D en WebGL (three.js intégré) : chargement hors connexion, même projection que le rendu vectoriel, pièces
visibles à l'écran, clic → repère, types masqués, éclaté, vues prédéfinies, compteurs en pièces, repères complétés, repli
vectoriel sans WebGL."""
import os
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE, APP

OPEN = "(k)=>{close3D();const S=SCN.find(s=>s[0]===k);T.mk(S[1],S[2],S[3]);open3D()}"
PX = """([x,y])=>{const c=document.querySelector('#v3c canvas'),g=document.createElement('canvas');g.width=c.width;g.height=c.height;const x2=g.getContext('2d');x2.drawImage(c,0,0);
  const k=c.width/c.clientWidth,d=x2.getImageData(Math.round(x*k),Math.round(y*k),1,1).data;return [d[0],d[1],d[2]]}"""


def t(s):
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1300, height=800)
        ev = pg.evaluate
        pg.add_script_tag(path=os.path.join(HERE, 'auditx.js'))
        src = open(APP, encoding='utf-8').read()
        s.check('id="three-src"' in src and 'Copyright 2010-2024 Three.js Authors' in src and 'SPDX-License-Identifier: MIT' in src, 'three.js r170 intégré au fichier avec sa licence MIT (aucun accès réseau)')
        s.check(ev("el('appVer').textContent").startswith('v2.'), 'application chargée')

        ev(OPEN, 'special_circ')
        pg.wait_for_function("V3D.gl===true", timeout=20000); pg.wait_for_timeout(200)
        st = ev("({gl:V3D.last.gl,cv:!!document.querySelector('#v3c canvas'),ov:!!document.querySelector('#v3ov svg'),n:V3D.last.n,lbl:V3D.last.lbl.map(l=>l.t)})")
        s.check(st['gl'] and st['cv'] and st['ov'] and st['n'] > 50, f'rendu WebGL actif : canevas + calque d\'étiquettes ({st["n"]} pièces affichées)')
        s.check({'S1', 'J1', 'F1'} <= set(st['lbl']), f'étiquettes de repères posées sur des pièces visibles : {st["lbl"]}')
        # projection : three.js et la formule du rendu vectoriel donnent le même point écran
        pj = ev("""()=>{const st=V3D,W=st.last.W,H=st.last.H,cam=st.last.cam,vw=v3View(W,H,cam),T=GL3.T;return st.s0.solids.slice(0,40).map(o=>{const p=o.F[0][0],v=new T.Vector3(...p).project(GL3.cam);
          return Math.hypot((v.x+1)/2*W-(vw.ox+dot(p,cam.r)*vw.k),(1-v.y)/2*H-(vw.oy-dot(p,cam.up)*vw.k))})}""")
        s.check(max(pj) < 0.5, f'même projection que le rendu vectoriel (écart maxi {max(pj):.3f} px sur 40 points)')
        lb = ev("V3D.last.lbl.find(l=>l.t==='S1')")
        px = ev(PX, [lb['x'], lb['y']]); bg = ev(PX, [5, 5])
        s.check(bg[0] > 240 and bg[1] > 235 and abs(px[0] - bg[0]) + abs(px[1] - bg[1]) + abs(px[2] - bg[2]) > 60, f'pièce réellement dessinée (pixel {px} ≠ fond {bg})')
        leg = ev("[...document.querySelectorAll('.v3ty')].map(x=>x.textContent.trim())")
        s.check(any(x.startswith('CP joues') and x.endswith(' 2') for x in leg), f'légende : pièces comptées (coque en facettes = 1 pièce) — {leg[:2]}')
        # clic → pièce et repère
        box = ev("(()=>{const r=el('v3c').getBoundingClientRect();return [r.left,r.top]})()")
        pg.mouse.click(box[0] + lb['x'], box[1] + lb['y'])
        pg.wait_for_timeout(150)
        inf = ev("[V3D.sel,el('v3i').innerText,V3D.s0.solids[V3D.sel]&&V3D.s0.solids[V3D.sel].nm]")
        s.check(inf[0] is not None and 'S1' in inf[1] and 'fond sup' in (inf[2] or ''), f'clic sur la pièce : sélection + repère S1 — {inf[1][:60]!r}')
        # types masqués
        ev("()=>{const b=document.querySelector('[data-v3k=\"fs\"]');b.checked=false;b.onchange()}")
        s.check(not ev("GL3.objs.some(g=>g&&g.o.col===C3.fs&&g.grp.visible)") and C3fs_not_in_used(ev), 'type décoché : pièces masquées')
        ev("()=>{const b=document.querySelector('[data-v3k=\"fs\"]');b.checked=true;b.onchange()}")
        # éclaté
        ev("()=>{const r=el('v3ex');r.value=100;r.oninput({target:r})}"); pg.wait_for_timeout(300)
        mv = ev("GL3.objs.filter(g=>g&&g.grp.visible&&g.grp.position.length()>20).length")
        s.check(mv > 10 and ev("V3D.last.gl"), f'éclaté : {mv} pièces écartées en WebGL')
        ev("()=>{const r=el('v3ex');r.value=0;r.oninput({target:r})}"); pg.wait_for_timeout(200)
        for k in ['dessus', 'face', 'cote', 'dessous', 'iso']:
            ev(f"v3Preset('{k}')")
        s.check(ev("V3D.view") == 'iso' and ev("V3D.last.gl"), 'vues prédéfinies (dessus, face, côté, dessous, iso)')
        ev("close3D()")
        s.check(ev("!V3D.on&&!V3D.gl&&GL3.objs.length===0"), 'fermeture : scène libérée')
        # repères complétés : rectangulaire avec cloisons en tronçons
        miss = ev("""()=>SCN.flatMap(S=>{if(S[0]==='circ')return[];const d=T.can(T.mk(S[1],S[2],S[3])),g=d.forme==='voile'?voileGeo(d):null;if(badDims(checks(d,g)))return[];const R=debit(d,g),t3=new Set(model3(d,R).solids.map(o=>o.tag).filter(Boolean));
          return R.filter(r=>['j','fi','fs'].includes(r.k)&&!t3.has(r.tag)).map(r=>S[0]+':'+r.tag)})""")
        # exceptions connues : planches découpées de la dalle (une ligne de débit par panneau, découpé en pièces de formes variées),
        # tronçons de parallélogramme (débit en L × l ⧸ biais, pièce 3D oblique)
        known = {'dalle_circ:F2', 'dalle_circ_pt:F2', 'dalle_rect:F2', 'dalle_pt_lhs:F2', 'dalle_rive:F2', 'para_long:J2'}
        s.check(set(miss) <= known, f'repères du débit portés en 3D sur les 36 scénarios, hors exceptions connues — reste {sorted(set(miss) - known)}')
        # repli vectoriel sans WebGL
        ev("window.V3_NOGL=true"); ev(OPEN, 'rect_fond_gs'); pg.wait_for_timeout(400)
        s.check(not ev("V3D.gl") and ev("document.querySelectorAll('#v3c path[data-i]').length") > 10, 'sans WebGL : rendu vectoriel conservé')
        ev("()=>{close3D();window.V3_NOGL=false}")
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', str(errs[:3]))
        b.close()


def C3fs_not_in_used(ev):
    return ev("!V3D.last.used.has(C3.fs)")


if __name__ == '__main__':
    import sys
    s = Suite('t_v28')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
