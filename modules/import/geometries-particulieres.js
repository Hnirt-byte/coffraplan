// Géométrie d’étude 10B et pièces CP 10C ; aucun accès au DOM, au stockage ou au projet.
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
// CP placé à l'intérieur de l'enveloppe du vide ; A et B restent ouverts.
// Dessus/dessous filants ; jonction joue/diagonale à onglet 22,5°.
function chanfrein45Fabrication(parametres,provenance){
  const g=chanfrein45(parametres,provenance),p=g.parametres,erreurs=[...g.erreurs],pieces=[];
  const fail=()=>({...g,version:1,fabricable:false,erreurs,pieces:[],contacts:[],limite:'Fabrication indisponible : '+erreurs.join(' ; ')});
  if(erreurs.length)return fail();
  const {L,e,H,retrait:r,ep:t,angle}=p,k=Math.SQRT2-1,h=H-2*t;
  if(p.orientation!=='vers_beton')erreurs.push('Seule l’orientation vers_beton est fabricable en V1');
  if(p.version!=null&&p.version!==1)erreurs.push('Version d’assemblage non prise en charge');
  if(p.angles||p.nombre!=null&&p.nombre!==1)erreurs.push('Un seul chanfrein est pris en charge');
  if(!(h>0))erreurs.push('H doit dépasser deux épaisseurs de CP');
  if(!(e-r-k*t>0))erreurs.push('Joue chanfreinée : longueur intérieure nulle ou négative');
  if(!(L-r-(Math.SQRT2+1)*t>0))erreurs.push('Diagonale et joue opposée : interférence ou ouverture A nulle');
  if(![g.aire,g.volume].every(Number.isFinite))erreurs.push('Dimensions calculées non finies');
  if(erreurs.length)return fail();
  const aire=P=>Math.abs(P.reduce((a,v,i)=>{const w=P[(i+1)%P.length];return a+v[0]*w[1]-v[1]*w[0]},0))/2;
  const ccw=P=>{const a=P.reduce((s,v,i)=>{const w=P[(i+1)%P.length];return s+v[0]*w[1]-v[1]*w[0]},0);return a<0?P.slice().reverse():P};
  const miroir=([x,y])=>[angle==='DA'||angle==='DB'?L-x:x,angle==='GB'||angle==='DB'?e-y:y];
  const prisme=(P,z,hauteur)=>{const bas=P.map(([x,y])=>[x,y,z]),haut=P.map(([x,y])=>[x,y,z+hauteur]);return[bas.slice().reverse(),haut,...bas.map((a,i)=>[a,bas[(i+1)%P.length],haut[(i+1)%P.length],haut[i]])]};
  const P=g.sommets;
  function ajout(id,nom,empreinte,z,hauteur,decoupe,coupes,face,longueurFace){
    const poly=ccw(empreinte),xs=decoupe.map(q=>q[0]),ys=decoupe.map(q=>q[1]),a=Math.max(...xs)-Math.min(...xs),b=Math.max(...ys)-Math.min(...ys);
    const aireDecoupe=aire(decoupe),volumeNet=aire(poly)*hauteur;
    pieces.push({id,nom,ep:t,empreinte:poly,z,hauteur,faces:prisme(poly,z,hauteur),contourDecoupe:decoupe,coupes,
      faceCoffrante:face,longueurFace:longueurFace??null,a,b,aireDecoupe,volumeBrut:aireDecoupe*t,volumeNet});
  }
  const contour=P.map(q=>q.slice()),coupePlan=[{nature:'diagonale dans le plan',angle:45,inclinaisonScie:0}];
  ajout('C1','Dessus pentagonal',P,H-t,t,contour,coupePlan,P.map(([x,y])=>[x,y,H]));
  ajout('C2','Dessous pentagonal',P,0,t,contour,coupePlan,P.map(([x,y])=>[x,y,0]));
  const rect=(a,b)=>[[0,0],[a,0],[a,b],[0,b]],face=(a,b)=>[...([t,H-t].map(z=>[...miroir(a),z])),...([H-t,t].map(z=>[...miroir(b),z]))];
  const joue=[[0,r],[t,r+k*t],[t,e],[0,e]].map(miroir),autre=[[L-t,0],[L,0],[L,e],[L-t,e]].map(miroir);
  ajout('C3','Joue côté chanfrein',joue,t,h,rect(e-r,h),[{extremite:'jonction diagonale',inclinaisonScie:22.5,retraitDos:k*t},{extremite:'parement opposé',inclinaisonScie:0}],face([0,r],[0,e]),e-r);
  ajout('C4','Joue opposée',autre,t,h,rect(e,h),[{extremite:'A et B',inclinaisonScie:0}],face([L,0],[L,e]),e);
  const D=r*Math.SQRT2,diag=[[0,r],[r,0],[r+t*Math.SQRT2,0],[t,r+k*t]].map(miroir);
  ajout('C5','Panneau diagonal',diag,t,h,rect(D+t,h),[{extremite:'jonction joue',inclinaisonScie:22.5,retraitDos:k*t},{extremite:'parement ouvert',inclinaisonScie:45,retraitDos:t}],face([0,r],[r,0]),D);
  pieces[4].coupeEpaisseur=[[0,0],[D,0],[D+t,t],[k*t,t]];
  pieces[2].coupeEpaisseur=[[0,0],[e-r,0],[e-r,t],[k*t,t]];
  return{...g,version:1,fabricable:true,erreurs:[],pieces,
    hypotheses:[g.hypotheses[0],'CP à l’intérieur de l’enveloppe ; A et B ouverts. Dessus/dessous filants, panneaux verticaux entre.','Contours de découpe avant biseaux ; faces, volumes et contacts après biseaux.'],
    assemblage:'Dessus/dessous pentagonaux filants ; joues et diagonale entre. Onglets 22,5° à la jonction ; diagonale coupée à 45° au parement ouvert. Faces coffrantes vers le béton.',
    contacts:[{pieces:['C3','C5'],segment:[[0,r],[t,r+k*t]].map(miroir),z:[t,H-t],nature:'onglet sans recouvrement'},
      ...['C3','C4','C5'].flatMap(id=>[{pieces:['C1',id],z:H-t,nature:'contact plan'},{pieces:['C2',id],z:t,nature:'contact plan'}])],
    ouvertures:{A:{y:0},B:{y:e}},
    limites:['Pièces monoblocs, sans raccord CP ; format du panneau à vérifier par le moteur.',
      'Faces A/B ouvertes. Surface de débit = découpe avant biseaux ; volume net après biseaux distinct du volume brut.',
      'Tenue mécanique, fixations et maintien sur chantier non vérifiés.'],limite:'Assemblage géométrique défini ; tenue mécanique et maintien à vérifier sur chantier.'};
}
root.CPI=Object.assign(root.CPI||{},{geometriesParticulieres:{chanfrein45,chanfrein45Fabrication}});
})(typeof globalThis!=='undefined'?globalThis:this);
