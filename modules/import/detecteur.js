// CoffraPlan — module d'import de plans, composant B : détecteur de réservations.
// Analyse un document normalisé (composant A) et liste des réservations POTENTIELLES, à confirmer par l'utilisateur.
// Ne valide jamais rien : statut « a_confirmer » ou « non_pris_en_charge » seulement. Cotes et coordonnées dans l'unité
// du fichier source (aucune conversion ici). Indépendant de l'interface et du moteur.
(function(root){'use strict';
const cp=o=>JSON.parse(JSON.stringify(o));
const dist=(a,b)=>Math.hypot(b[0]-a[0],b[1]-a[1]);

// Rectangle = 4 sommets, côtés opposés égaux et diagonales égales (à tol près, relatif à la diagonale)
function rectangle(pts,tol){
  let P=pts.slice();if(P.length===5&&dist(P[0],P[4])===0)P=P.slice(0,4);
  if(P.length!==4)return null;
  const [a,b,c,e]=[dist(P[0],P[1]),dist(P[1],P[2]),dist(P[2],P[3]),dist(P[3],P[0])],d1=dist(P[0],P[2]),d2=dist(P[1],P[3]),k=tol*Math.max(d1,d2);
  if(!(Math.min(a,b)>0)||Math.abs(a-c)>k||Math.abs(b-e)>k||Math.abs(d1-d2)>k)return null;
  // angle droit au premier sommet : écarte le quadrilatère croisé (« nœud papillon »), qui a lui aussi côtés et diagonales égaux
  const v0=[P[1][0]-P[0][0],P[1][1]-P[0][1]],v1=[P[2][0]-P[1][0],P[2][1]-P[1][1]];
  if(Math.abs(v0[0]*v1[0]+v0[1]*v1[1])>k*Math.max(a,b))return null;
  const iL=a>=b?0:1,u=[P[iL+1][0]-P[iL][0],P[iL+1][1]-P[iL][1]];
  let ang=Math.atan2(u[1],u[0])*180/Math.PI;ang=((ang%180)+180)%180;   // direction du grand côté, 0 ≤ angle < 180°
  return{L:Math.max(a,b),l:Math.min(a,b),angle:Math.round(ang*1e6)/1e6,centre:[(P[0][0]+P[2][0])/2,(P[0][1]+P[2][1])/2]};
}

// Rectangles reconstitués à partir de segments indépendants (LINE d'un DXF, traits d'un PDF). S = [{id, a:[x,y], b:[x,y]}] ;
// opt.eps = distance de raccord des extrémités (unité des segments), opt.tol = tolérance de forme. Un côté dessiné en plusieurs
// morceaux alignés est réuni. → [{pts (4 sommets), ids (segments, diagonales comprises), diag, accole (sommets reliés à d'autres
// traits), te (extrémités d'autres traits sur un côté), int (extrémités d'autres traits à l'intérieur), L, l, angle, centre}]
function rectSegments(S,opt){
  const eps=opt.eps,tol=opt.tol||0.005,N=[],G=new Map(),MAXC=50000;
  const node=p=>{const gi=Math.floor(p[0]/eps),gj=Math.floor(p[1]/eps);
    for(let di=-1;di<=1;di++)for(let dj=-1;dj<=1;dj++){const L=G.get((gi+di)+','+(gj+dj));if(L)for(const k of L)if(dist(N[k].p,p)<=eps)return k}
    const k=N.length,kk=gi+','+gj;N.push({p,e:new Map(),ok:true});if(!G.has(kk))G.set(kk,[]);G.get(kk).push(k);return k};
  const lier=(u,v,ids)=>{const x=N[u].e.get(v);if(x){ids.forEach(i=>x.includes(i)||x.push(i));return}const y=ids.slice();N[u].e.set(v,y);N[v].e.set(u,y)};
  S.forEach(s=>{const u=node(s.a),v=node(s.b);if(u!==v)lier(u,v,[s.id])});
  // côtés en plusieurs morceaux : un sommet à 2 voisins alignés de part et d'autre disparaît
  N.forEach((n,k)=>{if(n.e.size!==2)return;const [[u,iu],[v,iv]]=[...n.e],a=[N[u].p[0]-n.p[0],N[u].p[1]-n.p[1]],b=[N[v].p[0]-n.p[0],N[v].p[1]-n.p[1]];
    if(N[u].e.has(v)||Math.abs(a[0]*b[1]-a[1]*b[0])>tol*Math.hypot(...a)*Math.hypot(...b)||a[0]*b[0]+a[1]*b[1]>=0)return;
    N[u].e.delete(k);N[v].e.delete(k);n.e.clear();n.ok=false;lier(u,v,iu.concat(iv))});
  // index grossier des sommets restants (côtés, intérieur)
  const V=N.map((n,k)=>k).filter(k=>N[k].ok),[x0,y0,X1,Y1]=bornes(V.map(k=>N[k].p)),cs=Math.max(X1-x0,Y1-y0,eps)/64,Q=new Map();
  V.forEach(k=>{const c=Math.floor((N[k].p[0]-x0)/cs)+','+Math.floor((N[k].p[1]-y0)/cs);if(!Q.has(c))Q.set(c,[]);Q.get(c).push(k)});
  const R=[];let nc=0;
  for(const a of V){const A=[...N[a].e.keys()].filter(b=>b>a);if(N[a].e.size>6)continue;
    for(let i=0;i<A.length;i++)for(let j=i+1;j<A.length;j++){const b=A[i],d=A[j];
      for(const c of N[b].e.keys()){if(c<=a||c===d||!N[d].e.has(c))continue;if(++nc>MAXC)return R;
        const P=[a,b,c,d],r=rectangle(P.map(k=>N[k].p),tol);if(!r)continue;
        const dg=[[a,c],[b,d]].filter(([u,v])=>N[u].e.has(v)),ids=[[a,b],[b,c],[c,d],[d,a]].concat(dg).flatMap(([u,v])=>N[u].e.get(v));
        const accole=P.filter(k=>N[k].e.size>2+dg.filter(x=>x.includes(k)).length).length;
        let te=0,int=0;const Px=P.map(k=>N[k].p),bx=bornes(Px);
        for(let gx=Math.floor((bx[0]-x0)/cs);gx<=Math.floor((bx[2]-x0)/cs);gx++)for(let gy=Math.floor((bx[1]-y0)/cs);gy<=Math.floor((bx[3]-y0)/cs);gy++)
          for(const k of Q.get(gx+','+gy)||[]){if(P.includes(k))continue;const p=N[k].p;
            if(Px.some((q,m)=>dSeg(p,q,Px[(m+1)%4])<=eps))te++;else if(dansPoly(p,Px))int++}
        R.push(Object.assign({pts:Px,ids,diag:dg.length>0,accole,te,int},r))}}}
  return R}
// Emprise [x0,y0,x1,y1] sans Math.min(...tableau) : pile dépassée au-delà de ~100 000 sommets (grands plans)
function bornes(P){let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;for(const p of P){if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];if(p[1]<y0)y0=p[1];if(p[1]>y1)y1=p[1]}return[x0,y0,x1,y1]}
function dSeg(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],l=dx*dx+dy*dy,t=l?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)):0;return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)}
function dansPoly(p,P){let c=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const a=P[i],b=P[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c}return c}

// doc : document normalisé ; opt.tol : tolérance relative de forme (défaut 0,5 %)
// → {fichier, format, unite, candidats:[candidat]} (contrat : README.md)
function detecter(doc,opt){
  const tol=opt&&opt.tol>0?opt.tol:0.005;
  const candidats=(doc.entites||[]).map((e,i)=>{
    const c={id:'R'+(i+1),type:null,statut:'non_pris_en_charge',unite:doc.unite,
      source:{fichier:doc.fichier,format:doc.format,calque:e.calque==null?null:e.calque,id:String(e.id)},
      geometrie:cp(e),centre:null,dims:null,h:Number.isFinite(e.h)&&e.h>0?e.h:null,manquants:[],remarques:[]};
    // présentation (espace papier) : cadres, cartouches, tableaux ; coordonnées d'un autre repère que le dessin → jamais proposée
    if(e.espace==='papier')c.remarques.push('dessiné dans une présentation (espace papier'+(e.presentation?' « '+e.presentation+' »':'')+')');
    else if(e.type==='cercle'){
      if(e.r>0){c.type='circ';c.dims={D:2*e.r};c.centre=e.centre.slice(0,2)}else c.remarques.push('cercle de rayon nul');
    }else if(e.type==='polyligne'){
      const R=e.ferme?rectangle(e.points,tol):null;
      if(R){c.type='rect';c.dims={L:R.L,l:R.l,angle:R.angle};c.centre=R.centre;if(R.L-R.l<=1e-6*R.L)c.remarques.push('carré potentiel (côtés égaux)')}
      else c.remarques.push(e.ferme?'contour fermé non rectangulaire':'polyligne ouverte');
    }else c.remarques.push('géométrie non prise en charge'+(e.nature?' : '+e.nature:''));
    if(c.type){c.statut='a_confirmer';if(c.h==null)c.manquants.push('h');if(c.unite==null)c.manquants.push('unite')}
    return c});
  lignes(doc,candidats,tol);
  return{fichier:doc.fichier,format:doc.format,unite:doc.unite,candidats};
}

// Rectangles dessinés en 4 LINE indépendantes (espace Objet, même calque) : proposés seulement sans ambiguïté (sommets et côtés
// libres de tout autre trait du calque, diagonales admises) et s'ils ne doublent pas une polyligne déjà reconnue
function lignes(doc,C,tol){const G={},note=(c,m)=>{if(!c.remarques.includes(m))c.remarques.push(m)};
  (doc.entites||[]).forEach((e,i)=>{if(e.type==='autre'&&e.segment&&e.espace!=='papier')(G[e.calque]=G[e.calque]||[]).push({id:i,a:e.segment[0],b:e.segment[1]})});
  Object.keys(G).forEach(cal=>{const S=G[cal],P=S.flatMap(s=>[s.a,s.b]),ext=P.reduce((m,p)=>Math.max(m,Math.abs(p[0]),Math.abs(p[1])),1);
    rectSegments(S,{eps:1e-6*ext,tol}).forEach(r=>{const E=[...new Set(r.ids)].map(i=>C[i]),ids=E.map(c=>c.source.id).join('+');
      if(r.accole||r.te){E.forEach(c=>note(c,'côté d\'un rectangle de LINE non proposé : autres traits raccordés aux sommets ou sur les côtés'));return}
      const dbl=C.find(c=>c.type==='rect'&&c.geometrie.type==='polyligne'&&dist(c.centre,r.centre)<=tol*r.L&&Math.abs(c.dims.L-r.L)<=tol*r.L&&Math.abs(c.dims.l-r.l)<=tol*r.L);
      if(dbl){E.forEach(c=>note(c,'côté d\'un rectangle qui double la polyligne '+dbl.id));return}
      const c={id:'R'+(C.length+1),type:'rect',statut:'a_confirmer',unite:doc.unite,source:{fichier:doc.fichier,format:doc.format,calque:cal,id:ids},
        geometrie:{type:'polyligne',ferme:true,points:r.pts.map(p=>p.slice()),espace:'objet',presentation:null,lignes:E.map(c=>c.source.id)},
        centre:r.centre,dims:{L:r.L,l:r.l,angle:r.angle},h:null,manquants:['h'].concat(doc.unite==null?['unite']:[]),
        remarques:['rectangle formé de '+E.length+' LINE indépendantes'+(r.diag?' (diagonales comprises)':'')]};
      if(r.L-r.l<=1e-6*r.L)c.remarques.push('carré potentiel (côtés égaux)');
      E.forEach(x=>note(x,'côté du rectangle '+c.id));C.push(c)})})}

root.CPI=Object.assign(root.CPI||{},{detecteur:{detecter,rectangle,rectSegments}});
})(typeof globalThis!=='undefined'?globalThis:this);
