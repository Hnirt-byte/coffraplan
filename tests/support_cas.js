// Phase 9A : constructions géométriques FICTIVES pour tests/t_support.py (voiles droits et circulaires autour d'une réservation).
// Toutes les cotes en mm « réels » ; le dessin est en unités de dessin = mm / k (k = mm par unité : 1:50 sur un PDF → 50 × 25,4 / 72).
// Chargé dans la page (add_script_tag) ou dans Node (module.exports) ; aucune dépendance.
(function(root){'use strict';
const PI=Math.PI;
const K50=50*25.4/72;
// pièces de Bézier d'un arc (centre c, rayon r, de a0 à a1, radians, sens trigonométrique), ≤ 90° par pièce
function bez(c,r,a0,a1,id){const n=Math.max(1,Math.ceil((a1-a0)/(PI/2)-1e-9)),d=(a1-a0)/n,q=4/3*Math.tan(d/4),out=[];
  for(let i=0;i<n;i++){const a=a0+i*d,b=a+d,P=t=>[c[0]+r*Math.cos(t),c[1]+r*Math.sin(t)],p0=P(a),p3=P(b);
    out.push({id:(id||'b')+i,c:[p0,[p0[0]-q*r*Math.sin(a),p0[1]+q*r*Math.cos(a)],[p3[0]+q*r*Math.sin(b),p3[1]-q*r*Math.cos(b)],p3]})}
  return out}
// arc « DXF » {centre, r, a0, d}
const arc=(c,r,a0,a1,id)=>({id:id||'a',source:'arc',centre:c,r,a0:((a0%(2*PI))+2*PI)%(2*PI),d:a1-a0});
// arc aplati en segments (export de DAO)
function chaine(c,r,a0,a1,n,id){const S=[];for(let i=0;i<n;i++){const a=a0+(a1-a0)*i/n,b=a0+(a1-a0)*(i+1)/n;S.push({id:(id||'s')+i,a:[c[0]+r*Math.cos(a),c[1]+r*Math.sin(a)],b:[c[0]+r*Math.cos(b),c[1]+r*Math.sin(b)]})}return S}
const seg=(a,b,id)=>({id:id||'t',a,b});
// rectangle (centre, largeur suivant x, profondeur suivant y, angle en degrés) → 4 sommets
function rect(cx,cy,w,h,ang){const a=(ang||0)*PI/180,u=[Math.cos(a),Math.sin(a)],v=[-u[1],u[0]];
  return[[-1,-1],[1,-1],[1,1],[-1,1]].map(([i,j])=>[cx+i*w/2*u[0]+j*h/2*v[0],cy+i*w/2*u[1]+j*h/2*v[1]])}
const cotes=P=>P.map((p,i)=>seg(p,P[(i+1)%4],'k'+i));
// candidat au format de CPI.geometrie.detecterPage (statut a_confirmer)
function candRect(P,id){const L=Math.hypot(P[1][0]-P[0][0],P[1][1]-P[0][1]),l=Math.hypot(P[2][0]-P[1][0],P[2][1]-P[1][1]),a=L>=l?Math.atan2(P[1][1]-P[0][1],P[1][0]-P[0][0]):Math.atan2(P[2][1]-P[1][1],P[2][0]-P[1][0]);
  return{id:id||'P1-1',type:'rect',statut:'a_confirmer',unite:'pt',source:{page:1},centre:[(P[0][0]+P[2][0])/2,(P[0][1]+P[2][1])/2],dims:{L:Math.max(L,l),l:Math.min(L,l),angle:((a*180/PI)%180+180)%180},
    geometrie:{type:'polyligne',ferme:true,points:P},remarques:[]}}
const candCirc=(c,r,id)=>({id:id||'P1-1',type:'circ',statut:'a_confirmer',unite:'pt',source:{page:1},centre:c,dims:{D:2*r},geometrie:{type:'cercle',centre:c,r},remarques:[]});

// Voile droit horizontal d'épaisseur t (mm), faces y = ±t/2, longueur 2·Lw, interrompues sur l'ouverture de largeur w ;
// ouverture : 'rect' (contour d'une face à l'autre), 'circ' (cercle Ø D dans la bande), 'point' (repère seul) ; ang : rotation du tout (°)
function voileDroit(o){const k=o.k||K50,t=o.t/k,w=o.w/k,Lw=(o.Lw||3*o.w+4*o.t)/k,a=(o.ang||0)*PI/180,R=p=>[p[0]*Math.cos(a)-p[1]*Math.sin(a)+(o.x||0),p[0]*Math.sin(a)+p[1]*Math.cos(a)+(o.y||0)];
  const S=[],trou=o.ouverture==='rect';
  [-t/2,t/2].forEach((y,f)=>{if(trou){S.push(seg(R([-Lw,y]),R([-w/2,y]),'f'+f+'g'),seg(R([w/2,y]),R([Lw,y]),'f'+f+'d'))}else S.push(seg(R([-Lw,y]),R([Lw,y]),'f'+f))});
  let cand=null,P=null;
  if(o.ouverture==='rect'){P=rect(0,0,w,t,0).map(R);S.push(...cotes(P));cand=candRect(P)}
  else if(o.ouverture==='circ'){cand=candCirc(R([0,0]),o.D/k/2)}
  return{env:{unite:'pt',segments:S,courbes:[],arcs:[],textes:[]},obs:{repere:o.repere||'R1',candidat:cand,point:cand?null:R([0,0]),h:2.5,page:1,vue:o.vue||null},k,R}}

// Voile circulaire : centre (0,0), rayon intérieur Ri (mm), épaisseur t, réservation centrée à l'angle 90° (en haut), largeur w
// (corde, joues parallèles) ; faces dessinées de 90° − span à 90° + span, interrompues sur l'ouverture ;
// mode 'bezier' (PDF), 'arc' (DXF), 'chaine' (segments) ; ouverture 'rect' | 'circ' | 'point'
function voileCirc(o){const k=o.k||K50,Ri=o.Ri/k,Re=(o.Ri+o.t)/k,w=o.w/k,c=[0,0],S=[],C=[],A=[],mode=o.mode||'bezier',span=o.span||Math.min(PI/3,(4*o.w+4*o.t)/o.Ri);
  const yi=Math.sqrt(Ri*Ri-w*w/4),ye=Math.sqrt(Re*Re-w*w/4),trou=o.ouverture==='rect';
  const face=(r,f)=>{const g=trou?Math.asin(w/2/r):0,I=trou?[[PI/2+g,PI/2+span],[PI/2-span,PI/2-g]]:[[PI/2-span,PI/2+span]];
    I.forEach(([a0,a1],j)=>{const id='f'+f+j;if(mode==='bezier')C.push(...bez(c,r,a0,a1,id));else if(mode==='arc')A.push(arc(c,r,a0,a1,id));else S.push(...chaine(c,r,a0,a1,Math.max(6,Math.round((a1-a0)/(PI/90))),id))})};
  face(Ri,0);face(Re,1);
  let cand=null;
  if(trou){const P=[[-w/2,yi],[w/2,yi],[w/2,ye],[-w/2,ye]];S.push(...cotes(P));cand=candRect(P)}
  else if(o.ouverture==='circ')cand=candCirc([0,(Ri+Re)/2],o.D/k/2);
  return{env:{unite:'pt',segments:S,courbes:C,arcs:A,textes:[]},obs:{repere:o.repere||'R1',candidat:cand,point:cand?null:[0,(Ri+Re)/2],h:2.5,page:1,vue:o.vue||null},k}}

// ligne de nomenclature (format de nomenclatures.js)
const ligne=(o)=>({id:'L1',repere:o.repere||'R1',dims:o.D?{type:'circ',D:o.D,unite:'mm',texte:'Ø'+o.D}:{type:'rect',a:o.a,b:o.b,unite:'mm',texte:o.a+'x'+o.b,colonne:o.colonnes?'Largeur / Hauteur':undefined},
  cellules:o.cellules||[],description:o.description||''});

const SC={K50,bez,arc,chaine,seg,rect,cotes,candRect,candCirc,voileDroit,voileCirc,ligne};
if(typeof module!=='undefined'&&module.exports)module.exports=SC;else root.SC=SC;
})(typeof globalThis!=='undefined'?globalThis:this);
