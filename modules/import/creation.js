// Phase 9C : proposition puis préparation d'un ouvrage confirmé. Aucun accès au projet ni au DOM.
// Valeurs en mm seulement ; les mesures/calculs de l'analyse exigent une confirmation d'échelle.
(function(root){'use strict';
const clone=x=>JSON.parse(JSON.stringify(x)),positif=x=>typeof x==='number'&&Number.isFinite(x)&&x>0;
const toleranceValide=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0;
const CHAMPS={L:'ouverture.largeur_suivant_paroi_mm',h:'ouverture.hauteur_mm',D:'ouverture.diametre_mm',e:'support.epaisseur_mm',R:'support.rayon_interieur_mm',profondeur:'ouverture.traversee_mm',fL:'detail.largeur_feuillure_mm',fH:'detail.profondeur_feuillure_mm',fNiv:'detail.depart_feuillure_mm'};
function proposer(analyse,saisie,ctx){
  const a=analyse||{},s=saisie||{},o=ctx||{},valeurs={},origines={},manquants=[],alertes=[...(a.incertitudes||[]),'Proposition pour une traversée normale : seules la feuillure périphérique et la variante chanfrein 45° qualifiées sont prises en charge ; les autres détails restent à étudier.'];
  for(const [k,path] of Object.entries(CHAMPS)){
    const [g,n]=path.split('.'),v=a[g]&&a[g][n],p=(a.provenance||{})[path];
    const admissible=x=>k==='fNiv'?toleranceValide(x):positif(x);
    const sur=admissible(v)&&p&&(p.origine==='saisie'||p.origine==='cote_explicite'||o.mesuresConfirmees===true);
    valeurs[k]=Object.hasOwn(s,k)?(admissible(s[k])?s[k]:null):sur?v:null;
    origines[k]=Object.hasOwn(s,k)?{origine:valeurs[k]==null?'inconnue':'saisie',avant:sur?{valeur:v,provenance:p}:null}:sur?clone(p):{origine:'inconnue'};
  }
  const type=Object.hasOwn(s,'type')?s.type:a.ouverture&&a.ouverture.type||null,support=Object.hasOwn(s,'support')?s.support:a.support&&a.support.type||'inconnu';
  const joues=s.joues||null,largeurRef=s.largeurRef||null;
  const tolerance=Object.hasOwn(s,'tolerance')?(toleranceValide(s.tolerance)?s.tolerance:null):toleranceValide(o.tolerance)?o.tolerance:null;
  origines.tolerance={origine:tolerance==null?'inconnue':Object.hasOwn(s,'tolerance')?'saisie':'profil',source:Object.hasOwn(s,'tolerance')?'ouvrage':o.toleranceSource||'ouvrage'};
  for(const k of ['type','support','joues','largeurRef'])origines[k]={origine:Object.hasOwn(s,k)?'saisie':k==='type'||k==='support'?'analyse':'inconnue'};
  if(Object.hasOwn(s,'tolerance')&&s.tolerance!=null&&!toleranceValide(s.tolerance))manquants.push('tolérance de courbure valide (positive ou nulle)');
  if(type==='circ'){valeurs.L=valeurs.h=valeurs.e=valeurs.R=null;}else{valeurs.D=null;valeurs.profondeur=null;}
  if(support!=='voile_circulaire')valeurs.R=null;
  const requis=(k,lib)=>{if(!positif(valeurs[k]))manquants.push(lib)};
  if(!['rect','carre','circ'].includes(type))manquants.push('forme de l’ouverture');
  if(!['voile_droit','voile_circulaire'].includes(support))manquants.push('nature du support');
  if(type!=='circ')requis('e','épaisseur du voile');
  if(type==='circ'){requis('D','diamètre de l’ouverture');requis('profondeur','longueur de traversée du fourreau');}
  else{requis('L','largeur horizontale');requis('h','hauteur de l’ouverture');}
  if(!s.traversee)manquants.push('confirmation de la traversée normale au voile (sans biais ni pente)');
  let geometrie=null,fleches={interieure:null,exterieure:null},recommandation='a_determiner',solutions=[];
  if(support==='voile_circulaire'&&type!=='circ'){
    requis('R','rayon intérieur');
    if(!['par','rad'].includes(joues))manquants.push('joues parallèles ou radiales');
    if(type!=='circ'){
      const attendu=joues==='rad'?'exterieure':'commune';
      if(largeurRef!==attendu)manquants.push(joues==='rad'?'L doit être la corde extérieure (pas un développé ni une corde intérieure)':'L doit être la corde commune aux deux parements (pas un développé)');
      if(['par','rad'].includes(joues)&&['L','e','R'].every(k=>positif(valeurs[k]))&&o.voileGeo){
        geometrie=o.voileGeo({L:valeurs.L,l:valeurs.e,DcuveM:valeurs.R*2/1000,dRef:'int',joues,ep:0});
        if(!geometrie.ok)manquants.push('corde compatible avec les rayons');
        else if(o.sag){fleches={interieure:o.sag(geometrie.Ri,geometrie.cInt),exterieure:o.sag(geometrie.Re,geometrie.cExt)};
          if(!Object.values(fleches).every(Number.isFinite))manquants.push('flèches calculables');}
      }
    }
  }
  if(type==='circ'){solutions=['fourreau'];recommandation='fourreau';alertes.push('Fourreau : longueur de traversée, orientation, matériau et maintien à vérifier sur le chantier. Épaisseur, rayon et joues du voile ne sont pas utilisés par le modèle de fourreau.');}
  else if(support==='voile_droit'){solutions=['simple'];recommandation='simple';}
  else if(support==='voile_circulaire'){
    solutions=['cintre'];
    const f=fleches.interieure!=null&&fleches.exterieure!=null?Math.max(...Object.values(fleches)):null;
    if(tolerance!=null&&f!=null){recommandation=f<=tolerance&&joues==='par'?'simple':'cintre';if(recommandation==='simple')solutions.unshift('simple');}
    else alertes.push('Tolérance de courbure non renseignée ou géométrie incomplète : aucune nécessité de cintrage décidée automatiquement.');
    alertes.push('Solution simple : approximation à joues parallèles, seulement si les deux flèches respectent la tolérance confirmée.');
  }
  for(const [k,v] of Object.entries(fleches))origines['fleche_'+k]={origine:v==null?'inconnue':'calcul',source:'GEO.sag'};
  const solution=s.solution||null;if(!solution)manquants.push('solution de coffrage');else if(!solutions.includes(solution))manquants.push('solution compatible avec les données et la tolérance');
  const detail=s.detail||'aucun';
  if(detail==='feuillure'){
    if(!['rect','carre'].includes(type)||support!=='voile_droit'||solution!=='simple')manquants.push('feuillure : rectangle, voile droit et solution simple requis');
    requis('fL','largeur de feuillure');requis('fH','profondeur de feuillure');
    if(!toleranceValide(valeurs.fNiv))manquants.push('départ de feuillure depuis le parement A');
    if(valeurs.fNiv!=null&&valeurs.fH!=null&&valeurs.e!=null&&valeurs.fNiv+valeurs.fH>valeurs.e)manquants.push('départ + profondeur de feuillure dépasse la traversée');
  }else{for(const k of ['fL','fH','fNiv'])valeurs[k]=null;if(!['aucun','chanfrein45'].includes(detail))manquants.push('géométrie à étudier : fabrication indisponible pour ce détail');}
  let fabricationChanfrein=null;
  if(detail==='chanfrein45'){
    fabricationChanfrein=root.CPI.geometriesParticulieres.chanfrein45Fabrication({L:valeurs.L,H:valeurs.h,e:valeurs.e,retrait:s.retrait,ep:s.epChanfrein,angle:s.angleChanfrein,orientation:s.orientationChanfrein,version:1},
      {L:origines.L,H:origines.h,e:origines.e,retrait:{origine:positif(s.retrait)?'saisie':'inconnue'},ep:{origine:positif(s.epChanfrein)?'saisie':'inconnue'},angle:{origine:s.angleChanfrein?'saisie':'inconnue'},orientation:{origine:s.orientationChanfrein?'saisie':'inconnue'}});
    if(!['rect','carre'].includes(type)||support!=='voile_droit'||solution!=='simple')manquants.push('chanfrein : rectangle, voile droit et solution simple requis');
    if(s.confirmChanfrein!==true)manquants.push('confirmation du coin, de l’orientation, des coupes et de l’assemblage');
    manquants.push(...fabricationChanfrein.erreurs);
  }
  return{...(detail==='chanfrein45'?{fabricationChanfrein}:{}),detail,valeurs,origines,type,support,joues,largeurRef,tolerance,fleches,geometrie,geometrieSource:geometrie?'voileGeo':null,recommandation,solutions,solution,manquants:[...new Set(manquants)],alertes:[...new Set(alertes)],validation_utilisateur_requise:true};
}
function preparer(proposition,confirmation,ctx){
  const p=proposition,k=confirmation||{},o=ctx||{};
  if(k.confirme!==true)return{ok:false,messages:['Confirmation explicite requise']};
  if(!p||p.manquants.length)return{ok:false,messages:p?p.manquants:['Proposition absente']};
  if(p.type==='carre'&&p.valeurs.L!==p.valeurs.h)return{ok:false,messages:['Une ouverture carrée exige largeur = hauteur ; choisir rectangulaire sinon']};
  if(p.detail==='chanfrein45'&&!p.fabricationChanfrein?.fabricable)return{ok:false,messages:['Assemblage chanfreiné non calculé ou indisponible']};
  const forme=p.solution==='fourreau'?'circ':p.solution==='cintre'?'voile':'para',mod=o.modele;
  if(!mod||mod.forme!==forme)return{ok:false,messages:['Modèle de fabrication absent']};
  const d=modele(p,mod,k.ref);
  const M=o.moteur,c=M.canon(M.migr(d)),g=forme==='voile'?M.voileGeo(c):null;
  const E=M.limErr(c),W=E.length?[]:M.checks(c,g),messages=E.map(x=>x.msg).concat(W.filter(x=>x[0]!=='warn').map(x=>x[1]));
  if(forme==='voile'&&(!g||!g.ok))messages.push('Géométrie du voile impossible');
  if(messages.length||M.badDims(W))return{ok:false,messages};
  return{ok:true,plan:d,alertes:W.filter(x=>x[0]==='warn').map(x=>x[1])};
}
// Construction d'un brouillon sans accès au projet, partagée avec l'aperçu.
function modele(p,mod,ref){
  const forme=p.solution==='fourreau'?'circ':p.solution==='cintre'?'voile':'para';
  const v=p.valeurs,d=Object.assign(clone(mod),{forme,ref:String(ref||'').trim().toUpperCase(),nb:1});delete d.uid;delete d.origineImport;
  if(forme==='circ')Object.assign(d,{D:v.D,h:v.profondeur});
  else if(forme==='para'){delete d.chanfrein45;delete d.feuilTraversee;delete d.feuil;Object.assign(d,{ppB:v.L,ppH:v.h,ppE:v.e,ppA:0,ppBe:0,h:v.h});if(p.detail==='feuillure')Object.assign(d,{feuilTraversee:true,fL:v.fL,fH:v.fH,fNiv:v.fNiv});if(p.detail==='chanfrein45'){const c=p.fabricationChanfrein.parametres;d.chanfrein45={version:1,retrait:c.retrait,angle:c.angle,orientation:c.orientation};d.cp.j.e=c.ep;d.ep=c.ep;d.ppTr=true;}}
  else Object.assign(d,{L:v.L,l:v.e,h:v.h,DcuveM:v.R*2/1000,dRef:'int',joues:p.joues,constr:'mannequin'});
  return d;
}
root.CPI=Object.assign(root.CPI||{},{creation:{proposer,preparer,modele}});
})(typeof globalThis!=='undefined'?globalThis:this);
