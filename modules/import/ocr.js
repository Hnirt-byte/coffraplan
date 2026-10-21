// CoffraPlan — module d'import de plans : reconnaissance optique (OCR) locale d'une zone de page PDF.
// Moteur : Tesseract.js 7.0.0 + tesseract.js-core 7.0.0 (SIMD, LSTM seul) + modèle français fra « best_int » 4.0.0
// (Apache-2.0), copiés tels quels dans vendor/tesseract et recopiés dans le HTML par assembler.py (empreintes SHA-256).
// Hors connexion : le worker est construit depuis les blocs du HTML (URL blob, valable en file://) ; le wasm et le modèle y
// sont lus en base64 ; fetch et XMLHttpRequest du worker sont remplacés : toute autre requête échoue (aucun CDN, aucun service).
// La zone est rendue par PDF.js (CPI.pdf.rendreZone : rotation de page comprise), prétraitée (gris, contraste, traits longs
// de la grille relevés puis effacés), reconnue, puis convertie en textes et traits en points PDF (repère des textes de pdf.js)
// pour CPI.nomenclatures.analyser : aucun second moteur de nomenclature. Chaque texte garde sa valeur brute et sa confiance.
(function(root){'use strict';
const VERSION='Tesseract.js 7.0.0 · tesseract.js-core 7.0.0 (SIMD, LSTM) · fra 4.0.0 best_int';
const src=id=>{const s=root.document&&root.document.getElementById(id);if(!s)throw new Error('moteur OCR absent de ce fichier ('+id+')');return s.textContent};
let W=null,LOG=null;
// Script du worker : données embarquées, accès réseau coupé, cœur wasm (binaire fourni : aucun téléchargement), worker publié
function workerSrc(){return `"use strict";const CPI_WASM=${JSON.stringify(src('tess-wasm').replace(/\s+/g,''))},CPI_FRA=${JSON.stringify(src('tess-fra').replace(/\s+/g,''))};
const cpiB64=s=>{const t=atob(s),u=new Uint8Array(t.length);for(let i=0;i<t.length;i++)u[i]=t.charCodeAt(i);return u};
const cpiGunzip=async u=>new Uint8Array(await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
self.fetch=async u=>{if(/\\/fra\\.traineddata\\.gz$/.test(String(u)))return new Response(cpiB64(CPI_FRA));throw new Error('OCR hors connexion : requête refusée ('+u+')')};
self.XMLHttpRequest=function(){throw new Error('OCR hors connexion : requête refusée')};
${src('tess-core-src')}
;TesseractCore=(f=>async a=>f(Object.assign({},a,{wasmBinary:await cpiGunzip(cpiB64(CPI_WASM))})))(TesseractCore);
${src('tess-worker-src')}`}
// Démarrage (une fois ; relancé après arrêter()) : → worker Tesseract prêt (modèle fra chargé)
function charger(){if(W)return W;
  W=(async()=>{if(!root.Tesseract){const s=root.document.createElement('script');s.textContent=src('tess-src');root.document.head.appendChild(s);s.remove()}
    if(!root.Tesseract)throw new Error('Tesseract.js non chargé');
    const url=URL.createObjectURL(new Blob([workerSrc()],{type:'text/javascript'}));
    try{return await root.Tesseract.createWorker('fra',1,{workerPath:url,workerBlobURL:false,corePath:'cpi-ocr/',langPath:'cpi-ocr',cacheMethod:'none',gzip:true,
      logger:m=>{if(LOG)try{LOG(m)}catch(e){}},errorHandler:()=>{}})}
    finally{URL.revokeObjectURL(url)}})();
  W.catch(()=>{W=null});return W}
// Arrêt immédiat (annulation) : le worker est détruit, le prochain appel le relance
async function arreter(){const w=W;W=null;if(!w)return;try{(await w).terminate()}catch(e){}}

// Reconnaissance d'une image (canvas) : mots {texte, conf, x0, y0, x1, y1 (px), ligne} ; psm = mode de découpage Tesseract
// Image convertie ici (PNG, comme Tesseract le ferait) : un arrêt pendant la conversion lève 'annulé' au lieu d'appeler un worker
// détruit (Tesseract.js enverrait alors son message à un worker nul : erreur JS non interceptée)
async function reconnaitre(canvas,o){const p=charger(),w=await p,opt=o||{},vivant=()=>{if(W!==p)throw new Error('annulé')};LOG=opt.progres||null;
  try{const img=new Uint8Array(await (await new Promise((r,e)=>canvas.toBlob(x=>x?r(x):e(new Error('image de la zone illisible'))))).arrayBuffer());vivant();
    await w.setParameters({tessedit_pageseg_mode:String(opt.psm||11),preserve_interword_spaces:'1',user_defined_dpi:String(opt.dpi||300)});
    vivant();const r=await w.recognize(img,{},{blocks:true,text:false});const M=[];let nl=0;
    (r.data.blocks||[]).forEach(b=>(b.paragraphs||[]).forEach(p=>(p.lines||[]).forEach(l=>{nl++;(l.words||[]).forEach(m=>{if(!m.text||!m.text.trim())return;
      M.push({texte:m.text,conf:Math.round(m.confidence),x0:m.bbox.x0,y0:m.bbox.y0,x1:m.bbox.x1,y1:m.bbox.y1,ligne:nl,
        sym:(m.symbols||[]).map(s=>({t:s.text,c:Math.round(s.confidence),b:s.bbox}))})})})));
    if(opt.oslash)oslash(canvas,M);
    return M}
  finally{LOG=null}}
// Ø mal lu (« 0 », « O », « 9 », « @ »… : le modèle français le connaît mal) au début d'un mot, sur une image en noir et blanc :
// c'est un Ø si le caractère a un anneau fermé ET une barre diagonale continue en son milieu (un 0 ou un O ont le centre vide,
// un 9 ou un 2 n'ont pas d'anneau complet). Mot réécrit, note gardée (le brut de la cellule reste celui de Tesseract).
const OSL=/^[0OoQ@©®%92DGøØ]/;
function oslash(cv,M){let d=null,W=0;
  // « 90x70 » : une cote l × h n'est jamais précédée d'un Ø (le 9 d'un scan flou a l'air barré)
  M.forEach(m=>{const s=m.sym&&m.sym[0];if(!s||!s.b||!OSL.test(m.texte)||s.t==='Ø'||!(m.texte.length===1||/^.\d/.test(m.texte))||/^.\d*\s*[x×X*]\s*\d/.test(m.texte))return;
    if(!d){W=cv.width;d=cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,W,cv.height).data}
    const b=s.b,w=b.x1-b.x0,h=b.y1-b.y0,H=d.length/4/W;if(w<6||h<6)return;
    const ink=(x,y)=>{for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const X=Math.round(x+dx),Y=Math.round(y+dy);if(X>=0&&Y>=0&&X<W&&Y<H&&d[4*(Y*W+X)]<128)return true}return false};
    const cx=(b.x0+b.x1)/2,cy=(b.y0+b.y1)/2,n=36;let an=0;
    [0.3,0.35,0.4,0.45].forEach(r=>{let a=0;for(let i=0;i<n;i++){const t=2*Math.PI*i/n;if(ink(cx+r*w*Math.cos(t),cy+r*h*Math.sin(t)))a++}an=Math.max(an,a/n)});
    let dg=0;for(let i=0;i<=20;i++){const f=0.3+0.4*i/20;if(ink(b.x0+f*w,b.y1-f*h))dg++}
    m.osl={anneau:Math.round(an*100),barre:Math.round(dg/21*100)};
    if(an>=0.85&&dg/21>=0.85){m.note=`« ${m.texte[0]} » lu comme Ø (anneau barré)`;m.texte='Ø'+m.texte.slice(1)}})}


// ==== Image de la zone : rendu PDF.js, prétraitement, traits de la grille ====
const med=A=>{const B=A.filter(Number.isFinite).sort((a,b)=>a-b);return B.length?B[B.length>>1]:0};
const PX_MAX=14e6,COTE_MAX=6000;   // shortcut: zone plafonnée à 14 Mpx (mémoire du worker) ; une très grande zone est lue à plus basse résolution
// Échelle (pixels par point PDF) : 300 dpi par défaut, réduite pour rester sous les plafonds
const plafond=(z,k)=>Math.min(k,Math.sqrt(PX_MAX/((z.x1-z.x0)*(z.y1-z.y0))),COTE_MAX/Math.max(z.x1-z.x0,z.y1-z.y0));
// Prétraitement léger sur une copie (le PDF n'est pas touché) : niveaux de gris, contraste étiré (centiles 1 et 99),
// traits longs horizontaux et verticaux (grille du tableau) relevés puis effacés : Tesseract lit mieux les cellules sans cadre
function pretraiter(cv){const W=cv.width,H=cv.height,g=cv.getContext('2d',{willReadFrequently:true}),im=g.getImageData(0,0,W,H),d=im.data,n=W*H,G=new Uint8ClampedArray(n),h=new Uint32Array(256);
  for(let i=0;i<n;i++){const v=(d[4*i]*77+d[4*i+1]*150+d[4*i+2]*29)>>8;G[i]=v;h[v]++}
  let lo=0,hi=255,c=0;while(lo<255&&(c+=h[lo])<0.01*n)lo++;c=0;while(hi>0&&(c+=h[hi])<0.01*n)hi--;
  if(hi-lo<40){lo=0;hi=255}   // zone presque unie : pas d'étirement
  for(let i=0;i<n;i++)G[i]=(G[i]-lo)*255/(hi-lo);
  const Lh=Math.max(60,Math.round(0.04*W)),Lv=Math.max(60,Math.round(0.04*H)),RH=[],RV=[],noir=i=>G[i]<128;
  for(let y=0;y<H;y++){let x=0;while(x<W){if(!noir(y*W+x)){x++;continue}let e=x;while(e<W&&noir(y*W+e))e++;if(e-x>=Lh)RH.push({y,x0:x,x1:e});x=e}}
  for(let x=0;x<W;x++){let y=0;while(y<H){if(!noir(y*W+x)){y++;continue}let e=y;while(e<H&&noir(e*W+x))e++;if(e-y>=Lv)RV.push({x,y0:y,y1:e});y=e}}
  // regroupement des passages voisins en traits (épaisseur du trait)
  const grp=(R,p,a,b)=>{const T=[];R.forEach(r=>{const t=T.find(t=>r[p]-t.p1<=1&&r[a]<t[b]&&r[b]>t[a]);if(t){t.p1=r[p];t[a]=Math.min(t[a],r[a]);t[b]=Math.max(t[b],r[b])}else T.push({p0:r[p],p1:r[p],[a]:r[a],[b]:r[b]})});return T};
  const TH=grp(RH,'y','x0','x1'),TV=grp(RV,'x','y0','y1');
  RH.forEach(r=>{for(let x=r.x0;x<r.x1;x++)G[r.y*W+x]=255});RV.forEach(r=>{for(let y=r.y0;y<r.y1;y++)G[y*W+r.x]=255});
  for(let i=0;i<n;i++){d[4*i]=d[4*i+1]=d[4*i+2]=G[i];d[4*i+3]=255}
  const out=root.document.createElement('canvas');out.width=W;out.height=H;out.getContext('2d').putImageData(im,0,0);
  return{canvas:out,H:TH.map(t=>({y:(t.p0+t.p1)/2,x0:t.x0,x1:t.x1})),V:TV.map(t=>({x:(t.p0+t.p1)/2,y0:t.y0,y1:t.y1}))}}

// ==== Corrections automatiques prudentes (valeur brute toujours gardée) ====
// Confusions lettre / chiffre corrigées seulement dans une suite qui contient déjà un chiffre (« RO1 » → R01, « 6S0 » → 650) ;
// la 1re lettre d'un repère est gardée (« B18 », « S5 » restent) ; Ø lu « @ » ou « © » devant un nombre ; « rnm » → mm.
const AMB={O:'0',o:'0',I:'1',l:'1','|':'1',S:'5',B:'8'};
function corrJeton(t,C){if(!/\d/.test(t)||(t.match(/[A-Za-zÀ-ÿ]/g)||[]).filter(c=>!(c in AMB)).length>3)return t;   // mot ordinaire : rien
  let r=t.replace(/(^|[^A-Za-z0-9])[@©®](?=\d)/g,(m,a)=>{C.push(`« ${m.slice(a.length)} » lu comme Ø`);return a+'Ø'});
  // O → 0 partout dans la suite ; I, l, |, S, B seulement après son 1er caractère (« PS2 », « S5 », « B18 » restent) ;
  // 1re lettre d'un jeton gardée (lettre du repère)
  return r.replace(/[0-9OolI|SB]+/g,(s,p,all)=>{if(!/\d/.test(s)||/^\d+$/.test(s))return s;const debut=p===0||!/[A-Za-zÀ-ÿ0-9]/.test(all[p-1]);
    const v=[...s].map((c,i)=>/\d/.test(c)||i===0&&debut&&/[A-Za-z]/.test(c)?c:c==='O'||c==='o'?'0':i>0?AMB[c]:c).join('');
    if(v!==s)C.push(`« ${s} » lu comme ${v}`);return v})}
function corriger(texte){const C=[];let t=String(texte).replace(/[—–]/g,'-');   // tiret long ou demi-cadratin lu pour un tiret : typographie seule, non signalée
  t=t.replace(/\(\s*rn(m|)\s*\)|(?<![a-z])rnm(?![a-z])/g,m=>{const v=m.replace(/rn/,'m');C.push(`« ${m} » lu comme ${v}`);return v});
  t=t.split(/(\s+)/).map(x=>/\s/.test(x)?x:corrJeton(x,C)).join('');
  return{texte:t,corrections:C}}

// ==== Mots reconnus → textes et traits en points PDF (repère de pdf.js : Y vers le haut, page affichée) ====
const SEUIL=75;
const _S=0;   // confiance (%) sous laquelle un mot est signalé « incertain »
function versTextes(M,P,z,k,n,run){const T=[],X=x=>z.x0+x/k,Y=y=>z.y1-y/k;
  const L={};M.forEach(m=>{if(/^[|_\-—–~.,'`:;]+$/.test(m.texte)&&m.conf<50)return;(L[m.ligne]=L[m.ligne]||[]).push(m)});   // restes de traits
  Object.values(L).forEach(W=>{W.sort((a,b)=>a.x0-b.x0);const hl=med(W.map(m=>m.y1-m.y0))||1,G=[];
    W.forEach(m=>{const g=G[G.length-1],x=(g&&(g.x1+m.x0)/2);
      if(g&&m.x0-g.x1<=0.9*hl&&!P.V.some(v=>Math.abs(v.x-x)<=Math.max(2,(m.x0-g.x1)/2)&&v.y0<=Math.max(m.y1,g.y1)&&v.y1>=Math.min(m.y0,g.y0))){g.M.push(m);g.x1=Math.max(g.x1,m.x1);g.y0=Math.min(g.y0,m.y0);g.y1=Math.max(g.y1,m.y1)}
      else G.push({M:[m],x0:m.x0,x1:m.x1,y0:m.y0,y1:m.y1})});
    G.forEach(g=>{const brut=g.M.map(m=>m.texte).join(' '),c=corriger(brut),conf=Math.min(...g.M.map(m=>m.conf)),hh=med(g.M.map(m=>m.y1-m.y0));
      T.push({id:`${run}-t${T.length+1}`,calque:'',espace:'papier',presentation:'Page '+n,page:n,nature:'texte OCR',texte:c.texte,
        x:X((g.x0+g.x1)/2),y:Y((g.y0+g.y1)/2),h:0.72*hh/k,w:(g.x1-g.x0)/k,rot:0,
        ocr:{brut,conf,sym:g.M.map(m=>m.sym.map(s=>s.t+s.c).join(" ")).join(" · "),corrections:c.corrections,incertain:conf<SEUIL||c.corrections.length>0,box:{page:n,x0:X(g.x0),y0:Y(g.y1),x1:X(g.x1),y1:Y(g.y0)}}})})});
  const S=P.H.map(h=>({calque:'',espace:'papier',presentation:'Page '+n,page:n,a:[X(h.x0),Y(h.y)],b:[X(h.x1),Y(h.y)]}))
    .concat(P.V.map(v=>({calque:'',espace:'papier',presentation:'Page '+n,page:n,a:[X(v.x),Y(v.y0)],b:[X(v.x),Y(v.y1)]})));
  return{T,S}}

// Lecture d'une zone de page : rendu, prétraitement, reconnaissance, à deux résolutions (300 dpi, puis celle qui donne des mots
// d'environ 40 px de haut) ; la lecture de meilleure confiance moyenne est gardée. o = {progres(texte, fraction), annule() → vrai
// si abandon, run, psm, dpi} → {textes, traits, mesures:{passes:[{dpi, px, mots, hauteur, confiance}], retenue, ms}} ;
// lève 'annulé' si o.annule() devient vrai
const VISE=40;
async function lireZone(pdf,z,o){o=o||{};const t0=Date.now(),pr=o.progres||(()=>{}),stop=()=>{if(o.annule&&o.annule())throw new Error('annulé')};
  let k=plafond(z,(o.dpi||300)/72);const passes=[],R=[];
  for(let pass=1;pass<=2;pass++){const lb=`passe ${pass}/2, ${Math.round(k*72)} dpi`;pr(`Rendu de la zone (${lb})`,0);
    const cv=await root.CPI.pdf.rendreZone(pdf,z.page,z,k);stop();
    pr(`Prétraitement (${lb})`,0);const P=pretraiter(cv);stop();
    const M=await reconnaitre(P.canvas,{psm:o.psm||11,dpi:Math.round(k*72),progres:m=>{if(m&&m.status==='recognizing text')pr(`Reconnaissance (${lb})`,m.progress)}});stop();
    const hm=med(M.filter(m=>m.conf>=60&&m.texte.length>=2).map(m=>m.y1-m.y0)),n=M.reduce((s,m)=>s+m.texte.length,0),
      cf=n?M.reduce((s,m)=>s+m.conf*m.texte.length,0)/n:0;
    passes.push({dpi:Math.round(k*72),px:[P.canvas.width,P.canvas.height],mots:M.length,hauteur:Math.round(hm),confiance:Math.round(cf)});R.push({M,P,k,cf});
    const k2=hm?plafond(z,k*VISE/hm):k;
    if(pass===1&&!o.fixe&&hm&&Math.abs(k2-k)/k>0.15){k=k2;continue}
    break}
  const best=R.reduce((a,b)=>b.cf>a.cf+0.5?b:a);
  const nR=await relireCellules(best,pr,stop),{T,S}=versTextes(best.M,best.P,z,best.k,z.page,o.run||'o1');
  return{textes:T,traits:S,mesures:{passes,retenue:R.indexOf(best)+1,cellulesRelues:nR,ms:Date.now()-t0,moteur:VERSION}}}

// ==== Textes dessinés sur le plan (repères, annotations) : lecture ciblée de petits blocs (CPI.geometrie.blocsTexte) ====
// La page est rendue par tuiles (seules celles qui contiennent des blocs), chaque bloc est découpé, mis à ~32 px de hauteur de
// lettre et collé dans une mosaïque (fond blanc, larges marges) : une reconnaissance par mosaïque au lieu d'une par bloc ou d'une
// OCR de toute la page A0. Chaque mot est rendu à son bloc ; le texte garde valeur brute, confiance, corrections et emprise.
// o = {progres(texte, fraction), annule(), run} → {textes (format de lireZone, ocr.bloc = emprise du bloc lu), mesures}
// Mot réduit aux caractères dont le centre est dans le bloc lui-même (x0..x1, pixels) : la marge autour du bloc ne sert que de
// contexte (le trait du symbole voisin d'une étiquette encadrée, lu « | » ou « 1 », n'est pas une lettre du repère) ; null si vide
function noyau(w,x0,x1){const S=w.sym||[];if(!S.length||!S.every(s=>s.b))return w;const K=S.filter(s=>{const c=(s.b.x0+s.b.x1)/2;return c>=x0&&c<=x1});
  if(K.length===S.length)return w;if(!K.length)return null;
  return Object.assign({},w,{texte:K.map(s=>s.t).join(''),conf:Math.min(w.conf,...K.map(s=>s.c)),sym:K,x0:Math.min(...K.map(s=>s.b.x0)),x1:Math.max(...K.map(s=>s.b.x1))})}
const BL_PX=32,BL_W=2000,BL_H=2400,TUILE=3000,RELU_MAX=200;   // shortcut: au plus 200 relectures de repères douteux par page
async function lireBlocs(pdf,n,blocs,o){o=o||{};const t0=Date.now(),pr=o.progres||(()=>{}),stop=()=>{if(o.annule&&o.annule())throw new Error('annulé')};
  if(!blocs.length)return{textes:[],mesures:{blocs:0,mosaiques:0,ms:0,moteur:VERSION}};
  const hm=med(blocs.map(b=>b.h)),k=Math.min(6,Math.max(1.5,1.4*BL_PX/hm)),ts=TUILE/k,mg=b=>0.5*b.h,ov=Math.min(ts/2,Math.max(...blocs.map(b=>b.x1-b.x0+2*mg(b)),...blocs.map(b=>b.y1-b.y0+2*mg(b))));
  // tuiles qui se recouvrent de ov : chaque bloc (marges comprises) tient entier dans au moins une
  const X0=Math.min(...blocs.map(b=>b.x0-mg(b))),Y0=Math.min(...blocs.map(b=>b.y0-mg(b))),pas=ts-ov,T=new Map();
  blocs.forEach((b,i)=>{const cx=Math.max(0,Math.floor((b.x0-mg(b)-X0)/pas)),cy=Math.max(0,Math.floor((b.y0-mg(b)-Y0)/pas)),key=cx+','+cy;(T.get(key)||T.set(key,[]).get(key)).push(i)});
  const C=[];let nt=0;   // découpes : {i, cv (canvas), w, h}
  for(const [key,I] of T){stop();const [cx,cy]=key.split(',').map(Number),z={x0:X0+cx*pas,y0:Y0+cy*pas,x1:X0+cx*pas+ts,y1:Y0+cy*pas+ts};
    pr(`Rendu de la page ${n} (tuile ${++nt}/${T.size})`,nt/T.size);const cv=await root.CPI.pdf.rendreZone(pdf,n,z,k);
    I.forEach(i=>{const b=blocs[i],m=mg(b),s=BL_PX/b.h,w=Math.ceil((b.x1-b.x0+2*m)*s),h=Math.ceil((b.y1-b.y0+2*m)*s),c=root.document.createElement('canvas');c.width=w;c.height=h;
      c.getContext('2d').drawImage(cv,(b.x0-m-z.x0)*k,(z.y1-b.y1-m)*k,(b.x1-b.x0+2*m)*k,(b.y1-b.y0+2*m)*k,0,0,w,h);C.push({i,cv:c,w,h})})}
  // mosaïques : rangées de découpes séparées d'une hauteur de ligne ; gris puis seuil (lettres de couleur → noir)
  // écart horizontal de 3 hauteurs de lettre : en dessous, Tesseract soude parfois les mots de deux découpes voisines
  const M=[];let cur=null,x=0,y=0,rh=0;const gx=3*BL_PX,gy=Math.round(1.5*BL_PX);
  C.forEach(c=>{if(!cur||x+c.w+gx>BL_W&&x>gx){y+=rh+gy;x=gx;rh=0}if(!cur||y+c.h+gy>BL_H){cur={P:[],h:0};M.push(cur);x=gx;y=gy;rh=0}
    cur.P.push(Object.assign(c,{x,y}));x+=c.w+gx;rh=Math.max(rh,c.h);cur.h=Math.max(cur.h,y+c.h+gy)});
  const R=new Map();let nm=0;
  for(const m of M){stop();const cv=root.document.createElement('canvas');cv.width=BL_W;cv.height=m.h;const g=cv.getContext('2d',{willReadFrequently:true});
    g.fillStyle='#fff';g.fillRect(0,0,BL_W,m.h);m.P.forEach(c=>g.drawImage(c.cv,c.x,c.y));
    const im=g.getImageData(0,0,BL_W,m.h),d=im.data;for(let j=0;j<d.length;j+=4){const v=(d[j]*77+d[j+1]*150+d[j+2]*29)>>8<170?0:255;d[j]=d[j+1]=d[j+2]=v}g.putImageData(im,0,0);
    const W=await reconnaitre(cv,{psm:11,dpi:300,progres:q=>{if(q&&q.status==='recognizing text')pr(`Lecture des repères dessinés, page ${n} (${nm+1}/${M.length})`,q.progress)}});nm++;
    W.forEach(w=>{const xc=(w.x0+w.x1)/2,yc=(w.y0+w.y1)/2,c=m.P.find(c=>xc>=c.x&&xc<=c.x+c.w&&yc>=c.y&&yc<=c.y+c.h);if(!c)return;
      const v=noyau(w,c.x+0.4*BL_PX,c.x+c.w-0.4*BL_PX);if(v)(R.get(c.i)||R.set(c.i,[]).get(c.i)).push(v)})}
  // 2e lecture, seule et en une ligne (psm 7), des courtes lectures douteuses qui ressemblent à un repère (« D4 » à 37 %,
  // « |D16 », « D 7 ») : gardée si sa confiance est meilleure ; la 1re lecture reste dans brut1
  const RL=/^[^A-Za-z0-9]{0,3}[A-Za-z]{1,4}\s?[0-9OoSIlBZGAÀ]{1,4}[A-Za-z]?[^A-Za-z0-9]{0,3}$/,cv1=new Map(C.map(c=>[c.i,c])),relu=new Map();let nr=0;
  // o.prefixes (lettres des repères du tableau, « R ») : ces blocs sont relus en premier (RELU_MAX)
  const PX=o.prefixes&&o.prefixes.length?new RegExp('^[^A-Za-z0-9]{0,3}('+o.prefixes.join('|')+')','i'):null,ord=[...R].sort((a,b)=>PX?(a[1].some(w=>PX.test(w.texte))?0:1)-(b[1].some(w=>PX.test(w.texte))?0:1):0);
  for(const [i,W0] of ord){const W=W0.slice().sort((a,b)=>a.x0-b.x0),t=W.map(w=>w.texte).join(' '),cf=Math.min(...W.map(w=>w.conf));
    // repère seul ou l'un des mots (« o RÀ ») ; lettres ramenées à 24 px et traits épaissis d'un pixel : polices de DAO à un trait, mieux lues (mesuré sur un plan réel)
    if(cf>=SEUIL||!RL.test(t)&&!W.some(w=>RL.test(w.texte))||nr>=RELU_MAX)continue;stop();nr++;const c=cv1.get(i),p=24,e=0.75;
    pr(`Relecture des repères douteux, page ${n} (${nr})`,null);let best=null;
    for(const ep of [0,1]){const cv=root.document.createElement('canvas');cv.width=Math.ceil(c.w*e)+2*p;cv.height=Math.ceil(c.h*e)+2*p;   // sans puis avec épaississement
      const g=cv.getContext('2d',{willReadFrequently:true});g.fillStyle='#fff';g.fillRect(0,0,cv.width,cv.height);g.drawImage(c.cv,p,p,c.w*e,c.h*e);
      const im=g.getImageData(0,0,cv.width,cv.height),d=im.data,W_=cv.width,K=new Uint8Array(W_*cv.height);for(let j=0;j<K.length;j++)K[j]=(d[4*j]*77+d[4*j+1]*150+d[4*j+2]*29)>>8<170?1:0;
      for(let j=0;j<K.length;j++){const x=j%W_,v=K[j]||ep&&(x>0&&K[j-1]||j>=W_&&(K[j-W_]||x>0&&K[j-W_-1]))?0:255;d[4*j]=d[4*j+1]=d[4*j+2]=v}g.putImageData(im,0,0);
      const W2=(await reconnaitre(cv,{psm:7,dpi:300})).map(w=>noyau(w,p+0.4*BL_PX*e,p+(c.w-0.4*BL_PX)*e)).filter(w=>w&&w.texte.trim()),q=W2.length?Math.min(...W2.map(w=>w.conf)):-1;
      if(q>cf+5&&(!best||q>best.q))best={W:W2,q}}
    if(best)relu.set(i,{W:best.W,brut1:t,conf1:cf})}
  const out=[],run=o.run||'b';
  R.forEach((W,i)=>{const rl=relu.get(i);if(rl)W=rl.W.map(w=>Object.assign({},w,{x0:w.x0,x1:w.x1}));
    W=W.filter(w=>!(/^[|_\-—–~.,'`:;]+$/.test(w.texte)&&w.conf<50));if(!W.length)return;W.sort((a,b)=>a.x0-b.x0);
    const b=blocs[i],brut=W.map(w=>w.texte).join(' '),c=corriger(brut),conf=Math.min(...W.map(w=>w.conf));
    out.push({id:`${run}-p${n}-b${i}`,calque:'',espace:'papier',presentation:'Page '+n,page:n,nature:'texte OCR',texte:c.texte,x:(b.x0+b.x1)/2,y:(b.y0+b.y1)/2,h:b.h,w:b.x1-b.x0,rot:0,
      ocr:{brut,conf,corrections:c.corrections,incertain:conf<SEUIL||c.corrections.length>0,box:{page:n,x0:b.x0,y0:b.y0,x1:b.x1,y1:b.y1},bloc:true,mots:W.map(w=>({t:w.texte,c:w.conf})),...(rl?{relu:{brut1:rl.brut1,conf1:rl.conf1}}:{})}})});
  return{textes:out,mesures:{blocs:blocs.length,lus:out.length,relus:nr,ameliores:relu.size,tuiles:T.size,mosaiques:M.length,px_par_pt:Math.round(k*100)/100,ms:Date.now()-t0,moteur:VERSION}}}

// Cellules de la grille encrées mais sans mot reconnu (un « 0 » ou un « / » isolé que le découpage de la page a ignoré) :
// relues une à une comme une ligne de texte (psm 7). → nombre de cellules relues
const CEL_MAX=400;   // shortcut: au-delà de 400 cellules encrées vides, les suivantes ne sont pas relues (tableau géant) ; à relever si besoin
async function relireCellules(b,pr,stop){const {P,M}=b,c=P.canvas,W=c.width,f=(A,p)=>{const R=[];A.map(a=>a[p]).sort((x,y)=>x-y).forEach(v=>{if(!R.length||v-R[R.length-1]>4)R.push(v)});return R};
  const ys=f(P.H,'y'),xs=f(P.V,'x');if(ys.length<2||xs.length<2)return 0;
  const g=c.getContext('2d',{willReadFrequently:true}),C=[];
  for(let i=0;i+1<ys.length;i++)for(let j=0;j+1<xs.length;j++){const x0=xs[j]+4,x1=xs[j+1]-4,y0=ys[i]+4,y1=ys[i+1]-4;if(x1-x0<8||y1-y0<8)continue;
    // une vraie cellule : bordée en haut et en bas par un trait qui la traverse
    const borde=y=>P.H.some(h=>Math.abs(h.y-y)<=4&&h.x0<=x0&&h.x1>=x1);if(!borde(ys[i])||!borde(ys[i+1]))continue;
    if(M.some(m=>m.x1>x0&&m.x0<x1&&m.y1>y0&&m.y0<y1))continue;
    const d=g.getImageData(x0,y0,x1-x0,y1-y0).data;let n=0;for(let k=0;k<d.length;k+=4)if(d[k]<128)n++;
    if(n>=12)C.push({x0,y0,x1,y1})}
  let nR=0;const L=C.slice(0,CEL_MAX);
  for(let i=0;i<L.length;i++){const q=L[i],w=q.x1-q.x0,h=q.y1-q.y0,m=Math.round(h/2),cv=root.document.createElement('canvas');cv.width=w+2*m;cv.height=h+2*m;
    const x=cv.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,cv.width,cv.height);x.drawImage(c,q.x0,q.y0,w,h,m,m,w,h);
    pr('Relecture des cellules sans texte reconnu',i/L.length);
    const R=await reconnaitre(cv,{psm:7});stop();
    R.forEach(r=>{if(!r.texte.trim())return;M.push(Object.assign(r,{x0:r.x0-m+q.x0,x1:r.x1-m+q.x0,y0:r.y0-m+q.y0,y1:r.y1-m+q.y0,ligne:'c'+i,relu:true}))});if(R.length)nR++}
  return nR}

// ==== Tableau à grille (phase 5) : la grille d'abord, puis chaque cellule lue à part ====
// 1. Grille : traits vectoriels du PDF dans la zone (o.segments : CPI.pdf.chemins), sinon traits longs relevés sur l'image
//    (tableau numérisé) → CPI.nomenclatures.grilleTraits. 2. Orientation du tableau dans sa page (o.rot = 0..3 quarts de tour,
//    sinon cherchée : cellules plus hautes que larges → 90° et 270° essayés sur quelques cellules, la meilleure confiance gagne ;
//    180° seulement sur choix de l'utilisateur). 3. Rendu de la zone (PDF.js) à ~36 px par hauteur de lettre ; chaque cellule
//    découpée en retrait des traits, redressée, mise en noir et blanc en deux variantes : niveaux de gris, et couleur (seule la
//    couleur d'encre dominante du tableau est gardée : grille, nuages de révision et annotations d'une autre couleur s'effacent ;
//    le noir reste) ; traits longs restants effacés. 4. Lecture des cellules en mosaïque (une reconnaissance pour tout le tableau),
//    relecture une à une des cellules vides, douteuses ou lues différemment par les deux variantes. Les rangées viennent de la
//    géométrie, jamais de l'ordre des mots de Tesseract. Une cellule illisible reste vide (rien n'est inventé) ; brut et confiance
//    gardés. → null (pas de grille) | {G (pour CPI.nomenclatures.depuisGrille), textes (un par cellule lue), mesures}
const G_PX=[24,36],G_RELU=300;   // px de hauteur de lettre essayés : 24 (polices de DAO à un trait), 36 (polices pleines) ; shortcut: au plus 300 cellules relues une à une (tableau géant : les suivantes gardent la 1re lecture)
const rotZ=(z,q)=>{const P=[[z.x0,z.y0],[z.x1,z.y1],[z.x0,z.y1],[z.x1,z.y0]].map(p=>root.CPI.nomenclatures.tourne(p,-q));
  return{x0:Math.min(...P.map(p=>p[0])),y0:Math.min(...P.map(p=>p[1])),x1:Math.max(...P.map(p=>p[0])),y1:Math.max(...P.map(p=>p[1]))}};
const boiteRetour=(b,q)=>{const P=[[b[0],b[1]],[b[2],b[3]],[b[0],b[3]],[b[2],b[1]]].map(p=>root.CPI.nomenclatures.tourne(p,q));
  return[Math.min(...P.map(p=>p[0])),Math.min(...P.map(p=>p[1])),Math.max(...P.map(p=>p[0])),Math.max(...P.map(p=>p[1]))]};
// Pixel : encre ? teinte (0..11) ou -1 (gris, noir)
function pix(r,g,b){const mx=Math.max(r,g,b),mn=Math.min(r,g,b),l=(r*77+g*150+b*29)>>8,sat=mx?(mx-mn)/mx:0;
  if(sat>0.35&&mx>60){if(l>235)return null;let h=mx===r?(g-b)/(mx-mn):mx===g?2+(b-r)/(mx-mn):4+(r-g)/(mx-mn);h=((h*2)%12+12)%12;return{t:Math.round(h)%12,l}}
  return l<170?{t:-1,l}:null}
// Découpe redressée d'une boîte (px de la zone rendue) : rotation q quarts de tour dans le sens horaire de l'écran
function decoupe(cv,x,y,w,h,q){const c=root.document.createElement('canvas'),g=c.getContext('2d',{willReadFrequently:true}),dr=q%2;c.width=dr?h:w;c.height=dr?w:h;
  g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.translate(c.width/2,c.height/2);g.rotate(q*Math.PI/2);g.drawImage(cv,x,y,w,h,-w/2,-h/2,w,h);return c}
// Noir et blanc d'une découpe : garde(t) dit si une encre de teinte t est gardée ; traits longs (≥ 70 % du côté) effacés → {c, n (pixels noirs)}
function nb(src,garde){const W=src.width,H=src.height,g=src.getContext('2d',{willReadFrequently:true}),im=g.getImageData(0,0,W,H),d=im.data,B=new Uint8Array(W*H);
  for(let i=0;i<W*H;i++){const p=pix(d[4*i],d[4*i+1],d[4*i+2]);B[i]=p&&garde(p.t)?1:0}
  // restes des traits de la grille : passages presque aussi longs que la découpe, au bord seulement (un « 1 » ou le jambage d'un
  // « D » au milieu ou à gauche de la cellule restent)
  for(let y=0;y<H;y++){if(y>0.12*H&&y<0.88*H)continue;let x=0;while(x<W){if(!B[y*W+x]){x++;continue}let e=x;while(e<W&&B[y*W+e])e++;if(e-x>=0.9*W)for(let k=x;k<e;k++)B[y*W+k]=2;x=e}}
  for(let x=0;x<W;x++){if(x>0.06*W&&x<0.94*W)continue;let y=0;while(y<H){if(!B[y*W+x]){y++;continue}let e=y;while(e<H&&B[e*W+x])e++;if(e-y>=0.9*H)for(let k=y;k<e;k++)B[k*W+x]=2;y=e}}
  // traits fins (polices de DAO à un trait) : épaissis d'un pixel, Tesseract les lit nettement mieux (« 300 » lu « 500 » sinon)
  let ni=0,tr=0;for(let i=0;i<W*H;i++)if(B[i]===1){ni++;if(i%W===0||B[i-1]!==1)tr++}
  if(tr&&ni/tr<3.5){const A=B.slice();for(let y=0;y<H;y++)for(let x=0;x<W;x++){if(A[y*W+x]===1)continue;
    for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const X=x+dx,Y=y+dy;if(X>=0&&Y>=0&&X<W&&Y<H&&A[Y*W+X]===1){B[y*W+x]=1;dy=dx=2}}}}
  const c=root.document.createElement('canvas');c.width=W;c.height=H;const o=c.getContext('2d'),om=o.createImageData(W,H);let n=0,x0=W,y0=H,x1=-1,y1=-1;
  for(let i=0;i<W*H;i++){const v=B[i]===1?0:255;if(!v){n++;const x=i%W,y=(i-x)/W;if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y}om.data[4*i]=om.data[4*i+1]=om.data[4*i+2]=v;om.data[4*i+3]=255}o.putImageData(om,0,0);
  // tiret seul (valeur absente) : une barre horizontale pleine, Tesseract le lit mal ou pas du tout
  const bw=x1-x0+1,bh=y1-y0+1,tiret=n>=6&&bw>=3*bh&&bh<=0.25*H&&n>=0.6*bw*bh;
  return{c,n,tiret}}
// Lecture d'une liste de découpes en mosaïque : → par découpe, mots [{texte, conf, x0, y0, x1, y1, ligne}] (px de la découpe)
async function mosaique(C,o){const g=40,W=Math.max(2400,...C.map(c=>c.width+2*g)),R=C.map(()=>[]),M=[];let cur=null,x=g,y=g,rh=0;
  C.forEach((c,i)=>{if(cur&&x+c.width+g>W){y+=rh+g;x=g;rh=0}if(!cur||y+c.height+g>3000){cur={P:[],h:0};M.push(cur);x=g;y=g;rh=0}
    cur.P.push({i,c,x,y});x+=c.width+g;rh=Math.max(rh,c.height);cur.h=Math.max(cur.h,y+c.height+g)});
  for(const m of M){const cv=root.document.createElement('canvas');cv.width=W;cv.height=m.h;const x2=cv.getContext('2d');x2.fillStyle='#fff';x2.fillRect(0,0,W,m.h);m.P.forEach(p=>x2.drawImage(p.c,p.x,p.y));
    const Wd=await reconnaitre(cv,{psm:11,dpi:300,progres:o.progres,oslash:true});o.stop();
    Wd.forEach(w=>{const xc=(w.x0+w.x1)/2,yc=(w.y0+w.y1)/2,p=m.P.find(p=>xc>=p.x&&xc<=p.x+p.c.width&&yc>=p.y&&yc<=p.y+p.c.height);
      if(p)R[p.i].push(Object.assign({},w,{x0:w.x0-p.x,x1:w.x1-p.x,y0:w.y0-p.y,y1:w.y1-p.y}))})}
  return R}
// Mots d'une cellule → texte (lignes de haut en bas, mots de gauche à droite), confiance (la plus basse), restes de traits retirés
function texteMots(W){W=W.filter(m=>m.texte&&m.texte.trim()&&!(/^[|_\-—–~.,'`:;]+$/.test(m.texte)&&m.conf<50));if(!W.length)return null;
  const L=[];W.slice().sort((a,b)=>(a.y0+a.y1)-(b.y0+b.y1)).forEach(m=>{const yc=(m.y0+m.y1)/2,l=L.find(l=>Math.abs(l.y-yc)<=0.5*Math.max(l.h,m.y1-m.y0));if(l)l.M.push(m);else L.push({y:yc,h:m.y1-m.y0,M:[m]})});
  L.sort((a,b)=>a.y-b.y);return{texte:L.map(l=>l.M.sort((a,b)=>a.x0-b.x0).map(m=>m.texte).join(' ')).join('\n'),conf:Math.min(...W.map(m=>m.conf)),moy:W.reduce((s,m)=>s+m.conf,0)/W.length,
    notes:W.map(m=>m.note).filter(Boolean)}}
const chiffres=t=>String(t||'').replace(/\s+/g,'').replace(/[—–]/g,'-');
async function lireGrille(pdf,z,o){o=o||{};const t0=Date.now(),pr=o.progres||(()=>{}),stop=()=>{if(o.annule&&o.annule())throw new Error('annulé')},N=root.CPI.nomenclatures,run=o.run||'g';
  const dans=p=>p[0]>=z.x0-1&&p[0]<=z.x1+1&&p[1]>=z.y0-1&&p[1]<=z.y1+1;
  let S=(o.segments||[]).filter(s=>dans(s.a)||dans(s.b)),source='traits du PDF';
  const grilles=S=>[0,1,2,3].map(q=>{const g=N.grilleTraits(q?S.map(s=>({a:N.tourne(s.a,-q),b:N.tourne(s.b,-q)})):S,q?rotZ(z,q):z);return g&&Object.assign(g,{q})});
  let GQ=grilles(S);
  if(!GQ[0]){pr('Recherche de la grille sur l\'image',null);const k0=plafond(z,200/72),cv=await root.CPI.pdf.rendreZone(pdf,z.page,z,k0);stop();const P=pretraiter(cv),X=x=>z.x0+x/k0,Y=y=>z.y1-y/k0;
    S=P.H.map(h=>({a:[X(h.x0),Y(h.y)],b:[X(h.x1),Y(h.y)]})).concat(P.V.map(v=>({a:[X(v.x),Y(v.y0)],b:[X(v.x),Y(v.y1)]})));source='traits de l\'image';GQ=grilles(S)}
  if(!GQ[0])return null;
  // orientation : o.rot impose ; sinon 0° essayé sur quelques cellules, puis 90° et 270° si la lecture n'est pas nette (cellules
  // plus hautes que larges : 90° et 270° d'abord)
  const asp=med(GQ[0].rangs.flatMap(r=>r.cellules.map(c=>(r.y0-r.y1)/Math.max(0.1,c.x1-c.x0))));
  const Q=o.rot!=null?[o.rot%4]:asp>1.3?[1,3,0]:[0,1,3];
  const hq=g=>med(g.rangs.map(r=>r.y0-r.y1)),Qv=Q.filter(q=>GQ[q]);if(!Qv.length)return null;
  // rendu de la zone pour une hauteur de lettre de P px (hauteur de lettre ≈ 0,55 rangée ; rangées du sens de lecture : les plus basses)
  const hmin=0.55*Math.min(...Qv.map(q=>hq(GQ[q]))),RD={};
  const rendu=async P=>{if(!RD[P]){const k=plafond(z,Math.min(10,Math.max(3,P/hmin)));pr(`Rendu de la zone (${Math.round(k*72)} dpi)`,null);RD[P]={P,k,cv:await root.CPI.pdf.rendreZone(pdf,z.page,z,k)};stop()}return RD[P]};
  const px=(r,b)=>{const k=r.k,x0=(b[0]-z.x0)*k,x1=(b[2]-z.x0)*k,y0=(z.y1-b[3])*k,y1=(z.y1-b[1])*k;return[x0,y0,x1-x0,y1-y0]};
  // cellules d'une grille (repère q) : boîte page, découpe redressée en retrait des traits
  const cellules=(g,r)=>{const ins=2,out=[];g.rangs.forEach((rg,i)=>rg.cellules.forEach(c=>{const b=boiteRetour([c.x0,rg.y1,c.x1,rg.y0],g.q),[x,y,w,h]=px(r,b);
      if(w-2*ins<4||h-2*ins<4)return;out.push({i,j:c.j0,b,crop:decoupe(r.cv,x+ins,y+ins,w-2*ins,h-2*ins,g.q)})}));return out};
  // couleur d'encre dominante (teintes voisines gardées), d'après toutes les cellules d'une grille
  const dominante=Cl=>{const hs=new Float64Array(13);Cl.forEach(c=>{const W=c.crop.width,H=c.crop.height,d=c.crop.getContext('2d',{willReadFrequently:true}).getImageData(0,0,W,H).data;
      for(let i=0;i<W*H;i+=2){const p=pix(d[4*i],d[4*i+1],d[4*i+2]);if(p)hs[p.t+1]++}});
    let m=0;for(let i=1;i<13;i++)if(hs[i]>hs[m])m=i;const tot=hs.reduce((a,b)=>a+b,0),dom=hs[m]+(m?hs[(m-1+11)%12+1]+hs[m%12+1]:0);
    return{t:m-1,autres:tot-dom>=0.03*tot&&tot>0}};
  const variantes=(c,D)=>{const A=nb(c.crop,()=>true),V=[{nom:'gris',...A}];
    if(D.autres){const t=D.t,B=nb(c.crop,u=>u===-1||t>=0&&Math.min((u-t+12)%12,(t-u+12)%12)<=1);V.push({nom:'couleur',...B})}return V};
  // orientation et résolution : essais sur 10 cellules, chaque sens à 24 puis 36 px de lettre ; score : caractères lus dans des
  // mots d'au moins 2 lettres ou chiffres, pondérés par la confiance (un texte lu de travers donne des signes isolés, parfois à forte confiance)
  const E=[];for(const P of G_PX)for(const q of Qv){const g=GQ[q],r=await rendu(P),Cl=cellules(g,r),D=dominante(Cl),V=Cl.map(c=>variantes(c,D)[D.autres?1:0]).filter(v=>v.n>=12).slice(0,10);
    pr(`Orientation du tableau : essai à ${q*90}°`,null);const R=await mosaique(V.map(v=>v.c),{stop,progres:null});
    const sc=R.reduce((s,W)=>s+W.reduce((a,m)=>{const n=(m.texte.match(/[\p{L}\p{N}]/gu)||[]).length;return a+(n>=2?n*m.conf/100:0)},0),0)/Math.max(1,V.length);
    E.push({q,P,g,c:sc})}
  E.sort((a,b)=>b.c-a.c);const mesQ=Qv.length>1?Qv.map(q=>({rotation:q*90,score:Math.round(Math.max(...E.filter(e=>e.q===q).map(e=>e.c))*10)/10})):null;
  const g=E[0].g,RZ=await rendu(E[0].P),k=RZ.k,cv=RZ.cv,hr=hq(g),Cl=cellules(g,RZ),D=dominante(Cl),V=Cl.map(c=>variantes(c,D)),enc=V.map(v=>v.some(x=>x.n>=Math.max(12,0.002*x.c.width*x.c.height)));
  const L=V.map(()=>[]),tir=new Set();
  V.forEach((v,i)=>{const t=v[v.length-1];if(enc[i]&&t.tiret){tir.add(i);L[i]=v.map((x,j)=>j===v.length-1?{texte:'-',conf:90,moy:90,notes:[],tiret:true}:null)}});
  const I=Cl.map((c,i)=>i).filter(i=>enc[i]&&!tir.has(i)),nv=V[0]?V[0].length:1;
  if(o.trace)I.forEach(i=>o.trace.push({i:Cl[i].i,j:Cl[i].j,v:V[i].map(x=>x.c.toDataURL())}));   // diagnostic : images lues
  for(let v=0;v<nv;v++){stop();const R=await mosaique(I.map(i=>V[i][v].c),{stop,progres:m=>{if(m&&m.status==='recognizing text')pr(`Lecture des cellules (${v?'variante couleur':'niveaux de gris'})`,m.progress)}});
    I.forEach((i,n)=>{L[i][v]=texteMots(R[n])})}
  // relecture une à une : cellule encrée sans texte, douteuse, ou lue différemment par les deux variantes
  let nr=0;const div=new Set();
  // divergence : seulement si les deux lectures sont plausibles (une variante brouillée par un nuage n'en est pas une)
  for(const i of I){const A=L[i].filter(Boolean),dif=A.length===2&&chiffres(A[0].texte)!==chiffres(A[1].texte)&&Math.min(A[0].moy,A[1].moy)>=60;if(dif)div.add(i);
    if(nr>=G_RELU||A.length&&!dif&&Math.min(...A.map(a=>a.conf))>=SEUIL)continue;stop();nr++;pr('Relecture des cellules douteuses',nr/Math.max(1,I.length));
    for(let v=0;v<nv;v++){if(V[i][v].n<12)continue;const c=V[i][v].c,p=Math.round(Math.min(c.width,c.height)/3)+8,cc=root.document.createElement('canvas');cc.width=c.width+2*p;cc.height=c.height+2*p;
      const x2=cc.getContext('2d');x2.fillStyle='#fff';x2.fillRect(0,0,cc.width,cc.height);x2.drawImage(c,p,p);
      const r=texteMots(await reconnaitre(cc,{psm:c.height>1.6*RZ.P*1.5?6:7,dpi:300,oslash:true}));if(r&&(!L[i][v]||r.moy>L[i][v].moy))L[i][v]=r}}
  // titre : bande au-dessus du tableau (dans son sens de lecture), jusqu'à 4 hauteurs de rangée
  let titre='';const zq=rotZ(z,g.q),top=g.cadre[3],hT=Math.min(4*hr,zq.y1-top);
  if(hT>=0.6*hr){const b=boiteRetour([g.cadre[0],top+0.2*g.t,g.cadre[2],top+hT],g.q),[x,y,w,h]=px(RZ,b);if(w>8&&h>8){stop();const B=nb(decoupe(cv,x,y,w,h,g.q),()=>true);   // gris : le titre n'a pas toujours la couleur des cellules
    if(o.trace)o.trace.push({titre:true,v:[B.c.toDataURL()]});
    if(B.n>=12){const r=texteMots(await reconnaitre(B.c,{psm:6,dpi:300}));if(o.trace)o.trace.push({titreLu:r});if(r&&r.moy>=50)titre=corriger(r.texte).texte}}}
  // textes au contrat de lireZone (un par cellule lue) et matrice de la grille
  const nc=g.xs.length-1,lignes=g.rangs.map(()=>Array(nc).fill('')),ids=g.rangs.map(()=>Array.from({length:nc},()=>[])),T=[];
  Cl.forEach((c,i)=>{const A=L[i].map((r,v)=>r&&Object.assign({v},r)).filter(Boolean);if(!A.length)return;const best=A.reduce((a,b)=>b.moy>a.moy+0.5?b:a),cr=corriger(best.texte),C=(best.notes||[]).concat(cr.corrections);
    if(g.rangs[c.i].cellules.length===1&&nc>=3&&best.moy<50)return;   // rangée d'une seule cellule (bande de titre) mal lue : bruit
    if(div.has(i)&&A.length===2)C.push(`lectures différentes selon le traitement de l'image : « ${A[0].texte.replace(/\n/g,' ')} » (gris) / « ${A[1].texte.replace(/\n/g,' ')} » (couleur)`);
    const b=c.b,id=`${run}-c${c.i+1}-${c.j+1}`;
    T.push({id,calque:'',espace:'papier',presentation:'Page '+z.page,page:z.page,nature:'texte OCR',texte:cr.texte,x:(b[0]+b[2])/2,y:(b[1]+b[3])/2,h:0.55*hr,w:b[2]-b[0],rot:g.q*90,
      ocr:{brut:best.texte,conf:Math.round(best.conf),corrections:C,incertain:best.conf<SEUIL||C.length>0,box:{page:z.page,x0:b[0],y0:b[1],x1:b[2],y1:b[3]},cellule:[c.i,c.j],variante:A.length>1?(best.v?'couleur':'gris'):null}});
    lignes[c.i][c.j]=(lignes[c.i][c.j]?lignes[c.i][c.j]+'\n':'')+cr.texte;ids[c.i][c.j].push(id)});
  const cad=boiteRetour(g.cadre,g.q);
  return{G:{lignes,ids,titre,cadre:cad,page:z.page,rotation:g.q*90,zone:z},textes:T,
    mesures:{methode:'grille',source,rotation:g.q*90,orientations:mesQ,dpi:Math.round(k*72),rangees:g.rangs.length,colonnes:nc,cellules:Cl.length,encrees:I.length,
      lues:T.length,relues:nr,divergentes:div.size,couleur:D.autres?'encre dominante isolée':'monochrome',ms:Date.now()-t0,moteur:VERSION}}}

// ==== Tableau reconnu (CPI.nomenclatures.analyser sur les textes OCR) → grille de vérification → nomenclature ====
// Colonnes de la grille : celles demandées (repère, désignation, type, dimensions, niveau, observations) toujours affichées, les
// autres seulement si le tableau en a ; une colonne non reconnue va dans « Autres colonnes » (titre : valeur) : rien n'est perdu
const COLONNES=[['repere','Repère'],['description','Désignation'],['type','Type ou nature'],['ouverture',"Dimensions d'ouverture"],['reseau','Réseau (DN)'],
  ['niveau','Niveau ou altitude'],['angle','Angle'],['observations','Observations'],['lot','Lot / entreprise'],['quantite','Quantité'],['autre','Autres colonnes']];
const BASE=['repere','description','type','ouverture','niveau','observations'];
const VERS={repere:'repere',description:'description',type:'type',ouverture:'ouverture',diametre:'ouverture',largeur:'ouverture',hauteur:'ouverture',reseau:'reseau',
  niveau:'niveau',angle:'angle',observations:'observations',lot:'lot',quantite:'quantite'};
const unionBox=B=>B.length?{page:B[0].page,x0:Math.min(...B.map(b=>b.x0)),y0:Math.min(...B.map(b=>b.y0)),x1:Math.max(...B.map(b=>b.x1)),y1:Math.max(...B.map(b=>b.y1))}:null;
// Ø peut-être mal lu devant un nombre seul (« 2250 », « 0250 », « D120 ») dans la colonne des dimensions, mot incertain : signalé seulement
const OMAL=/^[2@©®0OoDGQ%9]\s?(\d{2,4})$/;
function grille(N,textes){const tid=new Map(textes.map(t=>[t.id,t]));
  const reps=N.lignes.map(L=>L.repere.trim()),pref={};
  reps.forEach(r=>{const m=r.toUpperCase().match(/^([A-Z]+)\d/);if(m)pref[m[1]]=(pref[m[1]]||0)+1});
  const out=N.lignes.map(L=>{const R={cells:{},brut:{},conf:{},corr:{},doute:{},box:{},edite:[],src:L.id},P={};
    N.colonnes.forEach((c,j)=>{const k=VERS[c.cle]||'autre',T=((L.idsCellules||[])[j]||[]).map(i=>tid.get(i)).filter(Boolean);(P[k]=P[k]||[]).push({c,v:L.cellules[j]||'',T})});
    Object.entries(P).forEach(([k,A])=>{const T=A.flatMap(a=>a.T),O=T.map(t=>t.ocr||{});
      let v=k==='autre'?A.filter(a=>a.v).map(a=>`${(a.c.titre||'colonne').replace(/\n/g,' ')} : ${a.v}`).join(' · '):A.map(a=>a.v).filter(Boolean).join(' — ');
      const corr=O.flatMap(o=>o.corrections||[]),conf=O.length?Math.min(...O.map(o=>o.conf)):null;
      if(k==='ouverture'&&!A.some(a=>a.c.cle==='ouverture')&&L.dims){   // colonne Diamètre ou Largeur + Hauteur : cote reconstituée, à confirmer
        v=L.dims.type==='circ'?'Ø'+L.dims.D:L.dims.a+'x'+L.dims.b;R.info=Object.assign(R.info||{},{[k]:`cote reprise de la colonne « ${L.dims.colonne.replace(/\n/g,' ')} » : ${v}`})}
      if(k==='ouverture'&&conf!=null&&conf<SEUIL&&OMAL.test(v.trim()))   // jamais converti : 250 peut être Ø50 ou 250 ; l'utilisateur précise Ø
        corr.push(`« ${v.trim()} » : nombre seul ambigu (symbole Ø mal lu ?), à préciser — valeur gardée telle quelle`);
      if(k==='ouverture'&&/\d[+'`´]\d/.test(v)){const u=v.replace(/(?<=\d)[+'`´](?=\d)/g,'');   // « 4+00x400 » : signe parasite dans un nombre
        if(u!==v&&root.CPI.nomenclatures.cotes(u).etat==='rect'){corr.push(`« ${v} » lu comme ${u}`);v=u}}
      if((k==='angle'||k==='niveau')&&/^[Oo]$/.test(v.trim())){corr.push(`« ${v.trim()} » lu comme 0`);v='0'}   // zéro seul lu comme la lettre O
      if(k==='repere'&&v){let u=v.replace(/\s+/g,'').toUpperCase();const m=u.match(/^([A-Z]+?)([IL1|O0SBZG]+)$/);
        if(!/\d/.test(u)&&m&&pref[m[1]]){u=m[1]+m[2].replace(/[IL|]/g,'1').replace(/O/g,'0').replace(/S/g,'5').replace(/B/g,'8').replace(/Z/g,'2').replace(/G/g,'6')}
        // « 53 » dans une colonne de repères S1, S2… : 1re lettre lue comme le chiffre qui lui ressemble (signalé)
        const LD={S:'5',B:'8',O:'0',I:'1',Z:'2',G:'6'},px=/^\d{2,}$/.test(u)&&Object.keys(pref).find(p=>p.length===1&&pref[p]>=2&&LD[p]===u[0]);if(px)u=px+u.slice(1);
        if(u!==v.replace(/\s+/g,'').toUpperCase())corr.push(`repère « ${v} » lu comme ${u}`);v=u}   // espaces et minuscules : sans signalement
      R.cells[k]=v;R.brut[k]=O.map(o=>o.brut).join(' ');R.conf[k]=conf;R.corr[k]=corr;R.doute[k]=conf!=null&&conf<SEUIL||corr.length>0;R.box[k]=unionBox(O.map(o=>o.box).filter(Boolean))});
    R.cle0=root.CPI.nomenclatures.cleRep(R.cells.repere||'');   // repère tel que reconnu : retrouve la ligne quand l'OCR est relancé
    return R});
  // repères en double, ou hors d'une suite régulière (D12, D15, D14 : 3 et 5 confondus) : signalés, jamais modifiés
  const rows=out,cles=rows.map(r=>r.cle0),num=rows.map(r=>{const m=r.cle0.match(/^([A-Z]*)(\d+)$/);return m?{p:m[1],n:+m[2]}:null});
  const suite=num.filter((x,i)=>i&&x&&num[i-1]&&x.p===num[i-1].p&&x.n===num[i-1].n+1).length>=0.7*(rows.length-1);
  rows.forEach((r,i)=>{if(!r.cle0)return;const m=[];
    if(cles.filter(c=>c===r.cle0).length>1)m.push('repère présent plusieurs fois dans le tableau');
    const x=num[i],a=num[i-1],b=num[i+1];
    const ok=(u,d)=>!u||u.p!==x.p||x.n===u.n+d;   // voisin absent, d'une autre série, ou dans la suite
    if(suite&&x&&!m.length&&(a||b)&&!(a&&ok(a,1))&&!(b&&ok(b,-1)))m.push('repère hors de la suite des repères voisins');
    if(m.length){r.corr.repere=(r.corr.repere||[]).concat(m.map(t=>t+' : à vérifier'));r.doute.repere=true}});
  return rows}
// Colonnes à afficher : la base, puis celles qui ont une valeur dans au moins une ligne
const colonnes=rows=>COLONNES.filter(([k])=>BASE.includes(k)||rows.some(r=>String(r.cells[k]||'').trim()));
// Grille vérifiée → nomenclature au contrat de nomenclatures.js (mêmes règles de cotes : CPI.nomenclatures.ligne).
// m = {id, fichier, page, zone, titre, unite (unité des dimensions : choisie ou lue dans l'en-tête), mesures}
function versNomenclature(rows,m){const C=colonnes(rows),cols=C.map(([k,t])=>({titre:t+(k==='ouverture'&&m.unite?` (${m.unite})`:''),cle:k,unite:k==='ouverture'?m.unite||null:null}));
  const lignes=rows.map((r,i)=>{const cells=C.map(([k])=>String(r.cells[k]||'').trim()),L=root.CPI.nomenclatures.ligne(cols,cells),inc=[],corr=[],brut={},cf={},cg={};
    C.forEach(([k,t])=>{if(r.brut&&r.brut[k])brut[t]=r.brut[k];if(r.conf&&r.conf[k]!=null)cf[t]=r.conf[k];(r.corr&&r.corr[k]||[]).forEach(c=>corr.push(`${t} : ${c}`));
      if(r.edite.includes(k))cg[t]=String(r.cells[k]||'');
      else if(r.doute&&r.doute[k]){inc.push(t);L.a_verifier.push(`${t} : lecture incertaine${r.brut&&r.brut[k]?` (OCR « ${r.brut[k]} »${r.conf[k]!=null?`, confiance ${r.conf[k]} %`:''})`:''}`)}});
    if(!r.src)L.a_verifier.push('ligne ajoutée à la main pendant la vérification');
    return Object.assign({id:`${m.id}-L${String(i+1).padStart(2,'0')}`,rang:i+1,ids:[],calques:[]},L,{box:unionBox(Object.values(r.box||{}).filter(Boolean))},
      m.texte?{corrige:cg}:{ocr:{brut,confiance:cf,corrections:corr,corrige:cg,incertain:inc,ajoutee:!r.src,moteur:VERSION,...(m.mesures&&m.mesures.methode?{methode:m.mesures.methode}:{})}})});
  const nI=lignes.reduce((s,L)=>s+(L.ocr?L.ocr.incertain.length:0),0);
  if(m.texte)return{id:m.id,ocr:false,grilleTexte:true,fichier:m.fichier,format:'pdf',espace:'papier',presentation:'Page '+m.page,page:m.page,titre:m.titre||'',nature:'reservations',colonnes:cols,
    cadre:m.zone?[m.zone.x0,m.zone.y0,m.zone.x1,m.zone.y1]:null,zone:m.zone,ids:[],calques:[],lignes,unite:m.unite||null,
    qualite:{niveau:'vérifiée',motifs:['textes du PDF rangés dans la grille de traits du tableau (en-tête non reconnu automatiquement), colonnes vérifiées par l\'utilisateur']}};
  return{id:m.id,ocr:true,fichier:m.fichier,format:'pdf',espace:'papier',presentation:'Page '+m.page,page:m.page,titre:m.titre||'',nature:'reservations',colonnes:cols,
    cadre:m.zone?[m.zone.x0,m.zone.y0,m.zone.x1,m.zone.y1]:null,zone:m.zone,ids:[],calques:[],lignes,unite:m.unite||null,mesures:m.mesures||null,
    qualite:{niveau:'OCR vérifiée',motifs:[`reconnaissance optique (${VERSION}), lignes vérifiées par l'utilisateur`,nI?`${nI} cellule(s) incertaine(s) non corrigée(s)`:'aucune cellule incertaine laissée']}}}

root.CPI=Object.assign(root.CPI||{},{ocr:{VERSION,SEUIL,COLONNES,oslash,charger,arreter,reconnaitre,pretraiter,corriger,lireZone,lireBlocs,lireGrille,grille,colonnes,versNomenclature}});
})(typeof globalThis!=='undefined'?globalThis:this);
