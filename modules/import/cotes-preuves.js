// Phase 10A : preuves écrites uniquement. Pas de DOM, stockage, mesure ni formule de fabrication.
(function(root){'use strict';
const MM={mm:1,cm:10,m:1000},clone=x=>JSON.parse(JSON.stringify(x));
const CHAMPS={L:'ouverture.largeur_suivant_paroi_mm',h:'ouverture.hauteur_mm',D:'ouverture.diametre_mm',e:'support.epaisseur_mm',R:'support.rayon_interieur_mm',profondeur:'ouverture.traversee_mm',fL:'detail.largeur_feuillure_mm',fH:'detail.profondeur_feuillure_mm',fNiv:'detail.depart_feuillure_mm'};
const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const rep=s=>root.CPI.nomenclatures.cleRep(String(s||'').replace(/^[^A-Za-z0-9]+|[^A-Za-z0-9]+$/g,''));
const roles=[['fL',/\blargeur(?:\s+de)?\s+feuillure\s*[:=]?\s*$/i],['fH',/\bprofondeur(?:\s+de)?\s+feuillure\s*[:=]?\s*$/i],['fNiv',/\bdepart(?:\s+de)?\s+feuillure\s*[:=]?\s*$/i],['e',/\b(?:epaisseur(?:\s+(?:du|de))?\s+(?:voile|support|mur)|ep\.?\s+(?:voile|support|mur))\s*[:=]?\s*$/i],
 ['R',/\b(?:rayon\s+interieur|r\s*int\.?)\s*[:=]?\s*$/i],
 ['Rext',/\b(?:rayon\s+exterieur|r\s*ext\.?)\s*[:=]?\s*$/i],
 ['Dint',/(?:diametre\s+interieur|[Øø]\s*int\.?)\s*[:=]?\s*$/i],
 ['Dext',/(?:diametre\s+exterieur|[Øø]\s*ext\.?)\s*[:=]?\s*$/i],
 ['L',/\b(?:largeur(?:\s+(?:de\s+la\s+)?reservation)?|corde\s+commune|corde\s+exterieure)\s*[:=]?\s*$/i],
 ['h',/\bhauteur(?:\s+(?:de\s+la\s+)?reservation)?\s*[:=]?\s*$/i],
 ['D',/(?:diametre\s+(?:de\s+la\s+)?(?:reservation|ouverture)|(?:reservation|ouverture)\s*[Øø])\s*[:=]?\s*$/i],
 ['profondeur',/\b(?:longueur\s+de\s+traversee|traversee\s+normale)\s*[:=]?\s*$/i]];
const DETAIL=/\b(chanfrein\w*|feuillure\w*|decrochement\w*|multi[ -]?sections?|plusieurs\s+sections|traversee\s+(?:biaise\w*|incline\w*)|biais\w*)\b/i;
// Conventions explicites : virgule décimale, groupes de trois chiffres séparés par
// espace/NBSP/espace fine ; point décimal seulement hors groupement ambigu à trois chiffres.
function nombre(brut,zero=false){const t=String(brut).trim(),invalide=raison=>({etat:'invalide',normalisee:null,valeur:null,raison});
  if(!/^[+]?\d[\d., \u00a0\u202f]*$/.test(t))return invalide('Dimension positive attendue, notation non reconnue');
  const ambigu=raison=>({etat:'ambigue',normalisee:null,valeur:null,raison});
  if(t.includes('.')&&(t.includes(',')||t.split('.').length>2||/\.\d{3}$/.test(t)))return ambigu('Séparateurs numériques ambigus : confirmer la valeur en millimètres');
  const entier=t.split(/[.,]/)[0];
  if(/[ \u00a0\u202f]/.test(entier)&&!/^\+?\d{1,3}(?:[ \u00a0\u202f]\d{3})+$/.test(entier))return invalide('Groupement de milliers irrégulier');
  if(!/^\+?(?:\d+|\d{1,3}(?:[ \u00a0\u202f]\d{3})+)(?:[.,]\d+)?$/.test(t))return invalide('Notation numérique non reconnue');
  const normalisee=t.replace(/[ \u00a0\u202f]/g,'').replace(',','.'),valeur=Number(normalisee);
  if(!Number.isFinite(valeur)||(zero?valeur<0:valeur<=0))return invalide('Dimension finie strictement positive requise');
  return{etat:'valide',normalisee,valeur,raison:null};
}
function analyser(ctx){const o=ctx||{},a=o.analyse||{},candidats=[],details=[],indicesNonAttribues=[],krep=rep(o.repere),homonyme=!!o.homonyme;
  for(const [champ,path] of Object.entries(CHAMPS)){
    const [g,k]=path.split('.'),p=(a.provenance||{})[path],v=a[g]&&a[g][k];
    if(Number.isFinite(v)&&(champ==='fNiv'?v>=0:v>0)&&p&&p.origine==='cote_explicite')candidats.push({id:'source-'+champ,champ,valeur_mm:v,brut:p.detail||String(v),unite:'mm',uniteOrigine:champ==='L'||champ==='h'||champ==='D'?(a.source||{}).uniteRetenue||null:null,
      page:(a.source||{}).page||null,vue:null,zone:o.zoneTable||null,statut:'exploitable',raison:'Cote explicite déjà attribuée par la nomenclature / analyse existante',source:clone(p),origine:'analyse',automatique:true});
  }
  for(const t of o.textes||[]){const lecture=String(t.texte||''),brut=t.ocr?String(t.ocr.brut??lecture):lecture,s=norm(lecture),vues=(o.vues||[]).filter(v=>v.page===t.page&&!v.incertaine&&v.region&&t.x>=v.region[0]&&t.x<=v.region[2]&&t.y>=v.region[1]&&t.y<=v.region[3]),vue=vues.length===1?vues[0]:null;
    const mots=lecture.match(/[\p{L}\p{N}_-]+/gu)||[],explicite=!!krep&&mots.some(m=>rep(m)===krep),oc=(o.occurrences||[]).filter(x=>x.fiable&&x.vue&&vue&&x.vue===vue.id&&x.page===t.page&&(x.nature||'repere')==='repere');
    const fiable=!t.ocr||(t.ocr.conf>=90&&!(t.ocr.corrections||[]).length);
    const mentions=new Set((lecture.match(/\b[A-Za-z]{1,5}[-_]?\d{1,6}\b/g)||[]).map(rep));
    const lie=!homonyme&&explicite&&fiable&&mentions.size===1;
    const raison=homonyme?'Repère homonyme dans plusieurs lignes : affectation à confirmer':lie?'Repère exact et rôle écrits dans la même annotation':explicite?'Annotation avec repère : lecture ou portée ambiguë à confirmer':oc.length?'Même vue qu’un repère fiable ; lien à confirmer':'Aucun lien fiable avec cette réservation';
    const h=Math.max(1,t.h||4),zone={page:t.page,x0:t.x-(t.w||h)/2,y0:t.y-h,y1:t.y+h,x1:t.x+(t.w||h)/2};
    if(DETAIL.test(s)){
      const motif=mentions.size&&!explicite?'Annotation désignant un autre repère : non attribuée à cette réservation':mentions.size>1?'Plusieurs repères : portée ambiguë':!mentions.size?'Mention sans repère : la vue commune ne prouve pas son attribution':raison;
      const d={id:'detail-'+t.id,type:'mention_textuelle',brut,page:t.page,vue:vue?vue.id:null,zone,raison:motif,reperes:[...mentions],statut:lie?'attribue':'non_attribue',fabrication_disponible:false};
      (lie?details:indicesNonAttribues).push(d);
    }
    // Nombre et unité explicites, unité isolée (ne pas lire m dans m²). Aucune unité de cartouche héritée.
    const rx=/(?:(?<![\p{L}\p{N}.,+\-−])|(?<=[Øø]))([+\-−]?\d(?:[\d.,]|[ \u00a0\u202f]+(?=[\d.,]))*)(?:[ \t\u00a0\u202f]*(mm|cm|m)(?![\p{L}\p{N}²³]))?/giu;let m;
    while((m=rx.exec(lecture))){const avant=s.slice(0,m.index),role=roles.find(([,r])=>r.test(avant)),champ=/\bdevelopp\w*\b/.test(avant)?'developpe':role?role[0]:'autre';
      if(!role&&!m[2])continue;
      const unite=m[2]?m[2].toLowerCase():null,numerique=nombre(m[1],champ==='fNiv'),conversion=unite&&numerique.etat==='valide'?numerique.valeur*MM[unite]:null,
        v=Number.isFinite(conversion)&&(champ==='fNiv'?conversion>=0:conversion>0)?conversion:null;
      if(unite&&numerique.etat==='valide'&&v==null)Object.assign(numerique,{etat:'invalide',valeur:null,normalisee:null,raison:'Conversion en millimètres non finie ou non positive'});
      candidats.push({id:String(t.id)+'-'+m.index,champ,brut,lecture,valeur_brute:m[1],unite,numerique,valeur_mm:v,page:t.page,vue:vue?vue.id:null,titreVue:vue?vue.titre:null,zone,
        referenceLargeur:champ==='L'?/corde\s+exterieure/.test(avant)?'exterieure':/corde\s+commune/.test(avant)?'commune':null:null,
        statut:numerique.etat==='ambigue'?'ambigue':numerique.etat==='invalide'?'invalide':!unite?'inconnu':lie&&CHAMPS[champ]?'exploitable':CHAMPS[champ]?'a_confirmer':'inconnu',raison,source:{id:t.id,ocr:t.ocr?clone(t.ocr):null},origine:'texte',automatique:lie&&!!CHAMPS[champ]&&v!=null});
    }
  }
  for(const c of o.contours||[]){if(!['rect','carre','circ'].includes(c.type)||!c.reconstruction&&['rect','carre'].includes(c.type)&&c.geometrie&&c.geometrie.points&&c.geometrie.points.length>5)details.push({id:'forme-'+c.id,type:'forme_non_reconnue',brut:'Forme particulière non reconnue ; ne pas assimiler à un rectangle',page:c.source&&c.source.page,vue:c.vue||null,raison:'Contour associé hors des formes prises en charge',statut:'a_examiner',fabrication_disponible:false});}
  const conflits=[];
  for(const champ of Object.keys(CHAMPS)){const cs=candidats.filter(c=>c.champ===champ&&c.automatique),valeurs=[...new Set(cs.map(c=>c.valeur_mm))];
    if(valeurs.length>1){conflits.push({champ,candidats:cs.map(c=>c.id),valeurs});cs.forEach(c=>{c.statut='contradictoire';c.automatique=false})}}
  return{candidats,details,indicesNonAttribues,conflits};
}
// Une affectation constitue une validation explicite du rôle et de la lecture, sans conversion de diamètre/rayon.
function affecter(dossier,id,champ,saisie){const c=dossier.candidats.find(c=>c.id===id);if(!c||!CHAMPS[champ])return null;
  const n=saisie!=null?nombre(saisie,champ==='fNiv'):null,v=n?n.valeur:c.valeur_mm;
  if(!Number.isFinite(v)||!(champ==='fNiv'?v>=0:v>0))return null;
  if(['Dint','Dext','Rext'].includes(c.champ)&&champ==='R'||c.champ==='developpe'&&champ==='L')return null;
  return{valeur:v,...(n?{interpretation:{brut:saisie,unite:'mm',normalisee:n.normalisee,valeur_mm:v,statut:'confirmee'}}:{}),origine:n?'saisie':'cote_explicite',statut:'confirmee',role_confirme:champ,candidate:clone(c)};
}
root.CPI=Object.assign(root.CPI||{},{cotesPreuves:{analyser,affecter,nombre,CHAMPS}});
})(typeof globalThis!=='undefined'?globalThis:this);
