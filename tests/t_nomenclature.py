"""Nomenclatures de réservations d'un DXF (modules/import/nomenclatures.js, lecteur dxf.js, fenêtre fenetre.js), sur des DXF
entièrement fictifs écrits par ezdxf (tests/dxf_nomenclatures.py). Scénarios de la demande (19/10/2026) :
  1. tableau dans l'espace Objet ; 2. dans une présentation ; 3. TEXT + LINE ; 4. MTEXT ; 5. plusieurs tableaux ;
  6. 7, 12 et 23 lignes ; 7. repères de formats différents ; 8. colonnes facultatives, cellules vides ; 9. ouverture ≠ DN réseau ;
  10. altimétrie ≠ hauteur à coffrer ; 11. géométrie retrouvée ; 12. absente ou ambiguë ; 13. plusieurs représentations d'une
  réservation ; 14. pas de tableau : ancien import intact ; 15. aucun filtrage (type, lot, fournisseur) ; 16. rien de créé sans
  confirmation ; 17. ouvrages et provenance enregistrés, rechargés, modifiés ; 18. moteur inchangé.
  + tableau d'aciers écarté, blocs et ACAD_TABLE, présentations, textes AutoCAD (%%c, MTEXT), lecture des cotes."""
import json, os, sys, tempfile
import ezdxf
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
import dxf_nomenclatures as DN

MOD = os.path.join(HERE, '..', 'modules', 'import')
JS = [os.path.join(MOD, f) for f in ('lecteur.js', 'dxf.js', 'detecteur.js', 'nomenclatures.js')]


def texte(p):
    b = open(p, 'rb').read()
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return b.decode('cp1252')


def ancien(tmp):
    d = ezdxf.new('R2000'); d.header['$INSUNITS'] = 4; m = d.modelspace()
    m.add_lwpolyline(DN.rect(1000, 500, 1200, 600), close=True, dxfattribs={'layer': 'RESA_A'})
    m.add_circle((500, 2500), 100, dxfattribs={'layer': 'RESA_B'})
    m.add_text('CHANTIER_DEMO_A', dxfattribs={'layer': 'COTATION'})
    p = os.path.join(tmp, 'CHANTIER_DEMO_A_ancien.dxf'); d.saveas(p)
    return p


ANALYSE = '''([n,txt])=>{const lu=CPI.lecteur.lirePlan({format:'dxf',nom:n,contenu:txt});if(!lu.ok)return {lu};const d=lu.document,C=CPI.detecteur.detecter(d).candidats,A=CPI.nomenclatures.analyser(d);
  const S=CPI.nomenclatures.associer(A.nomenclatures,C,d,{uniteDessin:d.unite,exclus:A.ecartes.flatMap(e=>e.ids)});
  return {doc:{presentations:d.presentations,nT:d.textes.length,ent:d.entites.map(e=>[e.id,e.type,e.espace,e.presentation])},C:C.map(c=>({id:c.id,h:c.source.id,st:c.statut,rq:c.remarques})),A,S}}'''


def t(s):
    tmp = tempfile.mkdtemp()
    F = DN.fichiers(tmp)
    old = ancien(tmp)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('about:blank')
        for p in JS:
            pg.add_script_tag(path=p)
        R = {n: pg.evaluate(ANALYSE, [n, texte(p)]) for n, (p, _) in F.items()}
        R['ancien'] = pg.evaluate(ANALYSE, ['ancien.dxf', texte(old)])
        K = pg.evaluate('''()=>{const c=CPI.nomenclatures.cotes;return ['650x800','0,65 x 0,80 m','65 x 80 x 20','Ø 12,5','%%c','DN250','SO','S.O.','à définir','/','','250','Trémie'].map(v=>[v,c(v,'mm')])
          .concat([['d250 saisie',c('d250','mm',true)],['d250 tableau',c('d250','mm')]])}''')
        # 14 contours près d'un même repère : le seul de mêmes cotes est le plus éloigné
        O = pg.evaluate('''()=>{const r=(x,L,l)=>({statut:'a_confirmer',type:'rect',id:'g'+x,dims:{L,l},geometrie:{type:'polyligne',espace:'objet',points:[[x,50],[x+l,50],[x+l,50+L],[x,50+L]]}});
          const C=[...Array(13)].map((_,i)=>r(20*i,100,50)).concat([r(300,800,650)]),L={id:'X-L01',repere:'Z9',dims:{type:'rect',a:650,b:800,unite:'mm'}};
          return CPI.nomenclatures.associer([{id:'X',unite:'mm',ids:[],lignes:[L]}],C,{textes:[{id:'t',texte:'Z9',espace:'objet',x:0,y:0,h:100}]},{uniteDessin:'mm'})['X-L01'].options.map(o=>[o.id,o.cotes])}''')
        s.check(not errs, 'page vide : modules sans erreur JS', '; '.join(errs))
        b.close()

    A23 = R['NOMENC_23_PRESENTATION.dxf']['A']; N = A23['nomenclatures']
    s.check(len(N) == 1 and N[0]['espace'] == 'papier' and N[0]['presentation'] == 'NOMENCLATURE' and N[0]['titre'] == 'NOMENCLATURE DES RÉSERVATIONS',
            '2. nomenclature trouvée dans la présentation « NOMENCLATURE » (non active, section BLOCKS), titre lu', json.dumps([(x['espace'], x['presentation'], x['titre']) for x in N]))
    L = N[0]['lignes']
    s.check(len(L) == 23 and [l['repere'] for l in L] == [r[0] for r in DN.L23], '6. 23 lignes, repères dans l\'ordre du tableau', json.dumps([l['repere'] for l in L]))
    exp = [[c.replace('%%c', 'Ø') for c in r] for r in DN.L23]
    s.check([l['cellules'] for l in L] == exp, '3. TEXT + LINE : toutes les cellules conservées telles quelles (vides comprises, %%c lu Ø)',
            json.dumps([(l['cellules'], e) for l, e in zip(L, exp) if l['cellules'] != e][:2], ensure_ascii=False))
    s.check([c['cle'] for c in N[0]['colonnes']] == ['repere', 'description', 'type', 'ouverture', 'reseau', 'niveau', 'angle', 'lot', 'observations']
            and N[0]['colonnes'][3]['titre'] == 'Ouverture\n(mm) l×h' and N[0]['unite'] == 'mm', '3. colonnes reconnues (titres sur deux lignes), unité mm de l\'en-tête',
            json.dumps(N[0]['colonnes'], ensure_ascii=False))
    s.check(N[0]['qualite']['niveau'] == 'bonne' and 'grille' in N[0]['qualite']['motifs'][0], '3. qualité de lecture : bonne (grille de traits)', json.dumps(N[0]['qualite'], ensure_ascii=False))
    s.check(N[0]['calques'] == ['NOMENC'] and all(l['ids'] for l in L), '5. calque des textes et identifiants DXF des cellules gardés par ligne')
    s.check({'R+1-D02', 'RES-08', 'D-12', 'd13', 'D 14'} <= {l['repere'] for l in L}, '7. repères de formats différents gardés tels quels')
    by = {l['repere']: l for l in L}
    s.check({by['D11']['type'], by['D06']['type'], by['D15']['type']} == {'Insert', 'Membrane'} and by['D11']['observations'] == 'Pas de coffrage nécessaire'
            and len({l['lot'] for l in L}) >= 10, '15. aucun filtrage : inserts, membrane, « pas de coffrage », tous les lots présents')
    s.check(by['R+1-D02']['dims'] == {'type': 'circ', 'D': 300, 'unite': 'mm', 'texte': 'Ø300', 'colonne': 'Ouverture\n(mm) l×h'} and by['R+1-D02']['reseau'] == 'DN250',
            '9. ouverture Ø300 retenue, DN250 du réseau gardé à part', json.dumps(by['R+1-D02']['dims'], ensure_ascii=False))
    s.check(by['D07']['dims'] is None and any('DN100' in a and 'ne donne pas' in a for a in by['D07']['a_verifier']), '9. DN seul : aucune cote inventée, ouverture à saisir',
            json.dumps(by['D07']['a_verifier'], ensure_ascii=False))
    s.check(by['D01']['dims'] == {'type': 'rect', 'a': 650, 'b': 800, 'unite': 'mm', 'texte': '650x800', 'colonne': 'Ouverture\n(mm) l×h'}, '9. 650x800 → ouverture rectangulaire 650 × 800 mm')
    s.check(by['R+1-D02']['niveau'] == '560 cm / dalle' and by['D01']['niveau'] == '+5,60 m' and all('h' not in (l['dims'] or {}) for l in L),
            '10. niveau gardé en texte (position), jamais en hauteur de coffrage', json.dumps(by['D01']['dims']))
    s.check(by['R+1-D02']['angle'] == '45°', '10. angle de position gardé en texte')
    for r, why in (('D06', 'non renseignée'), ('D11', 'non renseignée'), ('D15', 'non renseignée')):
        s.check(by[r]['dims'] is None and any(why in a for a in by[r]['a_verifier']), f'8. {r} (« à définir », SO, /) : cote manquante, pas inventée', json.dumps(by[r]['a_verifier'], ensure_ascii=False))
    s.check(by['D-12']['ouverture'] == 'Ø90' and by['D-12']['dims']['D'] == 90, 'texte AutoCAD %%c90 lu Ø90')
    E = A23['ecartes']
    s.check(len(E) == 1 and E[0]['nature'] == 'aciers' and 'aciers' in E[0]['raison'] and E[0]['nLignes'] == 3,
            'tableau d\'aciers (repères, Ø, nombre…) : identifié par son en-tête et écarté, signalé', json.dumps(E, ensure_ascii=False)[:300])
    C23 = R['NOMENC_23_PRESENTATION.dxf']['C']
    fr = [c for c in C23 if any('présentation' in r for r in c['rq'])]
    s.check(len(fr) == 1 and fr[0]['st'] == 'non_pris_en_charge', 'présentation active : rectangle du cadre non proposé comme réservation', json.dumps(fr, ensure_ascii=False))
    s.check(R['NOMENC_23_PRESENTATION.dxf']['doc']['presentations'] == ['Layout1', 'NOMENCLATURE'], 'noms des présentations lus (objets LAYOUT)')

    # association
    S, G = R['NOMENC_23_PRESENTATION.dxf']['S'], F['NOMENC_23_PRESENTATION.dxf'][1]
    st = lambda r: S[by[r]['id']]
    hid = lambda o: next(c['h'] for c in C23 if c['id'] == o['id'])
    for r, via in (('D01', 'TEXT'), ('R+1-D02', 'MULTILEADER (pointe de flèche)'), ('D03', 'TEXT'), ('RES-08', 'attribut de bloc')):
        x = st(r)
        s.check(x['statut'] == 'trouvee' and len(x['options']) == 1 and hid(x['options'][0]) == G[r], f'11. {r} : géométrie trouvée et cohérente (repère {via})', json.dumps(x, ensure_ascii=False)[:300])
    x = st('D04')
    s.check(x['statut'] == 'probable' and x['options'][0]['cotes'] == 'diff' and 'différentes' in x['note'], '12. D04 : repère proche mais cotes différentes → probable, à vérifier', json.dumps(x, ensure_ascii=False)[:300])
    x = st('D05')
    s.check(x['statut'] == 'multiple' and sorted(hid(o) for o in x['options']) == sorted([G['D05a'], G['D05b']]) and len(x['reperes']) == 2,
            '13. D05 en plan et en coupe : 2 possibilités proposées, aucune choisie d\'office', json.dumps(x, ensure_ascii=False)[:300])
    x = st('D09')
    s.check(x['statut'] == 'multiple' and len(x['options']) == 3 and all(o['via'] == 'cotes' for o in x['options']), '12. D09 sans repère dessiné, 3 contours de mêmes cotes : à choisir', json.dumps(x)[:300])
    x = st('D23')
    s.check(x['statut'] == 'probable' and x['options'][0]['via'] == 'cotes', '12. D23 : une seule géométrie de mêmes cotes, repère absent → probable seulement')
    x = st('D10')
    s.check(x['statut'] == 'absente' and 'aucun contour' in x['note'], '12. D10 : repère loin de tout contour → non retrouvée, ligne gardée')
    s.check(st('D06')['statut'] == 'absente' and sum(1 for l in L if S[l['id']]['statut'] == 'absente') >= 10, '12. lignes sans géométrie toujours présentes')
    s.check(len(O) == 14 and O[0] == ['g300', 'ok'] and all(c == 'diff' for _, c in O[1:]), '13. repère entouré de contours : la géométrie de mêmes cotes est proposée en premier', json.dumps(O[:3]))
    s.check(all(not o.get('id', '').startswith('#') for x in S.values() for o in x['options']) and all(hid(o) not in [c['h'] for c in fr] for x in S.values() for o in x['options']),
            'rapprochement : géométries de l\'espace Objet seulement')

    # MTEXT, espace Objet, sans grille, cm
    A7 = R['NOMENC_7_OBJET_MTEXT.dxf']['A']; N7 = A7['nomenclatures']
    s.check(len(N7) == 1 and N7[0]['espace'] == 'objet' and len(N7[0]['lignes']) == 7 and [l['repere'] for l in N7[0]['lignes']] == [f'T{i}' for i in range(1, 8)],
            '1. 4. 6. tableau MTEXT dans l\'espace Objet : 7 lignes', json.dumps([l['repere'] for l in N7[0]['lignes']] if N7 else None))
    L7 = {l['repere']: l for l in N7[0]['lignes']}
    s.check(L7['T2']['description'] == 'Fourreau\nchauffage' and L7['T6']['description'] == 'Réservation\nboîtier\nincendie', '4. cellules sur plusieurs lignes (MTEXT \\P) gardées dans leur ligne')
    s.check(L7['T3']['description'] == '' and L7['T7']['ouverture'] == '' and L7['T7']['observations'] == 'Dimensions à venir', '8. cellules vides et lignes incomplètes gardées')
    s.check(N7[0]['unite'] == 'cm' and L7['T1']['dims']['a'] == 65 and L7['T2']['dims'] == {'type': 'circ', 'D': 20, 'unite': 'cm', 'texte': 'Ø 20', 'colonne': 'Ouverture\n(cm)'},
            '4. unité cm de l\'en-tête, %%c en MTEXT lu Ø', json.dumps(L7['T2']['dims'], ensure_ascii=False))
    s.check('position des textes' in N7[0]['qualite']['motifs'][0] and N7[0]['qualite']['niveau'] != 'bonne', 'qualité : sans grille → à vérifier')
    x = R['NOMENC_7_OBJET_MTEXT.dxf']['S'][L7['T1']['id']]
    s.check(x['statut'] == 'trouvee' and x['options'][0]['cotes'] == 'ok', '11. T1 65 × 80 cm ↔ contour 650 × 800 mm : unités converties, trouvée')

    # plusieurs tableaux (présentation active, ENTITIES code 67)
    AP = R['NOMENC_PLUSIEURS.dxf']['A']
    s.check([(x['presentation'], len(x['lignes'])) for x in AP['nomenclatures']] == [('Layout1', 12), ('Layout1', 7)] and [e['nature'] for e in AP['ecartes']] == ['aciers'],
            '5. 6. deux nomenclatures (12 et 7 lignes) et un tableau d\'aciers écarté dans la présentation active',
            json.dumps([(x['presentation'], len(x['lignes'])) for x in AP['nomenclatures']]))
    NB = AP['nomenclatures'][1]
    s.check([l['repere'] for l in NB['lignes']] == [f'B-{i}' for i in range(1, 8)] and NB['titre'] == 'LISTE DES FOURREAUX', '5. en-tête en bas, lignes au-dessus, sans grille : ordre et titre')
    s.check(NB['lignes'][0]['dims']['D'] == 75 and any('à confirmer' in a for a in NB['lignes'][0]['a_verifier']), '9. colonne « Ø (mm) » : diamètre proposé, à confirmer')
    s.check([l['lot'] for l in NB['lignes']] == ['Lot ' + c for c in 'ABCDEFG'], '15. colonne Entreprise gardée, aucune ligne écartée')

    # blocs et ACAD_TABLE
    AB = R['NOMENC_BLOC_TABLE.dxf']['A']
    s.check([[l['repere'] for l in x['lignes']] for x in AB['nomenclatures']] == [['P1', 'P2', 'P3'], ['Q1', 'Q2']], 'tableau dans un bloc inséré (échelle 10) et ACAD_TABLE (bloc de rendu) lus',
            json.dumps([[l['repere'] for l in x['lignes']] for x in AB['nomenclatures']]))
    s.check(AB['nomenclatures'][1]['unite'] is None and any('unité' in a for a in AB['nomenclatures'][1]['lignes'][0]['a_verifier']), 'ACAD_TABLE sans unité : unité des cotes demandée, pas devinée')

    # 14. sans tableau
    s.check(R['ancien']['A']['nomenclatures'] == [] and R['ancien']['A']['ecartes'] == [] and [c['st'] for c in R['ancien']['C']] == ['a_confirmer', 'a_confirmer', 'non_pris_en_charge'],
            '14. DXF sans nomenclature : aucune nomenclature, détection géométrique inchangée')
    k = dict((v, r) for v, r in K)
    s.check(k['650x800']['etat'] == 'rect' and k['0,65 x 0,80 m'] == {'etat': 'rect', 'a': 0.65, 'b': 0.8, 'unite': 'm'} and k['65 x 80 x 20'].get('c') == 20
            and k['Ø 12,5'] == {'etat': 'circ', 'D': 12.5, 'unite': 'mm'} and k['DN250'] == {'etat': 'dn', 'D': 250} and k['250']['etat'] == 'seul'
            and all(k[v]['etat'] == 'manquant' for v in ('SO', 'S.O.', 'à définir', '/')) and k['']['etat'] == 'vide' and k['Trémie']['etat'] == 'illisible'
            and k['d250 saisie']['etat'] == 'circ' and k['d250 tableau']['etat'] != 'circ', 'lecture des cotes : l×h, Ø, DN, SO / à définir / « / », unité écrite', json.dumps(K, ensure_ascii=False)[:600])

    # ===== interface réelle =====
    p23 = F['NOMENC_23_PRESENTATION.dxf'][0]
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500, height=1100)
        J = lambda x, *a: pg.evaluate(x, *a)
        J('''()=>{el('iCh').value='CHANTIER_DEMO_N';el('iOuv').value='OUVRAGE_DEMO';el('iForme').value='rect';updF();
              el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='X1';addP()}''')
        P0 = J('JSON.stringify(P)'); LS0 = J('localStorage.getItem("resa3")')
        dbg0 = J('(()=>{const c=canon(migr(P[0]));return JSON.stringify(debit(c,null))})()')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', old); pg.wait_for_selector('#dxiT tr[data-i]')
        s.check(not pg.query_selector('#dxiTabN') and pg.is_visible('#dxiPG') and J('document.querySelectorAll("#dxiT tr[data-i]").length') == 2,
                '14. fenêtre, DXF sans nomenclature : pas d\'onglet, vue géométrique habituelle')
        pg.set_input_files('#dxiF', p23); pg.wait_for_selector('#dxnT tr[data-n]')
        s.check(pg.is_visible('#dxiPN') and not pg.is_visible('#dxiPG') and 'on' in pg.get_attribute('#dxiTabN', 'class'), 'vue « Nomenclature des réservations » affichée par défaut')
        s.check(J('document.querySelectorAll("#dxnT tr[data-n]").length') == 23 and '23 ligne(s) de nomenclature' in pg.inner_text('#dxnS'), '6. 23 lignes affichées, total indiqué')
        info = pg.inner_text('#dxiPN .dxn-i')
        s.check('présentation « NOMENCLATURE »' in info and 'NOMENCLATURE DES RÉSERVATIONS' in info and 'lecture : bonne' in info and 'Ouverture (mm) l×h → ouverture' in info,
                'tableau d\'origine, présentation, qualité et colonnes reconnues affichés', info)
        s.check('aciers' in J('el("dxiE").textContent'), 'tableau d\'aciers signalé comme non retenu')
        s.check(J('document.querySelectorAll("#dxnT [data-k=conf]:checked").length') == 0 and pg.is_disabled('#dxiGo'), '16. aucune ligne présélectionnée, rien à créer')
        row = lambda r: f'#dxnT tr[data-n="{[l["repere"] for l in L].index(r)}"]'
        s.check(pg.input_value(row('D01') + ' [data-k=cotes]') == '650 × 800' and pg.input_value(row('D06') + ' [data-k=cotes]') == ''
                and pg.input_value(row('D07') + ' [data-k=cotes]') == '', 'cotes proposées depuis le tableau ; « à définir » et DN seul : vides')
        ci = lambda h: str(J('h=>DXI.C.findIndex(c=>c.source.id===h)', h))
        s.check(pg.input_value(row('D01') + ' [data-k=geo]') == ci(G['D01']) and 'trouvée' in pg.inner_text(row('D01') + ' .gs'), '11. D01 : géométrie trouvée rattachée, statut affiché')
        s.check(pg.input_value(row('D05') + ' [data-k=geo]') == '' and J(f'document.querySelectorAll(\'{row("D05")} [data-k=geo] option\').length') == 3
                and 'plusieurs' in pg.inner_text(row('D05') + ' .gs'), '13. D05 : 2 possibilités proposées, aucune choisie')
        s.check('hauteur à coffrer' in pg.inner_text(row('D01') + ' .st') and 'niveau' not in pg.input_value(row('D01') + ' [data-k=h]'),
                '10. niveau +5,60 m ne remplit pas la hauteur : hauteur à coffrer demandée')
        # géométries rattachées retirées de l'autre vue
        pg.click('#dxiTabG')
        nG = J('document.querySelectorAll("#dxiT tr[data-i]").length')
        s.check(nG == 7 and pg.is_visible('#dxiPG') and 'rattachée' in pg.inner_text('#dxiS'), 'vue « Géométries » : les 4 géométries trouvées n\'y sont plus (pas de doublon)', str(nG))
        pg.click('#dxiTabN')
        pg.select_option(row('D05') + ' [data-k=geo]', ci(G['D05b']))
        pg.click('#dxiTabG'); s.check(J('document.querySelectorAll("#dxiT tr[data-i]").length') == 6, '13. géométrie choisie pour D05 : retirée de la vue géométrique'); pg.click('#dxiTabN')
        pg.click(row('D04') + ' td:nth-child(2)')
        s.check(J('document.querySelectorAll("#dxnV .g.on").length') == 1 and J('document.querySelectorAll("#dxnV .rp").length') >= 7, 'schéma : propositions de la ligne sélectionnée et repères du dessin')
        # tout sélectionner / tout décocher
        pg.click('#dxiPN button:has-text("Tout sélectionner")')
        s.check(J('document.querySelectorAll("#dxnT [data-k=conf]:checked").length') == 23 and pg.is_disabled('#dxiGo'), 'tout sélectionner : 23 cochées, aucune prête sans hauteur')
        pg.fill('#dxiH', '250')
        nr = J('dxnReady().length')
        s.check(0 < nr < 23 and f'({nr})' in pg.inner_text('#dxiGo'), 'hauteur commune : seules les lignes complètes sont créables', str(nr))
        pg.click('#dxiPN button:has-text("Tout décocher")')
        s.check(pg.is_disabled('#dxiGo') and J('JSON.stringify(P)') == P0 and J('localStorage.getItem("resa3")') == LS0, '16. tout décoché : rien créé, rien enregistré')
        # préparation : sélection libre, corrections
        for r in ('D01', 'R+1-D02', 'D04', 'D05', 'D07', 'D11', 'RES-08'):
            pg.check(row(r) + ' [data-k=conf]')
        s.check('à compléter' in pg.inner_text(row('D07') + ' .st') and 'cotes' in pg.inner_text(row('D07') + ' .st'), 'D07 : cotes à saisir')
        pg.fill(row('D07') + ' [data-k=cotes]', 'd120')
        pg.fill(row('D11') + ' [data-k=cotes]', '200x100')
        pg.select_option(row('D11') + ' [data-k=forme]', 'rect_fond')
        pg.fill(row('D04') + ' [data-k=cotes]', '450 x 200')
        pg.fill(row('RES-08') + ' [data-k=ref]', '')
        pg.fill(row('R+1-D02') + ' [data-k=h]', '300')
        pg.fill('#dxiInd', 'c')
        s.check(pg.input_value(row('RES-08') + ' [data-k=forme]') == 'carre' and pg.input_value(row('D07') + ' [data-k=forme]') == 'circ', 'forme proposée selon les cotes (carré, circulaire)')
        s.check(pg.text_content('#dxiGo') == 'Créer les ouvrages sélectionnés (7)', '7 lignes sélectionnées et prêtes', pg.text_content('#dxiGo'))
        s.check(J('JSON.stringify(P)') == P0, '16. avant « Créer » : aucun plan ajouté')
        pg.click('#dxiGo')
        Pn = J('P.slice(1)')
        s.check(len(Pn) == 7 and not pg.is_visible('#dxi'), '7 ouvrages créés après confirmation', str(len(Pn)))
        s.check(json.dumps(J('P[0]'), sort_keys=True) == json.dumps(json.loads(P0)[0], sort_keys=True), 'plan déjà présent inchangé')
        pr = {p['origineImport']['repere']: p for p in Pn}
        s.check([(pr[r]['forme'], pr[r].get('L'), pr[r].get('l'), pr[r].get('D'), pr[r]['h']) for r in ('D01', 'R+1-D02', 'D07', 'D11')]
                == [('rect', 800, 650, None, 250), ('circ', None, None, 300, 300), ('circ', None, None, 120, 250), ('rect_fond', 200, 100, None, 250)],
                'plans : formes, cotes du tableau ou corrigées, hauteur commune ou individuelle', json.dumps([(p['forme'], p.get('L'), p.get('D'), p['h']) for p in Pn]))
        s.check(pr['D01']['ref'] == 'D01' and pr['R+1-D02']['ref'] == 'R+1-D02' and pr['RES-08']['ref'] not in ('', 'RES-08') and all(p['ch'] == 'CHANTIER_DEMO_N' for p in Pn),
                'références : repères du tableau gardés, automatique si vidée', json.dumps([p['ref'] for p in Pn]))
        o = pr['D01']['origineImport']
        s.check(o['type'] == 'nomenclature' and o['espace'] == 'papier' and o['presentation'] == 'NOMENCLATURE' and o['nomenclature'] == 'N1' and o['ligne'] == 'N1-L01'
                and o['rang'] == 1 and o['textes'].get('Ouverture (mm) l×h') == '650x800' and o['textes'].get('Niveau') == '+5,60 m' and o['fichier'] == 'NOMENC_23_PRESENTATION.dxf'
                and o['format'] == 'dxf' and o['indice'] == 'C' and o['geometrie']['id'] == G['D01'] and o['geometrie']['statut'] == 'trouvee' and o['corrige'] == [] and o['unite'] == 'mm',
                '17. provenance : fichier, format, présentation, nomenclature, ligne, repère, textes sources, géométrie, indice', json.dumps(o, ensure_ascii=False)[:700])
        o = pr['D04']['origineImport']
        s.check(o['corrige'] == ['cotes'] and o['choix']['cotes'] == '450 x 200' and o['dims_source']['a'] == 400 and o['geometrie'] is None,
                '17. correction des cotes notée (choix et valeur du tableau) ; géométrie « probable » non rattachée d\'office', json.dumps(o, ensure_ascii=False)[:500])
        o = pr['D05']['origineImport']
        s.check(o['geometrie']['id'] == G['D05b'] and o['geometrie']['statut'] == 'choisie', '13. 17. géométrie choisie par l\'utilisateur notée « choisie »')
        o = pr['RES-08']['origineImport']
        s.check('ref' in o['corrige'] and o['choix']['ref'] == '' and o['repere'] == 'RES-08', '17. référence CoffraPlan automatique notée, repère d\'origine gardé')
        s.check(pr['D07']['origineImport']['dims_source'] is None and pr['D07']['origineImport']['textes'].get('Diamètre réseau') == 'DN100', '17. D07 : DN gardé en texte source, cotes saisies')
        s.check(all(p['origineImport'].get('indice') == 'C' and 'ind' in p and p['ind'] != 'C' for p in Pn), 'indice du document source distinct de l\'indice du plan CoffraPlan',
                json.dumps([(p.get('ind'), p['origineImport'].get('indice')) for p in Pn]))
        # 18. moteur inchangé
        same = J('''(vk=>P.slice(1).every(p=>{const q=JSON.parse(JSON.stringify(p));delete q.origineImport;const a=canon(migr(p)),b=canon(migr(q));
                  return JSON.stringify(debit(a,null))===JSON.stringify(debit(b,null))&&vk(gen(p))===vk(gen(q))&&JSON.stringify(dxfPlanFile(p))===JSON.stringify(dxfPlanFile(q))}))(h=>h.replace(/ data-(vk|glk)="[^"]*"/g,'').replace(/V3REG\\.get\\(\\d+\\)/g,''))''')
        s.check(same and J('(()=>{const c=canon(migr(P[0]));return JSON.stringify(debit(c,null))})()') == dbg0, '18. débit, feuilles et DXF identiques avec ou sans provenance ; plan existant inchangé')
        # 17. enregistrement, rechargement, modification
        with pg.expect_download() as dl:
            pg.click('#bSave')
        exp = json.loads(open(dl.value.path(), encoding='utf-8').read())
        s.check(exp['v'] == 10 and sum(1 for p in exp['plans'] if (p.get('origineImport') or {}).get('type') == 'nomenclature') == 7, '17. export JSON : enveloppe inchangée, 7 provenances')
        J('t=>loadText(t,"x.json",null)', json.dumps(dict(exp, plans=exp['plans'][:1]))); pg.click('#dlgB button:has-text("Remplacer")')
        J('t=>loadText(t,"x.json",null)', json.dumps(exp)); pg.click('#dlgB button:has-text("Remplacer")')
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        i1 = J('P.findIndex(p=>p.origineImport&&p.origineImport.repere==="D01")')
        s.check(J('P.length') == 8 and i1 > 0 and J(f'P[{i1}].origineImport.textes["Ouverture (mm) l×h"]') == '650x800', '17. rechargé puis appli rouverte : provenance relue')
        J(f'''()=>{{shP({i1});el('dh').value=320;liveCalc();addP()}}''')
        s.check(J(f'P[{i1}].h') == 320 and J(f'P[{i1}].origineImport.ligne') == 'N1-L01', '17. ouvrage modifié : provenance conservée')
        J(f'()=>dupP({i1})')
        s.check('origineImport' not in J(f'P[{i1 + 1}]'), '17. duplicata : sans provenance')

        # autres tableaux dans la fenêtre : cm de l'en-tête, unité absente à choisir
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['NOMENC_7_OBJET_MTEXT.dxf'][0]); pg.wait_for_selector('#dxnT tr[data-n]')
        s.check(pg.input_value('#dxnT tr[data-n="0"] [data-k=cotes]') == '650 × 800' and pg.input_value('#dxnT tr[data-n="1"] [data-k=cotes]') == 'Ø 200',
                '4. cotes en cm du tableau converties en mm dans la fenêtre')
        pg.set_input_files('#dxiF', F['NOMENC_BLOC_TABLE.dxf'][0]); pg.wait_for_selector('#dxnT tr[data-n]')
        pg.fill('#dxiH', '200')
        s.check('unité des cotes du tableau' in pg.inner_text('#dxnT tr[data-n="3"] .st') and pg.input_value('#dxnT tr[data-n="3"] [data-k=cotes]') == '',
                'ACAD_TABLE sans unité : choix demandé, cotes non proposées')
        pg.select_option('#dxiPN select[data-nu="N2"]', 'mm')
        s.check(pg.input_value('#dxnT tr[data-n="3"] [data-k=cotes]') == '200 × 200', 'unité choisie : cotes proposées')
        pg.set_input_files('#dxiF', p23); pg.wait_for_selector('#dxnT tr[data-n]')
        pg.fill('#dxiH', '250'); pg.click('#dxnT tr[data-n="4"] td:nth-child(2)')
        pg.locator('#dxi').screenshot(path=os.path.join(HERE, 'out', 't_nomenclature.png'))
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', '; '.join(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_nomenclature')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
