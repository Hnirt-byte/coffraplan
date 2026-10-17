"""v2.10 — vues à l'échelle normalisée (échelle par vue, barre d'échelle, cartouche), vue 3D des feuilles en rendu WebGL,
impression A4 (règles « écran étroit » limitées à l'écran, dimensions longues repliées), platelage soulevé en éclaté,
perçage des fonds Ø poteau + 0 mm par défaut."""
import os
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE

FORMS = [('rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400, 'oGs': True, 'oRenX': True}), ('voile', {'dL': 900, 'dl': 200, 'dh': 2100, 'dDcuve': 12, 'oCourb': 'reel'}),
         ('special', {'dBase': 'circ', 'oPot': True, 'oConc': True, 'oFondSup': True}), ('dalle', {'dlPt': True}), ('goulotte', {}), ('poutre', {}), ('para', {}), ('circ_fond', {})]
# impression (sans attendre les images 3D) puis mesure des vues à l'échelle
PRINT = """([f,ov,fmt,ech])=>{window.print=()=>{window._pr=(window._pr||0)+1};PRT.fmt=fmt;PRT.ech=ech;applyPage();PRT.lay='full';PRT.cp=PRT.mt=PRT.fa=true;P.length=0;T.mk(f,ov);printAll();
  const PX=96/25.4,r=e=>e.getBoundingClientRect(),V=[...document.querySelectorAll('#pvA .ps-c > svg[data-ech]')].map(sv=>{const vb=sv.viewBox.baseVal,b=r(sv),c=r(sv.parentElement),D=+sv.dataset.ech,bar=sv.parentElement.querySelector('.ech-b i');
    return {D,sc:(b.width/vb.width)*(+sv.dataset.k)/PX,inC:b.left>=c.left-1&&b.right<=c.right+1&&b.top>=c.top-1&&b.bottom<=c.bottom+1,lbl:(sv.parentElement.querySelector('.ps-cl .ech')||{}).textContent||'',
      bar:bar?r(bar).width/PX:0,barL:+(((sv.parentElement.querySelector('.ech-b')||{}).title||'').match(/(\\d+) mm/)||[0,0])[1]}});
  const cart=[...document.querySelectorAll('#pvA .ps .ech-c')].map(x=>x.textContent),nov=[...document.querySelectorAll('#pvA .ps-c > svg[data-vk]:not([data-ech])')].length;
  return {V,cart,nov,ECH}}"""


def t(s):
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500, height=1000)
        ev = pg.evaluate
        # ---- 1. vues à l'échelle normalisée, toutes formes, A3 et A4 ----
        for fmt in ('A3', 'A4'):
            for f, ov in FORMS:
                R = ev(PRINT, [f, ov, fmt, 'norm'])
                V = R['V']
                if f in ('rect_fond', 'special', 'dalle', 'circ_fond', 'voile'):
                    s.check(len(V) >= 1, f'[{f} {fmt}] vues à l\'échelle normalisée ({len(V)} vue(s), {R["nov"]} sans échelle)')
                s.check(all(x['D'] in R['ECH'] and abs(x['sc'] * x['D'] - 1) < 0.005 for x in V), f'[{f} {fmt}] échelle imprimée exacte (écart < 0,5 %)', str([(x['D'], round(1 / x['sc'], 2)) for x in V if abs(x['sc'] * x['D'] - 1) >= 0.005][:4]))
                s.check(all(x['inC'] for x in V), f'[{f} {fmt}] vue à l\'échelle contenue dans sa case')
                s.check(all(x['lbl'] == f' · Éch. 1/{x["D"]}' for x in V), f'[{f} {fmt}] échelle indiquée sous le titre de chaque vue')
                s.check(all(x['barL'] > 0 and abs(x['bar'] - x['barL'] / x['D']) < 0.3 and x['bar'] <= 60.5 for x in V), f'[{f} {fmt}] barre d\'échelle : longueur papier = longueur réelle / échelle', str([(x['barL'], x['D'], round(x['bar'], 1)) for x in V][:3]))
                if V:
                    s.check(any(c.startswith('Échelle') and f'impr. 100 % {fmt}' in c and 'fabriquer aux cotes' in c for c in R['cart']), f'[{f} {fmt}] cartouche : échelle(s), impression à 100 %, fabriquer aux cotes', str(R['cart'][:2]))
        # textes : régénérés à leur taille d'origine (seule la géométrie est réduite)
        fs = ev("""()=>{PRT.fmt='A3';PRT.ech='norm';P.length=0;T.mk('rect_fond',{dL:1200,dl:800,dh:400});const h=gen(coll()),tp=document.createElement('template');tp.innerHTML=h;
          const o=new Map([...tp.content.querySelectorAll('svg[data-vk]')].map(sv=>[sv.dataset.vk,[...sv.querySelectorAll('text')].map(t=>t.getAttribute('font-size')).join()]));window.print=()=>{};printAll();
          const n=[...document.querySelectorAll('#pvA svg[data-ech]')];return [n.length,n.filter(sv=>o.get(sv.dataset.vk)===[...sv.querySelectorAll('text')].map(t=>t.getAttribute('font-size')).join()).length,
            n.filter(sv=>+sv.dataset.k<+((tp.content.querySelector('svg[data-vk="'+sv.dataset.vk+'"]')||{dataset:{k:0}}).dataset.k)).length]}""")
        s.check(fs[0] > 0 and fs[1] == fs[0], f'textes des vues à l\'échelle : taille d\'origine conservée ({fs[1]}/{fs[0]})')
        s.check(fs[2] >= 1, f'géométrie redessinée plus petite pour tomber sur l\'échelle normalisée ({fs[2]} vue(s))')
        un = ev("()=>{unfitPrint();return [document.querySelectorAll('#pvA svg[data-ech],#pvA .ech-b,#pvA .ech').length,[...document.querySelectorAll('#pvA .ech-c')].every(x=>x.textContent==='Non à l\\'échelle — fabriquer aux cotes')]}")
        s.check(un[0] == 0 and un[1], 'après impression : vues, barres et cartouche rétablis')
        R = ev(PRINT, ['rect_fond', FORMS[0][1], 'A3', 'fit'])
        s.check(not R['V'] and all(c == 'Non à l\'échelle — fabriquer aux cotes' for c in R['cart']), 'réglage « agrandie à la case » : aucune échelle, cartouche « non à l\'échelle »')
        mult = ev("()=>{T.mk('poutre',{});const h=gen(coll());return [(h.match(/data-vk=/g)||[]).length,(h.match(/<svg /g)||[]).length]}")
        s.check(mult[1] > 0 and mult[0] < mult[1], f'vues à plusieurs échelles (poutre) : non repérées pour l\'échelle ({mult[0]}/{mult[1]})')
        same = ev("()=>{T.mk('rect_fond',{dL:1200,dl:800,dh:400});const d=coll(),n=h=>h.replace(/ data-(vk|k|glk)=\"[^\"]*\"/g,'').replace(/V3REG\\.get\\(\\d+\\)/g,'');return n(gen(d))===n(gen(d))}")
        s.check(same, 'hors impression : feuilles identiques d\'un appel à l\'autre (aucun facteur d\'échelle résiduel)')
        ev("()=>{PRT.ech='norm';PRT.fmt=''}")
        # ---- 2. impression A4 : règles « écran étroit » sans effet à l'impression ----
        pg.set_viewport_size({'width': 760, 'height': 1000}); pg.emulate_media(media='print')
        cols = ev("""()=>{window.print=()=>{};PRT.fmt='A4';applyPage();PRT.lay='full';PRT.cp=PRT.mt=PRT.fa=true;P.length=0;T.mk('dalle',{dlPt:true});printAll();
          const ps=[...document.querySelectorAll('#pvA .ps')],inf=ps.find(p=>/— INFORMATIONS/.test(p.querySelector('.ps-rf').textContent)),W=inf.getBoundingClientRect().width;
          const c=[...inf.querySelectorAll('.ps-bd > .ps-c')].map(x=>x.getBoundingClientRect().width/W);
          T.mk('voile',{dL:900,dl:200,dh:2100,dDcuve:12});printAll();const pl=[...document.querySelectorAll('#pvA .ps')][0],cs=[...pl.querySelectorAll('.ps-bd > .ps-c')].map(x=>x.getBoundingClientRect());
          let ovl=0;for(let i=0;i<cs.length;i++)for(let j=i+1;j<cs.length;j++){const a=cs[i],b=cs[j];if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>4&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>4)ovl++}
          const b1=[...document.querySelectorAll('#pvA .ps')].find(p=>/FEUILLE 1b/.test(p.querySelector('.ps-rf').textContent)),db=b1.querySelector('.ps-c .inf');
          return {c,ovl,n:cs.length,suite:!!db.querySelector('.sui-m'),j1:/J1/.test(db.textContent),wrap:!!db.querySelector('.nmw')}}""")
        s.check(len(cols['c']) == 3 and min(cols['c']) > 0.25, f'A4 (fenêtre étroite) : feuille INFORMATIONS sur 3 colonnes larges {[round(x, 2) for x in cols["c"]]}')
        s.check(cols['ovl'] == 0 and cols['n'] >= 3, f'A4 (fenêtre étroite) : vues du voile côte à côte, sans superposition ({cols["n"]} cases)')
        s.check(cols['j1'] and not cols['suite'] and cols['wrap'], 'A4 : débit du voile lisible en place (précision de coupe repliée, pas de renvoi « suite »)')
        pg.emulate_media(media='screen'); pg.set_viewport_size({'width': 1500, 'height': 1000})
        ev("()=>{unfitPrint();PRT.fmt=''}")
        # ---- 3. vue 3D des feuilles en rendu WebGL ----
        ev("""()=>{window._pr=0;window.print=()=>{window._pr=1};PRT.fmt='A3';PRT.mt=true;P.length=0;T.mk('special',{dBase:'circ',oPot:true,oConc:true,oFondSup:true});printAll()}""")
        pg.wait_for_function("window._pr===1", timeout=60000)
        g = ev("""()=>{const I=[...document.querySelectorAll('#pvA svg[data-glimg] image')];return {n:I.length,left:document.querySelectorAll('#pvA svg[data-glk]').length,
          jpg:I.every(i=>/^data:image\\/jpeg/.test(i.getAttribute('href'))),lbl:[...document.querySelectorAll('#pvA svg[data-glimg]')].map(s=>[...s.querySelectorAll('text')].filter(t=>/^[A-Z]\\d$/.test(t.textContent)).length)}}""")
        s.check(g['n'] == 2 and g['left'] == 0 and g['jpg'], f'feuilles MONTAGE : vues 3D en rendu WebGL (2 images, aucune vue vectorielle restante) — {g}')
        s.check(all(x >= 3 for x in g['lbl']), f'feuilles MONTAGE : repères posés sur l\'image 3D {g["lbl"]}')
        sz = ev("""async()=>{const i=document.querySelector('#pvA svg[data-glimg] image'),im=new Image();im.src=i.getAttribute('href');await im.decode();return [im.naturalWidth,im.naturalHeight]}""")
        s.check(sz[0] >= 2400, f'image 3D en haute définition pour l\'impression ({sz[0]} × {sz[1]} px)')
        nogl = ev("""async()=>{window.V3_NOGL=true;window._pr=0;T.mk('rect_fond',{dL:1300,dl:900,dh:500});printAll();await new Promise(r=>setTimeout(r,800));const r=[window._pr,document.querySelectorAll('#pvA svg[data-glk]').length,document.querySelectorAll('#pvA svg[data-glimg]').length];window.V3_NOGL=false;return r}""")
        s.check(nogl[0] == 1 and nogl[1] >= 1 and nogl[2] == 0, f'sans WebGL : vue 3D vectorielle conservée et impression lancée {nogl}')
        ev("()=>{unfitPrint();PRT.fmt=''}")
        # ---- 4. dalle en éclaté : le platelage s'élève au-dessus des coffrages ----
        z = ev("""()=>{const S=SCN.find(s=>s[0]==='dalle_circ_pt'),d=T.can(T.mk(S[1],S[2],S[3])),sc=model3(d,debit(d,null)),E=explode3(sc,1,null,exVec3(sc,camIso(d))).solids;
          const tp=E.filter(o=>o.role==='top'),ot=E.filter(o=>o.role!=='top'&&o.role!=='ctx'),zs=L=>L.flatMap(o=>o.F.flat().map(p=>p[2]));return [tp.length,sc.solids.filter(o=>o.role==='top').length,Math.min(...zs(tp)),Math.max(...zs(ot))]}""")
        s.check(z[0] == z[1] and z[0] > 0 and z[2] > z[3], f'dalle éclatée : toutes les planches du platelage présentes ({z[0]}/{z[1]}) et au-dessus du reste (bas {z[2]:.0f} > haut des autres pièces {z[3]:.0f})')
        ev("()=>{T.mk('dalle',{dlPt:true});open3D()}")
        pg.wait_for_function("V3D.gl===true", timeout=20000)
        vis = ev("()=>{const r=el('v3ex');r.value=100;r.oninput({target:r});v3Draw();return GL3.objs.filter(g=>g&&g.o.role==='top'&&g.grp.visible).length}")
        s.check(vis > 0, f'vue 3D interactive, éclaté 100 % : platelage affiché ({vis} planches)')
        ev("close3D()")
        # ---- 5. perçage des fonds : Ø poteau + 0 mm par défaut ----
        pj = ev("""()=>{const d=T.mk('special',{dBase:'circ',oPot:true,oFondSup:true}),c=T.can(d),o=Object.assign({},d);delete o.pJ;
          const sc=model3(c,debit(c,null)),h=sc.solids.filter(x=>x.holes&&x.holes.length).flatMap(x=>x.holes.map(q=>q[2]));return [el('oPJ').value,c.pJ,T.can(o).pJ,c.pD,[...new Set(h.map(r=>Math.round(r*10)/10))]]}""")
        s.check(pj[0] == '0' and pj[1] == 0 and pj[2] == 0, f'perçage des fonds : jeu par défaut 0 mm (champ {pj[0]}, plan {pj[1]}, ancien fichier sans valeur {pj[2]})')
        s.check(pj[4] == [pj[3] / 2], f'perçages modélisés au Ø du poteau (rayon {pj[4]} pour Ø {pj[3]})')
        s.check(ev("document.getElementById('appVer').textContent") == 'v2.10', 'version affichée v2.10')
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    import sys
    s = Suite('t_v210')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
