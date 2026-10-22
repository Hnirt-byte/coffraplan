"""Phase 9A (demande de Kévin du 22/10/2026) : géométrie du support d'une réservation (support.js, CPI.support).
Trois notions distinctes : forme de l'ouverture, nature du support (voile droit, voile circulaire, autre, inconnu), solution de
coffrage (jamais choisie : « a_determiner », pistes motivées). Aucun seuil de 500 mm : flèche calculée par GEO.sag du moteur, comparée
à une tolérance saisie. Valeurs absentes = null ; provenance de chaque valeur (cote explicite, mesure, calcul, saisie).
Cas : voile droit / circulaire, ouverture rectangulaire ou circulaire, 500 × 500, 500 × 1 000 (orientation réelle), 1 200 × 1 000,
rayons et épaisseurs différents, plusieurs vues, échelle absente ou incohérente, épaisseur absente, deux supports possibles, courbes
non circulaires, plan très chargé (relecture locale), faux positifs (tableau, cartouche, élévation, contour écarté) ; PDF (Bézier),
DXF (ARC, polylignes à bulge, bloc en miroir) ; analyse de bout en bout dans la fenêtre d'import (DXI.SP, export JSON), sans
création d'ouvrage ni modification de la nomenclature ; hors connexion. Plans entièrement fictifs : tests/support_fictifs.py,
tests/support_cas.js."""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
import support_fictifs as SF

SAG = 'GEO.sag'


def t(s):
    tmp = tempfile.mkdtemp()
    F = SF.fichiers(tmp)
    s.check(open(F['SUPPORT_PLAN.pdf'][0], 'rb').read() == open(SF.fichiers(tempfile.mkdtemp())['SUPPORT_PLAN.pdf'][0], 'rb').read(), 'PDF fictif : écriture déterministe')
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500)
        net = []
        pg.context.route(lambda u: not u.startswith(('file:', 'blob:', 'data:')), lambda r: (net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        pg.add_script_tag(path=os.path.join(HERE, 'support_cas.js'))
        J = pg.evaluate
        # A(code) : code JS qui construit x = {env, obs, k} et o (options) puis analyse ; renvoie le résultat
        A = lambda code, o='{}': J('()=>{const sag=GEO.sag;' + code + ';const O=Object.assign({k:x.k,sag},' + o + ');return CPI.support.analyser(x.obs,x.env,O)}')
        P0 = J('P.length')

        # ---- 1. voile droit, réservation rectangulaire 500 × 500
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"})', '{ligne:SC.ligne({a:500,b:500})}')
        s.check(r['support']['type'] == 'voile_droit' and r['support']['epaisseur_mm'] == 200 and r['ouverture']['type'] == 'carre'
                and r['provenance']['support.epaisseur_mm']['origine'] == 'mesure' and r['coffrage']['solution_proposee'] == 'a_determiner'
                and [p['solution'] for p in r['coffrage']['pistes']] == ['coffrage_rectangulaire'] and r['validation_utilisateur_requise'] is True,
                'voile droit + 500 × 500 : voile droit, épaisseur 200 mesurée, piste coffrage rectangulaire, solution « a_determiner », validation requise', json.dumps(r, ensure_ascii=False)[:500])
        s.check(r['support']['rayon_interieur_mm'] is None and r['coffrage']['fleche_interieure_mm'] is None, 'voile droit : rayon et flèche null (jamais inventés)')
        s.check(set(r) >= {'repere', 'ouverture', 'support', 'coffrage', 'provenance', 'preuves', 'incertitudes', 'validation_utilisateur_requise'}
                and any(p['type'] == 'faces_paralleles' and p['traverse'] for p in r['preuves']), 'contrat de sortie : clés attendues, preuve graphique (faces parallèles traversées)')
        r2 = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"})', '{ligne:SC.ligne({a:500,b:500})}')
        s.check(json.dumps(r, sort_keys=True) == json.dumps(r2, sort_keys=True), 'déterministe : même entrée → même résultat')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect",ang:37,x:300,y:-120})', '{ligne:SC.ligne({a:500,b:500})}')
        s.check(r['support']['type'] == 'voile_droit' and r['support']['epaisseur_mm'] == 200, 'voile droit incliné (37°) et décalé : même résultat')

        # ---- 2. voile circulaire, réservation 1 200 × 1 000 ; flèche calculée par le moteur ; tolérance saisie
        q = 'const x=SC.voileCirc({Ri:6000,t:250,w:1200,ouverture:"rect"})'
        f = J('GEO.sag(6000,1200)'), J('GEO.sag(6250,1200)')
        r = A(q, '{ligne:SC.ligne({a:1200,b:1000})}')
        S = r['support']
        s.check(S['type'] == 'voile_circulaire' and S['epaisseur_mm'] == 250 and S['rayon_interieur_mm'] == 6000 and S['rayon_exterieur_mm'] == 6250,
                'voile circulaire (Bézier) : rayon intérieur 6000, extérieur 6250, épaisseur 250', json.dumps(S))
        s.check(abs(r['coffrage']['fleche_interieure_mm'] - f[0]) < 0.06 and abs(r['coffrage']['fleche_exterieure_mm'] - f[1]) < 0.06
                and r['provenance']['coffrage.fleche_interieure_mm']['origine'] == 'calcul' and r['provenance']['support.rayon_interieur_mm']['origine'] == 'mesure',
                f'1200 × 1000 : flèches = GEO.sag(6000, 1200) = {f[0]:.1f} mm et GEO.sag(6250, 1200) (calcul du moteur) ; rayon mesuré', json.dumps(r['coffrage']))
        s.check([p['solution'] for p in r['coffrage']['pistes']] == ['a_determiner'] and 'tolérance' in r['coffrage']['pistes'][0]['motif'] and r['coffrage']['tolerance_mm'] is None,
                '1200 × 1000 sans tolérance : rien de choisi (flèche à comparer à la tolérance admissible, non fixée)')
        r5 = A(q, '{ligne:SC.ligne({a:1200,b:1000}),tolerance_mm:5}')
        r40 = A(q, '{ligne:SC.ligne({a:1200,b:1000}),tolerance_mm:40}')
        s.check(r5['coffrage']['pistes'][0]['solution'] == 'mannequin_cintre' and r40['coffrage']['pistes'][0]['solution'] == 'coffrage_rectangulaire'
                and r5['coffrage']['solution_proposee'] == r40['coffrage']['solution_proposee'] == 'a_determiner' and r5['provenance']['coffrage.tolerance_mm']['origine'] == 'saisie',
                '1200 × 1000 : tolérance 5 mm → piste mannequin cintré ; 40 mm → piste coffrage rectangulaire ; solution toujours « a_determiner »')
        cv = r['correspondance_voile']
        s.check(cv and cv['forme'] == 'voile' and cv['L'] == 1200 and cv['l'] == 250 and cv['h'] == 1000 and cv['DcuveM'] == 12 and cv['dRef'] == 'int' and cv['joues'] is None,
                'correspondance avec le voile cintré du moteur (L corde, l épaisseur, h, Ø cuve au parement intérieur) : proposée, jamais appliquée', json.dumps(cv, ensure_ascii=False))

        # ---- 3. 500 × 500 dans un voile circulaire : flèche, coffrage simple possible selon la tolérance
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:500,ouverture:"rect"})', '{ligne:SC.ligne({a:500,b:500}),tolerance_mm:10}')
        s.check(r['support']['type'] == 'voile_circulaire' and abs(r['coffrage']['fleche_interieure_mm'] - J('GEO.sag(6000,500)')) < 0.06
                and r['coffrage']['pistes'][0]['solution'] == 'coffrage_rectangulaire', '500 × 500 dans un voile Ø 12 m : flèche 5,2 mm ≤ tolérance 10 → piste coffrage rectangulaire simple')

        # ---- 4. 500 × 1 000 : la hauteur 1 000 n'est pas la largeur soumise à la courbure
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:500,ouverture:"rect",mode:"arc"})', '{ligne:SC.ligne({a:1000,b:500})}')
        O = r['ouverture']
        s.check(O['largeur_suivant_paroi_mm'] == 500 and O['largeur_mm'] == 500 and O['hauteur_mm'] == 1000 and abs(r['coffrage']['fleche_interieure_mm'] - J('GEO.sag(6000,500)')) < 0.06
                and 'mesure' in r['provenance']['ouverture.largeur_suivant_paroi_mm']['detail'],
                'tableau « 1000x500 », 500 mesuré le long de la paroi : largeur suivant la courbure 500, hauteur 1000, flèche sur 500 (pas sur 1000)', json.dumps(O))
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:500,ouverture:"rect"})', '{ligne:SC.ligne({a:500,b:1000,colonnes:true})}')
        s.check(r['ouverture']['largeur_suivant_paroi_mm'] == 500 and r['ouverture']['hauteur_mm'] == 1000 and r['provenance']['ouverture.largeur_mm']['detail'].startswith('colonnes'),
                'colonnes Largeur / Hauteur du tableau : largeur 500 (suivant la paroi), hauteur 1000, cotes explicites')
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:500,ouverture:"rect"})', '{k:null,ligne:SC.ligne({a:1000,b:500})}')
        s.check(r['ouverture']['largeur_suivant_paroi_mm'] is None and r['coffrage']['fleche_interieure_mm'] is None and any('orientation non confirmée' in m for m in r['incertitudes']),
                'sans échelle ni épaisseur : orientation non confirmée, largeur suivant la paroi et flèche null', json.dumps(r['incertitudes'], ensure_ascii=False))

        # ---- 5. réservation circulaire dans un voile droit et dans un voile cintré
        # en plan, une traversée circulaire est dessinée d'une face à l'autre (largeur = Ø) ; la forme vient du tableau
        r = A('const x=SC.voileDroit({t:300,w:200,ouverture:"rect"})', '{ligne:SC.ligne({D:200})}')
        s.check(r['ouverture']['type'] == 'circ' and r['ouverture']['diametre_mm'] == 200 and r['support']['type'] == 'voile_droit' and r['support']['epaisseur_mm'] == 300
                and r['coffrage']['pistes'][0]['solution'] == 'fourreau_circulaire', 'Ø200 dans un voile droit : ouverture circulaire, voile droit 300, piste fourreau')
        r = A('const x=SC.voileCirc({Ri:6000,t:300,w:200,ouverture:"rect"})', '{ligne:SC.ligne({D:200})}')
        s.check(r['ouverture']['type'] == 'circ' and r['support']['type'] == 'voile_circulaire' and r['coffrage']['pistes'][0]['solution'] == 'fourreau_circulaire'
                and 'même dans un voile cintré' in r['coffrage']['pistes'][0]['motif'] and 'traversée' in r['coffrage']['pistes'][0]['motif'],
                'Ø200 dans un voile cintré : piste fourreau / solution circulaire classique, même dans un voile cintré, sous réserve des contraintes de traversée')
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:500,ouverture:"rect"})', '{ligne:SC.ligne({D:500})}')
        s.check(r['ouverture']['type'] == 'circ' and r['support']['type'] == 'voile_circulaire' and r['coffrage']['pistes'][0]['solution'] == 'fourreau_circulaire'
                and 'même dans un voile cintré' in r['coffrage']['pistes'][0]['motif'],
                'Ø500 : traversée dessinée en rectangle dans la vue en plan d\'un voile cintré : forme du tableau (circulaire), piste fourreau')
        r = A('const x=SC.voileCirc({Ri:6000,t:300,w:500,ouverture:"circ",D:500})', '{ligne:SC.ligne({D:500})}')
        s.check(r['support']['type'] == 'inconnu', 'cercle Ø500 plus large que la paroi de 300 : jamais rattaché à cette paroi')

        # ---- 6. rayons et épaisseurs différents (Bézier, ARC, segments aplatis)
        for Ri, t_, w, mode in ((3000, 300, 800, 'bezier'), (12000, 180, 1500, 'arc'), (4000, 200, 800, 'chaine'), (25000, 400, 2000, 'bezier')):
            r = A(f'const x=SC.voileCirc({{Ri:{Ri},t:{t_},w:{w},ouverture:"rect",mode:"{mode}"}})', f'{{ligne:SC.ligne({{a:{w},b:900}})}}')
            S = r['support']
            s.check(S['type'] == 'voile_circulaire' and abs(S['rayon_interieur_mm'] - Ri) <= 0.01 * Ri and abs(S['epaisseur_mm'] - t_) <= 0.02 * t_
                    and abs(r['coffrage']['fleche_interieure_mm'] - J(f'GEO.sag({S["rayon_interieur_mm"]},{w})')) < 0.06,
                    f'R int {Ri}, épaisseur {t_}, {w} de large ({mode}) : rayon et épaisseur à 1-2 %, flèche du moteur', json.dumps(S))
        s.check(any('segments' in m for m in A('const x=SC.voileCirc({Ri:4000,t:200,w:800,ouverture:"rect",mode:"chaine"})')['incertitudes']),
                'faces reconstituées de segments (courbe aplatie) : rayon approché, signalé')

        # ---- 7. plusieurs vues : concordantes, discordantes
        V = J('''()=>{const sag=GEO.sag,L=SC.ligne({a:500,b:500}),a=SC.voileDroit({t:200,w:500,ouverture:"rect"}),b=SC.voileDroit({t:200,w:500,ouverture:"rect",ang:90,x:900}),
            c=SC.voileDroit({t:250,w:500,ouverture:"rect",x:2000});const f=x=>CPI.support.analyser(x.obs,x.env,{k:x.k,sag,ligne:L});
            return[CPI.support.consolider([f(a),f(b)]),CPI.support.consolider([f(a),f(c)])]}''')
        s.check(V[0]['support']['epaisseur_mm'] == 200 and V[0]['provenance']['support.epaisseur_mm']['vues'] == 2 and len(V[0]['observations']) == 2,
                'deux vues concordantes : épaisseur 200 gardée (2 vues)')
        s.check(V[1]['support']['epaisseur_mm'] is None and any('valeurs différentes selon les vues' in m for m in V[1]['incertitudes']),
                'deux vues discordantes (200 / 250) : épaisseur null, désaccord signalé')

        # ---- 8. échelle absente, incohérente ; épaisseur absente ; échelle déduite d'une épaisseur cotée
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"})', '{k:null}')
        s.check(r['support']['type'] == 'voile_droit' and r['support']['epaisseur_mm'] is None and any('échelle absente' in m for m in r['incertitudes'])
                and any('épaisseur absente' in m for m in r['incertitudes']), 'échelle absente : voile droit reconnu, épaisseur null (absente, signalée)')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"})', '{k:x.k*2,ligne:SC.ligne({a:500,b:500})}')
        s.check(r['support']['epaisseur_mm'] is None and any('échelle incohérente' in m for m in r['incertitudes']),
                'échelle incohérente (largeur mesurée 1000 pour un 500 × 500) : mesures non utilisées', json.dumps(r['incertitudes'], ensure_ascii=False))
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"})', '{echelle:{source:"vue 1:50",autres:[{k:x.k/2,source:"calibrage"}]}}')
        s.check(r['support']['epaisseur_mm'] is None and any('deux échelles différentes' in m for m in r['incertitudes']), 'deux échelles contradictoires pour la vue : mesures non utilisées')
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:1200,ouverture:"rect"})', '{k:null,ligne:SC.ligne({a:1200,b:1000,cellules:["ép. 250 mm"]})}')
        s.check(r['support']['epaisseur_mm'] == 250 and r['provenance']['support.epaisseur_mm']['source'] == 'nomenclature' and r['support']['rayon_interieur_mm'] == 6000
                and r['provenance']['support.rayon_interieur_mm']['origine'] == 'calcul' and any('échelle déduite' in m for m in r['incertitudes']) and r['support']['confiance'] != 'forte',
                'sans échelle, épaisseur « ép. 250 mm » au tableau : rayon calculé par le rapport du dessin (provenance calcul, signalé)', json.dumps(r['provenance'], ensure_ascii=False)[:400])
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"});x.env.textes.push({id:"c1",texte:"20",x:-30,y:0,h:2.5})', '{ligne:SC.ligne({a:500,b:500})}')
        s.check(r['support']['epaisseur_mm'] == 200 and r['provenance']['support.epaisseur_mm'] == {'origine': 'cote_explicite', 'source': 'dessin', 'detail': '« 20 » confirmée par la mesure (200 mm)'}
                and r['support']['confiance'] == 'forte', 'cote « 20 » écrite dans la paroi, confirmée par la mesure (cm) : cote explicite, confiance forte')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"});x.env.textes.push({id:"c1",texte:"20",x:-30,y:0,h:2.5})', '{k:null}')
        s.check(r['support']['epaisseur_mm'] is None and any('« 20 »' in m for m in r['incertitudes']), 'même cote sans échelle : non attribuée (proximité ≠ certitude), signalée')
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:500,ouverture:"rect",mode:"arc"});x.env.textes.push({id:"c2",texte:"R=6000",x:0,y:300,h:2.5})')
        s.check(r['support']['rayon_interieur_mm'] == 6000 and r['provenance']['support.rayon_interieur_mm']['origine'] == 'cote_explicite', 'cote « R=6000 » confirmée par la mesure : rayon explicite')
        r = A('const x=SC.voileCirc({Ri:6000,t:250,w:500,ouverture:"rect",mode:"arc"});x.env.textes.push({id:"c2",texte:"R=6000",x:0,y:300,h:2.5})', '{k:null}')
        s.check(r['support']['rayon_interieur_mm'] is None and any('Rayon' in m or 'rayon non confirmé' in m for m in r['incertitudes']), 'même cote sans échelle : rayon null (« rayon non confirmé »)')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"})', '{k:null,saisie:{epaisseur_mm:200}}')
        s.check(r['support']['epaisseur_mm'] == 200 and r['provenance']['support.epaisseur_mm']['origine'] == 'saisie', 'épaisseur saisie par l\'utilisateur : provenance « saisie »')

        # ---- 9. deux supports voisins possibles ; courbes non circulaires
        r = A('const x=SC.voileDroit({t:200,w:200,ouverture:"rect"}),y=SC.voileDroit({t:200,w:200,ouverture:"rect",ang:90});x.env.segments.push(...y.env.segments)')
        s.check(r['support']['type'] == 'inconnu' and r['support']['epaisseur_mm'] is None and any('deux supports possibles' in m for m in r['incertitudes']),
                'réservation 200 × 200 au croisement de deux voiles de 200 : deux supports possibles, rien de choisi', json.dumps(r['incertitudes'], ensure_ascii=False))
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"}),y=SC.voileCirc({Ri:6000,t:200,w:500,ouverture:"rect"});x.env.courbes=y.env.courbes.map(c=>({id:c.id,c:c.c.map(p=>[p[0],p[1]-6100/SC.K50])}))')
        s.check(r['support']['type'] == 'inconnu' and any('voile_droit et voile_circulaire' in m or 'voile_circulaire et voile_droit' in m for m in r['incertitudes']),
                'voile droit et voile circulaire superposés autour de la même réservation : deux supports possibles', json.dumps(r['incertitudes'], ensure_ascii=False))
        r = A('''const C=[],E=(a,b,id)=>{for(let i=0;i<4;i++){const B=SC.bez([0,0],1,i*Math.PI/2,(i+1)*Math.PI/2,id+i)[0];B.c=B.c.map(p=>[p[0]*a,p[1]*b]);C.push(B)}};
            E(400,200,"e");E(415,215,"f");const x={env:{unite:"pt",segments:[],courbes:C,arcs:[],textes:[]},obs:{repere:"R1",point:[0,207],h:2.5,page:1},k:SC.K50}''')
        s.check(r['support']['type'] == 'autre' and r['support']['rayon_interieur_mm'] is None and any('non circulaires' in m for m in r['incertitudes']),
                'parois elliptiques (Bézier non circulaires) : support « autre », aucun rayon')

        # ---- 10. faux positifs : quadrillage de tableau, cadre de tableau, contour écarté, vue en élévation, vue de détail
        r = A('const S=[];for(let i=0;i<8;i++)S.push(SC.seg([-100,i*8],[100,i*8],"g"+i));const P=SC.rect(0,28,30,8,0);S.push(...SC.cotes(P));const x={env:{unite:"pt",segments:S,courbes:[],arcs:[],textes:[]},obs:{repere:"R1",candidat:SC.candRect(P),page:1},k:SC.K50}')
        s.check(r['support']['type'] == 'inconnu' and any(p['type'] == 'quadrillage_ecarte' for p in r['preuves']), 'cellule d\'un quadrillage (lignes régulières) : pas un voile')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"})', '{cadres:[[-100,-100,100,100]]}')
        s.check(r['support']['type'] == 'inconnu' and any('tableau ou un cartouche' in m for m in r['incertitudes']), 'observation dans un tableau ou un cartouche : non analysée')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect"});x.obs.candidat.statut="non_pris_en_charge";x.obs.candidat.remarques=["cadre de feuille ou de vue"]')
        s.check(r['support']['type'] == 'inconnu' and any('contour écarté' in m for m in r['incertitudes']), 'contour écarté par le repérage : non analysé (sauf reprise explicite)')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect",vue:{id:"V2",type:"elevation"}})')
        s.check(r['support']['type'] == 'inconnu' and any('élévation' in m for m in r['incertitudes']), 'vue en élévation : épaisseur non visible, non analysée')
        r = A('const x=SC.voileDroit({t:200,w:500,ouverture:"rect",vue:{id:"V3",type:"detail"}})')
        s.check(r['support']['type'] == 'voile_droit' and any('détail' in m for m in r['incertitudes']), 'vue de détail : analysée, échelle propre signalée')
        r = A('const x=SC.voileDroit({t:600,w:500,ouverture:"circ",D:150})')
        s.check(r['support']['type'] == 'inconnu' and r['support']['epaisseur_mm'] is None and any(p['type'] == 'bande_possible' and p['ecart_mm'] == 600 for p in r['preuves'])
                and any('sans aller de l\'une à l\'autre' in m for m in r['incertitudes']),
                'réservation entre deux murs sans les toucher (pièce, dalle, élévation) : jamais un support, bande signalée (600 mm), épaisseur null', json.dumps(r['incertitudes'], ensure_ascii=False))

        # ---- 11. PDF fictif : courbes de Bézier relues par CPI.pdf.chemins ; bout en bout dans la fenêtre d'import
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['SUPPORT_PLAN.pdf'][0]); pg.wait_for_function('DXI&&DXI.NA&&DXI.doc')
        NL0 = J('JSON.stringify(DXI.NL.map(({L})=>L))')
        g = J('async()=>{const g=await CPI.pdf.chemins(DXI.pdf,1);return{n:g.courbes.length,s:g.segments.length,ok:CPI.support.arcsBezier(g.courbes,0.1).arcs.length}}')
        s.check(g['n'] > 0 and g['ok'] == g['n'], f'PDF : {g["n"]} pièces de Bézier des faces courbes relues, toutes reconnues comme arcs de cercle', json.dumps(g))
        J('()=>{dxiVue("p");DXI.page=1;dxrEchLue(50);el("dxrOcr")&&(el("dxrOcr").checked=false)}')
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob', timeout=200000)
        SP = J('DXI.SP')
        R = {J(f'DXI.NL.find(({{L}})=>L.id==="{k}").L.repere'): v for k, v in SP.items()}
        s.check(sorted(R) == ['R01', 'R02', 'R03', 'R04'], 'bout en bout : support analysé pour les 4 réservations associées', json.dumps(sorted(R)))
        e = lambda k: R.get(k, {}).get('support', {})
        s.check(e('R01').get('type') == 'voile_droit' and e('R01').get('epaisseur_mm') == 200 and e('R04').get('type') == 'voile_droit' and R['R04']['ouverture']['type'] == 'circ',
                'R01 (500 × 500) et R04 (Ø200) : voile droit 200 ; R04 ouverture circulaire (tableau)')
        s.check(any('repris pour l\'analyse du support' in m for m in R['R01']['incertitudes']),
                'R01 : contour raccordé aux faces (écarté comme cellule de quadrillage par le repérage) repris pour le support seulement, signalé')
        s.check(e('R02').get('type') == 'voile_circulaire' and e('R02').get('rayon_interieur_mm') == 6000 and e('R02').get('epaisseur_mm') == 250 and e('R02').get('confiance') == 'forte'
                and R['R02']['provenance']['support.epaisseur_mm']['source'] == 'nomenclature', 'R02 : voile circulaire R 6000, ép. 250 (désignation « ép. 250 mm » du tableau, confirmée), confiance forte',
                json.dumps(R.get('R02', {}).get('support')))
        s.check(R['R03']['ouverture']['largeur_suivant_paroi_mm'] == 500 and R['R03']['ouverture']['hauteur_mm'] == 1000 and abs(R['R03']['coffrage']['fleche_interieure_mm'] - J('GEO.sag(6000,500)')) < 0.06,
                'R03 « 1000x500 » : 500 suivant la courbure, hauteur 1000, flèche sur 500', json.dumps(R['R03']['ouverture']))
        s.check(all(r['validation_utilisateur_requise'] and r['coffrage']['solution_proposee'] == 'a_determiner' for r in R.values()), 'toutes : validation requise, solution « a_determiner »')
        js = J('dxrJSON()')
        s.check(len(js['supports']) == 4 and all('ligne' in x and 'support' in x for x in js['supports']), 'export JSON de l\'analyse : clé « supports » (4)')
        s.check(J('JSON.stringify(DXI.NL.map(({L})=>L))') == NL0 and J('P.length') == P0 and J('el("iForme").value') != 'voile',
                'nomenclature d\'origine inchangée ; aucun ouvrage créé ; forme voile non activée')

        # ---- 12. plan très chargé : plafond atteint, relecture locale autour de la réservation
        pg.set_input_files('#dxiF', F['SUPPORT_CHARGE.pdf'][0]); pg.wait_for_function('DXI&&DXI.doc&&DXI.doc.fichier==="SUPPORT_CHARGE.pdf"', timeout=120000)
        h = J('''async()=>{const g=await CPI.pdf.chemins(DXI.pdf,1),z=await CPI.pdf.chemins(DXI.pdf,1,{zones:[[150,560,250,680]]});
          const c=SC.candRect([[185.83,614.33],[214.17,614.33],[214.17,625.67],[185.83,625.67]]),f=G=>CPI.support.analyser({repere:"R01",candidat:c,page:1},CPI.support.envPdf(G,[]),{k:SC.K50,sag:GEO.sag});
          return{coupe:g.coupe,nG:g.segments.length,coupeZ:z.coupe,nZ:z.segments.length,a:f(g),b:f(z)}}''')
        s.check(h['coupe'] and not h['coupeZ'] and h['nZ'] < 100, f'plan chargé : plafond atteint sur la page ({h["nG"]} traits), relecture locale complète ({h["nZ"]} traits)')
        s.check(h['a']['support']['type'] == 'inconnu' and any('partiellement extraite' in m for m in h['a']['incertitudes']) and h['b']['support']['type'] == 'voile_droit' and h['b']['support']['epaisseur_mm'] == 200,
                'page coupée : support inconnu, géométrie partielle signalée ; relecture locale : voile droit 200', json.dumps([h['a']['support'], h['b']['support']]))

        # ---- 13. DXF : ARC, polylignes à bulge, bloc inséré en miroir et tourné (unité mm, échelle 1)
        for v in ('ARC', 'BULGE', 'BLOC'):
            txt = open(F[f'SUPPORT_{v}.dxf'][0], encoding='utf-8', errors='replace').read()
            # bloc : le détecteur ne décompose pas les blocs (inchangé) ; contour de R02 transformé comme le bloc (miroir X, 30°, point d'insertion)
            d = J('''(t)=>{const doc=CPI.dxf.decoder(t,"x.dxf"),C=CPI.detecteur.detecter(doc).candidats.filter(c=>c.statut==="a_confirmer"&&c.type==="rect"),env=CPI.support.envDxf(doc);
              if(/CUVE/.test(t)){const yi=Math.sqrt(6000**2-600**2),ye=Math.sqrt(6250**2-600**2),a=Math.PI/6,T=([x,y])=>[-x*Math.cos(a)-y*Math.sin(a)+20000,-x*Math.sin(a)+y*Math.cos(a)+5000];
                C.push(SC.candRect([[-600,yi],[600,yi],[600,ye],[-600,ye]].map(T),"BLOC"))}
              return{arcs:doc.arcs.length,src:[...new Set(doc.arcs.map(a=>a.source))],R:C.map(c=>CPI.support.analyser({repere:c.id,candidat:c},env,{k:1,sag:GEO.sag,ligne:{dims:{type:"rect",a:Math.round(c.dims.L),b:900,unite:"mm"}}}))}}''', txt)
            T = sorted(((r['support']['type'], r['support']['epaisseur_mm'], r['support']['rayon_interieur_mm']) for r in d['R']), key=str)
            s.check(('voile_circulaire', 250, 6000) in T and ('voile_droit', 200, None) in T, f'DXF {v} : voile circulaire R 6000 ép. 250 et voile droit ép. 200 ({", ".join(d["src"])})', json.dumps([T, d['arcs']]))
        k = J('()=>{const d=CPI.dxf.decoder(' + json.dumps(open(F['SUPPORT_ARC.dxf'][0], encoding='utf-8').read()) + ',"x");return [d.traits.length,d.entites.filter(e=>e.type==="autre"&&/ARC/.test(e.nature)).length]}')
        s.check(k[1] == 4, 'DXF : les 4 ARC restent « autre » dans les entités (détecteur inchangé), relevés à part (doc.arcs)', json.dumps(k))

        s.check(not net, 'aucune requête réseau', json.dumps(net[:3]))
        s.check(not errs, 'aucune erreur JS', json.dumps(errs[:3]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_support')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
