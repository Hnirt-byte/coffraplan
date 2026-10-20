// CoffraPlan — module d'import de plans : vues techniques d'une page PDF (phase 5). Une planche réunit plusieurs vues (plan,
// coupe, élévation, détail, ferraillage supérieur / inférieur) : un repère et un contour ne se rapprochent qu'à l'intérieur d'une
// même vue, et une réservation dessinée dans plusieurs vues reste UNE réservation (quantité du tableau = référence).
// Vues : titres (textes nettement plus hauts que la médiane de la page, avec un mot-clé : vue, coupe, élévation, détail,
// ferraillage, renfort, plan…), puis région de chaque titre = dessins (composantes de tracés sur une grille d'occupation) dont
// il est le titre le plus proche ; deux titres pour un même dessin : partagé entre eux. Dessin sans titre à portée : vue « autre ». Tout est déterministe ; aucun texte ni aucune cote n'est inventé.
// Indépendant de l'interface et du moteur. Charger après nomenclatures.js et rapprochement.js.
(function(root){'use strict';
const sansAcc=s=>String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'');
const DV_GAP=8,DV_MIN=30;   // cases : écart titre ↔ dessin admis (au moins, voir GMAX) ; dessin sans titre retenu comme vue à partir de 30 cases
const TYPES={plan:'plan',coupe:'coupe',elevation:'élévation',detail:'détail',ferraillage:'ferraillage',ferraillage_superieur:'ferraillage supérieur',ferraillage_inferieur:'ferraillage inférieur',autre:'autre'};
const CLES=['ferraillage','renfort','armatures','elevation','facade','detail','coupe','dessus','plan','vue','partie'];
const PARTIES=['dalle','radier','voile','poutre','puisard','longrine','semelle','plancher','acrotere','escalier','fosse','regard','cuve','mur'];
// distance d'édition bornée (mots lus par OCR : « FERRKAILTAGE »)
function lev(a,b){const m=a.length,n=b.length;if(Math.abs(m-n)>2)return 9;let p=Array.from({length:n+1},(x,j)=>j);
  for(let i=1;i<=m;i++){const q=[i];for(let j=1;j<=n;j++)q[j]=Math.min(p[j]+1,q[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1));p=q}return p[n]}
// mots-clés d'un titre : exacts, ou à 2 erreurs près pour les mots-clés d'au moins 8 lettres (ferraillage, élévation…) → {K, approx, W}
// « plan » : premier mot ou « vue en plan » (pas « n° du plan » d'un cartouche) ; « partie » : avec supérieure / inférieure
function motsCles(s){const W=sansAcc(s).toLowerCase().split(/[^a-z]+/).filter(Boolean),K=new Set();let approx=false;
  W.forEach((w,i)=>CLES.forEach(k=>{let ok=w===k||w===k+'s';if(!ok&&k.length>=8&&w.length>=6&&lev(w,k)<=2){ok=true;approx=true}if(!ok)return;
    if(k==='plan'&&!(i===0||W[i-1]==='en'))return;if(k==='dessus'&&!W.includes('vue'))return;if(k==='partie'&&!W.some(x=>/^(sup|inf)/.test(x)))return;K.add(k)}));
  return{K,approx,W}}
function typeVue(K,W){const sup=W.some(w=>/^sup/.test(w)),inf=W.some(w=>/^inf/.test(w));
  if(K.has('ferraillage')||K.has('renfort')||K.has('armatures')||K.has('partie')&&(sup||inf))return sup?'ferraillage_superieur':inf?'ferraillage_inferieur':'ferraillage';
  if(K.has('coupe'))return'coupe';if(K.has('elevation')||K.has('facade'))return'elevation';if(K.has('detail'))return'detail';
  if(K.has('plan')||K.has('dessus'))return'plan';return'autre'}
const partieDe=W=>PARTIES.find(p=>W.includes(p)||W.includes(p+'s'))||null;
const med=a=>{const s=a.slice().sort((x,y)=>x-y);return s.length?s[s.length>>1]:0};
const boite=t=>{const w=t.w||String(t.texte).length*0.7*t.h;return[t.x-w/2,t.y-t.h/2,t.x+w/2,t.y+t.h/2]};

// Titres de vue d'une page : grands textes réunis en lignes puis en blocs de 2 lignes au plus, avec un mot-clé
function titres(textes){const T=textes.filter(t=>t.h>0&&String(t.texte).trim()),hm=med(T.map(t=>t.h)),
    G=T.filter(t=>t.h>=1.8*hm&&!t.rot&&(!t.ocr||t.ocr.conf>=60||motsCles(t.texte).K.size)&&/\p{L}.*\p{L}|\d/u.test(t.texte));   // mot lu à moins de 60 % : bruit, sauf mot-clé reconnu
  const par=G.map((t,i)=>i),f=i=>par[i]===i?i:(par[i]=f(par[i]));
  G.forEach((a,i)=>G.forEach((b,j)=>{if(j<=i||Math.max(a.h,b.h)>1.3*Math.min(a.h,b.h))return;const A=boite(a),B=boite(b),h=Math.max(a.h,b.h);
    const ligne=Math.abs(a.y-b.y)<=0.4*h&&Math.max(B[0]-A[2],A[0]-B[2])<=2.5*h,
      dessous=Math.abs(a.y-b.y)>0.4*h&&Math.abs(a.y-b.y)<=2.6*h&&(Math.min(A[2],B[2])-Math.max(A[0],B[0])>-h||Math.abs(a.x-b.x)<=3*h);
    if(ligne||dessous)par[f(i)]=f(j)}));
  const R=new Map();G.forEach((t,i)=>{const r=f(i);(R.get(r)||R.set(r,[]).get(r)).push(t)});
  const out=[];R.forEach(L=>{L.sort((a,b)=>b.y-a.y||a.x-b.x);
    // lignes de haut en bas, mots de gauche à droite
    const lignes=[];L.forEach(t=>{const l=lignes.find(l=>Math.abs(l[0].y-t.y)<=0.4*t.h);l?l.push(t):lignes.push([t])});
    const texte=lignes.map(l=>l.sort((a,b)=>a.x-b.x).map(t=>t.texte).join(' ')).join(' ').replace(/\s+/g,' ').trim(),m=motsCles(texte);
    if(!m.K.size||m.K.size===1&&m.K.has('vue')&&m.W.length<2)return;
    const bx=L.map(boite),b=[Math.min(...bx.map(x=>x[0])),Math.min(...bx.map(x=>x[1])),Math.max(...bx.map(x=>x[2])),Math.max(...bx.map(x=>x[3]))];
    const cf=Math.min(...L.map(t=>t.ocr?t.ocr.conf:100));
    out.push({texte,b,h:Math.max(...L.map(t=>t.h)),ids:L.map(t=>t.id),type:typeVue(m.K,m.W),partie:partieDe(m.W),approx:m.approx,conf:cf,
      sous:m.K.size===1&&m.K.has('partie')})});
  return out}

// geo : CPI.pdf.chemins ; textes : textes de la page (PDF et OCR) ; o = {cadres:[[x0,y0,x1,y1]] (tableaux : ignorés)}
// → {vues:[{id,page,region,titre,type,libelle,partie,echelle,niveau,confiance,motifs}], carte} ; carte : pour situer()
function detecter(geo,textes,o){o=o||{};const n=geo.page,W=geo.w,H=geo.h,C=Math.max(4,0.008*Math.min(W,H)),nx=Math.ceil(W/C)+1,ny=Math.ceil(H/C)+1,N=nx*ny;
  const occ=new Uint8Array(N),cad=o.cadres||[],hors=p=>cad.some(b=>p[0]>=b[0]&&p[0]<=b[2]&&p[1]>=b[1]&&p[1]<=b[3]);
  const cel=(x,y)=>{const i=Math.floor(x/C),j=Math.floor(y/C);return i<0||j<0||i>=nx||j>=ny?-1:j*nx+i};
  const marque=(x,y)=>{if(hors([x,y]))return;const k=cel(x,y);if(k>=0)occ[k]=1};
  const Lmax=0.35*Math.min(W,H);
  (geo.segments||[]).forEach(s=>{const l=Math.hypot(s.b[0]-s.a[0],s.b[1]-s.a[1]);if(l>Lmax)return;const m=Math.max(1,Math.ceil(2*l/C));
    for(let q=0;q<=m;q++)marque(s.a[0]+(s.b[0]-s.a[0])*q/m,s.a[1]+(s.b[1]-s.a[1])*q/m)});
  (geo.contours||[]).forEach(k=>{(k.pts||[]).forEach(p=>marque(p[0],p[1]));(k.courbes||[]).forEach(c=>c.forEach(p=>marque(p[0],p[1])))});
  const B=geo.petits||[];for(let i=0;i<B.length;i+=4)marque((B[i]+B[i+2])/2,(B[i+1]+B[i+3])/2);
  // titres (hors tableaux) ; un sous-titre seul (« Partie supérieure ») prend le titre de ferraillage le plus proche comme parent
  const TT=titres(textes.filter(t=>!hors([t.x,t.y]))),pr=TT.filter(t=>!t.sous&&/^ferraillage/.test(t.type));
  TT.forEach(t=>{if(!t.sous)return;const c=[(t.b[0]+t.b[2])/2,(t.b[1]+t.b[3])/2];let best=null,bd=Infinity;
    pr.forEach(p=>{const d=Math.hypot((p.b[0]+p.b[2])/2-c[0],(p.b[1]+p.b[3])/2-c[1]);if(d<bd){bd=d;best=p}});
    if(best){t.parent=best;best.enfants=(best.enfants||0)+1;t.partie=t.partie||best.partie;t.texte=best.texte+' — '+t.texte}});
  const S=TT.filter(t=>!t.enfants);   // un titre principal découpé en sous-vues ne prend pas de région à lui seul
  // dessins : composantes connexes des cases dessinées (voisines à 2 cases) ; chacune va au titre le plus proche (écart entre
  // emprises, doublé pour un dessin au-dessus de son titre : un titre est le plus souvent au-dessus de sa vue), à moins de GMAX ;
  // une composante choisie comme la plus proche par plusieurs titres (vues reliées par un axe, une cote) est partagée entre eux
  // par propagation depuis chacun ; sans titre à portée : vue « autre » à partir de DV_MIN cases
  const comp=new Int32Array(N).fill(-1),K=[];
  for(let k0=0;k0<N;k0++){if(!occ[k0]||comp[k0]>=0)continue;const P=[k0],id=K.length;comp[k0]=id;
    for(let p=0;p<P.length;p++){const k=P[p],i=k%nx,j=(k-i)/nx;for(let di=-2;di<=2;di++)for(let dj=-2;dj<=2;dj++){const a=i+di,b=j+dj;if(a<0||b<0||a>=nx||b>=ny)continue;const q=b*nx+a;if(occ[q]&&comp[q]<0){comp[q]=id;P.push(q)}}}
    let b=[Infinity,Infinity,-Infinity,-Infinity];P.forEach(k=>{const i=k%nx,j=(k-i)/nx;b=[Math.min(b[0],i*C),Math.min(b[1],j*C),Math.max(b[2],(i+1)*C),Math.max(b[3],(j+1)*C)]});K.push({P,b})}
  const GMAX=Math.max(DV_GAP*C,0.12*Math.min(W,H)),ecart=(t,b)=>{const dx=Math.max(0,b[0]-t.b[2],t.b[0]-b[2]),dy=Math.max(0,b[1]-t.b[3],t.b[1]-b[3]);return Math.hypot(dx,dy)*(b[1]>t.b[3]-1?2:1)};
  const own=new Int16Array(N).fill(-1),choix=K.map(c=>{let best=-1,bd=GMAX;S.forEach((t,v)=>{const d=ecart(t,c.b);if(d<=bd){bd=d;best=v}});return best});
  const prefere=S.map(t=>{let best=-1,bd=GMAX;K.forEach((c,i)=>{if(c.P.length<4)return;const d=ecart(t,c.b);if(d<bd){bd=d;best=i}});return best});
  K.forEach((c,ci)=>{const T=[...new Set(S.map((t,v)=>prefere[v]===ci?v:-1).filter(v=>v>=0).concat(choix[ci]>=0?[choix[ci]]:[]))];
    if(T.length<=1){if(T.length)c.P.forEach(k=>own[k]=T[0]);return}
    // partage : propagation dans la composante depuis la case la plus proche de chaque titre
    const F=[];T.forEach(v=>{const t=S[v],cx=(t.b[0]+t.b[2])/2,cy=(t.b[1]+t.b[3])/2;let bk=-1,bd=Infinity;c.P.forEach(k=>{const i=k%nx,j=(k-i)/nx,d=Math.hypot((i+0.5)*C-cx,(j+0.5)*C-cy);if(d<bd){bd=d;bk=k}});if(own[bk]<0){own[bk]=v;F.push(bk)}});
    for(let p=0;p<F.length;p++){const k=F[p],i=k%nx,j=(k-i)/nx;for(let di=-2;di<=2;di++)for(let dj=-2;dj<=2;dj++){const a=i+di,b=j+dj;if(a<0||b<0||a>=nx||b>=ny)continue;const q=b*nx+a;if(comp[q]===ci&&own[q]<0){own[q]=own[k];F.push(q)}}}});
  const V=S.map(t=>({t,cases:0,b:[Infinity,Infinity,-Infinity,-Infinity]}));
  for(let k=0;k<N;k++){if(own[k]<0)continue;const v=V[own[k]],i=k%nx,j=(k-i)/nx;v.cases++;v.b=[Math.min(v.b[0],i*C),Math.min(v.b[1],j*C),Math.max(v.b[2],(i+1)*C),Math.max(v.b[3],(j+1)*C)]}
  K.forEach(c=>{if(own[c.P[0]]>=0||c.P.length<DV_MIN)return;const id=V.length;V.push({t:null,cases:c.P.length,b:c.b});c.P.forEach(k=>own[k]=id)});
  // vues : région = cases dessinées et titre ; échelle « 1/50 » écrite près du titre ; identifiant dans l'ordre de lecture
  const ech=textes.map(t=>{const m=sansAcc(t.texte).match(/(?:^|[^0-9.,\/])1\s*[\/:]\s*(\d{1,4})(?![0-9.,])/);return m&&+m[1]>1?{t,v:+m[1]}:null}).filter(Boolean);
  const out=V.map((v,k)=>{const t=v.t,b=t?[Math.min(v.b[0],t.b[0]),Math.min(v.b[1],t.b[1]),Math.max(v.b[2],t.b[2]),Math.max(v.b[3],t.b[3])]:v.b;
    if(!(b[2]>b[0]))return null;const motifs=[];let conf=t?(t.conf>=80&&!t.approx?'forte':t.conf>=50?'moyenne':'faible'):'faible';
    if(!t)motifs.push('dessin sans titre reconnu');else{if(t.approx)motifs.push('titre lu avec des erreurs (mot-clé rapproché)');if(t.conf<80)motifs.push(`titre lu par OCR à ${t.conf} %`);
      if(!v.cases){motifs.push('aucun tracé rattaché au titre');conf='faible'}}
    const e=t&&ech.find(x=>x.t.x>=t.b[0]-4*t.h&&x.t.x<=t.b[2]+4*t.h&&x.t.y>=t.b[1]-3*t.h&&x.t.y<=t.b[3]+1.5*t.h);
    const nv=t&&sansAcc(t.texte).match(/\bniv(?:eau)?\.?\s*:?\s*([+\-]?\d+[.,]?\d*|R\s*\+?\s*\d+|r\s*d\s*c|sous[- ]sol)/i);
    return{k,page:n,region:b.map(x=>Math.round(x*100)/100),titre:t?t.texte:null,titreIds:t?t.ids:[],type:t?t.type:'autre',partie:t?t.partie:null,
      echelle:e?{valeur:e.v,texte:e.t.texte}:null,niveau:nv?nv[1].replace(/\s+/g,''):null,confiance:conf,motifs,cases:v.cases}}).filter(Boolean);
  out.sort((a,b)=>b.region[3]-a.region[3]||a.region[0]-b.region[0]).forEach((v,i)=>{v.id='V'+n+'-'+(i+1);v.libelle=TYPES[v.type]});
  const ids=[];out.forEach(v=>ids[v.k]=v.id);out.forEach(v=>delete v.k);
  return{vues:out,carte:{page:n,C,nx,ny,own,ids,regions:out.map(v=>({id:v.id,b:v.region}))}}}

// Vue d'un point de la page (carte de detecter) : case dessinée du point, sinon la plus petite région de vue qui le contient
// (intérieur d'un contour), sinon la vue la plus présente à 2 cases ; null hors de toute vue
function situer(carte,x,y){if(!carte)return null;const{C,nx,ny,own,ids,regions}=carte,i=Math.floor(x/C),j=Math.floor(y/C);
  if(i>=0&&j>=0&&i<nx&&j<ny&&own[j*nx+i]>=0)return ids[own[j*nx+i]]||null;
  const R=(regions||[]).filter(r=>x>=r.b[0]&&x<=r.b[2]&&y>=r.b[1]&&y<=r.b[3]).sort((a,b)=>(a.b[2]-a.b[0])*(a.b[3]-a.b[1])-(b.b[2]-b.b[0])*(b.b[3]-b.b[1]));if(R.length)return R[0].id;
  const n={};for(let di=-2;di<=2;di++)for(let dj=-2;dj<=2;dj++){const a=i+di,b=j+dj;if(a<0||b<0||a>=nx||b>=ny)continue;const o=own[b*nx+a];if(o>=0&&ids[o])n[ids[o]]=(n[ids[o]]||0)+1}
  const K=Object.keys(n).sort((a,b)=>n[b]-n[a]);return K.length?K[0]:null}

// Occurrences physiques d'une ligne : la quantité du tableau est la référence, jamais multipliée par les vues. Vues « physiques »
// (plan, puis ferraillage, puis vue sans titre) : la plus fournie donne les occurrences localisées ; les repères des autres vues
// physiques de même partie, à la même position relative (± 10 % de la vue), sont des représentations de ces occurrences ;
// coupes, élévations, détails : représentations seulement. → {attendue, localisees, representations, restantes, physiques, notes}
const RANG={plan:0,ferraillage_superieur:1,ferraillage_inferieur:1,ferraillage:1,autre:2};
function consolider(L,r,vues){const Vx=new Map(vues.map(v=>[v.id,v])),Q=/^\s*\d+\s*$/.test(String(L.quantite==null?'':L.quantite))?parseInt(L.quantite,10):null;
  const O=(r&&r.occurrences||[]).map((o,j)=>Object.assign({j},o,{v:Vx.get(o.vue)||null})),notes=[];
  // lecture incertaine du repère : comptée seulement dans une vue en plan (ailleurs : représentation)
  const par=new Map();O.forEach(o=>{if(o.v&&o.v.type in RANG&&(o.fiable||o.v.type==='plan'))(par.get(o.v.id)||par.set(o.v.id,[]).get(o.v.id)).push(o)});
  const cand=[...par.entries()].map(([id,X])=>({v:Vx.get(id),X})).sort((a,b)=>RANG[a.v.type]-RANG[b.v.type]||b.X.length-a.X.length||b.X.filter(o=>o.fiable).length-a.X.filter(o=>o.fiable).length);
  const meilleur=cand.length?cand.filter(c=>RANG[c.v.type]===RANG[cand[0].v.type]).sort((a,b)=>b.X.length-a.X.length)[0]:null;
  const rel=(o,v)=>[(o.x-v.region[0])/Math.max(1,v.region[2]-v.region[0]),(o.y-v.region[1])/Math.max(1,v.region[3]-v.region[1])];
  const phys=meilleur?meilleur.X.slice().sort((a,b)=>b.y-a.y||a.x-b.x).map((o,k)=>({n:k+1,vue:meilleur.v.id,page:o.page,x:o.x,y:o.y,occurrence:o.j,representations:[o.j],fiable:o.fiable})):[];
  O.forEach(o=>{if(phys.some(p=>p.occurrence===o.j))return;o.role='representation';
    if(!o.v){notes.push(`localisation p. ${o.page} hors de toute vue reconnue : représentation, non comptée`);return}
    if(meilleur&&o.v.type in RANG&&o.v.id!==meilleur.v.id&&(o.v.partie||null)===(meilleur.v.partie||null)){const q=rel(o,o.v);let best=null,bd=0.1;
      phys.forEach(p=>{const s=rel(p,meilleur.v),d=Math.max(Math.abs(s[0]-q[0]),Math.abs(s[1]-q[1]));if(d<=bd){bd=d;best=p}});if(best)best.representations.push(o.j)}});
  O.forEach(o=>{if(!o.role)o.role='physique'});
  const loc=phys.length;
  if(meilleur&&cand.length>1)notes.push(`${O.length} représentation(s) dans ${new Set(O.map(o=>o.vue||'?')).size} vue(s) ; occurrences comptées dans la vue ${meilleur.v.id} (${TYPES[meilleur.v.type]}${meilleur.v.partie?' '+meilleur.v.partie:''}) seulement`);
  if(!meilleur&&O.length)notes.push('repère vu seulement en coupe, élévation, détail, hors vue ou en lecture incertaine hors d\'une vue en plan : aucune occurrence physique comptée');
  if(meilleur&&meilleur.v.type==='autre')notes.push('occurrences comptées dans une vue sans titre reconnu : à vérifier');
  if(Q!=null&&loc>Q)notes.push(`${loc} occurrences localisées pour une quantité de ${Q} au tableau : vues superposées ou repère réutilisé ? (la quantité du tableau est gardée)`);
  return{attendue:Q,localisees:loc,representations:O.length,restantes:Q==null?null:Math.max(0,Q-loc),depasse:Q!=null&&loc>Q,
    physiques:phys,roles:O.map(o=>({occurrence:o.j,vue:o.vue||null,type:o.v?o.v.type:null,role:o.role})),notes}}

// Contour du dessin hors nomenclature : à examiner (repère, cote écrite, diagonales), représentation d'une ligne (repère du
// tableau voisin, mais contour non retenu pour elle : autre vue, plusieurs contours possibles) ou parasite probable (cadre de
// ferraillage, forme isolée sans indice) ; jamais supprimé. cles : repères du tableau (cleRep) → {niveau, raison}
function classer(c,v,cles){const A=c.annot||{},I=[],N=root.CPI.nomenclatures;
  const dv0=v?`vue ${v.id}${v.titre?' « '+v.titre+' »':' (sans titre)'}`:'hors des vues reconnues';
  if(A.repere&&cles&&cles.has(N.cleRep(A.repere.texte)))return{niveau:'representation',raison:`repère « ${A.repere.texte} » de la nomenclature : représentation probable de cette ligne (non comptée) · ${dv0}`};
  if(A.repere)I.push(`repère « ${A.repere.texte} » voisin`);if(A.cotes)I.push(`cote écrite « ${A.cotes.texte} » voisine`);
  if((c.remarques||[]).some(m=>/diagonales/.test(m)))I.push('diagonales dessinées (réservation traversante ?)');
  const dv=v?`vue ${v.id}${v.titre?' « '+v.titre+' »':' (sans titre)'}`:'hors des vues reconnues';
  if(I.length)return{niveau:'examiner',raison:I.join(' ; ')+' · '+dv};
  if(v&&/^ferraillage/.test(v.type))return{niveau:'parasite',raison:`parasite probable : dans une vue de ferraillage (cadre, armature), sans repère ni cote · ${dv}`};
  if(v&&/^(coupe|elevation|detail)$/.test(v.type))return{niveau:'parasite',raison:`parasite probable : forme de ${TYPES[v.type]}, sans repère ni cote · ${dv}`};
  return{niveau:'parasite',raison:`parasite probable : aucun repère, aucune cote, aucune diagonale · ${dv}`}}

root.CPI=Object.assign(root.CPI||{},{vues:{detecter,situer,consolider,classer,titres,TYPES}});
})(typeof globalThis!=='undefined'?globalThis:this);
