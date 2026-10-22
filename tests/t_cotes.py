"""Phase 10A : association conservatrice, preuves, conflits et création réelle confirmée."""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
import cotes_fictifs as CF


def t(s):
    fichiers = CF.fichiers(tempfile.mkdtemp())
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1600)
        J = pg.evaluate
        net = []
        pg.context.route(lambda u: not u.startswith(('file:', 'blob:', 'data:')), lambda r: (net.append(r.request.url), r.abort()))
        J('''()=>{window.T10=(texte,id='t1',page=2)=>({id,texte,page,x:100,y:300,w:160,h:8});
          window.V10=[{id:'COUPE',page:2,titre:'Coupe fictive',region:[0,0,500,500],echelle:{valeur:20}}];
          window.A10={ouverture:{type:'carre',largeur_suivant_paroi_mm:500,hauteur_mm:500},support:{type:'voile_droit'},
            provenance:{'ouverture.largeur_suivant_paroi_mm':{origine:'cote_explicite',detail:'500x500'},
              'ouverture.hauteur_mm':{origine:'cote_explicite',detail:'500x500'}},source:{page:1,uniteRetenue:'mm'}};
          window.C10=(textes=[],extra={})=>CPI.cotesPreuves.analyser(Object.assign({analyse:A10,repere:'R01',textes,vues:V10,
            occurrences:[{page:2,vue:'COUPE',fiable:true}]},extra));}''')
        analyse = lambda textes, extra={}: J('x=>C10(x[0].map((v,i)=>T10(v,"T"+i)),x[1])', [textes, extra])
        r = analyse(['R01 : épaisseur du voile = 20 cm'])
        s.check(len(r['candidats']) == 3 and r['candidats'][0]['automatique'], 'nomenclature explicite conservée sans mesure graphique')
        e = r['candidats'][-1]
        s.check(e['valeur_mm'] == 200 and e['unite'] == 'cm' and e['brut'].endswith('20 cm') and e['champ'] == 'e'
                and e['statut'] == 'exploitable' and e['vue'] == 'COUPE', 'épaisseur nommée avec repère exact, coupe, brut et conversion cm conservés')
        r = analyse(['épaisseur du voile = 20 cm'])
        s.check(r['candidats'][-1]['statut'] == 'a_confirmer' and not r['candidats'][-1]['automatique'], 'même vue et proximité : lien insuffisant pour attribuer automatiquement')
        r = analyse(['20 cm'], dict(occurrences=[]))
        s.check(r['candidats'][-1]['champ'] == 'autre' and not r['candidats'][-1]['automatique'], 'cote isolée sans lien : rôle inconnu, valeur disponible pour relecture')
        r = analyse(['R01 : épaisseur du voile = 20 cm', 'R01 : épaisseur du voile = 300 mm'])
        s.check(r['conflits'][0]['valeurs'] == [200,300] and all(c['statut'] == 'contradictoire' for c in r['candidats'] if c['champ']=='e'), 'deux valeurs incompatibles : toutes les preuves gardées, aucun choix automatique')
        for unite, val in [('mm','200'),('cm','20'),('m','0,2')]:
            r=analyse([f'R01 : épaisseur du voile = {val} {unite}'])
            s.check(r['candidats'][-1]['valeur_mm'] == 200, 'unité explicite convertie : '+unite)
        r=analyse(['R01 : épaisseur du voile = 20'])
        s.check(r['candidats'][-1]['valeur_mm'] is None and r['candidats'][-1]['statut']=='inconnu', 'unité absente : aucun millimètre ni unité de cartouche inventé')
        r=analyse(['R01 : épaisseur du voile = 20 cm'], dict(homonyme=True))
        s.check(not r['candidats'][-1]['automatique'] and r['candidats'][-1]['statut']=='a_confirmer', 'deux lignes homonymes : repère seul insuffisant')
        r=analyse(['R01 épaisseur du voile = 20 cm ; R02 épaisseur du voile = 30 cm'])
        s.check(not any(c['automatique'] for c in r['candidats'] if c['champ']=='e'), 'annotation à plusieurs repères : portée ambiguë, aucune attribution silencieuse')
        r=J('C10([Object.assign(T10("R01 : épaisseur du voile = 20 cm"),{ocr:{conf:70,brut:"R01...",corrections:[]}})])')
        s.check(not r['candidats'][-1]['automatique'] and r['candidats'][-1]['source']['ocr']['conf']==70, 'OCR incertain : preuve gardée, validation requise')
        r=J("""C10([Object.assign(T10('R01 : épaisseur du voile = 20 cm'),{ocr:{conf:96,brut:'R01 : épaisseur du voile = 2O cm',corrections:['O → 0']}})])""")
        s.check(r['candidats'][-1]['brut'].endswith('2O cm') and r['candidats'][-1]['lecture'].endswith('20 cm')
                and not r['candidats'][-1]['automatique'], 'OCR corrigé : brut réellement conservé, lecture distincte et confirmation requise')
        r=analyse(['R01 : diamètre intérieur = 12 m', 'R01 : rayon extérieur = 6 m', 'R01 : largeur développée = 1 m'])
        s.check(all(not c['automatique'] for c in r['candidats'][2:]), 'diamètre intérieur, rayon extérieur et développé ne sont pas assimilés au rayon intérieur ou à la corde')
        s.check(J('''()=>{const d=C10([T10('R01 : diamètre intérieur = 12 m')]);return CPI.cotesPreuves.affecter(d,d.candidats.at(-1).id,'R')}''') is None,
                'affectation diamètre vers rayon intérieur refusée sans transformation implicite')
        s.check(J("""()=>{const d=C10([T10('R01 : largeur développée = 1 m')]);return CPI.cotesPreuves.affecter(d,d.candidats.at(-1).id,'L')}""") is None,
                'développé refusé comme corde même par affectation explicite')
        r=analyse(['R01 cuve Ø12 m', 'R01 réservation Ø200 mm'])
        s.check(not r['candidats'][-2]['automatique'] and r['candidats'][-1]['champ']=='D' and r['candidats'][-1]['automatique'],
                'diamètre de cuve non attribué à l’ouverture ; diamètre de réservation nommé utilisable')
        r=analyse(['R01 : chanfrein à 45 degrés, 10 cm'])
        s.check(len(r['details'])==1 and not r['details'][0]['fabrication_disponible'], 'chanfrein textuel conservé avec preuve et fabrication indisponible')
        r=analyse([],dict(contours=[dict(id='poly',type='polygone',source=dict(page=2))]))
        s.check(r['details'][0]['type']=='forme_non_reconnue', 'forme non reconnue conservée comme incertitude, pas comme rectangle')
        r=J('''()=>C10([T10('R01 : épaisseur du voile = 20 cm','a',1),T10('R01 : hauteur = 1 m','b',2)],
          {vues:[...V10,{id:'PLAN',page:1,region:[0,0,500,500],echelle:{valeur:50}}]})''')
        s.check([c['vue'] for c in r['candidats'][2:]]==['PLAN','COUPE'] and [c['valeur_mm'] for c in r['candidats'][2:]]==[200,1000],
                'repère multivues, échelles 1/50 et 1/20 : cotes écrites indépendantes des échelles')
        r=J('''()=>CPI.creation.proposer({ouverture:{type:'rect',largeur_suivant_paroi_mm:500},support:{},
          provenance:{'ouverture.largeur_suivant_paroi_mm':{origine:'mesure'}}},{},{mesuresConfirmees:false})''')
        s.check(r['valeurs']['L'] is None, 'mesure graphique sans échelle confirmée toujours inutilisable')
        # Lecteur PDF réel, sans injecter de cotes dans l'analyse ni le projet.
        def ouvrir(nom):
            if J('!!DXI'): J('dxiQuit();closeModal()')
            pg.click('#bDxi');pg.set_input_files('#dxiF',fichiers[nom]);pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
            J('()=>{DXI.ch="CHANTIER FICTIF 10A";DXI.ouv="VOILE";dxcOuvrir("n",DXI.NL.findIndex(x=>x.L.repere==="R01"))}')
        ouvrir('COTES')
        avant=J('JSON.stringify({P,PROF})')
        s.check(pg.input_value('#dxc_e')=='200' and pg.input_value('#dxc_L')=='500', 'PDF lu réellement : épaisseur explicitement rattachée et cote de nomenclature préremplies')
        eidx=J('DXC.dossier.candidats.findIndex(c=>c.origine==="texte"&&c.champ==="e")')
        J('j=>dxcVoirCote(j)', eidx);pg.wait_for_function('document.querySelector("#dxpO .hl")')
        s.check(J('DXI.ohl.page')==1 and pg.locator('#dxpO .hl').count()>0, 'source retrouvée via le surlignage existant du PDF')
        J('j=>dxcAffecter(j)', eidx)
        pg.fill('#dxc_e','21 cm');pg.select_option('#dxc_support','voile_droit');pg.check('#dxc_traversee');pg.select_option('#dxc_solution','simple')
        pg.click('#dxcRecap')
        s.check(J('JSON.stringify({P,PROF})')==avant and pg.is_disabled('#dxcCreer'), 'retenir / corriger / récapituler ne modifie pas le projet')
        pg.check('#dxcConfirme');pg.fill('#dxc_e','22 cm')
        s.check(pg.locator('#dxcConfirme').count()==0 and J('P.length')==0, 'correction après récapitulatif invalide la confirmation finale')
        pg.click('#dxcRecap');pg.check('#dxcConfirme');pg.click('#dxcCreer')
        s.check(J('P.length===1&&P[0].ppE===220'), 'création unique explicite avec cote corrigée')
        preuve=J('P[0].origineImport')
        s.check(preuve['cotesPdf']['retenues']['e']['candidate']['unite']=='cm' and preuve['proposition']['origines']['e']['brut']=='22 cm'
                and preuve['proposition']['origines']['e']['avant']['valeur']==200, 'preuve brute, unité, rôle confirmé et correction manuelle conservés')
        s.check(J('JSON.parse(projJson()).v===10&&JSON.parse(projJson()).plans[0].origineImport.cotesPdf.retenues.e.valeur===200'), 'export JSON v10 conserve les preuves sans migration')
        J('dxcCreer()')
        s.check(J('P.length')==1, 'validation répétée ne crée pas de doublon')
        J('stoAttendre()');pg.reload();pg.wait_for_function('_ready')
        s.check(J('P[0].origineImport.proposition.origines.e.brut')=='22 cm', 'rechargement IndexedDB conserve correction et preuves')
        sauvegarde=J('projJson()')
        J('txt=>loadText(txt,"fictif-10a.json",null)',sauvegarde)
        J('dlgEnd(true)');J('stoAttendre()')
        s.check(J('P.length===1&&P[0].origineImport.cotesPdf.retenues.e.candidate.unite==="cm"&&P[0].origineImport.proposition.origines.e.brut==="22 cm"'),
                'réimport JSON réel conserve la preuve, le rôle et la correction')
        ouvrir('COTES')
        s.check(pg.is_disabled('#dxcRecap') and 'déjà été créée' in pg.inner_text('#dxcEtat'), 'réimport du même PDF toujours bloqué par identité de ligne')
        ouvrir('CONFLIT')
        s.check(pg.input_value('#dxc_e')=='' and pg.is_disabled('#dxcRecap'), 'PDF deux coupes contradictoires : aucun choix automatique')
        pg.select_option('#dxc_support','voile_droit');pg.fill('#dxc_e','250');pg.check('#dxc_traversee');pg.select_option('#dxc_solution','simple')
        s.check(pg.is_disabled('#dxcRecap'), 'saisie seule ne résout pas silencieusement une contradiction')
        J('dxcArbitrer("e")')
        s.check(not pg.is_disabled('#dxcRecap'), 'arbitrage explicite permet le récapitulatif')
        pg.fill('#dxc_e','260')
        s.check(pg.is_disabled('#dxcRecap'), 'modifier une cote arbitrée impose un nouvel arbitrage')
        j=J('DXC.dossier.candidats.findIndex(c=>c.champ==="e"&&c.valeur_mm===300)')
        J('j=>dxcAffecter(j)',j)
        s.check(not pg.is_disabled('#dxcRecap') and J('dxcProposition().valeurs.e')==300, 'sélection explicite d’une preuve contradictoire résout le conflit sans effacer les autres preuves')
        ouvrir('DETAIL')
        pg.select_option('#dxc_support','voile_droit');pg.check('#dxc_traversee');pg.select_option('#dxc_solution','simple')
        J('dxcRecap();dxcCreer()')
        s.check(pg.is_disabled('#dxcRecap') and J('P.length')==1 and len(J('DXC.dossier.details'))==1, 'chanfrein explicite interdit une fabrication standard incorrecte même par appel direct')
        s.check(J('Object.values(DXI.CP).some(d=>d.details.length)') and 'étude de fabrication' in pg.inner_text('#dxcEtat'), 'dossier du détail non créé disponible dans l’export de l’analyse')
        ouvrir('CONFLIT');J('dxcArbitrer("e")')
        pg.check('#dxc_detail');pg.fill('#dxc_detailNote','Forme irrégulière non qualifiée')
        s.check(J('dxcProposition().cotesPdf.detailUtilisateur')=='Forme irrégulière non qualifiée' and pg.is_disabled('#dxcRecap'), 'signalement utilisateur d’une forme inhabituelle conservé et bloquant')
        s.check(not net, 'analyse, preuves et création hors connexion', str(net[:3]))
        s.check(not errs, 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__=='__main__':
    s=Suite('t_cotes')
    try:t(s)
    except Exception:
        import traceback
        s.check(False,'exception',traceback.format_exc()[-2200:])
    sys.exit(0 if s.report() else 1)
