// CoffraPlan — module d'import de plans : rapprochement nomenclature ↔ dessin d'un PDF (phase 4).
// La nomenclature est la référence des cotes de fabrication ; le dessin identifie et localise la réservation et, quand il le
// peut, contrôle ses cotes. Indices, tous déterministes : repère identique (texte du PDF ou lu par OCR, avec sa fiabilité),
// ligne de rappel, contour voisin (CPI.geometrie), cotes écrites près du repère ou du contour (une seule suffit à confirmer
// une dimension), mesure du contour si la page a une échelle. Une cote absente n'est jamais un conflit ; une cote différente
// n'en est un que si elle décrit la même dimension (cote écrite complète « l x h » ou « Ø », unité connue ou de même ordre de
// grandeur) ; une mesure différente n'est qu'une remarque (vue, coupe, échelle). Aucune cote n'est remplacée ici.
// Interpages : un repère identique rapproche une ligne d'un dessin d'une autre page ; des cotes seules, jamais (et sur la page
// du tableau seulement, en « probable »). Plusieurs localisations d'un repère = preuves d'une seule entrée (vues, coupes,
// détails) ; la quantité de la nomenclature est gardée et comparée, jamais déduite du nombre de vues.
// Indépendant de l'interface et du moteur. Charger après nomenclatures.js et geometrie.js.
(function(root){'use strict';
const MM={mm:1,cm:10,m:1000};
const OCR_MIN=30;   // % : en dessous, un mot lu par OCR n'est pas proposé comme repère, même incertain (bruit de traits, flèches, cotes tournées)
const NB=n=>(n.match(/\d+/)||[''])[0];
// Clé de repère tolérante aux confusions de lecture (S/5, O/0, I/1, L/1, B/8, Z/2, G/6, A/4 après les lettres du début) : rapprochement « incertain »
const CONF={S:'5',O:'0',I:'1',L:'1',B:'8',Z:'2',G:'6',A:'4'};
const cleFloue=k=>k.replace(/^([A-Z]+?)([A-Z0-9]*)$/,(m,a,b)=>a+[...b].map(c=>/\d/.test(c)?c:CONF[c]||c).join('')).replace(/(^|[^0-9])0+(?=\d)/g,'$1');

// Confiance OCR du repère lui-même : mots du bloc qui le composent (un trait de rappel lu « | » ou « / » à côté ne le dégrade pas)
function confRep(t,k,cleRep){const o=t.ocr;if(!o)return 100;const M=(o.mots||[]).filter(m=>{const z=cleRep(String(m.t).replace(/[^\p{L}\p{N}]+/gu,''));return z&&k.includes(z)});
  return M.length?Math.min(...M.map(m=>m.c)):o.conf}
// Textes rangés en colonne (≥ 5 alignés, régulièrement espacés) : colonne d'un tableau non reconnu, jamais une localisation
function colonnes(T){const ex=new Set(),P={};T.forEach(t=>(P[t.page]=P[t.page]||[]).push(t));
  Object.values(P).forEach(L=>[t=>t.x-(t.w||0)/2,t=>t.x].forEach(fx=>{const S=L.slice().sort((a,b)=>fx(a)-fx(b));let g=[];
    const fin=()=>{g.sort((a,b)=>a.y-b.y);let c=[g[0]];for(let i=1;i<=g.length;i++){const t=g[i];if(t&&t.y-c[c.length-1].y<=2.6*Math.max(t.h,1))c.push(t);else{if(c.length>=5)c.forEach(u=>ex.add(u.id));c=t?[t]:[]}}};
    S.forEach(t=>{if(g.length&&fx(t)-fx(g[0])>0.6*Math.max(t.h,1)){fin();g=[]}g.push(t)});if(g.length)fin()}));
  return ex}

// Clés d'un texte : texte entier sans ponctuation ni espaces, et chacun de ses mots (« |D16 », « D8 / », « D 7 » lus par OCR)
function cles(t,cleRep){const s=String(t.texte||''),K=new Set(),z=cleRep(s.replace(/[^\p{L}\p{N}\s]+/gu,' '));if(z)K.add(z);
  s.split(/[\s,;:()[\]{}|/\\]+/).forEach(w=>{const k=cleRep(w.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu,''));if(k)K.add(k)});return K}

// Comparaison de valeurs (tableau en unité uT, dessin en unité uA) : même valeur à 1 % ou 2 mm ; unité du dessin non écrite :
// essayée en mm, cm et m (« 40x40 » d'un plan en cm = 400x400 mm) → {ok, u} ; comparable = même ordre de grandeur ou unité écrite
function egal(vT,uT,vA,uA){const kT=MM[uT]||1,UA=uA?[uA]:uT?['mm','cm','m']:[null];
  for(const u of UA){const kA=u?MM[u]:kT,x=vT*kT,y=vA*kA;if(Math.abs(x-y)<=Math.max(uT||u?2:0,0.01*Math.max(x,y)))return{ok:true,u}}return{ok:false}}
const comparable=(vT,uT,vA,uA)=>!!uA||(()=>{const r=vA*(MM[uA]||MM[uT]||1)/(vT*(MM[uT]||1));return r>=0.5&&r<=2})();

// Nature d'une mention du repère k dans le texte t : 'repere' (isolé : localise la réservation) ou mention qui n'en localise aucune,
// gardée comme observation non rattachée avec son motif : 'multiplicateur'
// (« 2x D10-EXT », « 5x D11 » : note, liste), 'identifiant' (« 1-D1 », « D10-EXT » : panneau, armature, élément standard ; seulement
// si le repère du tableau n'a pas de tiret), 'annotation' (autres mots autour du repère : renvoi, note). T = textes de la page.
const MULT=/^\d+\s*[x×]$/i;
function natureMention(t,k,dashR,T,cleRep,cotes){const s=String(t.texte||''),h=Math.max(t.h||2,1);
  const W=s.split(/\s+/).filter(Boolean),gauche=T.find(u=>u!==t&&u.page===t.page&&Math.abs(u.y-t.y)<=0.5*h&&u.x<t.x&&t.x-(t.w||0)/2-(u.x+(u.w||0)/2)<=1.5*h&&MULT.test(String(u.texte).trim().split(/\s+/).pop()));
  if(W.some(w=>MULT.test(w))||gauche)return['multiplicateur',`quantité « ${(W.find(w=>MULT.test(w))||String(gauche.texte).trim())} » devant le repère (note, liste) : pas une localisation`];
  if(!dashR&&/[\p{L}\p{N}][-–—]|[-–—][\p{L}\p{N}]/u.test(s))return['identifiant',`identifiant composé « ${s.trim()} » (panneau, armature, élément ?) : pas un repère de réservation isolé`];
  const autres=W.map(w=>w.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu,'')).filter(w=>(w.match(/\p{L}/gu)||[]).length>=2&&cleFloue(cleRep(w))!==cleFloue(k)&&!/^(rect|circ|seul)$/.test(cotes(w,null).etat));   // « DS » lu pour D5 : le repère lui-même
  if(autres.length)return['annotation',`mention dans un texte (« ${s.trim()} ») : renvoi ou annotation, pas un repère isolé`];
  return['repere',null]}

// L = {id, repere, dims ({type:'rect',a,b}|{type:'circ',D}|null), unite, quantite, page (page du tableau), ids}
// textes : textes du dessin (PDF et OCR ; ceux des tableaux déjà retirés) ; C : candidats de CPI.geometrie (toutes pages)
// o = {mm: candidat → mm par point | null, rappels: texte → pointes [[x,y]] (lignes de rappel), exclus: Set d'ids de textes,
//      vue: (page, x, y) → id de vue | null (CPI.vues.situer) : contours et cotes voisines cherchés dans la vue du repère seulement,
//      vueIncertaine: id → vrai si les limites de la vue sont incertaines (aucune confirmation automatique)}
// → {lignes: {idLigne: résultat}, hors: [{texte, page, x, y, conf}], colonnes: nb de textes écartés (colonnes de tableau)}
function rapprocher(lignes,textes,C,o){o=o||{};const N=root.CPI.nomenclatures,cleRep=N.cleRep,cotes=N.cotes,dGeo=N.dGeo,ex=o.exclus||new Set();
  const T0=textes.filter(t=>!ex.has(t.id)&&t.page),col=colonnes(T0),T=T0.filter(t=>!col.has(t.id));
  const K=new Map(T.map(t=>[t.id,cles(t,cleRep)])),OK=C.map((c,i)=>({c,i})).filter(x=>x.c.statut==='a_confirmer'&&x.c.source&&x.c.source.page);
  const kLigne=new Map(lignes.map(L=>[L.id,cleRep(L.repere||'')])),toutes=new Set([...kLigne.values()].filter(Boolean));
  const R={},vue=o.vue||(()=>null),vC=new Map(OK.map(({c,i})=>[i,vue(c.source.page,c.centre[0],c.centre[1])]));
  lignes.forEach(L=>{const k=kLigne.get(L.id),num=/^\d+$/.test(k),occ=[];
    if(k)T.forEach(t=>{const ks=K.get(t.id);let flou=false;
      if(num){if(cleRep(String(t.texte).replace(/[^\p{L}\p{N}]+/gu,''))!==k)return}   // repère numérique : texte entier seulement
      else if(!ks.has(k)){if(!t.ocr||![...ks].some(x=>cleFloue(x)===cleFloue(k)&&!toutes.has(x)))return;flou=true}
      // lecture presque illisible (« —— DS) | » à 2 %) : bruit, pas un indice
      const pq=[],cf=confRep(t,k,cleRep);if(t.ocr&&cf<OCR_MIN)return;if(t.ocr&&(cf<root.CPI.ocr.SEUIL||(t.ocr.corrections||[]).length))pq.push(`lecture OCR incertaine (« ${t.ocr.brut} », confiance ${cf} %)`);
      if(flou)pq.push(`lu « ${t.texte} » : rapproché par confusion de lettres et de chiffres`);if(num)pq.push('repère purement numérique');
      const [nat,mn]=natureMention(t,k,/[-–—]/.test(L.repere||''),T,cleRep,cotes);if(mn)pq.push(mn);
      occ.push({t,fiable:!pq.length,doutes:pq,conf:cf,nature:nat,motifNature:mn})});
    // contour désigné par chaque localisation : le plus proche du repère ou du bout de sa ligne de rappel (≤ 4 hauteurs de texte)
    occ.forEach(x=>{const t=x.t,P=[[t.x,t.y]],h=Math.max(t.h||2,1),vt=x.vue=vue(t.page,t.x,t.y);x.vinc=!!(vt&&o.vueIncertaine&&o.vueIncertaine(vt));if(o.rappels)try{x.rappels=o.rappels(t)}catch(e){x.rappels=[]}else x.rappels=[];P.push(...x.rappels);
      const V=OK.filter(({c,i})=>c.source.page===t.page&&vC.get(i)===vt).map(({c,i})=>{let d=Infinity;for(const p of P)d=Math.min(d,dGeo(p,c.geometrie));return{i,d}}).filter(v=>v.d<=4*h).sort((a,b)=>a.d-b.d);
      x.contours=V;x.contour=V.length===1||V.length>1&&V[1].d>1.25*V[0].d+0.5*h?V[0].i:null;
      // cotes écrites voisines : près du repère (6 hauteurs) ou du contour désigné (4 hauteurs)
      const cc=x.contour!=null?C[x.contour].geometrie:null;x.cotes=[];
      T.forEach(u=>{if(u===t||u.page!==t.page||[...K.get(u.id)].some(z=>toutes.has(z))||vue(u.page,u.x,u.y)!==vt)return;const q=cotes(u.texte,null);if(!/^(rect|circ|seul)$/.test(q.etat))return;
        const d=Math.hypot(u.x-t.x,u.y-t.y),dc=cc?dGeo([u.x,u.y],cc):Infinity;if(d<=6*h||dc<=4*Math.max(u.h||h,1))x.cotes.push(Object.assign({texte:u.texte,id:u.id,d:Math.min(d,dc),ocr:!!u.ocr},q))});
      x.cotes.sort((a,b)=>a.d-b.d);x.cotes=x.cotes.slice(0,4)});
    // vue aux limites incertaines : son contour n'est jamais proposé d'office ni ses cotes voisines tenues pour une confirmation forte
    occ.forEach(x=>{if(x.vinc)x.doutes.push(`vue ${x.vue} aux limites incertaines : contour et cotes voisines à confirmer`)});
    R[L.id]=verifier(L,occ,C,o)});
  // dimensions seules : contours de la page du tableau, de mêmes cotes mesurées, non désignés par un repère → « probable »
  const pris=new Set();Object.values(R).forEach(r=>r.preuves.forEach(i=>pris.add(i)));
  lignes.forEach(L=>{const r=R[L.id];if(r.occurrences.length)return;
    const M=L.dims&&o.mm&&MM[L.unite]?OK.filter(({c,i})=>!pris.has(i)&&c.source.page===L.page&&mesure(L,c,o.mm(c))==='ok').map(({c,i})=>({c:i,id:c.id,d:null,via:'cotes',cotes:'ok'})):[];
    r.options=M;r.concordance=M.length?'probable':'absente';r.statut=M.length===1?'probable':M.length>1?'multiple':'absente';
    r.note=(kLigne.get(L.id)?'repère non trouvé sur le dessin':'ligne sans repère')+(M.length===1?' ; un contour de mêmes cotes mesurées sur la page du tableau (cotes seules : à vérifier)':M.length>1?` ; ${M.length} contours de mêmes cotes mesurées (cotes seules : à vérifier)`:'')});
  // repères hors nomenclature : textes de même préfixe que les repères du tableau (« D24 »), sans ligne correspondante
  const pre=new Set([...toutes].map(k=>(k.match(/^[A-Z]+/)||[''])[0]).filter(Boolean)),vu=new Set(),hors=[];
  T.forEach(t=>{[...K.get(t.id)].forEach(z=>{const m=z.match(/^([A-Z]{1,3})(\d{1,4})$/);if(!m||!pre.has(m[1])||toutes.has(z)||[...toutes].some(k=>cleFloue(k)===cleFloue(z))||vu.has(z+'|'+t.page))return;
    vu.add(z+'|'+t.page);hors.push({texte:z,page:t.page,x:t.x,y:t.y,h:t.h,conf:t.ocr?t.ocr.conf:null})})});
  return{lignes:R,hors,colonnes:col.size}}

// Mesure d'un contour (mm à l'échelle de sa page) comparée aux cotes du tableau : 'ok' | 'diff' | '?' (à 5 % : mesure sur un PDF)
function mesure(L,c,k){const d=L.dims,kT=MM[L.unite];if(!d||!kT||!(k>0)||!c.dims)return'?';const eq=(x,y)=>Math.abs(x-y)<=Math.max(5,0.05*Math.max(x,y));
  if(d.type==='circ')return c.type==='circ'?eq(d.D*kT,c.dims.D*k)?'ok':'diff':'?';
  return c.type==='rect'?eq(Math.max(d.a,d.b)*kT,c.dims.L*k)&&eq(Math.min(d.a,d.b)*kT,c.dims.l*k)?'ok':'diff':'?'}

// Vérification des cotes d'une ligne sur ses localisations, concordance, quantité
function verifier(L,occ,C,o){const d=L.dims,uT=L.unite||null,D={},notes=[];
  const noms=!d?[]:d.type==='circ'?[['D','Ø'+NB(String(d.D))]]:[['a',String(d.a)],['b',String(d.b)]];
  noms.forEach(([n,lb])=>D[n]={valeur:d[n],libelle:lb,etat:'non_verifiable',preuves:[]});
  const met=(n,etat,p)=>{const x=D[n];const r={conflit:3,confirmee:2,mesuree:1,non_verifiable:0};if(r[etat]>r[x.etat])x.etat=etat;x.preuves.push(p)};
  occ.forEach(x=>{if(!d||!x.fiable)return;const ou=`p. ${x.t.page}`;   // repère incertain : rien n'est confirmé par lui
    x.cotes.forEach(q=>{const src=`cote écrite « ${q.texte} » (${ou}${q.ocr?', OCR':''})`;
      if(q.etat==='seul'){const n=noms.find(([n])=>egal(d[n],uT,q.v,q.unite).ok);if(n)met(n[0],'confirmee',src);else x.doutes.push(`cote voisine « ${q.texte} » : ne correspond à aucune cote du tableau (autre dimension, autre élément ?)`);return}
      if((q.etat==='circ')!==(d.type==='circ')){x.doutes.push(`cote voisine « ${q.texte} » d'une autre forme : non comparée`);return}
      if(q.etat==='circ'){const e=egal(d.D,uT,q.D,q.unite);if(e.ok)met('D','confirmee',src+(e.u&&!q.unite&&e.u!==uT?` (lue en ${e.u})`:''));
        else if(comparable(d.D,uT,q.D,q.unite))met('D','conflit',src);else x.doutes.push(`cote voisine « ${q.texte} » non comparable (unité ?)`);return}
      // « l x h » écrit : même réservation, deux dimensions ; ordre libre ; unité non écrite essayée en mm, cm, m
      const U=q.unite?[q.unite]:uT?['mm','cm','m']:[null];let best=null;
      U.forEach(u=>{const A=egal(d.a,uT,q.a,u).ok,B=egal(d.b,uT,q.b,u).ok,A2=egal(d.a,uT,q.b,u).ok,B2=egal(d.b,uT,q.a,u).ok,s1=A+B,s2=A2+B2,s=Math.max(s1,s2);
        if(!best||s>best.s)best={s,u,ok:s1>=s2?{a:A,b:B}:{a:A2,b:B2}}});
      const lu=best.u&&!q.unite&&best.u!==uT?` (lue en ${best.u})`:'';
      if(best.s===0&&!comparable(Math.max(d.a,d.b),uT,Math.max(q.a,q.b),q.unite)){x.doutes.push(`cote voisine « ${q.texte} » non comparable (unité ?)`);return}
      ['a','b'].forEach(n=>met(n,best.ok[n]?'confirmee':'conflit',src+lu))});
    // mesure du contour désigné (page à l'échelle) : confirme à 5 % près ; une mesure différente n'est qu'une remarque
    if(x.contour!=null&&o.mm){const c=C[x.contour],k=o.mm(c),m=mesure(L,c,k);
      if(m==='ok')noms.forEach(([n])=>met(n,'mesuree',`contour ${c.id} mesuré à l'échelle de la page ${c.source.page}`));
      else if(m==='diff')x.doutes.push(`contour ${c.id} : mesure différente des cotes du tableau (vue, coupe, échelle de détail ?)`)}});
  const fi=occ.filter(x=>x.fiable),ctr=[...new Set(occ.filter(x=>x.contour!=null).map(x=>x.contour))],princ=[...new Set(fi.filter(x=>x.contour!=null&&!x.vinc).map(x=>x.contour))];
  let cc;if(!occ.length)cc='absente';else if(!fi.length)cc='probable';else if(Object.values(D).some(x=>x.etat==='conflit'))cc='conflit';
  else if(noms.length&&Object.values(D).every(x=>x.etat==='confirmee'||x.etat==='mesuree')&&fi.some(x=>!x.vinc))cc='forte';else cc='partielle';
  // localisations : vues multiples (pages différentes) ou occurrences physiques (quantité) ; jamais de quantité inventée
  const Q=/^\s*\d+/.test(L.quantite||'')?parseInt(L.quantite,10):null,pp={};fi.forEach(x=>pp[x.t.page]=(pp[x.t.page]||0)+1);
  const pages=Object.keys(pp).map(Number).sort((a,b)=>a-b),mx=Math.max(0,...Object.values(pp));let lecture='';
  if(fi.length>1)lecture=mx===1?`${fi.length} localisations sur ${pages.length} pages : vues d'une même réservation probables (plan, coupe, détail)`
    :Q&&Q>1&&mx<=Q?`${mx} localisations sur la page ${pages.find(p=>pp[p]===mx)} : occurrences physiques possibles (quantité ${Q} dans la nomenclature)`
    :`${mx} localisations sur la même page : vues ou occurrences distinctes ? (${Q?'quantité '+Q+' dans la nomenclature':'quantité non indiquée'})`;
  // cohérente : autant de localisations sur une page que la quantité ; trop : false ; moins (réservations non toutes dessinées) : inconnu
  const quantite={source:L.quantite||null,valeur:Q,localisations:fi.length,pages,lecture,coherente:Q==null||!fi.length?null:mx===Q?true:mx>Q?false:null};
  const options=ctr.map(i=>({c:i,id:C[i].id,d:Math.min(...occ.filter(x=>x.contour===i).map(x=>(x.contours.find(v=>v.i===i)||{d:0}).d)),via:'repere',cotes:'?'}));
  occ.forEach(x=>{if(x.contour==null)x.contours.slice(0,3).forEach(v=>{if(!options.some(p=>p.c===v.i))options.push({c:v.i,id:C[v.i].id,d:v.d,via:'repere',cotes:'?',ambigu:true})})});
  // contour proposé d'office : un seul, ou un par page (vues d'une même réservation) ; plusieurs sur une page : à choisir
  const unique=princ.length===1||princ.length>1&&new Set(princ.map(i=>C[i].source.page)).size===princ.length;
  const statut=unique&&(cc==='forte'||cc==='partielle')?'trouvee':options.length>1?'multiple':options.length||occ.length?'probable':'absente';
  const LB={forte:'concordance forte',partielle:'concordance partielle',probable:'correspondance probable',conflit:'conflit à examiner',absente:'non retrouvée sur le dessin'};
  if(occ.length&&!princ.length)notes.push(occ.some(x=>x.contours.length>1&&x.contour==null)?'plusieurs contours possibles près du repère : à choisir':'repère localisé, aucun contour reconnu à proximité');
  if(princ.length>1)notes.push(unique?`${princ.length} contours désignés, un par page (vues) : celui de la 1re page est proposé`:`${princ.length} contours désignés sur une même page (occurrences ?) : à choisir`);
  return{concordance:cc,libelle:LB[cc],statut,options,principal:princ.length?princ.slice().sort((a,b)=>C[a].source.page-C[b].source.page)[0]:null,preuves:ctr,
    occurrences:occ.map(x=>({id:x.t.id,texte:x.t.texte,page:x.t.page,x:x.t.x,y:x.t.y,h:x.t.h,source:x.t.ocr?'ocr':'pdf',conf:x.t.ocr?x.conf:null,brut:x.t.ocr?x.t.ocr.brut:null,
      corrections:x.t.ocr?x.t.ocr.corrections:[],box:x.t.ocr?x.t.ocr.box:null,vue:x.vue||null,fiable:x.fiable,nature:x.nature,motifNature:x.motifNature,doutes:x.doutes,rappels:x.rappels,contour:x.contour!=null?C[x.contour].id:null,
      cotes:x.cotes.map(q=>q.texte)})),
    reperes:occ.map(x=>({x:x.t.x,y:x.t.y,id:x.t.id})),dims:D,quantite,note:notes.concat(lecture?[lecture]:[]).join(' ; ')}}

root.CPI=Object.assign(root.CPI||{},{rapprochement:{rapprocher,colonnes,cleFloue,mesure}});
})(typeof globalThis!=='undefined'?globalThis:this);
