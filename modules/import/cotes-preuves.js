// Phase 10A : preuves écrites uniquement. Pas de DOM, stockage, mesure ni formule de fabrication.
(function(root){'use strict';
const MM={mm:1,cm:10,m:1000},clone=x=>JSON.parse(JSON.stringify(x));
const CHAMPS={L:'ouverture.largeur_suivant_paroi_mm',h:'ouverture.hauteur_mm',D:'ouverture.diametre_mm',e:'support.epaisseur_mm',R:'support.rayon_interieur_mm',profondeur:'ouverture.traversee_mm'};
const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const rep=s=>root.CPI.nomenclatures.cleRep(String(s||'').replace(/^[^A-Za-z0-9]+|[^A-Za-z0-9]+$/g,''));
const roles=[['e',/\b(?:epaisseur(?:\s+(?:du|de))?\s+(?:voile|support|mur)|ep\.?\s+(?:voile|support|mur))\s*[:=]?\s*$/i],
 ['R',/\b(?:rayon\s+interieur|r\s*int\.?)\s*[:=]?\s*$/i],
 ['Rext',/\b(?:rayon\s+exterieur|r\s*ext\.?)\s*[:=]?\s*$/i],
 ['Dint',/(?:diametre\s+interieur|[Øø]\s*int\.?)\s*[:=]?\s*$/i],
 ['Dext',/(?:diametre\s+exterieur|[Øø]\s*ext\.?)\s*[:=]?\s*$/i],
 ['L',/\b(?:largeur(?:\s+(?:de\s+la\s+)?reservation)?|corde\s+commune|corde\s+exterieure)\s*[:=]?\s*$/i],
 ['h',/\bhauteur(?:\s+(?:de\s+la\s+)?reservation)?\s*[:=]?\s*$/i],
 ['D',/(?:diametre\s+(?:de\s+la\s+)?(?:reservation|ouverture)|(?:reservation|ouverture)\s*[Øø])\s*[:=]?\s*$/i],
 ['profondeur',/\b(?:longueur\s+de\s+traversee|traversee\s+normale)\s*[:=]?\s*$/i]];
const DETAIL=/\b(chanfrein\w*|feuillure\w*|decrochement\w*|multi[ -]?sections?|plusieurs\s+sections|traversee\s+(?:biaise\w*|incline\w*)|biais\w*)\b/i;
function analyser(ctx){const o=ctx||{},a=o.analyse||{},candidats=[],details=[],krep=rep(o.repere),homonyme=!!o.homonyme;
  for(const [champ,path] of Object.entries(CHAMPS)){
    const [g,k]=path.split('.'),p=(a.provenance||{})[path],v=a[g]&&a[g][k];
    if(v>0&&p&&p.origine==='cote_explicite')candidats.push({id:'source-'+champ,champ,valeur_mm:v,brut:p.detail||String(v),unite:'mm',uniteOrigine:champ==='L'||champ==='h'||champ==='D'?(a.source||{}).uniteRetenue||null:null,
      page:(a.source||{}).page||null,vue:null,zone:o.zoneTable||null,statut:'exploitable',raison:'Cote explicite déjà attribuée par la nomenclature / analyse existante',source:clone(p),origine:'analyse',automatique:true});
  }
  for(const t of o.textes||[]){const lecture=String(t.texte||''),brut=t.ocr?String(t.ocr.brut??lecture):lecture,s=norm(lecture),vues=(o.vues||[]).filter(v=>v.page===t.page&&!v.incertaine&&v.region&&t.x>=v.region[0]&&t.x<=v.region[2]&&t.y>=v.region[1]&&t.y<=v.region[3]),vue=vues.length===1?vues[0]:null;
    const mots=lecture.match(/[\p{L}\p{N}_-]+/gu)||[],explicite=!!krep&&mots.some(m=>rep(m)===krep),oc=(o.occurrences||[]).filter(x=>x.fiable&&x.vue&&vue&&x.vue===vue.id&&x.page===t.page&&(x.nature||'repere')==='repere');
    const fiable=!t.ocr||(t.ocr.conf>=90&&!(t.ocr.corrections||[]).length);
    const mentions=new Set((lecture.match(/\b[A-Za-z]{1,5}[-_]?\d{1,6}\b/g)||[]).map(rep));
    const lie=!homonyme&&explicite&&fiable&&mentions.size===1;
    const raison=homonyme?'Repère homonyme dans plusieurs lignes : affectation à confirmer':lie?'Repère exact et rôle écrits dans la même annotation':explicite?'Annotation avec repère : lecture ou portée ambiguë à confirmer':oc.length?'Même vue qu’un repère fiable ; lien à confirmer':'Aucun lien fiable avec cette réservation';
    const h=Math.max(1,t.h||4),zone={page:t.page,x0:t.x-(t.w||h)/2,y0:t.y-h,y1:t.y+h,x1:t.x+(t.w||h)/2};
    if(DETAIL.test(s)&&(explicite||oc.length))details.push({id:'detail-'+t.id,type:'mention_textuelle',brut,page:t.page,vue:vue?vue.id:null,zone,raison,statut:'a_examiner',fabrication_disponible:false});
    // Nombre et unité explicites, unité isolée (ne pas lire m dans m²). Aucune unité de cartouche héritée.
    const rx=/(?:(?<![\p{L}\p{N}.,+\-])|(?<=[Øø]))(\d+(?:[.,]\d+)?)(?![\d.,])(?:[ \t]*(mm|cm|m)(?![\p{L}\p{N}²³]))?/giu;let m;
    while((m=rx.exec(lecture))){const avant=s.slice(0,m.index),role=roles.find(([,r])=>r.test(avant)),champ=/\bdevelopp\w*\b/.test(avant)?'developpe':role?role[0]:'autre';
      if(!role&&!m[2])continue;
      const unite=m[2]?m[2].toLowerCase():null,v=unite?Number(m[1].replace(',','.'))*MM[unite]:null;if(unite&&!(v>0))continue;
      candidats.push({id:String(t.id)+'-'+m.index,champ,brut,lecture,valeur_brute:m[1],unite,valeur_mm:v,page:t.page,vue:vue?vue.id:null,titreVue:vue?vue.titre:null,zone,
        referenceLargeur:champ==='L'?/corde\s+exterieure/.test(avant)?'exterieure':/corde\s+commune/.test(avant)?'commune':null:null,
        statut:!unite?'inconnu':lie&&CHAMPS[champ]?'exploitable':CHAMPS[champ]?'a_confirmer':'inconnu',raison,source:{id:t.id,ocr:t.ocr?clone(t.ocr):null},origine:'texte',automatique:lie&&!!CHAMPS[champ]&&v>0});
    }
  }
  for(const c of o.contours||[]){if(!['rect','carre','circ'].includes(c.type)||!c.reconstruction&&['rect','carre'].includes(c.type)&&c.geometrie&&c.geometrie.points&&c.geometrie.points.length>5)details.push({id:'forme-'+c.id,type:'forme_non_reconnue',brut:'Forme particulière non reconnue ; ne pas assimiler à un rectangle',page:c.source&&c.source.page,vue:c.vue||null,raison:'Contour associé hors des formes prises en charge',statut:'a_examiner',fabrication_disponible:false});}
  const conflits=[];
  for(const champ of Object.keys(CHAMPS)){const cs=candidats.filter(c=>c.champ===champ&&c.automatique),valeurs=[...new Set(cs.map(c=>c.valeur_mm))];
    if(valeurs.length>1){conflits.push({champ,candidats:cs.map(c=>c.id),valeurs});cs.forEach(c=>{c.statut='contradictoire';c.automatique=false})}}
  return{candidats,details,conflits};
}
// Une affectation constitue une validation explicite du rôle et de la lecture, sans conversion de diamètre/rayon.
function affecter(dossier,id,champ){const c=dossier.candidats.find(c=>c.id===id);if(!c||!CHAMPS[champ]||!(c.valeur_mm>0))return null;
  if(['Dint','Dext','Rext'].includes(c.champ)&&champ==='R'||c.champ==='developpe'&&champ==='L')return null;
  return{valeur:c.valeur_mm,origine:'cote_explicite',statut:'confirmee',role_confirme:champ,candidate:clone(c)};
}
root.CPI=Object.assign(root.CPI||{},{cotesPreuves:{analyser,affecter,CHAMPS}});
})(typeof globalThis!=='undefined'?globalThis:this);
