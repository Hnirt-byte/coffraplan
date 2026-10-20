"""Phase 4 : repérage des réservations sur le dessin (PDF vectoriel : geometrie.js, fenêtre dxr* ; DXF : rectangles en 4 LINE),
sur l'interface réelle et des plans entièrement fictifs (tests/detection_fictifs.py). Demande de Kévin du 20/10/2026 :
  détection : rectangles « re », traits séparés, côté en morceaux, cercles en Bézier, doublons, page tournée ; parasites écartés
  avec leur raison (cadre de feuille, cartouche subdivisé, quadrillage, nomenclature) ; repères et cotes écrites rattachés ;
  DXF : rectangle en 4 LINE (+ diagonales), côté en 2 LINE, doublon de polyligne, quadrillage, cadre subdivisé, 2 calques ;
  cotes : jamais en mm sans échelle ; échelle lue sur la page ou calibration par 2 points ; cote écrite avec unité sans échelle ;
  interface : contours cliquables ↔ lignes, états, corrections, rien de coché ni créé d'office ;
  nomenclature : rapprochement par repère, choix entre plusieurs contours, pas de doublon ; création par l'adaptateur,
  provenance complète ; DXF par la même fenêtre ; hors connexion."""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
import detection_fictifs as DF

DET = '''async([b64])=>{const b=Uint8Array.from(atob(b64),c=>c.charCodeAt(0)),x=await CPI.pdf.lire(b,'d.pdf'),d=x.document,NA=CPI.nomenclatures.analyser(d),out=[];
  for(const n of [1,2]){const g=await CPI.pdf.chemins(x.pdf,n),cad=NA.nomenclatures.concat(NA.ecartes).filter(N=>N.page===n&&N.cadre).map(N=>N.cadre);
    const r=CPI.geometrie.detecterPage(g,{fichier:'d.pdf',textes:d.textes.filter(t=>t.page===n),cadres:cad,zone:null});
    out.push(r.candidats.map(c=>({id:c.id,type:c.type,st:c.statut,dims:c.dims,rem:c.remarques,rep:c.annot.repere?c.annot.repere.texte:null,cot:c.annot.cotes?c.annot.cotes.texte:null,page:c.source.page,unite:c.unite})))}
  CPI.pdf.fermer(x.pdf);return{rot:d.pages[1].rotation,C:out}}'''


def t(s):
    import base64
    tmp = tempfile.mkdtemp()
    F = {n: p for n, (p, _) in DF.fichiers(tmp).items()}
    s.check(open(F['PDF_6_DETECTION.pdf'], 'rb').read() == open(DF.fichiers(tempfile.mkdtemp())['PDF_6_DETECTION.pdf'][0], 'rb').read(), 'PDF fictif : écriture déterministe')
    K = DF.K
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        net = []
        pg.context.route(lambda u: not u.startswith('file:') and not u.startswith('blob:') and not u.startswith('data:'), lambda r: (net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = lambda x, *a: pg.evaluate(x, *a)

        # ---- détection PDF (module seul)
        r = J(DET, [base64.b64encode(open(F['PDF_6_DETECTION.pdf'], 'rb').read()).decode()])
        C1, C2 = r['C']
        ok = [c for c in C1 if c['st'] == 'a_confirmer']; np_ = [c for c in C1 if c['st'] != 'a_confirmer']
        mm = lambda c: sorted([round(c['dims']['D'] * K)] if c['type'] == 'circ' else [round(c['dims']['L'] * K), round(c['dims']['l'] * K)])
        got = sorted((c['type'], tuple(mm(c)), c['rep'] or '') for c in ok)
        exp = sorted([('rect', (600, 1200), 'R10'), ('rect', (400, 400), 'R11'), ('circ', (250,), 'R12'), ('rect', (300, 500), ''), ('rect', (300, 500), 'R13'),
                      ('rect', (500, 900), ''), ('rect', (200, 300), 'R20'), ('circ', (160,), 'F1')])
        s.check(got == exp, 'PDF : 8 réservations possibles (re + diagonales, 4 traits dont un côté en 2 morceaux, cercles en Bézier, cercle tracé 2 fois compté 1 fois), repères rattachés',
                json.dumps(got))
        s.check(all(c['unite'] == 'pt' and c['page'] == 1 for c in C1), 'dimensions gardées en points PDF (aucune conversion sans échelle), page notée')
        raisons = ' | '.join(' '.join(c['rem']) for c in np_)
        s.check(len(np_) == 9 and 'cadre de feuille' in raisons and 'subdivisé' in raisons and raisons.count('quadrillage') == 6 and 'dans un tableau' in raisons,
                'parasites écartés avec leur raison : cadre de feuille, cartouche subdivisé, 6 cellules de quadrillage, nomenclature', raisons)
        r20 = next(c for c in ok if c['rep'] == 'R20')
        s.check(r20['cot'] == '300x200 mm' and next(c for c in ok if c['rep'] == 'R10')['rem'] == ['diagonales dessinées (réservation traversante probable)'],
                'cote écrite rattachée au contour voisin ; diagonales signalées')
        s.check(r['rot'] == 90 and sorted((c['type'], tuple(mm(c)), c['rep'] or '') for c in C2) == [('circ', (200,), ''), ('rect', (400, 800), 'R30')]
                and next(c for c in C2 if c['type'] == 'rect')['dims']['angle'] == 0,
                'page tournée (/Rotate 90) : contours dans le sens de l\'affichage (grand côté horizontal), repère lu', json.dumps(C2)[:400])

        # ---- détection DXF : rectangles en LINE
        txt = open(F['DETECTION_LIGNES.dxf'], encoding='cp1252').read()
        d = J('''t=>{const lu=CPI.lecteur.lirePlan({format:'dxf',nom:'d.dxf',contenu:t}),C=CPI.detecteur.detecter(lu.document).candidats;
          return C.map(c=>({id:c.id,type:c.type,st:c.statut,cal:c.source.calque,sid:c.source.id,dims:c.dims,rem:c.remarques,g:c.geometrie.type}))}''', txt)
        dok = [c for c in d if c['st'] == 'a_confirmer']
        rl = [c for c in dok if 'LINE indépendantes' in ' '.join(c['rem'])]
        s.check(sorted((c['dims']['L'], c['dims']['l'], len(c['sid'].split('+'))) for c in rl) == [(400, 400, 5), (1200, 600, 6)] and all(c['cal'] == 'RESA' and c['g'] == 'polyligne' for c in rl),
                'DXF : rectangle de 4 LINE + diagonales et carré dont un côté est en 2 LINE reconstitués (identifiants des LINE gardés)', json.dumps(rl)[:500])
        s.check(sorted(c['type'] for c in dok) == ['circ', 'rect', 'rect', 'rect'] and any('double la polyligne' in ' '.join(c['rem']) for c in d),
                'DXF : 4 LINE qui doublent une polyligne non reproposées ; quadrillage, cadre subdivisé, grille de nomenclature et rectangle sur 2 calques non proposés',
                json.dumps([(c['type'], c['cal'], c['dims']) for c in dok]))

        # ---- interface PDF
        J('''()=>{el('iCh').value='CHANTIER_DEMO_D';el('iOuv').value='OUVRAGE_D';el('iForme').value='rect';updF();el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='R99';addP()}''')
        P0 = J('JSON.stringify(P)')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['PDF_6_DETECTION.pdf']); pg.wait_for_selector('#dxnT tr[data-n]')
        s.check(J('DXI.NL.length') == 4 and J('DXI.C.length') == 0 and not J('document.querySelector("#dxnT [data-k=geo]")'), 'ouverture : nomenclature lue, aucun repérage tant qu\'il n\'est pas demandé')
        pg.click('#dxiTabP'); pg.wait_for_function('el("dxpPg").textContent.includes("Page 1 / 2")'); pg.wait_for_timeout(300)
        s.check('non définie' in pg.inner_text('#dxrE') and 'ÉCHELLE 1/50' in pg.inner_text('#dxrE').upper(), 'page sans échelle ; échelle 1/50 écrite sur la page proposée (pas appliquée d\'office)', pg.inner_text('#dxrE'))
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob&&!!el("dxrT")')
        # phase 5 : avec une nomenclature, les formes hors nomenclature sont dans une section repliée : l'ouvrir
        pg.click('#dxrHs')
        # finalisation phase 4 (demande de Kévin du 20/10/2026) : « Analyser le dessin » traite toutes les pages (8 formes page 1, 2 page 2)
        s.check('2 page(s) : 10 forme(s) possible(s)' in pg.inner_text('#dxrM') and 'sans échelle' in pg.inner_text('#dxrM'), 'bouton « Analyser le dessin » : bilan des 2 pages', pg.inner_text('#dxrM'))
        s.check(J('document.querySelectorAll("#dxpO .rs").length') == 8, 'aperçu : 8 contours superposés')
        s.check(J('document.querySelectorAll("#dxrT [data-k=conf]:checked").length') == 0 and pg.is_disabled('#dxiGo'), 'rien de coché, rien à créer')
        idx = lambda cid: J(f'DXI.C.findIndex(c=>c.id==="{cid}")')
        rid = lambda rep: J(f'DXI.C.findIndex(c=>c.annot&&c.annot.repere&&c.annot.repere.texte==="{rep}")')
        i8 = J('DXI.C.findIndex(c=>c.statut==="a_confirmer"&&c.type==="rect"&&!c.annot.repere&&c.dims.L>40)')
        s.check(J(f'DXI.R[{i8}].cotes') == '' and 'cotes' in pg.inner_text(f'#dxrT tr[data-r="{i8}"] .st'), 'contour sans texte, page sans échelle : cotes impossibles, « à compléter »',
                pg.inner_text(f'#dxrT tr[data-r="{i8}"] .st'))
        i20 = rid('R20')
        s.check(J(f'DXI.R[{i20}].cotes') == '300x200' and 'cote écrite' in pg.inner_text(f'#dxrT tr[data-r="{i20}"] .og') and J(f'DXI.R[{i20}].ref') == 'R20',
                'cote écrite avec unité : reprise sans échelle, origine affichée ; référence = repère', pg.inner_text(f'#dxrT tr[data-r="{i20}"]'))
        # clic sur un contour → ligne ; clic sur une ligne → contour
        pg.click(f'#dxpO .rs[data-r="{i20}"]')
        s.check(J('DXI.rsel') == i20 and J(f'el("dxrT").querySelector("tr[data-r=\\"{i20}\\"]").classList.contains("on")'), 'clic sur un contour : sa ligne est sélectionnée')
        pg.click(f'#dxrT tr[data-r="{i8}"] td:nth-child(2)')
        s.check(J(f'document.querySelector("#dxpO .rs.on").dataset.r') == str(i8), 'clic sur une ligne : son contour est mis en évidence')
        # échelle lue sur la page
        pg.click('#dxrE button:has-text("1/50")'); pg.wait_for_timeout(200)
        s.check('1/50 lue sur la page' in pg.inner_text('#dxrE') and J(f'DXI.R[{i8}].cotes') == '900x500', 'échelle 1/50 choisie : cotes proposées en mm (900 × 500)', J(f'DXI.R[{i8}].cotes'))
        # nomenclature : R10, R11, R12 trouvés (repère + cotes) et rattachés ; R13 : deux contours possibles, au choix
        lk = J('[...DXI.lk].map(i=>DXI.C[i].annot.repere&&DXI.C[i].annot.repere.texte).sort()')
        s.check(lk == ['R10', 'R11', 'R12'] and all(J(f'!document.querySelector("#dxrT tr[data-r=\\"{rid(x)}\\"]")') for x in lk),
                'nomenclature : R10, R11, R12 rattachés à leur contour (repère voisin, cotes identiques) et retirés de la liste repérée', json.dumps(lk))
        k13 = J('DXI.NL.findIndex(x=>x.L.repere==="R13")')
        o13 = J(f'dxnAS(DXI.NL[{k13}].L)')
        s.check(o13['statut'] == 'multiple' and len(o13['options']) == 2 and J(f'DXI.NR[{k13}].geo') == '', 'R13 : deux contours possibles, aucun choisi à la place de l\'utilisateur', json.dumps(o13)[:300])
        # doublon : même repère coché des deux côtés → refusé
        pg.fill('#dxiCh', 'CHANTIER_DEMO_D'); pg.dispatch_event('#dxiCh', 'change'); pg.fill('#dxiOuv', 'OUVRAGE_D'); pg.dispatch_event('#dxiOuv', 'change')
        pg.fill('#dxiH', '300'); pg.fill('#dxiInd', 'b')
        i13 = rid('R13')
        pg.check(f'#dxrT tr[data-r="{i13}"] [data-k=conf]'); pg.click('#dxiTabN'); pg.check(f'#dxnT tr[data-n="{k13}"] [data-k=conf]')
        s.check('double' in pg.inner_text(f'#dxnT tr[data-n="{k13}"] .st') and J(f'DXI.R[{i13}].x') is None, 'même réservation cochée dans la nomenclature et sur le dessin : refusée (doublon)',
                pg.inner_text(f'#dxnT tr[data-n="{k13}"] .st'))
        pg.select_option(f'#dxnT tr[data-n="{k13}"] [data-k=geo]', str(i13))
        s.check(J(f'DXI.lk.has({i13})') and not J(f'document.querySelector("#dxrT tr[data-r=\\"{i13}\\"]")') and 'prêt' in pg.inner_text(f'#dxnT tr[data-n="{k13}"] .st'),
                'contour choisi pour R13 : rattaché à la ligne, retiré de la liste repérée, plus de doublon')
        for k in range(4):
            if k != k13:
                pg.check(f'#dxnT tr[data-n="{k}"] [data-k=conf]')
        pg.click('#dxiTabP'); pg.wait_for_timeout(200)
        # corrections : cotes, forme, référence ; puis cochage
        pg.fill(f'#dxrT tr[data-r="{i8}"] [data-k=cotes]', '900x450'); pg.fill(f'#dxrT tr[data-r="{i8}"] [data-k=ref]', 'T1')
        iF1 = rid('F1')
        pg.fill(f'#dxrT tr[data-r="{iF1}"] [data-k=h]', '250')
        for i in (i8, i20, iF1):
            pg.check(f'#dxrT tr[data-r="{i}"] [data-k=conf]')
        st = {i: pg.inner_text(f'#dxrT tr[data-r="{i}"] .st') for i in (i8, i20, iF1)}
        s.check('repérée' in st[i8] and 'confirmer' in st[iF1] and 'repérée' in st[i20], 'états : cote écrite ou saisie = repérée ; mesure à l\'échelle = à confirmer', json.dumps(st, ensure_ascii=False))
        s.check(pg.text_content('#dxiGo') == 'Créer les ouvrages sélectionnés (7)' and J('JSON.stringify(P)') == P0, 'avant confirmation : 7 prêts, aucun ouvrage créé', pg.text_content('#dxiGo'))
        # page 2 tournée : calibration par 2 points
        pg.click('#dxiPP button[aria-label="Page suivante"]'); pg.wait_for_function('el("dxpPg").textContent.includes("Page 2 / 2")'); pg.wait_for_timeout(300)
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob')
        i30 = rid('R30')
        s.check(J(f'DXI.R[{i30}].cotes') == '' and J('DXI.C.length') == 19, 'page 2 repérée sans effacer la page 1 ; sans échelle : pas de cotes')
        pg.click('#dxrCal')
        k, H, bb = J('DXI.k'), J('DXI.doc.pages[1].h'), J('(()=>{const r=el("dxpO").getBoundingClientRect();return[r.left,r.top]})()')
        w, h = DF.pt(800), DF.pt(400)
        for x, y in ((300 - w / 2 + 0.6, 300 - h / 2 + 0.4), (300 + w / 2 - 0.5, 300 - h / 2 - 0.3)):   # clics près des sommets : accrochés
            pg.mouse.click(bb[0] + x * k, bb[1] + (H - y) * k)
        pg.fill('#dlgB input', '800'); pg.click('#dlgB button:has-text("Appliquer")'); pg.wait_for_timeout(200)
        e = J('DXI.cal[2]')
        s.check(e and e['mode'] == 'points' and abs(e['k'] - K) < 0.01 and J(f'DXI.R[{i30}].cotes') == '800x400' and 'calibr' not in pg.inner_text('#dxrE').lower()[:0],
                'calibration : 2 points accrochés aux sommets + 800 mm → échelle de la page 2, cotes 800 × 400', json.dumps(e))
        ic = J('DXI.C.findIndex(c=>c.source.page===2&&c.type==="circ")')
        s.check(J(f'DXI.R[{ic}].cotes') == 'Ø200' and J(f'DXI.R[{i8}].cotes') == '900x450', 'cercle de la page 2 : Ø200 ; échelle propre à chaque page, corrections gardées')
        pg.fill(f'#dxrT tr[data-r="{i30}"] [data-k=ref]', 'R30B'); pg.check(f'#dxrT tr[data-r="{i30}"] [data-k=conf]')
        pg.click('#dxiGo')
        Pn = J('P.slice(1)')
        got = [(p['forme'], p.get('L'), p.get('l'), p.get('D'), p['h'], p['ref']) for p in Pn]
        s.check(got == [('rect', 1200, 600, None, 300, 'R10'), ('carre', 400, 400, None, 300, 'R11'), ('circ', None, None, 250, 300, 'R12'), ('rect', 500, 300, None, 300, 'R13'),
                        ('rect', 300, 200, None, 300, 'R20'), ('rect', 900, 450, None, 300, 'T1'), ('circ', None, None, 160, 250, 'F1'), ('rect', 800, 400, None, 300, 'R30B')],
                'création : 4 lignes de nomenclature + 4 réservations du dessin, aucune en double', json.dumps(got))
        s.check(json.dumps(J('P[0]'), sort_keys=True) == json.dumps(json.loads(P0)[0], sort_keys=True), 'ouvrage existant inchangé')
        B = {p['ref']: p for p in Pn}
        o = B['T1']['origineImport']
        s.check(o['type'] == 'detection' and o['format'] == 'pdf' and o['page'] == 1 and o['unite_source'] == 'pt' and o['echelle']['mode'] == 'echelle' and o['echelle']['echelle'] == 50
                and o['cotes'] == {'origine': 'saisie', 'proposees': '900x500', 'retenues': '900x450'} and o['corrige'] == ['cotes', 'ref'] and o['id'] and o['boite']['unite'] == 'pt'
                and o['indice'] == 'B' and len(json.dumps(o)) < 3000,
                'provenance : page, contour, boîte en pt, échelle, cotes proposées / retenues, corrections, indice', json.dumps(o, ensure_ascii=False)[:900])
        o = B['R20']['origineImport']
        s.check(o['cotes']['origine'] == 'annotation' and o['annotation'] == '300x200 mm' and o['repere'] == 'R20' and o['corrige'] == [], 'provenance : cote écrite et repère repris')
        o = Pn[7]['origineImport']
        s.check(o['echelle']['mode'] == 'points' and o['echelle']['distance_mm'] == 800 and o['page'] == 2, 'provenance : calibration par 2 points (points, distances)', json.dumps(o['echelle']))
        o = Pn[3]['origineImport']
        s.check(o['type'] == 'nomenclature' and o['geometrie'] and o['geometrie']['statut'] == 'choisie' and o['geometrie']['unite'] == 'pt', 'ligne R13 : contour choisi noté dans la provenance')
        man = J('''(()=>{const p=P.find(q=>q.ref==='T1');el('iForme').value='rect';updF();el('iCh').value=p.ch;el('iOuv').value=p.ouv;el('iRef').value=p.ref;el('dL').value=900;el('dl').value=450;el('dh').value=300;liveCalc();
              return JSON.stringify(debit(canon(migr(coll())),null))===JSON.stringify(debit(canon(migr(p)),null))})()''')
        s.check(man, 'débit d\'un ouvrage repéré = débit de la même boîte saisie à la main')

        # ---- DXF par la même fenêtre : rectangle en LINE rattaché à la nomenclature R5
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['DETECTION_LIGNES.dxf']); pg.wait_for_selector('#dxnT tr[data-n]')
        a = J('dxnAS(DXI.NL[0].L)')
        s.check(J('DXI.NL[0].L.repere') == 'R5' and a['statut'] == 'trouvee' and 'LINE' in ' '.join(J(f'DXI.C[{a["options"][0]["c"]}].remarques')) and J('DXI.lk.size') == 1,
                'DXF : ligne R5 rattachée au rectangle de LINE (repère voisin, cotes identiques), retiré des géométries', json.dumps(a)[:300])
        pg.click('#dxiTabG')
        s.check(J('document.querySelectorAll("#dxiT tr[data-i]").length') == 3 and J('document.querySelectorAll("#dxiT [data-k=conf]:checked").length') == 0,
                'DXF : géométries restantes (carré de LINE, polyligne, cercle), rien de coché')
        pg.click('#mdBody button:has-text("Fermer")')
        net = [u for u in net if 'fonts.g' not in u]
        s.check(not net, 'hors connexion : aucune requête réseau', json.dumps(net[:5]))
        errs = [e for e in errs if 'net::ERR_FAILED' not in e]
        s.check(not errs, 'aucune erreur JS', '; '.join(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_detection')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
