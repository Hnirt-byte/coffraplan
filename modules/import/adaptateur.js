// CoffraPlan — module d'import de plans, composant C : adaptateur CoffraPlan.
// Convertit UNE réservation confirmée par l'utilisateur en plan au format existant (celui de coll()), puis la fait
// contrôler par le moteur (migr → canon → limErr / checks), reçu en paramètre : aucun calcul dupliqué, aucun accès
// direct aux variables de l'appli. Ne touche jamais aux plans enregistrés : renvoie un nouvel objet.
(function(root){'use strict';
const MM={mm:1,cm:10,m:1000};
const FORMES={rect:['rect','carre','rect_fond','carre_fond'],circ:['circ']};
const enMM=(v,u)=>Math.round(v*MM[u]*100)/100;   // 0,01 mm : efface le bruit des conversions (1,2 m → 1200)
const non=(raison,message,x)=>Object.assign({ok:false,raison,message},x||{});

// candidat : sortie du détecteur ; confirmation : {confirme:true, forme?, h? (mm), unite?, ref?, nb?}
// ctx : {moteur:{migr,canon,limErr,checks,badDims}, modele: plan de la forme visée (coll() du formulaire, comme openSeries)}
// → {ok:true, plan, provenance, alertes} | {ok:false, raison, message, manquants?, messages?, plan?}
function versPlan(candidat,confirmation,ctx){
  const k=confirmation||{};
  if(k.confirme!==true)return non('non_confirme','Réservation non confirmée par l\'utilisateur');
  if(!candidat||candidat.statut!=='a_confirmer'||!FORMES[candidat.type])return non('non_pris_en_charge','Géométrie non prise en charge',{messages:(candidat&&candidat.remarques)||[]});
  const unite=k.unite||candidat.unite,manquants=[];
  if(!MM[unite])manquants.push('unite');
  if(!(k.h>0||candidat.h>0))manquants.push('h');
  if(manquants.length)return non('a_completer','Informations à compléter : '+manquants.join(', '),{manquants});
  const h=k.h>0?k.h:enMM(candidat.h,unite),D=candidat.dims,dims=candidat.type==='circ'?{D:enMM(D.D,unite),h}:{L:enMM(D.L,unite),l:enMM(D.l,unite),h};
  const forme=k.forme||(candidat.type==='circ'?'circ':Math.abs(dims.L-dims.l)<0.5?'carre':'rect');
  if(!FORMES[candidat.type].includes(forme))return non('forme_incompatible',`Forme « ${forme} » incompatible avec une réservation ${candidat.type==='circ'?'circulaire':'rectangulaire'}`);
  if(forme.startsWith('carre')){if(Math.abs(dims.L-dims.l)>=0.5)return non('forme_incompatible','Forme carrée demandée pour un rectangle');dims.l=dims.L}
  const M=ctx&&ctx.moteur,mod=ctx&&ctx.modele;
  if(!M||!mod||mod.forme!==forme)return non('modele_manquant',`Modèle de plan « ${forme} » absent (chantier, CP et options en sont repris)`);
  const plan=Object.assign(JSON.parse(JSON.stringify(mod)),dims,{ref:k.ref!=null?String(k.ref).toUpperCase():'',nb:k.nb>=1?Math.round(k.nb):1});
  delete plan.uid;
  const c=M.canon(M.migr(plan)),LE=M.limErr(c),W=LE.length?[]:M.checks(c,null);
  const messages=LE.map(x=>x.msg).concat(W.filter(x=>x[0]!=='warn').map(x=>x[1]));
  if(messages.length||M.badDims(W))return non('invalide','Le moteur refuse ces cotes',{messages,plan});
  return{ok:true,plan,alertes:W.filter(x=>x[0]==='warn').map(x=>x[1]),
    provenance:Object.assign({},candidat.source,{candidat:candidat.id,unite_source:candidat.unite,unite,centre:candidat.centre,dims_source:JSON.parse(JSON.stringify(D)),h_saisie:k.h>0})};
}

root.CPI=Object.assign(root.CPI||{},{adaptateur:{versPlan,FORMES}});
})(typeof globalThis!=='undefined'?globalThis:this);
