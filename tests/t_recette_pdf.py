"""Régression de recette : en-têtes de grille fictifs gardés jusqu'aux preuves de création.
Les PDF réels et leurs données ne font jamais partie de ce banc.
"""
import json, sys, tempfile, traceback
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
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


if __name__=='__main__':
    s=Suite('t_recette_pdf')
    try:t(s);historique_pdf(s)
    except Exception:s.check(False,'exception',traceback.format_exc()[-2200:])
    sys.exit(0 if s.report() else 1)
