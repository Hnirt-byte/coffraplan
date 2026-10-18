// CoffraPlan — module d'import de plans, composant A : lecteur de plan.
// Décode un fichier source en « document normalisé » (contrat : modules/import/README.md).
// Indépendant de l'interface et du moteur : aucun accès au DOM, au stockage ni aux fonctions de app/CoffraPlan.html.
(function(root){'use strict';
const UNITES=['mm','cm','m'];
const TYPES=['polyligne','cercle','autre'];
// format → décodeur(contenu) → document normalisé. DXF, IFC et PDF vectoriel : pas encore écrits (étape suivante : DXF).
const DECODEURS={};
const pt=p=>Array.isArray(p)&&p.length>=2&&p.every(Number.isFinite);

// Contrôle d'un document normalisé (frontière de confiance : il vient d'un fichier externe)
function verifierDocument(doc){
  const err=[];
  if(!doc||typeof doc!=='object')return{ok:false,erreurs:['document absent']};
  if(typeof doc.fichier!=='string')err.push('fichier : nom absent');
  if(doc.unite!==null&&!UNITES.includes(doc.unite))err.push(`unité « ${doc.unite} » inconnue (mm, cm, m ou null si le fichier ne la donne pas)`);
  if(!Array.isArray(doc.entites))return{ok:false,erreurs:err.concat('entites : liste absente')};
  const vus=new Set();
  doc.entites.forEach((e,i)=>{const n=`entité ${i+1}`;
    if(!e||typeof e!=='object'){err.push(n+' : illisible');return}
    if(e.id==null||e.id===''){err.push(n+' : identifiant source absent')}else if(vus.has(String(e.id)))err.push(n+` : identifiant ${e.id} en double`);else vus.add(String(e.id));
    if(!TYPES.includes(e.type))err.push(n+` : type « ${e.type} » inconnu`);
    if(e.type==='cercle'&&!(pt(e.centre)&&Number.isFinite(e.r)))err.push(n+' : cercle sans centre ou rayon');
    if(e.type==='polyligne'&&!(Array.isArray(e.points)&&e.points.every(pt)))err.push(n+' : polyligne sans points lisibles');
    if(e.h!=null&&!Number.isFinite(e.h))err.push(n+' : hauteur illisible')});
  return{ok:!err.length,erreurs:err};
}

// source = {format:'normalise'|'dxf'|'ifc'|'pdf', nom, contenu}
// → {ok:true, document} | {ok:false, raison:'format_non_pris_en_charge'|'document_invalide', message, erreurs?}
function lirePlan(source){
  const fmt=source&&source.format;let doc;
  try{
    if(fmt==='normalise')doc=typeof source.contenu==='string'?JSON.parse(source.contenu):source.contenu;
    else if(DECODEURS[fmt])doc=DECODEURS[fmt](source.contenu,source.nom);
    else return{ok:false,raison:'format_non_pris_en_charge',message:`Lecture du format « ${fmt} » pas encore disponible`};
  }catch(e){return{ok:false,raison:'document_invalide',message:'Fichier illisible : '+(e&&e.message||e),erreurs:[]}}
  const v=verifierDocument(doc);
  return v.ok?{ok:true,document:doc}:{ok:false,raison:'document_invalide',message:'Document incomplet ou incohérent',erreurs:v.erreurs};
}

root.CPI=Object.assign(root.CPI||{},{lecteur:{lirePlan,verifierDocument,UNITES,DECODEURS}});
})(typeof globalThis!=='undefined'?globalThis:this);
