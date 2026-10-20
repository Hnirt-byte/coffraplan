"""Phase 5 (demande de Kévin du 20/10/2026) : lecture des nomenclatures (titres de colonnes, ordre des cotes, tirets, DN,
tableaux tournés, couleurs et nuages de révision), vues techniques (vues.js : titre, type, partie, région), occurrences
physiques sans doublon (quantité du tableau = référence, jamais multipliée par les vues), formes hors nomenclature
classées dans une section repliée, export JSON de l'analyse. Plans entièrement fictifs : tests/vues_fictifs.py."""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
import vues_fictifs as VF


def t(s):
    tmp = tempfile.mkdtemp()
    F = VF.fichiers(tmp)
    s.check(all(open(c, 'rb').read() == open(VF.fichiers(tempfile.mkdtemp())[n][0], 'rb').read() for n, (c, _) in F.items()), 'PDF fictifs : écriture déterministe')
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500)
        net = []
        pg.context.route(lambda u: not u.startswith('file:') and not u.startswith('blob:') and not u.startswith('data:'), lambda r: (net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = pg.evaluate

        # ---- module : titres de colonnes reconnus (unité séparée ou dans le titre)
        k = J('''()=>Object.fromEntries(['Nb','Nb.','Nombre','Qté','Quantité','Fonction','Largeur','Largeur (mm)','Hauteur mm','Ø','Ø (mm)','Diamètre','Diamètre (cm)']
          .map(t=>[t,CPI.nomenclatures.kinds(t)]))''')
        att = {'Nb': 'quantite', 'Nb.': 'quantite', 'Nombre': 'quantite', 'Qté': 'quantite', 'Quantité': 'quantite', 'Fonction': 'description', 'Largeur': 'largeur',
               'Largeur (mm)': 'largeur', 'Hauteur mm': 'hauteur', 'Ø': 'diametre', 'Ø (mm)': 'diametre', 'Diamètre': 'diametre', 'Diamètre (cm)': 'diametre'}
        s.check(all(att[t] in k[t] for t in att), 'titres de colonnes : Nb, Nombre, Qté, Quantité, Fonction, Largeur, Hauteur, Ø, Diamètre (unité séparée ou non)', json.dumps(k, ensure_ascii=False))

        # ---- module : titres de vues (mots-clés, OCR approximatif, faux titres, sous-titres)
        T = J('''()=>{const T=[];for(let i=0;i<20;i++)T.push({id:'p'+i,texte:'x'+i,x:20*i,y:10,h:2,w:4});
          const g=(id,texte,x,y,o)=>T.push(Object.assign({id,texte,x,y,h:5,w:texte.length*3},o||{}));
          g('a','N° DU PLAN',100,500);g('b','FERRKAILTAGE RADIER',300,500,{ocr:{conf:40}});g('c','Partie supérieure',300,490);
          g('d','COUPE B-B',600,500);g('e','à partir du niveau bas',100,300);g('f','ÉLÉVATION VOILE',600,300);
          return CPI.vues.titres(T).map(t=>({texte:t.texte,type:t.type,partie:t.partie,sous:t.sous,approx:t.approx}))}''')
        tx = {x['texte']: x for x in T}
        s.check('N° DU PLAN' not in tx and not any('partir' in x for x in tx), 'faux titres écartés : « N° DU PLAN », « à partir » (pas « partie »)', json.dumps(T, ensure_ascii=False))
        f = next((x for x in T if x['texte'].startswith('FERRKAILTAGE')), None)
        s.check(f and f['type'] == 'ferraillage_superieur' and f['partie'] == 'radier' and f['approx'],
                'titre lu par OCR « FERRKAILTAGE RADIER » + « Partie supérieure » : ferraillage supérieur du radier (lecture approchée signalée)', json.dumps(f, ensure_ascii=False))
        s.check(tx.get('COUPE B-B', {}).get('type') == 'coupe' and tx.get('ÉLÉVATION VOILE', {}).get('type') == 'elevation' and tx['ÉLÉVATION VOILE']['partie'] == 'voile',
                'types : coupe, élévation (partie voile)')

        # ---- module : consolidation (quantité du tableau = référence)
        c = J('''()=>{const V=[{id:'P',type:'plan',partie:'dalle',region:[0,0,100,100]},{id:'F',type:'ferraillage_inferieur',partie:'dalle',region:[200,0,300,100]},
            {id:'C',type:'coupe',partie:null,region:[0,200,100,250]}];
          const o=(vue,x,y,fiable)=>({page:1,vue,x,y,fiable:fiable!==false,doutes:[]});
          const a=CPI.vues.consolider({quantite:'2'},{occurrences:[o('P',20,80),o('P',60,30),o('F',220,80),o('C',30,220),o('F',290,10)]},V);
          const b=CPI.vues.consolider({quantite:'1'},{occurrences:[o('C',30,220),o('F',220,80)]},V);
          const d=CPI.vues.consolider({quantite:'1'},{occurrences:[o('P',20,80),o('P',60,30)]},V);
          const e=CPI.vues.consolider({quantite:''},{occurrences:[o('F',220,80,false)]},V);
          return{a:[a.attendue,a.localisees,a.representations,a.restantes,a.physiques[0].representations.length,a.physiques.map(p=>p.vue).join()],
            b:[b.localisees,b.restantes,b.physiques.map(p=>p.vue).join()],d:[d.localisees,d.restantes,d.depasse],e:[e.localisees,e.attendue]}}''')
        s.check(c['a'] == [2, 2, 5, 0, 2, 'P,P'], 'quantité 2, 5 représentations (plan ×2, ferraillage ×2, coupe) : 2 occurrences comptées dans le plan, ferraillage rattaché par position', json.dumps(c['a']))
        s.check(c['b'] == [1, 0, 'F'], 'sans vue en plan : occurrence comptée dans le ferraillage, jamais dans la coupe', json.dumps(c['b']))
        s.check(c['d'] == [2, 0, True], '2 occurrences pour une quantité de 1 : signalé, quantité du tableau gardée', json.dumps(c['d']))
        s.check(c['e'] == [0, None], 'lecture incertaine hors vue en plan : non comptée', json.dumps(c['e']))

        # ---- PDF_8 page 1 : nomenclature lue par le texte
        F8, inf = F['PDF_8_VUES.pdf']
        J('''()=>{el('iCh').value='CHANTIER_DEMO_V';el('iOuv').value='OUVRAGE_V';el('iForme').value='rect';updF();el('dL').value=700;el('dl').value=500;el('dh').value=250;el('iRef').value='Z98';addP()}''')
        P0 = J('JSON.stringify(P)')
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F8); pg.wait_for_selector('#dxnT tr[data-n]')
        N = J('''()=>Object.fromEntries(DXI.NL.map(({L})=>[L.repere,{q:L.quantite,nb:L.nb,d:L.dims&&(L.dims.type==='circ'?'Ø'+L.dims.D:L.dims.a+'x'+L.dims.b),av:(L.a_verifier||[]).join(' | ')}]))''')
        s.check(sorted(N) == ['V1', 'V2', 'V3', 'V4', 'V5'] and N['V1']['nb'] == 2, 'nomenclature : 5 lignes, quantité « Nb » 2 pour V1', json.dumps(N, ensure_ascii=False))
        s.check(N['V1']['d'] == '600x400', 'V1 : Ø « - » (absent) → Largeur × Hauteur 600 × 400', N['V1']['d'])
        s.check(N['V2']['d'] == 'Ø200', 'V2 : Ø seul → Ø200', N['V2']['d'])
        s.check(N['V3']['d'] == '500x300' and 'DN' not in (N['V3']['d'] or ''), 'V3 : DN100 des observations jamais pris pour une cote', N['V3']['d'])
        s.check(N['V4']['d'] == 'Ø65', 'V4 : Ø65 de la colonne, jamais le « Ø50 » de la fonction', N['V4']['d'])
        s.check(N['V5']['d'] is None and 'tous deux renseignés' in N['V5']['av'], 'V5 : Ø et Largeur × Hauteur renseignés : ambiguïté signalée, aucune cote choisie', json.dumps(N['V5'], ensure_ascii=False))

        # ---- analyse du dessin (sans OCR des repères : tous en texte)
        pg.click('#dxiTabP'); pg.wait_for_function('el("dxpPg").textContent.includes("/ 2")')
        J('el("dxrOcr").checked=false')
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob&&!!el("dxrT")', timeout=180000)
        V = J('dxrVues().map(v=>({id:v.id,page:v.page,type:v.type,partie:v.partie,titre:v.titre,region:v.region,confiance:v.confiance}))')
        vt = {v['titre']: v for v in V if v['titre']}
        s.check(vt.get('VUE EN PLAN DALLE', {}).get('type') == 'plan' and vt['VUE EN PLAN DALLE']['partie'] == 'dalle' and vt.get('COUPE A-A', {}).get('type') == 'coupe'
                and vt.get('FERRAILLAGE DALLE Partie inférieure', {}).get('type') == 'ferraillage_inferieur',
                'vues : plan dalle, coupe A-A, ferraillage inférieur dalle (titre, type, partie)', json.dumps(V, ensure_ascii=False))
        s.check(all(set(v) >= {'id', 'page', 'region', 'titre', 'type', 'partie', 'confiance'} for v in V) and len({v['id'] for v in V}) == len(V), 'vues : identifiants stables uniques, champs complets')
        idv = {t: v['id'] for t, v in vt.items()}
        pl, cp, fe = idv['VUE EN PLAN DALLE'], idv['COUPE A-A'], idv['FERRAILLAGE DALLE Partie inférieure']
        CS = J('Object.fromEntries(DXI.NL.map(({L})=>[L.repere,DXI.CS[L.id]]))')
        v1 = CS['V1']
        s.check([v1['attendue'], v1['localisees'], v1['restantes']] == [2, 2, 0] and v1['representations'] >= 3 and {p['vue'] for p in v1['physiques']} == {pl},
                'V1 (quantité 2) : 2 occurrences localisées dans le plan, coupe et ferraillage = représentations, 0 restante', json.dumps(v1, ensure_ascii=False)[:500])
        rf = [x['occurrence'] for x in v1['roles'] if x['vue'] == fe]
        s.check(rf and any(set(rf) & set(p['representations']) for p in v1['physiques']),
                'V1 : repère du ferraillage rattaché à l\'occurrence du plan à la même position relative')
        s.check(all(CS[r]['localisees'] == 1 and CS[r]['restantes'] == 0 for r in ('V2', 'V3', 'V4', 'V5')) and CS['V3']['representations'] == 2,
                'V2 à V5 : 1 occurrence chacune ; V3 vue en coupe = représentation, non comptée', json.dumps({r: CS[r]['localisees'] for r in CS}))
        s.check(sum(x['localisees'] for x in CS.values()) == 6 and not any(x['depasse'] for x in CS.values()), 'total : 6 occurrences pour 6 réservations au tableau, aucune multiplication par les vues')
        A = J('DXI.NL.map(({L})=>dxnAS(L).occurrences.filter(o=>o.contour).map(o=>[o.vue,DXI.C.find(c=>c.id===o.contour).vue])).flat()')
        s.check(A and all(a == c for a, c in A), 'chaque contour rattaché à un repère est dans la vue de ce repère', json.dumps(A))
        t1 = pg.inner_text(f'#dxnT tr[data-n="{J("DXI.NL.findIndex(x=>x.L.repere===\'V1\')")}"]')
        s.check('Quantité attendue 2' in t1 and 'localisée(s) : 2' in t1 and 'restante(s) : 0' in t1 and pl in t1, 'ligne V1 : quantité attendue, localisées, représentations, restantes et vue affichées', t1)

        # ---- formes hors nomenclature : section repliée, raisons, rien supprimé
        s.check(J('el("dxrH").tagName') == 'DETAILS' and not J('el("dxrH").open'), 'formes hors nomenclature : section repliée par défaut sous la nomenclature')
        H = J('dxrVis().map(i=>({id:DXI.C[i].id,vue:DXI.C[i].vue,n:dxrCl(i).niveau,r:dxrCl(i).raison}))')
        fer = [h for h in H if h['vue'] == fe]
        s.check(sum(1 for h in fer if h['n'] == 'parasite' and 'ferraillage' in h['r']) >= 6, '6 petits cadres d\'armatures du ferraillage : parasites probables, raison donnée', json.dumps(fer, ensure_ascii=False)[:600])
        s.check(all(h['r'] for h in H) and J('DXI.C.length') >= len(H), 'chaque forme hors nomenclature a sa raison ; aucune supprimée')
        pg.click('#dxrHs')
        s.check(J('el("dxrH").open') and pg.is_visible('#dxrT') and 'parasite probable' in pg.inner_text('#dxrT'), 'section ouverte : colonne « Raison » visible')

        # ---- export JSON (structures pour une future IA locale)
        X = J('dxrJSON()')
        s.check(X['format'] == 'coffraplan-analyse-plan' and all(k in X for k in ('tables', 'tableRows', 'views', 'graphicalObservations', 'physicalOccurrences', 'associations', 'evidence', 'uncertainties')),
                'JSON : tables, tableRows, views, graphicalObservations, physicalOccurrences, associations, evidence, uncertainties', ', '.join(X))
        s.check(len(X['physicalOccurrences']) == 6 and not any(p['vue'] == cp for p in X['physicalOccurrences']), 'JSON : 6 occurrences physiques, aucune dans la coupe')
        s.check(not J('el("dxrJ").disabled'), 'bouton « Analyse (JSON) » actif après l\'analyse')

        # ---- page 2 : nomenclature dessinée en couleur (glyphes magenta, grille bleue) avec un nuage de révision orange → OCR
        z = inf['z5']
        J('z=>{dxiVue("p");DXI.page=z.page;dxpPage();dxpZone(Object.assign({unite:"pt"},z))}', z)
        pg.wait_for_function('!el("dxpZo").disabled')
        pg.click('#dxpZo'); pg.wait_for_function('!DXI.ocJob', timeout=180000)
        R = J('DXI.OC?DXI.OC.rows.map(w=>w.cells):[]')
        att5 = {l[0]: l[3] for l in inf['NL5']}
        ok = [w for w in R if att5.get(w.get('repere')) and w.get('ouverture', '').replace('×', 'x').replace(' ', '') == att5[w['repere']]]
        s.check(len(R) == 4 and len(ok) >= 3 and any(w.get('repere') == 'R3' for w in R), 'OCR en couleur avec nuage de révision : 4 lignes, ≥ 3 cotes exactes, ligne R3 sous le nuage lue',
                json.dumps(R, ensure_ascii=False)[:600])

        # ---- création : V1 → un ouvrage, nb = quantité ; provenance des occurrences
        J('()=>{dxiVue("n")}')
        pg.fill('#dxiH', '300')
        i1 = J("DXI.NL.findIndex(x=>x.L.repere==='V1')")
        pg.check(f'#dxnT tr[data-n="{i1}"] [data-k=conf]')
        s.check(J('JSON.stringify(P)') == P0, 'avant confirmation : rien de créé')
        pg.click('#dxiGo')
        B = {p['ref']: p for p in J('P.slice(1)')}
        s.check('V1' in B and B['V1'].get('nb') == 2 and (B['V1']['L'], B['V1']['l']) == (600, 400), 'V1 créé : un ouvrage, nb = 2, 600 × 400', json.dumps({r: (p.get('nb'), p.get('L'), p.get('l')) for r, p in B.items()}))
        o = B['V1']['origineImport']['rapprochement']
        s.check(o['occurrences']['attendue'] == 2 and o['occurrences']['localisees'] == 2 and all(x.get('vue') and x.get('role') for x in o['localisations']),
                'provenance V1 : occurrences (attendue, localisées), vue et rôle de chaque localisation', json.dumps(o['occurrences'], ensure_ascii=False))
        J('()=>closeModal()')

        # ---- PDF_9 : nomenclature tournée de 90°, 270° et 180°
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['PDF_9_TOURNEES.pdf'][0]); pg.wait_for_function('DXI&&DXI.NA', timeout=120000)
        R9 = J('''DXI.NA.nomenclatures.map(N=>({p:N.page,rot:N.rotation||0,L:N.lignes.map(L=>L.repere+':'+(L.dims?(L.dims.type==='circ'?'Ø'+L.dims.D:L.dims.a+'x'+L.dims.b):'-')).join()}))''')
        ref = 'V1:600x400,V2:Ø200,V3:500x300,V4:Ø65,V5:-'
        s.check([r['rot'] for r in R9] == F['PDF_9_TOURNEES.pdf'][1]['rotations'], 'tableaux tournés de 90°, 270°, 180° : rotation reconnue', json.dumps(R9))
        s.check(len(R9) == 3 and all(r['L'] == ref for r in R9), 'tableaux tournés : mêmes 5 lignes et mêmes cotes que le tableau droit', json.dumps(R9, ensure_ascii=False))
        J('()=>closeModal()')

        net = [u for u in net if 'fonts.g' not in u]
        s.check(not net, 'hors connexion : aucune requête réseau', json.dumps(net[:5]))
        errs = [e for e in errs if 'net::ERR_FAILED' not in e and 'diacritics' not in e]
        s.check(not errs, 'aucune erreur JS', '; '.join(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_vues')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
