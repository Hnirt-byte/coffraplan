// CoffraPlan — module d'import de plans : décodeur DXF ASCII (inscrit dans CPI.lecteur.DECODEURS.dxf).
// Lit la section ENTITIES (LWPOLYLINE, POLYLINE R12 + VERTEX, CIRCLE ; le reste → « autre »), l'unité $INSUNITS et la
// table des calques ; chaque entité porte son espace (Objet ou présentation). Relève aussi les textes et les traits droits
// de tous les espaces, blocs insérés compris (tableaux, repères : voir nomenclatures.js). Charger après lecteur.js.
// Indépendant de l'interface et du moteur.
(function(root){'use strict';
const UNITES={4:'mm',5:'cm',6:'m'};   // $INSUNITS ; 0 ou absent → null (jamais devinée) ; autres codes → refus
const NOMS_U={1:'pouces',2:'pieds',3:'miles',7:'km',8:'micro-pouces',9:'mils',10:'yards',11:'angströms',12:'nanomètres',13:'microns',14:'décimètres'};
const fail=m=>{throw new Error(m)};

// Texte DXF → liste de paires [code, valeur] ; refuse binaire, paires incomplètes, codes illisibles, EOF absent
function paires(txt){
  if(typeof txt!=='string'||!txt.trim())fail('fichier vide');
  if(txt.startsWith('AutoCAD Binary DXF'))fail('DXF binaire non pris en charge (enregistrer en DXF ASCII)');
  const L=txt.replace(/^﻿/,'').split(/\r\n|\r|\n/);
  if(L.length&&L[L.length-1]==='')L.pop();
  const P=[];
  for(let i=0;i+1<L.length;i+=2){const c=L[i].trim();
    if(!/^-?\d+$/.test(c))fail(`ligne ${i+1} : code de groupe « ${c.slice(0,20)} » illisible (fichier non DXF ou abîmé)`);
    P.push([+c,L[i+1].trim()])}
  const n=P.length;
  if(!n||P[n-1][0]!==0||P[n-1][1]!=='EOF')fail('fichier incomplet : marque de fin EOF absente');
  return P;
}

// Paires → sections {NOM:[[code,val]…]}
function sections(P){
  const S={};let cur=null;
  for(let i=0;i<P.length;i++){const [c,v]=P[i];
    if(c===0&&v==='SECTION'){const nm=P[i+1];if(!nm||nm[0]!==2)fail('section sans nom');cur=S[nm[1]]=[];i++}
    else if(c===0&&v==='ENDSEC')cur=null;
    else if(cur)cur.push(P[i])}
  return S;
}

// Section → objets {type, g:[[code,val]…]} (une entrée par code 0)
function objets(sec){const O=[];for(const [c,v] of sec||[]){if(c===0)O.push({type:v,g:[]});else if(O.length)O[O.length-1].g.push([c,v])}return O}
const val=(o,c)=>{const x=o.g.find(p=>p[0]===c);return x?x[1]:undefined};
const num=(o,c,d)=>{const x=val(o,c);if(x===undefined)return d;const n=+x;if(!Number.isFinite(n))fail(`${o.type} : valeur ${c} illisible`);return n};

// Repère de l'entité (OCS) : (0,0,1) normal, (0,0,-1) = symétrie (X → -X) ; autre → hors plan
function repere(o){const z=[num(o,210,0),num(o,220,0),num(o,230,1)];
  if(Math.abs(z[0])<1e-9&&Math.abs(z[1])<1e-9)return z[2]>0?1:-1;return 0}

// En-tête : $INSUNITS et $ACADVER
function entete(sec){const H={};let k=null;for(const [c,v] of sec||[]){if(c===9)k=v;else if(k&&!(k in H))H[k]=v}return H}

function decoder(txt,nom){
  const S=sections(paires(txt));
  if(!S.ENTITIES)fail('section ENTITIES absente');
  const H=entete(S.HEADER),iu=H.$INSUNITS===undefined?0:+H.$INSUNITS;
  if(!Number.isInteger(iu)||iu<0)fail('$INSUNITS illisible');
  if(iu&&!UNITES[iu])fail(`unité du fichier non prise en charge : ${NOMS_U[iu]||'code '+iu} (mm, cm ou m attendus)`);
  const calques=objets(S.TABLES).filter(o=>o.type==='LAYER').map(o=>val(o,2)).filter(x=>x!==undefined);
  const E=objets(S.ENTITIES),entites=[],X=espaces(S);let n=0;
  const base=o=>{n++;const h=val(o,5);return Object.assign({id:h!==undefined?h:'#'+n,calque:val(o,8)===undefined?'0':val(o,8)},X.de(o))};
  const autre=(o,b,nature)=>entites.push(Object.assign(b,{type:'autre',nature}));
  // contour : fermé par le drapeau 1, ou dernier sommet = premier (dessin non « fermé » mais refermé exactement)
  // largeur non nulle : la ligne médiane n'est pas le contour exact du vide → non prise en charge
  const poly=(o,b,pts,f,bulge,large)=>{const s=repere(o);
    if(!s)return autre(o,b,o.type+' hors du plan XY');
    if(bulge)return autre(o,b,o.type+' avec arcs');
    if(large)return autre(o,b,o.type+' avec largeur non nulle');
    if(pts.length<2)return autre(o,b,o.type+' de moins de 2 sommets');
    const P=pts.map(p=>[s*p[0],p[1]]),z=P[P.length-1];
    entites.push(Object.assign(b,{type:'polyligne',points:P,ferme:!!(f&1)||(P.length>3&&z[0]===P[0][0]&&z[1]===P[0][1])}))};
  for(let i=0;i<E.length;i++){const o=E[i],b=base(o);
    if(o.type==='CIRCLE'){const s=repere(o),r=num(o,40,NaN);
      if(!s)autre(o,b,'CIRCLE hors du plan XY');
      else entites.push(Object.assign(b,{type:'cercle',centre:[s*num(o,10,NaN),num(o,20,NaN)],r}))}
    else if(o.type==='LWPOLYLINE'){const pts=[];let bulge=false,large=false;
      for(const [c,v] of o.g){if(c===10)pts.push([+v,NaN]);else if(c===20&&pts.length)pts[pts.length-1][1]=+v;else if(c===42&&+v!==0)bulge=true;else if((c===40||c===41||c===43)&&+v!==0)large=true}
      if(pts.some(p=>!p.every(Number.isFinite)))fail(`LWPOLYLINE ${b.id} : sommet illisible`);
      poly(o,b,pts,num(o,70,0),bulge,large)}
    else if(o.type==='POLYLINE'){const f=num(o,70,0),pts=[];let bulge=false,lisse=false,large=num(o,40,0)!==0||num(o,41,0)!==0;
      for(i++;i<E.length&&E[i].type==='VERTEX';i++){const v=E[i];pts.push([num(v,10,NaN),num(v,20,NaN)]);
        if(num(v,42,0)!==0)bulge=true;if(num(v,40,0)!==0||num(v,41,0)!==0)large=true;
        if(num(v,70,0)&(1|8|16))lisse=true}   // sommet ajouté par lissage, sommet de spline, point de contrôle de spline
      if(!E[i]||E[i].type!=='SEQEND')fail(`POLYLINE ${b.id} : fin SEQEND absente`);
      if(pts.some(p=>!p.every(Number.isFinite)))fail(`POLYLINE ${b.id} : sommet illisible`);
      if(f&(8|16|64))autre(o,b,'POLYLINE 3D ou maillage');
      else if(f&2||f&4||lisse)autre(o,b,'POLYLINE lissée (courbe ajustée ou spline)');   // 70 : bit 2 = courbe ajustée, bit 4 = spline
      else poly(o,b,pts,f,bulge,large)}
    else if(o.type==='LINE'){autre(o,b,'LINE');const S=[[num(o,10,NaN),num(o,20,NaN)],[num(o,11,NaN),num(o,21,NaN)]];
      if(S.flat().every(Number.isFinite)&&num(o,30,0)===num(o,31,0))b.segment=S}   // côté possible d'un rectangle en 4 LINE (detecteur.js)
    else autre(o,b,o.type==='INSERT'?'INSERT (bloc non décomposé)':o.type)}
  return Object.assign({format:'dxf',fichier:nom==null?'':String(nom),unite:iu?UNITES[iu]:null,version:H.$ACADVER||null,
    calques:[...new Set(calques.concat(entites.map(e=>e.calque)))],entites},annexes(S,E,X));
}

// Espaces AutoCAD. Entité : code 67 = 1 → espace papier ; propriétaire (330) → BLOCK_RECORD (table) → LAYOUT (objets) pour
// le nom de la présentation. Les présentations non actives sont dans BLOCKS (*Paper_Space0, 1…). R12 : pas de nom (null).
function espaces(S){
  const lay={},br={};
  for(const o of objets(S.OBJECTS))if(o.type==='LAYOUT'&&val(o,5)!==undefined){const n=o.g.filter(p=>p[0]===1).pop();if(n&&n[1])lay[val(o,5)]=n[1]}
  for(const o of objets(S.TABLES))if(o.type==='BLOCK_RECORD'&&val(o,5)!==undefined)br[val(o,5)]={nom:val(o,2)||'',lay:val(o,340)};
  const nomBR=h=>{const b=br[h];return b?lay[b.lay]||(/^\*paper_space/i.test(b.nom)?b.nom:null):null};
  const actif=Object.keys(br).find(h=>/^\*paper_space$/i.test(br[h].nom));
  return{nomBR,presentations:[...new Set(Object.values(lay))].filter(x=>x.toLowerCase()!=='model'),
    de:o=>+val(o,67)===1?{espace:'papier',presentation:nomBR(val(o,330))||(actif?nomBR(actif):null)}:{espace:'objet',presentation:null}};
}

// Textes : %%c → Ø, %%d → °, %%p → ±, soulignés supprimés ; MTEXT : mise en forme retirée, \P = retour à la ligne
const uni=s=>s.replace(/\\U\+([0-9a-fA-F]{4})/g,(m,h)=>String.fromCharCode(parseInt(h,16)));
const pct=s=>s.replace(/%%(\d{3})/g,(m,c)=>String.fromCharCode(+c)).replace(/%%[cC]/g,'Ø').replace(/%%[dD]/g,'°').replace(/%%[pP]/g,'±').replace(/%%[uUoOkK]/g,'').replace(/%%%/g,'%');
const txtBrut=s=>pct(uni(s));
function mtextBrut(s){
  return pct(uni(s).replace(/\\\\/g,'\u0001').replace(/\\[{}]/g,m=>m[1]==='{'?'\u0002':'\u0003')
    .replace(/\\P/g,'\n').replace(/\\~/g,' ').replace(/\\S([^;]*?)[\^\/#]([^;]*);/g,'$1/$2')
    .replace(/\\[ACcFfHhQTWp][^;]*;/g,'').replace(/\\M\+[0-9a-fA-F]{5}/g,'?').replace(/\\[LlOoKkNX]/g,'').replace(/[{}]/g,'')
    .replace(/\u0001/g,'\\').replace(/\u0002/g,'{').replace(/\u0003/g,'}'));
}

// Matrices 2D [a,b,c,d,e,f] : x' = a·x + c·y + e, y' = b·x + d·y + f
const app=(M,x,y)=>[M[0]*x+M[2]*y+M[4],M[1]*x+M[3]*y+M[5]];
const mul=(A,B)=>[A[0]*B[0]+A[2]*B[1],A[1]*B[0]+A[3]*B[1],A[0]*B[2]+A[2]*B[3],A[1]*B[2]+A[3]*B[3],A[0]*B[4]+A[2]*B[5]+A[4],A[1]*B[4]+A[3]*B[5]+A[5]];
const rotM=a=>{const c=Math.cos(a),s=Math.sin(a);return[c,s,-s,c,0,0]};
const BUDGET=500000;   // shortcut: au-delà de 500 000 textes + traits (fichiers énormes), le reste n'est pas relevé ; signalé

// Textes et traits de tous les espaces : ENTITIES (Objet + présentation active), présentations de BLOCKS, contenu des blocs
// insérés (INSERT ; ACAD_TABLE par son bloc de rendu *T…), transformé dans le repère de l'espace qui les contient.
// Texte : {id, calque, espace, presentation, nature, texte, x, y (centre estimé), h, w (largeur estimée), rot (°), bloc?, fleches?}
// Trait : {calque, espace, presentation, a:[x,y], b:[x,y]}. Coordonnées propres à chaque espace : jamais mélangées.
function annexes(S,E,X){
  const textes=[],traits=[],sig=new Set(),blocs={},fl={};let cur=null,nb=0;
  for(const o of objets(S.BLOCKS)){if(o.type==='BLOCK'){cur={nom:val(o,2)||'',br:val(o,330),base:[+val(o,10)||0,+val(o,20)||0],E:[]};blocs[cur.nom.toUpperCase()]=cur}
    else if(o.type==='ENDBLK')cur=null;else if(cur)cur.E.push(o)}
  const plein=()=>{if(++nb<=BUDGET)return false;sig.add('fichier très chargé : textes et traits au-delà de '+BUDGET+' non relevés');return true};
  // texte d'une ligne : centre estimé (largeur ≈ 0,6 h par caractère) selon le point d'insertion et la justification
  function pose(c,M,t,ox,oy,h,rot,dx,dy){if(plein())return;const r=rot*Math.PI/180,u=[Math.cos(r),Math.sin(r)],p=app(M,ox+dx*u[0]-dy*u[1],oy+dx*u[1]+dy*u[0]),
    k=Math.sqrt(Math.abs(M[0]*M[3]-M[1]*M[2]))||1;
    textes.push(Object.assign({},c,{texte:t,x:p[0],y:p[1],h:h*k,w:t.length*0.6*h*k,rot:((rot+Math.atan2(M[1],M[0])*180/Math.PI)%360+360)%360}))}
  function trait(c,M,a,b){if(plein())return;traits.push({calque:c.calque,espace:c.espace,presentation:c.presentation,a:app(M,a[0],a[1]),b:app(M,b[0],b[1])})}
  function walk(L,M,c0,pre,prof){
    for(let i=0;i<L.length;i++){const o=L[i],ty=o.type,sg=repere(o);
      let cal=val(o,8)===undefined?'0':val(o,8);if(cal==='0'&&c0.calque)cal=c0.calque;   // calque 0 dans un bloc : celui de l'insertion
      const h5=val(o,5),sp=c0.de?c0.de(o):c0,c={id:pre+(h5!==undefined?h5:'#'+i),calque:cal,espace:sp.espace,presentation:sp.presentation};if(c0.bloc)c.bloc=c0.bloc;
      const Mo=sg===-1?mul(M,[-1,0,0,1,0,0]):M;
      if(!sg&&ty!=='MULTILEADER')continue;
      if(ty==='TEXT'||ty==='ATTRIB'){if(ty==='ATTRIB'&&num(o,70,0)&1)continue;const t=txtBrut(val(o,1)||'').trim();if(!t)continue;
        const h=num(o,40,0),ha=num(o,72,0),va=num(o,ty==='TEXT'?73:74,0),p=[num(o,10,0),num(o,20,0)],q=ha||va?[num(o,11,p[0]),num(o,21,p[1])]:p,w=t.length*0.6*h;
        if(ha===3||ha===5)pose(Object.assign(c,{nature:ty}),Mo,t,(p[0]+q[0])/2,(p[1]+q[1])/2,h,num(o,50,0),0,h/2);
        else pose(Object.assign(c,{nature:ty}),Mo,t,q[0],q[1],h,num(o,50,0),ha===1||ha===4?0:ha===2?-w/2:w/2,va===2?0:va===3?-h/2:h/2)}
      else if(ty==='MTEXT'){const brut=o.g.filter(p=>p[0]===3).map(p=>p[1]).join('')+(val(o,1)||''),L2=mtextBrut(brut).split('\n').map(x=>x.trim());
        const h=num(o,40,0),at=num(o,71,1),ec=h*5/3*num(o,44,1),n=L2.length,H=(n-1)*ec+h,col=(at-1)%3,row=Math.floor((at-1)/3),
          rot=val(o,50)!==undefined?num(o,50,0)*180/Math.PI:val(o,11)!==undefined?Math.atan2(num(o,21,0),num(o,11,1))*180/Math.PI:0;
        L2.forEach((t,j)=>{if(!t)return;const w=t.length*0.6*h;
          pose(Object.assign({},c,{id:c.id+(n>1?'#'+(j+1):''),nature:'MTEXT'}),Mo,t,num(o,10,0),num(o,20,0),h,rot,col===0?w/2:col===2?-w/2:0,(row===0?0:row===1?H/2:H)-h/2-j*ec)})}
      else if(ty==='MULTILEADER'){let t=null,p=null,h=0,ll=false,f=[];
        for(const [k,v] of o.g){if(k===304&&v==='LEADER_LINE{')ll=true;else if(k===305)ll=false;else if(k===304&&t===null)t=v;
          else if(k===12&&!p)p=[+v,NaN];else if(k===22&&p&&isNaN(p[1]))p[1]=+v;else if(k===41&&!h)h=+v;
          else if(ll&&k===10)f.push([+v,NaN]);else if(ll&&k===20&&f.length&&isNaN(f[f.length-1][1]))f[f.length-1][1]=+v}
        f=f.filter(q=>q.every(Number.isFinite)).map(q=>app(M,q[0],q[1]));
        if(t&&p&&p.every(Number.isFinite))mtextBrut(t).split('\n').map(x=>x.trim()).forEach((x,j,A)=>{if(!x)return;
          pose(Object.assign({},c,{id:c.id+(A.length>1?'#'+(j+1):''),nature:'MULTILEADER',fleches:f}),M,x,p[0],p[1],h,0,x.length*0.3*h,-h/2-j*h*5/3)})}
      else if(ty==='LEADER'){const a=val(o,340);if(a!==undefined&&val(o,10)!==undefined)(fl[pre+a]=fl[pre+a]||[]).push(app(Mo,num(o,10,0),num(o,20,0)))}
      else if(ty==='LINE')trait(c,Mo,[num(o,10,0),num(o,20,0)],[num(o,11,0),num(o,21,0)]);
      else if(ty==='LWPOLYLINE'||ty==='POLYLINE'){let P=[],bul=false,f=num(o,70,0);
        if(ty==='LWPOLYLINE'){for(const [k,v] of o.g){if(k===10)P.push([+v,NaN]);else if(k===20&&P.length)P[P.length-1][1]=+v;else if(k===42&&+v)bul=true}}
        else for(i++;i<L.length&&L[i].type==='VERTEX';i++){P.push([num(L[i],10,0),num(L[i],20,0)]);if(num(L[i],42,0))bul=true}
        if(bul||f&(8|16|64)||P.some(q=>!q.every(Number.isFinite)))continue;
        for(let j=0;j+1<P.length;j++)trait(c,Mo,P[j],P[j+1]);if(f&1&&P.length>2)trait(c,Mo,P[P.length-1],P[0])}
      else if(ty==='INSERT'||ty==='ACAD_TABLE'){const B=blocs[String(val(o,2)||'').toUpperCase()];
        if(!B){sig.add(ty==='ACAD_TABLE'?'tableau AutoCAD (ACAD_TABLE) sans bloc de rendu : non lu':'bloc inséré introuvable : '+(val(o,2)||'?'));continue}
        if(prof>=8){sig.add('blocs imbriqués sur plus de 8 niveaux : non lus');continue}
        if(ty==='INSERT'&&(num(o,70,1)>1||num(o,71,1)>1))sig.add('MINSERT (blocs en réseau) : seule la première occurrence est lue');
        const r=ty==='ACAD_TABLE'?Math.atan2(num(o,21,0),num(o,11,1)):num(o,50,0)*Math.PI/180,sx=ty==='ACAD_TABLE'?1:num(o,41,1),sy=ty==='ACAD_TABLE'?1:num(o,42,1);
        const Mi=mul(Mo,mul([1,0,0,1,num(o,10,0),num(o,20,0)],mul(rotM(r),[sx,0,0,sy,-sx*B.base[0],-sy*B.base[1]])));
        walk(B.E,Mi,{calque:cal,espace:c.espace,presentation:c.presentation,bloc:c0.bloc||B.nom},c.id+'/',prof+1)}}
  }
  walk(E,[1,0,0,1,0,0],{de:X.de},'',0);   // ENTITIES : espace propre à chaque entité (code 67)
  for(const B of Object.values(blocs))if(/^\*paper_space\d+$/i.test(B.nom))walk(B.E,[1,0,0,1,0,0],{espace:'papier',presentation:X.nomBR(B.br)||B.nom},'',0);
  textes.forEach(t=>{const f=fl[t.id.split('#')[0]];if(f)t.fleches=(t.fleches||[]).concat(f)});
  return{presentations:X.presentations,textes,traits,signalements:[...sig]};
}

if(!root.CPI||!root.CPI.lecteur)throw new Error('dxf.js : charger lecteur.js avant');
root.CPI.lecteur.DECODEURS.dxf=decoder;
root.CPI.dxf={decoder,paires};
})(typeof globalThis!=='undefined'?globalThis:this);
