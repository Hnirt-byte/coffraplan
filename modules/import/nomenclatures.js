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
const ROT=[[1,0],[0,1],[-1,0],[0,-1]],tourne=(p,q)=>{const [c,s]=ROT[(q%4+4)%4];return[c*p[0]-s*p[1],s*p[0]+c*p[1]]};   // rotation exacte de q × 90°

// Nature d'une colonne d'après son titre : premier motif reconnu (« Réservation » seul = colonne des repères, en dernier)
const COLS=[
  // « Hauteur axe », « Axe réservations » : position de l'axe (altitude ou hauteur au-dessus d'un fond), jamais une cote d'ouverture
  ['niveau',mot("niv(eau|\\.)?|alti(metrie|tude)?|ngf|fil d'?eau|arase|cote (d'?axe|ngf|fil)|hauteur ?(\\/|par rapport|(d'? ?)?axe|sous)|axes? (des? )?(reservations?|tuyaux?|fourreaux?)|h ?\\/ ?[a-z]+")],
  ['angle',mot('angles?|orientation|azimut|gisement')],
  ['ouverture',mot("ouvertures?|tremies?|dim(ension)?s?\\.?|sections?|percements?|carottages?|passages?|encombrement|cotes|taille|l ?[x×*] ?[hl]|b ?[x×*] ?h")],
  ['reseau',mot("dn|reseaux?|canalisations?|tuyaux?|conduits?|gaines?|fluides?")],
  ['diametre',/(?<![a-z0-9])diam(etre|\.)?(?![a-z0-9])|ø|^[o0@©q](?: ?\(?(mm|cm|m)\)?)?$/],   // « O mm » : Ø d'un en-tête mal lu
  ['largeur',mot('larg(eur|\\.)?')],
  ['hauteur',mot('haut(eur|\\.)?')],
  ['quantite',mot('qte|quantites?|nombre|nb(re?)?|qt')],
  ['acier',mot('poids|masses?|faconnages?|nuances?|longueurs? developpees?|aciers?|armatures?|crochets?')],
  ['longueur',mot('long(ueur|\\.)?')],   // après « acier » : « longueur développée » reste une colonne d'aciers
  ['type',mot('types?|elements?|elts?|supports?|parois?|ouvrages?|localisation|emplacement|zone')],
  ['description',mot('designation|description|libelle|objet|nature|fonctions?|usage|destination|intitule')],
  ['observations',mot('observations?|remarques?|commentaires?|notes?|obs\\.?')],
  ['lot',mot("lots?|entreprises?|corps d'?etat|fournisseurs?|intervenants?|emetteur|responsable|societe|poseur")],
  // « Réservation(s) » n'est un titre de repères que seul (ou avec n°) : « Axe réservations », « Niveau réservation » n'en sont pas
  ['repere',new RegExp(mot("rep(ere|\\.)?|ref(erence|\\.)?|n°|no\\.?|num(ero|\\.)?|marque|identifiant|id|code").source+'|^(?:(?:n°|no) ?)?(?:reservations?|resas?)$')]];
const kinds=n=>COLS.filter(c=>c[1].test(n)).map(c=>c[0]);
const LIB={repere:'repère',description:'désignation',type:'type / élément',ouverture:'ouverture',reseau:'réseau',diametre:'diamètre',
  niveau:'niveau (position)',angle:'angle (position)',largeur:'largeur',hauteur:'hauteur',longueur:'longueur',quantite:'quantité',observations:'observations',lot:'lot / entreprise',acier:'acier (ferraillage)',autre:'non reconnue'};
// Nature du tableau : en-tête + titre seulement (un tableau d'aciers a aussi des repères et des diamètres)
const RESA=mot('reservations?|resas?|tremies?|fourreaux?|ouvertures?|percements?|carottages?|traversees?|incorporations?|passages?|rebouchages?');
const ACIER=mot('aciers?|fers|ha\\d*|ferraillages?|armatures?|nuances?|faconnages?|barres?|poids|masses?|kg|longueurs? developpees?|crochets?|epingles?|etriers?|cadres?|enrobages?|espacements?|fe ?e?500|b ?500|treillis');
const AUTRE=mot("indices?|ind\\.?|revisions?|modifications?|dessine|verifie|approuve|folios?|liste des plans|documents?|bordereau|planning");
// Trappes, regards, tampons (ouvertures équipées d'un cadre ou d'une feuillure) : tableau distinct, jamais des réservations
const TRAPPE=mot("trappes?|regards?|tampons?|feuillures?|ouvertures? equipees?|chassis|caillebotis");
const ECART=60;   // en hauteurs de texte : écart horizontal au-delà duquel deux titres (ou deux valeurs d'une ligne) ne sont plus du même tableau (colonne de commentaires large : ≈ 32 h mesurés)
const RAISON_TRAPPES='nomenclature de trappes / ouvertures équipées (cadres, feuillures) : lignes consultables, jamais créées comme réservations';
const POIDS={ouverture:2,niveau:1,angle:1,reseau:1,diametre:1};
function nature(titre,cols){let R=0,A=0,O=0,T=0;
  [titre].concat(cols.map(c=>c.titre)).forEach(t=>{const n=norm(t);if(RESA.test(n))R+=3;if(ACIER.test(n))A+=3;if(AUTRE.test(n))O+=3;if(TRAPPE.test(n))T+=3});
  if(T&&!RESA.test(norm(titre)))return'trappes';   // titre de trappes, ou colonne « feuillure » sans titre de réservations
  cols.forEach(c=>{R+=POIDS[c.cle]||0});
  return R>=3&&R>A&&R>O?'reservations':A>=3&&A>=R?'aciers':'autre'}
// unité d'une colonne : « (mm) », « en mm », ou « mm » seul en fin de titre (« Largeur mm », titre sur deux lignes)
const UNIT=/\(\s*(mm|cm|m)\s*\)|(?<![a-z])(?:en|unite :?) (mm|cm|m)(?![a-z])|(?<![a-z0-9])(mm|cm|m)$/;
const uCol=u=>u?u[1]||u[2]||u[3]:null;
const SOUS=/\(\s*(mm|cm|m)\s*\)|^\(.*\)$|^(mm|cm|m)$|(?<![a-z])[lb] ?[x×*] ?[hl](?![a-z])/;   // 2e ligne d'un titre de colonne

// Valeur d'une cellule de cotes → {etat:'rect',a,b,c?,unite} | {etat:'circ',D,unite} | {etat:'dn',D} | {etat:'seul',v,unite}
// | {etat:'manquant'|'vide'|'illisible'}. u0 = unité de la colonne ; une unité écrite dans la cellule l'emporte.
// saisie : texte tapé dans la fenêtre (« d250 » ou « o250 » acceptés pour Ø, le Ø étant rare sur un clavier).
const VIDE=/^(s\.?o\.?|sans objet|a definir|adf|a voir|nc|n\.c\.?|non communique|neant|nr|\/+|-+|—|–|\?+|x)$/;
function cotes(s,u0,saisie){
  const t0=String(s==null?'':s).trim(),t=norm(t0).replace(/,/g,'.');
  if(!t)return{etat:'vide'};
  if(VIDE.test(t))return{etat:'manquant',texte:t0};
  // unité : seulement celle écrite contre la cote elle-même (« 500x500 mm », « Ø250mm ») ; une autre valeur de la cellule
  // (« 500x500 — 4,86m » : hauteur d'axe fusionnée) ne donne jamais l'unité de l'ouverture (unité de la cellule seule : cotes(v, null))
  const N='(\\d+(?:\\.\\d+)?)',U='\\s*(?:mm|cm|m)?\\s*',UF='(?:\\s*(mm|cm|m)(?![a-z0-9]))?',un=s=>({unite:(s.match(/\d\s*(mm|cm|m)(?![a-z0-9])/)||[])[1]||u0||null});
  let m=t.match(new RegExp(N+U+'[x×*]\\s*'+N+'(?:'+U+'[x×*]\\s*'+N+')?'+UF));
  if(m)return Object.assign({etat:'rect',a:+m[1],b:+m[2]},un(m[0]),m[3]?{c:+m[3]}:{});
  if((m=t.match(new RegExp('(?:ø|diam\\.?|diametre|phi'+(saisie?'|d|o':'')+')\\s*'+N+UF))))return Object.assign({etat:'circ',D:+m[1]},un(m[0]));
  if((m=t.match(new RegExp('(?<![a-z])dn\\s*'+N))))return{etat:'dn',D:+m[1]};
  if((m=t.match(new RegExp('^'+N+'\\s*(mm|cm|m)?$'))))return Object.assign({etat:'seul',v:+m[1]},un(m[0]));
  return{etat:'illisible',texte:t0};
}

// Cotes d'une ligne, dans cet ordre : 1. ouverture explicite exploitable ; 2. diamètre exploitable (cercle) ; 3. Largeur et
// Hauteur (rectangle). Vide, « - », SO… = valeur absente, jamais une cote contradictoire : on passe à la colonne suivante.
// Diamètre et Largeur × Hauteur tous deux renseignés : ambiguïté signalée, rien n'est choisi. DN du réseau ≠ diamètre.
// « Hauteur » d'un tableau = 2e cote de l'ouverture, jamais la hauteur de coffrage (h reste à saisir) ; « Longueur » sans
// « Hauteur » = 2e cote (trappes, regards). Unité écrite dans la cellule différente de celle du titre de colonne : cote gardée,
// unité laissée à confirmer (conflitUnite), jamais convertie. DN dans la colonne Ouverture : réservation circulaire probable,
// noté dans info.dn, aucune cote tirée du DN (décision de Kévin, 21/10/2026).
function dimsLigne(cols,cells,av,info){
  const get=k=>cols.map((c,j)=>c.cle===k&&cells[j]?{c,v:cells[j]}:null).filter(Boolean),q=v=>`« ${v.replace(/\n/g,' ')} »`;
  // unité écrite dans la cellule contre la cote (ue) ou titre de colonne ; les deux différentes : à confirmer. info.uniteOrigine : provenance
  const uc=(r,c,v)=>{const ue=cotes(v,null).unite;if(ue&&c.unite&&ue!==c.unite){av.push(`unité « ${ue} » écrite dans la cellule, « ${c.unite} » dans le titre de la colonne « ${c.titre.replace(/\n/g,' ')} » : unité à confirmer (aucune conversion)`);return{unite:null,conflitUnite:true}}
    if(info)info.uniteOrigine=ue?'cellule':c.unite?'titre de colonne':null;return{unite:r.unite}};
  const dd=(r,c,v)=>Object.assign(r.etat==='rect'?{type:'rect',a:r.a,b:r.b}:{type:'circ',D:r.D},uc(r,c,v),{texte:v,colonne:c.titre});
  const absent=r=>r.etat==='vide'||r.etat==='manquant',dn='DN du réseau, diamètre de la réservation à saisir';
  const O=get('ouverture');
  if(O.length){const {c,v}=O[0],r=cotes(v,c.unite);
    if(r.etat==='rect'){if(r.c!=null)av.push(`ouverture ${q(v)} : 3e cote ignorée`);return dd(r,c,v)}
    if(r.etat==='circ')return dd(r,c,v);
    if(r.etat==='dn'&&info)info.dn={D:r.D,texte:v.replace(/\n/g,' ')};
    if(!absent(r))av.push(`ouverture ${q(v)} : `+(r.etat==='dn'?'DN : réservation circulaire probable, diamètre réel de réservation à confirmer (aucune cote tirée du DN)':r.etat==='seul'?'une seule cote, forme et cotes à préciser':'cotes non lues'))}
  let circ=null;
  const Dm=get('diametre');
  if(Dm.length){const {c,v}=Dm[0],r=cotes(v,c.unite);
    if(r.etat==='rect'||r.etat==='circ'||r.etat==='seul'){circ=dd(r.etat==='seul'?Object.assign({},r,{etat:'circ',D:r.v}):r,c,v);
      av.push(`cote prise dans la colonne « ${c.titre.replace(/\n/g,' ')} » : à confirmer comme cote de la réservation`)}
    else if(!absent(r))av.push(`colonne « ${c.titre.replace(/\n/g,' ')} » ${q(v)} : `+(r.etat==='dn'?dn:'cotes non lues'))}
  let rect=null;
  const La=get('largeur'),Ha=get('hauteur').length?get('hauteur'):get('longueur');
  if(La.length||Ha.length){const a=La.length?cotes(La[0].v,La[0].c.unite):{etat:'vide'},b=Ha.length?cotes(Ha[0].v,Ha[0].c.unite):{etat:'vide'};
    if(a.etat==='seul'&&b.etat==='seul'){const ua=uc(a,La[0].c,La[0].v),ub=uc(b,Ha[0].c,Ha[0].v),cf=ua.conflitUnite||ub.conflitUnite||ua.unite&&ub.unite&&ua.unite!==ub.unite;
      if(cf&&!ua.conflitUnite&&!ub.conflitUnite)av.push(`unités différentes « ${ua.unite} » / « ${ub.unite} » pour Largeur et Hauteur : unité à confirmer (aucune conversion)`);
      rect=Object.assign({type:'rect',a:a.v,b:b.v},cf?{unite:null,conflitUnite:true}:{unite:ua.unite||ub.unite},{texte:La[0].v+' × '+Ha[0].v,colonne:La[0].c.titre+' / '+Ha[0].c.titre})}
    else if(!absent(a)||!absent(b))av.push(a.etat==='seul'||b.etat==='seul'?'une seule des cotes Largeur / Hauteur lue : cotes à compléter':'cotes Largeur / Hauteur non lues')}
  if(circ&&rect){av.push(`diamètre ${q(circ.texte)} et Largeur × Hauteur ${q(rect.texte)} tous deux renseignés : forme et cotes à confirmer`);return null}
  if(circ)return circ;
  if(rect){av.push('cotes reprises des colonnes Largeur et Hauteur (la hauteur est une cote de l\'ouverture, pas la hauteur de coffrage) : à confirmer');return rect}
  if(O.length||Dm.length||La.length||Ha.length){if(!av.length)av.push('cotes de l\'ouverture non renseignées');return null}
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
  const hm=med(hg.map(t=>t.h)),yH=hg.reduce((s,t)=>s+t.y,0)/hg.length;let xL=Math.min(...hg.map(t=>t.x0)),xR=Math.max(...hg.map(t=>t.x1));
  const libre=t=>!used.has(t.i);
  // bande d'en-tête : entre deux traits horizontaux de la grille, sinon textes à mot-clé ou sous-titres « (mm) » juste au-dessus / au-dessous
  const Hy=fusion(g.A.H.filter(h=>couvre([h],xL,xR)>=0.5*(xR-xL)).map(h=>h.y),0.2*hm),   // croissant
    dessus=Hy.find(y=>y>yH+0.3*hm),dessous=Hy.filter(y=>y<yH-0.3*hm).pop();
  let band,grL=false;
  if(dessus!==undefined&&dessous!==undefined&&dessus-dessous<=8*hm){band=[dessous,dessus];grL=true}
  else{band=[Math.min(...hg.map(t=>t.y))-0.6*hm,Math.max(...hg.map(t=>t.y))+0.6*hm];
    // largeur du tableau : celle de la 1re ligne de valeurs (texte chiffré) contre l'en-tête, suivie de proche en proche (écart ≤ 30 h) :
    // des colonnes éloignées des autres (IDENTIFIANT, COMMENTAIRES larges) restent dans le tableau
    const pres=t=>Math.min(Math.abs(t.y-band[0]),Math.abs(t.y-band[1])),ln=g.T.filter(t=>libre(t)&&/\d/.test(t.n)&&t.x>=xL&&t.x<=xR&&(t.y<band[0]||t.y>band[1])&&pres(t)<=3*hm).sort((a,b)=>pres(a)-pres(b))[0];
    if(ln){const L=g.T.filter(t=>libre(t)&&Math.abs(t.y-ln.y)<=0.5*Math.max(t.h,ln.h)).sort((a,b)=>a.x0-b.x0);let i=L.indexOf(ln),j=i;
      while(i>0&&L[i].x0-L[i-1].x1<=ECART*hm)i--;while(j<L.length-1&&L[j+1].x0-L[j].x1<=ECART*hm)j++;xL=Math.min(xL,L[i].x0);xR=Math.max(xR,L[j].x1)}
    // en-tête sur plusieurs lignes (titres de groupe « DIMENSIONS (mm) » au-dessus de « Hauteur », « Largeur ») : lignes voisines dont
    // aucun texte n'a de chiffre (une ligne de valeurs a toujours un repère, une cote ou un niveau chiffrés)
    const sansChiffre=t=>!g.T.some(u=>Math.abs(u.y-t.y)<=0.5*Math.max(u.h,t.h)&&u.x>=xL-2*hm&&u.x<=xR+2*hm&&/\d/.test(u.n));
    for(let k=0;k<6;k++)g.T.forEach(t=>{if(!libre(t)||t.x<xL-2*hm||t.x>xR+2*hm||t.y>=band[0]&&t.y<=band[1])return;
      const d=t.y<band[0]?band[0]-t.y:t.y-band[1];if(d<=1.3*hm&&(K[t.i].length||SOUS.test(t.n)||t.h<=1.1*hm&&!/\d/.test(t.n)&&sansChiffre(t))){band[0]=Math.min(band[0],t.y-0.6*t.h);band[1]=Math.max(band[1],t.y+0.6*t.h)}})}
  // traits verticaux de la grille : ils traversent l'en-tête, entre les extrémités du trait qui la borde (grille) ou en
  // partant de son bord (un cadre de feuille ou le tableau voisin ne comptent pas)
  const yM=(band[0]+band[1])/2,ext=grL?etendue(g.A.H,dessus,xL,xR,hm):null,
    garde=v=>ext?v.x>=ext[0]-0.3*hm&&v.x<=ext[1]+0.3*hm:v.x>=xL-15*hm&&v.x<=xR+15*hm&&(Math.abs(v.y1-band[1])<=0.5*hm||Math.abs(v.y0-band[0])<=0.5*hm);
  let xs=fusion(g.A.V.filter(v=>v.y0-0.2*hm<=yM&&yM<=v.y1+0.2*hm&&garde(v)).map(v=>v.x),0.3*hm);
  if(ext&&xs.length){if(xs[0]>ext[0]+0.3*hm)xs.unshift(ext[0]);if(xs[xs.length-1]<ext[1]-0.3*hm)xs.push(ext[1])}
  const grC=xs.length>=2;
  const BT0=g.T.filter(t=>libre(t)&&t.y>=band[0]&&t.y<=band[1]&&t.x>=(grC?Math.min(xs[0],xL-2*hm):xL-2*hm)&&t.x<=(grC?Math.max(xs[xs.length-1],xR+2*hm):xR+2*hm));
  // colonnes d'en-tête de bas en haut : un titre au-dessus de plusieurs colonnes (« DIMENSIONS (mm) », « FINITIONS ») est un titre de
  // groupe : il ne fait pas une colonne, il donne son unité aux colonnes qu'il couvre
  const Cl=[],GR=new Map(),sur=(t,c)=>t.x0<=c.x1+0.3*hm&&t.x1>=c.x0-0.3*hm;
  BT0.slice().sort((a,b)=>a.y-b.y||a.x0-b.x0).forEach(t=>{const C=Cl.filter(c=>sur(t,c));
    if(C.length>=2&&C.every(c=>t.y>c.y+0.5*hm)){GR.set(t,C);return}
    if(C.length){const c=C[0];c.x0=Math.min(c.x0,t.x0);c.x1=Math.max(c.x1,t.x1);c.y=Math.max(c.y,t.y)}else Cl.push({x0:t.x0,x1:t.x1,y:t.y})});
  Cl.sort((a,b)=>a.x0-b.x0);for(let j=1;j<Cl.length;j++)if(Cl[j].x0<=Cl[j-1].x1+0.3*hm){Cl[j-1].x1=Math.max(Cl[j-1].x1,Cl[j].x1);Cl.splice(j--,1)}
  const pad=Math.max(4*hm,med(Cl.map(c=>c.x1-c.x0))),P0=ext&&grC?xs[0]:Cl[0].x0-pad,PN=ext&&grC?xs[xs.length-1]:Cl[Cl.length-1].x1+pad;
  // une ligne qui contient un chiffre (repère, cote, niveau) n'est pas un en-tête, même si ses mots ressemblent à des titres
  const enTete=T=>{const k=new Set();let c=0;T.forEach(t=>{if(K[t.i].length){c++;k.add(K[t.i][0])}});return c>=3&&k.size>=2&&!T.some(t=>/\d/.test(t.n))};
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
  const colonnes=B.slice(1).map((b,j)=>{const titre=cellule(BT.filter(t=>!GR.has(t)&&col(t.x)===j)),n=norm(titre),u=n.match(UNIT),xc=(B[j]+b)/2,
      gr=[...GR.keys()].find(t=>t.x0-0.3*hm<=xc&&t.x1+0.3*hm>=xc),gt=gr?gr.texte.trim():'';
    return Object.assign({titre,cle:kinds(n)[0]||'autre',unite:uCol(u)||(gr?uCol(norm(gt).match(UNIT)):null)},gr?{groupe:gt}:{})});
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
  return{titre:cellule(TT),colonnes,R:R.map(T=>colonnes.map((c,j)=>cellule(T.filter(t=>col(t.x)===j)))),RI:R.map(T=>colonnes.map((c,j)=>T.filter(t=>col(t.x)===j).map(t=>t.id))),RT:R,BT,TT,
    grille:{colonnes:grC,lignes:res.grille},cadre:[B0,Math.min(band[0],...RT.map(t=>t.y)),BN,Math.max(band[1],...RT.map(t=>t.y))],hm}
}

// doc (lecteur DXF) → {nomenclatures:[…], ecartes:[…], signalements:[…]} ; nomenclature = tableau de réservations
function analyser(doc){
  const G={},cleG=t=>t.espace+'\u0000'+(t.presentation||'');
  // tableau tourné de 90°, 180° ou 270° dans sa page : textes de même sens et traits ramenés à l'horizontale (rotation exacte),
  // tableau reconstruit comme les autres, cadre rendu dans le repère de la page
  (doc.textes||[]).forEach(t=>{const r=((t.rot||0)%360+360)%360,q=Math.round(r/90)%4;if(Math.abs(r-90*Math.round(r/90))>1||!t.texte||!(t.h>0))return;
    const k=cleG(t)+'\u0000'+q,g=G[k]=G[k]||{espace:t.espace,presentation:t.presentation,page:t.page,q,T:[],S:[]},p=tourne([t.x,t.y],-q);
    g.T.push(Object.assign({},t,{x:p[0],y:p[1],n:norm(t.texte),x0:p[0]-t.w/2,x1:p[0]+t.w/2}))});
  (doc.traits||[]).forEach(s=>{for(let q=0;q<4;q++){const g=G[cleG(s)+'\u0000'+q];if(g)g.S.push(q?Object.assign({},s,{a:tourne(s.a,-q),b:tourne(s.b,-q)}):s)}});
  const brut=[];
  Object.values(G).forEach(g=>{g.T.forEach((t,i)=>t.i=i);const K=g.T.map(t=>/\d/.test(t.n)&&!SOUS.test(t.n)?[]:kinds(t.n)),used=new Set();g.A=axes(g.S);
    // lignes d'en-tête possibles : textes à mot-clé alignés, coupées aux grands écarts et au 2e « repère » d'un en-tête complet
    const S=g.T.filter(t=>K[t.i].length).sort((a,b)=>b.y-a.y),rows=[];
    // tolérance 1 h : un titre de colonne sur deux lignes reste dans la même ligne d'en-tête (lignes à ± 0,8 h)
    S.forEach(t=>{const r=rows[rows.length-1];if(r&&Math.abs(r.y-t.y)<=Math.max(r.h,t.h))r.T.push(t);else rows.push({y:t.y,h:t.h,T:[t]})});
    const cand=[];
    rows.forEach(r=>{const hm=med(r.T.map(t=>t.h));let c=null;
      r.T.sort((a,b)=>a.x-b.x).forEach(t=>{const pk=K[t.i][0];
        if(!c||t.x0-c.x1>ECART*hm||pk==='repere'&&c.rep&&c.T.length>=3){c={T:[],x1:-Infinity,rep:false};cand.push(c)}
        c.T.push(t);c.x1=Math.max(c.x1,t.x1);c.rep=c.rep||pk==='repere'})});
    cand.map(c=>({T:c.T,k:new Set(c.T.map(t=>K[t.i][0])).size})).filter(c=>c.T.length>=3&&c.k>=2).sort((a,b)=>b.k-a.k||b.T.length-a.T.length)
      .forEach(c=>{if(c.T.some(t=>used.has(t.i)))return;const tb=construire(g,c.T,used,K);if(!tb)return;
        if(g.q){const c=tb.cadre,P=[[c[0],c[1]],[c[2],c[3]],[c[0],c[3]],[c[2],c[1]]].map(p=>tourne(p,g.q));tb.cadre=[Math.min(...P.map(p=>p[0])),Math.min(...P.map(p=>p[1])),Math.max(...P.map(p=>p[0])),Math.max(...P.map(p=>p[1]))];tb.rotation=90*g.q}
        brut.push(Object.assign(tb,{espace:g.espace,presentation:g.presentation},g.page?{page:g.page}:{}))})});
  brut.sort((a,b)=>(a.espace+(a.presentation||'')).localeCompare(b.espace+(b.presentation||''))||b.cadre[3]-a.cadre[3]||a.cadre[0]-b.cadre[0]);
  const nomenclatures=[],ecartes=[];
  brut.forEach(tb=>{const nat=nature(tb.titre,tb.colonnes),base={espace:tb.espace,presentation:tb.presentation,...(tb.page?{page:tb.page}:{}),titre:tb.titre,
      colonnes:tb.colonnes,cadre:tb.cadre,...(tb.rotation?{rotation:tb.rotation}:{}),ids:[...tb.BT,...tb.TT,...tb.RT.flat()].map(t=>t.id)};
    if(nat!=='reservations'||!tb.R.length){ecartes.push(Object.assign(base,{id:'T'+(ecartes.length+1),nature:nat,nLignes:tb.R.length,
      raison:nat==='aciers'?'nomenclature d\'aciers (ferraillage)':nat==='trappes'?RAISON_TRAPPES:nat==='autre'?'tableau non identifié comme nomenclature de réservations':'en-tête de nomenclature sans ligne lisible'},
      // trappes : lignes gardées pour consultation (saisie manuelle possible), jamais proposées à la création
      nat==='trappes'?{lignes:tb.R.map((cells,k)=>Object.assign({rang:k+1},ligne(tb.colonnes,cells)))}:{}));return}
    const id='N'+(nomenclatures.length+1);
    const lignes=tb.R.map((cells,k)=>Object.assign({id:id+'-L'+String(k+1).padStart(2,'0'),rang:k+1,ids:tb.RT[k].map(t=>t.id),calques:[...new Set(tb.RT[k].map(t=>t.calque))]},
      ligne(tb.colonnes,cells),{idsCellules:tb.RI[k]}));
    const nR=lignes.filter(l=>l.repere).length,nA=tb.colonnes.filter(c=>c.cle==='autre').length,motifs=[];
    motifs.push(tb.grille.colonnes&&tb.grille.lignes?'grille de traits lue':'pas de grille complète : '+(tb.grille.colonnes?'lignes':tb.grille.lignes?'colonnes':'colonnes et lignes')+' déduites de la position des textes');
    if(nR<lignes.length)motifs.push((lignes.length-nR)+' ligne(s) sans repère');if(nA)motifs.push(nA+' colonne(s) non reconnue(s), gardée(s) telles quelles');
    const niveau=tb.grille.colonnes&&tb.grille.lignes&&nR===lignes.length&&!nA?'bonne':nR>=lignes.length/2?'à vérifier':'faible';
    nomenclatures.push(Object.assign(base,{id,fichier:doc.fichier,format:doc.format||'dxf',nature:nat,calques:[...new Set(lignes.flatMap(l=>l.calques))],lignes,
      unite:[...new Set(tb.colonnes.filter(c=>c.cle==='ouverture'||c.cle==='diametre').map(c=>c.unite).filter(Boolean))].length===1?tb.colonnes.find(c=>c.unite&&(c.cle==='ouverture'||c.cle==='diametre')).unite:null,
      qualite:{niveau,motifs}}))});
  return{nomenclatures,ecartes,signalements:(doc.signalements||[]).slice()};
}

// ==== Tableau à grille de traits (phase 5) : cellules d'abord, textes ensuite ====
// Grille d'un tableau à partir de ses traits droits (points PDF, Y vers le haut ; traits vectoriels du PDF ou relevés sur l'image) :
// traits d'une même ligne réunis (interrompus, superposés, doublés), largeur du tableau = plus long trait horizontal, lignes
// horizontales qui couvrent au moins la moitié de cette largeur, colonnes verticales qui couvrent au moins le quart de sa hauteur ;
// dans chaque rangée, seules les séparations réellement tracées à sa hauteur comptent (cellules fusionnées : une cellule sur
// plusieurs colonnes). z = zone {x0,y0,x1,y1} → null (pas de grille d'au moins 2 colonnes et 1 rangée) ou
// {cadre:[x0,y0,x1,y1], xs (gauche → droite), ys (haut → bas), rangs:[{y0 (haut), y1 (bas), cellules:[{j0,j1,x0,x1}]}], t}
function grilleTraits(S,z){const W=z.x1-z.x0,Hz=z.y1-z.y0,t=Math.max(0.6,0.002*Math.max(W,Hz)),minL=Math.max(4,0.03*Math.min(W,Hz)),cl=(v,a,b)=>Math.min(b,Math.max(a,v)),H=[],V=[];
  S.forEach(s=>{const dx=s.b[0]-s.a[0],dy=s.b[1]-s.a[1],l=Math.hypot(dx,dy);if(!(l>=minL))return;
    if(Math.abs(dy)<=0.01*l){const p=(s.a[1]+s.b[1])/2;if(p<z.y0-t||p>z.y1+t)return;const u=cl(Math.min(s.a[0],s.b[0]),z.x0,z.x1),v=cl(Math.max(s.a[0],s.b[0]),z.x0,z.x1);if(v-u>=minL)H.push({p,u,v})}
    else if(Math.abs(dx)<=0.01*l){const p=(s.a[0]+s.b[0])/2;if(p<z.x0-t||p>z.x1+t)return;const u=cl(Math.min(s.a[1],s.b[1]),z.y0,z.y1),v=cl(Math.max(s.a[1],s.b[1]),z.y0,z.y1);if(v-u>=minL)V.push({p,u,v})}});
  const lignes=(A,gap)=>{A.sort((a,b)=>a.p-b.p);const C=[];A.forEach(s=>{const c=C[C.length-1];if(c&&s.p-c.p1<=t){c.p1=s.p;c.ps.push(s.p);c.I.push([s.u,s.v])}else C.push({p1:s.p,ps:[s.p],I:[[s.u,s.v]]})});
    return C.map(c=>{c.I.sort((a,b)=>a[0]-b[0]);const R=[];c.I.forEach(([u,v])=>{const r=R[R.length-1];if(r&&u<=r[1]+gap)r[1]=Math.max(r[1],v);else R.push([u,v])});return{p:med(c.ps),I:R}})};
  const cov=(I,a,b)=>I.reduce((s,[u,v])=>s+Math.max(0,Math.min(v,b)-Math.max(u,a)),0);
  const LH=lignes(H,0.02*W),LV=lignes(V,0.02*Hz);if(LH.length<2||LV.length<2)return null;
  let X0=0,X1=0;LH.forEach(l=>l.I.forEach(([u,v])=>{if(v-u>X1-X0){X0=u;X1=v}}));
  const ys=LH.filter(l=>cov(l.I,X0,X1)>=0.5*(X1-X0)).map(l=>l.p).sort((a,b)=>b-a);if(ys.length<2)return null;
  const Y0=ys[ys.length-1],Y1=ys[0];
  // séparation de colonnes : trait qui traverse toute une rangée (au moins une) ; les jambages de lettres dessinées en traits,
  // même alignés d'une rangée à l'autre, n'en traversent aucune
  const B0=ys.map((y,i)=>i?[ys[i],ys[i-1]]:null).filter(Boolean).filter(([b,a])=>a-b>=3*t),traverse=(l,[b,a])=>cov(l.I,b,a)>=0.8*(a-b);
  const LC=LV.filter(l=>l.p>=X0-2*t&&l.p<=X1+2*t&&cov(l.I,Y0,Y1)>=0.25*(Y1-Y0)&&B0.some(r=>traverse(l,r)));
  let xs=LC.map(l=>l.p).concat([X0,X1]).sort((a,b)=>a-b);
  xs=xs.filter((x,j)=>!j||x-xs[j-1]>2*t);if(xs.length<3)return null;   // une seule colonne : pas une grille
  const rangs=[];
  for(let i=0;i+1<ys.length;i++){const a=ys[i],b=ys[i+1];if(a-b<3*t)continue;
    const B=xs.map((x,j)=>j).filter(j=>!j||j===xs.length-1||LC.some(l=>Math.abs(l.p-xs[j])<=2*t&&traverse(l,[b,a])));
    rangs.push({y0:a,y1:b,cellules:B.slice(1).map((j,n)=>({j0:B[n],j1:j,x0:xs[B[n]],x1:xs[j]}))})}
  return rangs.length?{cadre:[X0,Y0,X1,Y1],xs,ys,rangs,t}:null}

// Textes extractibles d'une zone rangés dans la grille de ses traits (tableau dont l'en-tête n'est pas reconnu par analyser) :
// sens de lecture = celui de la majorité des textes ; un texte va à la cellule qui contient son centre. → G de depuisGrille, avec
// textes (copie des textes du PDF, sans incertitude : ocr.conf 100) | null
function textesEnGrille(S,z,T){const Q=[0,0,0,0];T.forEach(t=>Q[Math.round(((t.rot||0)%360+360)%360/90)%4]++);const q=Q.indexOf(Math.max(...Q));
  const Sq=q?S.map(s=>({a:tourne(s.a,-q),b:tourne(s.b,-q)})):S,P=[[z.x0,z.y0],[z.x1,z.y1],[z.x0,z.y1],[z.x1,z.y0]].map(p=>tourne(p,-q)),
    zq={x0:Math.min(...P.map(p=>p[0])),y0:Math.min(...P.map(p=>p[1])),x1:Math.max(...P.map(p=>p[0])),y1:Math.max(...P.map(p=>p[1]))},g=grilleTraits(Sq,zq);if(!g)return null;
  const nc=g.xs.length-1,lignes=g.rangs.map(()=>Array(nc).fill('')),ids=g.rangs.map(()=>Array.from({length:nc},()=>[])),pos=new Map(),textes=[];
  T.forEach(t=>{const p=tourne([t.x,t.y],-q),i=g.rangs.findIndex(r=>p[1]<=r.y0&&p[1]>=r.y1);if(i<0)return;const c=g.rangs[i].cellules.find(c=>p[0]>=c.x0&&p[0]<=c.x1);if(!c)return;
    (pos.get(i+','+c.j0)||pos.set(i+','+c.j0,[]).get(i+','+c.j0)).push(Object.assign({},t,{x:p[0],y:p[1]}))});
  pos.forEach((A,key)=>{const [i,j]=key.split(',').map(Number),v=cellule(A);lignes[i][j]=v;A.forEach(t=>{ids[i][j].push(t.id);const o=T.find(u=>u.id===t.id),hw=(o.w||0)/2,hh=(o.h||0);
    textes.push(Object.assign({},o,{ocr:{brut:o.texte,conf:100,corrections:[],incertain:false,box:{page:o.page,x0:o.x-(q%2?hh:hw),y0:o.y-(q%2?hw:hh),x1:o.x+(q%2?hh:hw),y1:o.y+(q%2?hw:hh)}}}))})});
  const c=g.cadre,C=[[c[0],c[1]],[c[2],c[3]],[c[0],c[3]],[c[2],c[1]]].map(p=>tourne(p,q));
  return{lignes,ids,titre:'',cadre:[Math.min(...C.map(p=>p[0])),Math.min(...C.map(p=>p[1])),Math.max(...C.map(p=>p[0])),Math.max(...C.map(p=>p[1]))],page:z.page,rotation:q*90,zone:z,textes,rangees:g.rangs.length}}

// Tableau dont chaque cellule est déjà lue (OCR cellule par cellule, ou textes d'un PDF rangés dans la grille) → nomenclature au
// contrat d'analyser. G = {lignes:[[texte de chaque colonne]] (rangées de haut en bas, '' = vide), ids:[[[id]]], titre, cadre, page,
// espace, presentation, fichier, format} ; cles = clés de colonnes choisies par l'utilisateur (sinon lues dans l'en-tête).
// En-tête : premières rangées (3 au plus) sans chiffre, ou dont les titres sont reconnus ; une rangée d'une seule cellule au-dessus
// est un titre. Sans en-tête reconnu, les colonnes restent « non reconnues » et toutes les rangées sont gardées : rien n'est
// abandonné, l'utilisateur affecte les colonnes. → {N (nomenclature, nature comprise), entete (vrai si au moins un titre reconnu)}
function depuisGrille(G,cles){const R=G.lignes,nc=Math.max(0,...R.map(r=>r.length)),ID=G.ids||[];
  // en-tête : 1re rangée (parmi les 10 premières) d'au moins 2 titres de natures différentes, sans valeur chiffrée ; les rangées
  // au-dessus forment le titre (cartouche, intitulé) ; les 2 suivantes la complètent si elles n'ont que des titres ou des unités
  const chiffre=v=>/\d/.test(norm(v).replace(/\(?(?<![a-z0-9])(mm|cm|m)(?![a-z0-9])\)?/g,'')),TT=G.titre?[G.titre]:[],E=[];
  const natR=r=>new Set(r.filter(v=>String(v||'').trim()&&!chiffre(v)).flatMap(v=>kinds(norm(v)).slice(0,1)));
  let e=-1;for(let i=0;i<Math.min(10,R.length-1);i++){const ne=R[i].filter(v=>String(v||'').trim());if(natR(R[i]).size>=2&&ne.filter(chiffre).length<=ne.length/3){e=i;break}}
  let h=0;
  if(e>=0){for(let i=0;i<e;i++)R[i].filter(v=>String(v||'').trim()).forEach(v=>TT.push(v));E.push(e);h=e+1;
    while(h<R.length-1&&E.length<3){const ne=R[h].filter(v=>String(v||'').trim());if(!ne.length||ne.some(chiffre)||!ne.every(v=>kinds(norm(v)).length||SOUS.test(norm(v))))break;E.push(h);h++}}
  // titre illisible : nature déduite des valeurs de la colonne (Ø…, l x h, repères) quand elles l'indiquent sans doute possible
  const VAL=R.slice(h).map(r=>r.map(v=>String(v||'').trim())),REPV=/^[A-Z]{1,3} ?\d{1,3}[A-Z]?$/i,deduite=j=>{const V=VAL.map(r=>r[j]||'').filter(v=>v&&!VIDE.test(norm(v)));if(!V.length)return null;
    const part=f=>V.filter(f).length/V.length;
    return part(v=>/^[øØ⌀∅] ?\d/.test(v))>=0.5?'diametre':part(v=>cotes(v,null).etat==='rect')>=0.5?'ouverture':part(v=>REPV.test(v))>=0.6?'repere':null};
  // titre de groupe fusionné sur n colonnes (« DIMENSIONS (mm) » puis « Hauteur Largeur » dans une seule cellule, titres vides à
  // droite, valeurs dessous) : les mots d'une ligne de n mots vont un par colonne, le groupe donne son unité ; la fonction de chaque
  // colonne vient de son sous-titre seul
  const TI=Array.from({length:nc},(x,j)=>E.map(i=>R[i][j]||'').filter(Boolean)),GP=[],val=j=>R.slice(h).some(r=>String(r[j]||'').trim());
  for(let j=0;j<nc;j++){let n=1;while(j+n<nc&&!TI[j+n].length&&val(j+n))n++;if(n<2)continue;
    const L=TI[j].join('\n').split('\n').map(x=>x.trim()).filter(Boolean);if(L.length<2)continue;
    const S=Array.from({length:n},()=>[]),reste=[];L.slice(1).forEach(l=>{const w=l.split(/\s+/);if(w.length===n)w.forEach((x,k)=>S[k].push(x));else reste.push(l)});
    if(!S[0].length)continue;for(let k=0;k<n;k++){TI[j+k]=S[k].concat(k?[]:reste);GP[j+k]=L[0]}j+=n-1}
  const colonnes=[];for(let j=0;j<nc;j++){const titre=TI[j].join('\n'),n=norm(titre),u=n.match(UNIT)||GP[j]&&norm(GP[j]).match(UNIT);let lu=kinds(n)[0]||'autre',dd=false;
    if(lu==='autre'){const x=deduite(j);if(x&&!(x==='repere'&&colonnes.some(c=>c.cle==='repere'))){lu=x;dd=true}}
    colonnes.push({titre:titre||'Colonne '+(j+1),cle:cles&&cles[j]||lu,cleLue:lu,unite:uCol(u),...(dd?{deduite:true}:{}),...(GP[j]?{groupe:GP[j]}:{})})}
  const entete=colonnes.some(c=>c.cleLue!=='autre'),titre=TT.join('\n'),nat=entete?nature(titre,colonnes):'autre',id=G.id||'G1';
  const lignes=[];R.slice(h).forEach((cells0,k)=>{const cells=colonnes.map((c,j)=>String(cells0[j]||'').trim());if(!cells.some(Boolean))return;
    const IDc=(ID[h+k]||[]).map(x=>x||[]),n=lignes.length+1;
    lignes.push(Object.assign({id:id+'-L'+String(n).padStart(2,'0'),rang:n,ids:IDc.flat(),calques:[]},ligne(colonnes,cells),{idsCellules:colonnes.map((c,j)=>IDc[j]||[])}))});
  const nR=lignes.filter(l=>l.repere).length,nA=colonnes.filter(c=>c.cle==='autre').length,motifs=['grille de traits lue, cellule par cellule'];
  if(!entete)motifs.push('en-tête non reconnu : colonnes à affecter');colonnes.filter(c=>c.deduite).forEach(c=>motifs.push(`colonne « ${c.titre.replace(/\n/g,' ')} » : ${LIB[c.cleLue]} déduit des valeurs (titre illisible)`));if(nR<lignes.length)motifs.push((lignes.length-nR)+' ligne(s) sans repère');if(nA)motifs.push(nA+' colonne(s) non reconnue(s), gardée(s) telles quelles');
  const U=[...new Set(colonnes.filter(c=>/^(ouverture|diametre|largeur|hauteur)$/.test(c.cle)).map(c=>c.unite).filter(Boolean))];
  return{entete,N:{id,fichier:G.fichier,format:G.format||'pdf',espace:G.espace||'papier',presentation:G.presentation||(G.page?'Page '+G.page:null),...(G.page?{page:G.page}:{}),
    titre,colonnes,cadre:G.cadre||null,...(G.rotation?{rotation:G.rotation}:{}),ids:ID.flat(2),nature:nat,calques:[],lignes,unite:U.length===1?U[0]:null,grille:true,
    qualite:{niveau:entete&&nR===lignes.length&&!nA?'bonne':'à vérifier',motifs}}}}

// Champs d'une ligne de tableau d'après ses cellules (une par colonne) : repère, désignation, type, observations, lot,
// quantité, niveau, angle, réseau, ouverture (textes) ; cotes lues par dimsLigne ; a_verifier (motifs). Sert aussi aux lignes
// reconnues par OCR puis corrigées par l'utilisateur (même contrat, mêmes règles).
function ligne(cols,cells){const av=[],cj=k=>cols.map((c,j)=>c.cle===k?j:-1).filter(j=>j>=0),v=key=>cj(key).map(j=>cells[j]).filter(Boolean).join(' — ');
  const L={cellules:cells,repere:(cj('repere').map(j=>cells[j]).find(Boolean)||'').replace(/\n/g,' '),description:v('description'),type:v('type'),observations:v('observations'),
    lot:v('lot'),quantite:v('quantite'),niveau:v('niveau'),angle:v('angle'),reseau:v('reseau'),ouverture:v('ouverture')||v('diametre'),dims:null,a_verifier:av};
  if(!L.repere)av.push(cj('repere').length?'repère absent de la ligne':'pas de colonne repère dans le tableau');
  const qn=L.quantite.replace(/\n/g,' ').trim(),qm=qn.match(/^(\d{1,4})\s*(u|ex|pcs?|pi[eè]ces?)?\.?$/i);L.nb=qm&&+qm[1]>0?+qm[1]:null;   // quantité du tableau : référence métier
  if(qn&&L.nb==null)av.push(`quantité « ${qn} » non lue comme un nombre entier`);
  const info={};L.dims=dimsLigne(cols,cells,av,info);if(info.dn)L.dn=info.dn;if(L.dims&&L.dims.unite)L.uniteOrigine=info.uniteOrigine||null;
  if(L.dims&&!L.dims.unite&&!L.dims.conflitUnite)av.push('unité des cotes non indiquée par le tableau');
  return L}

// Repère normalisé : majuscules, sans espaces ni séparateurs, zéros de tête des nombres retirés (D03 = D3 = d 3)
const cleRep=s=>sansAcc(s).toUpperCase().replace(/[\s._\-–—/]+/g,'').replace(/(^|[^0-9])0+(?=\d)/g,'$1');
function dansPoly(p,P){let c=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const a=P[i],b=P[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c}return c}
function dSeg(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],l=dx*dx+dy*dy,t=l?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)):0;return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)}
function dGeo(p,g){if(g.type==='cercle')return Math.max(0,Math.hypot(p[0]-g.centre[0],p[1]-g.centre[1])-g.r);
  const P=g.points;if(dansPoly(p,P))return 0;let d=Infinity;for(let i=0;i<P.length;i++)d=Math.min(d,dSeg(p,P[i],P[(i+1)%P.length]));return d}
// Cotes compatibles (mm) : 'ok' | 'diff' | '?' (unité inconnue ou cotes absentes) ; tolérance 1 % ou 2 mm ; kD = mm par unité du dessin
function compat(L,uT,c,kD){const d=L.dims;if(!d||!MM[d.unite||uT]||!(kD>0)||!c.dims)return'?';
  const kT=MM[d.unite||uT],eq=(x,y)=>Math.abs(x-y)<=Math.max(2,0.01*Math.max(x,y));
  if(d.type==='circ')return c.type==='circ'&&eq(d.D*kT,c.dims.D*kD)?'ok':'diff';
  return c.type==='rect'&&eq(Math.max(d.a,d.b)*kT,c.dims.L*kD)&&eq(Math.min(d.a,d.b)*kT,c.dims.l*kD)?'ok':'diff'}

// Rapprochement des lignes avec les géométries du détecteur (espace Objet d'un DXF ; page d'un PDF : textes et contours de la même
// page seulement). opt = {uniteDessin, unites:{idNomenclature:unité}, mm: candidat → mm par unité du dessin (PDF : échelle de la page)}
// → {idLigne: {statut, options:[{c (rang dans C), id, d, via, cotes}], reperes:[{x,y,id}], note}}
function associer(noms,C,doc,opt){
  const o=opt||{},pris=new Set(),idx={},papier={},kD=c=>o.mm?o.mm(c):MM[o.uniteDessin];
  const spT=t=>t.espace==='objet'?'o':t.page?'p'+t.page:null,spG=g=>g.espace!=='papier'?'o':g.page?'p'+g.page:null;   // espaces jamais mélangés
  noms.forEach(N=>N.ids.forEach(i=>pris.add(i)));(o.exclus||[]).forEach(i=>pris.add(i));
  (doc.textes||[]).forEach(t=>{if(pris.has(t.id))return;const k=new Set([cleRep(t.texte)]);t.texte.split(/[\s,;:()[\]]+/).forEach(x=>k.add(cleRep(x)));
    k.forEach(x=>{if(!x)return;if(spT(t))(idx[x]=idx[x]||[]).push(t);else(papier[x]=papier[x]||new Set()).add(t.presentation||'présentation')})});
  const geo=C.map((c,i)=>({c,i})).filter(x=>x.c.statut==='a_confirmer'&&x.c.geometrie&&spG(x.c.geometrie));
  const R={};
  noms.forEach(N=>{const uT=(o.unites||{})[N.id]||N.unite;N.lignes.forEach(L=>{const k=cleRep(L.repere),occ=k?idx[k]||[]:[],op={};
    occ.forEach(t=>{const P=[[t.x,t.y]].concat(t.fleches||[]),lim=4*t.h;
      geo.forEach(({c,i})=>{if(spG(c.geometrie)!==spT(t))return;const d=Math.min(...P.map(p=>dGeo(p,c.geometrie)));if(d<=lim&&(!op[i]||d<op[i].d))op[i]={c:i,id:c.id,d,via:'repere',cotes:compat(L,uT,c,kD(c))}})});
    // cotes compatibles d'abord (sinon tronquées au-delà des DXN_OPT premières propositions), puis distance
    const rg={ok:0,'?':1,diff:2};let options=Object.values(op).sort((a,b)=>rg[a.cotes]-rg[b.cotes]||a.d-b.d),statut,note='';
    const enPapier=k&&papier[k]?' ; repère présent dans une présentation (« '+[...papier[k]].join(' », « ')+' ») : lien non établi, fenêtre de présentation non interprétée':'';
    if(!occ.length){
      const M=L.dims?geo.filter(({c})=>compat(L,uT,c,kD(c))==='ok').map(({c,i})=>({c:i,id:c.id,d:null,via:'cotes',cotes:'ok'})):[];
      options=M;statut=M.length===1?'probable':M.length>1?'multiple':'absente';
      note=(k?'repère non trouvé dans '+(o.mm?'le dessin du PDF':'l\'espace Objet'):'ligne sans repère')+(M.length===1?' ; une seule géométrie de mêmes cotes':M.length>1?' ; '+M.length+' géométries de mêmes cotes':'')+enPapier}
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
  return{id:L.id,type:d.etat,statut:'a_confirmer',unite:'mm',source:{fichier:N.fichier,format:N.format||'dxf',calque:L.calques.join(', '),id:g?g.source.id:null},
    geometrie:null,centre:g?g.centre:null,dims:d.etat==='circ'?{D:d.D}:{L:Math.max(d.a,d.b),l:Math.min(d.a,d.b),angle:0},h:null,manquants:[],remarques:[]}}

// Provenance d'un ouvrage créé depuis une ligne (clé origineImport du plan). k = {forme, cotes (texte saisi), dims (mm), ref,
// uniteTableau, uniteChoisie, geo:{c: candidat, statut:'trouvee'|'choisie'} | null, rapprochement (PDF : rapprochement avec le dessin) | null}. Aucun contenu du DXF au-delà de la ligne.
// PDF : page, zone de page (points PDF, Y vers le haut : cadre du tableau, zone choisie ou zone de la saisie assistée) ;
// ligne saisie par l'utilisateur (N.saisie) : type 'saisie', ses textes sont les valeurs tapées ; ligne reconnue par OCR puis
// vérifiée (N.ocr) : type 'ocr', textes = valeurs retenues, ocr = {brut, confiance, corrections, corrige, incertain, ajoutee, moteur}.
function provenance(N,L,k){
  const textes={};N.colonnes.forEach((c,j)=>{const v=L.cellules[j];if(!v)return;let t=c.titre.replace(/\n/g,' ')||'colonne '+(j+1),n=2;const t0=t;while(t in textes)t=t0+' ('+(n++)+')';textes[t]=v});
  const d=L.dims,uT=d&&(d.unite||k.uniteTableau),kT=MM[uT],corrige=[];
  const mm=d&&kT?(d.type==='circ'?{etat:'circ',D:d.D*kT}:{etat:'rect',a:d.a*kT,b:d.b*kT}):null,eq=(x,y)=>Math.abs(x-y)<0.01;
  if(!mm||!k.dims||mm.etat!==k.dims.etat||(mm.etat==='circ'?!eq(mm.D,k.dims.D):!(eq(Math.max(mm.a,mm.b),Math.max(k.dims.a,k.dims.b))&&eq(Math.min(mm.a,mm.b),Math.min(k.dims.a,k.dims.b)))))corrige.push('cotes');
  if(String(k.ref||'')!==String(L.repere||'').toUpperCase())corrige.push('ref');
  if(k.nb!=null&&k.nb!==(L.nb||1))corrige.push('nb');
  const g=k.geo&&k.geo.c;
  const pdf=N.format==='pdf'?{page:N.page,zone:L.zone||N.zone||(N.cadre?{page:N.page,x0:N.cadre[0],y0:N.cadre[1],x1:N.cadre[2],y1:N.cadre[3],unite:'pt'}:null)}:{};
  return{fichier:N.fichier,format:N.format||'dxf',type:N.saisie?'saisie':N.ocr?'ocr':'nomenclature',espace:N.espace,presentation:N.presentation,calque:L.calques.join(', '),id:g?g.source.id:null,
    nomenclature:N.id,titre:N.titre,ligne:L.id,rang:L.rang,repere:L.repere,ids:L.ids.slice(),textes,
    unite_source:d?d.unite:null,unite_origine:d&&d.unite?L.uniteOrigine||null:null,unite:uT||null,dims_source:d?JSON.parse(JSON.stringify(d)):null,
    geometrie:g?{id:g.source.id,calque:g.source.calque,candidat:g.id,statut:k.geo.statut,unite:k.uniteDessin||null,centre:g.centre,dims_source:JSON.parse(JSON.stringify(g.dims))}:null,
    choix:{forme:k.forme,cotes:k.cotes,ref:k.ref||'',unite_tableau:k.uniteChoisie?k.uniteTableau:null,...(k.nb!=null?{nb:k.nb}:{})},corrige,
    quantite:{texte:L.quantite||'',tableau:L.nb==null?null:L.nb},a_verifier:L.a_verifier.slice(),h_saisie:true,...pdf,...(L.ocr?{ocr:JSON.parse(JSON.stringify(L.ocr))}:{}),...(k.rapprochement?{rapprochement:k.rapprochement}:{})};
}

root.CPI=Object.assign(root.CPI||{},{nomenclatures:{analyser,associer,cotes,ligne,nature,candidat,provenance,cleRep,dGeo,LIB,RAISON_TRAPPES,grilleTraits,depuisGrille,textesEnGrille,kinds:t=>kinds(norm(t)),tourne}});
})(typeof globalThis!=='undefined'?globalThis:this);
