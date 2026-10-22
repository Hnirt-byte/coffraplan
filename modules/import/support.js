// CoffraPlan — module d'import de plans, phase 9A : géométrie du SUPPORT d'une réservation (voile droit, voile circulaire).
// Trois notions séparées : forme de l'ouverture (rect, carré, circ), nature du support (voile droit, voile circulaire, autre,
// inconnu), solution de coffrage (jamais choisie ici : « a_determiner », pistes motivées seulement).
// Analyse LOCALE autour de l'observation (contour ou repère) : faces droites = lignes parallèles qui encadrent la réservation ;
// faces circulaires = arcs concentriques (ARC et polylignes à bulge d'un DXF, courbes de Bézier d'un PDF, chaînes de segments
// courts qui suivent un cercle). Valeurs en mm seulement avec une échelle fiable (ou une épaisseur cotée qui la donne) ; chaque
// valeur porte sa provenance (cote explicite, mesure, calcul, saisie) ; une valeur absente reste null, jamais supposée.
// Une proximité n'est jamais une certitude : validation_utilisateur_requise toujours vraie. Aucun seuil de taille d'ouverture :
// la flèche est calculée (fonction sag du moteur, reçue en paramètre, aucun calcul métier dupliqué) et comparée à une
// tolérance saisie. Indépendant de l'interface et du moteur. Charger après nomenclatures.js.
(function(root){'use strict';
const PI=Math.PI,TAU=2*PI,dist=(a,b)=>Math.hypot(b[0]-a[0],b[1]-a[1]),nang=a=>((a%TAU)+TAU)%TAU;
const ANG=2*PI/180;     // faces parallèles à 2° près ; côté d'un contour parallèle à une face
const AMBIGU=0.6;       // un 2e support (autre direction ou autre centre) étayé à 60 % du premier : ambigu, rien n'est choisi
const ACCORD=0.1;       // 10 % : cote écrite confirmée par la mesure, échelle cohérente avec les cotes du tableau
const MM={mm:1,cm:10,m:1000};
const r1=x=>x==null||!isFinite(x)?null:Math.round(x*10)/10;

// ---- courbes → arcs
const bz=(c,t)=>{const u=1-t;return[0,1].map(i=>u*u*u*c[0][i]+3*u*u*t*c[1][i]+3*u*t*t*c[2][i]+t*t*t*c[3][i])};
// cercle par 3 points (calcul dans le repère du 1er point : grandes coordonnées d'un DXF)
function cercle3(a,b,c){const bx=b[0]-a[0],by=b[1]-a[1],cx=c[0]-a[0],cy=c[1]-a[1],d=2*(bx*cy-by*cx);if(Math.abs(d)<1e-12*(bx*bx+by*by+cx*cx+cy*cy))return null;
  const B=bx*bx+by*by,C=cx*cx+cy*cy,x=(cy*B-by*C)/d,y=(bx*C-cx*B)/d;return{centre:[a[0]+x,a[1]+y],r:Math.hypot(x,y)}}
// arc par 3 points (début, milieu, fin) → {centre, r, a0, d} (d = ouverture dans le sens trigonométrique, 0 < d < 2π)
function arc3(s,m,e){const k=cercle3(s,m,e);if(!k)return null;const an=p=>Math.atan2(p[1]-k.centre[1],p[0]-k.centre[0]),a0=an(s),d=nang(an(e)-a0);
  return nang(an(m)-a0)<=d?Object.assign(k,{a0,d}):Object.assign(k,{a0:an(e),d:TAU-d})}
// Bézier cubiques [{id, c:[p0,c1,c2,p3]}] → {arcs, droits (pièces droites), autres (courbes non circulaires, points échantillonnés)}
function arcsBezier(C,eps){const arcs=[],droits=[],autres=[];
  (C||[]).forEach(({id,c})=>{const l=dist(c[0],c[3]),m=bz(c,0.5),dx=c[3][0]-c[0][0],dy=c[3][1]-c[0][1],f=l?Math.abs((m[0]-c[0][0])*dy-(m[1]-c[0][1])*dx)/l:dist(m,c[0]);
    if(f<=Math.max(1e-3*l,eps*0.05)){if(l>0)droits.push({id,a:c[0],b:c[3]});return}
    const a=l>0?arc3(c[0],m,c[3]):null,ok=a&&[0.25,0.75,0.125,0.875].every(t=>Math.abs(dist(bz(c,t),a.centre)-a.r)<=Math.max(0.005*a.r,eps*0.05));
    if(ok)arcs.push(Object.assign(a,{id,source:'bezier'}));else autres.push({id,pts:[0,0.25,0.5,0.75,1].map(t=>bz(c,t))})});
  return{arcs,droits,autres}}
// Chaînes de segments courts bout à bout (courbe aplatie par la DAO) : suites d'au moins 5 segments qui tournent toujours du même
// côté (0,05° à 30° par sommet) ; sur un cercle (écart ≤ 0,5 % du rayon) → arc ; sinon courbe non circulaire. → {arcs, autres, pris}
function arcsChaines(S,eps){const G=new Map(),N=[],key=p=>Math.round(p[0]/eps)+','+Math.round(p[1]/eps);
  const nd=p=>{const k=key(p);let i=G.get(k);if(i==null){i=N.length;G.set(k,i);N.push({p,e:[]})}return i};
  S.forEach((s,j)=>{const u=nd(s.a),v=nd(s.b);if(u!==v){N[u].e.push([v,j]);N[v].e.push([u,j])}});
  const vu=new Set(),arcs=[],autres=[],pris=new Set();
  const suite=(a,j0)=>{const P=[a],J=[];let cur=a,j=j0;for(;;){if(vu.has(j))break;vu.add(j);J.push(j);const e=N[cur].e.find(x=>x[1]===j),nx=e[0];P.push(nx);
      if(N[nx].e.length!==2)break;const f=N[nx].e.find(x=>x[1]!==j);cur=nx;j=f[1]}return{P,J}};
  const bouts=N.map((n,i)=>i).filter(i=>N[i].e.length!==2);
  const traiter=(P,J)=>{const Q=P.map(i=>N[i].p),hd=[];for(let i=0;i+1<Q.length;i++)hd.push(Math.atan2(Q[i+1][1]-Q[i][1],Q[i+1][0]-Q[i][0]));
    let i=0;while(i<hd.length-1){const sg=Math.sign(dang(hd[i],hd[i+1]));let k=i;
      while(k<hd.length-1){const t=dang(hd[k],hd[k+1]);if(Math.sign(t)!==sg||Math.abs(t)<0.05*PI/180||Math.abs(t)>30*PI/180)break;k++}
      if(sg&&k-i+1>=5){const R=Q.slice(i,k+2),a=arc3(R[0],R[R.length>>1],R[R.length-1]),js=J.slice(i,k+1);
        if(a&&R.every(q=>Math.abs(dist(q,a.centre)-a.r)<=Math.max(0.005*a.r,eps))){arcs.push(Object.assign(a,{id:'chaine:'+js.map(j=>S[j].id).slice(0,3).join('+'),source:'chaine'}));js.forEach(j=>pris.add(j))}
        else autres.push({id:'chaine:'+S[J[i]].id,pts:R})}
      i=Math.max(k,i+1)}};
  bouts.forEach(a=>N[a].e.forEach(([,j])=>{if(!vu.has(j)){const {P,J}=suite(a,j);if(J.length>=5)traiter(P,J)}}));
  N.forEach((n,a)=>n.e.forEach(([,j])=>{if(!vu.has(j)){const {P,J}=suite(a,j);if(J.length>=5)traiter(P,J)}}));   // boucles fermées
  return{arcs,autres,pris}}
const dang=(a,b)=>{let d=b-a;while(d>PI)d-=TAU;while(d<=-PI)d+=TAU;return d};
const angEcart=(a,b)=>{const d=Math.abs(nang(a)-nang(b))%PI;return Math.min(d,PI-d)};
const dansArc=(A,f)=>nang(f-A.a0)<=A.d;

// ---- environnement graphique, selon le format
// PDF : sortie de CPI.pdf.chemins (segments, courbes Bézier ; points, Y vers le haut) et textes de la page
function envPdf(geo,textes){return{unite:'pt',segments:geo.segments||[],courbes:geo.courbes||[],arcs:[],textes:textes||[],coupe:!!(geo.coupe||geo.coupeCourbes)}}
// DXF : document de CPI.dxf.decoder (traits, arcs, traits des polylignes à arcs) d'un espace (objet, ou présentation nommée)
function envDxf(doc,sel){sel=sel||{espace:'objet',presentation:null};const ok=x=>x.espace===sel.espace&&(sel.espace==='objet'||x.presentation===sel.presentation);
  const S=(doc.traits||[]).concat(doc.traitsArcs||[]).filter(ok).map((s,i)=>({id:s.id||'t'+i,a:s.a,b:s.b}));
  return{unite:doc.unite,segments:S,courbes:[],arcs:(doc.arcs||[]).filter(ok),textes:(doc.textes||[]).filter(ok),coupe:(doc.signalements||[]).some(m=>/très chargé/.test(m))}}

// ---- recherche des faces
// projection d'une liste de points sur une direction u → [min, max]
const proj=(P,o,u)=>{let a=Infinity,b=-Infinity;P.forEach(q=>{const t=(q[0]-o[0])*u[0]+(q[1]-o[1])*u[1];if(t<a)a=t;if(t>b)b=t});return[a,b]};
// longueur d'intervalles [t0,t1] hors de [x0,x1] et dans [-W,W]
function couv(I,x0,x1,W){const J=I.map(([a,b])=>[Math.max(a,-W),Math.min(b,W)]).filter(([a,b])=>b>a).sort((p,q)=>p[0]-q[0]),M=[];
  J.forEach(i=>{const l=M[M.length-1];if(l&&i[0]<=l[1])l[1]=Math.max(l[1],i[1]);else M.push(i.slice())});
  let s=0,g=0,d=0;M.forEach(([a,b])=>{const ga=Math.max(0,Math.min(b,x0)-a),dr=Math.max(0,b-Math.max(a,x1));g+=ga;d+=dr;s+=ga+dr});return{tot:s,g,d}}
// Faces droites : lignes (segments colinéaires réunis) de directions dirs (null : toutes), de part et d'autre du point p ;
// paire adjacente par direction (la plus proche de chaque côté, assez longue hors de la réservation)
function droites(p,S,dirs,K,eps,W){const D=[],out=[];
  S.forEach(s=>{const dx=s.b[0]-s.a[0],dy=s.b[1]-s.a[1],l=Math.hypot(dx,dy);if(!(l>eps))return;const th=nang(Math.atan2(dy,dx))%PI;
    if(dirs&&!dirs.some(d=>angEcart(th,d)<=ANG))return;let g=D.find(x=>angEcart(x.th,th)<=ANG);
    if(!g){g={th,u:[Math.cos(th),Math.sin(th)],S:[]};g.n=[-g.u[1],g.u[0]];D.push(g)}g.S.push(s)});
  D.forEach(g=>{const L=[];
    g.S.forEach(s=>{const off=((s.a[0]+s.b[0])/2-p[0])*g.n[0]+((s.a[1]+s.b[1])/2-p[1])*g.n[1],t=proj([s.a,s.b],p,g.u);let x=L.find(y=>Math.abs(y.off-off)<=eps);
      if(!x){x={off,I:[],ids:[]};L.push(x)}x.I.push(t);x.ids.push(s.id)});
    const [w0,w1]=K.length?proj(K,p,g.u):[0,0],[c0,c1]=K.length?proj(K,p,g.n):[0,0];
    L.forEach(x=>x.cv=couv(x.I,w0-eps,w1+eps,W));
    const assez=x=>x.cv.tot>=0.5*Math.max(eps,Math.min(W,Math.abs(x.off)*2));   // une face continue au-delà de l'ouverture
    // faces : lignes de part et d'autre de p, hors du contour (une ligne qui traverse l'ouverture est un axe ou une cote)
    const neg=L.filter(x=>x.off<0&&x.off<=c0+eps&&assez(x)).sort((a,b)=>b.off-a.off),pos=L.filter(x=>x.off>0&&x.off>=c1-eps&&assez(x)).sort((a,b)=>a.off-b.off);
    if(!neg.length||!pos.length)return;const a=neg[0],b=pos[0],t=b.off-a.off,tol=eps+0.02*t;
    if(c0<a.off-tol||c1>b.off+tol)return;   // la réservation déborde de la bande : pas ce support
    const trav=K.length>2&&Math.abs(c0-a.off)<=tol&&Math.abs(c1-b.off)<=tol;
    // quadrillage (tableau, cartouche) : au moins 5 lignes de cette direction régulièrement espacées dans la fenêtre
    const Lg=L.filter(x=>x.cv.tot>=0.5*Math.min(a.cv.tot,b.cv.tot)).map(x=>x.off).sort((u,v)=>u-v),ec=Lg.slice(1).map((v,i)=>v-Lg[i]),m=ec.reduce((s,v)=>s+v,0)/(ec.length||1);
    const grille=Lg.length>=5&&ec.every(e=>Math.abs(e-m)<=0.15*m);
    out.push({type:'voile_droit',classe:trav?2:1,score:Math.min(a.cv.tot,b.cv.tot),dir:g.th,u:g.u,n:g.n,t,faces:[a,b],
      w:w1-w0,bord:!(a.cv.g>0&&a.cv.d>0||b.cv.g>0&&b.cv.d>0),autres:L.filter(x=>x!==a&&x!==b&&assez(x)&&(x.off<a.off||x.off>b.off)).length,grille})});
  return out}
// Faces circulaires : arcs de même centre (à 0,5 % du rayon), rayons de part et d'autre du point p, arcs présents près de p
function circulaires(p,A,K,eps,W){const G=[],out=[];
  // même centre à 1 % du rayon près : les faces d'une même paroi lues autrement (Bézier, chaîne de segments) ont des centres ajustés
  // légèrement différents (constaté sur un plan réel : 0,5 pt pour un rayon de 65 pt)
  A.slice().sort((a,b)=>b.d*b.r-a.d*a.r).forEach(a=>{if(!(a.r>eps))return;let g=G.find(x=>dist(x.c,a.centre)<=eps+0.01*Math.max(x.r,a.r));if(!g){g={c:a.centre,r:a.r,A:[]};G.push(g)}g.A.push(a)});   // centre du groupe : celui de l'arc le plus long
  G.forEach(g=>{const c=g.c,rho=dist(p,c),phi=Math.atan2(p[1]-c[1],p[0]-c[0]);if(!(rho>eps))return;
    const R=[];g.A.forEach(a=>{let x=R.find(y=>Math.abs(y.r-a.r)<=eps+0.002*a.r);if(!x){x={r:a.r,A:[]};R.push(x)}x.A.push(a)});
    // positions le long de la paroi en longueur d'arc au rayon de p ; réservation : étendue angulaire de son contour
    const ang=q=>dang(phi,Math.atan2(q[1]-c[1],q[0]-c[0]))*rho,[w0,w1]=K.length?(()=>{let a=Infinity,b=-Infinity;K.forEach(q=>{const t=ang(q);if(t<a)a=t;if(t>b)b=t});return[a,b]})():[0,0];
    const rr=K.map(q=>dist(q,c)),c0=K.length?Math.min(...rr):rho,c1=K.length?Math.max(...rr):rho;
    R.forEach(x=>{const I=[];x.A.forEach(a=>{const s=dang(phi,a.a0);if(a.d>=TAU-1e-9){I.push([-PI*rho,PI*rho]);return}I.push([s*rho,(s+a.d)*rho]);if(s+a.d>PI)I.push([(s-TAU)*rho,(s+a.d-TAU)*rho])});
      x.cv=couv(I,w0-eps,w1+eps,W)});
    const assez=x=>x.cv.tot>=0.5*Math.max(eps,Math.min(W,Math.abs(x.r-rho)*2));
    const ins=R.filter(x=>x.r<rho-eps&&assez(x)).sort((a,b)=>b.r-a.r),ext=R.filter(x=>x.r>rho+eps&&assez(x)).sort((a,b)=>a.r-b.r);
    // largeur de l'ouverture suivant la paroi : corde (projection du contour sur la tangente en p)
    const ut=[-Math.sin(phi),Math.cos(phi)],[q0,q1]=K.length?proj(K,p,ut):[0,0];
    if(!ins.length||!ext.length)return;const a=ins[0],b=ext[0],t=b.r-a.r,w=q1-q0,sg=(r,l)=>l/2<r?r-Math.sqrt(r*r-l*l/4):r,tol=eps+0.02*t+sg(a.r,w);
    if(c0<a.r-tol||c1>b.r+tol)return;
    const trav=K.length>2&&Math.abs(c0-a.r)<=tol&&Math.abs(c1-b.r)<=eps+0.02*t;
    out.push({type:'voile_circulaire',classe:trav?2:1,score:Math.min(a.cv.tot,b.cv.tot),centre:c,ri:a.r,re:b.r,t,faces:[a,b],w,u:[-Math.sin(phi),Math.cos(phi)],
      bord:!(a.cv.g>0&&a.cv.d>0||b.cv.g>0&&b.cv.d>0),sources:[...new Set(a.A.concat(b.A).map(z=>z.source||'arc'))]})});
  return out}

// ---- textes : cotes d'épaisseur, rayons, diamètres
const NUM='(\\d+(?:[.,]\\d+)?)',UN='\\s*(mm|cm|m)?\\b';
const nb=s=>+String(s).replace(',','.');
const RX_EP=/(?:^|[^\p{L}])(?:ep|ép|epaisseur|épaisseur)\.?\s*(?:voile\s*)?[:=]?\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?(?![\p{L}\d])/iu;
const RX_R=new RegExp('^(?:R|rayon|R\\.?\\s*int\\.?|R\\.?\\s*ext\\.?|rayon\\s+(?:int|ext)\\w*)\\s*(?:[:=]\\s*'+NUM+UN+'|\\s'+NUM+'\\s*(mm|cm|m)\\b)\\s*$','i');
const RX_D=new RegExp('^(?:Ø|diam\\.?|diametre|diamètre)\\s*(?:cuve\\s*)?[:=]?\\s*'+NUM+UN+'\\s*$','i');
function lireR(s){const m=String(s).trim().match(RX_R);if(!m)return null;const v=m[1]!=null?nb(m[1]):nb(m[3]),u=m[1]!=null?m[2]:m[4];
  return{v,unite:u||null,face:/int/i.test(s)?'int':/ext/i.test(s)?'ext':null}}
function lireD(s){const m=String(s).trim().match(RX_D);return m?{v:nb(m[1]),unite:m[2]||null}:null}
// valeur écrite (unité écrite, sinon mm / cm / m) confirmée par une mesure en mm → unité retenue | null
const accord=(v,u,mes)=>!(mes>0)?null:(u?[u]:['mm','cm','m']).find(x=>Math.abs(v*MM[x]-mes)<=ACCORD*mes)||null;

// ---- nomenclature : cotes de l'ouverture et indications sur le support (cellules, désignation)
function ligneInfo(L){if(!L)return null;const d=L.dims||null,u=d&&!d.conflitUnite?d.unite||null:null,txt=[L.description||''].concat(L.cellules||[]).join(' | ');
  const ep=txt.match(RX_EP),R=txt.match(/\b(?:rayon|R)\s*(?:int\w*|ext\w*)?\s*[:=]\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\b/i),D=txt.match(/(?:Ø|diam\w*)\s*cuve\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\b/i);
  return{d,u,texte:txt,ep:ep?{v:nb(ep[1]),unite:ep[2]||u,texte:ep[0]}:null,R:R?{v:nb(R[1]),unite:R[2]||u,texte:R[0]}:null,Dc:D?{v:nb(D[1]),unite:D[2]||null,texte:D[0]}:null,
    courbe:/\b(cintr\w*|circulaire|courbe|cuve)\b/i.test(txt),droit:/\bvoile\s+droit\b/i.test(txt),colonnes:!!(d&&d.colonne&&/larg/i.test(d.colonne)&&/haut/i.test(d.colonne))}}

// ---- analyse d'une observation
// obs = {repere, candidat (contour de CPI.geometrie / CPI.detecteur) | null, point:[x,y] (repère seul), h (hauteur du texte), page, vue:{id,type,titre}|null}
// env = envPdf / envDxf ; o = {k (mm par unité du dessin) | null, echelle:{source, texte, autres:[{k,source}]}, ligne (nomenclature, association
//   fiable seulement), saisie:{epaisseur_mm, rayon_interieur_mm, largeur_suivant_paroi_mm, hauteur_mm}, tolerance_mm, sag (GEO.sag du moteur),
//   cadres:[[x0,y0,x1,y1]] (tableaux, cartouche), eps, fenetre (demi-côté, unité du dessin), repris (contour écarté par le repérage, repris : motif)}
function analyser(obs,env,o){o=o||{};const c=obs.candidat||null,g=c&&c.geometrie,inc=[],pv=[],prov={};
  const R={repere:obs.repere||null,observation:{page:obs.page||(c&&c.source&&c.source.page)||null,contour:c?c.id:null,forme_dessin:c?c.type:null,vue:obs.vue?{id:obs.vue.id,type:obs.vue.type,titre:obs.vue.titre||null}:null},
    ouverture:{type:null,largeur_mm:null,hauteur_mm:null,diametre_mm:null,largeur_suivant_paroi_mm:null},
    support:{type:'inconnu',epaisseur_mm:null,rayon_interieur_mm:null,rayon_exterieur_mm:null,confiance:null},
    coffrage:{solution_proposee:'a_determiner',pistes:[],fleche_interieure_mm:null,fleche_exterieure_mm:null,tolerance_mm:null},
    correspondance_voile:null,provenance:prov,preuves:pv,incertitudes:inc,validation_utilisateur_requise:true};
  const fin=()=>{if(!R.coffrage.pistes.length)pistes(R);R.incertitudes=[...new Set(inc)];return R};
  const p=c&&c.centre?c.centre:obs.point;if(!p)return(inc.push('observation sans position : rien à analyser'),fin());
  const K=g?g.type==='cercle'?Array.from({length:16},(x,i)=>[g.centre[0]+g.r*Math.cos(i*PI/8),g.centre[1]+g.r*Math.sin(i*PI/8)]):g.points||[]:[];
  const bb=K.length?[Math.min(...K.map(q=>q[0])),Math.min(...K.map(q=>q[1])),Math.max(...K.map(q=>q[0])),Math.max(...K.map(q=>q[1]))]:null;
  const s=bb?Math.max(bb[2]-bb[0],bb[3]-bb[1]):3*Math.max(obs.h||1,1),eps=o.eps>0?o.eps:0.01*s,W=o.fenetre>0?o.fenetre:6*s;
  // textes de la fenêtre élargie (cotes d'épaisseur, rayons) ; contexte des fonctions de valeurs
  o._p=p;o._env=Object.assign({},env,{textes:(env.textes||[]).filter(t=>Math.abs(t.x-p[0])<=2*W&&Math.abs(t.y-p[1])<=2*W)});
  const L=ligneInfo(o.ligne);
  // ouverture : forme et cotes du tableau (référence), sinon du dessin
  ouverture(R,L,c,prov,inc);
  if(c&&c.statut&&c.statut!=='a_confirmer'){const m=c.remarques&&c.remarques.length?' ('+c.remarques[0]+')':'';
    if(!o.repris){inc.push('contour écarté par le repérage'+m+' : support non analysé');return fin()}
    inc.push('contour écarté par le repérage'+m+', repris pour l\'analyse du support seulement (le plus proche du repère) : rattachement à confirmer')}
  const dansCadre=(o.cadres||[]).some(b=>p[0]>=b[0]&&p[0]<=b[2]&&p[1]>=b[1]&&p[1]<=b[3]);
  if(dansCadre){inc.push('observation dans un tableau ou un cartouche : support non analysé');return fin()}
  const vt=obs.vue&&obs.vue.type;
  if(vt==='elevation'){inc.push('vue en élévation : l\'épaisseur du support n\'y est pas visible, support non analysé sur cette vue');return fin()}
  // vue de ferraillage : les armatures dessinées sont des lignes parallèles (constaté sur un plan réel : faux voile entre deux aciers)
  if(vt&&/^ferraillage/.test(vt)){inc.push('vue de ferraillage : armatures dessinées en lignes parallèles, support non analysé sur cette vue');return fin()}
  if(vt==='detail')inc.push('vue de détail : échelle propre à la vue, à vérifier');
  if(env.coupe)inc.push('géométrie partiellement extraite (plafond de lecture atteint) : relire localement autour de la réservation (CPI.pdf.chemins avec zones)');
  // environnement local : fenêtre autour de p, hors tableaux, sans le contour de la réservation elle-même
  const box=[p[0]-W,p[1]-W,p[0]+W,p[1]+W],inB=q=>q[0]>=box[0]&&q[0]<=box[2]&&q[1]>=box[1]&&q[1]<=box[3],cad=o.cadres||[];
  const horsCad=q=>!cad.some(b=>q[0]>=b[0]&&q[0]<=b[2]&&q[1]>=b[1]&&q[1]<=b[3]);
  const surK=q=>K.length>2&&(g.type==='cercle'?Math.abs(dist(q,g.centre)-g.r)<=eps:K.some((a,i)=>dseg(q,a,K[(i+1)%K.length])<=eps));
  const coupeBox=(a,b)=>!(Math.max(a[0],b[0])<box[0]||Math.min(a[0],b[0])>box[2]||Math.max(a[1],b[1])<box[1]||Math.min(a[1],b[1])>box[3]);
  let S=env.segments.filter(sg=>coupeBox(sg.a,sg.b)&&horsCad(sg.a)&&horsCad(sg.b)&&!(surK(sg.a)&&surK(sg.b)));
  const CB=(env.courbes||[]).filter(x=>x.c.some(inB)&&x.c.every(horsCad)),B=arcsBezier(CB,eps);
  S=S.concat(B.droits.filter(sg=>!(surK(sg.a)&&surK(sg.b))));
  const CH=arcsChaines(S,eps);S=S.filter((x,j)=>!CH.pris.has(j));
  const propre=a=>g&&g.type==='cercle'&&dist(a.centre,g.centre)<=eps&&Math.abs(a.r-g.r)<=eps;
  const A=(env.arcs||[]).filter(a=>!propre(a)&&dist(p,a.centre)-a.r<=W+eps&&a.r-dist(p,a.centre)<=W+eps).concat(B.arcs.filter(a=>!propre(a)),CH.arcs);
  const NC=B.autres.concat(CH.autres).filter(x=>x.pts.some(q=>dist(q,p)<=2*s));
  // candidats : faces droites (côtés du contour seulement pour un rectangle), faces circulaires
  const dirs=c&&c.type==='rect'&&c.dims&&c.dims.angle!=null?[c.dims.angle*PI/180,c.dims.angle*PI/180+PI/2]:null;
  const Cd=droites(p,S,dirs,K,eps,W),grilles=Cd.filter(x=>x.grille),cand=Cd.filter(x=>!x.grille).concat(circulaires(p,A,K,eps,W));
  grilles.forEach(x=>pv.push({type:'quadrillage_ecarte',detail:'lignes parallèles régulièrement espacées (tableau, cartouche ?) : pas un voile',direction_deg:r1(x.dir*180/PI)}));
  cand.sort((a,b)=>b.classe-a.classe||b.score-a.score);
  const best=cand[0];
  if(!best){
    if(NC.length){R.support.type='autre';R.support.confiance='faible';inc.push('parois courbes non circulaires près de la réservation (ellipse, spline ?) : rayon non défini, support à préciser');
      pv.push({type:'courbe_non_circulaire',ids:NC.slice(0,6).map(x=>x.id)})}
    else inc.push('aucune paroi reconnue autour de la réservation (faces parallèles ou arcs concentriques) : support inconnu');
    return valeurs(R,L,null,o,inc,pv,prov),fin()}
  // rival : autre type, autre direction, ou autre paroi circulaire (centre ou rayons différents à 2 % près)
  const meme=(x,y)=>dist(x.centre,y.centre)<=eps+0.02*y.re&&Math.abs(x.ri-y.ri)<=eps+0.02*y.ri&&Math.abs(x.re-y.re)<=eps+0.02*y.re;
  const rival=cand.slice(1).find(x=>x.classe===best.classe&&x.score>=AMBIGU*best.score&&(x.type!==best.type||(x.type==='voile_droit'?angEcart(x.dir,best.dir)>ANG:!meme(x,best))));
  pv.push(...cand.slice(0,3).map(preuve));
  if(rival){R.support.type='inconnu';inc.push(`deux supports possibles (${best.type} et ${rival.type}) : à choisir par l'utilisateur`);return valeurs(R,L,null,o,inc,pv,prov),fin()}
  // réservation entre deux faces sans aller de l'une à l'autre : simple voisinage (pièce entre deux murs, vue en élévation, réservation de
  // dalle…) : jamais un support, la bande est seulement signalée
  if(best.classe===1){R.support.type='inconnu';const kk=o.k>0?o.k:null;
    pv.push({type:'bande_possible',support:best.type,ecart_unite:r1(best.t),ecart_mm:kk?r1(best.t*kk):null});
    inc.push(`réservation entre deux ${best.type==='voile_droit'?'lignes parallèles':'arcs concentriques'} sans aller de l'une à l'autre`+(kk?` (écart ${Math.round(best.t*kk)} mm)`:'')+' : voile possible, pièce entre deux murs, vue en élévation ou réservation de dalle ; support à préciser');
    return valeurs(R,L,null,o,inc,pv,prov),fin()}
  R.support.type=best.type;R.support.confiance='moyenne';
  if(best.bord)inc.push('faces présentes d\'un seul côté de la réservation (extrémité de voile, angle, ou lignes de cote alignées sur le contour ?) : support à confirmer');
  if(best.autres)inc.push('autres lignes parallèles à la paroi (doublage, isolation, cote ?) : épaisseur à confirmer');
  if(NC.length&&best.type==='voile_droit')inc.push('courbes non circulaires à proximité : paroi courbe possible');
  if(L&&L.courbe&&best.type==='voile_droit')inc.push('la nomenclature mentionne un ouvrage courbe (cintré, circulaire, cuve) et le dessin montre une paroi droite : à vérifier');
  if(L&&L.droit&&best.type==='voile_circulaire')inc.push('la nomenclature mentionne un voile droit et le dessin montre une paroi circulaire : à vérifier');
  valeurs(R,L,best,o,inc,pv,prov);
  // contour repris (écarté par le repérage, choisi par proximité du repère) : support seulement possible (constaté sur un plan réel :
  // gaine ou autre contour voisin pris pour la réservation) ; valeurs gardées dans la preuve, jamais dans le résultat ;
  // faces d'un seul côté : extrémité de voile possible, mais aussi lignes de cote alignées sur le contour (constaté sur un plan réel)
  if(o.repris||best.bord){const S=R.support;pv.push({type:'support_possible',support:S.type,epaisseur_mm:S.epaisseur_mm,rayon_interieur_mm:S.rayon_interieur_mm,
      fleche_interieure_mm:R.coffrage.fleche_interieure_mm,provenance:prov['support.epaisseur_mm']||null});
    inc.push(`support possible : ${S.type}${S.epaisseur_mm?' ép. '+S.epaisseur_mm+' mm':''}, d'après ${o.repris?'un contour repris':'des faces d\'un seul côté'} : à confirmer`);
    R.support={type:'inconnu',epaisseur_mm:null,rayon_interieur_mm:null,rayon_exterieur_mm:null,confiance:null};R.correspondance_voile=null;
    Object.assign(R.coffrage,{pistes:[],fleche_interieure_mm:null,fleche_exterieure_mm:null});
    Object.keys(prov).forEach(k=>{if(/^support\.|^coffrage\.fleche/.test(k))delete prov[k]});return fin()}
  if(R.support.confiance==='moyenne'&&prov['support.epaisseur_mm']&&prov['support.epaisseur_mm'].origine==='cote_explicite'&&!inc.some(m=>/échelle incohérente|échelle déduite|conflit/.test(m)))R.support.confiance='forte';
  return fin()}
function dseg(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],l=dx*dx+dy*dy,t=l?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)):0;return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)}
const preuve=x=>x.type==='voile_droit'?{type:'faces_paralleles',direction_deg:r1(x.dir*180/PI),ecart_unite:r1(x.t),traverse:x.classe===2,longueur_hors_ouverture:r1(x.score),traits:x.faces.map(f=>f.ids.slice(0,4))}
  :{type:'arcs_concentriques',centre:x.centre.map(r1),rayons_unite:[r1(x.ri),r1(x.re)],traverse:x.classe===2,longueur_hors_ouverture:r1(x.score),sources:x.sources,arcs:x.faces.map(f=>f.A.slice(0,4).map(a=>a.id))};

// forme et cotes de l'ouverture (mm) : nomenclature (cotes explicites), sinon contour mesuré plus tard
function ouverture(R,L,c,prov,inc){const O=R.ouverture,d=L&&L.d;
  if(d&&(d.type==='circ'||d.type==='rect')){const k=MM[L.u];
    if(!k){inc.push('unité des cotes du tableau inconnue : cotes de l\'ouverture non converties');O.type=d.type==='circ'?'circ':Math.abs(d.a-d.b)<1e-9?'carre':'rect';prov['ouverture.type']={origine:'cote_explicite',source:'nomenclature'};return}
    if(d.type==='circ'){O.type='circ';O.diametre_mm=d.D*k;prov['ouverture.diametre_mm']={origine:'cote_explicite',source:'nomenclature',detail:d.texte||null}}
    else{O.type=Math.abs(d.a-d.b)<1e-9?'carre':'rect';if(L.colonnes){O.largeur_mm=d.a*k;O.hauteur_mm=d.b*k;prov['ouverture.largeur_mm']=prov['ouverture.hauteur_mm']={origine:'cote_explicite',source:'nomenclature',detail:'colonnes '+d.colonne}}}
    prov['ouverture.type']={origine:'cote_explicite',source:'nomenclature'};return}
  if(c&&(c.type==='rect'||c.type==='circ')){O.type=c.type==='circ'?'circ':c.dims&&Math.abs(c.dims.L-c.dims.l)<=1e-6*c.dims.L?'carre':'rect';prov['ouverture.type']={origine:'mesure',source:'dessin'};
    inc.push('forme de l\'ouverture lue sur le dessin (aucune ligne de nomenclature associée) : en plan, une traversée circulaire peut être dessinée en rectangle')}}

// valeurs en mm : échelle, épaisseur, rayons, largeur suivant la paroi, orientation, flèches, pistes
function valeurs(R,L,b,o,inc,pv,prov){const O=R.ouverture,Sp=R.support,sa=o.saisie||{},d=L&&L.d,kd=L&&MM[L.u];
  let k=o.k>0?o.k:null,kS=k?`${+k.toPrecision(5)} mm par unité (${(o.echelle&&o.echelle.source)||'échelle fournie'})`:null;
  if(k&&o.echelle&&(o.echelle.autres||[]).some(x=>x.k>0&&Math.abs(x.k-k)>0.02*k)){inc.push('échelle incohérente : deux échelles différentes pour cette vue ('+[o.echelle.source].concat(o.echelle.autres.map(x=>x.source)).join(', ')+') : mesures non utilisées');k=null}
  if(!k&&!(o.k>0))inc.push('échelle absente : aucune mesure convertie en mm');
  // épaisseur explicite (saisie, nomenclature), puis cohérence de l'échelle avec les cotes du tableau
  const epS=sa.epaisseur_mm>0?sa.epaisseur_mm:null,epN=L&&L.ep&&MM[L.ep.unite]?L.ep.v*MM[L.ep.unite]:null;
  if(L&&L.ep&&!MM[L.ep.unite])inc.push(`épaisseur « ${L.ep.texte} » dans la nomenclature sans unité : non utilisée`);
  if(b&&k&&d&&kd&&b.classe===2){const w=b.w*k,cand=d.type==='circ'?[d.D*kd]:[d.a*kd,d.b*kd];
    if(!cand.some(v=>Math.abs(v-w)<=ACCORD*v)){inc.push(`échelle incohérente : largeur mesurée ${Math.round(w)} mm, cotes du tableau ${cand.map(Math.round).join(' × ')} mm (vue de détail, autre échelle ?) : mesures non utilisées`);k=null}}
  // sans échelle fiable : échelle déduite d'une épaisseur explicite (paroi traversée de face à face seulement)
  const epX=epS||epN;let kDed=false;
  if(!k&&b&&b.classe===2&&epX){k=epX/b.t;kDed=true;kS=`${+k.toPrecision(5)} mm par unité (déduite de l'épaisseur `+(epS?'saisie)':'de la nomenclature)');inc.push('mesures calculées avec une échelle déduite de l\'épaisseur '+(epS?'saisie':'de la nomenclature')+' : à vérifier')}
  if(!b){if(epS){Sp.epaisseur_mm=epS;prov['support.epaisseur_mm']={origine:'saisie'}}else if(epN){Sp.epaisseur_mm=epN;prov['support.epaisseur_mm']={origine:'cote_explicite',source:'nomenclature',detail:L.ep.texte}}
    largeur(R,L,null,null,o,inc,prov);return}
  const tMes=k&&!kDed?b.t*k:null;
  // cotes écrites dans la fenêtre : épaisseur près de la paroi, rayon / diamètre
  const T=o._env.textes;
  // épaisseur
  if(epS){Sp.epaisseur_mm=epS;prov['support.epaisseur_mm']={origine:'saisie'};if(tMes&&Math.abs(tMes-epS)>ACCORD*epS)inc.push(`épaisseur saisie ${epS} mm, mesurée ${Math.round(tMes)} mm : à vérifier`)}
  else{const ct=cotesEp(b,T,o,tMes);ct.forEach(x=>pv.push(x.preuve));const ok=ct.find(x=>x.mm!=null);
    if(epN&&ok&&Math.abs(ok.mm-epN)>ACCORD*epN){inc.push(`conflit d'épaisseur : nomenclature ${epN} mm, cote du dessin ${ok.mm} mm`);}
    else if(ok){Sp.epaisseur_mm=ok.mm;prov['support.epaisseur_mm']={origine:'cote_explicite',source:'dessin',detail:`« ${ok.texte} » confirmée par la mesure (${Math.round(tMes)} mm)`}}
    else if(epN){Sp.epaisseur_mm=epN;prov['support.epaisseur_mm']={origine:'cote_explicite',source:'nomenclature',detail:L.ep.texte};if(tMes&&Math.abs(tMes-epN)>ACCORD*epN)inc.push(`épaisseur de la nomenclature ${epN} mm, mesurée ${Math.round(tMes)} mm : à vérifier`)}
    else if(tMes){Sp.epaisseur_mm=r1(tMes);prov['support.epaisseur_mm']={origine:'mesure',source:'dessin',detail:`écart des faces ${r1(b.t)} ${o._env.unite||'unités'} × ${kS}`}}
    else{inc.push('épaisseur absente : ni cote, ni échelle');if(ct.length)inc.push('cote(s) voisine(s) de la paroi sans échelle pour les confirmer : '+ct.map(x=>'« '+x.texte+' »').join(', '))}}
  // rayons (voile circulaire)
  if(b.type==='voile_circulaire'){const ri=k?b.ri*k:null,re=k?b.re*k:null;
    if(sa.rayon_interieur_mm>0){Sp.rayon_interieur_mm=sa.rayon_interieur_mm;prov['support.rayon_interieur_mm']={origine:'saisie'}}
    else{const cr=cotesR(b,T,o,ri,re);cr.forEach(x=>pv.push(x.preuve));const ok=cr.find(x=>x.ri!=null);
      const nR=L&&(L.R&&MM[L.R.unite]?{v:L.R.v*MM[L.R.unite],t:L.R.texte}:L.Dc&&MM[L.Dc.unite]?{v:L.Dc.v*MM[L.Dc.unite]/2,t:L.Dc.texte,diam:true}:null);
      if(ok){Sp.rayon_interieur_mm=r1(ok.ri);prov['support.rayon_interieur_mm']={origine:'cote_explicite',source:'dessin',detail:ok.detail}}
      else if(nR&&ri&&(Math.abs(nR.v-ri)<=ACCORD*ri)){Sp.rayon_interieur_mm=nR.v;prov['support.rayon_interieur_mm']={origine:'cote_explicite',source:'nomenclature',detail:nR.t}}
      else if(nR&&ri&&Math.abs(nR.v-re)<=ACCORD*re&&Sp.epaisseur_mm){Sp.rayon_interieur_mm=r1(nR.v-Sp.epaisseur_mm);prov['support.rayon_interieur_mm']={origine:'calcul',detail:`${nR.t} (parement extérieur) − épaisseur`}}
      else if(ri){Sp.rayon_interieur_mm=r1(ri);prov['support.rayon_interieur_mm']={origine:kDed?'calcul':'mesure',source:'dessin',detail:kDed?`rapport rayon / épaisseur sur le dessin (${r1(b.ri/b.t)}) × épaisseur`:`rayon de la face intérieure ${r1(b.ri)} ${o._env.unite||'unités'} × ${kS}`};if(!kDed&&nR)inc.push(`rayon de la nomenclature (« ${nR.t} ») différent de la mesure : à vérifier`)}
      else{inc.push('rayon non confirmé : ni échelle ni cote de rayon rattachée');if(cr.length)inc.push('cote(s) de rayon ou de diamètre sans échelle pour les attribuer : '+cr.map(x=>'« '+x.texte+' »').join(', '))}}
    if(Sp.rayon_interieur_mm&&Sp.epaisseur_mm){Sp.rayon_exterieur_mm=r1(Sp.rayon_interieur_mm+Sp.epaisseur_mm);prov['support.rayon_exterieur_mm']={origine:'calcul',detail:'rayon intérieur + épaisseur'}}
    if(b.sources.includes('chaine'))inc.push('faces circulaires reconstituées à partir de segments (courbe aplatie) : rayon approché');}
  largeur(R,L,b,k,o,inc,prov)}

// cotes d'épaisseur écrites contre la paroi (dans la bande ou le long d'une face, près de la réservation) ; confirmées par la mesure seulement
function cotesEp(b,T,o,tMes){const out=[],cs=root.CPI.nomenclatures&&root.CPI.nomenclatures.cotes;
  T.forEach(t=>{const s=String(t.texte||'').trim();let v=null,u=null;const m=s.match(RX_EP);if(m){v=nb(m[1]);u=m[2]||null}else if(cs){const q=cs(s,null);if(q.etat==='seul'){v=q.v;u=q.unite}}
    if(v==null||!(v>0))return;const h=Math.max(t.h||1,1);
    // position du texte par rapport à la paroi : dans la bande (± 2 hauteurs) et à moins de 3 épaisseurs le long de la paroi
    let ok;if(b.type==='voile_droit'){const off=(t.x-(o._p[0]))*b.n[0]+(t.y-o._p[1])*b.n[1],al=Math.abs((t.x-o._p[0])*b.u[0]+(t.y-o._p[1])*b.u[1]);
      ok=off>=b.faces[0].off-2*h&&off<=b.faces[1].off+2*h&&al<=3*b.t+b.w}
    else{const r=dist([t.x,t.y],b.centre);ok=r>=b.ri-2*h&&r<=b.re+2*h&&dist([t.x,t.y],o._p)<=3*b.t+b.w}
    if(!ok)return;const un=accord(v,u,tMes);out.push({texte:s,mm:un?v*MM[un]:null,preuve:{type:'cote_voisine_epaisseur',texte:s,id:t.id||null,confirmee:!!un,unite:un}})});
  return out}
// rayons et diamètres écrits dans la fenêtre ; attribués à une face par la mesure seulement
function cotesR(b,T,o,ri,re){const out=[];
  T.forEach(t=>{const s=String(t.texte||'').trim(),R=lireR(s),D=R?null:lireD(s);if(!R&&!D)return;
    if(dist([t.x,t.y],o._p)>4*(b.t+b.w)+Math.min(b.ri,4*b.t))return;
    const v=R?R.v:D.v/2,u=R?R.unite:D.unite,ui=accord(v,u,ri),ue=accord(v,u,re);let x={texte:s,ri:null,preuve:{type:R?'cote_voisine_rayon':'cote_voisine_diametre',texte:s,id:t.id||null,face:null}};
    if(ui&&(!R||R.face!=='ext')){x.ri=v*MM[ui];x.detail=`« ${s} » confirmée par la mesure (face intérieure)`;x.preuve.face='int'}
    else if(ue&&(!R||R.face!=='int')&&b.t>0&&ri){x.ri=v*MM[ue]-(re-ri);x.detail=`« ${s} » (face extérieure, confirmée par la mesure) − épaisseur mesurée`;x.preuve.face='ext'}
    out.push(x)});
  return out}

// largeur suivant la paroi, orientation (largeur horizontale / hauteur), flèches, pistes de coffrage, correspondance avec le voile cintré
function largeur(R,L,b,k,o,inc,prov){const O=R.ouverture,Sp=R.support,Cf=R.coffrage,sa=o.saisie||{},d=L&&L.d,kd=L&&MM[L.u];
  const wMes=b&&k?b.w*k:null;
  if(sa.largeur_suivant_paroi_mm>0){O.largeur_suivant_paroi_mm=sa.largeur_suivant_paroi_mm;prov['ouverture.largeur_suivant_paroi_mm']={origine:'saisie'}}
  else if(O.type==='circ'&&O.diametre_mm){O.largeur_suivant_paroi_mm=O.diametre_mm;prov['ouverture.largeur_suivant_paroi_mm']={origine:'cote_explicite',source:'nomenclature',detail:'diamètre'}}
  else if(d&&d.type==='rect'&&kd){const a=d.a*kd,bb=d.b*kd,ma=wMes&&Math.abs(wMes-a)<=ACCORD*a,mb=wMes&&Math.abs(wMes-bb)<=ACCORD*bb;
    if(L.colonnes){O.largeur_suivant_paroi_mm=a;prov['ouverture.largeur_suivant_paroi_mm']={origine:'cote_explicite',source:'nomenclature',detail:'colonne Largeur'};
      if(wMes&&!ma&&mb)inc.push(`largeur mesurée le long de la paroi (${Math.round(wMes)} mm) égale à la Hauteur du tableau : orientation à vérifier`)}
    else if(ma||mb){const w=ma&&!mb?a:mb&&!ma?bb:a;O.largeur_suivant_paroi_mm=w;O.largeur_mm=w;O.hauteur_mm=w===a?bb:a;
      prov['ouverture.largeur_suivant_paroi_mm']=prov['ouverture.largeur_mm']=prov['ouverture.hauteur_mm']={origine:'cote_explicite',source:'nomenclature',detail:`orientation par la mesure le long de la paroi (${Math.round(wMes)} mm)`};
      if(ma&&mb&&Math.abs(a-bb)>1e-9)inc.push('les deux cotes du tableau sont proches de la mesure : orientation à confirmer')}
    else{inc.push(`orientation non confirmée : largeur horizontale (suivant la paroi) à choisir entre ${a} et ${bb} mm`+(wMes?` (mesure ${Math.round(wMes)} mm)`:''))}}
  else if(wMes&&O.type!=='circ'){O.largeur_suivant_paroi_mm=r1(wMes);prov['ouverture.largeur_suivant_paroi_mm']={origine:'mesure',source:'dessin'};inc.push('hauteur de l\'ouverture non visible en plan : à saisir')}
  else if(wMes&&O.type==='circ'){O.diametre_mm=r1(wMes);O.largeur_suivant_paroi_mm=r1(wMes);prov['ouverture.diametre_mm']=prov['ouverture.largeur_suivant_paroi_mm']={origine:'mesure',source:'dessin'}}
  // flèches : calcul du moteur (GEO.sag), corde = largeur suivant la paroi, aux deux parements
  if(o.tolerance_mm>0){Cf.tolerance_mm=o.tolerance_mm;prov['coffrage.tolerance_mm']={origine:'saisie'}}
  const w=O.largeur_suivant_paroi_mm,Ri=Sp.rayon_interieur_mm,Re=Sp.rayon_exterieur_mm;
  if(Sp.type==='voile_circulaire'&&w&&Ri){if(typeof o.sag!=='function')inc.push('flèche non calculée : fonction de calcul du moteur non fournie');
    else{const fi=o.sag(Ri,w),fe=Re?o.sag(Re,w):NaN;if(!isFinite(fi))inc.push('largeur suivant la paroi supérieure ou égale au diamètre intérieur : flèche non définie');
      else{Cf.fleche_interieure_mm=r1(fi);prov['coffrage.fleche_interieure_mm']={origine:'calcul',detail:`flèche de la corde ${w} mm sur le rayon ${Ri} mm (GEO.sag)`}}
      if(isFinite(fe)){Cf.fleche_exterieure_mm=r1(fe);prov['coffrage.fleche_exterieure_mm']={origine:'calcul',detail:`flèche de la corde ${w} mm sur le rayon ${Re} mm (GEO.sag)`}}}}
  else if(Sp.type==='voile_circulaire'&&!w)inc.push('largeur suivant la paroi inconnue : flèche non calculée');
  pistes(R);
  if(Sp.type==='voile_circulaire'&&(O.type==='rect'||O.type==='carre'))R.correspondance_voile={forme:'voile',L:w||null,l:Sp.epaisseur_mm,h:O.hauteur_mm,
    DcuveM:Ri?Math.round(Ri*2)/1000:null,dRef:Ri?'int':null,joues:null,note:'proposition pour le voile cintré (L = corde, l = épaisseur, Ø au parement intérieur) : jamais appliquée ; joues parallèles ou radiales à choisir'}}
// pistes motivées ; la solution reste « a_determiner » (choix du coffrage : lots suivants)
function pistes(R){const O=R.ouverture,Sp=R.support,Cf=R.coffrage,P=Cf.pistes,tol=Cf.tolerance_mm,f=Math.max(Cf.fleche_interieure_mm||0,Cf.fleche_exterieure_mm||0)||null;
  if(O.type==='circ')P.push({solution:'fourreau_circulaire',motif:'ouverture circulaire : fourreau ou solution circulaire classique à envisager'+(Sp.type==='voile_circulaire'?', même dans un voile cintré':'')+', sous réserve des contraintes de traversée'});
  else if(O.type==='rect'||O.type==='carre'){
    if(Sp.type==='voile_droit')P.push({solution:'coffrage_rectangulaire',motif:'paroi droite : aucune courbure à reprendre'});
    else if(Sp.type==='voile_circulaire'){
      if(f!=null&&tol>0)P.push(f<=tol?{solution:'coffrage_rectangulaire',motif:`flèche ${f} mm ≤ tolérance ${tol} mm : coffrage rectangulaire simple possible (contraintes de fabrication à vérifier)`}
        :{solution:'mannequin_cintre',motif:`flèche ${f} mm > tolérance ${tol} mm : courbure à reprendre (mannequin cintré)`});
      else if(f!=null)P.push({solution:'a_determiner',motif:`flèche ${f} mm à comparer à la tolérance admissible (non fixée)`});
      else P.push({solution:'a_determiner',motif:'courbure non chiffrée (rayon ou largeur suivant la paroi manquant)'})}}
  if(!P.length)P.push({solution:'a_determiner',motif:'support ou ouverture non déterminés'})}

// plusieurs observations d'un même repère (vues) : valeurs concordantes (à 2 %) gardées, désaccord → null + incertitude
function consolider(L){const V=L.filter(Boolean);if(!V.length)return null;if(V.length===1)return V[0];
  const R=JSON.parse(JSON.stringify(V[0]));R.observations=V.map(x=>x.observation);delete R.observation;R.preuves=V.flatMap(x=>x.preuves);R.incertitudes=[...new Set(V.flatMap(x=>x.incertitudes))];
  const ty=[...new Set(V.map(x=>x.support.type).filter(t=>t!=='inconnu'))];
  R.support.type=ty.length===1?ty[0]:'inconnu';if(ty.length>1)R.incertitudes.push('vues en désaccord sur le support ('+ty.join(', ')+') : à choisir');
  const RG={saisie:3,cote_explicite:2,calcul:1,mesure:0};
  [['support','epaisseur_mm'],['support','rayon_interieur_mm'],['support','rayon_exterieur_mm'],['ouverture','largeur_suivant_paroi_mm'],['ouverture','largeur_mm'],['ouverture','hauteur_mm'],['ouverture','diametre_mm'],['coffrage','fleche_interieure_mm'],['coffrage','fleche_exterieure_mm']].forEach(([a,k])=>{
    const X=V.map(x=>({v:x[a][k],p:x.provenance[a+'.'+k]})).filter(x=>x.v!=null);if(!X.length){R[a][k]=null;delete R.provenance[a+'.'+k];return}
    const m=X[0].v;if(X.every(x=>Math.abs(x.v-m)<=0.02*Math.abs(m))){X.sort((x,y)=>(RG[(y.p||{}).origine]||0)-(RG[(x.p||{}).origine]||0));R[a][k]=X[0].v;R.provenance[a+'.'+k]=Object.assign({},X[0].p,{vues:X.length})}
    else{R[a][k]=null;delete R.provenance[a+'.'+k];R.incertitudes.push(`${a}.${k} : valeurs différentes selon les vues (${X.map(x=>x.v).join(', ')}) : à choisir`)}});
  const cf=V.map(x=>x.support.confiance).filter(Boolean);R.support.confiance=R.support.type==='inconnu'?null:cf.includes('forte')?'forte':cf.includes('moyenne')?'moyenne':cf[0]||null;
  R.coffrage.pistes=[];R.coffrage.solution_proposee='a_determiner';pistes(R);R.validation_utilisateur_requise=true;return R}

root.CPI=Object.assign(root.CPI||{},{support:{analyser:(obs,env,o)=>analyser(obs,env,Object.assign({},o)),consolider,envPdf,envDxf,arcsBezier,arcsChaines,arc3}});
})(typeof globalThis!=='undefined'?globalThis:this);
