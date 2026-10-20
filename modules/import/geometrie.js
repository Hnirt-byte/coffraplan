// CoffraPlan — module d'import de plans : repérage géométrique des réservations sur une page PDF vectorielle.
// Entrée : tracés d'une page (CPI.pdf.chemins : segments et contours fermés, points PDF, Y vers le haut) et ses textes.
// Rectangles : reconstitués par CPI.detecteur.rectSegments (un contour fermé, un rectangle « re » ou des traits séparés donnent
// le même résultat) ; cercles : contours fermés en courbes de Bézier (ou polygones à nombreux sommets) dont tous les points
// sont à la même distance du centre. Les formes ne sont que des PROPOSITIONS : dimensions en points (échelle inconnue), aucune
// cote convertie ici. Cartouches, cellules de tableaux, cadres de feuille sont écartés avec leur raison (« non exploitable »).
// Textes voisins : repère (R12, TR-3…) et cotes écrites (650x800, Ø250) rattachés au contour le plus proche.
// Indépendant de l'interface et du moteur. Charger après detecteur.js et nomenclatures.js.
(function(root){'use strict';
const dist=(a,b)=>Math.hypot(b[0]-a[0],b[1]-a[1]);
const MIN=2;   // pt : en dessous (≈ 0,7 mm sur la feuille), hachures, flèches, symboles : ignorés
const REP=/^[A-Z]{1,4}[ .\-]?\d{1,4}[A-Z]?$/i;

// Contour fermé → cercle {centre, r} si sommets et milieux des courbes sont à 2 % près sur un même cercle, emprise carrée
function cercle(k){if(k.courbes.length<2&&k.pts.length<8)return null;
  const P=k.pts.concat(k.courbes.map(([a,b,c,d])=>[(a[0]+3*b[0]+3*c[0]+d[0])/8,(a[1]+3*b[1]+3*c[1]+d[1])/8]));
  const b=emprise(P),w=b[2]-b[0],h=b[3]-b[1];
  if(!(w>0)||Math.abs(w-h)>0.02*Math.max(w,h))return null;
  const c=[(b[0]+b[2])/2,(b[1]+b[3])/2],r=(w+h)/4;
  return P.every(p=>Math.abs(dist(p,c)-r)<=0.02*r)?{centre:c,r}:null}

// Emprise [x0,y0,x1,y1] d'une liste de points, sans Math.min(...) (pile dépassée au-delà de ~100 000 points)
function emprise(P){let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;for(const p of P){if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];if(p[1]<y0)y0=p[1];if(p[1]>y1)y1=p[1]}return[x0,y0,x1,y1]}
const dans=(b,p,m)=>p[0]>=b[0]-m&&p[0]<=b[2]+m&&p[1]>=b[1]-m&&p[1]<=b[3]+m;
function dPoly(p,P){let c=false,d=Infinity;for(let i=0,j=P.length-1;i<P.length;j=i++){const a=P[i],b=P[j];
  if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c;
  const dx=b[0]-a[0],dy=b[1]-a[1],l=dx*dx+dy*dy,t=l?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)):0;d=Math.min(d,Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy))}
  return c?0:d}
const dForme=(p,g)=>g.type==='cercle'?Math.max(0,dist(p,g.centre)-g.r):dPoly(p,g.points);

// geo : sortie de CPI.pdf.chemins ; ctx = {fichier, textes (de la page), cadres:[[x0,y0,x1,y1]] (tableaux reconnus, zones OCR),
// zone:{x0,y0,x1,y1}|null} → {candidats, ignores, coupe}. Candidat : contrat du détecteur (unite 'pt', source.page) + annot.
function detecterPage(geo,ctx){const n=geo.page,W=Math.min(geo.w,geo.h),z=ctx.zone,eps=0.25,C=[];let ignores=0;
  const dz=p=>!z||p[0]>=z.x0-eps&&p[0]<=z.x1+eps&&p[1]>=z.y0-eps&&p[1]<=z.y1+eps;
  const S=geo.segments.filter(s=>dz(s.a)&&dz(s.b));
  const T=(ctx.textes||[]).filter(t=>!(ctx.cadres||[]).some(b=>dans(b,[t.x,t.y],2)));
  const base=(type,g,centre,dims,id)=>({id:null,type,statut:'a_confirmer',unite:'pt',source:{fichier:ctx.fichier,format:'pdf',calque:null,page:n,id},
    geometrie:Object.assign(g,{espace:'papier',presentation:'Page '+n,page:n}),centre,dims,h:null,manquants:['h','echelle'],remarques:[],annot:{}});
  S.length&&root.CPI.detecteur.rectSegments(S,{eps,tol:0.01}).forEach(r=>{
    if(r.l<MIN){ignores++;return}
    const c=base('rect',{type:'polyligne',ferme:true,points:r.pts},r.centre,{L:r.L,l:r.l,angle:r.angle},r.ids.join('+'));
    c.cas={accole:r.accole,te:r.te,int:r.int,diag:r.diag};C.push(c)});
  const vus=[];
  geo.contours.forEach(k=>{const o=cercle(k);if(!o||!dz(o.centre))return;if(2*o.r<MIN){ignores++;return}
    if(vus.some(v=>dist(v.centre,o.centre)<=0.5&&Math.abs(v.r-o.r)<=0.5))return;vus.push(o);   // même cercle tracé et rempli
    C.push(Object.assign(base('circ',{type:'cercle',centre:o.centre,r:o.r},o.centre,{D:2*o.r},k.id),{cas:{}}))});
  // classement : ce qui ne peut pas être une réservation est écarté avec sa raison ; le reste est proposé, doutes notés
  C.forEach(c=>{const g=c.geometrie,P=g.type==='cercle'?[[g.centre[0]-g.r,g.centre[1]-g.r],[g.centre[0]+g.r,g.centre[1]+g.r]]:g.points,
      bx=emprise(P),L=c.type==='circ'?c.dims.D:c.dims.L,x=c.cas;
    c.bbox=bx;const nT=T.filter(t=>dForme([t.x,t.y],g)===0).length,np=m=>{c.statut='non_pris_en_charge';c.remarques.push(m)};
    if(z&&!(bx[0]>=z.x0-eps&&bx[1]>=z.y0-eps&&bx[2]<=z.x1+eps&&bx[3]<=z.y1+eps))np('dépasse la zone choisie');
    else if((ctx.cadres||[]).some(b=>dans(b,c.centre,2)))np('dans un tableau (nomenclature, aciers, indices…)');
    else if(L>=0.6*W||c.type==='rect'&&(bx[2]-bx[0]>=0.6*geo.w||bx[3]-bx[1]>=0.6*geo.h))np('cadre de feuille ou de vue');
    else if(x.te)np('contour subdivisé par d\'autres traits (tableau, cartouche ou légende)');
    else if(x.accole>=3)np('cellule d\'un quadrillage (sommets partagés avec d\'autres traits)');
    else if(nT>=3)np(nT+' textes à l\'intérieur (cartouche, légende ou tableau)');
    else if(L>=0.4*W)np('très grand contour (ouvrage, local ou vue) : pas une réservation');
    else if(x.int>30)np('contient un dessin (cadre de détail, de vue ou de légende, texte dessiné en traits)');
    else{if(x.accole)c.remarques.push('sommet(s) raccordé(s) à d\'autres traits : contour accolé à un mur ou à une autre forme ?');
      if(L>=0.25*W)c.remarques.push('grand contour : pièce, local ou élément architectural ?');
      if(x.int>4)c.remarques.push('traits à l\'intérieur (hachures, symbole ?)');
      if(x.diag)c.remarques.push('diagonales dessinées (réservation traversante probable)')}});
  // textes voisins : chaque repère ou cote écrite va au contour proposé le plus proche (à moins de 4 hauteurs de texte)
  const OK=C.filter(c=>c.statut==='a_confirmer'),cotes=root.CPI.nomenclatures&&root.CPI.nomenclatures.cotes;
  T.forEach(t=>{const s0=t.texte.trim(),m=s0.match(/^([A-Z]{1,4}[ .\-]?\d{1,4}[A-Z]?)\s*[:\-–]?\s+(\S.*)$/i);   // « R12 650x800 » : repère puis cotes
    (m?[m[1],m[2]]:[s0]).forEach(s=>{const q=cotes?cotes(s,null):{etat:'illisible'},k=REP.test(s)&&!/^\d+$/.test(s)?'repere':q.etat==='rect'||q.etat==='circ'?'cotes':null;if(!k)return;
      let best=null,bd=4*t.h;OK.forEach(c=>{const d=dForme([t.x,t.y],c.geometrie);if(d<=bd){bd=d;best=c}});
      if(best&&(!best.annot[k]||bd<best.annot[k].d))best.annot[k]=Object.assign({texte:s,id:t.id,d:bd},k==='cotes'?q:{})})});
  // ordre de lecture : de haut en bas, de gauche à droite ; identifiant stable dans la page
  C.sort((a,b)=>b.centre[1]-a.centre[1]||a.centre[0]-b.centre[0]).forEach((c,i)=>{c.id='P'+n+'-'+(i+1);delete c.cas});
  return{candidats:C,ignores,coupe:!!geo.coupe}}

// Textes dessinés en traits (export de DAO qui vectorise ses polices) : petits sous-chemins de la page (CPI.pdf.chemins, petits)
// regroupés en lignes de texte (lettres d'un même mot ou d'une même ligne, écart ≤ 1,2 hauteur : le « 1 » sans empattement des polices de DAO est très espacé, même bande verticale).
// o = {cadres:[[x0,y0,x1,y1]] (tableaux : exclus)} → [{x0,y0,x1,y1,h,n}] ; écarte les groupes trop hauts, trop longs ou trop
// fins (hachures, quadrillages, traits) : seuls des repères et de courtes annotations horizontales restent, à lire par OCR
const BT_H=[2.5,30],BT_W=200;   // pt : hauteur de lettre admise, longueur maximale d'une ligne de texte
function blocsTexte(geo,o){o=o||{};const B=geo.petits||[],N=B.length>>2,par=new Int32Array(N),CS=10,G=new Map();
  for(let i=0;i<N;i++)par[i]=i;const f=i=>{while(par[i]!==i)i=par[i]=par[par[i]];return i};
  for(let i=0;i<N;i++){const x0=B[4*i],y0=B[4*i+1],x1=B[4*i+2],y1=B[4*i+3],hi=Math.max(y1-y0,1);if(x1-x0<0.2&&y1-y0<0.2)continue;   // points
    const m=1.2*hi,c0=Math.floor((x0-m)/CS),c1=Math.floor((x1+m)/CS),r0=Math.floor(y0/CS),r1=Math.floor(y1/CS);
    for(let c=c0;c<=c1;c++)for(let r=r0;r<=r1;r++){const k=c*1e6+r,L=G.get(k);
      if(L){for(const j of L){const h=Math.max(hi,B[4*j+3]-B[4*j+1],1),gx=Math.max(B[4*j]-x1,x0-B[4*j+2]),gy=Math.max(B[4*j+1]-y1,y0-B[4*j+3]);
        if(gx<=1.2*h&&gy<=0.12*h){const a=f(i),b=f(j);if(a!==b)par[a]=b}}L.push(i)}else G.set(k,[i])}}
  const R=new Map();for(let i=0;i<N;i++){const x0=B[4*i],y0=B[4*i+1],x1=B[4*i+2],y1=B[4*i+3];if(x1-x0<0.2&&y1-y0<0.2)continue;
    const r=f(i),b=R.get(r);if(b){b.x0=Math.min(b.x0,x0);b.y0=Math.min(b.y0,y0);b.x1=Math.max(b.x1,x1);b.y1=Math.max(b.y1,y1);b.n++}else R.set(r,{x0,y0,x1,y1,n:1})}
  const cad=o.cadres||[],out=[];
  R.forEach(b=>{const h=b.y1-b.y0,w=b.x1-b.x0;b.h=h;
    if(b.n<2||h<BT_H[0]||h>BT_H[1]||w>BT_W||w>12*h||w<0.5*h)return;
    if(cad.some(c=>dans(c,[(b.x0+b.x1)/2,(b.y0+b.y1)/2],0)))return;out.push(b)});
  return out}

// Lignes de rappel d'un texte : traits droits (≥ 2 hauteurs de texte) partant à moins d'une hauteur du texte ; l'autre bout est
// suivi sur un 2e trait s'il s'y raccorde (rappel coudé). → pointes [[x,y]] (là où le rappel désigne quelque chose)
function rappels(geo,t,idx){const h=Math.max(t.h||2,1),bx=[t.x-(t.w||h*2)/2-h,t.y-h,t.x+(t.w||h*2)/2+h,t.y+h],W=Math.min(geo.w,geo.h),out=[];
  const I=idx||index(geo),pres=(p,r)=>I.pres(p,r),lg=s=>Math.hypot(s.b[0]-s.a[0],s.b[1]-s.a[1]);
  const S=I.dans(bx).filter(s=>{const l=lg(s);return l>=2*h&&l<=0.3*W});
  S.forEach(s=>{const ia=dans(bx,s.a,0),ib=dans(bx,s.b,0);if(ia===ib)return;let q=ia?s.b:s.a;
    const T=pres(q,0.3*h).filter(u=>u!==s&&lg(u)>=h);   // coude : un seul trait raccordé, suivi
    if(T.length===1){const u=T[0];q=dist(u.a,q)<dist(u.b,q)?u.b:u.a}
    out.push(q.slice())});
  return out}
// Index des segments par case (une fois par page)
function index(geo){const CS=20,G=new Map(),S=geo.segments,k=(c,r)=>c*1e6+r;
  S.forEach(s=>{const c0=Math.floor(Math.min(s.a[0],s.b[0])/CS),c1=Math.floor(Math.max(s.a[0],s.b[0])/CS),r0=Math.floor(Math.min(s.a[1],s.b[1])/CS),r1=Math.floor(Math.max(s.a[1],s.b[1])/CS);
    if((c1-c0+1)*(r1-r0+1)>400){[s.a,s.b].forEach(p=>{const q=k(Math.floor(p[0]/CS),Math.floor(p[1]/CS));(G.get(q)||G.set(q,[]).get(q)).push(s)});return}   // long trait : rangé par ses bouts
    for(let c=c0;c<=c1;c++)for(let r=r0;r<=r1;r++){const q=k(c,r);(G.get(q)||G.set(q,[]).get(q)).push(s)}});
  const pris=b=>{const R=new Set();for(let c=Math.floor(b[0]/CS);c<=Math.floor(b[2]/CS);c++)for(let r=Math.floor(b[1]/CS);r<=Math.floor(b[3]/CS);r++)(G.get(k(c,r))||[]).forEach(s=>R.add(s));return[...R]};
  return{dans:b=>pris(b).filter(s=>dans(b,s.a,0)||dans(b,s.b,0)),pres:(p,r)=>pris([p[0]-r,p[1]-r,p[0]+r,p[1]+r]).filter(s=>dist(s.a,p)<=r||dist(s.b,p)<=r)}}

root.CPI=Object.assign(root.CPI||{},{geometrie:{detecterPage,cercle,blocsTexte,rappels,index}});
})(typeof globalThis!=='undefined'?globalThis:this);
