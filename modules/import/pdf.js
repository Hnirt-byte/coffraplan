// CoffraPlan — module d'import de plans : lecteur PDF (PDF.js 6.4.299, Apache-2.0, intégré au HTML par assembler.py).
// PDF → document normalisé du lecteur (contrat : modules/import/README.md) : chaque page est un espace « papier » distinct
// (présentation « Page n »), ses textes et traits sont en points PDF, Y vers le haut, dans le sens où la page s'affiche
// (rotation /Rotate et matrices appliquées). Aucune géométrie n'est proposée comme réservation : une longueur sur la page
// n'est pas une cote réelle (échelle inconnue). Les coordonnées de deux pages ne sont jamais mélangées.
// Diagnostic par page : texte extractible, dessin vectoriel sans texte (textes vectorisés), image (numérisation probable).
// Chargé à la première ouverture d'un PDF ; aucune requête réseau (polices standard, CMap, wasm : désactivés).
(function(root){'use strict';
let LIB=null,FERME=Promise.resolve();   // FERME : dernière libération de document, attendue avant d'en ouvrir un autre
const SEG_DET=400000;   // shortcut: repérage des réservations (chemins), au-delà les traits ne sont pas lus (signalé) ; à relever si un vrai plan le demande
const PETIT=20,PETIT_MAX=400000;   // pt ; shortcut: au-delà de 400 000 petits sous-chemins par page, les suivants ne servent pas à chercher les textes dessinés
const COURBES_MAX=200000;   // shortcut: au-delà de 200 000 pièces de Bézier par page, les suivantes ne servent pas aux parois courbes (signalé : coupeCourbes)
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

// Parcours des tracés d'une page : chaque sous-chemin (m … z) en points de la page affichée (Y vers le bas ici, comme le
// viewport ; l'appelant retourne Y). sp(pts, ferme, courbes, peint) : pts = sommets (extrémités des segments et des courbes),
// courbes = [[p0, c1, c2, p3]…] (quadratiques élevées en cubiques), peint = faux pour un chemin de découpe sans tracé (W n).
function cheminsPage(lib,ol,vp,sp,img){const O=lib.OPS,D={0:'m',1:'l',2:'c',3:'q',4:'z'},imgs=new Set(IMG.map(k=>O[k]).filter(v=>v!=null));
  let ctm=[1,0,0,1,0,0],pile=[];
  for(let i=0;i<ol.fnArray.length;i++){const f=ol.fnArray[i],a=ol.argsArray[i];
    if(f===O.save)pile.push(ctm);else if(f===O.restore)ctm=pile.pop()||ctm;else if(f===O.transform)ctm=mul(ctm,a);
    else if(f===O.paintFormXObjectBegin){pile.push(ctm);if(a&&a[0])ctm=mul(ctm,a[0])}else if(f===O.paintFormXObjectEnd)ctm=pile.pop()||ctm;
    else if(imgs.has(f)){if(img)img()}
    else if(f===O.constructPath){const d=a&&a[1]&&a[1][0];if(!d||!d.length)continue;const peint=a[0]!==O.endPath;
      const T=mul(vp.transform,ctm),p=(x,y)=>[T[0]*x+T[2]*y+T[4],T[1]*x+T[3]*y+T[5]];
      let k=0,pts=null,cb=[],cur=null;const fin=z=>{if(pts&&pts.length>1)sp(pts,z,cb,peint);pts=null;cb=[]};
      sp.chemin&&sp.chemin();
      while(k<d.length){const o=D[d[k++]];
        if(o==='m'){fin(false);cur=p(d[k],d[k+1]);pts=[cur];k+=2}
        else if(o==='l'){cur=p(d[k],d[k+1]);k+=2;if(pts)pts.push(cur)}
        else if(o==='c'){const c1=p(d[k],d[k+1]),c2=p(d[k+2],d[k+3]),q=p(d[k+4],d[k+5]);k+=6;if(pts){cb.push([cur,c1,c2,q]);pts.push(q)}cur=q}
        else if(o==='q'){const c=p(d[k],d[k+1]),q=p(d[k+2],d[k+3]);k+=4;if(pts){cb.push([cur,[cur[0]+2/3*(c[0]-cur[0]),cur[1]+2/3*(c[1]-cur[1])],[q[0]+2/3*(c[0]-q[0]),q[1]+2/3*(c[1]-q[1])],q]);pts.push(q)}cur=q}
        else if(o==='z'){if(pts){const st=pts[0];fin(true);cur=st;pts=[st]}}
        else break}
      fin(false)}}}

// Traits droits (horizontaux et verticaux seulement : ceux des grilles de tableaux) et compte des chemins et images
function traitsPage(lib,ol,vp,n,P){const H=vp.height,S=[];let nCh=0,nSeg=0,nImg=0,coupe=false;
  const seg=(u,v)=>{nSeg++;if(coupe)return;const dx=v[0]-u[0],dy=v[1]-u[1],l=Math.hypot(dx,dy);
    if(l>0&&(Math.abs(dy)<=0.01*l||Math.abs(dx)<=0.01*l)){if(S.length>=SEG_MAX){coupe=true;return}S.push({calque:'',espace:'papier',presentation:P,page:n,a:[u[0],H-u[1]],b:[v[0],H-v[1]]})}};
  const sp=(pts,z,cb)=>{let j=0;for(let i=1;i<pts.length;i++){if(j<cb.length&&cb[j][3]===pts[i]){j++;continue}seg(pts[i-1],pts[i])}if(z)seg(pts[pts.length-1],pts[0])};
  sp.chemin=()=>nCh++;
  cheminsPage(lib,ol,vp,sp,()=>nImg++);
  return{S,nCh,nSeg,nImg,coupe}}

// Nature d'une page pour le rapport : lecture automatique possible ou saisie assistée
// « mixte » : peu de textes pour beaucoup de tracés (export de DAO qui vectorise une partie des textes, ex. un tableau)
function nature(p){return p.textes>=3?(p.chemins>50*p.textes?'mixte':'texte'):p.images&&p.chemins<50?'image':p.chemins?'vectoriel':'vide'}
const LIB_NAT={texte:'textes extractibles',mixte:'quelques textes extractibles, nombreux tracés (une partie des textes, par exemple un tableau, est peut-être dessinée en traits)',vectoriel:'dessin vectoriel sans texte extractible (textes probablement vectorisés)',image:'image seule (numérisation probable, pas de texte)',vide:'page vide'};

// Lecture : données (ArrayBuffer ou Uint8Array) → {ok:true, document, pdf (PDFDocumentProxy, pour l'aperçu)} | {ok:false, message}
async function lire(data,nom){let lib,pdf;
  try{lib=await charger()}catch(e){return{ok:false,message:'lecteur PDF indisponible : '+(e&&e.message||e)}}
  await FERME;   // le worker est partagé : PDF.js refuse un nouveau document tant qu'une libération est en cours
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

// Tracés d'une page pour le repérage des réservations (geometrie.js), relus à la demande (rien n'est gardé à l'ouverture) :
// segments droits de tous les chemins peints et sous-chemins fermés courbes ou à nombreux sommets (cercles possibles), en
// points de la page affichée, Y vers le haut (même repère que les textes). → {page, w, h, segments, contours, petits, courbes, coupe, coupeCourbes} ;
// petits = emprises [x0,y0,x1,y1,…] à plat des sous-chemins de moins de 20 pt (lettres dessinées, flèches, hachures) ;
// courbes (phase 9A, support.js) = pièces de Bézier [{id, c:[p0,c1,c2,p3]}] des sous-chemins peints de plus de 20 pt, ouverts ou fermés (parois courbes).
// o.zones = [[x0,y0,x1,y1]…] (points, Y vers le haut) : lecture LOCALE, seuls les tracés qui touchent une zone sont gardés (les plafonds
// s'appliquent après ce tri : une page très chargée se relit en entier autour des réservations)
async function chemins(pdf,n,o){const lib=await charger(),pg=await pdf.getPage(n),vp=pg.getViewport({scale:1}),ol=await pg.getOperatorList(),H=vp.height,S=[],C=[],B=[],K=[],Z=o&&o.zones&&o.zones.length?o.zones:null;
  let ch=0,coupe=false,coupeK=false;const Y=q=>[q[0],H-q[1]],touche=(x0,y0,x1,y1)=>!Z||Z.some(z=>x1>=z[0]&&x0<=z[2]&&y1>=z[1]&&y0<=z[3]);
  const sp=(pts,z,cb,peint)=>{if(!peint)return;const P=pts.map(Y),id=`p${n}-c${ch}`,q=P[P.length-1];z=z||P.length>2&&Math.hypot(q[0]-P[0][0],q[1]-P[0][1])<0.01;
    // petit sous-chemin (trait ou contour de lettre dessinée, flèche, hachure) : son emprise sert à trouver les textes dessinés
    let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;for(const p of P){if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];if(p[1]<y0)y0=p[1];if(p[1]>y1)y1=p[1]}
    if(Z){for(const c of cb)for(const p of c){const r=Y(p);if(r[0]<x0)x0=r[0];if(r[0]>x1)x1=r[0];if(r[1]<y0)y0=r[1];if(r[1]>y1)y1=r[1]}if(!touche(x0,y0,x1,y1))return}
    const petit=x1-x0<=PETIT&&y1-y0<=PETIT;
    if(petit&&B.length<4*PETIT_MAX)B.push(x0,y0,x1,y1);
    const garde=(a,b)=>!Z||touche(Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[0],b[0]),Math.max(a[1],b[1]));
    let j=0;for(let i=1;i<P.length;i++){if(j<cb.length&&cb[j][3]===pts[i]){j++;continue}if(!garde(P[i-1],P[i]))continue;if(S.length>=SEG_DET){coupe=true;break}S.push({id:id+'-'+S.length,a:P[i-1],b:P[i]})}
    if(z&&P.length>2&&!cb.length&&S.length<SEG_DET&&garde(P[P.length-1],P[0]))S.push({id:id+'-'+S.length,a:P[P.length-1],b:P[0]});
    if(z&&(cb.length||P.length>=8))C.push({id:id+'-k'+C.length,pts:P,courbes:cb.map(c=>c.map(Y))});
    if(!petit)cb.forEach((c,m)=>{if(K.length>=COURBES_MAX){coupeK=true;return}K.push({id:id+'-b'+m,c:c.map(Y)})})};
  sp.chemin=()=>ch++;
  cheminsPage(lib,ol,vp,sp,null);pg.cleanup();
  return{page:n,w:vp.width,h:vp.height,segments:S,contours:C,petits:B,courbes:K,coupe,coupeCourbes:coupeK,zones:Z}}

// Libère un document lu (le worker partagé reste ouvert pour le PDF suivant) ; lire() attend la fin de la libération
function fermer(pdf){try{const t=pdf&&pdf.loadingTask;if(t)FERME=Promise.all([FERME,t.destroy().catch(()=>{})])}catch(e){}return FERME}

root.CPI=Object.assign(root.CPI||{},{pdf:{charger,lire,rendre,rendreZone,chemins,fermer,nature,LIB_NAT}});
})(typeof globalThis!=='undefined'?globalThis:this);
