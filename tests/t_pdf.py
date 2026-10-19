"""Import PDF et fenêtre unique « Importer un plan » (modules/import/pdf.js, fenetre.js, PDF.js intégré), sur l'interface
réelle et des PDF entièrement fictifs (tests/pdf_fictifs.py). Demande de Kévin du 19/10/2026 :
  lecture : 1 page avec tableau, multipage, plusieurs tableaux, sans bordures, cellules multilignes, page tournée, en-têtes
  différents, tableau d'aciers écarté, accents et Ø × ± ; PDF vectoriel sans texte et PDF numérisé : rien d'inventé ;
  données : rectangle, carré, Ø explicite, DN seul, SO, cotes manquantes, niveau ≠ hauteur, toutes les lignes gardées ;
  interface : un seul bouton, DXF ou PDF, aperçu et pages, zone, aucune sélection d'office, saisie assistée ;
  création : plusieurs ouvrages, cotes, débit = saisie manuelle, export JSON, rechargement, provenance, annulation, existant intact ;
  compatibilité : assemblage déterministe, PDF.js figé (empreintes), hors connexion (aucune requête réseau), worker en file://."""
import json, os, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
import pdf_fictifs as PF

ROOT = os.path.join(HERE, '..')
LIRE = '''async([b64,n])=>{const b=Uint8Array.from(atob(b64),c=>c.charCodeAt(0)),x=await CPI.pdf.lire(b,n);if(!x.ok)return x;
  const d=x.document,A=CPI.nomenclatures.analyser(d),tid=new Map(d.textes.map(t=>[t.id,t]));CPI.pdf.fermer(x.pdf);
  return{pages:d.pages,nT:d.textes.length,rot:[...new Set(d.textes.map(t=>t.rot))],sig:d.signalements,
    pagesN:A.nomenclatures.map(N=>[...new Set(N.ids.map(i=>tid.get(i).page))]),
    N:A.nomenclatures.map(N=>({id:N.id,page:N.page,titre:N.titre,unite:N.unite,format:N.format,cles:N.colonnes.map(c=>c.cle),q:N.qualite.niveau,
      L:N.lignes.map(L=>({rep:L.repere,cells:L.cellules,dims:L.dims,niv:L.niveau,av:L.a_verifier}))})),
    E:A.ecartes.map(e=>({page:e.page,titre:e.titre,nature:e.nature}))}}'''


def b64(p):
    import base64
    return base64.b64encode(open(p, 'rb').read()).decode()


def t(s):
    rc = subprocess.run([sys.executable, os.path.join(ROOT, 'modules', 'import', 'assembler.py'), '--check'], capture_output=True, text=True)
    s.check(rc.returncode == 0, 'assemblage : blocs cpi-src et PDF.js identiques aux sources (assembler.py --check, empreintes SHA-256)', rc.stdout + rc.stderr)
    html = open(os.path.join(ROOT, 'app', 'CoffraPlan.html'), encoding='utf-8').read()
    s.check('id="pdfjs-src"' in html and 'id="pdfjs-worker-src"' in html and '<script src=' not in html and 'cdn' not in html.lower().split('id="pdfjs-src"')[0][-2000:],
            'HTML autonome : PDF.js intégré, aucun script externe')
    tmp = tempfile.mkdtemp()
    F = {n: p for n, (p, _) in PF.fichiers(tmp).items()}
    s.check(open(F['PDF_1_TABLEAU.pdf'], 'rb').read() == open(PF.fichiers(tempfile.mkdtemp())['PDF_1_TABLEAU.pdf'][0], 'rb').read(), 'PDF fictifs : écriture déterministe')
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        net = []
        pg.context.route(lambda u: not u.startswith('file:') and not u.startswith('blob:') and not u.startswith('data:'), lambda r: (net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = lambda x, *a: pg.evaluate(x, *a)
        R = {n: J(LIRE, [b64(p), n]) for n, p in F.items()}
        s.check(J('(async()=>!!(await CPI.pdf.charger()).GlobalWorkerOptions.workerPort)()'), 'PDF.js : worker lancé depuis le fichier ouvert en file://')

        # ---- lecture
        r = R['PDF_1_TABLEAU.pdf']; N = r['N']
        s.check(len(r['pages']) == 1 and r['pages'][0]['nature'] == 'texte' and r['pages'][0]['textes'] > 50, '1 page avec texte extractible : textes lus', json.dumps(r['pages']))
        s.check(len(N) == 1 and N[0]['titre'] == 'NOMENCLATURE DES RÉSERVATIONS' and N[0]['page'] == 1 and N[0]['format'] == 'pdf' and N[0]['q'] == 'bonne' and N[0]['unite'] == 'mm',
                'tableau à bordures : nomenclature reconnue (titre accentué, page 1, grille lue, mm de l\'en-tête)', json.dumps(N, ensure_ascii=False)[:600])
        s.check([l['cells'] for l in N[0]['L']] == PF.L1, 'toutes les lignes, cellules intactes (accents, Ø, ×, ±, œ ; cellules vides gardées)',
                json.dumps([l['cells'] for l in N[0]['L']], ensure_ascii=False))
        s.check(N[0]['cles'] == ['repere', 'description', 'ouverture', 'reseau', 'niveau', 'lot', 'observations'], 'colonnes reconnues (titre sur deux lignes)', json.dumps(N[0]['cles']))
        s.check(any(e['nature'] == 'aciers' and 'ACIERS' in (e['titre'] or '') for e in r['E']) and not any('Indice' in json.dumps(n) for n in N),
                'tableau d\'aciers écarté, tableau d\'indices non proposé', json.dumps(r['E'], ensure_ascii=False))
        L = {l['rep']: l for l in N[0]['L']}
        s.check(L['R01']['dims'] and (L['R01']['dims']['type'], L['R01']['dims']['a'], L['R01']['dims']['b']) == ('rect', 650, 800), 'rectangle 650 × 800 lu')
        s.check(L['R02']['dims'] and (L['R02']['dims']['a'], L['R02']['dims']['b']) == (400, 400), 'carré « 400 × 400 » lu (signe ×)')
        s.check(L['R03']['dims'] and L['R03']['dims']['type'] == 'circ' and L['R03']['dims']['D'] == 250, 'Ø250 explicite : ouverture circulaire 250 (DN200 du réseau ignoré)')
        s.check(L['R04']['dims'] is None and any('DN' in a for a in L['R04']['av']), 'DN250 seul : aucune cote inventée, signalé', json.dumps(L['R04'], ensure_ascii=False))
        s.check(L['R05']['dims'] is None and any('non renseignée' in a for a in L['R05']['av']), 'SO : donnée manquante')
        s.check(L['R06']['dims'] is None and L['R06']['niv'] == '±0,00', 'cotes vides : manquantes ; niveau ±0,00 gardé en texte')
        s.check(L['R01']['niv'] == '+2,85 / dalle', 'niveau par rapport à la dalle gardé comme position (pas une hauteur)')

        r = R['PDF_2_MULTIPAGE.pdf']; N = r['N']
        s.check([p['nature'] for p in r['pages']] == ['vectoriel', 'texte', 'texte'] and [n['page'] for n in N] == [2, 3, 3],
                'multipage : tableaux trouvés pages 2 et 3, page 1 sans tableau', json.dumps([(n['page'], n['titre']) for n in N], ensure_ascii=False))
        s.check(all(pp == [n['page']] for pp, n in zip(r['pagesN'], N)), 'coordonnées : chaque tableau ne contient que des textes de sa page', json.dumps(r['pagesN']))
        t2 = N[0]
        s.check(t2['titre'] == 'TABLEAU DES TRÉMIES' and [l['cells'] for l in t2['L']] == PF.fichiers(tempfile.mkdtemp())['PDF_2_MULTIPAGE.pdf'][1]['L2'],
                'tableau sans bordures, cellules multilignes : lignes reconstituées', json.dumps([l['cells'] for l in t2['L']], ensure_ascii=False))
        t3 = {n['titre']: n for n in N}
        p3 = t3.get('LISTE DES PERCEMENTS'); p4 = t3.get('RÉSERVATIONS — BÂTIMENT B')
        s.check(p3 and p4 and p3['unite'] == 'cm' and p3['cles'] == ['repere', 'type', 'ouverture', 'niveau', 'observations']
                and [l['rep'] for l in p4['L']] == ['P1', 'P2'] and p4['cles'] == ['repere', 'type', 'ouverture', 'angle'],
                'deux tableaux sur une page, en-têtes différents (N° / Élément / Dimensions (cm) ; Rep. / Type / Section / Angle)', json.dumps(t3, ensure_ascii=False)[:900])
        s.check(p3 and p3['L'][1]['dims']['type'] == 'circ' and p3['L'][1]['dims']['unite'] == 'cm' and p3['L'][0]['niv'] == '+1,20',
                'cotes en cm conservées dans leur unité ; « Hauteur / dalle » lue comme niveau')
        s.check(p4 and p4['L'][0]['dims']['D'] == 160 and p4['L'][0]['dims']['unite'] is None, 'Section Ø 160 sans unité : unité non devinée')

        r = R['PDF_3_TOURNEE.pdf']
        s.check(r['pages'][0]['rotation'] == 90 and r['pages'][0]['w'] == 842 and r['rot'] == [0] and [l['rep'] for l in r['N'][0]['L']] == ['M1'],
                'page tournée (/Rotate 90) : textes remis à l\'horizontale, tableau lu', json.dumps([r['pages'], r['rot']]))
        r = R['PDF_4_GRAPHIQUE.pdf']
        s.check([p['nature'] for p in r['pages']] == ['vectoriel', 'vectoriel'] and r['pages'][1]['chemins'] > 300 and r['N'] == [],
                'PDF vectoriel, nomenclature en tracés : aucune ligne inventée, pages classées « vectoriel »', json.dumps(r['pages']))
        r = R['PDF_5_SCAN.pdf']
        s.check(r['pages'][0]['nature'] == 'image' and r['N'] == [], 'PDF numérisé : classé « image », rien d\'inventé', json.dumps(r['pages']))

        # ---- interface : une seule commande, DXF ou PDF
        lb = J('''[...document.querySelectorAll('[onclick^="dxiOpen"]')].map(e=>e.textContent.trim())''')
        s.check(len(lb) >= 1 and all('Importer un plan' in x and 'DXF' not in x for x in lb) and J('!!document.querySelector(\'[onclick^="impJ"]\')'),
                'une seule commande « Importer un plan » (même fenêtre partout) ; chargement de projet JSON séparé', json.dumps(lb, ensure_ascii=False))
        J('''()=>{el('iCh').value='CHANTIER_DEMO_P';el('iOuv').value='OUVRAGE_P';el('iForme').value='rect';updF();el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='R06';addP()}''')
        P0 = J('JSON.stringify(P)')
        pg.click('#bDxi')
        s.check(pg.text_content('#dxi .ct').strip() == '📥 Importer un plan' and pg.get_attribute('#dxiF', 'accept') == '.dxf,.pdf', 'fenêtre : DXF et PDF proposés, rien d\'autre')
        bad = os.path.join(tmp, 'plan.dwg'); open(bad, 'wb').write(b'AC1032\x00\x00binaire')
        pg.set_input_files('#dxiF', bad); pg.wait_for_selector('#dxiZ .hint')
        s.check('DWG pas encore pris en charge' in pg.inner_text('#dxiZ'), 'DWG : refus clair (exporter en DXF ou PDF)', pg.inner_text('#dxiZ'))
        faux = os.path.join(tmp, 'faux.pdf'); open(faux, 'w').write('pas un pdf')
        pg.set_input_files('#dxiF', faux); pg.wait_for_selector('#dxiZ .hint')
        s.check('%PDF absent' in pg.inner_text('#dxiZ') and pg.is_disabled('#dxiGo'), 'faux PDF : erreur de lecture affichée')
        pg.set_input_files('#dxiF', F['PDF_1_TABLEAU.pdf']); pg.wait_for_selector('#dxnT tr[data-n]')
        n = pg.inner_text('#dxiN')
        s.check('PDF_1_TABLEAU.pdf' in n and '1 page' in n and 'lecture automatique : 6 ligne' in n, 'nom, format, pages et lecture automatique affichés', n)
        s.check(J('document.querySelectorAll("#dxnT tr[data-n]").length') == 6 and J('document.querySelectorAll("#dxnT [data-k=conf]:checked").length') == 0
                and pg.is_disabled('#dxiGo'), 'toutes les lignes affichées, aucune cochée d\'office')
        s.check(pg.is_visible('#dxiTabN') and pg.is_visible('#dxiTabP') and not pg.is_visible('#dxiTabG'), 'onglets Nomenclature et Aperçu ; pas d\'onglet Géométries (aucune géométrie exploitable)')
        fo = J('[...document.querySelectorAll("#dxnT [data-k=forme]")].map(e=>e.value)')
        s.check(fo[:3] == ['rect', 'carre', 'circ'] and fo[3:] == ['', '', ''], 'formes proposées : rect, carré, fourreau ; à choisir quand les cotes manquent', json.dumps(fo))
        s.check(not J('document.querySelector("#dxnT [data-k=geo]")'), 'PDF : aucune géométrie de la page rattachée (échelle inconnue)')
        # aperçu
        pg.click('#dxnT tr[data-n="1"] td:nth-child(10) button')
        pg.wait_for_function('el("dxpPg")&&el("dxpPg").textContent.includes("Page 1 / 1")')
        pg.wait_for_timeout(600)
        enc = J('''(()=>{const c=el('dxpCv'),g=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<g.length;i+=16)if(g[i]<128)n++;return n})()''')
        s.check(pg.is_visible('#dxiPP') and enc > 200, 'aperçu : page dessinée (pixels sombres)', str(enc))
        s.check(J('document.querySelectorAll("#dxpO .tb").length') == 1 and J('document.querySelectorAll("#dxpO .hl").length') == 1, 'aperçu : tableau reconnu encadré, ligne choisie surlignée')
        z0 = pg.inner_text('#dxpZ')
        pg.click('#dxiPP button[aria-label="Zoom avant"]'); pg.wait_for_timeout(300)
        s.check(pg.inner_text('#dxpZ') != z0 and '125' in pg.inner_text('#dxpZ'), 'zoom avant', pg.inner_text('#dxpZ'))
        pg.click('#dxiPP button:has-text("Ajuster")'); pg.wait_for_timeout(300)

        # zone : glisser sur le tableau des aciers → écarté ; sur la nomenclature → relue, mêmes 6 lignes
        def zone(x0, y0, x1, y1):
            pg.click('#dxpZm')
            k, H, bb = J('DXI.k'), J('DXI.doc.pages[DXI.page-1].h'), J('(()=>{const r=el("dxpO").getBoundingClientRect();return[r.left,r.top]})()')
            pg.mouse.move(bb[0] + x0 * k, bb[1] + (H - y1) * k); pg.mouse.down()
            pg.mouse.move(bb[0] + (x0 + x1) / 2 * k, bb[1] + (H - (y0 + y1) / 2) * k, steps=4)
            pg.mouse.move(bb[0] + x1 * k, bb[1] + (H - y0) * k, steps=4); pg.mouse.up()
        zone(30, 140, 320, 225)
        s.check(J('DXI.zone&&DXI.zone.page') == 1 and 'texte(s) dans la zone' in pg.inner_text('#dxpZi'), 'zone choisie à la souris', pg.inner_text('#dxpZi'))
        pg.click('#dxpZa')
        s.check('Aucune nomenclature de réservations reconnue' in pg.inner_text('#dxpZr') and 'aciers' in pg.inner_text('#dxpZr') and J('DXI.NL.length') == 6,
                'zone sur le tableau d\'aciers : écarté, rien ajouté', pg.inner_text('#dxpZr'))
        zone(290, 380, 800, 545)
        pg.click('#dxpZa')
        s.check('6 ligne(s) lue(s)' in pg.inner_text('#dxpZr') and 'N1' in pg.inner_text('#dxpZr') and J('DXI.NL.length') == 6 and J('DXI.NL.every(x=>x.N.id==="Z1"&&x.N.zone)'),
                'zone sur la nomenclature : relue (remplace la lecture automatique), toujours 6 lignes', pg.inner_text('#dxpZr'))
        s.check(J('document.querySelectorAll("#dxnT [data-k=conf]:checked").length') == 0, 'après analyse de zone : aucune ligne cochée')

        # ---- création
        pg.click('#dxiTabN')
        pg.fill('#dxiCh', 'CHANTIER_DEMO_P'); pg.dispatch_event('#dxiCh', 'change'); pg.fill('#dxiOuv', 'OUVRAGE_P'); pg.dispatch_event('#dxiOuv', 'change')
        pg.fill('#dxiInd', 'c'); pg.fill('#dxiH', '300')
        s.check('déjà utilisée' in pg.inner_text('#dxnT tr[data-n="5"] .st') or 'cotes' in pg.inner_text('#dxnT tr[data-n="5"] .st'), 'R06 : non créable (cotes manquantes, référence existante)')
        pg.fill('#dxnT tr[data-n="1"] [data-k=cotes]', '450x450')
        for k in (0, 1, 2):
            pg.check(f'#dxnT tr[data-n="{k}"] [data-k=conf]')
        s.check(pg.text_content('#dxiGo') == 'Créer les ouvrages sélectionnés (3)', 'bouton final : 3 ouvrages', pg.text_content('#dxiGo'))
        s.check(J('JSON.stringify(P)') == P0, 'avant confirmation : aucun ouvrage créé')
        pg.click('#dxiGo')
        Pn = J('P.slice(1)')
        s.check(len(Pn) == 3 and [(p['forme'], p.get('L'), p.get('l'), p.get('D'), p['h'], p['ref']) for p in Pn] ==
                [('rect', 800, 650, None, 300, 'R01'), ('carre', 450, 450, None, 300, 'R02'), ('circ', None, None, 250, 300, 'R03')],
                'ouvrages créés : rect 800 × 650, carré corrigé 450, fourreau Ø250, h 300, repères', json.dumps([(p['forme'], p.get('L'), p.get('l'), p.get('D'), p['h'], p['ref']) for p in Pn]))
        s.check(json.dumps(J('P[0]'), sort_keys=True) == json.dumps(json.loads(P0)[0], sort_keys=True), 'ouvrage existant inchangé')
        # débit identique à une saisie manuelle des mêmes cotes
        man = J('''(()=>{const p=P[1];el('iForme').value='rect';updF();el('iCh').value=p.ch;el('iOuv').value=p.ouv;el('iRef').value=p.ref;el('dL').value=800;el('dl').value=650;el('dh').value=300;liveCalc();
              const m=coll(),dm=debit(canon(migr(m)),null),di=debit(canon(migr(p)),null);return [JSON.stringify(dm)===JSON.stringify(di),JSON.stringify(dm).length]})()''')
        s.check(man[0] and man[1] > 50, 'débit de l\'ouvrage importé = débit de la même boîte saisie à la main', json.dumps(man))
        o = Pn[0]['origineImport']
        s.check(o['format'] == 'pdf' and o['fichier'] == 'PDF_1_TABLEAU.pdf' and o['page'] == 1 and o['nomenclature'] == 'Z1' and o['ligne'] == 'Z1-L01' and o['repere'] == 'R01'
                and o['type'] == 'nomenclature' and o['textes'].get('Ouverture (mm) l×h') == '650x800' and o['dims_source']['a'] == 650 and o['unite'] == 'mm'
                and o['zone']['page'] == 1 and o['zone']['unite'] == 'pt' and o['indice'] == 'C' and Pn[0].get('ind') != 'C' and len(json.dumps(o)) < 3000,
                'provenance PDF : fichier, format, page, tableau, ligne, repère, textes, cotes et unité sources, zone, indice source (sans le PDF)', json.dumps(o, ensure_ascii=False)[:900])
        o2 = Pn[1]['origineImport']
        s.check('cotes' in o2['corrige'] and o2['choix']['cotes'] == '450x450' and o2['dims_source']['a'] == 400, 'provenance : cotes corrigées par l\'utilisateur notées, cotes sources gardées')
        # export, rechargement, modification
        with pg.expect_download() as dl:
            pg.click('#bSave')
        exp = json.loads(open(dl.value.path(), encoding='utf-8').read())
        s.check(exp['v'] == 10 and sum(1 for p in exp['plans'] if (p.get('origineImport') or {}).get('format') == 'pdf') == 3, 'export JSON : enveloppe inchangée, 3 provenances PDF')
        J('t=>loadText(t,"x.json",null)', json.dumps(exp)); pg.click('#dlgB button:has-text("Remplacer")')
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        s.check(J('P.length') == 4 and J('P[1].origineImport.page') == 1 and J('P[3].origineImport.textes["Repère"]') == 'R03', 'JSON rechargé puis appli rouverte : provenance relue')
        J('''()=>{shP(1);el('dh').value=320;liveCalc();addP()}''')
        s.check(J('P[1].h') == 320 and J('P[1].origineImport.ligne') == 'Z1-L01', 'ouvrage modifié : provenance conservée')

        # ---- PDF graphique : saisie assistée
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['PDF_4_GRAPHIQUE.pdf'])
        pg.wait_for_function('el("dxpPg")&&el("dxpPg").textContent.includes("Page 1 / 2")')
        n = pg.inner_text('#dxiN')
        s.check('aucune nomenclature lisible automatiquement : saisie assistée' in n and pg.is_visible('#dxiPP'), 'PDF graphique : rapport « saisie assistée », aperçu ouvert', n)
        s.check('Aucune nomenclature de réservations exploitable' in J('el("dxiPN").textContent') and J('DXI.NL.length') == 0, 'aucune ligne proposée (rien d\'inventé)')
        pg.click('#dxiPP button[aria-label="Page suivante"]')
        pg.wait_for_function('el("dxpPg").textContent.includes("Page 2 / 2")'); pg.wait_for_timeout(500)
        s.check('vectoriel' in pg.inner_text('#dxpI'), 'navigation : page 2, nature affichée', pg.inner_text('#dxpI'))
        zone(50, 330, 560, 520)
        pg.click('#dxpZa')
        s.check('aucun texte extractible' in pg.inner_text('#dxpZr') and J('DXI.NL.length') == 0, 'zone sur le tableau en tracés : aucun texte, rien ajouté', pg.inner_text('#dxpZr'))
        for rep, des, ct in (('R01', 'Trémie gaine palière', '650x800'), ('R03', 'Fourreau EU', 'Ø250'), ('R09', 'Ligne à retirer', '')):
            pg.fill('#dxpR', rep); pg.fill('#dxpD', des); pg.fill('#dxpK', ct); pg.click('#dxiPP button:has-text("Ajouter la ligne")')
        s.check(J('DXI.NL.length') == 3 and J('DXI.NL.every(x=>x.N.saisie&&x.N.page===2)'), 'saisie assistée : 3 lignes ajoutées, rattachées à la page 2')
        pg.click('#dxiTabN')
        s.check(J('document.querySelectorAll("#dxnT [data-k=conf]:checked").length') == 0 and 'cotes non saisies' in pg.inner_text('#dxnT tr[data-n="2"]'),
                'lignes saisies non cochées ; cotes absentes signalées')
        pg.click('#dxnT tr[data-n="2"] button[aria-label="Retirer la ligne saisie"]')
        s.check(J('DXI.NL.length') == 2, 'ligne saisie retirée')
        pg.fill('#dxiH', '250'); pg.fill('#dxiInd', 'D')
        pg.check('#dxnT tr[data-n="0"] [data-k=conf]'); pg.check('#dxnT tr[data-n="1"] [data-k=conf]')
        s.check('déjà utilisée' in pg.inner_text('#dxnT tr[data-n="0"] .st'), 'référence R01 déjà utilisée dans l\'ouvrage : refusée, rien écrasé')
        s.check('déjà utilisée' in pg.inner_text('#dxnT tr[data-n="1"] .st'), 'R03 déjà créé par l\'import précédent : refusé aussi')
        pg.fill('#dxnT tr[data-n="0"] [data-k=ref]', 'R11'); pg.fill('#dxnT tr[data-n="1"] [data-k=ref]', 'R13')
        P3 = J('JSON.stringify(P)')
        pg.click('#dxiGo')
        Ps = J('P.slice(4)')
        s.check([(p['forme'], p.get('L'), p.get('l'), p.get('D'), p['h'], p['ref']) for p in Ps] == [('rect', 800, 650, None, 250, 'R11'), ('circ', None, None, 250, 250, 'R13')],
                'ouvrages créés depuis la saisie assistée', json.dumps([(p['forme'], p.get('L'), p.get('D'), p['ref']) for p in Ps]))
        s.check(J('JSON.stringify(P.slice(0,4))') == P3, 'ouvrages existants (dont R01 et R03) non modifiés')
        o = Ps[0]['origineImport'] if Ps else {}
        s.check(o.get('type') == 'saisie' and o.get('page') == 2 and o.get('format') == 'pdf' and o.get('textes', {}).get('Repère') == 'R01' and o.get('zone', {}).get('page') == 2
                and o.get('indice') == 'D' and 'ref' in o.get('corrige', []), 'provenance d\'une ligne saisie : type, page, zone, valeurs tapées, indice', json.dumps(o, ensure_ascii=False)[:700])
        # annulation immédiate
        pg.click('#toast button:has-text("Annuler")') if pg.is_visible('#toast button:has-text("Annuler")') else None
        s.check(J('P.length') == 4, 'annulation : ouvrages du dernier import retirés', str(J('P.length')))

        # ---- DXF toujours lu par la même fenêtre
        import ezdxf
        d = ezdxf.new('R2000'); d.header['$INSUNITS'] = 4; d.modelspace().add_circle((0, 0), 100)
        dx = os.path.join(tmp, 'demo.dxf'); d.saveas(dx)
        pg.click('#bDxi'); pg.set_input_files('#dxiF', dx); pg.wait_for_selector('#dxiT tr[data-i]')
        s.check('DXF AC1015' in pg.inner_text('#dxiN') and J('DXI.fmt') == 'dxf' and not J('el("dxiPP")'), 'DXF par la même fenêtre : lecture inchangée, pas d\'aperçu PDF')
        pg.click('#mdBody button:has-text("Fermer")')
        net = [u for u in net if 'fonts.g' not in u]   # polices Google de l'interface : facultatives, présentes avant l'import
        s.check(not net, 'hors connexion : aucune requête réseau pendant la lecture, l\'aperçu et la création', json.dumps(net[:5]))
        errs = [e for e in errs if 'net::ERR_FAILED' not in e]
        s.check(not errs, 'aucune erreur JS', '; '.join(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_pdf')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
