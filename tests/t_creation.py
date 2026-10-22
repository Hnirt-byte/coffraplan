"""Phase 9C : propositions sans mutation, préparation par moteurs existants et confirmation réelle dans Chromium.
PDF et cas entièrement fictifs. Aucun plan de chantier n'est versionné.
"""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
import support_fictifs as SF


def t(s):
    F = SF.fichiers(tempfile.mkdtemp())
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500)
        J = pg.evaluate
        net = []
        pg.context.route(lambda u: not u.startswith(('file:', 'blob:', 'data:')), lambda r: (net.append(r.request.url), r.abort()))
        pg.add_script_tag(path=os.path.join(HERE, 'support_cas.js'))
        J('''()=>{window.C9={proposer:(a,s={},o={})=>CPI.creation.proposer(a,s,Object.assign({sag:GEO.sag,voileGeo},o)),
          analyser:x=>CPI.support.analyser(x.obs,x.env,{k:x.k,sag:GEO.sag,ligne:SC.ligne({a:1200,b:1000})})};
          window.A9=C9.analyser(SC.voileCirc({Ri:6000,t:250,w:1200,ouverture:'rect'}));}''')
        prop = lambda s0, o0={}: J('x=>C9.proposer(A9,x[0],x[1])', [s0, o0])
        base = dict(joues='par', largeurRef='commune', solution='cintre', traversee=True)
        r = prop(base)
        s.check(r['valeurs']['e'] is None and r['valeurs']['R'] is None and r['fleches']['interieure'] is None,
                'mesures non confirmées : aucune épaisseur / aucun rayon converti pour créer')
        r = prop(base, dict(mesuresConfirmees=True))
        s.check(not r['manquants'] and r['tolerance'] is None and r['recommandation'] == 'a_determiner', 'tolérance vide : choix cintré explicite possible, aucune nécessité décidée')
        s.check(abs(r['fleches']['interieure'] - J('GEO.sag(6000,1200)')) < 1e-8, 'flèche intérieure par GEO.sag du moteur')
        s.check(abs(r['fleches']['exterieure'] - J('GEO.sag(6250,1200)')) < 1e-8, 'flèche extérieure par GEO.sag du moteur')
        s.check(prop(dict(base, tolerance=-1), dict(mesuresConfirmees=True))['manquants'], 'tolérance négative : à corriger, jamais ignorée')
        s.check(prop(dict(base, solution='simple'), dict(mesuresConfirmees=True))['manquants'], 'solution simple bloquée sans tolérance')
        r = prop(dict(base, solution='simple', tolerance=40), dict(mesuresConfirmees=True))
        s.check(not r['manquants'] and r['recommandation'] == 'simple', 'flèches sous tolérance 40 : proposition simple à confirmer')
        r = prop(dict(base, tolerance=5), dict(mesuresConfirmees=True))
        s.check(r['recommandation'] == 'cintre' and r['origines']['tolerance']['origine'] == 'saisie', 'tolérance 5 : cintrage proposé, provenance conservée')
        r = prop(dict(base, tolerance=0), dict(mesuresConfirmees=True))
        s.check(r['tolerance'] == 0 and r['recommandation'] == 'cintre', 'tolérance zéro respectée, pas remplacée par un seuil implicite')
        r = prop(dict(base, joues='rad', largeurRef='exterieure'), dict(mesuresConfirmees=True))
        s.check(not r['manquants'] and r['geometrie']['cExt'] == 1200 and r['geometrie']['cInt'] < 1200,
                'joues radiales : L corde extérieure, corde intérieure calculée par voileGeo')
        s.check(abs(r['fleches']['interieure'] - J('GEO.sag(6000,1200*6000/6250)')) < 1e-8, 'flèche radiale : corde intérieure propre, pas la corde extérieure')
        s.check(prop(dict(base, joues='rad'), dict(mesuresConfirmees=True))['manquants'], 'corde commune refusée pour joues radiales')
        s.check(prop(dict(base, largeurRef='autre'), dict(mesuresConfirmees=True))['manquants'], 'largeur développée non assimilée à une corde')
        s.check(prop(dict(base, joues=''), dict(mesuresConfirmees=True))['manquants'], 'choix explicite des joues requis')
        s.check(prop(dict(base, L=13000), dict(mesuresConfirmees=True))['manquants'], 'corde impossible bloquée avant fabrication')
        s.check(prop(dict(base, e=None), dict(mesuresConfirmees=True))['valeurs']['e'] is None, 'effacer une valeur ne rétablit pas une valeur supposée')
        r = prop(dict(base, e=300, R=7000), dict(mesuresConfirmees=True))
        s.check(r['origines']['e']['origine'] == 'saisie' and r['origines']['e']['avant']['valeur'] == 250 and r['valeurs']['R'] == 7000,
                'correction manuelle : valeur initiale et origine conservées')
        s.check(J('()=>CPI.creation.preparer(C9.proposer(A9),{},{}).ok') is False, 'adaptateur refuse une préparation non confirmée')
        r = J('''()=>{const ancien=DXI;try{DXI={C:[{id:'F1',type:'circ',dims:{D:10},source:{page:1},remarques:[],annot:{cotes:{texte:'Ø200 mm'}}}],cal:{1:{k:50}}};return dxcAnalyse('g',0)}finally{DXI=ancien}}''')
        s.check(r['ouverture']['diametre_mm'] == 200 and r['provenance']['ouverture.diametre_mm']['origine'] == 'cote_explicite', 'cote écrite explicite prioritaire sur une mesure graphique divergente')
        # Chargement et analyse via le vrai parcours PDF ; aucun OCR requis dans ce fictif.
        pg.click('#bDxi');pg.set_input_files('#dxiF', F['SUPPORT_PLAN.pdf'][0]);pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
        J('()=>{DXI.ch="CHANTIER 9C";DXI.ouv="CUVE";dxiVue("p");dxrEchLue(50);el("dxrOcr").checked=false}')
        pg.click('#dxrGo');pg.wait_for_function('!DXI.rJob', timeout=200000)
        initial = J('JSON.stringify({P,PROF,LIBU,ENT})')
        J('()=>{window.K9=rep=>DXI.NL.findIndex(({L})=>L.repere===rep);dxcOuvrir("n",K9("R01"))}')
        s.check(J('JSON.stringify({P,PROF,LIBU,ENT})') == initial, 'ouvrir la proposition : projet / profils / modèles / entreprise inchangés')
        s.check(pg.input_value('#dxc_L') == '500' and pg.input_value('#dxc_h') == '500', 'tableau carré 500×500 mm : dimensions explicites disponibles sans échelle')
        pg.select_option('#dxc_type','rect');pg.fill('#dxc_h','800');pg.select_option('#dxc_support', 'voile_droit');pg.fill('#dxc_e','20 cm');pg.check('#dxc_traversee');pg.select_option('#dxc_solution','simple')
        pg.click('#dxcRecap')
        s.check(J('JSON.stringify({P,PROF,LIBU,ENT})') == initial and pg.is_disabled('#dxcCreer'), 'récapitulatif sans création ; dernière confirmation décochée')
        J('dxcCreer()')
        s.check(J('P.length') == 0, 'appel création sans confirmation : aucun ouvrage')
        pg.check('#dxcConfirme');pg.fill('#dxc_ref','R01-A')
        s.check(J('P.length') == 0 and pg.locator('#dxcConfirme').count() == 0, 'modifier après récapitulatif invalide la confirmation')
        pg.click('#dxcRecap');pg.check('#dxcConfirme');pg.click('#dxcCreer')
        s.check(J('P.length') == 1 and J('P[0].forme') == 'para' and J('[P[0].ppB,P[0].ppH,P[0].ppE,P[0].ppA,P[0].ppBe]') == [500,800,200,0,0],
                'rectangle fictif 500×800, voile droit 200 : mannequin traversant existant, sans biais ni pente')
        s.check(J('P[0].origineImport.analyse.source.repere') == 'R01', 'ligne source et repère brut conservés après correction de la référence')
        s.check(J('P[0].origineImport.confirmation_utilisateur') and J('P[0].origineImport.proposition.origines.e.origine') == 'saisie' and J('P[0].origineImport.saisiesBrutes.e') == '20 cm', 'provenance, saisie brute avec unité et confirmation persistées')
        r = J('''()=>{const d=canon(migr(P[0])),R=debit(d,null);return{erreurs:checks(d,null).filter(x=>x[0]!=='warn'),pieces:R.length,html:gen(d).length,model:!!model3(d,R)}}''')
        s.check(not r['erreurs'] and r['pieces']>0 and r['html']>1000 and r['model'], 'rectangle droit créé : contrôles, débit, feuilles et visualisation existants')
        manuel = J('''()=>{const m=T.mk('para',{ppB:500,ppH:800,ppE:200,ppA:0,ppBe:0},()=>{el('iCh').value=P[0].ch;el('iOuv').value=P[0].ouv;el('iRef').value=P[0].ref});return{cree:T.sum(P[0]),manuel:T.sum(m),optionsCree:P[0],optionsManuel:m}}''')
        s.check(manuel['cree'] == manuel['manuel'], 'rectangle droit importé : débit identique à la saisie manuelle, mêmes dimensions et référence', json.dumps(manuel,ensure_ascii=False))
        J('dxcCreer();dxcOuvrir("n",K9("R01"))')
        s.check(J('P.length') == 1 and pg.is_disabled('#dxcRecap'), 'validation répétée / réouverture : création unique même après changement de référence')
        J('dxcFermer();dxcOuvrir("n",K9("R02"))')
        s.check(pg.input_value('#dxc_R') == '', 'rayon mesuré masqué tant que son échelle n’est pas confirmée')
        pg.check('#dxc_mesures');pg.select_option('#dxc_joues','rad');pg.select_option('#dxc_largeurRef','exterieure');pg.check('#dxc_traversee');pg.select_option('#dxc_solution','cintre')
        s.check(pg.input_value('#dxc_R') == '6000', 'confirmation explicite du calibrage rend la mesure disponible')
        pg.click('#dxcRecap');pg.check('#dxcConfirme');pg.click('#dxcCreer')
        r = J('''()=>{const d=canon(migr(P[1])),g=voileGeo(d),m=manGeo(d,g),R=debit(d,g),M=model3(d,R);return{n:P.length,g,m,err:checks(d,g).filter(x=>x[0]!=='warn'),pieces:R.length,html:gen(d).length,model:!!M}}''')
        s.check(r['n'] == 2 and r['g']['ok'] and r['g']['rad'] and not r['err'] and r['pieces']>0 and r['html']>1000 and r['model'],
                'ouvrage cintré confirmé : voileGeo, manGeo, checks, débit, feuilles et modèle 3D existants', json.dumps(r)[:500])
        before = J('JSON.stringify(P.slice(0,2))')
        J('dxcOuvrir("n",K9("R04"))');pg.select_option('#dxc_support','voile_droit');pg.fill('#dxc_e','200');pg.fill('#dxc_profondeur','230');pg.check('#dxc_traversee');pg.select_option('#dxc_solution','fourreau')
        pg.click('#dxcRecap');pg.check('#dxcConfirme');pg.click('#dxcCreer')
        s.check(J('[P[2].forme,P[2].D,P[2].h]') == ['circ',200,230], 'fourreau fictif : diamètre explicite, longueur de traversée saisie indépendamment de l’épaisseur')
        s.check(J('JSON.stringify(P.slice(0,2))') == before, 'ouvrages existants intacts après la nouvelle création')
        r = J('()=>{const d=canon(migr(P[2])),R=debit(d,null);return {err:checks(d,null).filter(x=>x[0]!=="warn"),html:gen(d).length,model:!!model3(d,R)}}')
        s.check(not r['err'] and r['html']>1000 and r['model'], 'fourreau utilisable par contrôles, feuilles et visualisation existants')
        # Profil chantier / ouvrage : nul par défaut, héritage et correction, export/rechargement.
        J('()=>{dxcFermer();closeModal();el("iCh").value="CHANTIER 9C";el("iOuv").value="CUVE";openProf()}')
        s.check(pg.input_value('#prTolCourb') == '' and pg.input_value('#prTolOuv') == '', 'nouveau profil : tolérances non renseignées')
        pg.fill('#prTolCourb','10');pg.fill('#prTolOuv','3');J('saveProf()')
        s.check(J('profCh("CHANTIER 9C").tolCourb') == 10 and J('profOu("CHANTIER 9C","CUVE").tolCourb') == 3, 'tolérance chantier et modification par ouvrage enregistrées')
        exp = J('JSON.parse(projJson())')
        s.check(exp['v'] == 10 and exp['profils']['CHANTIER 9C']['tolCourb'] == 10 and len(exp['plans'][0]['origineImport']['creationCles'])>0, 'enveloppe projet inchangée ; tolérances et identité exportées')
        J('stoAttendre()');pg.reload();pg.wait_for_function('_ready')
        s.check(J('P.length') == 3 and J('profOu("CHANTIER 9C","CUVE").tolCourb') == 3, 'rechargement IndexedDB : créations / tolérances conservées')
        pg.click('#bDxi');pg.set_input_files('#dxiF', F['SUPPORT_PLAN.pdf'][0]);pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
        pg.fill('#dxiCh','CHANTIER 9C');pg.dispatch_event('#dxiCh','change')
        pg.fill('#dxiOuv','CUVE');pg.dispatch_event('#dxiOuv','change')
        J('dxcOuvrir("n",0)')
        s.check(J('dxcProposition().tolerance') == 3 and J('dxcProposition().origines.tolerance.source') == 'profil ouvrage', 'tolérance ouvrage prioritaire sur le chantier')
        pg.fill('#dxc_tolerance','2')
        s.check(J('dxcProposition().tolerance') == 2 and J('profOu("CHANTIER 9C","CUVE").tolCourb') == 3, 'correction locale de tolérance : profil inchangé avant confirmation')
        pg.fill('#dxc_tolerance','')
        s.check(J('dxcProposition().tolerance') is None, 'effacement local explicite : aucune tolérance rétablie à l’insu de l’utilisateur')
        s.check(J('dxcRep("{R01}")===dxcRep("R01")'), 'identité de réservation stable malgré la ponctuation OCR périphérique')
        s.check(pg.is_disabled('#dxcRecap') and 'déjà été créée' in pg.inner_text('#dxcEtat'), 'réimport du même PDF : identité persistante empêche une seconde création')
        pg.set_input_files('#dxiF', F['SUPPORT_PLAN.pdf'][0]);pg.wait_for_function('DXI&&DXI.fmt==="pdf"&&!document.getElementById("dxcZ")')
        s.check(J('DXC===null && P.length===3'), 'changement de fichier : brouillon retiré, projets intacts')
        s.check(not net, 'parcours complet hors connexion', str(net[:3]))
        s.check(not errs, 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    s=Suite('t_creation')
    try:t(s)
    except Exception:
        import traceback
        s.check(False,'exception',traceback.format_exc()[-2000:])
    sys.exit(0 if s.report() else 1)
