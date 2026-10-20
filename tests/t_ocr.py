"""Reconnaissance OCR locale des nomenclatures PDF (modules/import/ocr.js, Tesseract.js intégré), sur l'interface réelle et des PDF
entièrement fictifs (tests/pdf_ocr_fictifs.py : textes dessinés en contours vectoriels, tableau numérisé ; tests/pdf_fictifs.py :
texte extractible). Demande de Kévin du 19/10/2026 (phase 3) :
  documents : textes en tracés, tableau en image, texte extractible (pas de régression, OCR évité), multipage, page tournée,
  tableau avec et sans bordures ; reconnaissance : repères, rectangle, Ø, DN seul, SO, vide, description longue, accents,
  plusieurs types gardés, valeurs incertaines signalées (brut gardé), ligne manquante / en trop / coupée corrigeable ;
  création : confirmation, rectangle, fourreau, à compléter, références sans doublon, provenance OCR, sauvegarde et
  rechargement, débit = saisie manuelle, annulation ; technique : HTML autonome en file://, aucune requête réseau, worker et
  wasm, arrêt de la reconnaissance, aciers écartés.
Réseau : les requêtes Google Fonts de l'interface (héritées, hors OCR) sont bloquées et ignorées ; toute autre requête échoue le test.
Les valeurs reconnues dépendent du rendu des polices : les contrôles portent sur la structure (lignes, colonnes, signalements)
et sur des cellules choisies, pas sur chaque caractère."""
import json, os, re, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
import pdf_fictifs as PF
import pdf_ocr_fictifs as PO

ROOT = os.path.join(HERE, '..')
cle = lambda s: re.sub(r'(^|[^0-9])0+(?=\d)', r'\1', re.sub(r'[\s._\-–—/]+', '', str(s or '').upper()))


def t(s):
    rc = subprocess.run([sys.executable, os.path.join(ROOT, 'modules', 'import', 'assembler.py'), '--check'], capture_output=True, text=True)
    s.check(rc.returncode == 0, 'assemblage : moteur OCR identique aux fichiers publiés (empreintes SHA-256) et aux sources', rc.stdout + rc.stderr)
    html = open(os.path.join(ROOT, 'app', 'CoffraPlan.html'), encoding='utf-8').read()
    s.check(all(f'id="{i}"' in html for i in ('tess-src', 'tess-worker-src', 'tess-core-src', 'tess-wasm', 'tess-fra')) and '<script src=' not in html
            and 'cdn.jsdelivr' not in html.split('id="tess-src"')[0], 'HTML autonome : Tesseract.js, cœur wasm et modèle français intégrés, aucun script externe')
    tmp = tempfile.mkdtemp()
    F = PO.fichiers(tmp)
    T1 = PF.fichiers(os.path.join(tmp, 'txt'))['PDF_1_TABLEAU.pdf'][0]
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        net = []   # polices Google de l'interface : demandées par l'appli depuis toujours, repli local sans réseau (hors OCR)
        pg.context.route(lambda u: not u.startswith('file:') and not u.startswith('blob:') and not u.startswith('data:'),
                         lambda r: (None if 'fonts.g' in r.request.url else net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = lambda x, *a: pg.evaluate(x, *a)

        # ---- corrections automatiques prudentes (brut gardé à part)
        C = J('''()=>Object.fromEntries(['RO1','B18','PS2','6S0x8OO','@250','DN2O0','+12,5O','(rnm)','évacuation','O250'].map(t=>[t,CPI.ocr.corriger(t).texte]))''')
        s.check(C == {'RO1': 'R01', 'B18': 'B18', 'PS2': 'PS2', '6S0x8OO': '650x800', '@250': 'Ø250', 'DN2O0': 'DN200', '+12,5O': '+12,50', '(rnm)': '(mm)',
                      'évacuation': 'évacuation', 'O250': 'O250'},
                'corrections : O/0, S/5, B/8 dans les nombres seulement ; 1re lettre d\'un repère gardée ; @ → Ø ; mots ordinaires intacts', json.dumps(C, ensure_ascii=False))

        # ---- nombre seul à faible confiance dans les dimensions : jamais converti en diamètre (250 ≠ Ø50), ambiguïté signalée
        A = J('''()=>{const V=['250','900','2500'],T=V.flatMap((v,i)=>[{id:'r'+i,texte:'A'+i,ocr:{brut:'A'+i,conf:95}},{id:'o'+i,texte:v,ocr:{brut:v,conf:40}}]);
          const N={colonnes:[{cle:'repere',titre:'Repère'},{cle:'ouverture',titre:'Ouverture'}],lignes:V.map((v,i)=>({id:'x'+i,repere:'A'+i,cellules:['A'+i,v],idsCellules:[['r'+i],['o'+i]]}))};
          const R=CPI.ocr.grille(N,T),M=CPI.ocr.versNomenclature(R,{id:'T',fichier:'t.pdf',page:1,zone:null,unite:'mm',mesures:{}});
          return R.map((w,i)=>({v:w.cells.ouverture,doute:w.doute.ouverture,corr:w.corr.ouverture.join(' '),etat:CPI.nomenclatures.cotes(w.cells.ouverture).etat,dims:M.lignes[i].dims}))}''')
        s.check(all(x['v'] == v and x['doute'] and 'ambigu' in x['corr'] and x['etat'] != 'circ' and not (x['dims'] or {}).get('D') for x, v in zip(A, ['250', '900', '2500'])),
                'ouverture 250 / 900 / 2500 à faible confiance : valeur gardée, ambiguïté signalée, aucune dimension circulaire exploitable', json.dumps(A, ensure_ascii=False))

        # ---- moteur : worker + wasm + modèle français, en file://, sans réseau
        m = J('''async()=>{const t=performance.now();await CPI.ocr.charger();const c=document.createElement('canvas');c.width=900;c.height=90;const g=c.getContext('2d');
          g.fillStyle='#fff';g.fillRect(0,0,900,90);g.fillStyle='#000';g.font='34px Liberation Sans, DejaVu Sans, sans-serif';g.fillText('Trémie réservée 650 x 800 mm',12,58);
          const M=await CPI.ocr.reconnaitre(c,{psm:7});return{ms:performance.now()-t,txt:M.map(m=>m.texte).join(' '),proto:location.protocol}}''')
        s.check(m['proto'] == 'file:' and 'Trémie' in m['txt'] and 'réservée' in m['txt'] and '650' in m['txt'] and '800' in m['txt'],
                'moteur démarré en file:// (worker blob, wasm et modèle fra embarqués) : texte français et chiffres reconnus', json.dumps(m, ensure_ascii=False))

        # ---- PDF 1 (3 pages, textes en contours) : fenêtre, page 2, zone de la nomenclature, OCR
        J('''()=>{el('iCh').value='CHANTIER_DEMO_O';el('iOuv').value='OUVRAGE_O';el('iForme').value='rect';updF();el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='RA07';addP()}''')
        P0 = J('JSON.stringify(P)')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['OCR_1_CONTOURS.pdf'][0])
        pg.wait_for_function('el("dxpPg")&&el("dxpPg").textContent.includes("/ 3")')
        n = pg.inner_text('#dxiN')
        s.check('aucune nomenclature lisible automatiquement : OCR ou saisie assistée' in n and J('DXI.NL.length') == 0, 'PDF en tracés : rien lu par le texte, OCR proposé', n)
        inf = F['OCR_1_CONTOURS.pdf'][1]

        def zone(z):
            J('z=>{dxiVue("p");DXI.page=z.page;dxpPage();dxpZone(Object.assign({unite:"pt"},z))}', z)
            pg.wait_for_function('!el("dxpZo").disabled')

        def ocr():
            pg.click('#dxpZo')
            pg.wait_for_function('!DXI.ocJob', timeout=120000)
            return pg.inner_text('#dxpZr')
        s.check(pg.is_visible('#dxpZo') and pg.is_disabled('#dxpZo') and pg.text_content('#dxpZo').strip() == 'Reconnaître le tableau (OCR)' and pg.text_content('#dxpZa').strip() == 'Analyser la zone',
                'aperçu : deux actions distinctes, « Analyser la zone » et « Reconnaître le tableau (OCR) », actives seulement avec une zone')
        zone(inf['z1'])
        pg.click('#dxpZa')
        s.check('aucun texte extractible' in pg.inner_text('#dxpZr') and 'Reconnaître le tableau (OCR)' in pg.inner_text('#dxpZr'), 'analyse texte de la zone : rien, l\'OCR est indiqué')
        r = ocr()
        G = lambda: J('DXI.OC&&DXI.OC.rows.map(w=>Object.assign({},w.cells,{_d:Object.keys(w.doute).filter(k=>w.doute[k]),_b:w.brut,_c:w.conf,_s:w.src}))')
        R = G()
        s.check('7 ligne(s) reconnue(s)' in r and len(R) == 7 and J('DXI.NL.length') == 0, 'OCR : 7 lignes reconnues (tableau à bordures), rien encore dans la nomenclature', r)
        reps = [w.get('repere', '') for w in R]
        ok_rep = sum(1 for w, l in zip(R, PO.L1) if cle(w.get('repere')) == cle(l[0]))
        s.check(ok_rep >= 5 and all(reps), 'repères alphanumériques : au moins 5 sur 7 exacts, aucun vide', json.dumps(reps))
        byd = dict(zip(['tremie', 'fourreau', 'dn', 'so', 'vide', 'longue', 'carottage'], R))
        s.check(byd['tremie'].get('ouverture') == '650x800' and byd['longue'].get('ouverture') == '1200x500', 'dimensions rectangulaires reconnues (650x800, 1200x500)',
                json.dumps([w.get('ouverture') for w in R]))
        s.check(all(re.fullmatch(r'Ø\s?' + d, w.get('ouverture', '')) or (re.fullmatch(r'\d+', w.get('ouverture', '')) and d in w['ouverture'] and 'ouverture' in w['_d'])
                    for w, d in ((byd['fourreau'], '250'), (byd['carottage'], '120'))),
                'dimension circulaire : Ø reconnu, sinon nombre brut gardé et signalé (jamais converti en Ø)', json.dumps([w.get('ouverture') for w in R]))
        s.check('DN160' in byd['dn'].get('reseau', '') and not byd['dn'].get('ouverture'), 'DN seul : dans « Réseau », ouverture vide (non inventée)')
        s.check(byd['so'].get('ouverture', '').upper() == 'SO' and not byd['vide'].get('ouverture'), 'cellule SO gardée, cellule vide laissée vide')
        s.check('désenfumage' in byd['longue'].get('description', '') and 'palier' in byd['longue'].get('description', ''), 'description longue sur deux lignes réunie')
        s.check(any('étanchéité' in w.get('description', '') for w in R) and len({w.get('type', '') for w in R}) >= 5, 'accents ; plusieurs types d\'éléments gardés (aucun filtre)',
                json.dumps([w.get('type') for w in R], ensure_ascii=False))
        nd = J('document.querySelectorAll("#dxoT .fi.dt").length')
        tip = J('[...document.querySelectorAll("#dxoT .fi.dt")].map(e=>e.title)[0]||""')
        s.check(nd >= 1 and 'OCR brut' in tip and 'confiance' in tip, 'cellules incertaines signalées dans la grille, texte brut et confiance consultables', f'{nd} · {tip}')
        s.check(J('document.querySelectorAll("#dxpO .od").length') >= 1, 'cellules incertaines encadrées sur l\'aperçu de la page')
        J('''()=>{const i=[...document.querySelectorAll('#dxoT .fi')].find(e=>e.classList.contains('dt'));i.focus()}''')
        s.check(J('document.querySelectorAll("#dxpO .hl").length') == 1 and J('DXI.ohl&&DXI.ohl.page') == 2, 'cellule choisie : emplacement encadré sur le PDF')
        s.check(J('[...document.querySelectorAll("#dxoT thead th")].map(e=>e.textContent)')[1:7] == ['Repère', 'Désignation', 'Type ou nature', "Dimensions d'ouverture", 'Réseau (DN)', 'Niveau ou altitude'],
                'grille : repère, désignation, type, dimensions, (réseau), niveau, observations, état')
        s.check(J('DXI.OC.unite') == 'mm', 'unité des dimensions lue dans l\'en-tête « (mm) »')

        # corrections dans la grille : repère, ligne manquante, ligne en trop, ligne coupée
        def cell(i, k, v):
            sel = f'#dxoT tr[data-o="{i}"] [data-k={k}]'
            pg.fill(sel, v)
        for i, l in enumerate(PO.L1):
            if R[i].get('repere') != l[0] or i == 1:
                cell(i, 'repere', l[0])
        if R[1].get('ouverture') != 'Ø250':
            cell(1, 'ouverture', 'Ø250')
        pg.click('#dxoT tr[data-o="6"] button[aria-label="Insérer une ligne"]')
        cell(7, 'repere', 'RA09'); cell(7, 'description', 'Ligne manquante ajoutée'); cell(7, 'ouverture', '300x300')
        pg.click('#dxoT tr[data-o="7"] button[aria-label="Insérer une ligne"]')
        cell(8, 'description', '(suite de la désignation)')
        pg.click('#dxoT tr[data-o="7"] button[aria-label="Fusionner avec la suivante"]')
        pg.click('#dxoT tr[data-o="0"] button[aria-label="Insérer une ligne"]'); cell(1, 'description', 'fausse ligne')
        pg.click('#dxoT tr[data-o="1"] button[aria-label="Retirer la ligne"]')
        R = G()
        s.check(len(R) == 8 and R[7]['repere'] == 'RA09' and R[7]['description'] == 'Ligne manquante ajoutée (suite de la désignation)' and not any(w.get('description') == 'fausse ligne' for w in R)
                and pg.is_visible('#dxoG button:has-text("Rétablir les 1 ligne(s) retirée(s)")'),
                'grille : ligne ajoutée, ligne coupée fusionnée, fausse ligne retirée (rétablissable)', json.dumps([w.get('repere') for w in R]))
        # relance de l'OCR : les corrections sont gardées
        r = ocr()
        R2 = G()
        s.check(len(R2) == 8 and [w.get('repere') for w in R2[:7]] == [l[0] for l in PO.L1] and R2[7]['repere'] == 'RA09' and R2[1].get('ouverture') == 'Ø250'
                and 'corrections gardées' in r and not any(w.get('description') == 'fausse ligne' for w in R2),
                'OCR relancé : corrections de l\'utilisateur et ligne ajoutée gardées', r + ' ' + json.dumps([w.get('repere') for w in R2]))
        # ajout à la nomenclature
        pg.click('#dxoV')
        s.check('8 ligne(s) ajoutée(s)' in pg.inner_text('#dxoR') and J('DXI.NL.length') == 8 and J('DXI.NL.every(x=>x.N.ocr&&x.N.page===2)'), 'lignes vérifiées ajoutées à la nomenclature (8)', pg.inner_text('#dxoR'))
        pg.click('#dxiTabN')
        s.check(J('document.querySelectorAll("#dxnT tr[data-n]").length') == 8 and J('document.querySelectorAll("#dxnT [data-k=conf]:checked").length') == 0 and pg.is_disabled('#dxiGo'),
                'onglet Nomenclature : 8 lignes, aucune cochée d\'office')
        s.check('(OCR)' in pg.inner_text('#dxiPN') and '8 ligne(s) reconnue(s) par OCR' in pg.inner_text('#dxnS'), 'tableau signalé comme lu par OCR', pg.inner_text('#dxnS'))
        st = J('[...document.querySelectorAll("#dxnT tr[data-n]")].map(t=>t.querySelector(".st").innerText)')
        s.check('DN du réseau' in st[2] or 'réseau' in st[2], 'DN seul : cotes à saisir (jamais tirées du DN)', st[2])
        # aciers (même page) : écartés
        zone(inf['za'])
        r = ocr()
        s.check('aucune nomenclature de réservations reconnue' in r and 'aciers' in r and J('DXI.NL.length') == 8, 'tableau d\'aciers reconnu par OCR : écarté, rien ajouté', r)
        # page tournée, tableau sans bordures
        zone(inf['z3'])
        r = ocr()
        R3 = G()
        s.check(len(R3) == 3 and [cle(w.get('repere')) for w in R3] == ['P1', 'P2', 'P3'] and R3[1].get('ouverture') == '500x500' and 'DN100' in json.dumps(R3[2]),
                'page tournée (/Rotate 90), tableau sans bordures : 3 lignes, repères et cotes', json.dumps(R3, ensure_ascii=False)[:500])
        s.check(J('DXI.NL.length') == 8, 'nouvelle zone : la nomenclature déjà ajoutée n\'est pas touchée avant « Ajouter »')
        # tableau A reconnu (corrigé), puis zone B sans résultat : la grille A n'est pas présentée comme résultat de B, corrections gardées
        pg.fill('#dxoT tr[data-o="0"] [data-k=description]', 'corrigé avant zone B')
        zone(inf['za'])
        r = ocr()
        s.check('aucune nomenclature de réservations reconnue' in r and 'reconnaissance précédente' in r and pg.is_visible('#dxoA')
                and J('DXI.OC.ancienne&&DXI.OC.rows.length===3&&DXI.OC.rows[0].cells.description==="corrigé avant zone B"&&DXI.OC.rows[0].edite.includes("description")'),
                'zone B sans résultat après le tableau A : grille A signalée « reconnaissance précédente », corrections gardées', r)
        pg.click('#dxoV')
        s.check(J('DXI.NL.length') == 11, 'deuxième tableau OCR ajouté (11 lignes)')
        # arrêt d'une reconnaissance en cours
        pg.click('#dxpZo'); pg.wait_for_selector('#dxoP button:has-text("Annuler")')
        # v3.1 : le bouton n'est plus recréé à chaque progression (un clic pouvait être perdu)
        J("()=>{window._ab=document.querySelector('#dxoP button');window._an=0;new MutationObserver(()=>window._an++).observe(el('dxoP'),{subtree:true,childList:true,characterData:true,attributes:true})}")
        pg.wait_for_function('window._an>=3')
        s.check(J("()=>document.querySelector('#dxoP button')===window._ab&&window._ab.isConnected&&!!DXI.ocJob"), 'progression OCR : bouton « Annuler » inchangé pendant les actualisations', str(J('window._an')))
        pg.click('#dxoP button:has-text("Annuler")')
        s.check('annulée' in pg.inner_text('#dxpZr') and not J('DXI.ocJob') and J('DXI.NL.length') == 11 and not pg.is_disabled('#dxpZo'), 'reconnaissance annulée : moteur arrêté, rien modifié')

        # ---- création
        pg.click('#dxiTabN')
        pg.fill('#dxiCh', 'CHANTIER_DEMO_O'); pg.dispatch_event('#dxiCh', 'change'); pg.fill('#dxiOuv', 'OUVRAGE_O'); pg.dispatch_event('#dxiOuv', 'change')
        pg.fill('#dxiInd', 'c'); pg.fill('#dxiH', '300')
        k9 = J('DXI.NL.findIndex(x=>x.L.repere==="RA09")')
        for k in (0, 1, k9):
            pg.check(f'#dxnT tr[data-n="{k}"] [data-k=conf]')
        pg.check('#dxnT tr[data-n="2"] [data-k=conf]')
        s.check('à compléter' in pg.inner_text('#dxnT tr[data-n="2"] .st') and pg.text_content('#dxiGo') == 'Créer les ouvrages sélectionnés (3)',
                'ligne DN seul cochée : « à compléter », non créée ; 3 ouvrages prêts', pg.inner_text('#dxnT tr[data-n="2"] .st'))
        s.check(J('JSON.stringify(P)') == P0, 'avant confirmation : aucun ouvrage créé')
        pg.click('#dxiGo')
        Pn = J('P.slice(1)')
        got = [(p['forme'], p.get('L'), p.get('l'), p.get('D'), p['h'], p['ref']) for p in Pn]
        s.check(got == [('rect', 800, 650, None, 300, 'RA01'), ('circ', None, None, 250, 300, 'RA02'), ('carre', 300, 300, None, 300, 'RA09')],
                'ouvrages créés : rectangle 800 × 650, fourreau Ø250, carré ajouté à la main ; repères repris', json.dumps(got))
        man = J('''(()=>{const p=P[1];el('iForme').value='rect';updF();el('iCh').value=p.ch;el('iOuv').value=p.ouv;el('iRef').value=p.ref;el('dL').value=800;el('dl').value=650;el('dh').value=300;liveCalc();
              const m=coll(),dm=debit(canon(migr(m)),null),di=debit(canon(migr(p)),null);return [JSON.stringify(dm)===JSON.stringify(di),JSON.stringify(dm).length]})()''')
        s.check(man[0] and man[1] > 50, 'débit de l\'ouvrage reconnu = débit de la même boîte saisie à la main', json.dumps(man))
        o = Pn[0]['origineImport']
        s.check(o['type'] == 'ocr' and o['format'] == 'pdf' and o['fichier'] == 'OCR_1_CONTOURS.pdf' and o['page'] == 2 and o['zone']['unite'] == 'pt'
                and abs(o['zone']['x0'] - inf['z1']['x0']) < 1 and o['repere'] == 'RA01' and o['indice'] == 'C' and o['dims_source']['a'] == 650 and o['unite'] == 'mm'
                and 'brut' in o['ocr'] and 'confiance' in o['ocr'] and 'Tesseract' in o['ocr']['moteur'] and o['textes'].get('Repère') == 'RA01' and len(json.dumps(o)) < 4000,
                'provenance OCR : PDF, page, zone, méthode, repère, textes bruts et retenus, unité, cotes, indice (sans image ni PDF)', json.dumps(o, ensure_ascii=False)[:900])
        o3 = Pn[2]['origineImport']
        s.check(o3['ocr']['ajoutee'] and o3['ocr']['corrige'].get('Repère') == 'RA09' and any('à la main' in a for a in o3['a_verifier']), 'provenance : ligne ajoutée et valeurs corrigées par l\'utilisateur')
        with pg.expect_download() as dl:
            pg.click('#bSave')
        exp = json.loads(open(dl.value.path(), encoding='utf-8').read())
        s.check(exp['v'] == 10 and sum(1 for p in exp['plans'] if (p.get('origineImport') or {}).get('type') == 'ocr') == 3, 'export JSON : enveloppe inchangée, 3 provenances OCR')
        J('t=>loadText(t,"x.json",null)', json.dumps(exp)); pg.click('#dlgB button:has-text("Remplacer")')
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        s.check(J('P.length') == 4 and J('P[1].origineImport.type') == 'ocr' and J('P[2].D') == 250, 'JSON rechargé, appli rouverte : ouvrages et provenance relus')
        # annulation d'un import
        n0 = J('P.length')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['OCR_2_SCAN.pdf'][0])
        pg.wait_for_function('el("dxpPg")&&el("dxpPg").textContent.includes("/ 1")')
        i2 = F['OCR_2_SCAN.pdf'][1]
        s.check('image seule' in pg.inner_text('#dxpI'), 'PDF numérisé : page « image seule »', pg.inner_text('#dxpI'))
        zone(i2['z2'])
        r = ocr()
        R4 = G()
        s.check(len(R4) == 4 and J('DXI.OC.unite') == 'cm' and R4[0].get('ouverture') == '90x70' and R4[2].get('ouverture') == '93x210' and R4[3].get('ouverture', '').upper() == 'SO',
                'tableau numérisé (image, cotes en cm) : 4 lignes, cotes et unité', json.dumps(R4, ensure_ascii=False)[:500])
        s.check(all(re.fullmatch(r'S\d', w.get('repere', '')) for w in R4), 'repères du scan normalisés (S1… : 1re lettre et chiffres)', json.dumps([w.get('repere') for w in R4]))
        pg.click('#dxoV'); pg.click('#dxiTabN')
        pg.fill('#dxiCh', 'CHANTIER_DEMO_O'); pg.dispatch_event('#dxiCh', 'change'); pg.fill('#dxiOuv', 'OUVRAGE_S'); pg.dispatch_event('#dxiOuv', 'change'); pg.fill('#dxiH', '200')
        s.check(J('DXI.NR[0].cotes') == '900 × 700', 'cotes en cm converties en mm pour la création (90x70 cm → 900 × 700)', J('DXI.NR[0].cotes'))
        pg.check('#dxnT tr[data-n="0"] [data-k=conf]'); pg.click('#dxiGo')
        s.check(J('P.length') == n0 + 1 and J('P[P.length-1].L') == 900, 'création depuis le scan')
        pg.click('#toast button:has-text("Annuler")')
        s.check(J('P.length') == n0, 'annulation de l\'import : ouvrage retiré')

        # ---- PDF à texte extractible : l'OCR n'est pas lancé sans accord, doublons évités
        pg.click('#bDxi'); pg.set_input_files('#dxiF', T1); pg.wait_for_selector('#dxnT tr[data-n]')
        s.check(J('DXI.NL.length') == 6, 'PDF à texte extractible : lecture automatique inchangée (6 lignes)')
        pg.click('#dxiTabP'); zone({'page': 1, 'x0': 290, 'y0': 380, 'x1': 800, 'y1': 545})
        pg.click('#dxpZo')
        s.check(pg.is_visible('#dlg') and 'déjà lisible par le texte' in pg.inner_text('#dlgB') and not J('DXI.ocJob'), 'texte extractible : OCR non lancé sans confirmation', pg.inner_text('#dlgB'))
        pg.click('#dlgB button:has-text("Lancer")')
        pg.wait_for_function('!DXI.ocJob&&DXI.OC', timeout=120000)
        pg.click('#dxoV')
        s.check('déjà' in pg.inner_text('#dxoR') and J('DXI.NL.length') == 6, 'OCR confirmé : lignes déjà lues par le texte non ajoutées (pas de doublon)', pg.inner_text('#dxoR'))
        # stabilisation : arrêt du moteur pendant la conversion de l'image → TypeError « postMessage » non interceptée (t_ocr intermittent)
        n0 = len(errs)
        st = J('''async()=>{const cv=document.createElement('canvas');cv.width=3000;cv.height=2000;const g=cv.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,3000,2000);
          await CPI.ocr.charger();let e=null;const p=CPI.ocr.reconnaitre(cv,{}).catch(x=>e=String(x&&x.message||x));await CPI.ocr.arreter();await Promise.race([p,new Promise(r=>setTimeout(r,3000))]);return e}''')
        pg.wait_for_timeout(300)
        s.check(st == 'annulé' and len(errs) == n0, 'OCR arrêté pendant la préparation de l\'image : « annulé », aucune erreur JS', json.dumps([st, errs[n0:][:2]], ensure_ascii=False))
        s.check(not net, 'aucune requête réseau pendant toute la suite', json.dumps(net[:5]))
        s.check(not [e for e in errs if 'Failed to load resource' not in e], 'aucune erreur JavaScript', json.dumps(errs[:5], ensure_ascii=False))
        b.close()


if __name__ == '__main__':
    s = Suite('t_ocr')
    try:
        t(s)
    except Exception:
        import traceback
        traceback.print_exc(); s.check(False, 'exception')
    sys.exit(0 if s.report() else 1)
