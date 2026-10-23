"""Phase 10C : assemblage CP réel, attentes indépendantes, uniquement des cas/PDF fictifs."""
import base64, io, itertools, json, math, os, struct, sys, tempfile, traceback
import xml.etree.ElementTree as ET
import ezdxf
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.shape, ifcopenshell.util.element
from shapely.geometry import Polygon, MultiPoint, Point, LineString
from shapely.affinity import translate, rotate
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
from t_v30 import glb
import pdf_fictifs as PF
import support_fictifs as SF


def proche(a,b):return abs(a-b)<max(1e-6,abs(b)*1e-8)


def glb_sommets(raw):
    n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);bin=raw[28+n:]
    out={}
    for node in j['nodes']:
        if 'mesh' not in node:continue
        pr=j['meshes'][node['mesh']]['primitives'][0];a=j['accessors'][pr['attributes']['POSITION']];v=j['bufferViews'][a['bufferView']]
        p=struct.unpack_from('<%df'%(3*a['count']),bin,v.get('byteOffset',0)+a.get('byteOffset',0))
        out[node['name']]=list(zip(p[0::3],p[1::3],p[2::3]))
    return out


def t(s):
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        b,pg,errs=open_app(pw,width=1600);J=pg.evaluate
        net=[]
        pg.context.route(lambda u:not u.startswith(('file:','blob:','data:')),lambda r:(net.append(r.request.url),r.abort()))
        # Le polygone de référence et les attentes CP sont calculés ici, sans utiliser les formules JS.
        for cp,ret in [(18,40),(12,60),(27,25)]:
            for angle in ['GA','DA','DB','GB']:
                nom=f'{angle}, CP {cp}, retrait {ret}'
                r=J('''([cp,ret,angle])=>{const d=canon(migr(T.mk('para',{ppB:600,ppH:800,ppE:240,ppA:0,ppBe:0,ppChan:true,ppRetrait:ret,ppAngle:angle,ppOrientation:'vers_beton'},()=>setCProw('j',{...readCP().j,e:cp}))));
                  const F=chanfreinGeo(d),R=debit(d,null),M=model3(d,R);window.CF=d;window.CR=R;window.CM=M;
                  return {F,erreurs:checks(d,null).filter(w=>w[0]!=='warn'),R:R.map(q=>({q:q.q,a:q.a,b:q.b,m2:q.m2,tag:q.tag,ftag:q.ftag,sh:q.sh,net:q.volumeNet,brut:q.volumeBrut})),
                    explose:explode3(M,1,null,exVec3(M,camIso(d))).solids.map(q=>({F:q.F})),ac:acPlan(d,true),
                    solides:M.solids.map(q=>({id:q.chanfreinPiece,F:q.F,tag:q.tag,role:q.role})),
                    coupe:Object.values(nestPieces(d,R)).flat().map(q=>({tag:q.tag,poly:q.poly})),
                    nest:Object.values(cpNest(d,R)).map(n=>({fail:n.fail.length,aire:n.aUsed,polys:n.sheets.flat().map(p=>p.poly)})),
                    svg:genChanfrein(d).top,html:gen(d),gabarits:gabPieces(d,'roll').pieces||[],
                    bim:bimModel(d).pcs.filter(p=>p.kind==='cp').map(p=>({tag:p.tag,q:bimQty(p)}))}}''',[cp,ret,angle])
                F=r['F'];h=800-2*cp;k=math.sqrt(2)-1;diag=ret*math.sqrt(2)
                s.check(F['fabricable'] and not r['erreurs'] and len(F['pieces'])==5,'cinq panneaux contrôlés : '+nom,str(r['erreurs']))
                miroir=lambda q:(600-q[0] if angle in ['DA','DB'] else q[0],240-q[1] if angle in ['GB','DB'] else q[1])
                vide=Polygon([miroir(q) for q in [(0,ret),(ret,0),(600,0),(600,240),(0,240)]])
                s.check(proche(vide.area,144000-ret*ret/2) and proche(F['volume'],vide.area*800),'vide pentagonal exact : '+nom)
                if cp==18:s.check(proche(F['aire'],143200) and proche(F['volume'],114560000) and proche(F['pieces'][4]['longueurFace'],56.568542494923804),'références métier 143200 / 114560000 / diagonale : '+angle)
                footprints=[vide,vide,
                  Polygon([miroir(q) for q in [(0,ret),(cp,ret+k*cp),(cp,240),(0,240)]]),
                  Polygon([miroir(q) for q in [(600-cp,0),(600,0),(600,240),(600-cp,240)]]),
                  Polygon([miroir(q) for q in [(0,ret),(ret,0),(ret+math.sqrt(2)*cp,0),(cp,ret+k*cp)]])]
                vols=[vide.area*cp]*2+[(cp*(240-ret)-k*cp*cp/2)*h,cp*240*h,(cp*diag+(1-k)*cp*cp/2)*h]
                aires=[vide.area]*2+[(240-ret)*h,240*h,(diag+cp)*h]
                dimensions=[(600,240),(600,240),(240-ret,h),(240,h),(diag+cp,h)]
                for i,p in enumerate(F['pieces']):
                    poly=Polygon(p['empreinte']);row=r['R'][i]
                    s.check(poly.symmetric_difference(footprints[i]).area<1e-7 and proche(p['volumeNet'],vols[i]) and proche(row['net'],vols[i]),f'{nom} {p["id"]} : contour et volume finis indépendants')
                    s.check(proche(row['a'],dimensions[i][0]) and proche(row['b'],dimensions[i][1]) and proche(row['m2']*1e6,aires[i]) and row['q']==1,f'{nom} {p["id"]} : débit et brut de découpe')
                    z=[800-cp,0,cp,cp,cp][i];hauteur=[cp,cp,h,h,h][i]
                    s.check(proche(p['z'],z) and proche(p['hauteur'],hauteur) and {round(v[2],6) for f in p['faces'] for v in f}=={round(z,6),round(z+hauteur,6)},f'{nom} {p["id"]} : niveaux Z physiques attendus')
                    pc=next(x for x in r['bim'] if x['tag']==row['ftag'])
                    s.check(proche(pc['q']['V'],vols[i]) and proche(pc['q']['Vb'],aires[i]*cp) and pc['q']['e']==cp,f'{nom} {p["id"]} : BIM net et brut distincts')
                faces=[([(0,ret),(0,240)],2), ([(600,0),(600,240)],3), ([(0,ret),(ret,0)],4)]
                s.check(all(LineString([miroir(q) for q in edge]).difference(Polygon(F['pieces'][i]['empreinte']).boundary).length<1e-7 for edge,i in faces),'faces coffrantes latérales et diagonale entièrement couvertes sans interstice : '+nom)
                s.check(len({q['tag'] for q in r['R']})==5 and all(q['tag'] for q in r['solides'] if q.get('id')),'cinq repères CP uniques au débit et en 3D : '+nom)
                s.check(all(q[0] for q in r['ac']),'auto-contrôles existants : lisibilité, bornes, surfaces, repères et formulaire : '+nom,str([q for q in r['ac'] if not q[0]]))
                # Aucune intersection de volume entre les pièces, testée avec Shapely et leurs plages Z.
                s.check(all(Polygon(a['empreinte']).intersection(Polygon(b['empreinte'])).area*max(0,min(a['z']+a['hauteur'],b['z']+b['hauteur'])-max(a['z'],b['z']))<1e-5 for a,b in itertools.combinations(F['pieces'],2)),'aucun recouvrement volumique CP : '+nom)
                boites=[]
                for solid in r['solides']:
                    pts=[(v[1]+300,v[0],v[2]+400) for f in solid['F'] for v in f]
                    boites.append((MultiPoint([(x,y) for x,y,z in pts]).convex_hull,min(z for x,y,z in pts),max(z for x,y,z in pts)))
                s.check(all(a[0].intersection(b[0]).area*max(0,min(a[2],b[2])-max(a[1],b[1]))<1e-4 for a,b in itertools.combinations(boites,2)),'aucune interférence CP et bois, ni entre traverses : '+nom)
                ex=[]
                for solid in r['explose']:
                    pts=[(v[1]+300,v[0],v[2]+400) for f in solid['F'] for v in f]
                    ex.append((MultiPoint([(x,y) for x,y,z in pts]).convex_hull,min(z for x,y,z in pts),max(z for x,y,z in pts)))
                s.check(all(a[0].intersection(b[0]).area*max(0,min(a[2],b[2])-max(a[1],b[1]))<1e-4 for a,b in itertools.combinations(ex,2)),'vue éclatée : toutes les pièces séparées sans interférence : '+nom)
                s.check(all(Polygon(q['empreinte']).difference(vide).area<1e-7 for q in F['pieces']),'faces CP dans le vide de référence : '+nom)
                contact=footprints[2].boundary.intersection(footprints[4].boundary)
                s.check(proche(contact.length,math.hypot(cp,k*cp)) and [c['inclinaisonScie'] for c in F['pieces'][4]['coupes']]==[22.5,45],'contact jointif et coupes 22,5° / 45° : '+nom)
                s.check(all(n['fail']==0 for n in r['nest']) and len(r['coupe'])==5 and sorted(len(q['poly']) for q in r['coupe'])==[4,4,4,5,5] and proche(sum(Polygon(q['poly']).area for q in r['coupe']),sum(aires)),'imbrication : cinq contours, pentagones conservés et surfaces exactes : '+nom)
                # La section dessinée est comparée aux empreintes physiques par rapports d'aires.
                root=ET.fromstring(r['svg']);paths=[q for q in root if q.tag.endswith('path') and q.attrib.get('d','').startswith('M')]
                def path_poly(q):
                    import re
                    v=list(map(float,re.findall(r'-?\d+(?:\.\d+)?(?:e[+-]?\d+)?',q.attrib['d'],re.I)))
                    return Polygon(list(zip(v[0::2],v[1::2])))
                paths=[q for q in paths if q.attrib.get('fill')!='none']
                s.check(len(paths)>=4 and all(proche(path_poly(paths[i+1]).area/path_poly(paths[0]).area,footprints[i+2].area/vide.area) for i in range(3)),'2D : mêmes empreintes CP que le modèle 3D : '+nom)
                s.check('CHANFREIN — DÉCOUPES' in r['html'] and '22,5' in r['html'] and not r['gabarits'],'feuilles obligatoires cotées et coupes droites sans faux gabarit : '+nom)
                # Vérification des positions 3D, y compris la réflexion entre repères.
                for i,q in enumerate(F['pieces']):
                    solid=next(x for x in r['solides'] if x.get('id')==q['id'])
                    got={tuple(round(v,6) for v in pt) for face in solid['F'] for pt in face}
                    attendu={(round(y,6),round(x-300,6),round(z-400,6)) for face in q['faces'] for x,y,z in face}
                    s.check(got==attendu,f'{nom} {q["id"]} : transformation exacte vers para')
                # Quatre positions et épaisseurs variables : relire réellement les exports.
                if cp==18 or angle=='GA':
                    exp=J('''async()=>{const b64=u=>{let s='';for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode(...u.subarray(i,i+8192));return btoa(s)};
                      return {dx:b64(dxfPlanFile(CF).bytes),ifc:b64(ifcFile(CF).bytes),glb:b64((await glbFile(CF,false)).bytes),glbx:b64((await glbFile(CF,true)).bytes),O:bimModel(CF).O}}''')
                    dx=ezdxf.read(io.StringIO(base64.b64decode(exp['dx']).decode('cp1252').replace('\r\n','\n')))
                    pol=[Polygon([(v.dxf.location.x,v.dxf.location.y) for v in e.vertices]) for e in dx.modelspace() if e.dxftype()=='POLYLINE' and e.dxf.layer=='CP_DECOUPE']
                    s.check(len(pol)==5 and sorted(len(list(p.exterior.coords))-1 for p in pol)==[4,4,4,5,5] and all(abs(p.area-a)<p.length*.001 for p,a in zip(sorted(pol,key=lambda p:p.area),sorted(aires))),'DXF relu : contours pentagonaux et aires de découpe : '+nom,str({'n':len(pol),'sommets':[len(list(p.exterior.coords))-1 for p in pol],'aires':sorted(p.area for p in pol),'attendu':sorted(aires)}))
                    norm=lambda p:translate(p,-p.bounds[0],-p.bounds[1])
                    reps={}
                    for text in dx.modelspace():
                        if text.dxftype()=='TEXT' and text.dxf.layer=='CP_REPERES' and text.dxf.text in {q['ftag'] for q in r['R']}:
                            point=Point(text.dxf.insert.x,text.dxf.insert.y)
                            matches=[poly for poly in pol if poly.buffer(.001).covers(point)]
                            if len(matches)==1:reps[text.dxf.text]=matches[0]
                    attendu_coupes=[vide,vide,Polygon([(0,0),(240-ret,0),(240-ret,h),(0,h)]),Polygon([(0,0),(240,0),(240,h),(0,h)]),Polygon([(0,0),(diag+cp,0),(diag+cp,h),(0,h)])]
                    s.check(set(reps)=={q['ftag'] for q in r['R']} and all(min(norm(reps[q['ftag']]).hausdorff_distance(norm(rotate(attendu_coupes[i],a,origin=(0,0)))) for a in [0,90,180,270])<.002 for i,q in enumerate(r['R'])),'DXF : repères reliés aux vrais contours, précision 0,001 mm : '+nom,str({'reps':list(reps),'attendus':[q['ftag'] for q in r['R']],'distance':{q['ftag']:min(norm(reps[q['ftag']]).hausdorff_distance(norm(rotate(attendu_coupes[i],a,origin=(0,0)))) for a in [0,90,180,270]) if q['ftag'] in reps else None for i,q in enumerate(r['R'])}}))
                    ifc=ifcopenshell.file.from_string(base64.b64decode(exp['ifc']).decode())
                    plates=ifc.by_type('IfcPlate');sett=ifcopenshell.geom.settings();sett.set(sett.USE_WORLD_COORDS,True)
                    s.check(len(plates)==5,'IFC : cinq panneaux physiques, pas de fermeture A/B : '+nom)
                    O=exp['O'];points=glb_sommets(base64.b64decode(exp['glb']))
                    valid,_,vol_glb,_=glb(base64.b64decode(exp['glb']))
                    okx,_,vx,_=glb(base64.b64decode(exp['glbx']))
                    s.check(okx and all(abs(next(v for name,vs in vx.items() if name==q['ftag'] for v in vs)-vols[i]/1e9)<vols[i]/1e9*1e-5 for i,q in enumerate(r['R'])),'GLB éclaté relu : volumes et identités des cinq panneaux : '+nom)
                    for i,plate in enumerate(sorted(plates,key=lambda q:q.Tag)):
                        shape=ifcopenshell.geom.create_shape(sett,plate).geometry
                        volume=ifcopenshell.util.shape.get_volume(shape);qto=ifcopenshell.util.element.get_psets(plate)['Qto_PlateBaseQuantities']
                        s.check(proche(volume,vols[i]/1e9) and proche(qto['NetVolume'],vols[i]/1e9) and proche(qto['GrossVolume'],aires[i]*cp/1e9),f'IFC {nom} {plate.Tag} : volume tessellé net et brut')
                        attendu={(round((y-O[0])/1000,6),round((x-300-O[1])/1000,6),round((z-400)/1000,6)) for face in F['pieces'][i]['faces'] for x,y,z in face}
                        got={tuple(round(float(v),6) for v in pt) for pt in ifcopenshell.util.shape.get_vertices(shape)}
                        s.check(attendu==got,f'IFC {nom} {plate.Tag} : positions et sommets conservés')
                        gv=next(v for name,vs in vol_glb.items() if name==plate.Tag for v in vs)
                        pts=points[plate.Tag];gset={(round(x,6),round(y,6),round(z,6)) for x,y,z in pts}
                        gexp={(x,z,-y) for x,y,z in attendu}
                        s.check(valid and abs(gv-vols[i]/1e9)<vols[i]/1e9*1e-5 and gset==gexp,f'GLB {nom} {plate.Tag} : maillage, volume et positions conservés',str({'valide':valid,'volume':gv,'attendu':vols[i]/1e9,'absents':list(gexp-gset),'ajoutes':list(gset-gexp)}))
        # Invalidités de fabrication et combinaisons rejetées par les contrôles réels.
        invalides=J('''()=>{const p={L:600,e:240,H:800,retrait:40,ep:18,angle:'GA',orientation:'vers_beton',version:1};
          return [{L:null},{e:null},{H:null},{ep:0},{ep:400},{retrait:0},{retrait:-1},{retrait:240},{retrait:580},{angle:''},{angle:['GA','DA']},{orientation:'vers_vide'},{version:2},{nombre:2},{H:36},{e:45}].map(x=>CPI.geometriesParticulieres.chanfrein45Fabrication({...p,...x}))}''')
        s.check(all(not f['fabricable'] and f['erreurs'] and not f['pieces'] for f in invalides),'dimensions absentes, dégénérescences, interférences et variantes non prises en charge bloquées')
        bad=J('''()=>[{ppA:1},{ppBe:1},{feuilTraversee:true},{renX:true},{ppTr:false},{cp:{...CF.cp,j:{...CF.cp.j,e:100}}},{cp:{...CF.cp,j:{...CF.cp.j,f:'500x500'}}}].map(x=>limErr(canon({...CF,...x})))''')
        s.check(all(bad),'limErr : biais, pente, feuillure, renfort incompatible, CP/format invalides et traverses absentes bloqués')
        # WebGL utilise les cinq solides CP du même modèle, en vue assemblée et éclatée.
        J('open3D(CF)');pg.wait_for_function('V3D.gl===true&&GL3.objs.length>0')
        s.check(J("GL3.objs.filter(q=>q&&q.o.chanfreinPiece&&q.mesh.geometry.attributes.position.count>0).length")==5,'WebGL : cinq véritables panneaux CP')
        J("el('v3ex').value='100';el('v3ex').dispatchEvent(new Event('input'))")
        s.check(J("V3D.ex===1&&GL3.objs.filter(q=>q&&q.o.chanfreinPiece).length===5"),'éclaté : cinq panneaux identifiés conservés')
        J('close3D()')
        # PDF fictif : deux épaisseurs contradictoires et un détail attribué, aucune suppression de preuve.
        page=PF.Page(1190,842);SF.plan(page)
        for y,txt in [(500,'R01 : chanfrein 45 degrés, retrait 40 mm'),(480,'R01 : épaisseur du voile = 240 mm'),(460,'R01 : épaisseur du voile = 250 mm')]:page.texte(70,y,txt,10)
        fichier=PF.ecrire(os.path.join(tmp,'CHANFREIN_FICTIF.pdf'),[page])
        pg.click('#bDxi');pg.set_input_files('#dxiF',fichier);pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
        J('()=>{DXI.ch="CHANTIER FICTIF 10C";DXI.ouv="VOILE";dxcOuvrir("n",DXI.NL.findIndex(x=>x.L.repere==="R01"))}')
        avant=J('JSON.stringify({P,PROF,LIBU,ENT})')
        pg.select_option('#dxc_type','rect');pg.select_option('#dxc_support','voile_droit');pg.select_option('#dxc_geometrie','chanfrein45');pg.select_option('#dxc_solution','simple')
        for key,v in dict(L=600,h=800,e=240,retrait=40,epChanfrein=18).items():pg.fill('#dxc_'+key,str(v))
        pg.select_option('#dxc_angleChanfrein','GA');pg.select_option('#dxc_orientationChanfrein','vers_beton')
        pg.check('#dxc_traversee');pg.check('#dxc_confirmChanfrein')
        s.check(pg.is_disabled('#dxcRecap'),'contradiction PDF conservée : aucune fabrication avant arbitrage')
        J('dxcArbitrer("e")')
        s.check(not pg.is_disabled('#dxcRecap') and J('dxcProposition().fabricable'),'variante calculée, qualifiée et arbitrée : création disponible')
        pg.select_option('#dxc_orientationChanfrein','vers_vide')
        s.check(pg.is_disabled('#dxcRecap'),'autre orientation : étude sans fabrication, aucun retournement implicite')
        pg.select_option('#dxc_orientationChanfrein','vers_beton')
        s.check(J('JSON.stringify({P,PROF,LIBU,ENT})')==avant,'PDF, aperçu et corrections sans modification du projet')
        pg.click('#dxcRecap');J('dxcCreer()')
        s.check(J('P.length')==0 and pg.is_disabled('#dxcCreer'),'récapitulatif sans confirmation : aucun ouvrage')
        pg.check('#dxcConfirme');pg.fill('#dxc_retrait','41')
        s.check(pg.locator('#dxcConfirme').count()==0,'modifier le retrait invalide la confirmation précédente')
        pg.fill('#dxc_retrait','40');pg.click('#dxcRecap');pg.check('#dxcConfirme');pg.click('#dxcCreer')
        J('dxcCreer()')
        s.check(J('P.length===1&&P[0].chanfrein45.retrait===40&&P[0].cp.j.e===18&&P[0].ppTr') and pg.is_disabled('#dxcRecap'),'un seul ouvrage, paramètres métier CP et renforts conservés')
        s.check(J("P[0].origineImport.proposition.qualificationChanfrein&&P[0].origineImport.cotesPdf.details.length>0&&P[0].origineImport.cotesPdf.conflits.length>0"),'preuves, contradictions et qualification persistées sans effacer les détails')
        s.check(J('''()=>{const d=JSON.parse(JSON.stringify(P[0]));delete d.origineImport;return JSON.stringify(T.sum(d))===JSON.stringify(T.sum(P[0]))}'''),'fabrication indépendante des métadonnées de provenance')
        J('dxcFermer();dxiQuit();closeModal();setForm(P[0])')
        s.check(J('JSON.stringify(T.sum(P[0]))===JSON.stringify(T.sum(coll()))&&coll().chanfrein45.angle==="GA"'),'formulaire : paramètres et débit restitués exactement')
        J('window.CJSON=projJson();window.CSUM=JSON.stringify(T.sum(P[0]));stoAttendre()')
        pg.reload();pg.wait_for_function('_ready');pg.add_script_tag(path=os.path.join(HERE,'helpers.js'))
        s.check(J('P.length===1&&P[0].chanfrein45.angle==="GA"&&P[0].origineImport.confirmation_utilisateur'),'IndexedDB : rechargement de l’ouvrage confirmé')
        saved=J('projJson()');somme=J('JSON.stringify(T.sum(P[0]))')
        J('P=[]');J('s=>loadText(s,"FICTIF.json",null)',saved);pg.wait_for_function('P.length===1')
        s.check(J('JSON.stringify(T.sum(P[0]))')==somme and json.loads(saved)['v']==10,'réimport JSON v10 : mêmes pièces et mêmes dimensions')
        J('dupP(0)')
        s.check(J('P.length===2&&P[1].chanfrein45.angle==="GA"&&!P[1].origineImport&&P[1].uid!==P[0].uid'),'duplication autorisée : géométrie conservée, nouvelle identité sans origine PDF')
        pg.click('#bDxi');pg.set_input_files('#dxiF',fichier);pg.wait_for_function('DXI&&DXI.fmt==="pdf"')
        J('()=>{DXI.ch="CHANTIER FICTIF 10C";DXI.ouv="VOILE";dxcOuvrir("n",DXI.NL.findIndex(x=>x.L.repere==="R01"))}')
        s.check(pg.is_disabled('#dxcRecap') and J('dxcDeja(DXC.cles)'),'réimport du PDF : identité persistante interdit un doublon')
        J("DXC.dossier.details.push({type:'mention_textuelle',brut:'R01 : feuillure et chanfrein'})")
        pg.select_option('#dxc_geometrie','chanfrein45');pg.check('#dxc_confirmChanfrein')
        s.check(not J('dxcProposition().qualificationChanfrein'),'la sélection du chanfrein ne supprime pas un autre détail attribué')
        r=J('''()=>{const keep=DXC.dossier.details;try{return [
          ['R02 : chanfrein 45 degrés',true],['R01 : chanfrein 30 degrés',false],
          ['R01 : chanfrein et pente',false],['R01 : deux chanfreins 45 degrés',false],
          ['R01 : 10 chanfreins 45 degrés',false],['R01 : 01 chanfrein 45 degrés',true]
          ].map(([brut,attendu])=>{DXC.dossier.details=[{type:'mention_textuelle',brut}];return {brut,attendu,obtenu:dxcProposition().qualificationChanfrein}})}finally{DXC.dossier.details=keep}}''')
        for q in r:s.check(q['obtenu']==q['attendu'],'qualification sans effacement des détails : '+q['brut'])
        s.check(not net,'fonctionnement local sans service externe',str(net[:2]))
        s.check(not errs,'aucune erreur JavaScript',str(errs[:3]));b.close()

if __name__=='__main__':
    s=Suite('t_chanfrein_fabrication')
    try:t(s)
    except Exception:s.check(False,'exception',traceback.format_exc()[-2600:])
    sys.exit(0 if s.report() else 1)
