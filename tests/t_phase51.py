"""Phase 5.1 (demande de Kévin du 21/10/2026) : corrections après essais sur trois plans réels. Cas synthétiques anonymes qui
reproduisent chaque défaut relevé : unité d'une altitude prise pour celle de l'ouverture, colonnes « Axe réservations » /
« Niveau réservation » prises pour des repères, en-tête à deux niveaux, trappes mêlées aux réservations, tableau OCR ajouté en
double, titres de vue (dessous, titre moins haut, renforts, cartouche, renvoi), grande vue marquée incertaine, faux repères
(« 1-D1 », « 2x D10 »), comptage dans une vue de détail ou sans titre, repère étiqueté deux fois sans quantité, DN."""
import json, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
import vues_fictifs as VF

# Tableau à deux niveaux d'en-tête, sans traits (textes extractibles seulement), colonne de commentaires large (> 30 h de texte)
DOC2 = '''()=>{const T=[],t=(texte,x,y,w,h)=>T.push({id:'t'+T.length,espace:'papier',presentation:'Page 1',page:1,texte,x,y,h:h||7,w:w||texte.length*4.2,rot:0});
  t('Nomenclature des réservations',500,930,180,8.6);
  t('DIMENSIONS (mm)',333,903,90);t('FINITIONS',628,903,50);t('Axe',429,896,18);t('Niveau',502,896,32);
  t('IDENTIFIANT',21,890,62);t('COMMENTAIRES',215,890,82);t('Non',563,889,20);t('Scellement',622,889,52);t('Scellement',687,889,52);
  t('réservations',429,884.5,59);t('réservation',501,884.5,53);t('Hauteur',303,883,38);t('Largeur',364,883,37);
  t('rebouché',563,878,40);t('non étanche',622,878,55);t('étanche',687,878,36);
  [['R01','ALIMENTATION DEPUIS BASSIN','500','500','206.660'],['R02','DEPART VERS OUVRAGE','350','400','209.290'],['R03','LIAISON','250','250','207.415']].forEach((r,i)=>{const y=866-13*i;
    t(r[0],12,y,15);t(r[1],60+r[1].length*2.1,y,r[1].length*4.2);t(r[2],303,y,15);t(r[3],364,y,15);t(r[4],429,y,30);t('Non',563,y,15);t('Non',622,y,15);t('Oui',687,y,15)});
  return{fichier:'fictif.pdf',format:'pdf',textes:T,traits:[],signalements:[]}}'''


def t(s):
    tmp = tempfile.mkdtemp()
    F = VF.fichiers(tmp)
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500)
        J = pg.evaluate

        # ---- A1 : unités
        u = J('''()=>{const N=CPI.nomenclatures,c=(cells,cols)=>N.ligne(cols.map(([titre,cle,unite])=>({titre,cle,unite})),cells);
          const a=c(['X1','500','500','4,86m'],[['Rep','repere',null],['Largeur (mm)','largeur','mm'],['Hauteur (mm)','hauteur','mm'],['Hauteur axe au-dessus du radier (m)',N.kinds('Hauteur axe au-dessus du radier (m)')[0],'m']]);
          const f=c(['X2','500x500 — 4,86m'],[['Rep','repere',null],['Dimensions (mm)','ouverture','mm']]);
          const k=c(['X3','500 m'],[['Rep','repere',null],['Ø (mm)','diametre','mm']]);
          return{a:[a.dims,a.niveau,a.uniteOrigine],f:f.dims,k:[k.dims,k.a_verifier.join(' | ')],
            m:N.cotes('500x500 — 4,86m','mm'),e:N.cotes('650x800 mm',null),p:CPI.nomenclatures.provenance({colonnes:[],fichier:'f',format:'pdf'},Object.assign({id:'L',rang:1,ids:[],calques:[]},a),{forme:'carre',cotes:'500x500',dims:{etat:'rect',a:500,b:500},ref:'X1'}).unite_origine}}''')
        s.check(u['a'][0]['a'] == 500 and u['a'][0]['b'] == 500 and u['a'][0]['unite'] == 'mm' and u['a'][1] == '4,86m',
                'A1 : Largeur 500 mm, Hauteur 500 mm, Hauteur d\'axe 4,86 m → ouverture 500 × 500 mm, niveau séparé', json.dumps(u['a'], ensure_ascii=False))
        s.check(u['f']['unite'] == 'mm' and u['m']['unite'] == 'mm' and u['e']['unite'] == 'mm',
                'A1 : « 500x500 — 4,86m » : unité de la colonne (mm), jamais le « m » de l\'altitude ; « 650x800 mm » : unité écrite contre la cote', json.dumps([u['f'], u['m'], u['e']], ensure_ascii=False))
        s.check(u['k'][0]['unite'] is None and u['k'][0].get('conflitUnite') and 'à confirmer' in u['k'][1],
                'A1 : unité de la cellule (m) contraire à celle de la colonne (mm) : cote gardée, unité à confirmer, aucune conversion', json.dumps(u['k'], ensure_ascii=False))
        s.check(u['a'][2] == 'titre de colonne' and u['p'] == 'titre de colonne', 'A1 : provenance de l\'unité gardée (ligne et origineImport)', json.dumps(u, ensure_ascii=False)[:300])
        d = J('''()=>{DXI={NU:{}};const N={id:'T',unite:'mm'},r=[dxnU(N,{dims:{type:'circ',D:500,unite:null,conflitUnite:true}}),dxnU(N,{dims:{type:'circ',D:500,unite:null}})];DXI.NU.T='cm';r.push(dxnU(N,{dims:{conflitUnite:true,unite:null}}));DXI=null;return r}''')
        s.check(d == ['', 'mm', 'cm'], 'A1 : création : unité contradictoire jamais remplacée en silence par celle de l\'en-tête (seulement par un choix de l\'utilisateur)', json.dumps(d))
        g = J('''()=>{const {N}=CPI.nomenclatures.depuisGrille({lignes:[['Repère','Ouverture (mm)','Hauteur (mm)'],['R1','500x500','300']],ids:[[[],[],[]],[[],[],[]]],page:1});
          const w=CPI.ocr.grille(N,[])[0];return{o:w.cells.ouverture,a:w.cells.autre}}''')
        s.check(g['o'] == '500x500' and '300' in (g['a'] or ''), 'A1 : grille OCR : colonne Hauteur jamais fusionnée dans l\'ouverture quand le tableau a une colonne Ouverture', json.dumps(g, ensure_ascii=False))

        # ---- A2 : colonnes, en-tête à deux niveaux
        k = J('''()=>Object.fromEntries(['IDENTIFIANT','Axe réservations','Axe\\nréservations','Niveau réservation','Hauteur axe au-dessus du radier (m)','Longueur','Longueur développée','Réservation','N° réservation','Nomenclature des réservations']
          .map(t=>[t,CPI.nomenclatures.kinds(t)[0]||null]))''')
        s.check(k == {'IDENTIFIANT': 'repere', 'Axe réservations': 'niveau', 'Axe\nréservations': 'niveau', 'Niveau réservation': 'niveau', 'Hauteur axe au-dessus du radier (m)': 'niveau',
                      'Longueur': 'longueur', 'Longueur développée': 'acier', 'Réservation': 'repere', 'N° réservation': 'repere', 'Nomenclature des réservations': None},
                'A2 : « réservations » seul n\'est pas une preuve de colonne de repères ; Axe / Niveau réservation, Hauteur axe → niveau ; Longueur', json.dumps(k, ensure_ascii=False))
        A = J(f'''()=>{{const A=CPI.nomenclatures.analyser(({DOC2})()),N=A.nomenclatures[0];return N?{{n:A.nomenclatures.length,col:N.colonnes.map(c=>[c.titre.replace(/\\n/g,' '),c.cle,c.unite||null]),
          L:N.lignes.map(L=>[L.repere,L.dims&&L.dims.a,L.dims&&L.dims.b,L.dims&&L.dims.unite,L.niveau,L.observations])}}:null}}''')
        cols = {c[0]: c for c in (A or {}).get('col', [])}
        s.check(A and A['n'] == 1 and cols.get('IDENTIFIANT', [0, 0])[1] == 'repere' and cols.get('COMMENTAIRES', [0, 0])[1] == 'observations'
                and cols.get('Hauteur', [0, 0, 0])[1:] == ['hauteur', 'mm'] and cols.get('Largeur', [0, 0, 0])[1:] == ['largeur', 'mm'] and cols.get('Axe réservations', [0, 0])[1] == 'niveau',
                'A2 : en-tête à deux niveaux (textes) : toutes les colonnes reconstruites, unité du groupe « DIMENSIONS (mm) » appliquée à Hauteur et Largeur', json.dumps(A, ensure_ascii=False)[:700])
        s.check(A and [l[0] for l in A['L']] == ['R01', 'R02', 'R03'] and A['L'][1][1:5] == [400, 350, 'mm', '209.290'],
                'A2 : repères R01…R03 (jamais le niveau NGF), cotes Largeur × Hauteur en mm, niveau NGF séparé', json.dumps(A and A['L'], ensure_ascii=False))
        G = J('''()=>{const {N}=CPI.nomenclatures.depuisGrille({lignes:[['IDENTIFIANT','COMMENTAIRES','DIMENSIONS (mm)\\nHauteur Largeur','','Axe\\nréservations'],['R01','ALIMENTATION','500','400','206.660']],
            ids:[[[],[],[],[],[]],[[],[],[],[],[]]],page:1});return{col:N.colonnes.map(c=>[c.cle,c.unite||null]),L:N.lignes.map(L=>[L.repere,L.dims&&L.dims.a,L.dims&&L.dims.b,L.dims&&L.dims.unite,L.niveau])}}''')
        s.check(G['col'] == [['repere', None], ['observations', None], ['hauteur', 'mm'], ['largeur', 'mm'], ['niveau', None]] and G['L'] == [['R01', 400, 500, 'mm', '206.660']],
                'A2 : grille OCR : titre de groupe fusionné sur deux colonnes éclaté (Hauteur / Largeur), unité du groupe, Axe réservations = niveau', json.dumps(G, ensure_ascii=False))

        # ---- A3 : trappes / ouvertures équipées séparées ; aciers toujours écartés
        tr = J('''()=>{const T=[],t=(texte,x,y)=>T.push({id:'t'+T.length,espace:'papier',presentation:'Page 1',page:1,texte,x,y,h:7,w:texte.length*4.2,rot:0});
          t('Nomenclature des trappes',200,960);t('IDENTIFIANT',20,940);t('COMMENTAIRES',120,940);t('Longueur',240,940);t('Largeur',300,940);t('Diamètre',360,940);t('Feuillure',420,940);
          [['T01','CHAMBRE','1800','900','','70'],['T02','REGARD','','','660','70']].forEach((r,i)=>r.forEach((v,j)=>v&&t(v,[20,120,240,300,360,420][j],925-12*i)));
          const A=CPI.nomenclatures.analyser({fichier:'f',format:'pdf',textes:T,traits:[],signalements:[]}),e=A.ecartes[0];
          return{n:A.nomenclatures.length,e:e&&{nature:e.nature,raison:e.raison,lignes:e.lignes&&e.lignes.map(L=>[L.repere,L.dims&&L.dims.a,L.dims&&L.dims.b])},
            g:CPI.nomenclatures.nature('',[{titre:'Trappe',cle:'autre'},{titre:'Dimensions (mm)',cle:'ouverture'},{titre:'Feuillure',cle:'autre'}]),
            a:CPI.nomenclatures.nature('LISTE DE FERS',[{titre:'Poids',cle:'acier'},{titre:'Ø',cle:'diametre'}])}}''')
        s.check(tr['n'] == 0 and tr['e'] and tr['e']['nature'] == 'trappes' and 'jamais créées' in tr['e']['raison'] and tr['e']['lignes'][0] == ['T01', 900, 1800],
                'A3 : nomenclature des trappes : catégorie distincte, aucune réservation proposée, lignes consultables (Longueur × Largeur lues)', json.dumps(tr, ensure_ascii=False))
        s.check(tr['g'] == 'trappes' and tr['a'] == 'aciers', 'A3 : grille OCR de trappes (Trappe, Feuillure) écartée ; liste de fers toujours « aciers »', json.dumps(tr, ensure_ascii=False))

        # ---- DN dans la colonne Ouverture : DN gardé, aucune cote
        dn = J('''()=>{const L=CPI.nomenclatures.ligne([{titre:'Rep',cle:'repere'},{titre:'Ouverture (mm)',cle:'ouverture',unite:'mm'}],['D2','DN400']);return[L.dims,L.dn,L.a_verifier.join(' | ')]}''')
        s.check(dn[0] is None and dn[1] == {'D': 400, 'texte': 'DN400'} and 'diamètre réel de réservation à confirmer' in dn[2],
                'DN dans la colonne Ouverture : réservation circulaire probable, DN gardé, aucun diamètre fabriqué', json.dumps(dn, ensure_ascii=False))

        # ---- B1 : titres et vues
        ti = J('''()=>{const T=[];for(let i=0;i<40;i++)T.push({id:'p'+i,texte:'D'+i,x:20*i,y:10,h:8.5,w:14});
          const g=(id,texte,x,y,h,o)=>T.push(Object.assign({id,texte,x,y,h,w:texte.length*0.7*h},o||{}));
          g('a','Vue dessous dalle',100,500,16);g('b','Vue dessus dalle',600,500,16);g('c','VUE',100,300,14.2,{ocr:{conf:94}});g('d','PLAN',160,300,14.2,{ocr:{conf:95}});
          g('e','RENFORTS RESERVATIONS',600,300,16);g('f','RADIER',900,700,14.2);g('h','Vue en plan, ferraillage radier : voir plan N° 2',300,900,16);
          g('i','PLAN DE NOTES',900,400,16);g('j','ligne deux',900,385,16);g('k','ligne trois',900,370,16);
          return CPI.vues.titres(T).map(t=>[t.texte,t.type])}''')
        tt = dict(ti)
        s.check(tt.get('Vue dessous dalle') == 'plan' and tt.get('Vue dessus dalle') == 'plan', 'B1 : « Vue dessous dalle » et « Vue dessus dalle » = vues en plan', json.dumps(ti, ensure_ascii=False))
        s.check(tt.get('VUE PLAN') == 'plan' and 'RADIER' not in tt, 'B1 : « VUE » « PLAN » lus séparément à 1,67 × la médiane : vue en plan (mot-clé fort) ; « RADIER » seul à 1,67 × : pas un titre', json.dumps(ti, ensure_ascii=False))
        s.check(tt.get('RENFORTS RESERVATIONS') == 'detail', 'B1 : « Renforts réservations » = vue de détail (jamais comptée pour les occurrences)', json.dumps(ti, ensure_ascii=False))
        s.check(not any('voir' in x for x in tt) and not any('NOTES' in x for x in tt), 'B1 : renvoi (« voir plan ») et paragraphe de 3 lignes : pas des titres de vue', json.dumps(ti, ensure_ascii=False))
        dv = J('''()=>{const S=[],K=[],rect=(x0,y0,x1,y1)=>{const P=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]];K.push({pts:P,courbes:[]});P.forEach((p,i)=>S.push({a:p,b:P[(i+1)%4]}))};
          rect(50,50,700,650);for(let i=1;i<12;i++)S.push({a:[50+50*i,50],b:[50+50*i,80]});   // grande vue titrée (> 30 % de la page)
          rect(100,100,130,130);rect(140,100,170,130);rect(100,140,170,170);   // partie de la vue séparée par un blanc
          const T=[];for(let i=0;i<20;i++)T.push({id:'p'+i,texte:'n'+i,x:760+10*i,y:20,h:3,w:6});
          T.push({id:'t1',texte:'VUE EN PLAN DALLE',x:350,y:665,h:9,w:120},{id:'t2',texte:'PLAN GUIDE GENIE CIVIL',x:870,y:400,h:9,w:130});   // cartouche : titre sans dessin
          const r=CPI.vues.detecter({page:1,w:1000,h:700,segments:S,contours:K,petits:[]},T,{});
          return{V:r.vues.map(v=>[v.titre,v.type,!!v.incertaine,v.motifs.join(' ; '),v.id]),p:CPI.vues.situer(r.carte,115,115)}}''')
        vp = [v for v in dv['V'] if v[0] == 'VUE EN PLAN DALLE']
        s.check(vp and not vp[0][2], 'B1 : grande vue en plan titrée (> 30 % de la page) : pas incertaine par sa seule aire', json.dumps(dv, ensure_ascii=False))
        s.check(not any(v[0] == 'PLAN GUIDE GENIE CIVIL' for v in dv['V']), 'B1 : titre de cartouche sans dessin : pas une vue', json.dumps(dv, ensure_ascii=False))
        s.check(vp and dv['p'] == vp[0][4] and not any(v[0] is None for v in dv['V']), 'B1 : partie de la vue séparée par un blanc rattachée à la vue titrée qui la contient', json.dumps(dv, ensure_ascii=False))

        fr = J('''()=>{const S=[],K=[],rect=(x0,y0,x1,y1)=>{const P=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]];K.push({pts:P,courbes:[]});P.forEach((p,i)=>S.push({a:p,b:P[(i+1)%4]}))};
          rect(5,5,995,695);rect(100,200,400,500);for(let i=1;i<6;i++)S.push({a:[100+50*i,200],b:[100+50*i,230]});   // cadre de feuille, dessin
          const T=[];for(let i=0;i<20;i++)T.push({id:'p'+i,texte:'n'+i,x:40+10*i,y:20,h:3,w:6});
          T.push({id:'t1',texte:'PLAN',x:250,y:170,h:9,w:30});
          [['Plan guide : client',680],['Indice B : modification',665],['Echelle : 1/50',650],['Dessiné par : X',635]].forEach(([texte,y],i)=>T.push({id:'c'+i,texte,x:850,y,h:9,w:texte.length*6}));
          const r=CPI.vues.detecter({page:1,w:1000,h:700,segments:S,contours:K,petits:[]},T,{});
          return r.vues.filter(v=>v.titre).map(v=>[v.titre,v.region.map(Math.round),!!v.incertaine])}''')
        s.check(len(fr) == 1 and fr[0][0] == 'PLAN' and fr[0][1][2] <= 450 and not fr[0][2],
                'B1 : titre à l\'intérieur du cadre de feuille : rattaché à son dessin, jamais au cadre (vue non étendue à la page) ; « Plan guide » dans un bloc de notes : pas une vue', json.dumps(fr, ensure_ascii=False))

        # ---- B2 : faux repères, B3 : comptage conservateur
        r = J('''()=>{const L=[{id:'e',repere:'D5',dims:null,unite:'mm',quantite:'',page:1},{id:'a',repere:'D1',dims:null,unite:'mm',quantite:'',page:1},{id:'b',repere:'D10',dims:null,unite:'mm',quantite:'',page:1},{id:'c',repere:'TR-3',dims:null,unite:'mm',quantite:'',page:1}];
          const T=[{id:'1',page:1,texte:'1-D1',x:100,y:100,h:5,w:15},{id:'2',page:1,texte:'D1',x:300,y:300,h:5,w:8},{id:'3',page:1,texte:'1—D1',x:120,y:200,h:5,w:15,ocr:{conf:90,brut:'1—D1',corrections:[]}},
            {id:'4',page:1,texte:'5x',x:600,y:600,h:5,w:8},{id:'5',page:1,texte:'D10',x:612,y:600,h:5,w:10},{id:'6',page:1,texte:'2x D10',x:700,y:650,h:5,w:20},
            {id:'7',page:1,texte:'voir détail D1',x:50,y:700,h:5,w:40},{id:'10',page:1,texte:'DS',x:950,y:50,h:5,w:8,ocr:{conf:88,brut:'DS',corrections:[]}},{id:'8',page:1,texte:'TR-3',x:800,y:100,h:5,w:15},{id:'9',page:1,texte:'D1 650x800',x:900,y:900,h:5,w:30}];
          const R=CPI.rapprochement.rapprocher(L,T,[],{}).lignes,f=k=>R[k].occurrences.map(o=>[o.texte,o.nature,o.fiable]);
          const V=[{id:'P',type:'plan',partie:null,region:[0,0,1000,1000]}];
          const c=CPI.vues.consolider({quantite:'1'},{occurrences:R.b.occurrences.map(o=>Object.assign({},o,{vue:'P'}))},V);
          return{e:f('e'),a:f('a'),b:f('b'),c:f('c'),cb:[c.localisees,c.nonRattachees,c.roles.map(x=>x.motif).join(' | ')]}}''')
        s.check(r['a'] == [['D1', 'repere', True], ['voir détail D1', 'annotation', False], ['D1 650x800', 'repere', True]],
                'B2 : « 1-D1 » (identifiant d\'armature / panneau) jamais lu comme D1 ; renvoi « voir détail D1 » = annotation non rattachée ; « D1 650x800 » = repère', json.dumps(r, ensure_ascii=False))
        s.check(r['e'] == [['DS', 'repere', False]], 'B2 : « DS » lu par OCR pour D5 : repère isolé (lecture incertaine), jamais une annotation', json.dumps(r['e'], ensure_ascii=False))
        s.check([x[1] for x in r['b']] == ['multiplicateur', 'multiplicateur'] and r['c'] == [['TR-3', 'repere', True]],
                'B2 : « 5x D10 », « 2x D10 » = multiplicateurs (note, liste) ; repère à tiret du tableau (TR-3) toujours reconnu', json.dumps(r, ensure_ascii=False))
        s.check(r['cb'][0] == 0 and r['cb'][1] == 2 and 'quantité' in r['cb'][2], 'B2 : mention non isolée jamais comptée comme occurrence physique, gardée non rattachée avec son motif', json.dumps(r['cb'], ensure_ascii=False))
        c = J('''()=>{const V=[{id:'P',type:'plan',partie:'dalle',region:[0,0,100,100]},{id:'F',type:'ferraillage',partie:'dalle',region:[200,0,300,100]},{id:'R',type:'detail',partie:null,region:[0,200,100,300]},
            {id:'A',type:'autre',partie:null,region:[400,0,500,100]},{id:'Pi',type:'plan',partie:'radier',region:[0,400,300,700],incertaine:true}];
          const o=(vue,x,y)=>({page:1,vue,x,y,fiable:true,doutes:[]}),C=(q,O,v)=>CPI.vues.consolider({quantite:q},{occurrences:O},v||V);
          const r1=C('',[o('P',20,80),o('P',60,30)]),r2=C('',[o('F',220,80)]),r3=C('',[o('R',20,220)]),r4=C('',[o('A',420,80)]),r5=C('2',[o('P',20,80),o('P',60,30)]);
          const r6=C('',[o('F',220,80)],V.filter(v=>v.id!=='Pi'));
          return{r1:[r1.localisees,r1.nonRattachees,r1.notes.join(' | ')],r2:[r2.localisees,r2.notes.join(' | ')],r3:r3.localisees,r4:r4.localisees,r5:[r5.localisees,r5.restantes],r6:r6.localisees}}''')
        s.check(c['r1'][:2] == [0, 2] and 'une ou plusieurs' in c['r1'][2],
                'B3 : même repère deux fois dans la vue en plan, quantité non indiquée : aucune occurrence décidée, deux observations à vérifier', json.dumps(c, ensure_ascii=False))
        s.check(c['r2'][0] == 0 and 'pas de repli' in c['r2'][1] and c['r6'] == 1,
                'B3 : vue en plan douteuse dans le document : pas de repli sur le ferraillage (sans plan douteux : ferraillage compté, comme avant)', json.dumps(c, ensure_ascii=False))
        s.check(c['r3'] == 0 and c['r4'] == 0 and c['r5'] == [2, 0], 'B3 : vue de renforts / détail et vue sans titre jamais comptées ; quantité 2 au tableau : 2 occurrences comptées', json.dumps(c, ensure_ascii=False))

        # ---- A4 : OCR sur la zone d'un tableau déjà lu automatiquement : remplacement proposé, jamais un doublon silencieux
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['PDF_8_VUES.pdf'][0]); pg.wait_for_selector('#dxnT tr[data-n]')
        n0 = J('DXI.NL.length')
        J('()=>{DXI.NR[0].h="321";DXI.NR[0].conf=true}')
        ok = J('''()=>{const N=DXI.NA.nomenclatures[0],c=N.cadre,z={page:N.page,x0:c[0]-2,y0:c[1]-2,x1:c[2]+2,y1:c[3]+2,unite:'pt'};dxiVue('p');DXI.page=z.page;dxpPage();dxpZone(z);
          const {T,S}=dxpZoneTS(z),G=CPI.nomenclatures.textesEnGrille(S,z,T);if(!G)return'pas de grille';
          dxoGrilleLue({z},{G,textes:G.textes,mesures:{ms:0,rangees:G.rangees,colonnes:G.lignes[0].length,source:'test',dpi:null}},false);return!!DXI.OC}''')
        s.check(ok is True, 'A4 : grille de vérification construite sur la zone du tableau lu automatiquement', str(ok))
        J('dxoValider()')
        dlg = J('el("dlg").style.display==="flex"?el("dlgB").innerText:""')
        s.check('le remplacer' in dlg.lower() and 'retirées' in dlg and J('DXI.NL.length') == n0, 'A4 : remplacement du tableau existant proposé explicitement ; rien d\'ajouté avant confirmation', dlg[:300])
        J('dlgEnd(0)')
        s.check(J('DXI.NL.length') == n0 and J('DXI.NA.nomenclatures.length') == 1, 'A4 : refus : rien d\'ajouté ni retiré')
        no = J('DXI.OC.rows.length'); J('dxoValider()'); J('dlgEnd(1)')
        R = J('''()=>({n:DXI.NL.length,ids:[...new Set(DXI.NL.map(x=>x.N.id))],h:DXI.NR[DXI.NL.findIndex(x=>x.L.repere==='V1')].h,c:DXI.NR[DXI.NL.findIndex(x=>x.L.repere==='V1')].conf,msg:el('dxoR').innerText})''')
        s.check(R['n'] == no and len(R['ids']) == 1 and R['ids'][0] != 'N1' and R['h'] == '321' and R['c'],
                'A4 : remplacement confirmé : lignes de la grille vérifiée seulement (aucun doublon), choix de l\'utilisateur gardés sur la ligne correspondante', json.dumps(R, ensure_ascii=False))
        J('()=>closeModal()')

        errs2 = [e for e in errs if 'net::ERR_FAILED' not in e and 'diacritics' not in e]
        s.check(not errs2, 'aucune erreur JS', '; '.join(errs2[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_phase51')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
