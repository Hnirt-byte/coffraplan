"""v2.4 — passe complète : renfort du mannequin de voile, défauts (feuilles annexes, axe des poteaux), audit (code mort,
cache gouGeo, stockage plein, textes hostiles), cartes repliables, accueil, série depuis un tableau, comparaison de deux
indices, mode chantier. Interface réelle ; aucune boîte de dialogue du navigateur."""
import json, os, re
from playwright.sync_api import sync_playwright
from lib import Suite, APP, OUT, HERE

OK = '#dlg [data-r="1"]'
ALLPRT = 'localStorage.setItem("resaPrint",JSON.stringify({cp:true,mt:true,fa:true}))'


def page(pw, w=1400, h=900, prt=True):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': w, 'height': h}, accept_downloads=True, has_touch=True)
    pg = ctx.new_page()
    errs, dialogs = [], []
    pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
    pg.on('dialog', lambda d: (dialogs.append(d.type), d.accept()))
    pg.goto('file://' + APP); pg.evaluate('localStorage.clear();' + (ALLPRT if prt else '')); pg.reload()
    pg.wait_for_function('typeof gen==="function" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
    return b, pg, errs, dialogs


def rl(pg):
    pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))


def t(s):
    src = open(APP, encoding='utf-8').read()
    with sync_playwright() as pw:
        # ============ 1. Mannequin de voile : renfort perpendiculaire au plus grand côté ============
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        MAN = "(ov)=>{const d=T.can(T.mk('voile',ov)),g=voileGeo(d),M=manGeo(d,g),R=debit(d,g),sc=model3(d,R);return{nC:M.nC,nM:M.nM,hp:M.hp,Lin:M.Lin,W:checks(d,g).map(x=>x[1]),bois:(R.bois||[]).map(b=>[b.n,b.q,Math.round(b.L)]),cp:R.map(r=>r.n),ov:overlap3(sc,0.5,6).length,txt:gen(d)}}"
        r = ev(MAN, {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10})
        s.check(r['Lin'] > r['hp'] and r['nM'] == 1 and r['nC'] == 0, f"R03 (corde 670 × h 270) : largeur > hauteur → 1 montant ({r['nM']}), aucune cerce", str({k: r[k] for k in ('nC', 'nM', 'hp', 'Lin')}))
        s.check(any('Montants' in b[0] and b[1] == 1 and abs(b[2] - r['hp']) < 1 for b in r['bois']), f"R03 : montant au débit bois (1 × L {round(r['hp'])})", str(r['bois']))
        s.check(r['ov'] == 0, 'R03 : 3D sans interpénétration avec le montant', str(r['ov']))
        s.check('1 × 63 × 75 par niveau' in r['txt'] or 'Montants 63 × 75 : 1 par niveau' in r['txt'], 'R03 : montant décrit sur le plan')
        r = ev(MAN, {'dL': 400, 'dl': 150, 'dh': 900, 'dDcuve': 10})
        s.check(r['hp'] > r['Lin'] and r['nC'] >= 1, f"hauteur > largeur → au moins 1 cerce ({r['nC']})")
        r = ev(MAN, {'dL': 500, 'dl': 150, 'dh': 536, 'dDcuve': 10})
        s.check(r['hp'] > r['Lin'] and r['nC'] == 1 and r['nM'] == 0, f"h 500 > largeur 464 (entraxe 600 non atteint) → 1 cerce à mi-hauteur", str({k: r[k] for k in ('nC', 'nM', 'hp', 'Lin')}))
        s.check(r['ov'] == 0, 'cerce ajoutée : 3D sans interpénétration')
        r = ev(MAN, {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10, 'oEM': 0})
        s.check(r['nM'] == 0, 'entraxe des montants = 0 (aucun, choix de l\'utilisateur) : respecté')
        r = ev("()=>{const d=T.can(T.mk('voile',{dL:2000,dl:200,dh:2500,dDcuve:12})),g=voileGeo(d),M=manGeo(d,g);return [M.nC,M.nM]}")
        s.check(r[0] >= 3 and r[1] >= 1, f'grand voile : renforts par entraxe inchangés ({r})')
        b.close()

        # ============ 2. Valeurs par défaut ============
        b, pg, errs, dlg = page(pw, prt=False)
        ev = pg.evaluate
        r = ev("[...document.querySelectorAll('#zPrt input[type=checkbox]')].map(e=>[e.closest('label').textContent.trim(),e.checked])")
        s.check(all(not c for l, c in r if re.search(r'Feuilles CP|Montage 3D|Fiche atelier|Noir et blanc', l)) and len([1 for l, c in r if re.search(r'Feuilles CP|Montage 3D|Fiche atelier|Noir et blanc', l)]) == 4,
                'impression : feuilles CP, montage 3D, fiche atelier, noir et blanc décochés par défaut', str(r))
        r = ev("(()=>{const s=[...document.querySelectorAll('#zPrt select')].find(x=>[...x.options].some(o=>/feuilles/.test(o.text)&&/Si/.test(o.text)));return s?[s.value,[...s.options].map(o=>o.text)]:null})()")
        s.check(r and r[0] == '0' and 'Si > 5 feuilles' in r[1], 'sommaire : « Jamais » par défaut, option « Si > 5 feuilles »', str(r))
        r = ev("()=>{PRT.som=true;PRT.cp=PRT.mt=PRT.fa=true;T.mk('rect',{dL:1200,dl:800,dh:300});const a=printPack([coll()]);const n=(a.match(/class=\"ps[ \"]/g)||[]).length;const som=/SOMMAIRE/.test(a);PRT.som=false;PRT.cp=PRT.mt=PRT.fa=false;return [n,som]}")
        s.check(r[1] == (r[0] - 1 > 5), f'sommaire seulement au-delà de 5 feuilles ({r[0]} feuilles, sommaire {r[1]})')
        n0 = ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});return (gen(coll()).match(/class=\"ps[ \"]/g)||[]).length}")
        ev("()=>{PRT.cp=PRT.mt=PRT.fa=true}")
        n1 = ev("(gen(coll()).match(/class=\"ps[ \"]/g)||[]).length")
        s.check(n0 < n1, f'feuilles annexes ajoutées seulement si cochées ({n0} → {n1} feuilles)')
        r = ev("()=>{const d=T.can(T.mk('special',{dBase:'circ',oConc:true,oPot:true,oFondSup:true}));return [d.pR,checks(d,null).map(x=>x[1]).filter(m=>/concentrique/.test(m))]}")
        s.check(r[0] == 200 and not r[1], 'forme spéciale : axe des poteaux 200 par défaut, plus d\'alerte concentrique à l\'ouverture', str(r))
        b.close()

        # ============ 3. Audit ============
        for fn in ['xlsxBlob', 'travLen', 'gabFit', 'pip2', 'chantierSheets', 'debitCSVSelfTest', 'nestCount', 'platePoly', 'jouePiecesSelfTest', 'zipStore', 'normPoly']:
            s.check(not re.search(r'function ' + fn + r'\(', src), f'code mort retiré : {fn}')
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        r = ev("()=>{T.mk('goulotte',{});const d=canon(coll());let n=0;const g0=gouGeo0;window.gouGeo0=x=>{n++;return g0(x)};_gouC.clear();const t=performance.now();liveCalc();prev();const ms=performance.now()-t;window.gouGeo0=g0;return [n,Math.round(ms)]}")
        s.check(r[0] <= 3, f'goulotte : géométrie calculée {r[0]} fois par recalcul (11 avant le cache), {r[1]} ms')
        r = ev("()=>{T.mk('goulotte',{});const d=canon(coll()),a=JSON.stringify(gouGeo0(d));gen(coll());debit(d,null);cutNest(d,debit(d,null));model3(d,debit(d,null));return a===JSON.stringify(gouGeo(d))}")
        s.check(r, 'cache gouGeo : résultat non modifié par les appelants (identique au calcul direct)')
        r = ev("""()=>{const o=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='resa3')throw new Error('QuotaExceededError');return o.call(this,k,v)};
          try{T.mk('rect',{dL:1200,dl:800,dh:300});el('iRef').value='';addP(false);if(dlgOpen())dlgEnd(true)}finally{Storage.prototype.setItem=o}}""")
        pg.wait_for_timeout(100); r = ev("dlgOpen()?el('dlgB').textContent:''")
        s.check('refuse d\'enregistrer' in r, 'stockage du navigateur plein : l\'utilisateur est prévenu (au lieu d\'une perte silencieuse)', r)
        ev("dlgEnd(true)")
        # textes hostiles dans toutes les saisies libres : rien ne doit s'exécuter ni s'insérer
        X = '<img src=x onerror="window.__x=(window.__x||0)+1">'
        ev("()=>{window.prompt=null}")
        ev(f"""(X)=>{{P.length=0;T.mk('rect',{{dL:1200,dl:800,dh:300}});el('iCh').value=X;el('iOuv').value=X;el('iRef').value=X;el('iInd').value=X;addP(false);if(dlgOpen())dlgEnd(true);
          T.mk('rect',{{dL:1300,dl:800,dh:300}});el('iCh').value=X;el('iOuv').value=X;el('iRef').value=X+'2';el('iInd').value='B';addP(true);if(dlgOpen())dlgEnd(true)}}""", X)
        pg.wait_for_timeout(200)
        steps = ["rnL()", "shP(0)", "prev()", "showChantier()", "VIEW='plan';prev()", "openCmp()", "closeModal();showCmp(0,1)", "openChm()", "closeChm()",
                 "LIBU.push({name:" + json.dumps(X) + ",d:coll()});libUI();libManage()", "closeModal();openSeries();el('serT').value=" + json.dumps('Réf\tForme\tL\tl\th\n' + X + '\t' + X + '\t1000\t600\t250') + ";serAnalyse()",
                 "closeModal();uiAlert(" + json.dumps(X) + "," + json.dumps(X) + ")", "dlgEnd(false);toast(" + json.dumps(X) + ")", "dossierHtml(chantierPlans(S('iCh')))", "autoControl(true);closeModal()", "foldInit();foldSums()"]
        bad = []
        for st in steps:
            try:
                ev("()=>{" + st + "}")
            except Exception as e:
                bad.append(st + ' → ' + str(e)[:120])
        pg.wait_for_timeout(500)
        s.check(not bad, 'textes hostiles : tous les écrans s\'ouvrent', str(bad))
        s.check(ev("!window.__x") and ev("!document.querySelector('img[src=\"x\"]')"), 'textes hostiles (balises dans chantier, ouvrage, repère, indice, modèle, tableau collé) : rien n\'est exécuté ni inséré')
        s.check(not dlg, 'aucune boîte de dialogue du navigateur', str(dlg))
        s.check(not errs, 'audit : aucune erreur JS', str(errs[:3]))
        b.close()

        # DXF ouvert dans AutoCAD (police txt.shx) : aucun caractère sans glyphe (affiché « ? »), titres en deux lignes
        import ezdxf
        b, pg, errs, dlg = page(pw)
        bad, n = [], 0
        for f, ov in [('voile', {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10}), ('special', {'dBase': 'circ', 'oPot': True, 'oConc': True, 'oFondSup': True}), ('dalle', {'dlPt': True}), ('goulotte', {}), ('rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400})]:
            by = pg.evaluate("([f,ov])=>{const x=dxfPlanFile(T.mk(f,ov));return x.err||Array.from(x.bytes)}", [f, ov])
            p_ = os.path.join(OUT, f'v24_{f}.dxf'); open(p_, 'wb').write(bytes(by))
            doc = ezdxf.readfile(p_); T_ = [e.dxf.text for e in doc.modelspace() if e.dxftype() == 'TEXT']; n += len(T_)
            bad += [(f, t) for t in T_ if any(ord(c) > 126 and c not in 'àâäçéèêëîïôöùûüÀÂÄÇÉÈÊËÎÏÔÖÙÛÜœŒ' for c in t)]
            tt = [e for e in doc.modelspace() if e.dxftype() == 'TEXT' and e.dxf.layer == 'CARTOUCHE']
            H_ = {round(e.dxf.height, 3) for e in tt if re.match(r'(VUE EN PLAN|CP À DÉCOUPER|GABARITS 1:1|VUES DES FEUILLES)', e.dxf.text)}
            s.check(len(H_) == 1, f'DXF {f} : titres de section de même hauteur ({H_})', str(sorted({round(e.dxf.height) for e in tt})))
        s.check(not bad, f'DXF : {n} textes, aucun caractère absent de la police AutoCAD txt.shx (— × · → ° Ø remplacés)', str(bad[:4]))
        s.check(any('%%c' in t for t in [e.dxf.text for e in ezdxf.readfile(os.path.join(OUT, 'v24_special.dxf')).modelspace() if e.dxftype() == 'TEXT']), 'DXF : diamètre écrit %%c (symbole Ø AutoCAD)')
        b.close()

        # ============ 4. Cartes repliables + accueil ============
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        s.check(ev("el('zWel').style.display") != 'none', 'accueil affiché quand aucun plan')
        pg.click('#zWel button:has-text("Trémie 500")'); pg.wait_for_timeout(300)
        s.check(ev("S('iForme')") == 'carre' and ev("V('dL')") == 500, 'accueil : modèle « Trémie 500 × 500 » chargé')
        cards = ev("[...document.querySelectorAll('.sb .cd>.ct.fold')].map(t=>foldKey(t.parentNode))")
        s.check(all(k in cards for k in ['Chantier', 'Type', 'Dimensions', 'Contreplaqué', 'Impression', 'Plans']), f'cartes repliables ({len(cards)}) : {cards}')
        pg.click('.sb .cd:has(#dL) > .ct')
        r = ev("(()=>{const c=el('dL').closest('.cd');return [c.classList.contains('col'),el('dL').offsetParent===null,c.querySelector('.sum').textContent,c.querySelector('.ct').getAttribute('aria-expanded')]})()")
        s.check(r[0] and r[1] and '500' in r[2] and r[3] == 'false', f'Dimensions repliée : champs masqués, résumé « {r[2]} »')
        pg.focus('.sb .cd:has(#iCh) > .ct'); pg.keyboard.press('Enter')
        s.check(ev("el('iCh').closest('.cd').classList.contains('col')"), 'clavier : Entrée replie la carte')
        el_sum = ev("el('iCh').closest('.cd').querySelector('.sum').textContent")
        s.check(el_sum and el_sum != '—', f'résumé Chantier : « {el_sum} »')
        ev("()=>{el('iCh').value='CH';T.mk('carre',{dL:99999})}"); ev("liveCalc()")
        pg.click('#zChk [data-f="dL"]')
        s.check(not ev("el('dL').closest('.cd').classList.contains('col')") and ev("document.activeElement.id") == 'dL', 'alerte vers un champ d\'une carte repliée : la carte se déplie')
        rl(pg); ev = pg.evaluate
        s.check(ev("el('iCh').closest('.cd').classList.contains('col')") and not ev("el('dL').closest('.cd').classList.contains('col')"), 'état replié / déplié mémorisé')
        ev("()=>{T.mk('carre',{});el('iRef').value=''}"); pg.click('#bAdd')
        s.check(ev("el('zWel').style.display") == 'none', 'accueil masqué dès le premier plan')
        ev("()=>{dlP(0)}")
        s.check(ev("el('zWel').style.display") != 'none', 'liste vidée : accueil de retour')
        pg.click('#zWel button:has-text("Masquer")')
        rl(pg); ev = pg.evaluate
        s.check(ev("el('zWel').style.display") == 'none', '« Masquer » : accueil plus affiché')
        s.check(not errs, 'repli / accueil : aucune erreur JS', str(errs[:3]))
        b.close()

        # ============ 5. Série depuis un tableau ============
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});el('iCh').value='';el('iOuv').value='Bassin'}")
        pg.click('button:has-text("Série de plans depuis un tableau")')
        pg.fill('#serT', 'T1\tRectangulaire\t1000\t600\t250\t2'); ev("serAnalyse()")
        s.check('nom du chantier' in ev("el('serR').textContent") and ev("el('serGo').disabled"), 'série sans nom de chantier : bloquée avec explication')
        ev("closeModal()"); ev("el('iCh').value='STEP'")
        snap0 = ev("formSnap()")
        pg.click('button:has-text("Série de plans depuis un tableau")')
        T = ('Réf\tForme\tL\tl\th\tNombre\tOuvrage\n'
             'T1\tRectangulaire\t1000\t600\t250\t2\t\n'
             'F1\tFourreau\t\t\t200\t4\tPoste\n'
             'X1\tbidule\t1\t1\t1\t1\t\n'
             'T2\t\t800\t800\t300\t\t\n'
             'T3\tRectangulaire\t1 200\t7a0\t250\t1\t\n'
             'T4\trect\t900\t500\t250\t1\t')
        pg.fill('#serT', T); pg.wait_for_timeout(700)
        R = ev("SER.rows.map(x=>({f:x.f,st:x.st,m:x.msg.join(' | '),d:x.d?{ref:x.d.ref,L:x.d.L,l:x.d.l,h:x.d.h,D:x.d.D,nb:x.d.nb,ouv:x.d.ouv,forme:x.d.forme}:null}))")
        s.check(ev("SER.head") and R[0]['st'] == 'ok' and R[0]['d']['L'] == 1000 and R[0]['d']['l'] == 600 and R[0]['d']['h'] == 250 and R[0]['d']['nb'] == 2 and R[0]['d']['ouv'] == 'Bassin', 'ligne 1 : rectangulaire 1000 × 600 × 250, × 2, ouvrage du formulaire', str(R[0]))
        s.check(R[1]['f'] == 'circ' and R[1]['d']['h'] == 200 and R[1]['d']['nb'] == 4 and R[1]['d']['ouv'] == 'Poste', 'ligne 2 : fourreau → circulaire, ouvrage de la colonne', str(R[1]))
        s.check(R[2]['st'] == 'er' and 'inconnue' in R[2]['m'], 'forme inconnue : ligne refusée avec motif')
        s.check(R[3]['f'] == 'carre' and R[3]['d']['L'] == 800 and R[3]['d']['nb'] == 1, 'forme absente, L = l → carré, nombre 1 par défaut', str(R[3]))
        s.check(R[4]['st'] == 'er' and 'illisible' in R[4]['m'], 'cote illisible (« 7a0 ») : ligne refusée', str(R[4]))
        s.check(R[5]['st'] in ('ok', 'wn') and R[5]['f'] == 'rect', 'abréviation « rect » reconnue')
        s.check(ev("el('serGo').textContent") == 'Créer 4 plan(s)', 'bouton « Créer 4 plan(s) » (lignes refusées exclues)')
        s.check(ev("formSnap()") == snap0, 'analyse : formulaire remis exactement dans son état')
        pg.click('#serGo'); pg.wait_for_timeout(300)
        P = ev("P.map(p=>[p.ref,p.forme,p.L,p.l,p.h,p.nb,p.ch,p.ouv])")
        s.check([x[0] for x in P] == ['T1', 'F1', 'T2', 'T4'] and all(x[6] == 'STEP' for x in P), f'4 plans créés, chantier du formulaire : {P}')
        s.check(ev("formSnap()") == snap0, 'création : formulaire inchangé')
        # séparateur point-virgule, sans en-tête, virgule décimale ; Ø pour une forme sans diamètre
        pg.click('button:has-text("Série de plans depuis un tableau")')
        pg.fill('#serT', 'T5;Rectangulaire;1000,5;600;250;1\nT6;Fourreau;;;;1'); pg.wait_for_timeout(700)
        R = ev("SER.rows.map(x=>({st:x.st,L:x.d&&x.d.L,m:x.msg.join(' | ')}))")
        s.check(not ev("SER.head") and R[0]['L'] == 1000.5, 'sans en-tête, « ; » et virgule décimale : L 1000,5', str(R))
        pg.fill('#serT', 'Réf\tForme\tL\tØ\th\nT1\tRectangulaire\t1000\t300\t250'); pg.wait_for_timeout(700)
        R = ev("SER.rows.map(x=>({st:x.st,m:x.msg.join(' | ')}))")
        s.check(R[0]['st'] in ('er', 'wn') and ('déjà utilisée' in R[0]['m'] or 'sans objet' in R[0]['m']), 'référence déjà utilisée / colonne sans objet signalées', str(R))
        ev("closeModal()")
        pg.click('#toast button:has-text("Annuler")') if ev("el('toast').classList.contains('act')") else None
        s.check(not dlg, 'série : aucune boîte de dialogue du navigateur', str(dlg))
        s.check(not errs, 'série : aucune erreur JS', str(errs[:3]))
        b.close()
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        ev("()=>{el('iCh').value='STEP';openSeries();el('serT').value='A1\\tCarré\\t500\\t500\\t200\\t1\\nA2\\tCarré\\t600\\t600\\t200\\t1';serAnalyse()}")
        pg.click('#serGo'); pg.click('#toast button:has-text("Annuler")')
        s.check(ev("P.length") == 0, 'série : « Annuler » retire les plans créés')
        b.close()

        # ============ 6. Comparer deux indices ============
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        ev("()=>{window._np=0;window.print=()=>{window._np++}}")
        ev("()=>{T.mk('rect',{dL:1000,dl:600,dh:250});el('iRef').value='R1';el('iInd').value='A';addP(false);if(dlgOpen())dlgEnd(true)}")
        ev("()=>{T.mk('rect',{dL:1000,dl:600,dh:250});el('iRef').value='R9';addP(false);if(dlgOpen())dlgEnd(true)}")
        ev("()=>{T.mk('rect',{dL:1100,dl:600,dh:250,oFeuil:true});el('iRef').value='R1';el('iInd').value='B';addP(false);if(dlgOpen())dlgEnd(true)}")
        ev("shP(2)"); snap = ev("formSnap()")
        pg.click('#zEdit button:has-text("Comparer")')
        s.check(ev("el('cmpA').value") == '0' and 'même repère' in ev("el('cmpA').selectedOptions[0].text"), 'comparer R1 ind. B : R1 ind. A proposé par défaut (même repère)')
        pg.click('#mdBody .bpr'); pg.wait_for_timeout(300)
        t = ev("el('pvA').innerText")
        s.check('COMPARAISON R1 IND. A → R1 IND. B' in t.upper(), 'feuille de comparaison titrée A → B')
        rows = ev("[...document.querySelectorAll('#pvA table.cmp')[0].rows].slice(1).map(r=>[...r.cells].map(c=>c.textContent))")
        s.check(any('Longueur' in r[1] and r[2] == '1000' and r[3] == '1100' for r in rows) and any('Indice' in r[1] and r[2] == 'A' and r[3] == 'B' for r in rows), 'saisies modifiées : longueur 1000 → 1100, indice A → B', str(rows))
        s.check(any('Feuillure' in r[1] for r in rows), 'option cochée détectée (feuillure)')
        s.check(not any(r[2] == r[3] for r in rows) and not any(r[1].startswith('Largeur l') for r in rows), 'saisies identiques non listées (largeur inchangée absente)', str(rows))
        st = ev("[...document.querySelectorAll('#pvA table.cmp')[1].rows].slice(1).map(r=>r.className)")
        s.check('chg' in st and ('add' in st), f'débit : lignes modifiées et ajoutées surlignées ({st})')
        s.check(ev("formSnap()") == snap and ev("EI") == 2, 'comparaison : formulaire et plan affiché inchangés')
        pg.keyboard.press('Control+p'); pg.wait_for_timeout(300)
        s.check(ev("window._np") == 1 and ev("!!document.querySelector('#pvA .ps.portrait')"), 'Ctrl+P : impression de la feuille de comparaison')
        pg.click('button:has-text("Retour au plan")')
        s.check(ev("VIEW") == 'plan', 'retour au plan')
        s.check(not errs, 'comparaison : aucune erreur JS', str(errs[:3]))
        b.close()

        # ============ 7. Mode chantier ============
        b, pg, errs, dlg = page(pw, w=1180, h=820)
        ev = pg.evaluate
        ev("()=>{T.mk('rect',{dL:1000,dl:600,dh:250});el('iRef').value='R1';addP(false);if(dlgOpen())dlgEnd(true);T.mk('special',{dBase:'circ',oPot:true});el('iRef').value='R2';addP(false);if(dlgOpen())dlgEnd(true)}")
        pg.click('button[aria-label="Mode chantier"]'); pg.wait_for_timeout(400)
        n = ev("CHM.n"); vis = ev("[...el('chmV').querySelectorAll('.ps')].filter(s=>s.style.display!=='none').length")
        s.check(ev("chmOn()") and n == ev("(gen(P[0]).match(/class=\"ps[ \"]/g)||[]).length") and vis == 1, f'mode chantier : {n} feuilles, une seule affichée')
        w = ev("el('chmV').querySelector('.ps').getBoundingClientRect().width"); W = ev("el('chmS').clientWidth")
        s.check(abs(w - (W - 20)) < 3, f'feuille ajustée à la largeur de l\'écran ({w:.0f} / {W - 20})')
        s.check(ev("[...el('chmV').querySelectorAll('.drg,.no-print')].every(e=>getComputedStyle(e).display==='none')"), 'lecture seule : poignées et boutons d\'écran masqués')
        pg.click('#chmR'); s.check(ev("CHM.k") == 1 and ev("el('chmPg').textContent") == f'Feuille 2 / {n}', 'bouton › : feuille suivante')
        pg.keyboard.press('ArrowLeft'); s.check(ev("CHM.k") == 0, 'touche ← : feuille précédente')
        bx = pg.locator('#chmS').bounding_box(); y = bx['y'] + bx['height'] / 2
        pg.mouse.move(bx['x'] + bx['width'] * 0.8, y); pg.mouse.down(); pg.mouse.move(bx['x'] + bx['width'] * 0.2, y + 10, steps=5); pg.mouse.up()
        s.check(ev("CHM.k") == 1, 'balayage vers la gauche : feuille suivante')
        pg.select_option('#chmP', '1'); pg.wait_for_timeout(300)
        s.check(ev("CHM.i") == 1 and ev("CHM.k") == 0, 'choix du plan R2 : première feuille')
        pg.click('#chmK')
        tags = ev("[...el('chmC').querySelectorAll('input[data-t]')].map(e=>e.dataset.t)")
        s.check(tags and all(t.startswith('R2-') for t in tags), f'repères du plan R2 ({len(tags)})')
        pg.click('#chmC input[data-t]'); pg.wait_for_timeout(100)
        s.check(ev("el('chmKn').textContent") == f'1 / {len(tags)}', 'repère coché : compteur 1 / n')
        pg.keyboard.press('Escape'); s.check(not ev("chmOn()"), 'Échap : mode chantier fermé')
        rl(pg); ev = pg.evaluate
        ev("openChm()"); ev("chmPlan(1)")
        s.check(ev("el('chmC').querySelectorAll('input:checked').length") == 1 and ev("el('chmKn').textContent").startswith('1 /'), 'repères cochés conservés (rechargement)')
        s.check(ev("JSON.stringify(P).indexOf('resaChk')") < 0 and 'chk' not in ev("Object.keys(P[1]).join(',')"), 'repères cochés hors du fichier projet (format inchangé)')
        ev("closeChm()")
        s.check(not errs, 'mode chantier : aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    import sys
    s = Suite('t_v24')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
