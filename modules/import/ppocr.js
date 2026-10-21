// CoffraPlan — module d'import de plans : moteur de reconnaissance PP-OCRv6 (PaddleOCR, Apache-2.0) exécuté localement par
// ONNX Runtime Web 1.30.0 (Microsoft, MIT) en WebAssembly SIMD. Modèle « PP-OCRv6 small » de reconnaissance de lignes de texte
// (multilingue : français accentué, Ø, ×, °), tel que publié (empreinte SHA-256 vérifiée par assembler.py), embarqué dans le HTML :
// aucun téléchargement, aucune requête réseau, aucun service extérieur. Chargé au premier besoin (≈ 2 s), puis gardé en mémoire.
// Contrat commun des moteurs (CPI.moteurs) : lire(images) → [{texte, conf (0-100), chars:[{t,c}], orientation (0 | 90 | 270)}] ;
// une image = une ligne de texte (cellule, repère) ; jamais de cote ni de repère inventé : un texte illisible reste vide.
(function(root){'use strict';
const VERSION='PP-OCRv6 small (reconnaissance) · ONNX Runtime Web 1.30.0 (WebAssembly SIMD)';
const src=id=>{const s=root.document&&root.document.getElementById(id);if(!s)throw new Error('moteur PP-OCR absent de ce fichier ('+id+')');return s.textContent};
const b64=s=>{const t=atob(s.replace(/\s+/g,'')),u=new Uint8Array(t.length);for(let i=0;i<t.length;i++)u[i]=t.charCodeAt(i);return u};
const gunzip=async u=>new Uint8Array(await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
const H=48,W_MIN=64,W_MAX=3200;   // hauteur d'entrée du modèle ; largeur = celle du texte (sans complément à 320 : même justesse mesurée, calcul plus court), plafonnée
let P=null;
// Démarrage (une fois) : ONNX Runtime depuis les blocs du HTML (une page file:// ne peut ni lancer de threads ni lire un fichier voisin :
// un seul fil, wasm et module de chargement fournis en mémoire), session du modèle, dictionnaire
function charger(){if(P)return P;
  P=(async()=>{if(!root.ort){const s=root.document.createElement('script');s.textContent=src('ppocr-ort-src');root.document.head.appendChild(s);s.remove()}
    const ort=root.ort;if(!ort)throw new Error('ONNX Runtime non chargé');
    ort.env.wasm.numThreads=1;ort.env.wasm.proxy=false;
    ort.env.wasm.wasmPaths={mjs:URL.createObjectURL(new Blob([src('ppocr-ort-mjs')],{type:'text/javascript'})),
      wasm:URL.createObjectURL(new Blob([await gunzip(b64(src('ppocr-ort-wasm')))],{type:'application/wasm'}))};
    const rec=await ort.InferenceSession.create(await gunzip(b64(src('ppocr-rec'))),{executionProviders:['wasm'],graphOptimizationLevel:'all'});
    return{ort,rec,dict:src('ppocr-dict').replace(/^\n|\n$/g,'').split('\n')}})();
  P.catch(()=>{P=null});return P}

// Lignes (canvas, texte noir sur fond clair) → [{texte, conf, chars}] ; entrée BGR normalisée (x/255 − 0,5) / 0,5, hauteur 48, largeur
// proportionnelle ; par lots de largeurs voisines (≤ 8 lignes, complétées par des zéros comme dans PaddleOCR) : moins d'appels au moteur ;
// décodage CTC glouton (0 = blanc)
const LOT=8;
async function lignes(M,C){const P=C.map((c,i)=>{const w=Math.min(W_MAX,Math.max(1,Math.round(c.width*H/Math.max(1,c.height))));
    const t=root.document.createElement('canvas');t.width=w;t.height=H;const g=t.getContext('2d',{willReadFrequently:true});g.fillStyle='#fff';g.fillRect(0,0,w,H);g.drawImage(c,0,0,w,H);
    return{i,w,d:g.getImageData(0,0,w,H).data}}).sort((a,b)=>a.w-b.w),R=[];
  for(let k=0;k<P.length;){const L=[P[k]];while(L.length<LOT&&k+L.length<P.length&&P[k+L.length].w<=1.3*P[k].w+16)L.push(P[k+L.length]);k+=L.length;
    const W=Math.max(W_MIN,L[L.length-1].w),N=H*W,X=new Float32Array(L.length*3*N);
    L.forEach((l,b)=>{const B=b*3*N;for(let y=0;y<H;y++)for(let x=0;x<l.w;x++){const i=4*(y*l.w+x),o=B+y*W+x;X[o]=l.d[i+2]/127.5-1;X[N+o]=l.d[i+1]/127.5-1;X[2*N+o]=l.d[i]/127.5-1}});
    const r=await M.rec.run({[M.rec.inputNames[0]]:new M.ort.Tensor('float32',X,[L.length,3,H,W])}),o=r[M.rec.outputNames[0]],T=o.dims[1],Cn=o.dims[2],p=o.data;
    L.forEach((l,b)=>{const ch=[];let prev=0;for(let s=0;s<T;s++){const O=(b*T+s)*Cn;let q=0,m=-1;for(let j=0;j<Cn;j++){const v=p[O+j];if(v>m){m=v;q=j}}
        if(q&&q!==prev)ch.push({t:q-1<M.dict.length?M.dict[q-1]:' ',c:Math.round(100*m)});prev=q}
      R[l.i]={texte:ch.map(x=>x.t).join('').replace(/\s+/g,' ').trim(),conf:ch.length?Math.round(ch.reduce((a,x)=>a+x.c,0)/ch.length):0,chars:ch}})}
  return R}
const tourne=(c,sens)=>{const t=root.document.createElement('canvas');t.width=c.height;t.height=c.width;const g=t.getContext('2d');
  g.translate(t.width/2,t.height/2);g.rotate(sens*Math.PI/2);g.drawImage(c,-c.width/2,-c.height/2);return t};
// images → lectures ; o.vertical (vrai, ou fonction image → vrai) : ligne écrite de bas en haut ou de haut en bas, les deux sens
// sont lus et la lecture la plus sûre est gardée (orientation 90 ou 270) ; o.annule() → vrai : arrêt (lève « annulé »)
async function lire(images,o){o=o||{};const M=await charger(),V=images.map(c=>typeof o.vertical==='function'?o.vertical(c):!!o.vertical),R=[];
  if(o.annule&&o.annule())throw new Error('annulé');
  // b : quart de tour horaire (texte écrit de bas en haut → 90°, sens trigonométrique des PDF) ; a : antihoraire (haut en bas → 270°)
  const h=images.map((c,i)=>V[i]?null:c),a=images.map((c,i)=>V[i]?tourne(c,-1):null),b=images.map((c,i)=>V[i]?tourne(c,1):null);
  const lit=async A=>{const I=A.map((c,i)=>c?i:-1).filter(i=>i>=0),L=I.length?await lignes(M,I.map(i=>A[i])):[],O=[];I.forEach((i,k)=>O[i]=L[k]);return O};
  const [Lh,La,Lb]=[await lit(h),await lit(a),await lit(b)];if(o.annule&&o.annule())throw new Error('annulé');
  const sc=x=>x.conf*Math.min(1,x.texte.length/3);
  images.forEach((c,i)=>R.push(V[i]?(sc(Lb[i])>sc(La[i])?Object.assign(Lb[i],{orientation:90}):Object.assign(La[i],{orientation:270})):Object.assign(Lh[i],{orientation:0})));
  return R}
async function arreter(){const p=P;P=null;if(!p)return;try{(await p).rec.release()}catch(e){}}
root.CPI=Object.assign(root.CPI||{},{ppocr:{VERSION,charger,lire,arreter}});
})(typeof globalThis!=='undefined'?globalThis:this);
