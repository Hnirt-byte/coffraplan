// Phase 10B : géométrie d'étude du vide uniquement. Aucun débit ni création d'ouvrage.
(function(root){'use strict';
const ANGLES=['GA','DA','DB','GB']; // gauche/droite sur A (y=0) ou B (y=e)
function chanfrein45(parametres,provenance){
  const p={...parametres},erreurs=[];
  for(const k of ['L','e','H','retrait','ep'])if(typeof p[k]!=='number'||!Number.isFinite(p[k])||p[k]<=0)erreurs.push(k+' : valeur finie strictement positive requise');
  const angle=ANGLES.indexOf(p.angle);
  if(angle<0)erreurs.push('Angle concerné : choisir GA, DA, DB ou GB');
  if(!['vers_beton','vers_vide'].includes(p.orientation))erreurs.push('Orientation des faces coffrantes à choisir explicitement');
  if(p.retrait>=Math.min(p.L,p.e))erreurs.push('Retrait strictement inférieur à L et e : section pentagonale requise');
  const base={type:'chanfrein45',parametres:p,provenance:JSON.parse(JSON.stringify(provenance||{})),erreurs,
    fabricable:false,limite:'Géométrie à étudier : face diagonale, assemblages et déductions CP non pris en charge. Création, débit, gabarits et exports de fabrication indisponibles.',
    hypotheses:['Section constante sur H ; un seul angle, retrait égal sur les deux côtés adjacents, angle fixé à 45°.',
      'Section du vide en mm, A : y=0, B : y=e ; Z vertical. Épaisseur CP et orientation conservées, sans calcul de panneaux.']};
  if(erreurs.length)return{...base,sommets:[],faces:[],segments:[],cotes:[]};
  const rectangle=[[0,0],[p.L,0],[p.L,p.e],[0,p.e]],sommets=[];
  rectangle.forEach((v,i)=>{
    if(i!==angle){sommets.push(v);return;}
    for(const j of [(i+3)%4,(i+1)%4]){
      const w=rectangle[j],longueur=Math.hypot(w[0]-v[0],w[1]-v[1]);
      sommets.push([v[0]+p.retrait*(w[0]-v[0])/longueur,v[1]+p.retrait*(w[1]-v[1])/longueur]);
    }
  });
  const bas=sommets.map(([x,y])=>[x,y,0]),haut=sommets.map(([x,y])=>[x,y,p.H]);
  const segments=sommets.map((a,i)=>{const b=sommets[(i+1)%5];return{a,b,longueur:Math.hypot(b[0]-a[0],b[1]-a[1]),diagonal:a[0]!==b[0]&&a[1]!==b[1]}});
  const faces=[bas.slice().reverse(),haut,...bas.map((a,i)=>[a,bas[(i+1)%5],haut[(i+1)%5],haut[i]])];
  return{...base,sommets,faces,segments,reference:{rectangle,angle:rectangle[angle],parementA:[[0,0],[p.L,0]],parementB:[[0,p.e],[p.L,p.e]]},
    cotes:['L','e','H','retrait','ep'].map(k=>({parametre:k,valeur:p[k],unite:'mm',origine:(provenance||{})[k]||{origine:'inconnue'}})),
    aire:p.L*p.e-p.retrait*p.retrait/2,volume:(p.L*p.e-p.retrait*p.retrait/2)*p.H};
}
root.CPI=Object.assign(root.CPI||{},{geometriesParticulieres:{chanfrein45}});
})(typeof globalThis!=='undefined'?globalThis:this);
