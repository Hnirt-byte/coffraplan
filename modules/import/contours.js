// CoffraPlan — phase 9B : ouvertures contextuelles PDF, sans cote physique ni création.
// Un repère fiable de la nomenclature + deux diagonales + traverses dessinées + deux
// faces traversées sont nécessaires. Les filtres du détecteur ordinaire restent actifs.
(function(root){'use strict';
const d=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]),cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
const sub=(a,b)=>[a[0]-b[0],a[1]-b[1]],dot=(a,b)=>a[0]*b[0]+a[1]*b[1];
const cle=s=>root.CPI.nomenclatures.cleRep(String(s||'').replace(/^[\s({\[]+|[\s)}\]]+$/g,''));
function intersection(a,b){const u=sub(a.b,a.a),v=sub(b.b,b.a),den=cross(u,v),l=d(a.a,a.b),m=d(b.a,b.b);
  if(!l||!m||Math.abs(den)<0.25*l*m||Math.min(l,m)<0.6*Math.max(l,m))return null;
  const w=sub(b.a,a.a),t=cross(w,v)/den,q=cross(w,u)/den;
  if(t<0.3||t>0.7||q<0.3||q>0.7)return null;
  return[a.a[0]+t*u[0],a.a[1]+t*u[1]]}
function distance(p,a,b){const u=sub(b,a),l=dot(u,u),t=l?Math.max(0,Math.min(1,dot(sub(p,a),u)/l)):0;return d(p,[a[0]+t*u[0],a[1]+t*u[1]])}
// Deux traverses : couverture des deux petits côtés, fragments admis. Les diagonales
// ne prouvent pas leurs propres limites ; ni une croix isolée ni un repère seul ne suffit.
function traverses(P,S,diags){const sides=P.map((p,i)=>({a:p,b:P[(i+1)%4],l:d(p,P[(i+1)%4])})).sort((a,b)=>a.l-b.l),out=[];
  for(const side of sides.slice(0,2)){if(!(side.l>0))return null;const u=sub(side.b,side.a).map(x=>x/side.l),tol=0.22*side.l,I=[];
    S.forEach(s=>{if(diags.includes(s)||distance(s.a,side.a,side.b)>tol||distance(s.b,side.a,side.b)>tol)return;
      const v=sub(s.b,s.a),l=d(s.a,s.b);if(!l||Math.abs(cross(u,v))>0.4*l)return;
      const t=[dot(sub(s.a,side.a),u),dot(sub(s.b,side.a),u)].sort((a,b)=>a-b);
      I.push({a:Math.max(0,t[0]),b:Math.min(side.l,t[1]),id:s.id})});
    I.sort((a,b)=>a.a-b.a);let end=0,total=0;for(const x of I){if(x.b>end){total+=x.b-Math.max(end,x.a);end=x.b}}
    if(total<0.5*side.l)return null;out.push({traits:I.map(x=>x.id),couverture:total/side.l})}return out}
function grille(S,p,size){const groups=[];
  S.forEach(s=>{const l=d(s.a,s.b);if(l<2*size||distance(p,s.a,s.b)>2*size)return;let a=Math.atan2(s.b[1]-s.a[1],s.b[0]-s.a[0]);a=(a+Math.PI)%Math.PI;
    let g=groups.find(g=>Math.abs(g.a-a)<0.035);if(!g){g={a,V:[]};groups.push(g)}
    const off=-(s.a[0]-p[0])*Math.sin(g.a)+(s.a[1]-p[1])*Math.cos(g.a);if(!g.V.some(v=>Math.abs(v-off)<0.01*size))g.V.push(off)});
  return groups.some(g=>{const V=g.V.sort((a,b)=>a-b);for(let i=0;i<V.length;i++)for(let j=i+1;j<V.length;j++){
    const step=V[j]-V[i];if(step<0.05*size)continue;
    if([2,3,4].every(k=>V.some(v=>Math.abs(v-V[i]-k*step)<0.1*step)))return true}return false})}
function reconstruire(geo,ctx){ctx=ctx||{};const api=root.CPI,G=api.geometrie,labels=ctx.reperes||[],T=ctx.textes||[],cad=ctx.cadres||[],idx=G.index(geo),env=api.support.envPdf(geo,T),out=[];
  const keys=new Set(labels.map(cle)),seen=new Set(),inside=(p,b)=>p[0]>=b[0]&&p[0]<=b[2]&&p[1]>=b[1]&&p[1]<=b[3];
  const texts=T.filter(t=>keys.has(cle(t.texte))&&(!t.ocr||t.ocr.conf>=75)&&!cad.some(b=>inside([t.x,t.y],b)));
  for(const t of texts){const h=Math.max(t.h||1,0.5),Q=[[t.x,t.y]].concat(G.rappels(geo,t,idx)),R=12*h,local=new Set();
    Q.forEach(p=>idx.dans([p[0]-R,p[1]-R,p[0]+R,p[1]+R]).forEach(s=>{const l=d(s.a,s.b);if(l>0&&l<=4*R)local.add(s)}));
    // Le filtre de longueur des diagonales ne doit pas supprimer les petits
    // fragments qui prouvent une traverse (la hauteur OCR n'est pas leur taille).
    const borders=[...local],L=borders.filter(s=>d(s.a,s.b)>=0.6*h),found=[];
    // Recherche bornée à la fenêtre d'un repère (pas de produit cartésien de la page).
    if(L.length>1500)continue;
    for(let i=0;i<L.length;i++)for(let j=i+1;j<L.length;j++){const a=L[i],b=L[j],p=intersection(a,b);if(!p||cad.some(z=>inside(p,z)))continue;
      const size=Math.max(d(a.a,a.b),d(b.a,b.b)),near=Math.min(...Q.map(q=>d(q,p)));if(near>Math.max(4*h,0.6*size))continue;
      const P=[a.a,a.b,b.a,b.b].map(q=>q.slice()).sort((x,y)=>Math.atan2(x[1]-p[1],x[0]-p[0])-Math.atan2(y[1]-p[1],y[0]-p[0]));
      if(ctx.zone&&!P.every(q=>inside(q,[ctx.zone.x0,ctx.zone.y0,ctx.zone.x1,ctx.zone.y1])))continue;
      const lengths=P.map((q,k)=>d(q,P[(k+1)%4])).sort((a,b)=>b-a);if(lengths[3]<0.1*lengths[0])continue;
      const tr=traverses(P,borders,[a,b]);if(!tr)continue;
      const c={id:'reconstruction',type:'rect',statut:'a_confirmer',unite:'pt',source:{fichier:ctx.fichier,format:'pdf',calque:null,page:geo.page,id:[a.id,b.id].join('+')},
        geometrie:{type:'polyligne',ferme:false,points:P,espace:'papier',presentation:'Page '+geo.page,page:geo.page},centre:p,
        dims:{L:(lengths[0]+lengths[1])/2,l:(lengths[2]+lengths[3])/2,angle:null},h:null,manquants:['h','confirmation_contour'],
        bbox:[Math.min(...P.map(q=>q[0])),Math.min(...P.map(q=>q[1])),Math.max(...P.map(q=>q[0])),Math.max(...P.map(q=>q[1]))],
        annot:{repere:{texte:t.texte,id:t.id,d:near}},remarques:['contour reconstruit (diagonales, traverses et parements) : limites à confirmer'],
        reconstruction:{type:'diagonales_parements',explicite:false,repere:{id:t.id,texte:t.texte},diagonales:[a.id,b.id],traverses:tr,preuves:[]}};
      const test=api.support.analyser({candidat:c,page:geo.page},env,{cadres:cad});
      if(!/^(voile_droit|voile_circulaire)$/.test(test.support.type)||grille(env.segments,p,size))continue;
      c.reconstruction.preuves=test.preuves.filter(x=>x.type==='faces_paralleles'||x.type==='arcs_concentriques');
      found.push({c,d:near})}
    found.sort((a,b)=>a.d-b.d);
    // Un repère qui désigne deux ouvertures équivalentes reste indécidé.
    if(!found.length)continue;
    const first=found[0],different=x=>d(first.c.centre,x.c.centre)>h||['L','l'].some(k=>Math.abs(first.c.dims[k]-x.c.dims[k])>0.2*first.c.dims[k]);
    if(found.slice(1).some(x=>x.d<=first.d+0.5*h&&different(x)))continue;
    const c=found[0].c,key=c.centre.map(v=>Math.round(v*10)).join('|');if(seen.has(key))continue;seen.add(key);out.push(c)}
  return out}
root.CPI=Object.assign(root.CPI||{},{contours:{reconstruire}});
})(typeof globalThis!=='undefined'?globalThis:this);
