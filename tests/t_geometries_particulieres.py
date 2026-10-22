"""Phase 10B : géométries et PDF fictifs, contrôles indépendants des dimensions fabriquées."""
import base64, json, os, sys, tempfile, traceback
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.shape
from t_v30 import glb
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
import pdf_fictifs as PF
import support_fictifs as SF


def t(s):
    with tempfile.TemporaryDirectory() as dossier, sync_playwright() as pw:
        pdf=PF.Page(1190,842)
        SF.plan(pdf)
        for y, texte in [(500,'R01 : largeur feuillure = 40 mm'),
                         (480,'R01 : profondeur feuillure = 30 mm'),
                         (460,'R01 : depart feuillure = 20 mm'),
                         (440,'R01 : largeur feuillure = 50 mm'),
                         (420,'R01 : depart feuillure = 0 mm')]:
            pdf.texte(70,y,texte,10)
        fichier=PF.ecrire(os.path.join(dossier,'FEUILLURE_FICTIVE.pdf'),[pdf])
        b, pg, errs=open_app(pw,width=1600)
        J=pg.evaluate
        pg.click('#bDxi');pg.set_input_files('#dxiF',fichier)
        pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
        J('()=>{DXI.ch="CHANTIER FICTIF 10B";DXI.ouv="VOILE";dxcOuvrir("n",DXI.NL.findIndex(x=>x.L.repere==="R01"))}')
        before=J('JSON.stringify({P,PROF,LIBU})')
        s.check(J('DXC.dossier.details.length')>=3,'preuves du détail retrouvées par le lecteur PDF réel')
        s.check(J('DXC.dossier.conflits.some(x=>x.champ==="fL")'),'largeurs de feuillure contradictoires conservées')
        s.check(pg.is_disabled('#dxcRecap'),'détail non qualifié : aucune création standard')
        pg.select_option('#dxc_type','rect');pg.select_option('#dxc_support','voile_droit')
        pg.select_option('#dxc_solution','simple');pg.check('#dxc_traversee')
        for k,v in dict(L=600,h=800,e=240).items():pg.fill('#dxc_'+k,str(v))
        pg.select_option('#dxc_geometrie','feuillure')
        s.check(pg.is_visible('#dxc_fL') and pg.is_disabled('#dxcRecap'),'feuillure sélectionnée : dimensions manquantes et qualification bloquantes')
        for k,v in dict(fL=40,fH=30,fNiv=20).items():pg.fill('#dxc_'+k,str(v))
        pg.check('#dxc_qualification')
        s.check(pg.is_disabled('#dxcRecap'),'qualification ne contourne pas une contradiction non arbitrée')
        J('dxcArbitrer("fL")')
        pg.fill('#dxc_fNiv','0');J('dxcArbitrer("fNiv")')
        s.check(J('dxcProposition().valeurs.fNiv')==0 and not pg.is_disabled('#dxcRecap'),'départ zéro : cote PDF explicite et arbitrage manuel valides, conflit conservé')
        pg.fill('#dxc_fNiv','20')
        s.check(pg.is_disabled('#dxcRecap'),'nouvelle correction du départ invalide son arbitrage')
        J('dxcArbitrer("fNiv")')
        s.check(not pg.is_disabled('#dxcRecap'),'dimensions, qualification et arbitrage explicites permettent le récapitulatif')
        s.check(pg.locator('#dxcGeo svg').count()==3 and 'depuis le linteau' in pg.inner_text('#dxcQualification'),'aperçu coté et convention du départ depuis A visibles avant confirmation')
        s.check(J('JSON.stringify({P,PROF,LIBU})')==before,'proposition et aperçu sans mutation du projet')
        J('window.G10P=dxcProposition();window.G10M=DXI.M.para')
        r=J('''()=>{const p=G10P,prop=s=>CPI.creation.proposer(DXC.analyse,Object.assign({},DXC.saisie,{traversee:true},s));
          return {sans:CPI.creation.preparer(p,{},{}),zero:prop({fL:0}),neg:prop({fNiv:-1}),
            manque:prop({fH:null}),depasse:prop({fNiv:230}),courbe:prop({support:'voile_circulaire'}),
            inconnu:prop({detail:'autre'}),depart0:prop({fNiv:0})}}''')
        for k in ['zero','neg','manque','depasse','courbe','inconnu']:
            s.check(bool(r[k]['manquants']),'paramètre invalide bloqué : '+k)
        s.check(not r['sans']['ok'] and r['depart0']['valeurs']['fNiv']==0,'confirmation obligatoire ; départ zéro explicite autorisé')
        pg.click('#dxcRecap');J('dxcCreer()')
        s.check(J('P.length')==0,'récapitulatif et appel sans confirmation : aucune création')
        pg.check('#dxcConfirme');pg.fill('#dxc_fH','31')
        s.check(pg.locator('#dxcConfirme').count()==0,'correction après récapitulatif invalide la confirmation')
        pg.fill('#dxc_fH','30');pg.click('#dxcRecap');pg.check('#dxcConfirme');pg.click('#dxcCreer')
        J('dxcCreer();window.G10D=canon(migr(P[0]))')
        s.check(J('P.length')==1 and pg.is_disabled('#dxcRecap'),'création unique et validations répétées refusées')
        s.check(J('[G10D.forme,G10D.ppB,G10D.ppH,G10D.ppE,G10D.h,G10D.feuilTraversee,G10D.fL,G10D.fH,G10D.fNiv]')==['para',600,800,240,800,True,40,30,20], 'dimensions métier : hauteur réelle 800, traversée 240 ; aucune rotation implicite du contrôle mécanique')
        s.check(J('P[0].origineImport.proposition.detail==="feuillure"&&P[0].origineImport.proposition.qualificationFeuillure&&P[0].origineImport.cotesPdf.conflits.length>0'),'qualification, preuves et contradiction arbitrée conservées')
        s.check(J('''()=>{const d={...G10D,ppTr:false},R=debit(d,null),S=model3(d,R).solids.filter(x=>x.nm==='feuillure traversante');return S.map(x=>x.role).join('|')==='base|top|wall|wall'&&S.slice(2).every(x=>x.exv[0]===0&&x.exv[2]===0)}'''),'éclaté sans traverses : chaque tasseau suit son panneau, sans vecteur hérité')
        r=J('''()=>{const d=G10D;return [
          {fL:0},{fH:-1},{fNiv:-1},{fNiv:null},{fNiv:220},{ppA:1},{ppBe:1}
          ].map(v=>checks({...d,...v},null).filter(x=>x[0]!=='warn'))}''')
        s.check(all(r),'moteur : bornes, départ obligatoire, dépassement, biais et pente rejetés même hors interface')
        r=J('''()=>{const d=G10D,R=debit(d,null),M=model3(d,R),B=bimModel(d),bois=M.solids.filter(x=>x.nm==='feuillure traversante');
          window.G10R=R;window.G10S=M;
          return {err:checks(d,null).filter(x=>x[0]!=='warn'),cp:R.map(x=>({q:x.q,a:x.a,b:x.b,k:x.k})),
            bois:R.bois.filter(x=>/feuillure/.test(x.n)).map(x=>({q:x.q,L:x.L,n:x.n})),
            bounds:bois.map(bb3),volumes:bois.map(x=>bimVol(bimGeo([x]))),
            bim:B.pcs.filter(x=>x.nm==='feuillure traversante').map(x=>({vol:bimVol(x.geo),k:x.k,q:x.qty})),
            html:gen(d),svg:render3(M,800,600,30).svg,gab:gabPieces(d,'roll')}}''')
        s.check(not r['err'],'contrôles de fabrication acceptent la variante complète',str(r['err']))
        cp=sorted((x['q'],max(x['a'],x['b']),min(x['a'],x['b'])) for x in r['cp'] if x['k']=='j')
        s.check(cp==[(2,600,240),(2,764,240)],'CP : 2 panneaux 600×240 et 2 panneaux 764×240 (800 − 2×18)',str(cp))
        s.check([(x['q'],x['L']) for x in r['bois']]==[(2,680),(2,800)] and all('40×30' in x['n'] for x in r['bois']),'4 tasseaux réemployés du rect : 2×680 et 2×800, section 40×30',str(r['bois']))
        expect=sorted([[20,-340,-440,50,340,-400],[20,-340,400,50,340,440],
                       [20,-340,-400,50,-300,400],[20,300,-400,50,340,400]])
        s.check(sorted(r['bounds'])==expect,'3D : tasseaux hors vide, seulement entre X=20 et X=50, ouvertures A/B intactes',str(r['bounds']))
        s.check(sorted(r['volumes'])==[816000,816000,960000,960000],'volumes 3D indépendants du débit : 680/800 × 40 × 30',str(r['volumes']))
        s.check(len(r['bim'])==4 and sorted(x['vol'] for x in r['bim'])==sorted(r['volumes']) and all(x['k']=='bois' for x in r['bim']),'BIM : mêmes quatre tasseaux et volumes que la 3D',str(r['bim']))
        s.check('FEUILLURE TRAVERSANTE' in r['html'] and '4 tasseaux' in r['html'] and '<path' in r['svg'],'feuille cotée dédiée, montage et représentation vectorielle du modèle complet', str({k:(v if not isinstance(v,str) else [len(v), 'FEUILLURE TRAVERSANTE' in v,'4 tasseaux' in v,'<svg' in v]) for k,v in r.items() if k in ['html','svg']}))
        rnest=J('''()=>{const N=cpNest(G10D,G10R);return Object.values(N).flatMap(g=>g.sheets.flatMap(s=>s.map(p=>[p.w,p.h])))}''')
        s.check(len(rnest)==4 and sorted(sorted(x) for x in rnest)==sorted([[240,600],[240,600],[240,764],[240,764]]),'imbrication : quatre découpes CP aux dimensions du débit',str(rnest))
        dessin=J('''()=>{const v=feuilTraverseVues(G10D),q=document.createElement('div');q.innerHTML=v.top+v.a+v.b;
          return {text:q.textContent,ratios:[...q.querySelectorAll('svg:first-child rect[fill="#f0e8d0"]')].map(r=>+r.getAttribute('width')/+r.getAttribute('height'))}}''')
        s.check(len(dessin['ratios'])==4 and all(abs(a-b)<1e-8 for a,b in zip(dessin['ratios'],[17,17,.05,.05]))
                and all(str(n) in dessin['text'] for n in [600,800,240,40,30,20]),'2D : quatre tasseaux aux rapports 680/40 et 40/800, cotes du vide et de pose identiques au modèle 3D',str(dessin))
        s.check(not r['gab'].get('pieces'),'pièces à coupes droites : cotes de débit, aucun faux gabarit cintré')
        r=J('''()=>{const dx=dxfPlanFile(G10D),bb=bimModel(G10D),i=ifcFile(G10D);return {dxerr:dx.err||null,txt:new TextDecoder('windows-1252').decode(dx.bytes),ifcerr:i.err||null,ifclen:(i.txt||i.text||'').length,bim:bb.err||null}}''')
        s.check(not r['dxerr'] and 'feuillure' in r['txt'].lower() and not r['bim'] and not r['ifcerr'],'DXF inclut la feuillure et BIM/IFC accepte le modèle',str({k:v for k,v in r.items() if k!='txt'}))
        # Relire les géométries exportées, pas seulement vérifier l'existence des fichiers.
        r=J("""async()=>{const b64=u=>{let s='';for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode(...u.subarray(i,i+8192));return btoa(s)};
          return {ifc:b64(ifcFile(G10D).bytes),glb:b64((await glbFile(G10D,false)).bytes),tags:G10R.bois.filter(x=>/feuillure/.test(x.n)).map(x=>x.ftag)}}""")
        ifc=ifcopenshell.file.from_string(base64.b64decode(r['ifc']).decode('utf-8'))
        settings=ifcopenshell.geom.settings()
        bois=[x for x in ifc.by_type('IfcMember') if x.Tag in r['tags']]
        volumes=sorted(ifcopenshell.util.shape.get_volume(ifcopenshell.geom.create_shape(settings,x).geometry) for x in bois)
        s.check(len(volumes)==4 and all(abs(a-b)<1e-9 for a,b in zip(volumes,[.000816,.000816,.000960,.000960])), 'IFC relu par ifcopenshell : volumes réels des quatre tasseaux',str(volumes))
        ok, js, volumes, bounds=glb(base64.b64decode(r['glb']))
        vv=sorted(v for nom,vs in volumes.items() if any(tag in nom for tag in r['tags']) for v in vs)
        s.check(ok and len(vv)==4 and all(abs(a-b)<1e-9 for a,b in zip(vv,[.000816,.000816,.000960,.000960])), 'GLB relu : quatre maillages de tasseaux, volumes exacts en m³',str(vv))
        J('closeModal();open3D(G10D)');pg.wait_for_function('V3D.gl===true&&GL3.objs.length>0')
        s.check(J("GL3.objs.filter(x=>x&&x.o.nm==='feuillure traversante'&&x.mesh.geometry.attributes.position.count>0).length") == 4,'WebGL : les quatre tasseaux du modèle partagé sont rendus')
        J('close3D()')
        # Comparaison de l'import confirmé avec le formulaire manuel, puis aller-retour exact.
        r=J('''()=>{const d=P[0];setForm(d);return {sum:T.sum(d),manual:T.sum(coll()),flag:coll().feuilTraversee}}''')
        s.check(r['flag'] and r['sum']==r['manual'],'édition manuelle : paramètres et débit exactement restitués',json.dumps(r,ensure_ascii=False))
        r=J('''()=>{const d=JSON.parse(projJson());window.G10JSON=d;return {v:d.v,plan:d.plans[0],sum:T.sum(d.plans[0]),origine:d.plans[0].origineImport}}''')
        s.check(r['v']==10 and r['plan']['feuilTraversee'] and r['sum']==J('T.sum(P[0])') and r['origine']['confirmation_utilisateur'],'JSON v10 : métier et preuves restituent le même ouvrage')
        J('stoAttendre()');pg.reload();pg.wait_for_function('_ready')
        s.check(J('P.length===1&&P[0].feuilTraversee&&P[0].fNiv===20&&P[0].origineImport.proposition.detail==="feuillure"'),'IndexedDB : rechargement du détail et de la confirmation')
        # Géométrie B : tous les coins, dimensions indépendantes, pas de débit rectangulaire de repli.
        r=J("""()=>{const g=CPI.geometriesParticulieres.chanfrein45,p={L:600,e:240,H:800,retrait:40,ep:18,angle:'GA',orientation:'vers_beton'};
          return {coins:['GA','DA','DB','GB'].map(angle=>g({...p,angle},{L:{origine:'saisie'}})),
            invalides:[{retrait:0},{retrait:-1},{retrait:240},{retrait:null},{angle:''},{ep:null},{orientation:''},{L:Infinity},{H:NaN}].map(x=>g({...p,...x}))}}""")
        for g in r['coins']:
            s.check(len(g['sommets'])==5 and len(g['faces'])==7 and g['aire']==143200 and g['volume']==114560000 and not g['fabricable'] and not g['erreurs'], 'pentagone constant, aire et volume indépendants : '+g['parametres']['angle'])
            volume=J('g=>bimVol({t:"brep",F:g.faces})',g)
            s.check(abs(volume-g['volume'])<1e-6,'faces orientées : volume 3D indépendant identique au pentagone '+g['parametres']['angle'])
            diag=[x for x in g['segments'] if x['diagonal']]
            s.check(len(diag)==1 and abs(diag[0]['longueur']-40*2**.5)<1e-9 and g['provenance']['L']['origine']=='saisie', 'diagonale 45° et provenance : '+g['parametres']['angle'])
        s.check(all(g['erreurs'] and not g['sommets'] and not g['fabricable'] for g in r['invalides']), 'valeurs manquantes, retrait dégénéré, coin et orientation non identifiés : aucune géométrie fabriquée')
        # Réouvrir un PDF fictif après rechargement et étudier une autre ligne sans création.
        pg.click('#bDxi');pg.set_input_files('#dxiF',fichier);pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
        J('()=>{DXI.ch="CHANTIER FICTIF 10B";DXI.ouv="VOILE";dxcOuvrir("n",DXI.NL.findIndex(x=>x.L.repere==="R02"))}')
        pg.select_option('#dxc_type','rect');pg.select_option('#dxc_support','voile_droit')
        pg.select_option('#dxc_geometrie','chanfrein45')
        s.check('à corriger' in pg.inner_text('#dxcGeo') and pg.is_disabled('#dxcRecap'),'chanfrein sans dimensions : inconnues visibles, création bloquée')
        for k,v in dict(L=600,h=800,e=240,retrait=40,epChanfrein=18).items():pg.fill('#dxc_'+k,str(v))
        pg.select_option('#dxc_angleChanfrein','GA');pg.select_option('#dxc_orientationChanfrein','vers_beton');pg.check('#dxc_confirmChanfrein')
        s.check(pg.locator('#dxcGeo svg polygon').count()==1 and pg.is_disabled('#dxcRecap') and 'débit' in pg.inner_text('#dxcGeo'), 'chanfrein complet : aperçu du pentagone, fabrication et exports explicitement indisponibles')
        J('dxcCreer()')
        s.check(J('P.length')==1 and J('Object.values(DXI.CP).some(x=>x.geometrieEtudiee&&x.geometrieEtudiee.sommets.length===5)'), 'étude conservée dans le dossier exportable, jamais ajoutée comme ouvrage')
        # Une preuve de chanfrein / autre forme ne peut être requalifiée en feuillure par une case générique.
        J("DXC.dossier.details.push({type:'mention_textuelle',brut:'R02 : chanfrein 10 mm'})")
        pg.select_option('#dxc_geometrie','feuillure')
        for k,v in dict(fL=40,fH=30,fNiv=0).items():pg.fill('#dxc_'+k,str(v))
        pg.check('#dxc_qualification');pg.check('#dxc_traversee');pg.select_option('#dxc_solution','simple')
        s.check(pg.is_disabled('#dxcRecap') and not J('dxcProposition().qualificationFeuillure'), 'preuve de chanfrein incompatible : aucune qualification abusive de feuillure')
        s.check(not errs,'aucune erreur JavaScript',str(errs[:3]))
        b.close()

if __name__=='__main__':
    s=Suite('t_geometries_particulieres')
    try:t(s)
    except Exception:s.check(False,'exception',traceback.format_exc()[-2400:])
    sys.exit(0 if s.report() else 1)
