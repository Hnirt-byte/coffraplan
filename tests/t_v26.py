"""v2.6 — crédibilité : catalogue CP (filmé phénolique par âme), flèche des joues, note d'hypothèses, cartouche entreprise,
enregistrement direct dans un fichier (File System Access), noms de chantiers réels retirés."""
import json, os, re
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, APP

# Riga Wood, Concrete formwork (03/2026) — Riga Form, 3 travées égales : portée → [(q kN/m², u mm)] pour 9…24 mm
RIGA_T = [9, 12, 15, 18, 21, 24]
RIGA = {'par': {200: [(59, 1.6), (79, 1.2), (92, .85), (112, .72), (126, .60), (144, .55)], 300: [(39, 4.8), (53, 3.3), (62, 2.3), (74, 1.8), (84, 1.4), (96, 1.2)],
                500: [(14, 13), (23, 9.9), (34, 8.3), (45, 7.0), (50, 5.3), (58, 4.4)]},
        'per': {200: [(51, 2.5), (64, 1.4), (84, 1.0), (98, .78), (117, .67), (132, .58)], 300: [(28, 6.2), (42, 4.0), (56, 2.8), (65, 2.0), (78, 1.7), (88, 1.4)],
                500: [(10, 16.4), (18, 12), (27, 9.6), (39, 8.0), (47, 6.2), (53, 4.9)]}}
FL = "([f,ov])=>{const d=T.can(T.mk(f,ov)),F=flecheCP(d);return F&&{nd:!!F.nd,full:F.full,soft:F.soft,r:F.r,f:(F.faces||[]).map(x=>({face:x.face,a:x.a,u:x.u,lim:x.lim,ok:x.ok})),W:checks(d,null).filter(x=>/^Flèche du CP/.test(x[1])).map(x=>x[1])}}"
BOX = ('rect', {'dL': 600, 'dl': 600, 'dh': 400})


def t(s):
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        ev = pg.evaluate
        src = open(APP, encoding='utf-8').read()
        s.check(ev("el('appVer').textContent").startswith(('v2.', 'v3.')), 'version affichée (v2.6 ou suivante)')  # v3.0 : numéro majeur 3 admis  # v2.7 : numéro vérifié par t_ux
        s.check('CHANTIER_DEMO_A' not in src and 'CHANTIER_DEMO_B' not in src, 'aucun nom de chantier réel dans l\'application')

        # ---- catalogue CP ----
        cat = ev("Object.keys(CPT).map(k=>[k,CPT[k].n])")
        s.check([k for k, _ in cat][:3] == ['filme', 'filmec', 'filmep'] and dict(cat)['filme'] == 'CP filmé bouleau', f'catalogue : filmé bouleau (défaut), combi, peuplier / eucalyptus, puis CTBX, cintrable — {cat}')
        s.check(ev("JSON.stringify(CPDEF)") == '{"t":"filme","e":18,"f":"2500x1250"}' and 'EN 636-3' in src, 'CP par défaut : filmé phénolique bouleau 18 mm (EN 636-3)')
        mec = ev("['filme','filmec','filmep','ctbx','cintr'].map(t=>{const m=cpMec({t,e:18});return m&&m.E})")
        s.check(mec == [7452, 7452, None, 4000, None], f'module retenu à 18 mm (sens le plus faible) : bouleau 7452, combi 7452, okoumé 4000, peuplier et cintrable sans donnée — {mec}')
        s.check(ev("cpMec({t:'filme',e:12}).E") == 6781 and ev("cpMec({t:'filmec',e:24}).E") == 7783, 'modules par épaisseur (Koskisen tab. 3-2 / 3-3)')

        # ---- modèle de flèche ----
        w = ev("plateW(564,400,0.01,7452*18**3/12)")
        s.check(abs(w - 1.5846) < 0.01, f'plaque (Ritz) : 564 × 400, q0 = 10 kN/m², 18 mm → {w:.3f} mm (référence numpy 1,585)')
        ub = ev("[[300,300],[564,400],[400,800],[300,900],[1164,400]].map(([a,h])=>{const D=7452*18**3/12,q=25*h/1e6;return plateW(a,h,q,D)/(5/384*q*a**4/D)})")
        s.check(all(0 < x <= 1.0 for x in ub), f'plaque ≤ bande horizontale chargée à la poussée maxi (borne haute), 5 cas — {[round(x, 2) for x in ub]}')
        k = ev("[FL_F,FL_K]")
        E = ev("CPMEC.filme.E")
        errs_r = []
        for dirn, ix in (('par', 0), ('per', 1)):
            for L, row in RIGA[dirn].items():
                for t_, (q, u) in zip(RIGA_T, row):
                    e = E[str(t_)][ix]; qn = q / 1000
                    up = k[0] * (0.00688 * qn * L ** 4 / (e * t_ ** 3 / 12) + k[1] * qn * L * L / t_)
                    errs_r.append(up / u - 1)
        s.check(min(errs_r) > -0.07 and max(errs_r) < 0.14, f'coefficients (× {k[0]}, cisaillement {k[1]}) contre le tableau Riga Form 03/2026 (36 cas) : {min(errs_r) * 100:+.0f} % … {max(errs_r) * 100:+.0f} %')

        # ---- flèche des joues ----
        r = ev(FL, list(BOX))
        s.check(r['full'] and not r['W'] and [round(x['a']) for x in r['f']] == [257, 282] and all(x['ok'] for x in r['f']),
                f'boîte 600 × 600 × 400, cloisons CP : portées 257 / 282 mm, flèche admise — {r["f"]}')
        r0 = ev(FL, ['rect', dict(BOX[1], oRenX=False)])
        x = max(r0['f'], key=lambda z: z['u'] / z['lim'])
        s.check(not r0['full'] and round(x['a']) == 564 and not x['ok'] and r0['W'] and f"≈ {x['u']:.1f}".replace('.', ',') in r0['W'][0] and 'cloisons CP' in r0['W'][0],
                f'même boîte sans renforts : portée 564 mm entre angles, alerte avec conseil — {r0["W"]}')
        rt = ev(FL, ['rect', dict(BOX[1], oRenX=True, oRenXs='t50')])
        s.check(rt['soft'] and not rt['full'] and round(max(z['a'] for z in rt['f'])) == 564, 'tasseaux 50 × 50 : appuis ponctuels non comptés (portée entre angles), signalé')
        r24 = ev("()=>{const d=T.can(T.mk('rect',{dL:600,dl:600,dh:400,oRenX:false}));d.cp=Object.assign({},d.cp,{j:{t:'filme',e:24,f:'2500x1250'}});return flecheCP(canon(d)).w.u}")
        s.check(r24 < x['u'] * 0.6, f'CP 24 mm : flèche réduite ({r24:.2f} < {x["u"]:.2f} mm)')
        nd = ev("()=>{const d=T.can(T.mk('rect',{dL:600,dl:600,dh:400}));d.cp=Object.assign({},d.cp,{j:{t:'filmep',e:18,f:'2500x1250'}});const c=canon(d);return [flecheCP(c).nd,hypRows(c,null,debit(c,null)).find(r=>r[0]==='Flèche du CP')[1]]}")
        s.check(nd[0] and 'aucune rigidité publiée' in nd[1], f'CP peuplier / eucalyptus : flèche non vérifiée, dit dans les hypothèses — {nd[1]}')
        hv = ev("()=>{const d=T.can(T.mk('voile',{dL:670,dl:150,dh:270,dDcuve:10})),g=voileGeo(d);return hypRows(d,g,debit(d,g)).find(r=>r[0]==='Flèche du CP')}")
        s.check('forme non couverte' in hv[1] and hv[2] == '—', 'voile : flèche non vérifiée, forme non couverte (dit)')
        hr = ev("()=>{const d=T.can(T.mk('rect',{dL:600,dl:600,dh:400}));return hypRows(d,null,debit(d,null)).find(r=>r[0]==='Flèche du CP')}")
        s.check('Calcul indicatif' in hr[2] and 'Koskisen' in hr[2] and 'portée 257 mm / 300' in hr[1] and 'fluage' in hr[1], f'hypothèses : valeurs, critère, origine sourcée — {hr}')
        fx = ev("()=>{T.mk('rect',{dL:600,dl:600,dh:400,oRenX:false});const d=coll(),m=fixMsgs(d).find(x=>/^Flèche du CP/.test(x[1]));const r=fixFind(d,m[1]);return r&&r.patch}")
        s.check(fx == {'renX': True, 'renXs': 'cp'}, f'auto-contrôle : correction proposée = cloisons CP pleine hauteur — {fx}')
        fl = ev("()=>{T.mk('rect',{dL:600,dl:600,dh:400});const d=coll();PROF[chKey(d.ch)]=Object.assign({},PROF_DEF,{fl:150});const F=flecheCP(T.can(d));delete PROF[chKey(d.ch)];return [F.r,F.faces[0].lim,F.faces[0].a]}")
        s.check(fl[0] == 150 and abs(fl[1] - fl[2] / 150) < 1e-6, 'profil chantier : flèche admise portée / 150 prise en compte')

        # ---- cartouche entreprise ----
        g0 = ev("()=>{ENT={};T.mk('rect',{dL:600,dl:600,dh:400});return gen(coll())}")
        s.check('Vérifié : ________' in g0 and 'Visa : ________' in g0 and "Non à l'échelle" in g0, 'cartouche : dessiné / vérifié / visa / « non à l\'échelle » même sans entreprise')
        logo = ev("()=>{const c=document.createElement('canvas');c.width=40;c.height=20;const x=c.getContext('2d');x.fillStyle='#e8820c';x.fillRect(0,0,40,20);return c.toDataURL('image/png')}")
        ev("()=>openEnt()")
        pg.fill('#enNom', 'ENTREPRISE <b>TEST</b>'); pg.fill('#enDes', 'K. T.')
        ev("u=>{el('enImg').src=u;el('enImg').style.display=''}", logo)
        ev("saveEnt()")
        e1 = ev("JSON.parse(localStorage.getItem('resaEnt'))")
        g1 = ev("gen(coll())")
        s.check(e1['nom'] == 'ENTREPRISE <b>TEST</b>' and e1['logo'].startswith('data:image/png') and 'ENTREPRISE &lt;b&gt;TEST&lt;/b&gt;' in g1 and '<b>TEST</b>' not in g1 and 'Dessiné : K. T.' in g1 and '<img src="data:image/png' in g1,
                'cartouche : nom (échappé), dessinateur, logo, mémorisés')
        s.check(ev("Object.keys(entOk({nom:'x',logo:'javascript:alert(1)',autre:1}))") == ['nom'] and ev("Object.keys(entOk({logo:'data:image/svg+xml;base64,AAAA'}))") == [],
                'cartouche : logo non image (script, SVG) refusé, clés inconnues ignorées')
        HH = """(hide)=>{window.print=()=>{};PRT.lay='full';let st=null;if(hide){st=document.createElement('style');st.textContent='.ps-ent{display:none!important}';document.head.appendChild(st)}
          printAll();const bad=[...document.querySelectorAll('#pvA .ps-c')].filter(c=>c.scrollHeight>c.clientHeight+1).length,
          hh=Math.max(...[...document.querySelectorAll('#pvA .ps:not(.portrait) .ps-h')].map(h=>h.getBoundingClientRect().height));document.body.classList.remove('pm');if(st)st.remove();return [bad,hh]}"""
        ov, ov0 = ev(HH, False), ev(HH, True)
        s.check(ov[0] == 0 and ov[1] - ov0[1] <= 8, f'impression avec logo : aucune case qui déborde, cartouche des plans + {ov[1] - ov0[1]:.0f} px au plus 8 ({ov0[1]:.0f} → {ov[1]:.0f})')

        # ---- enregistrement direct (faux fichier) ----
        ev("""()=>{window._w=[];window._pk=0;window._mk=(name)=>({name,createWritable:async()=>({write:async t=>window._w.push(t),close:async()=>{}}),getFile:async()=>({text:async()=>window._file})});
          window.showSaveFilePicker=async o=>{window._pk++;window._sug=o.suggestedName;return window._mk('chantier_A.json')}}""")
        ev("()=>{P.length=0;T.mk('rect',{dL:600,dl:600,dh:400});EI=-1;addP(true,true)}")
        ev("async()=>{await expJ()}")
        st = ev("({n:_w.length,pk:_pk,sug:_sug,dirty:isDirty(),toast:el('toast').textContent})")
        J = json.loads(ev("_w[0]"))
        s.check(st['n'] == 1 and st['pk'] == 1 and re.match(r'coffraplan_\d{4}-\d\d-\d\d\.json', st['sug']) and not st['dirty'] and 'chantier_A.json' in st['toast'],
                f'Chrome / Edge : 1er enregistrement → choix du fichier, écrit, projet marqué enregistré — {st}')
        s.check(J['app'] == 'plans-reservation' and J['v'] == 10 and len(J['plans']) == 1 and J['ent']['nom'] == 'ENTREPRISE <b>TEST</b>', 'contenu écrit : format v 10 + cartouche entreprise')
        ev("async()=>{markDirty();await expJ()}")
        s.check(ev("[_w.length,_pk]") == [2, 1], 'Ctrl+S suivant : réécrit le même fichier sans redemander')
        ev("async()=>{await expJ(true)}")
        s.check(ev("_pk") == 2, 'Enregistrer sous (Ctrl+Maj+S) : nouveau choix de fichier')
        ev("()=>{window.showSaveFilePicker=async()=>{const e=new Error('a');e.name='AbortError';throw e};FH=null;el('toast').textContent=''}")
        dls = []
        pg.on('download', lambda d: dls.append(d))
        ev("async()=>{await expJ()}"); pg.wait_for_timeout(500)
        s.check(not dls and 'impossible' not in ev("el('toast').textContent"), 'abandon du choix de fichier : ni téléchargement ni message d\'erreur')
        # ouverture : le fichier choisi devient la cible des enregistrements
        ev("""(j)=>{window._file=j;window.showOpenFilePicker=async()=>[window._mk('projet_B.json')];window.showSaveFilePicker=async()=>{window._pk++;return window._mk('autre.json')};window._pk=0;window._w=[]}""",
           json.dumps({'app': 'plans-reservation', 'v': 10, 'plans': J['plans'] * 2, 'profils': {}, 'modeles': [], 'ent': {'nom': 'AUTRE SA'}}))
        ev("async()=>{await impJ()}"); pg.wait_for_timeout(100)
        if ev("dlgOpen()"):
            pg.click('#dlg [data-r="1"]')
        pg.wait_for_timeout(100)
        ev("async()=>{await expJ()}")
        s.check(ev("[P.length,ENT.nom,_pk,_w.length,FH&&FH.name]") == [2, 'AUTRE SA', 0, 1, 'projet_B.json'], 'ouvrir un fichier : plans + cartouche chargés, Ctrl+S réécrit ce fichier')

        # ---- note d'hypothèses ----
        ev("()=>{P.length=0;[['R1',{dL:600,dl:600,dh:400,oRenX:false}],['R2',{dL:1200,dl:800,dh:400}]].forEach(([r,o])=>{T.mk('rect',o);el('iRef').value=r;EI=-1;addP(true,true)});T.mk('voile',{dL:670,dl:150,dh:270,dDcuve:10});el('iRef').value='R3';EI=-1;addP(true,true)}")
        pg.click('#bNote'); pg.wait_for_timeout(200)
        sh = ev("[...document.querySelectorAll('#pvA .ps')].map(p=>p.innerText)")
        s.check(len(sh) == 4 and "NOTE D'HYPOTHÈSES" in sh[0] and 'pas une note de calcul' in sh[0] and 'Koskisen' in sh[0] and 'EN 1991-1-1' in sh[0], f'note : synthèse + 1 feuille par plan ({len(sh)}), limites et sources')
        s.check('p = 25 × 0,40 m = 10,0 kN/m²' in sh[1] and 'NON CONFORME' in sh[1] and 'Flèche du CP' in sh[1], 'note : plan R1 — poussée, flèche non conforme, alerte reprise')
        s.check('conforme' in sh[2] and 'NON CONFORME' not in sh[2] and 'Renfort le plus sollicité' in sh[2], 'note : plan R2 — flèche conforme, renfort le plus sollicité')
        s.check('forme non couverte' in sh[3], 'note : voile — flèche non vérifiée (dit)')
        pr = ev("()=>{window.print=()=>{};printAll();const n=document.querySelectorAll('#pvA .ps').length,p=[...document.querySelectorAll('#pvA .pno')].map(x=>x.textContent);document.body.classList.remove('pm');return [n,p,VIEW]}")
        s.check(pr[0] == 4 and pr[1][-1] == 'p. 4 / 4' and pr[2] == 'note', f'impression de la note : 4 feuilles numérotées — {pr[1]}')
        ev("()=>{VIEW='plan';prev()}")
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    import sys
    s = Suite('t_v26')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
