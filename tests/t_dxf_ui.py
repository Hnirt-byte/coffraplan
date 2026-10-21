"""Import DXF dans l'appli (fenêtre « Importer un plan DXF », modules/import/fenetre.js), sur l'interface réelle et des
DXF fictifs écrits par ezdxf (CHANTIER_DEMO_A) :
  1. ouverture et lecture ; 2. liste ↔ aperçu (sélection synchronisée, positions du DXF) ; 3. filtre par calque ;
  4. unité absente (R12) → choix demandé ; 5. hauteur absente → saisie (commune, puis individuelle) ;
  6. rien de créé avant « Créer » ; 7. création de plusieurs ouvrages ; 8. plans existants conservés ;
  9. provenance enregistrée, exportée en JSON, rechargée, conservée après réouverture ;
  10. provenance gardée après modification (coll / addP) ; 11. pas de provenance sur un duplicata ;
  12. import annulable (retour à l'état initial) ; 13. hors connexion ; 14. moteur inchangé (débit, feuilles, DXF de plan) ;
  références automatiques du lot sans collision avec le projet ni les références saisies ; rappel des réglages repris ;
  + formulaire et saisie non enregistrée préservés ; bloc cpi-src du HTML = sources du module (assembler.py --check)."""
import json, math, os, subprocess, sys, tempfile
import ezdxf
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE

ROOT = os.path.join(HERE, '..')


def rect(cx, cy, L, l, a=0):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-L / 2, -l / 2), (L / 2, -l / 2), (L / 2, l / 2), (-L / 2, l / 2))]


def fichiers(tmp):
    H = {}
    d = ezdxf.new('R2000'); d.header['$INSUNITS'] = 4; m = d.modelspace()
    for n in ('RESA_A', 'RESA_B', 'COTATION'):
        d.layers.add(n)
    H['r1'] = m.add_lwpolyline(rect(1000, 500, 1200, 600), close=True, dxfattribs={'layer': 'RESA_A'}).dxf.handle
    H['r2'] = m.add_lwpolyline(rect(3000, 1500, 800, 400, 30), close=True, dxfattribs={'layer': 'RESA_A'}).dxf.handle
    H['ca'] = m.add_lwpolyline(rect(2000, 2500, 500, 500, 45), close=True, dxfattribs={'layer': 'RESA_B'}).dxf.handle
    H['ci'] = m.add_circle((500, 2500), 100, dxfattribs={'layer': 'RESA_B'}).dxf.handle
    H['ou'] = m.add_lwpolyline(rect(4000, 500, 300, 300), close=False, dxfattribs={'layer': 'RESA_A'}).dxf.handle
    m.add_line((0, 0), (4500, 0), dxfattribs={'layer': 'COTATION'})
    m.add_text('CHANTIER_DEMO_A', dxfattribs={'layer': 'COTATION'})
    multi = os.path.join(tmp, 'CHANTIER_DEMO_A_niveau1.dxf'); d.saveas(multi)
    d = ezdxf.new('R12'); m = d.modelspace()
    H['p12'] = m.add_polyline2d(rect(2, 1, 1.2, 0.6), close=True, dxfattribs={'layer': 'RESA'}).dxf.handle
    m.add_circle((4, 1), 0.08, dxfattribs={'layer': 'RESA'})
    r12 = os.path.join(tmp, 'CHANTIER_DEMO_A_r12.dxf'); d.saveas(r12)
    bad = os.path.join(tmp, 'pas_un_dxf.dxf'); open(bad, 'w').write('bonjour\n')
    return multi, r12, bad, H


def t(s):
    rc = subprocess.run([sys.executable, os.path.join(ROOT, 'modules', 'import', 'assembler.py'), '--check'], capture_output=True, text=True)
    s.check(rc.returncode == 0, 'HTML : bloc cpi-src identique aux sources modules/import/*.js (assembler.py --check)', rc.stdout + rc.stderr)
    html = open(os.path.join(ROOT, 'app', 'CoffraPlan.html'), encoding='utf-8').read()
    s.check('<script src=' not in html and 'id="cpi-src"' in html, 'HTML autonome : aucun script externe, module intégré')
    tmp = tempfile.mkdtemp()
    multi, r12, bad, H = fichiers(tmp)
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        net = []
        # 13. hors connexion : toute requête réseau est coupée et notée (seules les polices Google sont attendues, facultatives)
        pg.context.route(lambda u: not u.startswith('file:'), lambda r: (net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = lambda x, *a: pg.evaluate(x, *a)
        # plan existant + saisie en cours non enregistrée (formulaire)
        J('''()=>{el('iCh').value='CHANTIER_DEMO_A';el('iOuv').value='OUVRAGE_DEMO';el('iForme').value='rect';updF();
              el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='T1';addP();
              el('dL').value=900;liveCalc()}''')
        P0 = J('JSON.stringify(P)'); F0 = J('formSnap()'); H0 = J('HIS.length'); EI0 = J('EI')
        LS0 = J('localStorage.getItem("resa3")')
        dbg0 = J('(()=>{const c=canon(migr(P[0]));return JSON.stringify(debit(c,null))})()')

        # 1. ouverture et lecture
        pg.click('#bDxi')
        # 20/10/2026 : fenêtre unique DXF + PDF, titre « Importer un plan » (changement voulu, voir CHANGELOG)
        s.check(pg.is_visible('#dxi') and pg.text_content('#dxi .ct').strip() == '📥 Importer un plan' and '.pdf' in pg.get_attribute('#dxiF', 'accept'),
                '1. commande « Importer un plan » : fenêtre ouverte, DXF et PDF acceptés')
        pg.set_input_files('#dxiF', bad)
        pg.wait_for_selector('#dxiZ .hint')
        s.check('Fichier non lu' in pg.inner_text('#dxiZ') and pg.is_disabled('#dxiGo'), '1. fichier non DXF : refus écrit, rien à créer', pg.inner_text('#dxiZ'))
        pg.set_input_files('#dxiF', multi)
        pg.wait_for_selector('#dxiT tr[data-i]')
        n = pg.inner_text('#dxiN')
        s.check('CHANTIER_DEMO_A_niveau1.dxf' in n and 'mm' in n, '1. nom du fichier et unité affichés', n)
        s.check(J('document.querySelectorAll("#dxiT tr[data-i]").length') == 4, '1. 4 réservations potentielles listées')
        st = pg.inner_text('#dxiS')
        s.check('4 réservation(s) potentielle(s)' in st and '3 rectangle(s) ou carré(s), 1 cercle(s)' in st, '1. bilan : nombre de réservations potentielles', st)
        rows = J('''[...document.querySelectorAll('#dxiT tr[data-i]')].map(t=>[...t.cells].map(c=>c.querySelector('select')?c.querySelector('select').value:c.innerText.trim()))''')
        s.check([r[2] for r in rows] == [H['r1'], H['r2'], H['ca'], H['ci']] and [r[3] for r in rows] == ['RESA_A', 'RESA_A', 'RESA_B', 'RESA_B'],
                '1. identifiants (handles DXF) et calques', json.dumps(rows))
        s.check([r[4] for r in rows] == ['rect', 'rect', 'carre', 'circ'], '1. formes par défaut : rect, rect, carre, circ (pas de fond)', json.dumps([r[4] for r in rows]))
        s.check(rows[0][5] == '1200 × 600' and rows[1][5] == '800 × 400 · 30°' and rows[2][5].startswith('500 × 500') and rows[3][5] == 'Ø 200',
                '1. cotes converties en mm, orientation', json.dumps([r[5] for r in rows]))
        fo = J('''[...document.querySelectorAll('#dxiT tr[data-i] select')].map(e=>[...e.options].map(o=>o.value))''')
        s.check(fo == [['rect', 'rect_fond'], ['rect', 'rect_fond'], ['carre', 'carre_fond'], ['circ']], '2. formes compatibles seulement ; fond = choix explicite', json.dumps(fo))
        npt = pg.inner_text('#dxiNP')
        s.check('(3)' in npt and 'polyligne ouverte' in J('document.querySelector("#dxiNP").textContent') and 'LINE' in J('document.querySelector("#dxiNP").textContent'),
                '1. géométries non prises en charge visibles avec la raison', npt)

        # 2. aperçu : positions et orientations du DXF, sélection synchronisée
        sv = J('''(()=>{const S=el('dxiV');return{n:S.querySelectorAll('.c').length,np:S.querySelectorAll('.np').length,vb:S.getAttribute('viewBox'),
              ci:[...S.querySelectorAll('circle.c')].map(c=>[+c.getAttribute('cx'),+c.getAttribute('cy'),+c.getAttribute('r')]),
              r2:S.querySelector('.c[data-i="1"]').getAttribute('points')}})()''')
        s.check(sv['n'] == 4 and sv['np'] == 1, '2. aperçu : 4 réservations dessinées, polyligne ouverte en tirets', json.dumps(sv))
        s.check(sv['ci'] == [[500, -2500, 100]], '2. aperçu : cercle à sa position DXF (Y vers le haut)', json.dumps(sv['ci']))
        p2 = [tuple(map(float, q.split(','))) for q in sv['r2'].split()]
        a2 = math.degrees(math.atan2(-(p2[1][1] - p2[0][1]), p2[1][0] - p2[0][0]))
        s.check(abs(a2 - 30) < 1e-6 and abs(sum(x for x, _ in p2) / 4 - 3000) < 1e-6, '2. aperçu : rectangle tourné de 30° conservé', sv['r2'])
        pg.click('#dxiV .c[data-i="2"]')
        s.check(J('[...document.querySelectorAll("#dxiT tr.on")].map(t=>t.dataset.i)') == ['2'] and J('[...document.querySelectorAll("#dxiV .c.on")].map(t=>t.dataset.i)') == ['2'],
                '2. clic dans l\'aperçu → ligne en surbrillance')
        pg.click('#dxiT tr[data-i="3"] td:nth-child(6)')
        s.check(J('[...document.querySelectorAll("#dxiT tr.on")].map(t=>t.dataset.i)') == ['3'] and J('[...document.querySelectorAll("#dxiV .c.on")].map(t=>t.dataset.i)') == ['3'],
                '2. clic dans la liste → réservation en surbrillance dans l\'aperçu')

        # 3. filtre par calque
        pg.uncheck('#dxi input[data-lay="RESA_B"]')
        s.check(J('document.querySelectorAll("#dxiT tr[data-i]").length') == 2 and J('document.querySelectorAll("#dxiV .c").length') == 2
                and '2 réservation(s) potentielle(s)' in pg.inner_text('#dxiS'), '3. calque décoché : ses réservations quittent la liste, l\'aperçu et le bilan')
        pg.check('#dxi input[data-lay="RESA_B"]')
        s.check(J('document.querySelectorAll("#dxiT tr[data-i]").length') == 4, '3. calque recoché : réservations revenues')

        # 5. hauteur absente
        sts = J('[...document.querySelectorAll("#dxiT .st")].map(e=>e.textContent)')
        s.check(all('hauteur' in x for x in sts), '5. hauteur absente du DXF : saisie demandée sur chaque ligne', json.dumps(sts))
        pg.check('#dxiT tr[data-i="0"] [data-k=conf]')
        s.check(pg.is_disabled('#dxiGo') and '(0)' in pg.inner_text('#dxiGo'), '5. ligne cochée sans hauteur : non créable (0)')
        pg.fill('#dxiH', '300')
        sts = J('[...document.querySelectorAll("#dxiT .st")].map(e=>e.textContent)')
        s.check(all(x.startswith('✓') or x.startswith('⚠') for x in sts), '5. hauteur commune 300 : toutes les lignes prêtes', json.dumps(sts))
        pg.fill('#dxiT tr[data-i="3"] [data-k=h]', '450')
        pg.fill('#dxiT tr[data-i="1"] [data-k=ref]', 't1')
        s.check('déjà utilisée' in pg.inner_text('#dxiT tr[data-i="1"] .st'), '7. référence déjà utilisée dans l\'ouvrage : signalée, ligne non créable', pg.inner_text('#dxiT tr[data-i="1"] .st'))
        pg.fill('#dxiT tr[data-i="1"] [data-k=ref]', 'T9')
        pg.select_option('#dxiT tr[data-i="2"] select', 'carre_fond')
        pg.check('#dxiT tr[data-i="1"] [data-k=conf]'); pg.check('#dxiT tr[data-i="2"] [data-k=conf]')
        s.check(pg.text_content('#dxiGo') == 'Créer les ouvrages sélectionnés (3)' and not pg.is_disabled('#dxiGo'), '7. bouton final : nombre exact de plans (3)', pg.inner_text('#dxiGo'))

        # 6. rien de créé avant confirmation ; formulaire et saisie en cours intacts après analyse
        s.check(J('JSON.stringify(P)') == P0 and J('localStorage.getItem("resa3")') == LS0, '6. avant « Créer » : aucun plan ajouté ni enregistré')
        s.check(J('formSnap()') == F0 and J('EI') == EI0 and J('HIS.length') == H0, '§5 formulaire, saisie non enregistrée et historique intacts pendant l\'import')
        pg.click('#mdBody button:has-text("Fermer")')
        s.check(J('formSnap()') == F0 and J('JSON.stringify(P)') == P0, '§5 fermeture de la fenêtre : formulaire et plans inchangés')
        pg.click('#bDxi')
        s.check(J('document.querySelectorAll("#dxiT tr[data-i] [data-k=conf]:checked").length') == 3 and pg.input_value('#dxiH') == '300',
                '§5 réouverture : préparation de l\'import retrouvée')

        # 7. création
        pg.click('#dxiGo')
        N = J('P.length')
        s.check(N == 4 and not pg.is_visible('#dxi'), '7. 3 ouvrages créés, fenêtre fermée', str(N))
        Pn = J('P.slice(1)')
        s.check([(p['forme'], p.get('L'), p.get('l'), p.get('D'), p['h']) for p in Pn] == [('rect', 1200, 600, None, 300), ('rect', 800, 400, None, 300), ('carre_fond', 500, 500, None, 300)],
                '7. plans : formes, cotes du contour (sans ajout d\'épaisseurs CP), hauteur', json.dumps([(p['forme'], p.get('L'), p.get('l'), p['h']) for p in Pn]))
        s.check([p['ref'] for p in Pn] == ['T02', 'T9', 'T03'] and all(p['ch'] == 'CHANTIER_DEMO_A' and p['ouv'] == 'OUVRAGE_DEMO' for p in Pn),
                '7. références (saisie ou suivante libre), chantier et ouvrage courants', json.dumps([(p['ref'], p['ch'], p['ouv']) for p in Pn]))
        s.check(len({p['uid'] for p in J('P')}) == 4, '7. identifiants de plans distincts')
        # 8. plan existant conservé
        s.check(json.dumps(J('P[0]'), sort_keys=True) == json.dumps(json.loads(P0)[0], sort_keys=True), '8. plan déjà présent inchangé')
        # 9. provenance
        o = Pn[1].get('origineImport') or {}
        s.check(o.get('format') == 'dxf' and o.get('fichier') == 'CHANTIER_DEMO_A_niveau1.dxf' and o.get('id') == H['r2'] and o.get('calque') == 'RESA_A'
                and o.get('unite_source') == 'mm' and abs(o['centre'][0] - 3000) < 1e-6 and abs(o['centre'][1] - 1500) < 1e-6
                and abs(o['dims_source']['angle'] - 30) < 1e-6 and abs(o['dims_source']['L'] - 800) < 1e-6 and 'contenu' not in json.dumps(o),
                '9. provenance : format, fichier, entité, calque, unité, centre, orientation, cotes initiales (sans le contenu du DXF)', json.dumps(o))
        s.check('origineImport' not in J('P[0]'), '9. plan non importé : pas de provenance')
        # 14. moteur inchangé : la provenance n'influe sur aucune sortie
        same = J('''(vk=>P.slice(1).every(p=>{const q=JSON.parse(JSON.stringify(p));delete q.origineImport;const a=canon(migr(p)),b=canon(migr(q));
                  return JSON.stringify(debit(a,null))===JSON.stringify(debit(b,null))&&vk(gen(p))===vk(gen(q))&&JSON.stringify(dxfPlanFile(p))===JSON.stringify(dxfPlanFile(q))}))(h=>h.replace(/ data-(vk|glk)="[^"]*"/g,'').replace(/V3REG\\.get\\(\\d+\\)/g,''))''')
        s.check(same, '14. débit, feuilles (hors clés internes : empreintes data-vk / data-glk, rang V3REG) et DXF de plan identiques avec ou sans provenance')
        s.check(J('(()=>{const c=canon(migr(P[0]));return JSON.stringify(debit(c,null))})()') == dbg0, '14. débit du plan existant inchangé')
        # export JSON (téléchargement) puis rechargement
        with pg.expect_download() as dl:
            pg.click('#bSave')
        exp = json.loads(open(dl.value.path(), encoding='utf-8').read())
        s.check(sorted(exp) == sorted(['app', 'v', 'date', 'plans', 'profils', 'modeles', 'ent']) and exp['v'] == 10
                and exp['plans'][2].get('origineImport', {}).get('id') == H['r2'], '9. export JSON : enveloppe inchangée, provenance dans le plan')
        indice = exp['plans'][2]['origineImport'].get('indice')
        J('t=>loadText(t,"x.json",null)', json.dumps(dict(exp, plans=exp['plans'][:1])))
        pg.click('#dlgB button:has-text("Remplacer")')
        s.check(J('P.length') == 1, 'rechargement : projet sans les plans importés')
        J('t=>loadText(t,"x.json",null)', json.dumps(exp))
        pg.click('#dlgB button:has-text("Remplacer")')
        s.check(J('P.length') == 4 and J('P[2].origineImport&&P[2].origineImport.id') == H['r2'], '9. JSON rechargé : provenance relue')
        # fermeture puis réouverture de l'appli
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        s.check(J('P.length') == 4 and J('P[2].origineImport.calque') == 'RESA_A' and abs(J('P[3].origineImport.dims_source.L') - 500) < 1e-6,
                '9. réouverture de CoffraPlan : provenance conservée (stockage local)')
        # 10. modification du plan (formulaire → coll → addP)
        J('''()=>{shP(2);el('dh').value=350;liveCalc();addP()}''')
        s.check(J('P[2].h') == 350 and J('P[2].origineImport&&P[2].origineImport.id') == H['r2'], '10. plan modifié puis mis à jour : provenance conservée')
        J('()=>{fixAllPlans(1);closeModal()}')
        s.check(J('P[2].origineImport&&P[2].origineImport.id') == H['r2'], '10. corrections automatiques de tous les plans : provenance conservée')
        J('''()=>{shP(2);el('dL').value=850;el('iRef').value='';liveCalc();addP(true)}''')
        s.check(J('P.length') == 5 and 'origineImport' not in J('P[4]'), '11. « Nouveau » depuis un plan importé : plan indépendant, sans provenance')
        J('()=>dupP(1)')
        s.check(J('P.length') == 6 and 'origineImport' not in J('P[2]') and J('P[1].origineImport.id') == H['r1'], '11. duplicata : pas de provenance héritée, original intact')

        # 12. import annulable + 4. unité absente (R12)
        J('()=>{while(P.length>1)P.pop();svP();rnL()}')
        Pa = J('JSON.stringify(P)')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', r12); pg.wait_for_selector('#dxiU')
        n = pg.inner_text('#dxiN')
        s.check('absente' in n and all('unité' in x for x in J('[...document.querySelectorAll("#dxiT .st")].map(e=>e.textContent)')), '4. R12 sans unité : signalée, choix demandé', n)
        s.check(J('[...document.querySelectorAll("#dxiT tr[data-i]")].map(t=>t.cells[5].innerText)') == ['1,2 × 0,6 (unité ?)', 'Ø 0,2 (unité ?)'], '4. cotes en unité du fichier tant qu\'elle n\'est pas choisie')
        pg.select_option('#dxiU', 'm'); pg.fill('#dxiH', '200'); pg.fill('#dxiInd', 'b')
        s.check(J('[...document.querySelectorAll("#dxiT tr[data-i]")].map(t=>t.cells[5].innerText)') == ['1200 × 600', 'Ø 160'], '4. unité m choisie : cotes converties en mm')
        pg.click('#dxi button:has-text("Confirmer les lignes prêtes")')
        pg.click('#dxiGo')
        s.check(J('P.length') == 3 and J('P[1].origineImport.unite_source') is None and J('P[1].origineImport.unite') == 'm' and J('P[1].origineImport.indice') == 'B',
                '4. unité choisie notée dans la provenance (unité du fichier : absente) ; indice du plan source', json.dumps(J('P[1].origineImport')))
        pg.click('#toast button:has-text("Annuler")')
        # phase 7 : le projet est enregistré dans IndexedDB (l'ancien stockage resa3 n'est plus écrit) : relu dans la base
        s.check(J('JSON.stringify(P)') == Pa and J('stoAttendre().then(()=>stoEnregistre()).then(r=>JSON.stringify(r.plans))') == Pa, '12. « Annuler » : retour exact à l\'état d\'avant l\'import')

        # références automatiques du lot : jamais celles saisies dans le lot ni celles du projet (relecture PR #5)
        J('''()=>{el('iCh').value='CHANTIER_DEMO_A';el('iOuv').value='OUVRAGE_REF';el('iForme').value='rect';updF();
              el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='T01';EI=-1;addP()}''')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', multi); pg.wait_for_selector('#dxiT tr[data-i]')
        s.check(pg.input_value('#dxiOuv') == 'OUVRAGE_REF', 'références : ouvrage courant repris (OUVRAGE_REF)')
        pg.fill('#dxiH', '300'); pg.fill('#dxiT tr[data-i="1"] [data-k=ref]', 'T02')
        pg.check('#dxiT tr[data-i="0"] [data-k=conf]'); pg.check('#dxiT tr[data-i="1"] [data-k=conf]')
        rp = pg.text_content('#dxiP')
        s.check('Repris du formulaire' in rp and 'Rectangulaire' in rp and 'mm' in rp and 'options' in rp, 'rappel des réglages repris (CP, montage, options) avant création', rp)
        pg.click('#dxiGo')
        R = J('''P.filter(p=>p.ouv==='OUVRAGE_REF').map(p=>p.ref)''')
        s.check(sorted(R) == ['T01', 'T02', 'T03'] and J('P[P.length-2].ref') == 'T03' and J('P[P.length-1].ref') == 'T02',
                'références : T01 existant, B saisie T02 → A automatique reçoit T03 (pas de doublon T02)', json.dumps(R))
        n0 = J('P.length')
        s.check(J('''(()=>{const L=[{ch:'CHANTIER_DEMO_A',ouv:'OUVRAGE_REF',ref:'T02'}];return dxiRefs(L)})()''') is False and J('P.length') == n0,
                'références : dernière vérification refuse un doublon avec le projet, sans toucher aux plans')
        A = J('''(()=>{const L=[{ch:'CHANTIER_DEMO_A',ouv:'OUVRAGE_REF',ref:''},{ch:'CHANTIER_DEMO_A',ouv:'OUVRAGE_REF',ref:'T04'},{ch:'CHANTIER_DEMO_A',ouv:'OUVRAGE_REF',ref:''}];return [dxiRefs(L),L.map(d=>d.ref)]})()''')
        s.check(A == [True, ['T05', 'T04', 'T06']], 'références : plusieurs automatiques autour d\'une saisie, sans collision', json.dumps(A))
        s.check(not [u for u in net if 'fonts.g' not in u], '13. hors connexion : aucune requête réseau nécessaire', '; '.join(net[:5]))
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', '; '.join(errs[:5]))
        pg.screenshot(path=os.path.join(HERE, 'out', 't_dxf_ui.png'))
        b.close()


if __name__ == '__main__':
    s = Suite('t_dxf_ui')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
