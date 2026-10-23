// Phase 11 : préparation locale, mêmes propositions/contrôles que DXC. Aucun moteur de fabrication supplémentaire.
const dxprCopie=x=>JSON.parse(JSON.stringify(x));
const DXPR_ETATS=['À examiner','À compléter','Prêt à confirmer','Validé pour le lot','Créé','Non pris en charge','Ignoré'];
function dxprAcces(){if(DXI?.fmt!=='pdf')return;
  const tabs=document.querySelector('#dxi .dxi-tab');if(tabs&&!el('dxprTab'))tabs.insertAdjacentHTML('beforeend','<button id="dxprTab" role="tab" onclick="dxprOuvrir()">Préparation des réservations</button>');
}
function dxprBase(){const D=DXI;if(!D||D.fmt!=='pdf')return null;if(!D.M)dxiModels();return D.PR||(D.PR={rows:{},ordre:[],selection:[],filtres:{},revision:null,message:''})}
function dxprLecture(X){return{case:id=>X.controles?.[id]?.checked===true,val:(id,def='')=>X.controles?.[id]?.value??(id==='dxc_ref'?X.ref:id==='dxc_nb'?String(X.nombre||1):def)}}
function dxprCalcul(X){try{return dxcPreparer(X,dxprLecture(X))}catch(e){return{p:{valeurs:{},manquants:[e.message]},r:{ok:false,messages:['Proposition à réexaminer : '+e.message]},note:''}}}
function dxprEmpreinte(X,x){return JSON.stringify({cles:X.cles,controles:X.controles||{},modeles:X.modeles,contexte:[X.D.ch,X.D.ouv,X.D.ind],x})}
function dxprInvalider(X,m){if(X.validation){X.invalidation=m;X.validation=null;}const B=X.D.PR;if(B){B.selection=B.selection.filter(k=>k!==X.cles[0]);B.revision=null;}}
function dxprSauver(){const X=DXC;if(!X||X.D!==DXI||!el('dxcZ'))return;
  X.controles=Object.fromEntries([...el('dxcZ').querySelectorAll('input[id^="dxc_"],select[id^="dxc_"]')].map(e=>[e.id,{value:e.value,checked:e.type==='checkbox'&&e.checked}]));
  const B=dxprBase();B.rows[X.cles[0]]=X;
  if(X.validation&&X.validation!==dxprEmpreinte(X,dxprCalcul(X)))dxprInvalider(X,'Données ou réglages modifiés depuis la validation');
}
function dxprInventaire(){const D=DXI,B=dxprBase();if(!B)return[];const lignes=D.NL.map((_,i)=>['n',i]),rattaches=new Set();
  dxnContoursLignes().liens.forEach(ids=>ids.forEach(id=>rattaches.add(id)));
  D.C.forEach((c,i)=>{if(!rattaches.has(c.id)&&c.statut==='a_confirmer')lignes.push(['g',i])});
  B.ordre=lignes.map(([kind,i])=>{const neuf=dxcNouveau(kind,i),key=neuf.cles[0],ex=B.rows[key];
    const source=JSON.stringify({analyse:neuf.analyse,dossier:neuf.dossier,cles:neuf.cles});
    if(ex){if(ex.source!==source)dxprInvalider(ex,'Analyse ou preuves sources modifiées');Object.assign(ex,{D,kind,i,analyse:neuf.analyse,dossier:neuf.dossier,cles:neuf.cles,source});}
    else{neuf.source=source;B.rows[key]=neuf;}return key;
  });return B.ordre.map(k=>B.rows[k]);
}
function dxprCharger(kind,i){const B=dxprBase(),key=dxcCles(kind,i)[0];if(!B.ordre.length)dxprInventaire();if(!B.rows[key]){const X=dxcNouveau(kind,i);X.source=JSON.stringify({analyse:X.analyse,dossier:X.dossier,cles:X.cles});B.rows[key]=X;}return B.rows[key]}
function dxprRestaurer(){const X=DXC;if(!X?.controles)return;for(const [id,v] of Object.entries(X.controles)){const e=el(id);if(e){e.value=v.value;if(e.type==='checkbox')e.checked=v.checked}}}
function dxprEtat(X,x=dxprCalcul(X)){
  if(dxcDeja(X.cles))return'Créé';if(X.ignore)return'Ignoré';
  if(X.validation){if(X.validation===dxprEmpreinte(X,x)&&x.r.ok)return'Validé pour le lot';dxprInvalider(X,'La proposition doit être relue et confirmée');}
  const p=x.p,s=X.saisie;
  if(s.detail==='autre'||s.detail==='chanfrein45'&&s.orientationChanfrein==='vers_vide'||(X.kind==='g'&&X.D.C[X.i].statut!=='a_confirmer'))return'Non pris en charge';
  if((x.r.messages||[]).some(m=>/non pris en charge|non prise en charge|interférence|format CP insuffisant/.test(m)))return'Non pris en charge';
  if(X.dossier.conflits.some(c=>X.arbitrages[c.champ]==null)||X.kind==='g'&&!X.controles?.dxc_traversee?.checked)return'À examiner';
  if(!x.r.ok||!String(X.D.ch||'').trim())return'À compléter';return'Prêt à confirmer';
}
function dxprControleHistorique(LN,L){return LN.map(i=>['n',i]).concat(L.map(i=>['g',i])).flatMap(([k,i])=>{const X=dxcNouveau(k,i),p={detail:'aucun',valeurs:{},manquants:[]};dxcControlePreuves(X,p,{case:()=>false,val:()=>''});return p.manquants.map(m=>(X.ref||X.cles[0])+' : '+m)})}
function dxprOuvrir(){if(DXI?.fmt!=='pdf'||DXI.rJob)return;dxcFermer();const B=dxprBase();dxprInventaire();dxiVue('prep');
  if(!el('dxprZ'))el('dxiZ').insertAdjacentHTML('beforeend','<section id="dxprZ" class="dxo" aria-label="Préparation des réservations"></section>');
  el('dxprZ').hidden=false;dxprTable();dxiBtn();el('dxprZ').scrollIntoView({block:'start'});
}
function dxprTable(){const B=dxprBase(),z=el('dxprZ');if(!B||!z)return;const rows=B.ordre.map(k=>B.rows[k]),calc=rows.map(X=>({X,x:dxprCalcul(X)}));calc.forEach(a=>a.etat=dxprEtat(a.X,a.x));
  const count=e=>calc.filter(a=>a.etat===e).length,F=B.filtres;
  const opts=(id,lib,values)=>`<label>${lib}<select class="fi" id="${id}" onchange="dxprFiltre('${id}',this.value)"><option value="">Tous</option>${values.map(v=>`<option${F[id]===v?' selected':''}>${esc(v)}</option>`).join('')}</select></label>`;
  const page=X=>String(X.kind==='n'?DXI.NL[X.i].N.page||'?':DXI.C[X.i].source.page||'?'),vue=X=>X.kind==='n'?DXI.NL[X.i].N.id:DXI.C[X.i].vue||'dessin';
  z.innerHTML=`<div class="ct">Préparation des réservations</div><p>Brouillon local : aucune création avant validation individuelle, sélection et confirmation du lot. Exportez la préparation avant de fermer le fichier.</p>
    <p id="dxprBilan" role="status">Total détecté : ${rows.length} · à examiner : ${count('À examiner')} · incomplet : ${count('À compléter')} · prêt : ${count('Prêt à confirmer')} · validé : ${count('Validé pour le lot')} · créé : ${count('Créé')} · ignoré : ${count('Ignoré')} · non pris en charge : ${count('Non pris en charge')}</p>
    <details><summary>Réglages communs de fabrication</summary><p>Chantier et ouvrage : champs en haut de la fenêtre. Les modèles sont repris du formulaire et des profils existants ; aucune cote de réservation n’est propagée. Pour utiliser un modèle personnel, le choisir dans le formulaire avant l’import.</p><button class="btn bs bo" onclick="dxprModeles()">Actualiser les réglages communs depuis le formulaire / profil</button><p>Les brouillons existants gardent leurs réglages jusqu’à une reprise explicite dans leur fiche.</p></details>
    <div class="dxp-b">${opts('dxprStat','Statut',DXPR_ETATS)}${opts('dxprPage','Page',[...new Set(rows.map(page))])}${opts('dxprVue','Tableau / vue',[...new Set(rows.map(vue))])}${opts('dxprType','Forme',['rect','carre','circ'])}${opts('dxprRest','Création',['Restantes','Déjà créées'])}<label>Référence<input class="fi" id="dxprRef" type="search" value="${esc(F.dxprRef||'')}" oninput="dxprFiltre('dxprRef',this.value)"></label></div>
    <div class="dxi-t"><table class="ser" id="dxprT"><thead><tr><th>Lot</th><th>Référence / source</th><th>Forme / cotes connues</th><th>À compléter / support</th><th>Détail / statut</th><th>Actions</th></tr></thead><tbody>${calc.filter(({X,x,etat})=>(!F.dxprStat||etat===F.dxprStat)&&(!F.dxprPage||page(X)===F.dxprPage)&&(!F.dxprVue||vue(X)===F.dxprVue)&&(!F.dxprType||x.p.type===F.dxprType)&&(!F.dxprRest||(etat==='Créé')===(F.dxprRest==='Déjà créées'))&&(!F.dxprRef||(dxprLecture(X).val('dxc_ref')||X.ref||X.cles[0]).toLowerCase().includes(F.dxprRef.toLowerCase()))).map(({X,x,etat})=>{const i=B.ordre.indexOf(X.cles[0]);return `<tr data-prep="${i}"><td><input type="checkbox" aria-label="Inclure ${esc(X.ref||'ligne '+(i+1))}" ${B.selection.includes(X.cles[0])?'checked':''} ${etat==='Validé pour le lot'?'':'disabled'} onchange="dxprSelection(${i},this.checked)"></td><td><b>${esc(dxprLecture(X).val('dxc_ref')||X.ref||'Ligne '+(i+1))}</b><br>p. ${esc(page(X))} · ${esc(vue(X))}<br><small>${esc(X.kind==='n'?DXI.NL[X.i].L.id:DXI.C[X.i].id)}</small></td><td>${esc(x.p.type||'inconnue')}<br>${Object.entries(x.p.valeurs).filter(([,v])=>v!=null).map(([k,v])=>esc(k)+' : '+nf(v)+' mm').join('<br>')||'Cotes inconnues'}</td><td>${esc((x.r.messages||[]).join(' ; '))}<br>Support : ${esc(x.p.support||'inconnu')}</td><td>${esc((X.dossier.details||[]).map(d=>d.brut).join(' ; ')||x.p.detail||'aucun')}<br><b>${esc(etat)}</b>${X.invalidation?'<br>'+esc(X.invalidation):''}</td><td><button class="btn bs bo" onclick="dxprFicheOuvrir(${i})">${etat==='Créé'?'Consulter les preuves':'Préparer / modifier — preuves'}</button><button class="btn bs bo" onclick="dxprVoir(${i})">Voir PDF</button><button class="btn bs bo" onclick="dxprIgnorer(${i})" ${etat==='Créé'?'disabled':''}>${X.ignore?'Rétablir':'Ignorer'}</button></td></tr>`}).join('')}</tbody></table></div>
    <div class="dxp-b"><button class="btn bs bpr" id="dxprLot" onclick="dxprRecap()">Créer les ouvrages validés (${B.selection.length})</button><button class="btn bs bo" onclick="dxprExporter()">Exporter la préparation</button><label class="btn bs bo">Reprendre une préparation<input id="dxprFichier" type="file" accept=".json" hidden onchange="dxprLire(this.files[0]);this.value=''"></label>${B.annulation?'<button class="btn bs bo" onclick="dxprAnnuler()">Annuler le dernier lot créé</button>':''}</div><p id="dxprMessage" role="status">${esc(B.message||'Aucune sélection automatique.')}</p><div id="dxprResume"></div>`;
}
function dxprFiltre(k,v){const B=dxprBase();B.filtres[k]=v;dxprTable();if(k==='dxprRef'){const e=el(k);e.focus();e.setSelectionRange(v.length,v.length)}}
function dxprSelection(i,on){const B=dxprBase(),key=B.ordre[i];B.selection=B.selection.filter(k=>k!==key);if(on&&dxprEtat(B.rows[key])==='Validé pour le lot')B.selection.push(key);B.revision=null;dxprTable()}
function dxprIgnorer(i){const B=dxprBase(),X=B.rows[B.ordre[i]];X.ignore=!X.ignore;dxprInvalider(X,'Réservation écartée du lot');dxprTable()}
function dxprVoir(i){const B=dxprBase(),X=B.rows[B.ordre[i]];if(X.kind==='n')dxpVoir(X.i);else{DXI.page=DXI.C[X.i].source.page;dxrSel(X.i);dxiVue('p')}}
function dxprFicheOuvrir(i){dxprSauver();const B=dxprBase(),X=B.rows[B.ordre[i]];if(X)dxcOuvrir(X.kind,X.i)}
function dxprSuivante(pas){dxprSauver();const B=dxprBase(),i=B.ordre.indexOf(DXC?.cles[0]),n=B.ordre.length;if(!n)return;
  if(pas==='incomplet'){for(let k=1;k<=n;k++){const j=(i+k+n)%n;if(['À examiner','À compléter'].includes(dxprEtat(B.rows[B.ordre[j]])))return dxprFicheOuvrir(j)}return toast('Aucune réservation à compléter');}
  dxprFicheOuvrir(Math.min(n-1,Math.max(0,i+pas)));
}
function dxprFiche(){const X=DXC,B=dxprBase();if(!X||!B)return;if(!B.ordre.includes(X.cles[0]))B.ordre.push(X.cles[0]);
  el('dxcZ').insertAdjacentHTML('afterbegin','<nav class="dxp-b" aria-label="Navigation des réservations"><button class="btn bs bo" onclick="dxprSuivante(-1)">Précédente</button><button class="btn bs bo" onclick="dxprSuivante(1)">Suivante</button><button class="btn bs bo" onclick="dxprSuivante(\'incomplet\')">Prochaine à compléter</button><button class="btn bs bo" onclick="dxprOuvrir()">Retour au tableau</button></nav>');
  el('dxcZ').insertAdjacentHTML('beforeend','<button class="btn bs bpr" id="dxprValider" onclick="dxprValider()">Valider cette proposition pour le lot</button><div id="dxprValidation" role="status"></div><details><summary>CP et montage de cette proposition</summary><div id="dxprReglages"></div><button class="btn bs bo" onclick="dxprReprendreModeles()">Reprendre explicitement les réglages communs</button></details>');dxprReglages();
}
function dxprReglages(){const X=DXC;if(!X||!el('dxprReglages'))return;const f=X.saisie.solution==='fourreau'?'circ':X.saisie.solution==='cintre'?'voile':'para',m=X.modeles[f];
  el('dxprReglages').innerHTML='<p>Repris du formulaire / profil, conservés dans ce brouillon. Les cotes géométriques ne sont pas copiées.</p>'+(f==='circ'?'<p>Matériau du fourreau : '+esc(m.mat||'à vérifier')+'</p>':`<label>Type CP<select class="fi" id="dxprCPtype" onchange="dxprCP('t',this.value)">${Object.entries(CPT).map(([k,c])=>`<option value="${esc(k)}"${m.cp.j.t===k?' selected':''}>${esc(c.n||k)}</option>`).join('')}</select></label><label>Épaisseur CP (mm)<input class="fi" id="dxprCPep" inputmode="decimal" value="${esc(m.cp.j.e)}" onchange="dxprCP('e',parseCote(this.value,'mm'))"></label><label>Format CP<input class="fi" id="dxprCPformat" value="${esc(m.cp.j.f)}" onchange="dxprCP('f',this.value)"></label>`)+`<label>Montage<select class="fi" id="dxprMont" onchange="dxprCP('mont',this.value)">${[...el('iMont').options].map(o=>o.value).map(v=>`<option${m.mont===v?' selected':''}>${v}</option>`).join('')}</select></label>`;
}
function dxprCP(k,v){const X=DXC;if(k==='e'&&X.saisie.detail==='chanfrein45')dxprEpChanfrein(v);for(const m of Object.values(X.modeles)){if(k==='mont')m.mont=v;else if(m.cp?.j)m.cp.j[k]=v;}dxprInvalider(X,'Réglages de fabrication modifiés');dxcRefresh()}
function dxprModeles(){dxiModels();dxprBase().message='Réglages communs actualisés. Reprise explicite dans chaque fiche existante.';dxprTable()}
function dxprEpChanfrein(v){DXC.saisie.epChanfrein=v;DXC.saisiesBrutes.epChanfrein=String(v??'');if(el('dxc_epChanfrein'))el('dxc_epChanfrein').value=v??''}
function dxprReprendreModeles(){DXC.modeles=dxprCopie(DXI.M);if(DXC.saisie.detail==='chanfrein45')dxprEpChanfrein(DXC.modeles.para.cp.j.e);dxprInvalider(DXC,'Réglages communs repris explicitement');dxcRefresh();dxprReglages()}
function dxprValider(){dxprSauver();const X=DXC,x=dxprCalcul(X),B=dxprBase();if(!x.r.ok||!String(DXI.ch||'').trim()||dxcDeja(X.cles)||X.ignore){el('dxprValidation').textContent='Non validé : '+(x.r.messages||[]).join(' ; ');return;}
  // Confirmation via le récapitulatif individuel existant, sans ajout à P.
  dxcRecap();const z=el('dxcResume');z.querySelector('#dxcCreer')?.remove();const c=z.querySelector('#dxcConfirme');if(c){c.removeAttribute('onchange');c.parentElement.lastChild.textContent=' J’ai relu cette proposition, ses preuves et les réglages ; je la valide pour le lot, sans créer d’ouvrage.';}
  z.insertAdjacentHTML('beforeend','<button class="btn bs bpr" id="dxprConfirmer" onclick="dxprConfirmer()">Confirmer la validation pour le lot</button>');
}
function dxprConfirmer(){if(!C('dxcConfirme')||!DXC?.revision)return;const x=dxcPreparer();if(!x.r.ok||JSON.stringify(x)!==DXC.revision)return dxcRefresh();
  dxprSauver();DXC.validation=dxprEmpreinte(DXC,x);DXC.invalidation=null;dxprBase().revision=null;el('dxprValidation').innerHTML='Validé pour le lot — aucun ouvrage créé, sélectionner la ligne dans le tableau. <button class="btn bs bo" onclick="dxprSuivante(1)">Suivante</button><button class="btn bs bo" onclick="dxprOuvrir()">Retour au tableau</button>';el('dxprConfirmer').disabled=true;
}
function dxprLot(){const B=dxprBase(),cles=B.selection.slice(),errors=[],seen=new Set(),plans=[],xs=[];dxprInventaire();
  if(!cles.length)errors.push('Sélectionner explicitement des propositions validées');
  for(const key of cles){const X=B.rows[key];if(!X||!B.ordre.includes(key)){errors.push('Source disparue : '+key);continue;}const x=dxprCalcul(X);
    if(!x.r.ok||!X.validation||X.validation!==dxprEmpreinte(X,x)||X.ignore||dxcDeja(X.cles)){errors.push((dxprLecture(X).val('dxc_ref')||X.ref||key)+' : validation absente, périmée, réservation déjà créée ou '+(x.r.messages||[]).join(' ; '));continue;}
    if(X.cles.some(k=>seen.has(k))){errors.push(X.ref+' : identité source sélectionnée deux fois');continue;}X.cles.forEach(k=>seen.add(k));
    plans.push(dxcOrigine(X,x));xs.push({X,x});
  }
  if(plans.length&&!dxiRefs(plans))errors.push('Références en collision dans le projet ou entre les ouvrages du lot');
  return{plans,xs,errors,empreinte:JSON.stringify({cles,etats:xs.map(({X,x})=>dxprEmpreinte(X,x)),plans})};
}
function dxprRecap(){dxprSauver();const B=dxprBase(),r=dxprLot(),z=el('dxprResume');B.revision=null;
  if(r.errors.length){B.message=r.errors.join(' ; ');z.innerHTML='<p role="alert">Aucun ouvrage créé : '+esc(B.message)+'</p>';return;}
  B.revision=r.empreinte;z.innerHTML=`<h3>Lot sélectionné : ${r.plans.length} réservation(s), aucun ouvrage encore créé</h3><ul>${r.xs.map(({X,x},i)=>`<li><b>${esc(r.plans[i].ref)}</b> · ${esc(fmLb(x.r.plan.forme))} · ${x.r.plan.nb} exemplaire(s) · ${esc(x.p.detail)} · ${Object.entries(x.p.valeurs).filter(([,v])=>v!=null).map(([k,v])=>esc(k)+' '+nf(v)+' mm').join(' · ')} · ${esc(x.r.plan.forme==='circ'?x.r.plan.mat:cpName(x.r.plan.cp.j))} · montage ${esc(x.r.plan.mont)}<ul>${x.r.alertes.map(a=>'<li>'+esc(a)+'</li>').join('')}</ul></li>`).join('')}</ul><p>Les réservations bloquées et non sélectionnées restent dans le brouillon. Création tout ou rien.</p><label><input type="checkbox" id="dxprConfirmeLot"> Je confirme la création de ces seuls ouvrages relus.</label><button class="btn bs bpr" id="dxprCreer" onclick="dxprCreer()">Confirmer et créer le lot</button>`;
}
function dxprCreer(){const B=dxprBase();if(!C('dxprConfirmeLot')||!B.revision||B.creation)return;const r=dxprLot();
  if(r.errors.length||r.empreinte!==B.revision){B.revision=null;B.message='Aucun ouvrage créé : '+(r.errors.join(' ; ')||'lot modifié depuis le récapitulatif');el('dxprResume').textContent=B.message;return;}
  B.creation=true;try{const plans=r.plans.map(d=>{planUid(d);return d});P=P.concat(plans);profFromPlans(plans);svP();profLists();rnL();updBtn();markDirty();
    B.annulation=plans.map(p=>({uid:p.uid,etat:JSON.stringify(p)}));B.selection=[];B.revision=null;B.message=plans.length+' ouvrage(s) effectivement créé(s).';dxprTable();toast(B.message);
  }finally{B.creation=false;}
}
function dxprAnnuler(){const B=dxprBase(),a=B.annulation;if(!a)return;
  if(a.some(q=>{const p=P.find(p=>p.uid===q.uid);return!p||JSON.stringify(p)!==q.etat})){B.message='Annulation refusée : un ouvrage du lot a été modifié ou retiré.';return dxprTable();}
  const u=EI>=0&&P[EI]?.uid,ids=new Set(a.map(q=>q.uid));P=P.filter(p=>!ids.has(p.uid));EI=u?P.findIndex(p=>p.uid===u):-1;svP();rnL();updBtn();markDirty();B.annulation=null;B.message=a.length+' ouvrage(s) du lot retiré(s), autres plans conservés.';dxprTable();
}
function dxprPreparation(){dxprSauver();dxprInventaire();const D=DXI,B=dxprBase(),source={};
  for(const k of ['NA','NR','C','R','NU','AS','HR','cal','GP','GI','OT','OM','VU','CS','SP','ana','no','nz','ns','rn'])if(D[k]!=null)source[k]=dxprCopie(D[k]);
  return{format:'coffraplan-preparation-pdf',v:1,pdf:{nom:D.nom,empreinte:D.empreinte},contexte:{ch:D.ch,ouv:D.ouv,ind:D.ind},source,modeles:dxprCopie(D.M),
    lignes:B.ordre.map(k=>{const X=B.rows[k];return{cle:k,cles:X.cles,kind:X.kind,i:X.i,retenues:X.retenues,arbitrages:X.arbitrages,saisie:X.saisie,saisiesBrutes:X.saisiesBrutes,controles:X.controles||{},modeles:X.modeles,validation:X.validation||null,invalidation:X.invalidation||null,ignore:!!X.ignore,preuves:X.dossier}})};
}
function dxprExporter(){const j=dxprPreparation();dlBlob(new Blob([JSON.stringify(j,null,2)],{type:'application/json'}),'coffraplan-preparation.json')}
async function dxprLire(f){if(!f)return;try{dxprReprendre(JSON.parse(await f.text()))}catch(e){dxprBase().message='Préparation refusée : '+e.message;dxprTable()}}
function dxprReprendre(j){const D=DXI;if(!D||D.fmt!=='pdf')throw Error('Ouvrir d’abord le PDF original');
  if(j.format!=='coffraplan-preparation-pdf'||j.v!==1)throw Error('Format non compatible ou ancienne analyse sans empreinte vérifiable ; reprendre les preuves avec le PDF et exporter une préparation');
  if(!/^[a-f0-9]{64}$/.test(j.pdf?.empreinte||'')||j.pdf.empreinte!==D.empreinte)throw Error('Empreinte différente : ce brouillon ne correspond pas au PDF ouvert');
  if(!Array.isArray(j.lignes)||!Array.isArray(j.source?.NA?.nomenclatures)||!Array.isArray(j.source.C)||!Array.isArray(j.source.NR)||!j.modeles?.para||!j.modeles?.circ||!j.modeles?.voile)throw Error('Structure de préparation incomplète');
  const ns=j.source.NA.nomenclatures;if(ns.some(n=>!Array.isArray(n.lignes)||!Number.isInteger(n.page)||n.page<1||n.page>D.doc.pages.length))throw Error('Page source absente du PDF');
  if(!Array.isArray(j.source.R)||j.source.R.length!==j.source.C.length||j.source.C.some(c=>!c.source||c.source.page<1||c.source.page>D.doc.pages.length||!Array.isArray(c.bbox)||c.bbox.length!==4||!c.bbox.every(Number.isFinite)))throw Error('Contours sources incohérents');
  const avant={...D};try{dxcFermer();for(const k of ['NA','NR','C','R','NU','AS','HR','cal','GP','GI','OT','OM','VU','CS','SP','ana','no','nz','ns','rn']){if(j.source[k]!=null)D[k]=dxprCopie(j.source[k]);else delete D[k];}
    D.NL=D.NA.nomenclatures.flatMap(N=>N.lignes.map(L=>({N,L})));if(D.NR.length!==D.NL.length)throw Error('Lignes sources incohérentes');
    for(const k of ['ch','ouv','ind'])D[k]=String(j.contexte?.[k]||'');D.M=dxprCopie(j.modeles);D.PR=null;D.lk=new Set();dxnLinks();const rows=dxprInventaire(),B=dxprBase(),seen=new Set();
    for(const saved of j.lignes){if(seen.has(saved.cle))throw Error('Identité de brouillon répétée');seen.add(saved.cle);const X=rows.find(x=>x.cles[0]===saved.cle);if(!X)throw Error('Identité source introuvable');
      for(const k of ['retenues','arbitrages','saisie','saisiesBrutes','controles','modeles','validation','invalidation','ignore'])if(saved[k]!=null)X[k]=dxprCopie(saved[k]);
      if(X.validation&&(X.validation!==dxprEmpreinte(X,dxprCalcul(X))||dxcDeja(X.cles)))dxprInvalider(X,'Validation recalculée à la reprise : nouvelle relecture nécessaire');
    }B.message='Préparation reprise pour le même PDF ; validations recalculées, aucune sélection et aucun ouvrage ajouté.';dxiRender();dxprOuvrir();return true;
  }catch(e){Object.assign(D,avant);throw e;}
}

// Dossier ciblé : sélection de plans enregistrés, moteurs consolidés existants.
let DOSC=null;
function doscPlans(){return P.filter(p=>chKey(p.ch)===chKey(DOSC.ch))}
function doscCle(p){if(p.uid)return p.uid;if(!DOSC.sansUid.has(p))DOSC.sansUid.set(p,'local:'+DOSC.sansUid.size);return DOSC.sansUid.get(p)}
function doscChoisis(){return doscPlans().filter(p=>DOSC.selection.includes(doscCle(p)))}
function doscOuvrir(){DOSC={ch:S('iCh',''),selection:[],q:'',sansUid:new Map()};modal('<div id="doscZ"></div>',true);doscTable()}
function doscTable(){const L=doscPlans(),sel=doscChoisis(),C0=chantierData(sel),groups=[...new Set(L.map(p=>p.ouv||''))];
  el('doscZ').innerHTML=`<div class="ct">Préparer un dossier de fabrication</div><p>Chantier : ${esc(DOSC.ch||'non renseigné')} · sélectionner les plans enregistrés. Un plan reste une ligne, sa quantité est conservée.</p><label>Rechercher une référence<input class="fi" id="doscQ" type="search" value="${esc(DOSC.q)}" oninput="DOSC.q=this.value;doscTable();el('doscQ').focus()"></label><div class="dxp-b"><button class="btn bs bo" onclick="doscTout(true)">Tout sélectionner</button><button class="btn bs bo" onclick="doscTout(false)">Tout désélectionner</button></div>${groups.map(g=>`<fieldset><legend>${esc(g||'Sans ouvrage')} <button class="btn bs bo" data-ouv="${esc(g)}" onclick="doscOuvrage(this.dataset.ouv)">Sélectionner cet ouvrage</button></legend>${L.filter(p=>(p.ouv||'')===g&&(!DOSC.q||String(p.ref||'').toLowerCase().includes(DOSC.q.toLowerCase()))).map(p=>`<label style="display:block"><input type="checkbox" data-plan-uid="${esc(doscCle(p))}" ${DOSC.selection.includes(doscCle(p))?'checked':''} onchange="doscSelection(this.dataset.planUid,this.checked)"> ${esc(p.ref||'Sans référence')} · ${esc(fmLb(p.forme))} · × ${p.nb||1}</label>`).join('')}</fieldset>`).join('')}
    <div id="doscBilan" role="status"><b>${sel.length} plan(s) · ${sel.reduce((s,p)=>s+(p.nb||1),0)} exemplaire(s)</b><p>Ouvrages : ${esc([...new Set(sel.map(p=>p.ouv||'—'))].join(' · '))}</p><p>CP : ${Object.values(C0.cp).some(c=>c.est||c.extraM2>0)?'≈ ':''}${Object.values(C0.cp).reduce((s,c)=>s+c.nP,0)} panneau(x), ${nf(Object.values(C0.cp).reduce((s,c)=>s+c.m2,0),3)} m² · Bois : ${nf(Object.values(C0.bois).reduce((s,c)=>s+c.ml,0),3)} ml</p><ul>${C0.warn.concat(chantierCpErreurs(C0),sel.flatMap(p=>{const d=canon(migr(p));return checks(d,d.forme==='voile'?voileGeo(d):null).map(w=>(p.ref||'Plan')+' : '+w[1])})).map(m=>'<li>'+esc(m)+'</li>').join('')}</ul><p>Retenus : ${esc(sel.map(p=>(p.ref||'—')+' × '+(p.nb||1)).join(' ; '))}</p></div><button class="btn bs bpr" id="doscApercu" ${sel.length?'':'disabled'} onclick="doscGenerer()">Voir le dossier — Imprimer / Enregistrer au format PDF</button><button class="btn bs bo" onclick="closeModal()">Annuler</button><p id="doscErreur" role="alert"></p>`;
}
function doscSelection(key,on){DOSC.selection=DOSC.selection.filter(k=>k!==key);if(on)DOSC.selection.push(key);doscTable()}
function doscTout(on){DOSC.selection=on?doscPlans().map(doscCle):[];doscTable()}
function doscOuvrage(g){DOSC.selection=[...new Set(DOSC.selection.concat(doscPlans().filter(p=>(p.ouv||'')===g).map(doscCle)))];doscTable()}
function doscHtml(list){const C0=chantierData(list),erreurs=C0.warn.concat(chantierCpErreurs(C0));if(erreurs.length)throw Error(erreurs.join(' ; '));const avant={...PRT};try{PRT.cp=true;PRT.mt=true;return dossierHtml(list,true)}finally{Object.assign(PRT,avant)}}
function doscGenerer(){const L=doscChoisis();if(!L.length)return;const C0=chantierData(L),cpErreurs=C0.warn.concat(chantierCpErreurs(C0));if(cpErreurs.length){el('doscErreur').textContent='Dossier bloqué : '+cpErreurs.join(' ; ');return;}
  const erreurs=L.flatMap(p=>{const d=canon(migr(p));return limErr(d).map(e=>p.ref+' : '+e.msg).concat(checks(d,d.forme==='voile'?voileGeo(d):null).filter(w=>w[0]!=='warn').map(w=>p.ref+' : '+w[1]))});if(erreurs.length){el('doscErreur').textContent=erreurs.join(' ; ');return;}const r=dxprCopie(L);try{openDossier(r);closeModal()}catch(e){el('doscErreur').textContent='Dossier bloqué : génération incomplète — '+e.message+' ; répartir les ouvrages en plusieurs dossiers';}
}
function doscRetour(){const r=DOS?.retour;if(r){_loading=true;try{setForm(JSON.parse(r.form))}finally{_loading=false}EI=r.ei;}VIEW='plan';prev()}
