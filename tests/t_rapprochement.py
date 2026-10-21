"""Phase 4, finalisation (demande de Kévin du 20/10/2026) : rapprochement nomenclature ↔ dessin d'un PDF (rapprochement.js),
repères dessinés lus par OCR ciblé (geometrie.blocsTexte → ocr.lireBlocs), liste consolidée, corrections gardées, robustesse.
Plan entièrement fictif : tests/rapprochement_fictifs.py. Scénarios de la demande :
  A dimension partielle (R12 : une seule cote « 600 ») · B repère sans contour (R13) · C vues multiples (R18 plan + coupe)
  D nomenclature page 1, repère page 2 (R13, R19 dessiné en contours de glyphes → OCR) · E mêmes cotes, repères différents (R14, R15)
  F conflit réel (R16 : « 900x500 » pour 800 × 500) · G OCR incertain (module) · H nouvelle analyse : corrections gardées, contour
  disparu non transmis · I grands plans (module : 250 000 sommets, 300 000 traits ; erreur lisible dans la fenêtre)
  J quantités (R17 ×2 sur une page) ; R20 absente du dessin mais créable ; R21 hors nomenclature ; hors connexion."""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
import rapprochement_fictifs as RF


def t(s):
    tmp = tempfile.mkdtemp()
    F = RF.fichiers(tmp)['PDF_7_RAPPROCHEMENT.pdf'][0]
    s.check(open(F, 'rb').read() == open(RF.fichiers(tempfile.mkdtemp())['PDF_7_RAPPROCHEMENT.pdf'][0], 'rb').read(), 'PDF fictif : écriture déterministe')
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500)
        net = []
        pg.context.route(lambda u: not u.startswith('file:') and not u.startswith('blob:') and not u.startswith('data:'), lambda r: (net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = pg.evaluate

        # ---- module : G (repère OCR incertain), confusion de lettres, colonne de tableau non reconnu, cotes d'une autre unité
        g = J('''()=>{const L=[{id:'a',repere:'R12',dims:{type:'rect',a:600,b:400},unite:'mm',quantite:'',page:1},{id:'b',repere:'D5',dims:null,unite:'mm',quantite:'',page:1},
            {id:'c',repere:'P8',dims:{type:'rect',a:400,b:400},unite:'mm',quantite:'',page:1}];
          const T=[{id:'t1',page:2,texte:'R12',x:100,y:100,h:7,w:14,ocr:{brut:'R12',conf:41,corrections:[],mots:[{t:'R12',c:41}]}},{id:'t2',page:2,texte:'600x400',x:100,y:90,h:6,w:20},
            {id:'t3',page:2,texte:'DS',x:300,y:100,h:7,w:12,ocr:{brut:'DS',conf:90,corrections:[],mots:[{t:'DS',c:90}]}},{id:'t4',page:2,texte:'P8',x:500,y:100,h:7,w:12},{id:'t5',page:2,texte:'40x40',x:500,y:91,h:6,w:16}];
          for(let i=0;i<6;i++)T.push({id:'c'+i,page:3,texte:'R1'+(i+2),x:50,y:700-15*i,h:7,w:14});
          const r=CPI.rapprochement.rapprocher(L,T,[],{});return{a:r.lignes.a,b:r.lignes.b,c:r.lignes.c,col:r.colonnes}}''')
        s.check(g['a']['concordance'] == 'probable' and not g['a']['occurrences'][0]['fiable'] and all(x['etat'] == 'non_verifiable' for x in g['a']['dims'].values())
                and 'incertaine' in ' '.join(g['a']['occurrences'][0]['doutes']),
                'G : repère lu par OCR à 41 % : correspondance probable, jamais forte, même avec une cote écrite identique', json.dumps(g['a'], ensure_ascii=False)[:400])
        s.check(g['b']['concordance'] == 'probable' and 'confusion' in ' '.join(g['b']['occurrences'][0]['doutes']), 'repère « DS » rapproché de D5 par confusion S/5 : incertain')
        s.check(g['col'] == 6 and len(g['a']['occurrences']) == 1, 'colonne de 6 repères alignés (tableau non reconnu) : jamais prise pour des localisations')
        s.check(g['c']['concordance'] == 'forte' and 'lue en cm' in ' '.join(g['c']['dims']['a']['preuves']),
                'cote écrite sans unité « 40x40 » près de P8 (400 × 400 mm) : lue en cm, confirmée (pas de faux conflit d\'unité)', json.dumps(g['c']['dims'], ensure_ascii=False)[:300])

        # ---- module : I (grands plans) : pas de dépassement de pile, temps maîtrisé
        big = J('''()=>{const t0=Date.now(),N=250000,P=[];for(let i=0;i<N;i++){const a=2*Math.PI*i/N;P.push([1000+800*Math.cos(a),1000+800*Math.sin(a)])}
          const S=[];for(let i=0;i<300000;i++){const x=(i%600)*5,y=Math.floor(i/600)*5;S.push({id:'s'+i,a:[x,y],b:[x+3,y+0.5]})}
          const B=new Float64Array(4*200000);for(let i=0;i<200000;i++){const x=(i%500)*7,y=Math.floor(i/500)*9;B.set([x,y,x+1.5,y+6],4*i)}
          let err=null,r=null;try{r=CPI.geometrie.detecterPage({page:1,w:3370,h:2384,segments:S,contours:[{id:'k',pts:P,courbes:[]}],petits:B},{fichier:'x',textes:[],cadres:[],zone:null});
            CPI.detecteur.rectSegments(S.slice(0,200000),{eps:0.25,tol:0.01});CPI.geometrie.blocsTexte({petits:B},{})}catch(e){err=String(e)}
          return{err,n:r&&r.candidats.length,ms:Date.now()-t0}}''')
        s.check(big['err'] is None and big['ms'] < 60000, 'I : 250 000 sommets, 300 000 traits, 200 000 petits tracés : aucune erreur de pile, calcul borné', json.dumps(big))

        # ---- interface : ouverture, analyse du dessin (toutes pages, OCR des repères dessinés)
        J('''()=>{el('iCh').value='CHANTIER_DEMO_R';el('iOuv').value='OUVRAGE_R';el('iForme').value='rect';updF();el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='Z99';addP()}''')
        P0 = J('JSON.stringify(P)')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F); pg.wait_for_selector('#dxnT tr[data-n]')
        s.check(J('DXI.NL.map(x=>x.L.repere+":"+x.L.quantite).join()') == 'R12:1,R13:1,R14:1,R15:1,R16:1,R17:2,R18:1,R19:1,R20:1' and not J('DXI.ana'),
                'nomenclature lue (9 lignes, quantités) ; aucun rapprochement avant « Analyser le dessin »')
        pg.click('#dxiTabP'); pg.wait_for_function('el("dxpPg").textContent.includes("/ 2")')
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob', timeout=180000)
        # phase 5 : avec une nomenclature, les formes hors nomenclature sont dans une section repliée : l'ouvrir
        pg.click('#dxrHs')
        m = pg.inner_text('#dxrM')
        s.check('2 page(s)' in m and '1 forte(s), 6 partielle(s), 0 probable(s), 1 conflit(s), 1 non retrouvée(s)' in m, 'bilan du rapprochement : 1 forte, 6 partielles, 1 conflit, 1 non retrouvée', m)
        k = {r: J(f'DXI.NL.findIndex(x=>x.L.repere==="{r}")') for r in ['R12', 'R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R20']}
        A = lambda r: J(f'dxnAS(DXI.NL[{k[r]}].L)')
        NR = lambda r: J(f'DXI.NR[{k[r]}]')
        et = lambda a: {x['libelle']: x['etat'] for x in a['dims'].values()}
        a = A('R12')
        s.check(a['concordance'] == 'partielle' and et(a) == {'600': 'confirmee', '400': 'non_verifiable'} and NR('R12')['cotes'] == '600 × 400' and NR('R12')['geo'] == '',
                'A : R12 et une seule cote 600 → concordance partielle, 600 confirmée, 400 non vérifiable (pas un conflit), cotes 600 × 400 gardées, aucun contour inventé',
                json.dumps([a['concordance'], et(a), NR('R12')['cotes']], ensure_ascii=False))
        a = A('R13')
        s.check(a['concordance'] == 'partielle' and [o['page'] for o in a['occurrences']] == [2] and NR('R13')['geo'] == '' and NR('R13')['cotes'] == 'Ø 250'
                and et(a) == {'Ø250': 'non_verifiable'}, 'B et D : R13 (tableau page 1) localisé page 2 par son repère seul : aucun contour ni cote inventés', json.dumps(a, ensure_ascii=False)[:300])
        a = A('R19')
        o = a['occurrences'][0]
        s.check(o['source'] == 'ocr' and o['page'] == 2 and o['fiable'] and o['conf'] >= 75 and o['box'] and a['statut'] == 'trouvee' and NR('R19')['geo'] != '',
                'D : repère R19 DESSINÉ en traits lu par OCR (texte, page, position, brut, confiance, zone) et rattaché à son contour page 2', json.dumps(o, ensure_ascii=False)[:400])
        a14, a15 = A('R14'), A('R15')
        s.check(a14['concordance'] == 'forte' and et(a14) == {'600': 'confirmee', '400': 'confirmee'} and a15['concordance'] == 'partielle'
                and NR('R14')['geo'] != NR('R15')['geo'] and NR('R14')['geo'] != '' and NR('R15')['geo'] != '',
                'E : R14 et R15 de mêmes cotes : deux entrées, chacune son contour, aucune fusion ; R14 cotée « 600x400 » : forte', json.dumps([a14['concordance'], a15['concordance']]))
        a = A('R16')
        s.check(a['concordance'] == 'conflit' and et(a) == {'800': 'conflit', '500': 'confirmee'} and NR('R16')['cotes'] == '800 × 500',
                'F : cote écrite « 900x500 » pour 800 × 500 : conflit sur 800 seulement, cotes du tableau gardées', json.dumps(et(a)))
        a = A('R18')
        s.check(len(a['occurrences']) == 2 and sorted(o['page'] for o in a['occurrences']) == [1, 2] and len(a['preuves']) == 2 and all(J(f'DXI.lk.has({i})') for i in a['preuves'])
                and 'vues' in a['quantite']['lecture'] and a['quantite']['coherente'] is True,
                'C : R18 en plan et en coupe : une seule entrée, deux preuves graphiques, aucun contour proposé en double', json.dumps(a['quantite'], ensure_ascii=False))
        a = A('R17')
        s.check(a['quantite']['valeur'] == 2 and a['quantite']['localisations'] == 2 and a['quantite']['coherente'] is True and 'occurrences physiques' in a['quantite']['lecture']
                and a['statut'] == 'multiple' and NR('R17')['geo'] == '',
                'J : quantité 2 et deux occurrences sur la page : occurrences physiques possibles, aucun contour choisi d\'office, aucune quantité inventée', json.dumps(a['quantite'], ensure_ascii=False))
        s.check(A('R20')['concordance'] == 'absente' and NR('R20')['cotes'] == '300 × 300', 'R20 non retrouvée sur le dessin : cotes du tableau gardées (ligne créable)')
        hors = J('dxrVis().map(i=>DXI.C[i].annot.repere&&DXI.C[i].annot.repere.texte)')
        s.check(J('DXI.HR.map(x=>x.texte)') == ['R21'] and hors == ['R21'], 'hors nomenclature : repère R21 et sa forme, seuls proposés à part (7 contours rattachés aux lignes)', json.dumps(hors))
        s.check(J('document.querySelectorAll("#dxnT [data-k=conf]:checked").length+document.querySelectorAll("#dxrT [data-k=conf]:checked").length') == 0 and J('JSON.stringify(P)') == P0,
                'rien de coché ni créé d\'office')
        # interface : statut et localisations affichés ; clic → page et repère surlignés
        pg.click('#dxiTabN')
        t16 = pg.inner_text(f'#dxnT tr[data-n="{k["R16"]}"]')
        s.check('conflit à examiner' in t16 and 'contredite' in t16 and 'p. 1 · r16' in t16.lower(), 'ligne R16 : conflit, cote contredite, localisation affichés', t16)
        pg.click(f'#dxnT tr[data-n="{k["R18"]}"] .rp button:has-text("p. 2")'); pg.wait_for_timeout(300)
        s.check(J('DXI.vue') == 'p' and J('DXI.page') == 2 and J('document.querySelectorAll("#dxpO .hl").length') == 1, 'clic sur une localisation : page 2, repère surligné')

        # ---- échelle 1/50 de la page 1 : la mesure renforce R15 ; elle ne lève pas le conflit de R16 (cote écrite) et ne remplace rien
        J('()=>{DXI.page=1;dxpPage()}'); pg.wait_for_timeout(200)
        pg.click('#dxrE button:has-text("1/50")'); pg.wait_for_timeout(200)
        s.check(A('R15')['concordance'] == 'forte' and et(A('R15')) == {'600': 'mesuree', '400': 'mesuree'} and A('R16')['concordance'] == 'conflit' and NR('R15')['cotes'] == '600 × 400',
                'page 1 à l\'échelle : R15 confirmée par la mesure (forte), R16 reste en conflit, cotes du tableau inchangées')

        # ---- H : corrections puis nouvelle analyse
        i21 = J('DXI.C.findIndex(c=>c.annot&&c.annot.repere&&c.annot.repere.texte==="R21")'); id21 = J(f'DXI.C[{i21}].id')
        pg.fill(f'#dxrT tr[data-r="{i21}"] [data-k=cotes]', '310x210'); pg.fill(f'#dxrT tr[data-r="{i21}"] [data-k=h]', '250'); pg.fill(f'#dxrT tr[data-r="{i21}"] [data-k=ref]', 'X21')
        pg.check(f'#dxrT tr[data-r="{i21}"] [data-k=conf]')
        pg.click('#dxiTabN')
        pg.select_option(f'#dxnT tr[data-n="{k["R16"]}"] [data-k=geo]', 'rej')
        pg.select_option(f'#dxnT tr[data-n="{k["R14"]}"] [data-k=geo]', '')
        g15 = NR('R15')['geo']
        pg.select_option(f'#dxnT tr[data-n="{k["R15"]}"] [data-k=geo]', g15)
        pg.fill(f'#dxnT tr[data-n="{k["R12"]}"] [data-k=h]', '200')
        avant = J('JSON.stringify(DXI.C.map(c=>c.id))')
        pg.click('#dxiTabP'); pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob', timeout=180000)
        j21 = J(f'DXI.C.findIndex(c=>c.id==="{id21}")')
        r21 = J(f'DXI.R[{j21}]')
        s.check(j21 >= 0 and r21['cotes'] == '310x210' and r21['h'] == '250' and r21['ref'] == 'X21' and r21['conf'] and J('JSON.stringify(DXI.C.map(c=>c.id))') == avant,
                'H : nouvelle analyse : même contour (même identifiant), cotes, hauteur, référence et coche gardées', json.dumps(r21)[:300])
        s.check(NR('R16')['rej'] and NR('R14')['geo'] == '' and NR('R14')['geoT'] and J(f'DXI.C[{NR("R15")["geo"]}].id') == J(f'DXI.C[{g15}].id') and NR('R12')['h'] == '200',
                'H : rapprochement rejeté (R16), « aucun contour » (R14), contour choisi (R15) et hauteur saisie (R12) gardés')
        # zone qui exclut le contour de R15 : il disparaît, son rattachement n'est transmis à aucun autre contour
        c15 = J(f'DXI.C[{NR("R15")["geo"]}].bbox')
        J('z=>{DXI.page=1;dxpZone(Object.assign({unite:"pt"},z))}', {'page': 1, 'x0': 30, 'y0': 500, 'x1': c15[0] - 20, 'y1': 760})
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob', timeout=180000)
        s.check(NR('R15')['geo'] == '' and 'absent de la nouvelle analyse' in NR('R15')['perdu'], 'H : contour disparu : rattachement retiré et signalé, jamais transféré', NR('R15')['perdu'])
        J('()=>dxpZone(null)'); pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob', timeout=180000)

        # ---- I dans la fenêtre : une erreur pendant l'analyse est lisible, le bouton revient, les résultats précédents restent
        n0 = J('DXI.C.length')
        J('()=>{window._dp=CPI.geometrie.detecterPage;CPI.geometrie.detecterPage=()=>{throw new RangeError("Maximum call stack size exceeded")}}')
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob', timeout=60000)
        s.check('Analyse impossible' in pg.inner_text('#dxrM') and not pg.is_disabled('#dxrGo') and J('DXI.C.length') == n0, 'I : erreur pendant l\'analyse : message lisible, bouton rendu, résultats gardés',
                pg.inner_text('#dxrM'))
        J('()=>{CPI.geometrie.detecterPage=window._dp}')

        # ---- création : cotes du tableau, provenance du rapprochement
        pg.fill('#dxiH', '300'); pg.click('#dxiTabN')
        for r in ('R12', 'R13', 'R16', 'R18', 'R19', 'R20'):
            pg.check(f'#dxnT tr[data-n="{k[r]}"] [data-k=conf]')
        s.check(pg.text_content('#dxiGo') == 'Créer les ouvrages sélectionnés (7)' and J('JSON.stringify(P)') == P0, 'avant confirmation : 6 lignes + R21 prêtes, rien de créé', pg.text_content('#dxiGo'))
        pg.click('#dxiGo')
        B = {p['ref']: p for p in J('P.slice(1)')}
        s.check(sorted(B) == ['R12', 'R13', 'R16', 'R18', 'R19', 'R20', 'X21'] and (B['R16']['L'], B['R16']['l']) == (800, 500) and B['R13']['D'] == 250 and (B['R12']['L'], B['R12']['l'], B['R12']['h']) == (600, 400, 200)
                and (B['X21']['L'], B['X21']['l']) == (310, 210), 'création : cotes du tableau (R16 800 × 500 malgré la cote 900 du dessin), hauteur saisie, aucune cote mesurée imposée',
                json.dumps({r: (p.get('L'), p.get('l'), p.get('D'), p['h']) for r, p in B.items()}))
        o = B['R13']['origineImport']['rapprochement']
        s.check(o['concordance'] == 'partielle' and o['localisations'][0]['page'] == 2 and o['cotes']['D']['etat'] == 'non_verifiable', 'provenance R13 : localisation page 2, Ø non vérifiable', json.dumps(o, ensure_ascii=False)[:400])
        o = B['R19']['origineImport']['rapprochement']['localisations'][0]
        s.check(o['source'] == 'ocr' and o['brut'] and o['confiance'] >= 75 and o['zone']['unite'] == 'pt' and B['R19']['origineImport']['geometrie'],
                'provenance R19 : repère lu par OCR (texte brut, confiance, zone) et contour', json.dumps(o, ensure_ascii=False))
        o = B['R16']['origineImport']['rapprochement']
        s.check(o['rejete'] and o['concordance'] == 'rejete' and o['cotes']['a']['etat'] == 'conflit', 'provenance R16 : rejet de l\'utilisateur et conflit gardés')
        o = B['R18']['origineImport']['rapprochement']
        s.check(len(o['localisations']) == 2 and 'vues' in o['quantite']['lecture'], 'provenance R18 : deux localisations (plan, coupe)')
        s.check(json.dumps(J('P[0]'), sort_keys=True) == json.dumps(json.loads(P0)[0], sort_keys=True), 'ouvrage existant inchangé')
        J('()=>closeModal()')
        net = [u for u in net if 'fonts.g' not in u]
        s.check(not net, 'hors connexion : aucune requête réseau', json.dumps(net[:5]))
        # « Detected N diacritics » : message du moteur Tesseract sur sa sortie d'erreur, pas une erreur de l'appli
        errs = [e for e in errs if 'net::ERR_FAILED' not in e and 'diacritics' not in e]
        s.check(not errs, 'aucune erreur JS', '; '.join(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_rapprochement')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
