// CoffraPlan — module d'import de plans : décodeur DXF ASCII (inscrit dans CPI.lecteur.DECODEURS.dxf).
// Lit la section ENTITIES (LWPOLYLINE, POLYLINE R12 + VERTEX, CIRCLE ; le reste → « autre »), l'unité $INSUNITS et la
// table des calques. Charger après lecteur.js. Indépendant de l'interface et du moteur.
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
  const E=objets(S.ENTITIES),entites=[];let n=0;
  const base=o=>{n++;const h=val(o,5);return{id:h!==undefined?h:'#'+n,calque:val(o,8)===undefined?'0':val(o,8)}};
  const autre=(o,b,nature)=>entites.push(Object.assign(b,{type:'autre',nature}));
  // contour : fermé par le drapeau 1, ou dernier sommet = premier (dessin non « fermé » mais refermé exactement)
  const poly=(o,b,pts,f,bulge)=>{const s=repere(o);
    if(!s)return autre(o,b,o.type+' hors du plan XY');
    if(bulge)return autre(o,b,o.type+' avec arcs');
    if(pts.length<2)return autre(o,b,o.type+' de moins de 2 sommets');
    const P=pts.map(p=>[s*p[0],p[1]]),z=P[P.length-1];
    entites.push(Object.assign(b,{type:'polyligne',points:P,ferme:!!(f&1)||(P.length>3&&z[0]===P[0][0]&&z[1]===P[0][1])}))};
  for(let i=0;i<E.length;i++){const o=E[i],b=base(o);
    if(o.type==='CIRCLE'){const s=repere(o),r=num(o,40,NaN);
      if(!s)autre(o,b,'CIRCLE hors du plan XY');
      else entites.push(Object.assign(b,{type:'cercle',centre:[s*num(o,10,NaN),num(o,20,NaN)],r}))}
    else if(o.type==='LWPOLYLINE'){const pts=[];let bulge=false;
      for(const [c,v] of o.g){if(c===10)pts.push([+v,NaN]);else if(c===20&&pts.length)pts[pts.length-1][1]=+v;else if(c===42&&+v!==0)bulge=true}
      if(pts.some(p=>!p.every(Number.isFinite)))fail(`LWPOLYLINE ${b.id} : sommet illisible`);
      poly(o,b,pts,num(o,70,0),bulge)}
    else if(o.type==='POLYLINE'){const f=num(o,70,0),pts=[];let bulge=false;
      for(i++;i<E.length&&E[i].type==='VERTEX';i++){const v=E[i];pts.push([num(v,10,NaN),num(v,20,NaN)]);if(num(v,42,0)!==0)bulge=true}
      if(!E[i]||E[i].type!=='SEQEND')fail(`POLYLINE ${b.id} : fin SEQEND absente`);
      if(pts.some(p=>!p.every(Number.isFinite)))fail(`POLYLINE ${b.id} : sommet illisible`);
      if(f&(8|16|64))autre(o,b,'POLYLINE 3D ou maillage');else poly(o,b,pts,f,bulge)}
    else autre(o,b,o.type==='INSERT'?'INSERT (bloc non décomposé)':o.type)}
  return{format:'dxf',fichier:nom==null?'':String(nom),unite:iu?UNITES[iu]:null,version:H.$ACADVER||null,
    calques:[...new Set(calques.concat(entites.map(e=>e.calque)))],entites};
}

if(!root.CPI||!root.CPI.lecteur)throw new Error('dxf.js : charger lecteur.js avant');
root.CPI.lecteur.DECODEURS.dxf=decoder;
root.CPI.dxf={decoder,paires};
})(typeof globalThis!=='undefined'?globalThis:this);
