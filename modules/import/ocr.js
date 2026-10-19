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
async function reconnaitre(canvas,o){const w=await charger(),opt=o||{};LOG=opt.progres||null;
  try{await w.setParameters({tessedit_pageseg_mode:String(opt.psm||11),preserve_interword_spaces:'1',user_defined_dpi:String(opt.dpi||300)});
    const r=await w.recognize(canvas,{},{blocks:true,text:false});const M=[];let nl=0;
    (r.data.blocks||[]).forEach(b=>(b.paragraphs||[]).forEach(p=>(p.lines||[]).forEach(l=>{nl++;(l.words||[]).forEach(m=>{if(!m.text||!m.text.trim())return;
      M.push({texte:m.text,conf:Math.round(m.confidence),x0:m.bbox.x0,y0:m.bbox.y0,x1:m.bbox.x1,y1:m.bbox.y1,ligne:nl,
        sym:(m.symbols||[]).map(s=>({t:s.text,c:Math.round(s.confidence)}))})})})));
    return M}
  finally{LOG=null}}


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

// ==== Tableau reconnu (CPI.nomenclatures.analyser sur les textes OCR) → grille de vérification → nomenclature ====
// Colonnes de la grille : celles demandées (repère, désignation, type, dimensions, niveau, observations) toujours affichées, les
// autres seulement si le tableau en a ; une colonne non reconnue va dans « Autres colonnes » (titre : valeur) : rien n'est perdu
const COLONNES=[['repere','Repère'],['description','Désignation'],['type','Type ou nature'],['ouverture',"Dimensions d'ouverture"],['reseau','Réseau (DN)'],
  ['niveau','Niveau ou altitude'],['angle','Angle'],['observations','Observations'],['lot','Lot / entreprise'],['quantite','Quantité'],['autre','Autres colonnes']];
const BASE=['repere','description','type','ouverture','niveau','observations'];
const VERS={repere:'repere',description:'description',type:'type',ouverture:'ouverture',diametre:'ouverture',largeur:'ouverture',hauteur:'ouverture',reseau:'reseau',
  niveau:'niveau',angle:'angle',observations:'observations',lot:'lot',quantite:'quantite'};
const unionBox=B=>B.length?{page:B[0].page,x0:Math.min(...B.map(b=>b.x0)),y0:Math.min(...B.map(b=>b.y0)),x1:Math.max(...B.map(b=>b.x1)),y1:Math.max(...B.map(b=>b.y1))}:null;
// Ø mal lu devant un nombre seul (« 2250 », « 0250 », « @16 », « D120 ») dans la colonne des dimensions, mot incertain seulement
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
        v=L.dims.type==='circ'?'Ø'+L.dims.D:L.dims.a+'x'+L.dims.b;corr.push(`cote reprise de la colonne « ${L.dims.colonne.replace(/\n/g,' ')} » : ${v}`)}
      if(k==='ouverture'&&conf!=null&&conf<SEUIL){const m=v.trim().match(OMAL);if(m){corr.push(`« ${v.trim()} » interprété Ø${m[1]} (symbole Ø mal lu ?)`);v='Ø'+m[1]}}
      if(k==='ouverture'&&/\d[+'`´]\d/.test(v)){const u=v.replace(/(?<=\d)[+'`´](?=\d)/g,'');   // « 4+00x400 » : signe parasite dans un nombre
        if(u!==v&&root.CPI.nomenclatures.cotes(u).etat==='rect'){corr.push(`« ${v} » lu comme ${u}`);v=u}}
      if((k==='angle'||k==='niveau')&&/^[Oo]$/.test(v.trim())){corr.push(`« ${v.trim()} » lu comme 0`);v='0'}   // zéro seul lu comme la lettre O
      if(k==='repere'&&v){let u=v.replace(/\s+/g,'').toUpperCase();const m=u.match(/^([A-Z]+?)([IL1|O0SBZG]+)$/);
        if(!/\d/.test(u)&&m&&pref[m[1]]){u=m[1]+m[2].replace(/[IL|]/g,'1').replace(/O/g,'0').replace(/S/g,'5').replace(/B/g,'8').replace(/Z/g,'2').replace(/G/g,'6')}
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
    return Object.assign({id:`${m.id}-L${String(i+1).padStart(2,'0')}`,rang:i+1,ids:[],calques:[]},L,{box:unionBox(Object.values(r.box||{}).filter(Boolean)),
      ocr:{brut,confiance:cf,corrections:corr,corrige:cg,incertain:inc,ajoutee:!r.src,moteur:VERSION}})});
  const nI=lignes.reduce((s,L)=>s+L.ocr.incertain.length,0);
  return{id:m.id,ocr:true,fichier:m.fichier,format:'pdf',espace:'papier',presentation:'Page '+m.page,page:m.page,titre:m.titre||'',nature:'reservations',colonnes:cols,
    cadre:m.zone?[m.zone.x0,m.zone.y0,m.zone.x1,m.zone.y1]:null,zone:m.zone,ids:[],calques:[],lignes,unite:m.unite||null,mesures:m.mesures||null,
    qualite:{niveau:'OCR vérifiée',motifs:[`reconnaissance optique (${VERSION}), lignes vérifiées par l'utilisateur`,nI?`${nI} cellule(s) incertaine(s) non corrigée(s)`:'aucune cellule incertaine laissée']}}}

root.CPI=Object.assign(root.CPI||{},{ocr:{VERSION,SEUIL,COLONNES,charger,arreter,reconnaitre,pretraiter,corriger,lireZone,grille,colonnes,versNomenclature}});
})(typeof globalThis!=='undefined'?globalThis:this);
