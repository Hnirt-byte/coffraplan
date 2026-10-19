// CoffraPlan — module d'import de plans : lecteur PDF (PDF.js 6.4.299, Apache-2.0, intégré au HTML par assembler.py).
// PDF → document normalisé du lecteur (contrat : modules/import/README.md) : chaque page est un espace « papier » distinct
// (présentation « Page n »), ses textes et traits sont en points PDF, Y vers le haut, dans le sens où la page s'affiche
// (rotation /Rotate et matrices appliquées). Aucune géométrie n'est proposée comme réservation : une longueur sur la page
// n'est pas une cote réelle (échelle inconnue). Les coordonnées de deux pages ne sont jamais mélangées.
// Diagnostic par page : texte extractible, dessin vectoriel sans texte (textes vectorisés), image (numérisation probable).
// Chargé à la première ouverture d'un PDF ; aucune requête réseau (polices standard, CMap, wasm : désactivés).
(function(root){'use strict';
let LIB=null;
const SEG_MAX=60000;   // shortcut: au-delà, les traits d'une page ne sont plus relevés (le diagnostic les compte) ; à relever si un vrai plan le demande
const src=id=>{const s=root.document&&root.document.getElementById(id);if(!s)throw new Error('lecteur PDF absent de ce fichier ('+id+')');return s.textContent};
const blobUrl=t=>URL.createObjectURL(new Blob([t],{type:'text/javascript'}));
// Worker : le module publié, transformé en script classique au chargement (une page ouverte en file:// ne peut pas lancer
// de worker de module depuis une URL blob) ; texte du bloc inchangé. Sans worker : PDF.js tourne dans la page (plus lent).
function charger(){if(LIB)return LIB;
  LIB=(async()=>{const lib=await import(blobUrl(src('pdfjs-src'))),ws=src('pdfjs-worker-src');
    let ok=false;try{const w=new Worker(blobUrl(ws.replace(/import\.meta\.url/g,'self.location.href').replace(/export\s*\{[^}]*\}\s*;?\s*$/,'')));
      ok=await new Promise(r=>{const t=setTimeout(()=>r(false),8000);w.onerror=()=>{clearTimeout(t);r(false)};w.onmessage=()=>{clearTimeout(t);r(true)}});
      if(ok){w.onerror=w.onmessage=null;lib.GlobalWorkerOptions.workerPort=w}else w.terminate()}catch(e){ok=false}
    if(!ok)await import(blobUrl(ws));
    return lib})();
  LIB.catch(()=>{LIB=null});return LIB}
// produit de matrices PDF [a b c d e f] (m1 × m2, comme Util.transform) : calcul local, indépendant des versions de PDF.js
const mul=(m1,m2)=>[m1[0]*m2[0]+m1[2]*m2[1],m1[1]*m2[0]+m1[3]*m2[1],m1[0]*m2[2]+m1[2]*m2[3],m1[1]*m2[2]+m1[3]*m2[3],m1[0]*m2[4]+m1[2]*m2[5]+m1[4],m1[1]*m2[4]+m1[3]*m2[5]+m1[5]];
const OPTS={isEvalSupported:false,enableXfa:false,useSystemFonts:true,disableFontFace:false,standardFontDataUrl:null,cMapUrl:null,wasmUrl:null,iccUrl:null,
  stopAtErrors:false,verbosity:0};
const IMG=['paintImageXObject','paintInlineImageXObject','paintImageMaskXObject','paintImageXObjectRepeat','paintInlineImageXObjectGroup','paintImageMaskXObjectGroup','paintImageMaskXObjectRepeat','paintSolidColorImageMask'];
// caractères illisibles (police sans table Unicode) : zone privée, contrôles, U+FFFD
const illisible=s=>{const c=[...s].filter(x=>!/\s/.test(x));return c.length>0&&c.filter(x=>/[-�\u0000-\u001F]/.test(x)).length>=c.length/2};

// Textes d'une page : morceaux voisins sur la même ligne de base réunis (certains PDF placent chaque caractère à part)
function textesPage(lib,tc,vp,n,P){const M=vp.transform,H=vp.height,R=[];let nIl=0;
  tc.items.forEach(it=>{if(!it.str||!it.str.trim())return;
    const m=mul(M,it.transform),fs=Math.hypot(m[2],m[3]);if(!(fs>0))return;
    const a=Math.atan2(m[1],m[0]),c=Math.cos(a),s=Math.sin(a),w=Math.max(0,it.width*Math.hypot(m[0],m[1])/(Math.hypot(it.transform[0],it.transform[1])||1));
    const r=R[R.length-1];
    if(r&&Math.abs(r.a-a)<0.02&&Math.abs(r.fs-fs)<=0.25*Math.max(r.fs,fs)){const dx=m[4]-r.ex,dy=m[5]-r.ey,gap=dx*c+dy*s,perp=-dx*s+dy*c;
      if(Math.abs(perp)<=0.25*fs&&gap>=-0.3*fs&&gap<=0.35*fs){r.str+=(gap>0.12*fs&&!/\s$/.test(r.str)&&!/^\s/.test(it.str)?' ':'')+it.str;r.ex=m[4]+c*w;r.ey=m[5]+s*w;r.w=Math.hypot(r.ex-r.ox,r.ey-r.oy);return}}
    R.push({str:it.str,a,fs,ox:m[4],oy:m[5],ex:m[4]+c*w,ey:m[5]+s*w,w})});
  const T=[];
  R.forEach(r=>{const t=r.str.replace(/\s+/g,' ').trim();if(!t)return;if(illisible(t)){nIl++;return}
    const c=Math.cos(r.a),s=Math.sin(r.a),h=0.7*r.fs;   // h : hauteur des majuscules ≈ 0,7 corps (comme la hauteur d'un texte DXF)
    // centre : origine + demi-largeur le long du texte + demi-hauteur vers le haut du texte (repère écran, Y vers le bas)
    const x=r.ox+c*r.w/2+s*h/2,y=r.oy+s*r.w/2-c*h/2,rot=((-r.a*180/Math.PI)%360+360)%360;
    T.push({id:`p${n}-t${T.length+1}`,calque:'',espace:'papier',presentation:P,page:n,nature:'texte PDF',texte:t,x,y:H-y,h,w:r.w,rot:Math.round(rot*100)/100})});
  return{T,nIl}}

// Traits droits (horizontaux et verticaux seulement : ceux des grilles de tableaux) et compte des chemins et images
function traitsPage(lib,ol,vp,n,P){const O=lib.OPS,D={0:'m',1:'l',2:'c',3:'q',4:'z'},H=vp.height,S=[],imgs=new Set(IMG.map(k=>O[k]).filter(v=>v!=null));
  let ctm=[1,0,0,1,0,0],pile=[],nCh=0,nSeg=0,nImg=0,coupe=false;
  for(let i=0;i<ol.fnArray.length;i++){const f=ol.fnArray[i],a=ol.argsArray[i];
    if(f===O.save)pile.push(ctm);else if(f===O.restore)ctm=pile.pop()||ctm;else if(f===O.transform)ctm=mul(ctm,a);
    else if(f===O.paintFormXObjectBegin){pile.push(ctm);if(a&&a[0])ctm=mul(ctm,a[0])}else if(f===O.paintFormXObjectEnd)ctm=pile.pop()||ctm;
    else if(imgs.has(f))nImg++;
    else if(f===O.constructPath){const d=a&&a[1]&&a[1][0];if(!d||!d.length)continue;nCh++;
      const T=mul(vp.transform,ctm),p=(x,y)=>[T[0]*x+T[2]*y+T[4],H-(T[1]*x+T[3]*y+T[5])];
      let k=0,cur=null,st=null;
      const seg=(u,v)=>{nSeg++;if(coupe)return;const dx=v[0]-u[0],dy=v[1]-u[1],l=Math.hypot(dx,dy);
        if(l>0&&(Math.abs(dy)<=0.01*l||Math.abs(dx)<=0.01*l)){if(S.length>=SEG_MAX){coupe=true;return}S.push({calque:'',espace:'papier',presentation:P,page:n,a:u,b:v})}};
      while(k<d.length){const o=D[d[k++]];
        if(o==='m'){cur=st=p(d[k],d[k+1]);k+=2}
        else if(o==='l'){const q=p(d[k],d[k+1]);k+=2;if(cur)seg(cur,q);cur=q}
        else if(o==='c'){cur=p(d[k+4],d[k+5]);k+=6}
        else if(o==='q'){cur=p(d[k+2],d[k+3]);k+=4}
        else if(o==='z'){if(cur&&st)seg(cur,st);cur=st}
        else break}}}
  return{S,nCh,nSeg,nImg,coupe}}

// Nature d'une page pour le rapport : lecture automatique possible ou saisie assistée
// « mixte » : peu de textes pour beaucoup de tracés (export de DAO qui vectorise une partie des textes, ex. un tableau)
function nature(p){return p.textes>=3?(p.chemins>50*p.textes?'mixte':'texte'):p.images&&p.chemins<50?'image':p.chemins?'vectoriel':'vide'}
const LIB_NAT={texte:'textes extractibles',mixte:'quelques textes extractibles, nombreux tracés (une partie des textes, par exemple un tableau, est peut-être dessinée en traits)',vectoriel:'dessin vectoriel sans texte extractible (textes probablement vectorisés)',image:'image seule (numérisation probable, pas de texte)',vide:'page vide'};

// Lecture : données (ArrayBuffer ou Uint8Array) → {ok:true, document, pdf (PDFDocumentProxy, pour l'aperçu)} | {ok:false, message}
async function lire(data,nom){let lib,pdf;
  try{lib=await charger()}catch(e){return{ok:false,message:'lecteur PDF indisponible : '+(e&&e.message||e)}}
  try{pdf=await lib.getDocument(Object.assign({data:new Uint8Array(data)},OPTS)).promise}
  catch(e){return{ok:false,message:e&&e.name==='PasswordException'?'PDF protégé par mot de passe':'fichier PDF illisible ('+(e&&e.message||e)+')'}}
  const doc={format:'pdf',fichier:nom,version:'PDF',unite:null,entites:[],textes:[],traits:[],presentations:[],pages:[],signalements:[]};
  try{const meta=await pdf.getMetadata().catch(()=>null);if(meta&&meta.info&&meta.info.PDFFormatVersion)doc.version='PDF '+meta.info.PDFFormatVersion}catch(e){}
  for(let n=1;n<=pdf.numPages;n++){const P='Page '+n;
    try{const pg=await pdf.getPage(n),vp=pg.getViewport({scale:1}),tc=await pg.getTextContent(),ol=await pg.getOperatorList();
      const {T,nIl}=textesPage(lib,tc,vp,n,P),{S,nCh,nSeg,nImg,coupe}=traitsPage(lib,ol,vp,n,P);
      const info={n,presentation:P,w:vp.width,h:vp.height,rotation:pg.rotate,textes:T.length,textesIllisibles:nIl,chemins:nCh,segments:nSeg,images:nImg};
      info.nature=nature(info);doc.pages.push(info);doc.presentations.push(P);doc.textes.push(...T);doc.traits.push(...S);
      if(nIl)doc.signalements.push(`${P} : ${nIl} texte(s) illisible(s) (police sans correspondance Unicode), ignoré(s)`);
      if(coupe)doc.signalements.push(`${P} : plus de ${SEG_MAX} traits droits, les suivants ne sont pas lus pour les grilles de tableaux`);
      pg.cleanup()}
    catch(e){doc.pages.push({n,presentation:P,nature:"vide",erreur:String(e&&e.message||e),textes:0,chemins:0,images:0,segments:0});doc.signalements.push(`${P} : non lue (${e&&e.message||e})`)}}
  return{ok:true,document:doc,pdf}}

// Rendu d'une page dans un canvas (aperçu) ; échelle = pixels CSS par point PDF ; renvoie la tâche de rendu (annulable)
async function rendre(pdf,n,canvas,echelle){const pg=await pdf.getPage(n),vp=pg.getViewport({scale:echelle}),r=(root.devicePixelRatio||1);
  canvas.width=Math.round(vp.width*r);canvas.height=Math.round(vp.height*r);canvas.style.width=vp.width+'px';canvas.style.height=vp.height+'px';
  const t=pg.render({canvas,canvasContext:canvas.getContext('2d'),viewport:vp,transform:r!==1?[r,0,0,r,0,0]:null});
  return t}

// Rendu d'une zone de page (points PDF, Y vers le haut, page affichée : rotation comprise) dans un canvas neuf, fond blanc,
// à k pixels par point (OCR) ; le PDF n'est pas modifié
async function rendreZone(pdf,n,z,k){const pg=await pdf.getPage(n),vp=pg.getViewport({scale:k}),H=vp.height/k,cv=root.document.createElement('canvas');
  cv.width=Math.max(1,Math.ceil((z.x1-z.x0)*k));cv.height=Math.max(1,Math.ceil((z.y1-z.y0)*k));const g=cv.getContext('2d',{willReadFrequently:true});
  g.fillStyle='#fff';g.fillRect(0,0,cv.width,cv.height);
  await pg.render({canvas:cv,canvasContext:g,viewport:vp,transform:[1,0,0,1,-z.x0*k,-(H-z.y1)*k],background:'#fff'}).promise;
  return cv}

// Libère un document lu (le worker partagé reste ouvert pour le PDF suivant)
function fermer(pdf){try{const t=pdf&&pdf.loadingTask;if(t)t.destroy().catch(()=>{})}catch(e){}}

root.CPI=Object.assign(root.CPI||{},{pdf:{charger,lire,rendre,rendreZone,fermer,nature,LIB_NAT}});
})(typeof globalThis!=='undefined'?globalThis:this);
