"""Régression de recette : en-têtes de grille fictifs gardés jusqu'aux preuves de création.
Les PDF réels et leurs données ne font jamais partie de ce banc.
"""
import json, sys, tempfile, traceback
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
import preparation_fictif as PF
import pdf_fictifs as PDF


def t(s):
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        b, pg, errs = open_app(pw); J=pg.evaluate; net=[]
        pg.context.route(lambda u:not u.startswith(('file:','blob:','data:')),lambda r:(net.append(r.request.url),r.abort()))
        donnees=J('''()=>{window.HEAD12=[{titre:'Ouverture (cm) H × L',cle:'ouverture',unite:'cm'},{titre:'Hauteur axe (m)',cle:'niveau',unite:'m'},
          {titre:'Note <img src=x onerror="window.inject12=1">',cle:'autre',unite:null}];
          window.ROW12={cells:{repere:'F99',ouverture:'73x127',niveau:'4,2 m'},brut:{ouverture:'73x127'},conf:{ouverture:98},corr:{},doute:{},box:{},edite:[],src:'F-L1'};
          const m={id:'F',fichier:'fictif.pdf',page:1,unite:'cm'},historique=CPI.ocr.versNomenclature([ROW12],m),n=CPI.ocr.versNomenclature([ROW12],{...m,entetesSource:HEAD12});
          const clone=JSON.parse(JSON.stringify(n));delete clone.entetesSource;
          const copie=JSON.stringify(n.entetesSource);HEAD12[0].titre='modifié';const independant=copie===JSON.stringify(n.entetesSource);HEAD12[0].titre='Ouverture (cm) H × L';
          return {identique:JSON.stringify(clone)===JSON.stringify(historique),absent:!Object.hasOwn(historique,'entetesSource'),independant,
            entetes:n.entetesSource,natif:CPI.ocr.versNomenclature([ROW12],{...m,texte:true,entetesSource:HEAD12}).entetesSource}}''')
        s.check(donnees['identique'] and donnees['absent'],'mêmes lignes et dimensions ; ancien contrat inchangé sans en-têtes source')
        s.check(donnees['independant'],'en-têtes copiés : une modification de la grille ne réécrit pas la provenance validée')
        s.check(donnees['entetes']==donnees['natif'],'provenance conservée pour OCR et grille à texte natif')
        pg.click('#bDxi');pg.set_input_files('#dxiF',PF.fichier(tmp));pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
        J('''()=>{dxiVue('p');DXI.ch='CHANTIER FICTIF RECETTE';DXI.ouv='VOILE';DXI.OC={page:1,zone:{page:1,x0:1,y0:1,x1:100,y1:100},
          titre:'Grille fictive',unite:'cm',mesures:{},rows:[ROW12],suppr:[],pdfTexte:false,src:{colonnes:HEAD12}};dxoGrille()}''')
        pg.click('#dxoV')
        s.check(J('DXI.NL.filter(({L})=>L.repere==="F99").length===1'),'validation de la grille par le vrai bouton : une seule ligne ajoutée')
        J('()=>{window.INDEX12=DXI.NL.findIndex(({L})=>L.repere==="F99");dxcOuvrir("n",INDEX12)}')
        pg.get_by_text('Données et preuves disponibles',exact=True).click()
        s.check('Ouverture (cm) H × L' in pg.inner_text('[data-entetes-source]') and 'Hauteur axe (m)' in pg.inner_text('[data-entetes-source]'),'fiche : intitulés et unités lus visibles, distincts des colonnes normalisées',pg.inner_text('[data-entetes-source]'))
        s.check(J('!window.inject12&&document.querySelectorAll("[data-entetes-source] img").length===0'),'en-têtes traités en texte, aucun HTML exécuté')
        s.check(J('dxcProposition().valeurs.L===null&&dxcProposition().valeurs.h===null'),'ordre des dimensions non déduit automatiquement de la preuve OCR')
        s.check(J('P.length===0') and pg.is_disabled('#dxcRecap'),'données insuffisantes : aucune création et récapitulatif bloqué')
        preparation=J('dxprPreparation()');J('j=>dxprReprendre(j)',json.loads(json.dumps(preparation)))
        J('()=>dxcOuvrir("n",INDEX12)')
        pg.get_by_text('Données et preuves disponibles',exact=True).click()
        s.check('Ouverture (cm) H × L' in pg.inner_text('[data-entetes-source]'),'export/reprise JSON du même PDF : en-têtes restitués dans les preuves',pg.inner_text('[data-entetes-source]'))
        pg.select_option('#dxc_type','rect');pg.select_option('#dxc_support','voile_droit');pg.fill('#dxc_L','1270');pg.fill('#dxc_h','730');pg.fill('#dxc_e','180')
        pg.select_option('#dxc_solution','simple');pg.check('#dxc_traversee');pg.click('#dxcRecap')
        s.check(J('P.length===0'),'récapitulatif des valeurs saisies explicitement : aucun ouvrage avant confirmation')
        pg.check('#dxcConfirme');pg.click('#dxcCreer')
        s.check(J('P.length===1&&P[0].origineImport.analyse.source.entetesSource[0].titre==="Ouverture (cm) H × L"'),'création confirmée : en-têtes source gardés dans origineImport')
        s.check(J('P[0].ppB===1270&&P[0].ppH===730&&P[0].ppE===180'),'valeurs fabriquées issues des saisies explicites, aucune inversion depuis l’en-tête')
        # Plusieurs textes fiables pointent vers le même contour : ils ne prouvent pas une identité commune.
        liens=J('''()=>{const avant=DXI,plans=P;try{
          const N={id:'TABLE-FICTIVE',page:1,unite:'mm',ids:[],lignes:[]},L=[11,12,13].map((n,i)=>({id:'L-FICTIVE-'+n,repere:'F'+n,rang:i+1,
            dims:{type:'rect',a:720,b:520,unite:'mm',colonne:'Largeur / Hauteur',texte:'720x520 mm'},cellules:['F'+n,'720x520'],a_verifier:[]}));N.lignes=L;
          const c={id:'CONTOUR-FICTIF',type:'rect',statut:'a_confirmer',source:{page:1},bbox:[0,0,10,8],centre:[5,4],dims:{L:10,l:8},
            geometrie:{type:'polyligne',points:[[0,0],[10,0],[10,8],[0,8]],ferme:true},annot:{},remarques:[]};
          DXI={...avant,empreinte:'EMPREINTE-FICTIVE-PARTAGE',NL:L.map(l=>({N,L:l})),NR:L.map(l=>dxnNR(l)),C:[c],R:[{}],SP:{},PR:null,CP:{},
            NA:{nomenclatures:[N],ecartes:[]},AS:Object.fromEntries(L.map(l=>[l.id,{concordance:'partielle',occurrences:[{contour:c.id,fiable:true,nature:'repere',page:1}],note:''}]))};P=[];
          DXI.SP[L[0].id]={ouverture:{},support:{type:'voile_circulaire'},provenance:{},preuves:[],incertitudes:[]};
          const a=dxnContoursLignes(),keys=L.map((_,i)=>dxcCles('n',i)),analyse=dxcAnalyse('n',0),inventaire=dxprInventaire();
          P=[{origineImport:{creationCles:keys[0]}}];const dej=L.map((_,i)=>dxcDeja(dxcCles('n',i)));
          const g=dxcNouveau('g',0),pg={detail:'aucun',valeurs:{},manquants:[]};dxcControlePreuves(g,pg,{case:()=>false,val:()=>''});
          const r={distinctes:keys.every(k=>k.length===1)&&new Set(keys.map(k=>k[0])).size===3,dej,ambigu:a.partages.every(s=>s.has(c.id)),
            support:analyse.support.type,alerte:analyse.incertitudes.join(' '),garde:pg.manquants.join(' '),contourVisible:inventaire.some(x=>x.kind==='g'&&x.i===0)};
          DXI.NR[1].geo='0';DXI.NR[1].geoT=true;const choisi=dxnContoursLignes();r.choix=choisi.liens[1].has(c.id)&&!choisi.liens[0].has(c.id)&&!choisi.liens[2].has(c.id);
          DXI.NR[0].geo='0';DXI.NR[0].geoT=true;const n=dxcNouveau('n',0),pn={detail:'aucun',valeurs:{},manquants:[]};dxcControlePreuves(n,pn,{case:()=>false,val:()=>''});r.conflit=pn.manquants.join(' ');
          DXI.NR[1].geo='';const refus=dxnContoursLignes();r.refus=refus.liens[0].has(c.id)&&!refus.liens[1].size&&!refus.partages[1].size;
          DXI.NR=L.map(l=>dxnNR(l));DXI.AS[L[1].id].occurrences=[];DXI.AS[L[2].id].occurrences=[];
          const unique=dxcCles('n',0);P=[{origineImport:{creationCles:unique}}];r.unique=unique.length===2&&dxcDeja(dxcCles('g',0))&&!dxcDeja(dxcCles('n',1));
          return r;
        }finally{DXI=avant;P=plans}}''')
        s.check(liens['distinctes'] and liens['ambigu'],'contour partagé : trois identités de ligne distinctes, rattachement explicitement ambigu')
        s.check(liens['dej']==[True,False,False],'créer une ligne ne marque pas les deux autres comme déjà créées')
        s.check(liens['support']=='inconnu' and 'plusieurs lignes' in liens['alerte'],'support issu du contour ambigu ignoré ; avertissement conservé dans les preuves')
        s.check(liens['contourVisible'] and 'plusieurs lignes' in liens['garde'],'contour partagé visible mais création isolée bloquée avant choix du rattachement')
        s.check(liens['choix'],'choix explicite unique : priorité à la ligne choisie, sans fusion des identités voisines')
        s.check('Même contour choisi explicitement' in liens['conflit'],'deux choix explicites du même contour : conflit bloquant')
        s.check(liens['refus'],'retirer un rattachement explicite est respecté, sans repli vers une association automatique')
        s.check(liens['unique'],'rattachement unique historique : lien ligne/contour et refus de doublon conservés')
        hyp=J('''()=>[3.6,8.4].map(D=>{const d=T.mk('voile',{dL:850,dl:220,dh:650,dDcuve:D}),g=voileGeo(d),R=debit(d,g),h=hypRows(d,g,R).find(x=>x[0]==='Faces cintrées');
          return {ok:g.ok,diametre:d.DcuveM,hypothese:h[1],attendu:'Ø cuve '+nf(D,2)+' m',html:gen(d)}})''')
        s.check(all(x['ok'] and x['attendu'] in x['hypothese'] and 'Ø cuve 0 m' not in x['hypothese'] for x in hyp),'hypothèses du voile : diamètre réellement saisi, ancien champ absent sans fausse cote nulle')
        s.check(all(x['attendu'] in x['html'] and 'Ø cuve 0 m' not in x['html'] for x in hyp),'feuilles générées : diamètre de cuve correct dans les hypothèses imprimées')
        s.check(not net,'aucune requête réseau');s.check(not errs,'aucune erreur JavaScript',str(errs[:2]));b.close()


def historique_pdf(s):
    """Ancien bouton de création, vrai PDF et moteur ; seuls les rapprochements sont imposés."""
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        page=PDF.Page()
        PDF.tableau(page,30,550,[('Repère',65),('Largeur (mm)',100),('Hauteur (mm)',100),('Quantité',65)],
                    [['F11','600','800','1'],['F12','900','700','1']],titre='NOMENCLATURE DES RÉSERVATIONS')
        chemin=PDF.ecrire(tmp+'/HISTORIQUE_FICTIF.pdf',[page])
        for manuel in (False,True):
            b,pg,errs=open_app(pw);J=pg.evaluate
            pg.click('#bDxi');pg.set_input_files('#dxiF',chemin)
            pg.wait_for_function('DXI&&DXI.fmt==="pdf"&&DXI.NL.length===2')
            J('''()=>{const D=DXI,c={id:'CONTOUR-FICTIF-PARTAGE',type:'rect',statut:'a_confirmer',source:{id:'FICTIF',page:1},
              bbox:[400,200,410,208],centre:[405,204],dims:{L:10,l:8},geometrie:{type:'polyligne',points:[[400,200],[410,200],[410,208],[400,208]],ferme:true},annot:{},remarques:[]};
              D.C=[c];D.R=[{conf:false,forme:'',h:'',ref:'',cotes:''}];D.ana={};D.AS={};
              D.NL.forEach(({L},k)=>{D.AS[L.id]={statut:'trouvee',concordance:'partielle',options:[{c:0}],reperes:[],preuves:[0],note:'',
                occurrences:[{page:1,x:405,y:204,texte:L.repere,source:'pdf',corrections:[],fiable:true,doutes:[],contour:c.id,cotes:[]}]};
                D.NR[k].geo='0';D.NR[k].cotes=dxnPre(k)});
              dxnLinks();dxnRefresh();dxiVue('n');
              window.candidatsHist=[];const versPlan=CPI.adaptateur.versPlan;
              CPI.adaptateur.versPlan=(c,...args)=>{candidatsHist.push(JSON.parse(JSON.stringify(c)));return versPlan(c,...args)};
            }''')
            pg.fill('#dxiCh','CHANTIER FICTIF HISTORIQUE');pg.dispatch_event('#dxiCh','change')
            pg.fill('#dxiOuv','VOILE FICTIF');pg.dispatch_event('#dxiOuv','change');pg.fill('#dxiH','230')
            s.check(all('Contour proposé à plusieurs lignes' in pg.inner_text(f'#dxnT tr[data-n="{k}"] .st') for k in (0,1)),
                    'ancien PDF : les deux lignes signalent le contour ignoré avant confirmation')
            if manuel:
                pg.select_option('#dxnT tr[data-n="0"] [data-k=geo]','0')
                s.check(J('dxnContoursLignes().liens[0].has(DXI.C[0].id)&&!dxnContoursLignes().liens[1].size'),
                        'ancien PDF : sélecteur réel, rattachement manuel unique à F11')
            for k in (0,1):pg.check(f'#dxnT tr[data-n="{k}"] [data-k=conf]')
            s.check(J('P.length===0') and not pg.is_disabled('#dxiGo'),'ancien PDF : sélection prête sans création avant confirmation')
            J('candidatsHist=[]');pg.click('#dxiGo')
            plans=J('P');centres=J('candidatsHist.slice(-2).map(c=>c.centre)')
            s.check(len(plans)==2 and [(p['ref'],p['L'],p['l'],p['h']) for p in plans]==[('F11',800,600,230),('F12',900,700,230)],
                    'ancien PDF : deux ouvrages réels, cotes distinctes du tableau préservées'+(' après choix manuel' if manuel else ' malgré l’ambiguïté'))
            s.check(centres==([[405,204],None] if manuel else [None,None]),
                    'ancien PDF : adaptateur métier alimenté seulement par le contour univoque',str(centres))
            origines=[p['origineImport'] for p in plans]
            s.check([o['geometrie']['candidat'] if o['geometrie'] else None for o in origines]==
                    (['CONTOUR-FICTIF-PARTAGE',None] if manuel else [None,None]),
                    'ancien PDF : contour absent des provenances ambiguës, attribué une seule fois après choix manuel')
            loc=[o['rapprochement']['localisations'][0] for o in origines]
            s.check([o['contour'] for o in loc]==(['CONTOUR-FICTIF-PARTAGE',None] if manuel else [None,None]) and
                    all(not o['fiable'] and o['doutes'] for o in (loc[1:] if manuel else loc)),
                    'ancien PDF : observations non rattachées signalées, aucun lien ambigu conservé comme preuve fiable')
            s.check(all(any('rattachement à clarifier' in x for x in o['a_verifier']) for o in (origines[1:] if manuel else origines)),
                    'ancien PDF : incertitude gardée dans les ouvrages créés')
            s.check(not errs,'ancien PDF : aucune erreur JavaScript',str(errs[:2]));b.close()

def support_rattache(s):
    """Supports calculés par les vrais modules ; modifications et confirmations par les contrôles réels."""
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        for cas in ('retrait','rejet','autre','partage','saisie','multivue','cote_tableau','cote_liee'):
            p=PDF.Page(1190,842)
            PDF.tableau(p,30,780,[('Repère',65),('Désignation',180),('Largeur (mm)',100),('Hauteur (mm)',100),('Quantité',65)],
                [['F11','Voile ép. 280 mm' if cas=='cote_tableau' else 'Réservation fictive','600','800','1'],
                 ['F12','Réservation fictive','900','700','1'],['F13','Réservation indépendante','700','900','1']],titre='NOMENCLATURE DES RÉSERVATIONS')
            chemin=PDF.ecrire(tmp+'/SUPPORT_RATTACHE_FICTIF.pdf',[p])
            b,pg,errs=open_app(pw,width=1500);J=pg.evaluate
            pg.add_script_tag(path=HERE+'/support_cas.js')
            pg.click('#bDxi');pg.set_input_files('#dxiF',chemin);pg.wait_for_function('DXI&&DXI.fmt==="pdf"&&DXI.NL.length===3')
            J('''cas=>{const D=DXI,courbe=['autre','partage'].includes(cas),S=[
              courbe?SC.voileCirc({Ri:6000,t:200,w:600,ouverture:'rect',k:1}):SC.voileDroit({t:200,w:600,ouverture:'rect',k:1,x:500,y:200}),
              SC.voileDroit({t:350,w:900,ouverture:'rect',k:1,x:500,y:450}),SC.voileDroit({t:280,w:700,ouverture:'rect',k:1,x:500,y:650})];
              if(cas==='multivue')S.push(SC.voileDroit({t:200,w:600,ouverture:'rect',k:1,x:850,y:500}));
              if(cas==='cote_liee')S[0].env.textes=[{id:'EP-FICTIVE',texte:'épaisseur voile = 200 mm',x:500,y:200,h:10}];
              D.C=S.map((s,i)=>{const c=s.obs.candidat;c.id='SUPPORT-FICTIF-'+i;c.annot={};const P=c.geometrie.points;c.bbox=[Math.min(...P.map(p=>p[0])),Math.min(...P.map(p=>p[1])),Math.max(...P.map(p=>p[0])),Math.max(...P.map(p=>p[1]))];return c});
              D.R=S.map(()=>({conf:false,forme:'',h:'',ref:'',cotes:''}));D.ana={};D.AS={};D.SP={};D.ch='CHANTIER FICTIF SUPPORT';D.ouv='VOILE';
              const observation=i=>({page:1,x:D.C[i].centre[0],y:D.C[i].centre[1],texte:'F'+(11+i),source:'pdf',corrections:[],fiable:true,doutes:[],contour:D.C[i].id,cotes:[]});
              D.NL.forEach(({L},k)=>{D.NR[k].geo=String(k);D.NR[k].cotes=dxnPre(k);D.AS[L.id]={statut:'trouvee',concordance:'partielle',options:D.C.map((_,c)=>({c})),reperes:[],preuves:[k],note:'',occurrences:[observation(k)]};
                const indices=cas==='multivue'&&k===0?[0,3]:[k];if(indices.length>1)D.AS[L.id].occurrences.push(observation(3));
                D.SP[L.id]=CPI.support.consolider(indices.map(i=>CPI.support.analyser(S[i].obs,S[i].env,{k:1,sag:GEO.sag,ligne:L})),{sag:GEO.sag});});
              dxnLinks();dxnRefresh();dxiVue('n');window.supportInitial=JSON.stringify(D.SP);window.keySupport=k=>dxcCles('n',k)[0];
            }''',cas)
            def ouvrir(k):
                pg.click('#dxiTabN');pg.locator(f'#dxnT tr[data-n="{k}"]').get_by_role('button',name='Proposer un coffrage').click()
            def valider(courbe=False):
                pg.check('#dxc_mesures');pg.check('#dxc_traversee')
                pg.select_option('#dxc_solution','cintre' if courbe else 'simple')
                if courbe:pg.select_option('#dxc_joues','par');pg.select_option('#dxc_largeurRef','commune')
                pg.click('#dxprValider');pg.check('#dxcConfirme');pg.click('#dxprConfirmer')
            ouvrir(2);valider();ouvrir(0)
            s.check(J('DXC.analyse.support.epaisseur_mm')==(280 if cas=='cote_tableau' else 200),cas+' : support calculé, épaisseur initiale disponible')
            if cas=='cote_liee':
                j=J('DXC.dossier.candidats.findIndex(c=>c.id==="source-e")')
                pg.locator('#dxcCible_'+str(j)).locator('..').get_by_role('button',name='Retenir cette cote').click()
            if cas=='saisie':pg.select_option('#dxc_support','voile_droit');pg.fill('#dxc_e','260')
            valider(cas in ('autre','partage'))
            pg.click('#dxprTab');pg.check('#dxprT tr[data-prep="0"] input');pg.check('#dxprT tr[data-prep="2"] input');pg.click('#dxprLot')
            s.check(J('!!DXI.PR.revision&&P.length===0'),cas+' : lot validé et récapitulé sans création')
            avant=J('dxprPreparation()')
            validation_independante=J('DXI.PR.rows[keySupport(2)].validation')
            ouvrir(0);pg.click('#dxcRecap');s.check(J('!!DXC.revision'),cas+' : récapitulatif individuel prêt avant changement')
            pg.click('#dxiTabN')
            if cas=='partage':
                pg.select_option('#dxnT tr[data-n="0"] [data-k=geo]','0')
                pg.select_option('#dxnT tr[data-n="1"] [data-k=geo]','0')
                s.check(J('dxnContoursLignes().conflits.size===2&&dxcAnalyse("n",0).support.type==="inconnu"&&dxcAnalyse("n",1).support.type==="inconnu"'),
                        'partage : double rattachement explicite, supports périmés ignorés et conflit bloquant')
            choix='rej' if cas=='rejet' else '1' if cas=='autre' else '3' if cas=='multivue' else ''
            pg.select_option('#dxnT tr[data-n="0"] [data-k=geo]',choix)
            s.check(J('!DXC.revision&&!DXC.validation&&!DXI.PR.revision&&!DXI.PR.selection.includes(keySupport(0))&&P.length===0'),
                    cas+' : récapitulatifs, validation et sélection invalidés avant toute création')
            s.check(J('DXI.PR.rows[keySupport(2)].validation')==validation_independante and J('dxcAnalyse("n",2).support.epaisseur_mm===280'),
                    cas+' : autre ligne, support et validation indépendants conservés')
            s.check(J('JSON.stringify(DXI.SP)===supportInitial'),cas+' : résultats bruts non détruits, filtrage des dépendances à la lecture')
            pg.locator('#dxcZ').get_by_text('Données et preuves disponibles',exact=True).click()
            s.check(pg.locator('#dxcIncertitudes').count()==1 and 'rattachement actuel' in pg.inner_text('#dxcIncertitudes') and 'À revalider' in pg.inner_text('#dxprValidation') and
                    pg.inner_text('#dxcPreuves')==J('JSON.stringify(DXC.analyse.preuves,null,2)'),cas+' : preuves et statut de la fiche déjà ouverte actualisés')
            attendu=200 if cas=='multivue' else 280 if cas=='cote_tableau' else None
            a=J('dxcAnalyse("n",0)')
            s.check(a['support'].get('epaisseur_mm')==attendu and a['support'].get('rayon_interieur_mm') is None and
                    a['support']['type']==('voile_droit' if cas=='multivue' else 'inconnu'),cas+' : analyse actuelle sans support ni rayon du contour retiré')
            s.check(any('rattachement actuel' in x for x in a['incertitudes']) and
                    not any(x.get('contour')=='SUPPORT-FICTIF-0' for x in a.get('observations',[a.get('observation',{})])),
                    cas+' : incertitude visible et observations périmées absentes de l’analyse utilisée')
            if cas=='partage':s.check(J('dxnContoursLignes().liens[1].has("SUPPORT-FICTIF-0")&&dxcAnalyse("n",1).support.type==="inconnu"'),
                    'attribution à F12 : aucun transfert du support calculé pour F11 et aucun repli sur le précédent contour de F12')
            ouvrir(0);pg.check('#dxc_mesures')
            valeur=260 if cas=='saisie' else attendu
            s.check(J('dxcProposition().valeurs.e')==valeur and J('dxcProposition().valeurs.R===null'),
                    cas+' : confirmer les mesures ne ressuscite aucune cote géométrique périmée')
            s.check(J('dxcProposition().valeurs.L===600&&dxcProposition().valeurs.h===800'),cas+' : cotes indépendantes de nomenclature conservées')
            if cas=='multivue':s.check(a.get('observation',{}).get('contour')=='SUPPORT-FICTIF-3' and a['preuves'],
                    'multivue : observation encore liée et ses preuves préservées, sans dupliquer les formules métier')
            if cas=='cote_tableau':s.check(a['provenance']['support.epaisseur_mm']['source']=='nomenclature',
                    'cote écrite indépendante : épaisseur de nomenclature et provenance conservées')
            if valeur is None:s.check(pg.is_disabled('#dxcRecap'),cas+' : création bloquée tant que les données nécessaires manquent')
            # Export par le bouton réel ; les supports actifs exportés sont filtrés, même si le cache brut est conservé.
            pg.click('#dxprTab')
            with pg.expect_download() as dl:pg.get_by_text('Exporter la préparation',exact=True).click()
            prepare=json.load(open(dl.value.path(),encoding='utf8'))
            ligne=J('DXI.NL[0].L.id')
            analyse_exportee=J('dxrJSON().supports.find(x=>x.ligne===DXI.NL[0].L.id).support')
            s.check(analyse_exportee.get('epaisseur_mm')==attendu and analyse_exportee.get('rayon_interieur_mm') is None,
                    cas+' : export d’analyse historique sans support périmé')
            s.check(prepare['source']['SP'][ligne]['support'].get('epaisseur_mm')==attendu and
                    prepare['source']['SP'][ligne]['support'].get('rayon_interieur_mm') is None,
                    cas+' : export sans épaisseur ni rayon périmés')
            # Reprendre aussi un ancien export : il contient encore l’ancien SP et d’anciennes validations.
            ancien=json.loads(json.dumps(avant));ancien['source']['NR']=prepare['source']['NR']
            fichier=tmp+'/REPRISE_SUPPORT_FICTIVE.json'
            with open(fichier,'w',encoding='utf8') as f:json.dump(ancien,f)
            pg.set_input_files('#dxprFichier',fichier);pg.wait_for_function('dxprBase().message.includes("reprise")')
            s.check(J('P.length===0&&!DXI.PR.rows[keySupport(0)].validation&&dxcAnalyse("n",0).support.rayon_interieur_mm==null') and
                    J('dxcAnalyse("n",0).support.epaisseur_mm??null')==attendu,
                    cas+' : reprise ancienne, preuves filtrées et validation périmée refusée')
            s.check(J('dxprCalcul(DXI.PR.rows[keySupport(0)]).p.valeurs.e')==(260 if cas=='saisie' else attendu),
                    cas+' : reprise ancienne sans réutilisation d’une cote retenue dépendante du contour retiré')
            with open(fichier,'w',encoding='utf8') as f:json.dump(prepare,f)
            pg.set_input_files('#dxprFichier',fichier);pg.wait_for_function('dxprBase().message.includes("reprise")');ouvrir(0)
            s.check(J('dxcProposition().valeurs.e')==(260 if cas=='saisie' else attendu),cas+' : export/reprise actuel sans réapparition de l’ancienne épaisseur')
            pg.select_option('#dxc_support','voile_droit');pg.select_option('#dxc_solution','simple');pg.check('#dxc_traversee')
            if cas=='multivue':pg.check('#dxc_mesures')
            if valeur is None:pg.fill('#dxc_e','260')
            if cas=='saisie':s.check(pg.input_value('#dxc_e')=='260' and J('DXC.saisiesBrutes.e==="260"'),
                    'saisie explicite confirmée : valeur et provenance préservées après retrait et reprise')
            pg.click('#dxcRecap');pg.check('#dxcConfirme');pg.click('#dxcCreer')
            s.check(J('P.length===1&&P[0].forme==="para"&&P[0].ppB===600&&P[0].ppH===800') and
                    J('P[0].ppE')==(valeur if valeur is not None else 260),cas+' : vraie création avec les seules données actuelles ou saisies explicitement')
            s.check(J('P[0].origineImport.analyse.support.rayon_interieur_mm==null&&P[0].origineImport.proposition.valeurs.R===null&&P[0].origineImport.confirmation_utilisateur'),
                    cas+' : provenance de création sans ancien rayon ni validation automatique')
            J('dxcCreer()');s.check(J('P.length===1') and pg.is_disabled('#dxcRecap'),cas+' : double validation et nouvelle création de la même réservation refusées')
            s.check(not errs,cas+' : aucune erreur JavaScript',str(errs[:2]));b.close()


if __name__=='__main__':
    s=Suite('t_recette_pdf')
    try:t(s);historique_pdf(s);support_rattache(s)
    except Exception:s.check(False,'exception',traceback.format_exc()[-2200:])
    sys.exit(0 if s.report() else 1)
