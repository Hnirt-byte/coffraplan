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
  return{fichier:doc.fichier,format:doc.format,unite:doc.unite,candidats};
}

root.CPI=Object.assign(root.CPI||{},{detecteur:{detecter,rectangle}});
})(typeof globalThis!=='undefined'?globalThis:this);
