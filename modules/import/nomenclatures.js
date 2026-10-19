// CoffraPlan — module d'import de plans : nomenclatures de réservations (tableaux de textes d'un DXF).
// Reconstruit les tableaux dessinés en textes (TEXT, MTEXT, attributs, blocs ; ACAD_TABLE par son bloc de rendu) dans
// l'espace Objet et dans chaque présentation, à partir des textes et traits relevés par dxf.js. La nature d'un tableau
// (réservations, aciers, autre) se décide sur son en-tête et son titre, jamais sur ses lignes. Un tableau de réservations
// garde TOUTES ses lignes : aucun filtre (lot, fournisseur, type, matériau, nature…) ; le choix appartient à l'utilisateur.
// Cotes lues sans rien inventer : SO, à définir, vide → manquant ; DN du réseau ≠ ouverture ; niveau ≠ hauteur à coffrer.
// Rapprochement avec les géométries du détecteur (états trouvee / probable / multiple / absente), jamais tranché à la place
// de l'utilisateur ; coordonnées d'une présentation jamais comparées à celles de l'espace Objet.
// Indépendant de l'interface et du moteur.
(function(root){'use strict';
const sansAcc=s=>String(s==null?'':s).normalize('NFD').replace(/[̀-ͯ]/g,'');
const norm=s=>sansAcc(s).toLowerCase().replace(/[⌀∅]/g,'ø').replace(/\s+/g,' ').trim();
const mot=a=>new RegExp('(?<![a-z0-9])(?:'+a+')(?![a-z0-9])');
const med=A=>{const B=A.filter(Number.isFinite).sort((a,b)=>a-b);return B.length?B[B.length>>1]:0};
const MM={mm:1,cm:10,m:1000};

// Nature d'une colonne d'après son titre : premier motif reconnu (« Réservation » seul = colonne des repères, en dernier)
const COLS=[
  ['niveau',mot("niv(eau|\\.)?|alti(metrie|tude)?|ngf|fil d'?eau|arase|cote (d'?axe|ngf|fil)|hauteur ?(\\/|par rapport|d'?axe|sous)|h ?\\/ ?[a-z]+")],
  ['angle',mot('angles?|orientation|azimut|gisement')],
  ['ouverture',mot("ouvertures?|tremies?|dim(ension)?s?\\.?|sections?|percements?|carottages?|passages?|encombrement|cotes|taille|l ?[x×*] ?[hl]|b ?[x×*] ?h")],
  ['reseau',mot("dn|reseaux?|canalisations?|tuyaux?|conduits?|gaines?|fluides?")],
  ['diametre',/(?<![a-z0-9])diam(etre|\.)?(?![a-z0-9])|ø/],
  ['largeur',mot('larg(eur|\\.)?')],
  ['hauteur',mot('haut(eur|\\.)?')],
  ['quantite',mot('qte|quantites?|nombre|nbre?|qt')],
  ['type',mot('types?|elements?|elts?|supports?|parois?|ouvrages?|localisation|emplacement|zone')],
  ['description',mot('designation|description|libelle|objet|nature|fonctions?|usage|destination|intitule')],
  ['observations',mot('observations?|remarques?|commentaires?|notes?|obs\\.?')],
  ['lot',mot("lots?|entreprises?|corps d'?etat|fournisseurs?|intervenants?|emetteur|responsable|societe|poseur")],
  ['repere',mot("rep(ere|\\.)?|ref(erence|\\.)?|n°|no\\.?|num(ero|\\.)?|marque|identifiant|id|code|reservations?|resas?")]];
const kinds=n=>COLS.filter(c=>c[1].test(n)).map(c=>c[0]);
const LIB={repere:'repère',description:'désignation',type:'type / élément',ouverture:'ouverture',reseau:'réseau',diametre:'diamètre',
  niveau:'niveau (position)',angle:'angle (position)',largeur:'largeur',hauteur:'hauteur',quantite:'quantité',observations:'observations',lot:'lot / entreprise',autre:'non reconnue'};
// Nature du tableau : en-tête + titre seulement (un tableau d'aciers a aussi des repères et des diamètres)
const RESA=mot('reservations?|resas?|tremies?|fourreaux?|ouvertures?|percements?|carottages?|traversees?|incorporations?|passages?|rebouchages?');
const ACIER=mot('aciers?|ha\\d*|ferraillages?|armatures?|nuances?|faconnages?|barres?|poids|masses?|kg|longueurs? developpees?|crochets?|epingles?|etriers?|cadres?|enrobages?|espacements?|fe ?e?500|b ?500|treillis');
const AUTRE=mot("indices?|ind\\.?|revisions?|modifications?|dessine|verifie|approuve|folios?|liste des plans|documents?|bordereau|planning");
const POIDS={ouverture:2,niveau:1,angle:1,reseau:1,diametre:1};
function nature(titre,cols){let R=0,A=0,O=0;
  [titre].concat(cols.map(c=>c.titre)).forEach(t=>{const n=norm(t);if(RESA.test(n))R+=3;if(ACIER.test(n))A+=3;if(AUTRE.test(n))O+=3});
  cols.forEach(c=>{R+=POIDS[c.cle]||0});
  return R>=3&&R>A&&R>O?'reservations':A>=3&&A>=R?'aciers':'autre'}
const UNIT=/\(\s*(mm|cm|m)\s*\)|(?<![a-z])(?:en|unite :?) (mm|cm|m)(?![a-z])/;
const SOUS=/\(\s*(mm|cm|m)\s*\)|^\(.*\)$|(?<![a-z])[lb] ?[x×*] ?[hl](?![a-z])/;   // 2e ligne d'un titre de colonne

// Valeur d'une cellule de cotes → {etat:'rect',a,b,c?,unite} | {etat:'circ',D,unite} | {etat:'dn',D} | {etat:'seul',v,unite}
// | {etat:'manquant'|'vide'|'illisible'}. u0 = unité de la colonne ; une unité écrite dans la cellule l'emporte.
// saisie : texte tapé dans la fenêtre (« d250 » ou « o250 » acceptés pour Ø, le Ø étant rare sur un clavier).
const VIDE=/^(s\.?o\.?|sans objet|a definir|adf|a voir|nc|n\.c\.?|non communique|neant|nr|\/+|-+|—|–|\?+|x)$/;
function cotes(s,u0,saisie){
  const t0=String(s==null?'':s).trim(),t=norm(t0).replace(/,/g,'.');
  if(!t)return{etat:'vide'};
  if(VIDE.test(t))return{etat:'manquant',texte:t0};
  const mu=t.match(/\d\s*(mm|cm|m)(?![a-z0-9])/),u=mu?mu[1]:u0||null,N='(\\d+(?:\\.\\d+)?)',U='\\s*(?:mm|cm|m)?\\s*';
  let m=t.match(new RegExp(N+U+'[x×*]\\s*'+N+'(?:'+U+'[x×*]\\s*'+N+')?'));
  if(m)return Object.assign({etat:'rect',a:+m[1],b:+m[2],unite:u},m[3]?{c:+m[3]}:{});
  if((m=t.match(new RegExp('(?:ø|diam\\.?|diametre|phi'+(saisie?'|d|o':'')+')\\s*'+N))))return{etat:'circ',D:+m[1],unite:u};
  if((m=t.match(new RegExp('(?<![a-z])dn\\s*'+N))))return{etat:'dn',D:+m[1]};
  if((m=t.match(new RegExp('^'+N+'\\s*(mm|cm|m)?$'))))return{etat:'seul',v:+m[1],unite:u};
  return{etat:'illisible',texte:t0};
}

// Cotes d'une ligne : la colonne « ouverture » d'abord ; un DN ou une cote seule ne donnent pas de cote certaine
function dimsLigne(cols,cells,av){
  const get=k=>cols.map((c,j)=>c.cle===k&&cells[j]?{c,v:cells[j]}:null).filter(Boolean),q=v=>`« ${v.replace(/\n/g,' ')} »`;
  const dd=(r,c,v)=>r.etat==='rect'?{type:'rect',a:r.a,b:r.b,unite:r.unite,texte:v,colonne:c.titre}:{type:'circ',D:r.D,unite:r.unite,texte:v,colonne:c.titre};
  const O=get('ouverture');
  if(O.length){const {c,v}=O[0],r=cotes(v,c.unite);
    if(r.etat==='rect'){if(r.c!=null)av.push(`ouverture ${q(v)} : 3e cote ignorée`);return dd(r,c,v)}
    if(r.etat==='circ')return dd(r,c,v);
    av.push(`ouverture ${q(v)} : `+(r.etat==='dn'?'DN du réseau, diamètre de la réservation à saisir':r.etat==='seul'?'une seule cote, forme et cotes à préciser':r.etat==='manquant'?'non renseignée':'cotes non lues'));
    return null}
  const Dm=get('diametre');
  if(Dm.length){const {c,v}=Dm[0],r=cotes(v,c.unite);
    if(r.etat==='rect'||r.etat==='circ'||r.etat==='seul'){av.push(`cote prise dans la colonne « ${c.titre} » : à confirmer comme cote de la réservation`);return dd(r.etat==='seul'?{etat:'circ',D:r.v,unite:r.unite}:r,c,v)}
    av.push(`colonne « ${c.titre} » ${q(v)} : `+(r.etat==='dn'?'DN du réseau, diamètre de la réservation à saisir':r.etat==='manquant'?'non renseignée':'cotes non lues'));return null}
  const La=get('largeur'),Ha=get('hauteur');
  if(La.length&&Ha.length){const a=cotes(La[0].v,La[0].c.unite),b=cotes(Ha[0].v,Ha[0].c.unite);
    if(a.etat==='seul'&&b.etat==='seul'){av.push('cotes reconstituées des colonnes Largeur et Hauteur : à confirmer');return{type:'rect',a:a.v,b:b.v,unite:a.unite===b.unite?a.unite:null,texte:La[0].v+' × '+Ha[0].v,colonne:La[0].c.titre+' / '+Ha[0].c.titre}}}
  const R=get('reseau');
  av.push(R.length?`ouverture non donnée : le réseau ${q(R[0].v)} ne donne pas la cote de la réservation`:'cotes de l\'ouverture absentes du tableau');
  return null;
}

// Cellule : textes triés de haut en bas puis de gauche à droite ; même ligne → espace, lignes → retour à la ligne
function cellule(T){const L=[];T.slice().sort((a,b)=>b.y-a.y||a.x-b.x).forEach(t=>{const l=L[L.length-1];if(l&&Math.abs(l.y-t.y)<=0.5*Math.max(l.h,t.h))l.T.push(t);else L.push({y:t.y,h:t.h,T:[t]})});
  return L.map(l=>l.T.sort((a,b)=>a.x-b.x).map(t=>t.texte.trim()).join(' ')).join('\n').trim()}

// Traits horizontaux (y) et verticaux (x) d'un groupe, fusionnés à tol près
function axes(S,tol){const H=[],V=[];
  S.forEach(s=>{const dx=s.b[0]-s.a[0],dy=s.b[1]-s.a[1],l=Math.hypot(dx,dy);if(!(l>0))return;
    if(Math.abs(dy)<=0.01*l)H.push({y:(s.a[1]+s.b[1])/2,x0:Math.min(s.a[0],s.b[0]),x1:Math.max(s.a[0],s.b[0])});
    else if(Math.abs(dx)<=0.01*l)V.push({x:(s.a[0]+s.b[0])/2,y0:Math.min(s.a[1],s.b[1]),y1:Math.max(s.a[1],s.b[1])})});
  return{H,V}}
const fusion=(A,tol)=>{const R=[];A.slice().sort((a,b)=>a-b).forEach(v=>{if(!R.length||v-R[R.length-1]>tol)R.push(v)});return R};
const couvre=(H,x0,x1)=>H.reduce((s,h)=>s+Math.max(0,Math.min(h.x1,x1)-Math.max(h.x0,x0)),0);
// étendue du trait horizontal (segments bout à bout fusionnés) à la hauteur y qui recouvre [x0, x1]
function etendue(H,y,x0,x1,hm){const S=H.filter(h=>Math.abs(h.y-y)<=0.2*hm).sort((a,b)=>a.x0-b.x0),R=[];
  S.forEach(h=>{const r=R[R.length-1];if(r&&h.x0<=r[1]+0.3*hm)r[1]=Math.max(r[1],h.x1);else R.push([h.x0,h.x1])});
  return R.find(r=>r[0]<=x1&&r[1]>=x0)||null}

// Un tableau à partir d'une ligne d'en-tête hg (textes) ; renvoie null si aucune colonne lisible
function construire(g,hg,used,K){
  const hm=med(hg.map(t=>t.h)),yH=hg.reduce((s,t)=>s+t.y,0)/hg.length,xL=Math.min(...hg.map(t=>t.x0)),xR=Math.max(...hg.map(t=>t.x1));
  const libre=t=>!used.has(t.i);
  // bande d'en-tête : entre deux traits horizontaux de la grille, sinon textes à mot-clé ou sous-titres « (mm) » juste au-dessus / au-dessous
  const Hy=fusion(g.A.H.filter(h=>couvre([h],xL,xR)>=0.5*(xR-xL)).map(h=>h.y),0.2*hm),   // croissant
    dessus=Hy.find(y=>y>yH+0.3*hm),dessous=Hy.filter(y=>y<yH-0.3*hm).pop();
  let band,grL=false;
  if(dessus!==undefined&&dessous!==undefined&&dessus-dessous<=8*hm){band=[dessous,dessus];grL=true}
  else{band=[Math.min(...hg.map(t=>t.y))-0.6*hm,Math.max(...hg.map(t=>t.y))+0.6*hm];
    for(let k=0;k<3;k++)g.T.forEach(t=>{if(!libre(t)||t.x<xL-2*hm||t.x>xR+2*hm||t.y>=band[0]&&t.y<=band[1])return;
      const d=t.y<band[0]?band[0]-t.y:t.y-band[1];if(d<=1.3*hm&&(K[t.i].length||SOUS.test(t.n))){band[0]=Math.min(band[0],t.y-0.6*t.h);band[1]=Math.max(band[1],t.y+0.6*t.h)}})}
  // traits verticaux de la grille : ils traversent l'en-tête, entre les extrémités du trait qui la borde (grille) ou en
  // partant de son bord (un cadre de feuille ou le tableau voisin ne comptent pas)
  const yM=(band[0]+band[1])/2,ext=grL?etendue(g.A.H,dessus,xL,xR,hm):null,
    garde=v=>ext?v.x>=ext[0]-0.3*hm&&v.x<=ext[1]+0.3*hm:v.x>=xL-15*hm&&v.x<=xR+15*hm&&(Math.abs(v.y1-band[1])<=0.5*hm||Math.abs(v.y0-band[0])<=0.5*hm);
  let xs=fusion(g.A.V.filter(v=>v.y0-0.2*hm<=yM&&yM<=v.y1+0.2*hm&&garde(v)).map(v=>v.x),0.3*hm);
  if(ext&&xs.length){if(xs[0]>ext[0]+0.3*hm)xs.unshift(ext[0]);if(xs[xs.length-1]<ext[1]-0.3*hm)xs.push(ext[1])}
  const grC=xs.length>=2;
  const BT0=g.T.filter(t=>libre(t)&&t.y>=band[0]&&t.y<=band[1]&&t.x>=(grC?Math.min(xs[0],xL-2*hm):xL-2*hm)&&t.x<=(grC?Math.max(xs[xs.length-1],xR+2*hm):xR+2*hm));
  const Cl=[];BT0.slice().sort((a,b)=>a.x0-b.x0).forEach(t=>{const c=Cl[Cl.length-1];if(c&&t.x0<=c.x1+0.3*hm)c.x1=Math.max(c.x1,t.x1);else Cl.push({x0:t.x0,x1:t.x1})});
  const pad=Math.max(4*hm,med(Cl.map(c=>c.x1-c.x0))),P0=ext&&grC?xs[0]:Cl[0].x0-pad,PN=ext&&grC?xs[xs.length-1]:Cl[Cl.length-1].x1+pad;
  const enTete=T=>{const k=new Set();let c=0;T.forEach(t=>{if(K[t.i].length){c++;k.add(K[t.i][0])}});return c>=3&&k.size>=2};
  // lignes de texte d'un côté de l'en-tête (dir -1 : dessous, +1 : dessus) : bandes de la grille, sinon regroupement par hauteur
  function cote(dir){
    const bord=dir<0?band[0]:band[1],loin=t=>dir<0?bord-t.y:t.y-bord;
    const D=g.T.filter(t=>libre(t)&&!BT0.includes(t)&&t.x>=P0&&t.x<=PN&&loin(t)>0).sort((a,b)=>loin(a)-loin(b));
    const Hc=fusion(g.A.H.filter(h=>couvre([h],P0,PN)>=0.5*(xR-xL)).map(h=>h.y),0.2*hm).filter(y=>dir<0?y<=bord+0.2*hm:y>=bord-0.2*hm).sort((a,b)=>dir<0?b-a:a-b);
    if(grL&&Hc.length>=2){const R=[];let vides=0;
      for(let k=0;k+1<Hc.length;k++){const a=Math.min(Hc[k],Hc[k+1]),b=Math.max(Hc[k],Hc[k+1]);if(b-a>10*hm)break;
        const T=D.filter(t=>t.y>a&&t.y<b);if(T.length&&enTete(T))break;
        if(!T.length){if(++vides>=2)break;continue}vides=0;R.push({y:(a+b)/2,T})}
      return{G:R,grille:true}}
    const L=[];D.forEach(t=>{const l=L.find(l=>Math.abs(l.y-t.y)<=0.5*Math.max(l.h,t.h));if(l)l.T.push(t);else L.push({y:t.y,h:t.h,T:[t]})});
    L.sort((a,b)=>loin(a)-loin(b));
    const G=[],pas=[];let prev=bord;
    for(const l of L){const gap=Math.abs(l.y-prev);if(gap>(G.length?Math.max(4*hm,2.5*(med(pas)||2*hm)):6*hm)||enTete(l.T))break;if(G.length)pas.push(gap);G.push(l);prev=l.y}
    return{G,grille:false}}
  // côté des lignes : celui qui en a le plus (en-tête en haut ou en bas ; un titre seul ne fait pas un côté)
  let dir=-1,res=cote(-1);const r2=cote(1);if(r2.G.length>res.G.length){dir=1;res=r2}
  const DT=res.G.flatMap(l=>l.T);
  // colonnes : traits de la grille ; sinon, entre deux titres, au milieu du plus large intervalle libre de textes (titres centrés,
  // valeurs alignées à gauche : le milieu entre titres tomberait dans une valeur) ; bords extérieurs complétés par les textes
  let B;
  if(grC)B=xs.slice();
  else{B=[];for(let j=0;j+1<Cl.length;j++){const a=Cl[j].x1,b=Cl[j+1].x0;let libres=[[a,b]];
      DT.forEach(t=>{libres=libres.flatMap(([u,v])=>t.x1<=u||t.x0>=v?[[u,v]]:[[u,t.x0],[t.x1,v]].filter(([p,q])=>q-p>0))});
      const w=libres.sort((p,q)=>(q[1]-q[0])-(p[1]-p[0]))[0];B.push(w?(w[0]+w[1])/2:(a+b)/2)}}
  const all=BT0.concat(DT),xmin=Math.min(...all.map(t=>t.x0)),xmax=Math.max(...all.map(t=>t.x1));
  if(!(ext&&grC)){if(!B.length||xmin<B[0]-0.3*hm)B.unshift(xmin-0.5*hm);if(xmax>B[B.length-1]+0.3*hm)B.push(xmax+0.5*hm)}
  const B0=B[0],BN=B[B.length-1],col=x=>{for(let j=0;j+1<B.length;j++)if(x<B[j+1])return j;return B.length-2};
  const BT=BT0.filter(t=>t.x>=B0&&t.x<=BN);
  const colonnes=B.slice(1).map((b,j)=>{const titre=cellule(BT.filter(t=>col(t.x)===j)),n=norm(titre),u=n.match(UNIT);
    return{titre,cle:kinds(n)[0]||'autre',unite:u?u[1]||u[2]:null}});
  if(!colonnes.some(c=>c.cle!=='autre'))return null;
  // lignes du tableau : bandes de la grille ; sans grille, une ligne par repère, les lignes de texte sans repère
  // (valeurs sur plusieurs lignes) rattachées au repère le plus proche en hauteur
  const rj=colonnes.findIndex(c=>c.cle==='repere'),G=res.G.map(l=>Object.assign({},l,{T:l.T.filter(t=>t.x>=B0&&t.x<=BN)})).filter(l=>l.T.length);
  let R;
  if(res.grille||rj<0)R=G.map(l=>l.T);
  else{const A=G.filter(l=>l.T.some(t=>col(t.x)===rj));
    if(!A.length)R=G.map(l=>l.T);
    else{R=A.map(a=>a.T.slice());G.forEach(l=>{if(A.includes(l))return;let k=0;A.forEach((a,j)=>{if(Math.abs(a.y-l.y)<Math.abs(A[k].y-l.y))k=j});R[k].push(...l.T)})}}
  // titre : textes au-delà de l'en-tête, du côté opposé aux lignes
  const bt=dir<0?band[1]:band[0],TT=g.T.filter(t=>libre(t)&&!BT0.includes(t)&&t.x>=B0-2*hm&&t.x<=BN+2*hm&&(dir<0?t.y>bt&&t.y-bt<=6*hm:t.y<bt&&bt-t.y<=6*hm));
  const RT=R.flat();
  [...BT,...TT,...RT].forEach(t=>used.add(t.i));
  return{titre:cellule(TT),colonnes,R:R.map(T=>colonnes.map((c,j)=>cellule(T.filter(t=>col(t.x)===j)))),RT:R,BT,TT,
    grille:{colonnes:grC,lignes:res.grille},cadre:[B0,Math.min(band[0],...RT.map(t=>t.y)),BN,Math.max(band[1],...RT.map(t=>t.y))],hm}
}

// doc (lecteur DXF) → {nomenclatures:[…], ecartes:[…], signalements:[…]} ; nomenclature = tableau de réservations
function analyser(doc){
  const G={},cleG=t=>t.espace+'\u0000'+(t.presentation||'');
  (doc.textes||[]).forEach(t=>{const r=((t.rot||0)%360+360)%360;if(Math.min(r,360-r)>1||!t.texte||!(t.h>0))return;
    const g=G[cleG(t)]=G[cleG(t)]||{espace:t.espace,presentation:t.presentation,T:[],S:[]};g.T.push(Object.assign({},t,{n:norm(t.texte),x0:t.x-t.w/2,x1:t.x+t.w/2}))});
  (doc.traits||[]).forEach(s=>{const g=G[cleG(s)];if(g)g.S.push(s)});
  const brut=[];
  Object.values(G).forEach(g=>{g.T.forEach((t,i)=>t.i=i);const K=g.T.map(t=>/\d/.test(t.n)&&!SOUS.test(t.n)?[]:kinds(t.n)),used=new Set();g.A=axes(g.S);
    // lignes d'en-tête possibles : textes à mot-clé alignés, coupées aux grands écarts et au 2e « repère » d'un en-tête complet
    const S=g.T.filter(t=>K[t.i].length).sort((a,b)=>b.y-a.y),rows=[];
    // tolérance 1 h : un titre de colonne sur deux lignes reste dans la même ligne d'en-tête (lignes à ± 0,8 h)
    S.forEach(t=>{const r=rows[rows.length-1];if(r&&Math.abs(r.y-t.y)<=Math.max(r.h,t.h))r.T.push(t);else rows.push({y:t.y,h:t.h,T:[t]})});
    const cand=[];
    rows.forEach(r=>{const hm=med(r.T.map(t=>t.h));let c=null;
      r.T.sort((a,b)=>a.x-b.x).forEach(t=>{const pk=K[t.i][0];
        if(!c||t.x0-c.x1>30*hm||pk==='repere'&&c.rep&&c.T.length>=3){c={T:[],x1:-Infinity,rep:false};cand.push(c)}
        c.T.push(t);c.x1=Math.max(c.x1,t.x1);c.rep=c.rep||pk==='repere'})});
    cand.map(c=>({T:c.T,k:new Set(c.T.map(t=>K[t.i][0])).size})).filter(c=>c.T.length>=3&&c.k>=2).sort((a,b)=>b.k-a.k||b.T.length-a.T.length)
      .forEach(c=>{if(c.T.some(t=>used.has(t.i)))return;const tb=construire(g,c.T,used,K);if(tb)brut.push(Object.assign(tb,{espace:g.espace,presentation:g.presentation}))})});
  brut.sort((a,b)=>(a.espace+(a.presentation||'')).localeCompare(b.espace+(b.presentation||''))||b.cadre[3]-a.cadre[3]||a.cadre[0]-b.cadre[0]);
  const nomenclatures=[],ecartes=[];
  brut.forEach(tb=>{const nat=nature(tb.titre,tb.colonnes),base={espace:tb.espace,presentation:tb.presentation,titre:tb.titre,
      colonnes:tb.colonnes,cadre:tb.cadre,ids:[...tb.BT,...tb.TT,...tb.RT.flat()].map(t=>t.id)};
    if(nat!=='reservations'||!tb.R.length){ecartes.push(Object.assign(base,{id:'T'+(ecartes.length+1),nature:nat,nLignes:tb.R.length,
      raison:nat==='aciers'?'nomenclature d\'aciers (ferraillage)':nat==='autre'?'tableau non identifié comme nomenclature de réservations':'en-tête de nomenclature sans ligne lisible'}));return}
    const id='N'+(nomenclatures.length+1),cj=k=>tb.colonnes.map((c,j)=>c.cle===k?j:-1).filter(j=>j>=0);
    const lignes=tb.R.map((cells,k)=>{const av=[],T=tb.RT[k],v=key=>cj(key).map(j=>cells[j]).filter(Boolean).join(' — ');
      const L={id:id+'-L'+String(k+1).padStart(2,'0'),rang:k+1,ids:T.map(t=>t.id),calques:[...new Set(T.map(t=>t.calque))],cellules:cells,
        repere:(cj('repere').map(j=>cells[j]).find(Boolean)||'').replace(/\n/g,' '),description:v('description'),type:v('type'),observations:v('observations'),
        lot:v('lot'),quantite:v('quantite'),niveau:v('niveau'),angle:v('angle'),reseau:v('reseau'),ouverture:v('ouverture')||v('diametre'),dims:null,a_verifier:av};
      if(!L.repere)av.push(cj('repere').length?'repère absent de la ligne':'pas de colonne repère dans le tableau');
      L.dims=dimsLigne(tb.colonnes,cells,av);
      if(L.dims&&!L.dims.unite)av.push('unité des cotes non indiquée par le tableau');
      return L});
    const nR=lignes.filter(l=>l.repere).length,nA=tb.colonnes.filter(c=>c.cle==='autre').length,motifs=[];
    motifs.push(tb.grille.colonnes&&tb.grille.lignes?'grille de traits lue':'pas de grille complète : '+(tb.grille.colonnes?'lignes':tb.grille.lignes?'colonnes':'colonnes et lignes')+' déduites de la position des textes');
    if(nR<lignes.length)motifs.push((lignes.length-nR)+' ligne(s) sans repère');if(nA)motifs.push(nA+' colonne(s) non reconnue(s), gardée(s) telles quelles');
    const niveau=tb.grille.colonnes&&tb.grille.lignes&&nR===lignes.length&&!nA?'bonne':nR>=lignes.length/2?'à vérifier':'faible';
    nomenclatures.push(Object.assign(base,{id,fichier:doc.fichier,nature:nat,calques:[...new Set(lignes.flatMap(l=>l.calques))],lignes,
      unite:[...new Set(tb.colonnes.filter(c=>c.cle==='ouverture'||c.cle==='diametre').map(c=>c.unite).filter(Boolean))].length===1?tb.colonnes.find(c=>c.unite&&(c.cle==='ouverture'||c.cle==='diametre')).unite:null,
      qualite:{niveau,motifs}}))});
  return{nomenclatures,ecartes,signalements:(doc.signalements||[]).slice()};
}

// Repère normalisé : majuscules, sans espaces ni séparateurs, zéros de tête des nombres retirés (D03 = D3 = d 3)
const cleRep=s=>sansAcc(s).toUpperCase().replace(/[\s._\-–—/]+/g,'').replace(/(^|[^0-9])0+(?=\d)/g,'$1');
function dansPoly(p,P){let c=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const a=P[i],b=P[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c}return c}
function dSeg(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],l=dx*dx+dy*dy,t=l?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)):0;return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)}
function dGeo(p,g){if(g.type==='cercle')return Math.max(0,Math.hypot(p[0]-g.centre[0],p[1]-g.centre[1])-g.r);
  const P=g.points;if(dansPoly(p,P))return 0;let d=Infinity;for(let i=0;i<P.length;i++)d=Math.min(d,dSeg(p,P[i],P[(i+1)%P.length]));return d}
// Cotes compatibles (mm) : 'ok' | 'diff' | '?' (unité inconnue ou cotes absentes) ; tolérance 1 % ou 2 mm
function compat(L,uT,c,uD){const d=L.dims;if(!d||!MM[d.unite||uT]||!MM[uD]||!c.dims)return'?';
  const kT=MM[d.unite||uT],kD=MM[uD],eq=(x,y)=>Math.abs(x-y)<=Math.max(2,0.01*Math.max(x,y));
  if(d.type==='circ')return c.type==='circ'&&eq(d.D*kT,c.dims.D*kD)?'ok':'diff';
  return c.type==='rect'&&eq(Math.max(d.a,d.b)*kT,c.dims.L*kD)&&eq(Math.min(d.a,d.b)*kT,c.dims.l*kD)?'ok':'diff'}

// Rapprochement des lignes avec les géométries du détecteur (espace Objet seulement). opt = {uniteDessin, unites:{idNomenclature:unité}}
// → {idLigne: {statut, options:[{c (rang dans C), id, d, via, cotes}], reperes:[{x,y,id}], note}}
function associer(noms,C,doc,opt){
  const o=opt||{},pris=new Set(),idx={},papier={};
  noms.forEach(N=>N.ids.forEach(i=>pris.add(i)));(o.exclus||[]).forEach(i=>pris.add(i));
  (doc.textes||[]).forEach(t=>{if(pris.has(t.id))return;const k=new Set([cleRep(t.texte)]);t.texte.split(/[\s,;:()[\]]+/).forEach(x=>k.add(cleRep(x)));
    k.forEach(x=>{if(!x)return;if(t.espace==='objet')(idx[x]=idx[x]||[]).push(t);else(papier[x]=papier[x]||new Set()).add(t.presentation||'présentation')})});
  const geo=C.map((c,i)=>({c,i})).filter(x=>x.c.statut==='a_confirmer'&&x.c.geometrie&&x.c.geometrie.espace!=='papier');
  const R={};
  noms.forEach(N=>{const uT=(o.unites||{})[N.id]||N.unite;N.lignes.forEach(L=>{const k=cleRep(L.repere),occ=k?idx[k]||[]:[],op={};
    occ.forEach(t=>{const P=[[t.x,t.y]].concat(t.fleches||[]),lim=4*t.h;
      geo.forEach(({c,i})=>{const d=Math.min(...P.map(p=>dGeo(p,c.geometrie)));if(d<=lim&&(!op[i]||d<op[i].d))op[i]={c:i,id:c.id,d,via:'repere',cotes:compat(L,uT,c,o.uniteDessin)}})});
    let options=Object.values(op).sort((a,b)=>a.d-b.d),statut,note='';
    const enPapier=k&&papier[k]?' ; repère présent dans une présentation (« '+[...papier[k]].join(' », « ')+' ») : lien non établi, fenêtre de présentation non interprétée':'';
    if(!occ.length){
      const M=L.dims?geo.filter(({c})=>compat(L,uT,c,o.uniteDessin)==='ok').map(({c,i})=>({c:i,id:c.id,d:null,via:'cotes',cotes:'ok'})):[];
      options=M;statut=M.length===1?'probable':M.length>1?'multiple':'absente';
      note=(k?'repère non trouvé dans l\'espace Objet':'ligne sans repère')+(M.length===1?' ; une seule géométrie de mêmes cotes':M.length>1?' ; '+M.length+' géométries de mêmes cotes':'')+enPapier}
    else if(!options.length){statut='absente';note=`repère trouvé ${occ.length} fois, aucun contour reconnu à proximité`}
    else if(options.length===1){const ok=options[0].cotes==='ok'&&!/^\d+$/.test(k);statut=ok?'trouvee':'probable';
      note=ok?'repère à proximité, cotes identiques':options[0].cotes==='diff'?'cotes du dessin différentes de celles du tableau':/^\d+$/.test(k)?'repère purement numérique : à vérifier':'cotes non comparables (unité ou cotes manquantes)'}
    else{statut='multiple';note=`${options.length} contours possibles`+(occ.length>1?` (repère présent ${occ.length} fois : vue, coupe ou détail ?)`:'')}
    R[L.id]={statut,options,reperes:occ.map(t=>({x:t.x,y:t.y,id:t.id})),note}})});
  return R;
}

// Ligne + choix de l'utilisateur → candidat au format du détecteur, pour l'adaptateur (cotes déjà en mm)
// s = {dims:{etat:'rect',a,b}|{etat:'circ',D} (mm), geo: candidat du détecteur rattaché | null}
function candidat(N,L,s){const d=s&&s.dims,g=s&&s.geo;if(!d||(d.etat!=='rect'&&d.etat!=='circ'))return null;
  return{id:L.id,type:d.etat,statut:'a_confirmer',unite:'mm',source:{fichier:N.fichier,format:'dxf',calque:L.calques.join(', '),id:g?g.source.id:null},
    geometrie:null,centre:g?g.centre:null,dims:d.etat==='circ'?{D:d.D}:{L:Math.max(d.a,d.b),l:Math.min(d.a,d.b),angle:0},h:null,manquants:[],remarques:[]}}

// Provenance d'un ouvrage créé depuis une ligne (clé origineImport du plan). k = {forme, cotes (texte saisi), dims (mm), ref,
// uniteTableau, uniteChoisie, geo:{c: candidat, statut:'trouvee'|'choisie'} | null}. Aucun contenu du DXF au-delà de la ligne.
function provenance(N,L,k){
  const textes={};N.colonnes.forEach((c,j)=>{const v=L.cellules[j];if(!v)return;let t=c.titre.replace(/\n/g,' ')||'colonne '+(j+1),n=2;const t0=t;while(t in textes)t=t0+' ('+(n++)+')';textes[t]=v});
  const d=L.dims,uT=d&&(d.unite||k.uniteTableau),kT=MM[uT],corrige=[];
  const mm=d&&kT?(d.type==='circ'?{etat:'circ',D:d.D*kT}:{etat:'rect',a:d.a*kT,b:d.b*kT}):null,eq=(x,y)=>Math.abs(x-y)<0.01;
  if(!mm||!k.dims||mm.etat!==k.dims.etat||(mm.etat==='circ'?!eq(mm.D,k.dims.D):!(eq(Math.max(mm.a,mm.b),Math.max(k.dims.a,k.dims.b))&&eq(Math.min(mm.a,mm.b),Math.min(k.dims.a,k.dims.b)))))corrige.push('cotes');
  if(String(k.ref||'')!==String(L.repere||'').toUpperCase())corrige.push('ref');
  const g=k.geo&&k.geo.c;
  return{fichier:N.fichier,format:'dxf',type:'nomenclature',espace:N.espace,presentation:N.presentation,calque:L.calques.join(', '),id:g?g.source.id:null,
    nomenclature:N.id,titre:N.titre,ligne:L.id,rang:L.rang,repere:L.repere,ids:L.ids.slice(),textes,
    unite_source:d?d.unite:null,unite:uT||null,dims_source:d?JSON.parse(JSON.stringify(d)):null,
    geometrie:g?{id:g.source.id,calque:g.source.calque,candidat:g.id,statut:k.geo.statut,centre:g.centre,dims_source:JSON.parse(JSON.stringify(g.dims))}:null,
    choix:{forme:k.forme,cotes:k.cotes,ref:k.ref||'',unite_tableau:k.uniteChoisie?k.uniteTableau:null},corrige,a_verifier:L.a_verifier.slice(),h_saisie:true};
}

root.CPI=Object.assign(root.CPI||{},{nomenclatures:{analyser,associer,cotes,candidat,provenance,cleRep,LIB}});
})(typeof globalThis!=='undefined'?globalThis:this);
