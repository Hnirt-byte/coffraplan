// Phase 9C : brouillon local à la fenêtre d'import, récapitulatif puis ajout explicite à P.
let DXC=null;
const dxcRep=s=>CPI.nomenclatures.cleRep(String(s||'').replace(/^[^A-Za-z0-9]+|[^A-Za-z0-9]+$/g,''));
function dxcCles(kind,i){const D=DXI,base=D.empreinte||D.nom,keys=[];
  if(kind==='n'){
    // Le repère peut être répété sur plusieurs lignes du même PDF : utiliser l'identité de la ligne source.
    const {N,L}=D.NL[i],rep=dxcRep(L.repere);
    const ligne=[N.page??'?',N.id||'?',L.id||L.rang||rep||'?'].join('|');
    keys.push(base+'|ligne|'+ligne);
    const a=dxnAS(L),ids=new Set((a.occurrences||[]).filter(o=>o.fiable&&o.contour).map(o=>o.contour));
    D.C.filter(c=>ids.has(c.id)).forEach(c=>keys.push(base+'|contour|'+dxrCle(c)));
  }else{const c=D.C[i];keys.push(base+'|contour|'+dxrCle(c));}
  return keys;
}
function dxcDeja(cles){return P.some(p=>((p.origineImport||{}).creationCles||[]).some(k=>cles.includes(k)))}
function dxcAnalyse(kind,i){const D=DXI;
  const a=kind==='n'&&D.SP&&D.SP[D.NL[i].L.id];
  const r=a?JSON.parse(JSON.stringify(a)):{ouverture:{},support:{type:'inconnu'},provenance:{},preuves:[],incertitudes:[]};
  const O=r.ouverture,p=r.provenance;
  if(kind==='n'){
    const {N,L}=D.NL[i],d=L.dims,u=dxnU(N,L),k=DXI_MM[u];
    r.source={table:N.id,ligne:L.id,page:N.page,repere:L.repere,cotes:L.dims||null,uniteRetenue:u||null,cellules:L.cellules||[],ocr:L.ocr||null};
    if(d&&k&&!d.conflitUnite){
      O.type=d.type==='circ'?'circ':d.a===d.b?'carre':'rect';
      const set=(key,v)=>{if(O[key]==null&&v>0){O[key]=v;p['ouverture.'+key]={origine:'cote_explicite',source:'nomenclature',detail:d.texte||L.ouverture}}};
      if(d.type==='circ')set('diametre_mm',d.D*k);
      else if(d.a===d.b||/larg/i.test(d.colonne||'')&&/haut/i.test(d.colonne||'')){set('largeur_suivant_paroi_mm',d.a*k);set('hauteur_mm',d.b*k)}
      else r.incertitudes.push('Cotes du tableau '+d.a*k+' × '+d.b*k+' mm : orientation horizontale / verticale à renseigner.');
    }
    if(L.a_verifier&&L.a_verifier.length)r.incertitudes.push(...L.a_verifier);
  }else{
    const c=D.C[i];O.type=c.type;r.source={candidat:c.id,source:c.source,geometrie:c.geometrie};
    r.preuves.push({type:'annotations_et_calibrage',annotations:c.annot||{},calibrage:D.cal[c.source.page]||null});
    r.incertitudes.push(...c.remarques,'Forme du contour à confirmer : une traversée circulaire peut être représentée en rectangle.');
    if(c.reconstruction)r.preuves.push({type:'contour_reconstruit',detail:c.reconstruction});
    const A=c.annot&&c.annot.cotes,dm=A&&CPI.nomenclatures.cotes(A.texte,null);
    if(dm&&dm.etat==='circ'&&DXI_MM[dm.unite]){O.diametre_mm=dm.D*DXI_MM[dm.unite];p['ouverture.diametre_mm']={origine:'cote_explicite',source:'dessin',detail:A.texte};}
    const e=D.cal[c.source.page];
    if(O.diametre_mm==null&&!c.reconstruction&&c.type==='circ'&&e&&e.k>0){O.diametre_mm=c.dims.D*e.k;p['ouverture.diametre_mm']={origine:'mesure',source:'dessin',detail:'calibrage de la page '+c.source.page};}
  }
  return r;
}
function dxcOuvrir(kind,i){const D=DXI;if(!D||D.fmt!=='pdf'||D.rJob)return;
  // Un contour déjà rattaché utilise la même identité que sa ligne de nomenclature.
  if(kind==='g'){const k=D.NR.findIndex(r=>r.geo!==''&&+r.geo===i);if(k>=0){kind='n';i=k;}}
  if(!D.M)dxiModels();
  const a=dxcAnalyse(kind,i),L=kind==='n'?D.NL[i].L:null;
  const dossier=dxcDossier(kind,i,a);
  DXC={D,kind,i,analyse:a,dossier,retenues:{},arbitrages:{},saisie:{},saisiesBrutes:{},cles:dxcCles(kind,i),ref:L?dxcRep(L.repere):'',revision:null};
  for(const c of dossier.candidats.filter(c=>c.automatique&&c.origine==='texte')){
    const path=CPI.cotesPreuves.CHAMPS[c.champ], [g,k]=path.split('.');
    a[g]=a[g]||{};a[g][k]=c.valeur_mm;a.provenance[path]={origine:'cote_explicite',source:'annotation PDF',detail:c.brut,candidate:c};
  }
  for(const c of dossier.conflits){const [g,k]=CPI.cotesPreuves.CHAMPS[c.champ].split('.');if(a[g])a[g][k]=null;}
  let z=el('dxcZ');if(!z){el('dxi').insertAdjacentHTML('beforeend','<section id="dxcZ" class="dxo" aria-label="Proposition de coffrage"></section>');z=el('dxcZ');}
  const input=(id,label)=>`<div class="fd"><label for="dxc_${id}">${label}</label><input class="fi" id="dxc_${id}" inputmode="decimal" placeholder="inconnue — à renseigner" oninput="dxcSaisie('${id}',this.value)"><small id="dxcOrig_${id}"></small></div>`;
  const select=(id,label,opts,value)=>`<div class="fd"><label for="dxc_${id}">${label}</label><select class="fi" id="dxc_${id}" onchange="dxcChoix('${id}',this.value)">${opts.map(([v,t])=>`<option value="${v}"${v===value?' selected':''}>${t}</option>`).join('')}</select></div>`;
  z.innerHTML=`<div class="ct">Proposer un coffrage — ${esc(L?L.repere:D.C[i].id)}</div>
    <p>Complétez les données, choisissez une solution puis vérifiez le récapitulatif. Rien n'est créé avant votre confirmation finale.</p>
    <div class="mu">Chantier : ${esc(D.ch||'à saisir en haut de la fenêtre')} · Ouvrage : ${esc(D.ouv||'—')}</div>
    <details><summary>Données et preuves disponibles</summary><div>${esc(L?L.cellules.filter(Boolean).join(' · '):D.C[i].id)}</div>
      <ul>${(a.incertitudes||[]).map(x=>'<li>'+esc(x)+'</li>').join('')}</ul><pre style="white-space:pre-wrap">${esc(JSON.stringify(a.preuves,null,2))}</pre></details>
    ${dxcCotesHTML()}
    <label><input type="checkbox" id="dxc_mesures" onchange="dxcRefresh()"> Je confirme les échelles utilisées pour ces mesures, dans chaque vue concernée (vérifier le calibrage dans l'aperçu).</label>
    <div class="g2">${select('type','Ouverture',[['','À choisir'],['rect','Rectangulaire'],['carre','Carrée'],['circ','Circulaire']],a.ouverture.type)}
    ${select('support','Support',[['inconnu','À confirmer'],['voile_droit','Voile droit'],['voile_circulaire','Voile circulaire']],a.support.type)}</div>
    <div class="g3">${input('L','Largeur horizontale L — corde (mm)')}${input('h','Hauteur de l’ouverture (mm)')}${input('D','Diamètre de l’ouverture (mm)')}</div>
    <div class="g3">${input('e','Épaisseur du voile (mm)')}${input('R','Rayon intérieur du voile (mm)')}${input('profondeur','Longueur de traversée du fourreau (mm)')}</div>
    <div class="g2">${select('joues','Joues du voile circulaire',[['','Choix explicite requis'],['par','Parallèles'],['rad','Radiales']],null)}
    ${select('largeurRef','Signification de L',[['','À confirmer'],['commune','Corde commune aux deux parements'],['exterieure','Corde au parement extérieur'],['autre','Développé / corde intérieure : reporter la bonne corde']],null)}</div>
    <div class="hint">L n'est pas un développé. Joues parallèles : même corde aux deux parements. Joues radiales : saisir la corde extérieure. Aucune conversion implicite entre ces valeurs.</div>
    ${input('tolerance','Tolérance de courbure de cet ouvrage (mm, facultative)')}
    <div class="mu" id="dxcTolProfil"></div>
    <label><input type="checkbox" id="dxc_traversee" onchange="dxcRefresh()"> Je confirme une traversée normale au voile, sans biais ni pente, et les contraintes de maintien.</label>
    ${select('solution','Solution à choisir',[['','À choisir'],['simple','Mannequin rectangulaire simple'],['cintre','Mannequin cintré'],['fourreau','Fourreau circulaire']],null)}
    <div class="fd"><label for="dxc_ref">Référence</label><input class="fi" id="dxc_ref" value="${esc(DXC.ref)}" placeholder="automatique" oninput="dxcRefresh()"></div>
    <div class="fd"><label for="dxc_note">Source des corrections / contraintes à conserver (facultatif)</label><input class="fi" id="dxc_note" oninput="dxcRefresh()" placeholder="Ex. coupe et unité relues, cote de traversée confirmée"></div><div id="dxcEtat" role="status"></div><button class="btn bs bo" onclick="dxcFermer()">Annuler la proposition</button>
    <button class="btn bs bpr" id="dxcRecap" onclick="dxcRecap()">Vérifier le récapitulatif</button><div id="dxcResume"></div>`;
  dxcRefresh();z.scrollIntoView({block:'start'});
}
function dxcFermer(){DXC=null;const z=el('dxcZ');if(z)z.remove()}
function dxcSaisie(k,v){if(!DXC)return;delete DXC.arbitrages[k];DXC.saisiesBrutes[k]=v;DXC.saisie[k]=v.trim()===''?null:(parseCote(v,'mm')??NaN);dxcRefresh()}
function dxcChoix(k,v){if(!DXC)return;DXC.saisie[k]=v;dxcRefresh()}
function dxcProposition(){const X=DXC,D=DXI;if(!X||X.D!==D)return null;
  const ch=profCh(D.ch)||{},ou=profOu(D.ch,D.ouv)||{},tol=ou.tolCourb!=null?ou.tolCourb:ch.tolCourb;
  const p=CPI.creation.proposer(X.analyse,Object.assign({},X.saisie,{traversee:C('dxc_traversee')}),{mesuresConfirmees:C('dxc_mesures'),tolerance:tol,toleranceSource:ou.tolCourb!=null?'profil ouvrage':'profil chantier',voileGeo,sag:GEO.sag});
  for(const [k,c] of Object.entries(X.retenues)){
    if(p.valeurs[k]!=null)p.origines[k]=p.valeurs[k]===c.valeur&&!Object.hasOwn(X.saisiesBrutes,k)?c:{origine:'saisie',avant:c,brut:X.saisiesBrutes[k],role_confirme:k};
  }
  for(const conflit of X.dossier.conflits)if(X.arbitrages[conflit.champ]!==p.valeurs[conflit.champ]||p.valeurs[conflit.champ]==null)p.manquants.push('arbitrage des cotes contradictoires : '+conflit.champ);
  if(X.dossier.details.length||C('dxc_detail'))p.manquants.push('détail particulier : étude de fabrication requise, création standard indisponible');
  const coteL=X.retenues.L?X.retenues.L.candidate:(X.analyse.provenance['ouverture.largeur_suivant_paroi_mm']||{}).candidate;
  if(p.support==='voile_circulaire'&&coteL&&coteL.referenceLargeur&&p.largeurRef!==coteL.referenceLargeur)p.manquants.push('L issue du PDF : référence de corde incompatible avec les joues choisies');
  p.cotesPdf={...X.dossier,retenues:X.retenues,arbitrages:X.arbitrages,saisiesBrutes:{...X.saisiesBrutes},valeurs:{...p.valeurs},origines:JSON.parse(JSON.stringify(p.origines)),detailUtilisateur:C('dxc_detail')?S('dxc_detailNote',''):null};
  DXI.CP[X.cles[0]]=p.cotesPdf;
  return p;
}
function dxcRefresh(){if(!DXC||DXC.D!==DXI||!el('dxcEtat'))return;
  DXC.revision=null;el('dxcResume').innerHTML='';const p=dxcProposition(),X=DXC;
  for(const k of Object.keys(p.valeurs)){
    const e=el('dxc_'+k),o=el('dxcOrig_'+k);if(e&&!Object.hasOwn(X.saisie,k))e.value=p.valeurs[k]==null?'':String(p.valeurs[k]);
    if(o)o.textContent=(p.origines[k].origine||'inconnue')+(p.origines[k].detail?' · '+p.origines[k].detail:'');
  }
  const circ=p.type==='circ',courbe=p.support==='voile_circulaire';
  for(const k of ['L','h'])el('dxc_'+k).parentElement.hidden=circ;
  for(const k of ['D','profondeur'])el('dxc_'+k).parentElement.hidden=!circ;
  for(const k of ['R','joues'])el('dxc_'+k).parentElement.hidden=!courbe||circ;
  el('dxc_e').parentElement.hidden=circ;
  el('dxc_tolerance').parentElement.hidden=circ;
  el('dxcTolProfil').hidden=circ;
  el('dxc_largeurRef').parentElement.hidden=!courbe||circ;
  if(!Object.hasOwn(X.saisie,'tolerance'))el('dxc_tolerance').value=p.tolerance==null?'':String(p.tolerance);
  el('dxcOrig_tolerance').textContent=p.origines.tolerance.origine;
  el('dxcTolProfil').textContent='Tolérance retenue : '+(p.tolerance==null?'non renseignée':nf(p.tolerance)+' mm')+' ('+p.origines.tolerance.source+'). Modifiable dans le profil chantier / ouvrage, ou ici pour cette création.';
  const manque=p.manquants.concat(!String(DXI.ch||'').trim()?['chantier']:[]),deja=dxcDeja(X.cles);
  el('dxcEtat').innerHTML=`<p><b>Proposition à confirmer : ${esc(({simple:'mannequin rectangulaire simple',cintre:'mannequin cintré',fourreau:'fourreau circulaire'})[p.recommandation]||'solution à déterminer')}</b></p>`
    +(courbe?`<div>Flèches intérieure / extérieure : ${nf(p.fleches.interieure)} / ${nf(p.fleches.exterieure)} mm (GEO.sag). Tolérance : ${nf(p.tolerance)} mm.</div>`:'')
    +`<ul>${p.alertes.map(x=>'<li>'+esc(x)+'</li>').join('')}</ul>`+(manque.length?'<p>À compléter : '+esc(manque.join(' ; '))+'</p>':'')+(deja?'<p>Cette réservation a déjà été créée dans le projet.</p>':'');
  el('dxcRecap').disabled=!!manque.length||deja;
}
function dxcPreparer(){const p=dxcProposition();if(!p)return null;const f=p.solution==='fourreau'?'circ':p.solution==='cintre'?'voile':'para';
  const m=Object.assign({},DXI.M[f],{ch:chKey(DXI.ch),ouv:ouKey(DXI.ouv)});
  const r=CPI.creation.preparer(p,{confirme:true,ref:S('dxc_ref','')},{modele:m,moteur:{migr,canon,limErr,checks,badDims,voileGeo}});
  return{p,r,note:S('dxc_note','').trim(),saisiesBrutes:Object.assign({},DXC.saisiesBrutes)};
}
function dxcRecap(){if(!DXC||DXC.D!==DXI)return;const x=dxcPreparer();if(!x)return;
  const {p,r}=x,z=el('dxcResume');if(!r.ok){z.innerHTML='<p>Non créé : '+esc(r.messages.join(' ; '))+'</p>';return;}
  if(!String(DXI.ch||'').trim()||dxcDeja(DXC.cles))return;
  DXC.revision=JSON.stringify(x);
  z.innerHTML=`<h3>Récapitulatif — un seul ouvrage, aucun existant remplacé</h3><p>${esc(r.plan.ch)} · ${esc(r.plan.ouv)} · ${esc(r.plan.ref||'référence automatique')} · ${esc(fmLb(r.plan.forme))}</p>
    <ul>${Object.entries(p.valeurs).filter(([,v])=>v!=null).map(([k,v])=>`<li>${esc(({L:'L corde',h:'Hauteur',D:'Diamètre',e:'Épaisseur voile',R:'Rayon intérieur',profondeur:'Longueur du fourreau'})[k])} : ${nf(v)} mm — ${esc(p.origines[k].origine)}</li>`).join('')}</ul>
    <p>${esc(x.note)}</p><p>Joues : ${esc(p.joues||'sans objet')} · L : ${esc(p.largeurRef||'sans objet')} · Tolérance : ${nf(p.tolerance)} mm (${esc(p.origines.tolerance.origine)}).</p>
    <p>Fabrication reprise du formulaire / profil : ${r.plan.forme==='circ'?esc(r.plan.mat||'matériau à vérifier'):esc(cpName(r.plan.cp&&r.plan.cp.j))+' · '+esc(r.plan.mont||'montage à vérifier')}. Options et renforts du modèle existant conservés ; à vérifier.</p>
    <ul>${r.alertes.map(a=>'<li>'+esc(a)+'</li>').join('')}</ul>
    <label><input type="checkbox" id="dxcConfirme" onchange="el('dxcCreer').disabled=!this.checked"> J'ai vérifié les données, leur origine, les contraintes de traversée et les réglages de fabrication ; je confirme la création.</label>
    <button class="btn bs bpr" id="dxcCreer" disabled onclick="dxcCreer()">Confirmer et créer l’ouvrage</button>`;
}
function dxcCreer(){const X=DXC;if(!X||X.D!==DXI||!C('dxcConfirme')||!X.revision)return;
  const x=dxcPreparer();if(!x||!x.r.ok||JSON.stringify(x)!==X.revision){dxcRefresh();return;}
  if(dxcDeja(X.cles)||!String(DXI.ch||'').trim())return dxcRefresh();
  const d=x.r.plan;if(!dxiRefs([d])){toast('Référence déjà utilisée : choisir une autre référence');return;}
  const date=new Date().toISOString().slice(0,10);d.date=date;
  d.origineImport={type:'creation_confirmee',format:'pdf',fichier:DXI.nom,indice:DXI.ind||null,date,creationCles:X.cles,
    cotesPdf:JSON.parse(JSON.stringify(x.p.cotesPdf)),proposition:JSON.parse(JSON.stringify(x.p)),analyse:JSON.parse(JSON.stringify(X.analyse)),confirmation_utilisateur:true,note_utilisateur:x.note,saisiesBrutes:x.saisiesBrutes};
  planUid(d);P.push(d);X.revision=null;svP();profFromPlans([d]);profLists();rnL();updBtn();markDirty();
  dxcRefresh();toast('✓ Ouvrage '+d.ref+' créé après confirmation');
}

// Dossier rattaché à l'identité de la ligne / contour, jamais au seul repère.
function dxcDossier(kind,i,analyse){const D=DXI,L=kind==='n'?D.NL[i].L:null;
  const occurrences=L?(dxnAS(L).occurrences||[]):[],ids=new Set(occurrences.map(o=>o.contour).filter(Boolean));
  const contours=kind==='g'?[D.C[i]]:D.C.filter(c=>ids.has(c.id));
  const dossier=CPI.cotesPreuves.analyser({analyse,repere:L?L.repere:(D.C[i].annot.repere||{}).texte,
    textes:D.doc&&D.NA?dxrTextes():[],vues:Object.values(D.VU||{}).flatMap(v=>v.vues),occurrences,
    homonyme:L&&D.NL.filter(x=>dxcRep(x.L.repere)===dxcRep(L.repere)).length>1,contours,
    zoneTable:L&&L.ids?dxpBox(D.NL[i]):null});
  D.CP=D.CP||{};D.CP[dxcCles(kind,i)[0]]=dossier;return dossier;
}
function dxcCotesHTML(){const X=DXC,labels={L:'Largeur / corde L',h:'Hauteur',D:'Diamètre ouverture',e:'Épaisseur du voile',R:'Rayon intérieur',profondeur:'Longueur de traversée'};
  return `<details open><summary>Cotes retrouvées dans le PDF (${X.dossier.candidats.length})</summary>
    <p>Une proximité ne prouve pas un rôle. Les unités sont lues contre la valeur ; aucune mesure graphique ni échelle de page n'est utilisée ici. Diamètres et rayons extérieurs restent à examiner, sans conversion en rayon intérieur.</p>
    ${X.dossier.candidats.length?'<div style="overflow:auto"><table><thead><tr><th>Brut / unité</th><th>Valeur</th><th>Source / lien</th><th>Statut / rôle proposé</th><th>Affectation explicite</th></tr></thead><tbody>'+X.dossier.candidats.map((c,j)=>`<tr><td>${esc(c.brut)}${c.lecture&&c.lecture!==c.brut?'<br>Lecture : '+esc(c.lecture):''}<br>Unité : ${esc(c.uniteOrigine||c.unite||'inconnue')}</td><td>${nf(c.valeur_mm)} mm</td><td>p. ${esc(c.page||'?')} · ${esc(c.titreVue||c.vue||'vue non identifiée')}<br>${esc(c.raison)}${c.numerique&&c.numerique.raison?'<br>'+esc(c.numerique.raison):''}${c.zone?`<button class="btn bs bo" type="button" onclick="dxcVoirCote(${j})">Voir la source</button>`:''}</td><td>${esc(c.statut)} · ${esc(labels[c.champ]||c.champ)}</td><td><select class="fi" aria-label="Champ de la cote ${j+1}" id="dxcCible_${j}"><option value="">Choisir le rôle</option>${Object.entries(labels).map(([k,v])=>`<option value="${k}"${k===c.champ?' selected':''}>${esc(v)}</option>`).join('')}</select>${c.numerique&&c.numerique.etat!=='valide'?`<label for="dxcValeur_${j}">Valeur confirmée en mm (ex. 1200 ou 1,2)</label><input class="fi" id="dxcValeur_${j}" inputmode="decimal" oninput="dxcRefresh()">`:''}<button class="btn bs bo" type="button" onclick="dxcAffecter(${j})">${c.numerique&&c.numerique.etat!=='valide'?'Confirmer et retenir':'Retenir cette cote'}</button></td></tr>`).join('')+'</tbody></table></div>':'<p>Aucune cote écrite exploitable retrouvée. Compléter les valeurs manuellement après relecture.</p>'}
    ${X.dossier.conflits.map(c=>`<p>Conflit sur ${esc(labels[c.champ])} : ${c.valeurs.map(v=>nf(v)+' mm').join(' / ')}. Retenir une preuve ou saisir la correction puis <button class="btn bs bo" onclick="dxcArbitrer('${c.champ}')">Confirmer la saisie pour ${esc(labels[c.champ])}</button>.</p>`).join('')}
    <div id="dxcCotesChoix" role="status"></div></details>
    <details open><summary>Détails particuliers / limites de fabrication</summary><ul>${X.dossier.details.map(d=>`<li>${esc(d.brut)} · p. ${esc(d.page||'?')} · ${esc(d.raison)} — étude spécifique requise</li>`).join('')}</ul>
    <div id="dxcIndices"><b>Indices non attribués — à examiner</b><p>Ces mentions ne prouvent pas un détail de cette réservation. Relire la source puis signaler explicitement une particularité si elle la concerne.</p><ul>${(X.dossier.indicesNonAttribues||[]).map(d=>`<li>${esc(d.brut)} · p. ${esc(d.page||'?')} · ${esc(d.raison)}</li>`).join('')}</ul></div>
    <label><input type="checkbox" id="dxc_detail" onchange="dxcRefresh()"> Je signale une forme inhabituelle, un chanfrein, une feuillure ou une traversée particulière.</label>
    <input class="fi" id="dxc_detailNote" aria-label="Description du détail particulier" placeholder="Décrire le détail à étudier" oninput="dxcRefresh()">
    <p>Un détail signalé empêche la création standard. Ces formes ne sont pas fabriquées par cette proposition ; conserver le dossier via l'export de l'analyse.</p></details>`;
}
function dxcAffecter(j){if(!DXC)return;const c=DXC.dossier.candidats[j],k=S('dxcCible_'+j,''),r=CPI.cotesPreuves.affecter(DXC.dossier,c.id,k,el('dxcValeur_'+j)?S('dxcValeur_'+j,''):null);
  if(!r){el('dxcCotesChoix').textContent='Affectation impossible : choisir un rôle compatible et une valeur finie positive non ambiguë. Un diamètre / rayon extérieur ne devient pas un rayon intérieur.';return;}
  DXC.retenues[k]=r;DXC.saisie[k]=r.valeur;delete DXC.saisiesBrutes[k];DXC.arbitrages[k]=r.valeur;
  el('dxc_'+k).value=String(r.valeur);dxcRefresh();el('dxcCotesChoix').textContent='Cote retenue pour '+k+' : '+r.valeur+' mm. Origine et preuve conservées.';
}
function dxcArbitrer(k){if(!DXC)return;const p=dxcProposition(),v=p.valeurs[k];if(!(v>0))return;
  DXC.arbitrages[k]=v;dxcRefresh();el('dxcCotesChoix').textContent='Arbitrage explicite de '+k+' : '+v+' mm ; les valeurs contradictoires restent dans les preuves.';
}
function dxcVoirCote(j){if(!DXC)return;const c=DXC.dossier.candidats[j],D=DXI;if(!c.zone)return;
  D.ohl=c.zone;D.page=c.page;D.hl=-1;D.hlo=null;D.scroll=true;dxiVue('p');
}
