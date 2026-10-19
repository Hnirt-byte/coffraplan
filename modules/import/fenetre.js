// CoffraPlan — module d'import de plans, composant D : fenêtre « Importer un plan » (DXF ou PDF, dans l'appli).
// Seul composant lié à l'appli : il appelle ses fonctions (modal, coll, setForm, P, svP, nextRef, toast…) au moment de
// l'action, jamais au chargement. Chaîne : fichier → A (lecteur + dxf.js) → B (détecteur) → choix de l'utilisateur ligne
// par ligne → C (adaptateur : contrôles du moteur) → ajout à P comme serCreate. Rien n'est créé avant « Créer les ouvrages
// sélectionnés ». Provenance gardée dans le plan : clé optionnelle origineImport (métadonnée, jamais lue par le moteur).
// Nomenclatures de réservations (nomenclatures.js, fonctions dxn*) : vue par défaut quand le DXF en contient ; toutes les
// lignes proposées, aucune cochée d'office ; les géométries rattachées sont retirées de la vue « Géométries du dessin ».
// PDF (pdf.js, fonctions dxp*) : mêmes nomenclatures et même création ; vue « Aperçu du plan » (pages, zoom, zone à analyser,
// saisie assistée des lignes quand le tableau n'est pas lisible). Aucune géométrie de la page n'est convertie en cote.
// OCR (ocr.js, fonctions dxo*) : zone reconnue visuellement, grille de vérification modifiable (cellules incertaines signalées,
// lignes ajoutées, fusionnées ou retirées), puis lignes ajoutées à la même nomenclature (même création, aucune cochée d'office).
let DXI=null;
const DXI_MM={mm:1,cm:10,m:1000};
const DXI_NP=300;   // shortcut: au-delà, les géométries non prises en charge sont comptées mais pas listées une à une (fichiers à milliers de LINE / TEXT)
const dxiNum=v=>nf(Math.round(v*10)/10,1).replace(/,0$/,'');
function dxiCss(){if(el('dxiCss'))return;document.head.insertAdjacentHTML('beforeend',`<style id="dxiCss">
#mdBody:has(#dxi){width:min(1320px,100%)}
#dxi .dxi-g{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;align-items:end;margin-top:10px}#dxi .fd{margin:0}
#dxi .dxi-u{margin:10px 0 0;padding:8px 10px;border:1px solid var(--accent);border-radius:6px;font-size:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#dxi .dxi-u select{width:auto}
#dxi .dxi-l{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;margin:10px 0 4px;align-items:center}#dxi .dxi-l b{color:var(--muted);font-weight:600}
#dxi .dxi-s{font-size:12px;margin:4px 0}
#dxi .dxi-w{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);gap:10px;margin-top:6px}
#dxiV{width:100%;height:380px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;display:block}
#dxiV .c{fill:rgba(136,146,168,.16);stroke:var(--muted);stroke-width:1.5px;vector-effect:non-scaling-stroke;cursor:pointer}
#dxiV .c.cf{stroke:var(--okt);fill:rgba(46,204,113,.2)}#dxiV .c.on{stroke:var(--accent);stroke-width:3px;fill:rgba(232,130,12,.35)}
#dxiV .np{fill:none;stroke:var(--muted);stroke-width:1px;stroke-dasharray:4 3;vector-effect:non-scaling-stroke;opacity:.6}
#dxiV text{fill:var(--text);pointer-events:none;font-family:'Barlow',sans-serif}
#dxi .dxi-t{max-height:420px;overflow:auto;border:1px solid var(--border);border-radius:6px}#dxi .dxi-t .ser{margin:0}
#dxiT th{position:sticky;top:0;background:var(--surface)}#dxiT tr{cursor:pointer}#dxiT tr.on td{background:rgba(232,130,12,.16)}
#dxiT .fi{padding:3px 5px;font-size:12px;min-width:0}#dxiT .np td{color:var(--muted)}
#dxi details{margin-top:8px;font-size:12px}#dxi summary{cursor:pointer;color:var(--muted)}
#dxi .dxi-tab{display:flex;gap:4px;margin-top:10px;border-bottom:1px solid var(--border)}
#dxi .dxi-tab button{background:none;border:1px solid transparent;border-bottom:none;border-radius:6px 6px 0 0;padding:6px 12px;color:var(--muted);cursor:pointer;font:inherit;font-size:12px}
#dxi .dxi-tab button.on{border-color:var(--border);background:var(--surface2);color:var(--text);font-weight:600}
#dxi .dxn-i{font-size:12px;margin:6px 0;padding:6px 8px;border:1px solid var(--border);border-radius:6px;line-height:1.5}#dxi .dxn-i select{width:auto}
#dxnT td{white-space:pre-line}#dxnT .fi{padding:3px 5px;font-size:12px;min-width:0}#dxnT select[data-k=forme]{min-width:110px}#dxnT tr{cursor:pointer}#dxnT tr.on td{background:rgba(232,130,12,.16)}
#dxnT .mu,#dxi .mu{color:var(--muted);font-size:11px}#dxnT .av{color:var(--acct);font-size:11px}#dxnT .gs{font-size:11px;margin-top:2px}
#dxnT th{position:sticky;top:0;background:var(--surface);z-index:1}
#dxnV{width:100%;height:260px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;display:block;margin-top:8px}
#dxnV .g{fill:rgba(136,146,168,.16);stroke:var(--muted);stroke-width:1.5px;vector-effect:non-scaling-stroke}#dxnV .g.on{stroke:var(--accent);stroke-width:3px;cursor:pointer}
#dxnV .g.cf{stroke:var(--okt);fill:rgba(46,204,113,.3)}#dxnV .rp{fill:var(--acct)}#dxnV .rp.on{fill:var(--redt)}#dxnV text{fill:var(--text);pointer-events:none;font-family:'Barlow',sans-serif}
#dxi.drop{outline:2px dashed var(--accent);outline-offset:4px}
#dxi .dxp{display:grid;grid-template-columns:minmax(0,3fr) minmax(250px,1fr);gap:10px;margin-top:8px}
#dxpW{height:min(64vh,640px);overflow:auto;background:var(--surface2);border:1px solid var(--border);border-radius:6px}
#dxpC{position:relative;margin:0 auto;width:max-content}#dxpCv{display:block;background:#fff}
#dxpO{position:absolute;left:0;top:0}#dxpO.zm{cursor:crosshair}
#dxpO .tb{fill:rgba(46,204,113,.06);stroke:var(--okt);stroke-dasharray:6 4;vector-effect:non-scaling-stroke;stroke-width:1.5px}
#dxpO .hl{fill:rgba(232,130,12,.22);stroke:var(--accent);vector-effect:non-scaling-stroke;stroke-width:2px}
#dxpO .zn{fill:rgba(52,120,246,.10);stroke:#3478f6;vector-effect:non-scaling-stroke;stroke-width:2px;stroke-dasharray:5 3}
#dxpO text{fill:var(--okt);font-family:'Barlow',sans-serif}
#dxi .dxp-b{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:12px}#dxi .dxp-b .btn{padding:4px 9px}
#dxi .dxp-s{font-size:12px;display:flex;flex-direction:column;gap:8px}#dxi .dxp-s .fd{margin:0}#dxi .dxp-s fieldset{border:1px solid var(--border);border-radius:6px;padding:6px 8px;margin:0}
#dxi .dxp-s legend{font-weight:600;padding:0 4px}
#dxpO .od{fill:rgba(232,170,12,.18);stroke:var(--acct);stroke-dasharray:3 2;vector-effect:non-scaling-stroke;stroke-width:1px}
#dxi .dxo{border:1px solid var(--border);border-radius:6px;padding:6px 8px;margin:10px 0 0;font-size:12px}#dxi .dxo legend{font-weight:600;padding:0 4px}
#dxoT td{vertical-align:top}#dxoT .fi{padding:3px 5px;font-size:12px;min-width:60px;width:100%;box-sizing:border-box}#dxoT th{position:sticky;top:0;background:var(--surface);z-index:1}
#dxoT .fi.dt{border-color:var(--acct);background:rgba(232,170,12,.14)}#dxoT .fi.ed{border-color:var(--okt)}#dxoT tr.on td{background:rgba(232,130,12,.16)}
#dxoT td.ac{white-space:nowrap}#dxoT td.ac .btn{padding:2px 6px}#dxoP progress{width:100%}
@media (max-width:820px){#dxi .dxi-w,#dxi .dxi-g,#dxi .dxp{grid-template-columns:1fr}}
</style>`)}

function dxiOpen(){dxiCss();modal(`<div class="cd" style="margin:0" id="dxi" ondragover="event.preventDefault();this.classList.add('drop')" ondragleave="this.classList.remove('drop')"
  ondrop="event.preventDefault();this.classList.remove('drop');dxiFile(event.dataTransfer.files[0])"><div class="ct">📥 Importer un plan</div>
  <div class="hint">Formats lus : <b>DXF</b> ASCII (nomenclatures de réservations, rectangles, carrés et cercles du dessin) et <b>PDF</b> (nomenclatures en texte
  extractible, aperçu des pages, saisie assistée si le tableau n'est pas lisible). Chaque réservation est à confirmer ; aucun ouvrage n'est créé avant
  « Créer les ouvrages sélectionnés ». Les projets et plans déjà enregistrés ne sont pas modifiés. Pour ouvrir un projet CoffraPlan (.json) : 📂 Charger.</div>
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><label class="btn bs bo" style="cursor:pointer;display:inline-flex;align-items:center">📂 Choisir un plan (.dxf, .pdf)
  <input type="file" id="dxiF" accept=".dxf,.pdf" hidden onchange="dxiFile(this.files[0]);this.value=''"></label><span class="mu">ou glisser le fichier ici</span><span id="dxiN" style="font-size:12px"></span></div>
  <div id="dxiZ"></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:10px"><button class="btn bs bo" onclick="closeModal()">Fermer</button>
  <button class="btn bs bpr" id="dxiGo" disabled onclick="dxiCreate()">Créer les ouvrages sélectionnés (0)</button></div></div>`,true);
  if(DXI)dxiRender()}

function dxiErr(nom,lu){dxiQuit();if(!el('dxiZ'))return;el('dxiN').innerHTML=`<b>${esc(nom)}</b>`;
  el('dxiZ').innerHTML=`<div class="hint" style="margin:10px 0 0;border-left-color:var(--red)">⛔ Fichier non lu : ${esc(lu.message)}${(lu.erreurs||[]).length?' — '+esc(lu.erreurs.slice(0,5).join(' · ')):''}</div>`;dxiBtn()}
function dxiQuit(){if(DXI&&DXI.ocJob)CPI.ocr.arreter();if(DXI&&DXI.pdf)CPI.pdf.fermer(DXI.pdf);DXI=null}
// Format reconnu au contenu (en-tête %PDF, DWG « AC10 ») puis à l'extension ; DXF : UTF-8 strict (R2007 et suivants), sinon CP-1252 (R12 à R2004)
async function dxiFile(f){if(!f)return;let b,txt;
  try{b=await f.arrayBuffer()}catch(e){return dxiErr(f.name,{message:'fichier illisible'})}
  const deb=new TextDecoder('latin1').decode(new Uint8Array(b,0,Math.min(1024,b.byteLength))),ext=(f.name.match(/\.([a-z0-9]+)$/i)||[,''])[1].toLowerCase();
  if(deb.includes('%PDF-'))return dxpFile(f.name,b);
  if(ext==='pdf')return dxiErr(f.name,{message:'en-tête %PDF absent : ce n\'est pas un PDF lisible'});
  if(/^AC1\d/.test(deb)||ext==='dwg')return dxiErr(f.name,{message:'DWG pas encore pris en charge : exporter le plan en DXF ASCII (ou en PDF) depuis le logiciel de DAO'});
  if(ext==='ifc'||/^ISO-10303-21/.test(deb))return dxiErr(f.name,{message:'IFC pas encore pris en charge à l\'import : formats lus : DXF et PDF'});
  try{txt=new TextDecoder('utf-8',{fatal:true}).decode(b)}catch(e){txt=new TextDecoder('windows-1252').decode(b)}
  const lu=CPI.lecteur.lirePlan({format:'dxf',nom:f.name,contenu:txt});
  if(!lu.ok)return dxiErr(f.name,lu);
  dxiQuit();const doc=lu.document,C=CPI.detecteur.detecter(doc).candidats,cur=coll(),lay={},NA=CPI.nomenclatures.analyser(doc);
  C.forEach(c=>{lay[c.source.calque]=true});
  const NL=NA.nomenclatures.flatMap(N=>N.lignes.map(L=>({N,L})));
  DXI={fmt:'dxf',nom:f.name,doc,C,R:C.map(()=>({conf:false,forme:'',h:'',ref:''})),lay,u:doc.unite||'',ch:cur.ch,ouv:cur.ouv,ind:'',hCom:'',sel:-1,M:null,
    NA,NL,NR:NL.map(({L})=>({conf:false,forme:'',cotes:'',cotesT:false,h:'',ref:String(L.repere||'').toUpperCase(),geo:'',geoT:false})),NU:{},nsel:-1,vue:NL.length?'n':'g',lk:new Set()};
  dxnAssoc();if(el('dxiZ'))dxiRender()}

// Plans modèles (chantier, CP, options) pour chaque forme visée : même méthode que serAnalyse, formulaire rétabli ensuite
function dxiModels(){const D=DXI,tpl=coll(),tplS=formSnap(),ei=EI,ho=_hisOff,M={},ch=String(D.ch||'').trim().toUpperCase(),ouv=String(D.ouv||'').trim();delete tpl.date;
  _hisOff=true;try{_loading=true;try{el('iCh').value=ch;el('iOuv').value=ouv}finally{_loading=false}
    ['rect','carre','rect_fond','carre_fond','circ'].forEach(f=>{let d;
      if(f===tpl.forme)d=JSON.parse(JSON.stringify(tpl));else{_loading=true;try{el('iForme').value=f;updF()}finally{_loading=false}applyProf(true);d=coll();delete d.date}
      M[f]=Object.assign(d,{ch,ouv})})}
  finally{_loading=true;try{setForm(JSON.parse(tplS))}finally{_loading=false}EI=ei;_hisOff=ho;syncVis()}
  D.M=M}
const dxiVis=i=>DXI.lay[DXI.C[i].source.calque]&&!(DXI.lk&&DXI.lk.has(i));   // géométrie rattachée à une ligne de nomenclature : dans l'autre vue
function dxiDef(c){if(c.type==='circ')return 'circ';const k=DXI_MM[DXI.u];return (k?(c.dims.L-c.dims.l)*k<0.5:c.dims.L-c.dims.l<=1e-6*c.dims.L)?'carre':'rect'}
function dxiFormes(c){return c.type==='circ'?['circ']:dxiDef(c)==='carre'?['carre','carre_fond']:['rect','rect_fond']}
function dxiDims(c){const k=DXI_MM[DXI.u],v=x=>dxiNum(k?x*k:x),u=k?'':' (unité ?)';
  return (c.type==='circ'?'Ø '+v(c.dims.D)+u:v(c.dims.L)+' × '+v(c.dims.l)+u)+(c.dims.angle?' · '+dxiNum(c.dims.angle)+'°':'')}

// État de chaque ligne : np (non pris en charge) · ac (à compléter) · er (refusé) · wn / ok (prêt) ; x = sortie de versPlan
function dxiEval(){const D=DXI;if(!D.M)dxiModels();const hc=parseCote(D.hCom,'mm'),moteur={migr,canon,limErr,checks,badDims};
  D.R.forEach((r,i)=>{const c=D.C[i];r.x=null;
    if(c.statut!=='a_confirmer'){r.st='np';r.msg=c.remarques.join(' · ')||'géométrie non prise en charge';return}
    let h=hc;if(String(r.h).trim()!==''){try{h=parseCote(r.h,'mm')}catch(e){h=null}}
    const man=[];if(!D.u)man.push('unité du fichier');if(!(h>0))man.push(String(r.h).trim()?'hauteur illisible':'hauteur');if(!String(D.ch||'').trim())man.push('chantier');
    if(man.length){r.st='ac';r.msg='à compléter : '+man.join(', ');return}
    const x=CPI.adaptateur.versPlan(c,{confirme:true,forme:r.forme||dxiDef(c),h,unite:D.u,ref:r.ref.trim()},{moteur,modele:D.M[r.forme||dxiDef(c)]});
    if(!x.ok){r.st='er';r.msg=x.message+(x.messages&&x.messages.length?' : '+x.messages.join(' · '):'');return}
    const p=x.plan;
    if(p.ref&&P.some(q=>chKey(q.ch)===chKey(p.ch)&&ouKey(q.ouv).toLowerCase()===ouKey(p.ouv).toLowerCase()&&String(q.ref||'').toUpperCase()===p.ref)){r.st='er';r.msg=`référence ${p.ref} déjà utilisée dans cet ouvrage`;return}
    r.x=x;r.st=x.alertes.length?'wn':'ok';r.msg=x.alertes.join(' · ')});
  dxnEval(moteur,hc);
  // références saisies en double dans le lot (lignes confirmées des deux vues)
  const n={},Lr=D.R.filter((r,i)=>r.x&&r.conf&&dxiVis(i)).concat((D.NR||[]).filter(r=>r.x&&r.conf));
  Lr.forEach(r=>{if(r.x.plan.ref)n[r.x.plan.ref]=(n[r.x.plan.ref]||0)+1});
  Lr.forEach(r=>{if(n[r.x.plan.ref]>1){r.x=null;r.st='er';r.msg='référence en double dans l\'import'}})}
const dxiReady=()=>DXI?DXI.R.map((r,i)=>i).filter(i=>DXI.R[i].conf&&DXI.R[i].x&&dxiVis(i)):[];
const dxnReady=()=>DXI&&DXI.NR?DXI.NR.map((r,k)=>k).filter(k=>DXI.NR[k].conf&&DXI.NR[k].x):[];
function dxiBtn(){const b=el('dxiGo');if(!b)return;const n=dxiReady().length+dxnReady().length;b.disabled=!n;b.textContent=`Créer les ouvrages sélectionnés (${n})`}

function dxiHead(){const D=DXI,d=D.doc,pdf=D.fmt==='pdf';if(!el('dxiN'))return;
  const nO=D.NL.filter(x=>x.N.ocr).length;
  el('dxiN').innerHTML=pdf?`<b>${esc(D.nom)}</b> · ${esc(d.version)} · ${d.pages.length} page(s) · `+(D.NL.some(x=>!x.N.saisie&&!x.N.ocr)?`lecture automatique : <b>${D.NL.filter(x=>!x.N.saisie&&!x.N.ocr).length} ligne(s) de nomenclature</b>`
      :'<b style="color:var(--acct)">aucune nomenclature lisible automatiquement : OCR ou saisie assistée</b>')+(nO?` · OCR : <b>${nO} ligne(s)</b>`:'')
    :`<b>${esc(D.nom)}</b>${d.version?' · DXF '+esc(d.version):''} · unité : ${d.unite?`<b>${d.unite}</b> (donnée par le fichier)`:'<b style="color:var(--redt)">absente du fichier</b>'}`}
function dxiRender(){const D=DXI,Z=el('dxiZ');if(!Z||!D)return;const d=D.doc,pdf=D.fmt==='pdf';dxiHead();
  const L=[...new Set(D.C.map(c=>c.source.calque))].sort(_cmp),nb=k=>D.C.filter(c=>c.source.calque===k&&c.statut==='a_confirmer').length,
    NA=D.NA,E=NA.ecartes.map(e=>`${esc(e.id)}${e.titre?' « '+esc(e.titre.replace(/\n/g,' '))+' »':''} (${dxnOu(e)}, ${e.nLignes} ligne(s)) : ${esc(e.raison)}`).concat(NA.signalements.map(esc));
  Z.innerHTML=(d.unite||pdf?'':`<div class="dxi-u">⚠ Le fichier ne donne pas son unité ($INSUNITS absent ou nul, toujours le cas en R12). Unité des cotes du dessin :
    <select class="fi" id="dxiU" onchange="DXI.u=this.value;dxnAssoc();dxiRows()"><option value="">— choisir —</option>${['mm','cm','m'].map(u=>`<option${D.u===u?' selected':''}>${u}</option>`).join('')}</select></div>`)
  +`<div class="dxi-g"><div class="fd"><label>Chantier</label><input class="fi" id="dxiCh" value="${esc(D.ch)}" onchange="DXI.ch=this.value;DXI.M=null;dxiUpd()"></div>
    <div class="fd"><label>Ouvrage</label><input class="fi" id="dxiOuv" value="${esc(D.ouv)}" onchange="DXI.ouv=this.value;DXI.M=null;dxiUpd()"></div>
    <div class="fd"><label>Indice du plan source</label><input class="fi" id="dxiInd" value="${esc(D.ind)}" placeholder="ex. B" oninput="DXI.ind=this.value"></div>
    <div class="fd"><label>Hauteur commune (mm)</label><input class="fi" id="dxiH" value="${esc(D.hCom)}" placeholder="facultative" oninput="DXI.hCom=this.value;dxiHph();dxiUpd()"></div></div>
  ${E.length?`<details class="mu" id="dxiE" style="margin-top:8px"><summary>Tableaux non retenus et limites de lecture (${E.length})</summary><ul style="margin:4px 0">${E.map(x=>'<li>'+x+'</li>').join('')}</ul>
    <div>Ces tableaux sont signalés, pas utilisés : leurs lignes ne deviennent pas des réservations.</div></details>`:''}
  ${D.NL.length||pdf?`<div class="dxi-tab" role="tablist"><button id="dxiTabN" role="tab" onclick="dxiVue('n')">Nomenclature des réservations (${D.NL.length})</button>
    <button id="dxiTabG" role="tab" onclick="dxiVue('g')"${D.C.length?'':' hidden'}>Géométries du dessin</button>${pdf?'<button id="dxiTabP" role="tab" onclick="dxiVue(\'p\')">Aperçu du plan</button>':''}</div>${dxnPane()}${pdf?dxpPane():''}`:''}
  <div id="dxiPG">
  <div class="dxi-l"><b>Calques analysés</b>${L.map(k=>`<label><input type="checkbox" data-lay="${esc(k)}"${D.lay[k]?' checked':''} onchange="DXI.lay[this.dataset.lay]=this.checked;dxiRows()"> ${esc(k)} (${nb(k)})</label>`).join('')}</div>
  <div class="dxi-s" id="dxiS"></div>
  <div class="dxi-w"><div><svg id="dxiV" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Schéma des réservations reconnues"></svg>
    <div class="hint" style="margin:6px 0 0">Schéma des réservations reconnues, à leur position et orientation dans le DXF (contours en tirets : polylignes non reconnues).
    Ce n'est pas un rendu complet du fichier : textes, lignes, blocs, hachures… ne sont pas dessinés.</div></div>
  <div><div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap"><button class="btn bs bo" onclick="dxiAll(true)" title="Cocher les lignes visibles prêtes (✓ ou ⚠)">✓ Confirmer les lignes prêtes</button><button class="btn bs bo" onclick="dxiAll(false)">Tout décocher</button></div>
  <div class="dxi-t"><table class="ser" id="dxiT"><thead><tr><th title="Confirmer">Créer</th><th>#</th><th>Entité DXF</th><th>Calque</th><th>Forme</th><th>Cotes (mm)</th><th>h (mm)</th><th>Réf.</th><th>Statut</th></tr></thead><tbody></tbody></table></div></div></div>
  <details id="dxiNP"><summary></summary><table class="ser"><thead><tr><th>#</th><th>Entité DXF</th><th>Calque</th><th>Raison</th></tr></thead><tbody></tbody></table></details></div>
  <div class="hint" id="dxiP" style="margin:8px 0 0"></div>`;
  dxiRows();if(D.NL.length||pdf){dxnRows();dxiVue(D.vue)}if(pdf)dxoGrille()}
const dxnOu=N=>N.page?'page '+N.page:N.espace==='objet'?'espace Objet':'présentation « '+esc(N.presentation||'?')+' »';
function dxiHph(){const v=DXI.hCom.trim();document.querySelectorAll('#dxiT input[data-k=h],#dxnT input[data-k=h]').forEach(e=>{e.placeholder=v||'à saisir'})}
// Liste, aperçu et bilan des lignes visibles (calques cochés) ; cotes affichées selon l'unité choisie
function dxiRows(){const D=DXI,T=el('dxiT');if(!T)return;
  const V=D.C.map((c,i)=>i).filter(dxiVis),ok=V.filter(i=>D.C[i].statut==='a_confirmer'),np=V.filter(i=>D.C[i].statut!=='a_confirmer');
  T.tBodies[0].innerHTML=ok.length?ok.map(i=>{const c=D.C[i],r=D.R[i],fo=r.forme||dxiDef(c);
    return `<tr data-i="${i}" onclick="dxiSel(${i})"><td><input type="checkbox" data-k="conf"${r.conf?' checked':''} aria-label="Créer ${esc(c.id)}" onchange="DXI.R[${i}].conf=this.checked;dxiUpd()"></td>
    <td>${esc(c.id)}</td><td>${esc(c.source.id)}</td><td>${esc(c.source.calque)}</td>
    <td><select class="fi" data-k="forme" onchange="DXI.R[${i}].forme=this.value;dxiUpd()">${dxiFormes(c).map(f=>`<option value="${f}"${f===fo?' selected':''}>${esc(fmLb(f))}${/_fond$/.test(f)?' (choix explicite)':''}</option>`).join('')}</select></td>
    <td>${esc(dxiDims(c))}</td><td><input class="fi" data-k="h" style="width:70px" value="${esc(r.h)}" placeholder="${esc(D.hCom.trim()||'à saisir')}" oninput="DXI.R[${i}].h=this.value;dxiUpd()"></td>
    <td><input class="fi" data-k="ref" style="width:70px" value="${esc(r.ref)}" placeholder="auto" oninput="DXI.R[${i}].ref=this.value;dxiUpd()"></td><td class="st"></td></tr>`}).join('')
    :`<tr><td colspan="9" style="color:var(--muted)">Aucune réservation reconnue sur les calques cochés.</td></tr>`;
  const NP=el('dxiNP');NP.querySelector('summary').textContent=`Géométries non prises en charge, non créées (${np.length})`;
  NP.querySelector('tbody').innerHTML=np.slice(0,DXI_NP).map(i=>{const c=D.C[i];return `<tr class="np"><td>${esc(c.id)}</td><td>${esc(c.source.id)}</td><td>${esc(c.source.calque)}</td><td>${esc(c.remarques.join(' · ')||'géométrie non prise en charge')}</td></tr>`}).join('')
    +(np.length>DXI_NP?`<tr class="np"><td colspan="4">… et ${np.length-DXI_NP} autre(s)</td></tr>`:'');
  dxiSvg(V);dxiUpd()}
// Aperçu : coordonnées du DXF (Y vers le haut), échelle ajustée à la zone ; numéros = colonne #
function dxiSvg(V){const D=DXI,S=el('dxiV');if(!S)return;const sh=[],pts=[];
  V.forEach(i=>{const c=D.C[i],g=c.geometrie;
    if(g.type==='cercle'){pts.push([g.centre[0]-g.r,g.centre[1]-g.r],[g.centre[0]+g.r,g.centre[1]+g.r]);sh.push({i,c,g})}
    else if(g.type==='polyligne'&&g.points&&g.points.length>1){g.points.forEach(p=>pts.push(p));sh.push({i,c,g})}});
  if(!pts.length){S.removeAttribute('viewBox');S.innerHTML='<text x="50%" y="50%" text-anchor="middle" font-size="13">Aucune géométrie à dessiner</text>';return}
  const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),
    w=Math.max(x1-x0,1e-9),h=Math.max(y1-y0,1e-9),m=Math.max(w,h)*0.06,fs=Math.max(w,h)*0.028;
  S.setAttribute('viewBox',`${x0-m} ${-y1-m} ${w+2*m} ${h+2*m}`);
  S.innerHTML=sh.map(({i,c,g})=>{const ok=c.statut==='a_confirmer',a=ok?`class="c" data-i="${i}" onclick="dxiSel(${i},1)"`:'class="np"',t=ok?`<title>${esc(c.id+' · '+c.source.calque+' · '+dxiDims(c))}</title>`:'';
    const e=g.type==='cercle'?`<circle ${a} cx="${g.centre[0]}" cy="${-g.centre[1]}" r="${g.r}">${t}</circle>`
      :`<${g.ferme?'polygon':'polyline'} ${a} points="${g.points.map(p=>p[0]+','+(-p[1])).join(' ')}">${t}</${g.ferme?'polygon':'polyline'}>`;
    return e+(ok&&c.centre?`<text x="${c.centre[0]}" y="${-c.centre[1]}" font-size="${fs}" text-anchor="middle" dominant-baseline="central">${esc(c.id.slice(1))}</text>`:'')}).join('')}
function dxiSel(i,fromSvg){const D=DXI;if(!D)return;D.sel=i;
  document.querySelectorAll('#dxiT tr[data-i]').forEach(t=>t.classList.toggle('on',+t.dataset.i===i));
  document.querySelectorAll('#dxiV .c').forEach(s=>s.classList.toggle('on',+s.dataset.i===i));
  if(fromSvg){const t=document.querySelector(`#dxiT tr[data-i="${i}"]`);if(t)t.scrollIntoView({block:'nearest'})}}
function dxiAll(on){const D=DXI;if(!D)return;dxiEval();D.R.forEach((r,i)=>{if(dxiVis(i)&&D.C[i].statut==='a_confirmer')r.conf=on?r.conf||!!r.x:false});
  document.querySelectorAll('#dxiT tr[data-i]').forEach(t=>{t.querySelector('[data-k=conf]').checked=D.R[+t.dataset.i].conf});dxiUpd()}
// Statuts, bilan, couleurs de l'aperçu et compte du bouton final, sans reconstruire la liste (garde la saisie en cours)
function dxiUpd(){const D=DXI;if(!D||!el('dxiT'))return;dxiEval();
  const lb={ok:'✓ prêt',wn:'⚠ prêt — ',ac:'… ',er:'⛔ non créé — '};
  document.querySelectorAll('#dxiT tr[data-i]').forEach(t=>{const i=+t.dataset.i,r=D.R[i],s=t.querySelector('.st');s.className='st '+(r.st==='ac'?'wn':r.st);s.textContent=lb[r.st]+(r.st==='ok'?'':r.msg)});
  document.querySelectorAll('#dxiV .c').forEach(s=>{const i=+s.dataset.i;s.classList.toggle('cf',D.R[i].conf);s.classList.toggle('on',i===D.sel)});
  const V=D.C.map((c,i)=>i).filter(dxiVis),ok=V.filter(i=>D.C[i].statut==='a_confirmer'),nr=ok.filter(i=>D.C[i].type==='rect').length,
    pr=ok.filter(i=>D.R[i].x).length,cf=ok.filter(i=>D.R[i].conf).length,n=dxiReady().length;
  el('dxiS').innerHTML=`<b>${ok.length} réservation(s) potentielle(s)</b> (${nr} rectangle(s) ou carré(s), ${ok.length-nr} cercle(s)) · ${pr} prête(s) · ${cf} confirmée(s) · <b>${n} à créer</b> · ${V.length-ok.length} géométrie(s) non prise(s) en charge`
    +(D.lk&&D.lk.size?` · ${D.lk.size} rattachée(s) à la nomenclature (vue « Nomenclature »)`:'');
  dxnUpd();dxiParams();dxiBtn()}
// Rappel des réglages repris du formulaire / du profil du chantier pour les formes à créer
function dxiParams(){const D=DXI,z=el('dxiP');if(!z||!D.M)return;const F=[...new Set(dxiReady().map(i=>D.R[i].forme||dxiDef(D.C[i])).concat(dxnReady().map(k=>D.NR[k].x.plan.forme)))];
  z.style.display=F.length?'':'none';
  z.innerHTML='Repris du formulaire ou du profil du chantier : '+F.map(f=>{const m=D.M[f],o=[m.gs&&'goussets',m.renX&&'renforts en croix',m.feuil&&'feuillure'].filter(Boolean);
    return `<b>${esc(fmLb(f))}</b> ${f==='circ'?'matériau '+esc(m.mat||'—'):esc(cpName(m.cp&&m.cp.j))+' · '+esc(String(m.mont||'').toLowerCase())+' · options : '+(o.length?o.join(', '):'aucune')}`}).join(' ; ')}

// Références automatiques : celles du projet et celles saisies dans le lot sont réservées d'abord, puis nextRef sans collision
const dxiKey=(d,r)=>chKey(d.ch)+'\u0000'+ouKey(d.ouv).toLowerCase()+'\u0000'+String(r==null?d.ref||'':r).toUpperCase();
function dxiRefs(L){const used=new Set(P.map(p=>dxiKey(p)));L.forEach(d=>{if(d.ref)used.add(dxiKey(d))});
  L.forEach(d=>{if(d.ref)return;let r=nextRef(d.ch,d.ouv);const m=r.match(/^([A-Z]*)(\d+)$/);let n=+m[2];
    while(used.has(dxiKey(d,r)))r=m[1]+String(++n).padStart(m[2].length,'0');d.ref=r;used.add(dxiKey(d))});
  const seen=new Set(P.map(p=>dxiKey(p)));return L.every(d=>!seen.has(dxiKey(d))&&(seen.add(dxiKey(d)),true))}

// Création : lignes confirmées et acceptées par le moteur seulement ; ajoutées à la suite (rien n'est remplacé), annulables
function dxiCreate(){const D=DXI;if(!D)return;dxiEval();const L=dxiReady(),LN=dxnReady();if(!L.length&&!LN.length)return dxiBtn();
  const uids=[],today=new Date().toISOString().slice(0,10),ind=String(D.ind||'').trim().toUpperCase()||null;
  // lignes de nomenclature d'abord (ordre du tableau), puis géométries ; provenance de la ligne (textes sources, choix, géométrie rattachée)
  const N=LN.map(k=>{const r=D.NR[k],d=JSON.parse(JSON.stringify(r.x.plan));d.date=today;d.origineImport=Object.assign(dxnProv(k),{indice:ind,date:today});return d})
    .concat(L.map(i=>{const x=D.R[i].x,d=JSON.parse(JSON.stringify(x.plan));d.date=today;
    d.origineImport=Object.assign(JSON.parse(JSON.stringify(x.provenance)),{indice:ind,date:today});return d}));
  // dernière vérification avant de toucher aux plans enregistrés : aucune référence en double, sinon rien n'est créé
  if(!dxiRefs(N)){toast('⛔ Références en double : aucun ouvrage créé');return dxiUpd()}
  N.forEach(d=>{uids.push(planUid(d));P.push(d)});
  svP();profFromPlans(P.slice(-N.length));profLists();rnL();updBtn();closeModal();const nom=D.nom;dxiQuit();
  toast(`${N.length} ouvrage(s) créé(s) depuis ${nom}`,'Annuler',()=>{const u=EI>=0&&P[EI]?P[EI].uid:null;P=P.filter(p=>!uids.includes(p.uid));EI=u?P.findIndex(p=>p.uid===u):-1;svP();rnL();updBtn();toast('Import annulé')})}

// ==== Nomenclatures de réservations (vue par défaut quand le DXF en contient) ====
const DXN_ST={trouvee:'✓ trouvée, cohérente',probable:'≈ probable, à vérifier',multiple:'⋯ plusieurs possibles',absente:'∅ non retrouvée',choisie:'✓ choisie'};
const DXN_OPT=12;   // shortcut: au plus 12 géométries proposées par ligne (les autres sont comptées) ; liste filtrable si un vrai plan l'exige
const dxnU=(N,L)=>L.dims&&L.dims.unite||DXI.NU[N.id]||N.unite||'';
const dxnDims=r=>CPI.nomenclatures.cotes(r.cotes,'mm',true);
function dxnDef(dm){return dm.etat==='circ'?'circ':dm.etat==='rect'?(Math.abs(dm.a-dm.b)<0.5?'carre':'rect'):''}
function dxnFormes(dm){return dm.etat==='circ'?['circ']:dm.etat==='rect'?(dxnDef(dm)==='carre'?['carre','carre_fond']:['rect','rect_fond']):['','rect','carre','rect_fond','carre_fond','circ']}
// Cotes proposées (mm) : celles du tableau, si leur unité est connue ; jamais devinées
function dxnPre(k){const {N,L}=DXI.NL[k],d=L.dims,f=DXI_MM[dxnU(N,L)];if(!d||!f)return'';return d.type==='circ'?'Ø '+dxiNum(d.D*f):dxiNum(d.a*f)+' × '+dxiNum(d.b*f)}
// Rapprochements (à refaire si l'unité du dessin ou d'un tableau change) ; une correspondance « trouvée » est rattachée d'office, modifiable
function dxnAssoc(){const D=DXI;if(!D.NL.length)return;
  // PDF : aucune géométrie de la page n'est rattachée (échelle inconnue) ; les lignes gardent leurs cotes écrites ou saisies
  D.AS=D.fmt==='pdf'?{}:CPI.nomenclatures.associer(D.NA.nomenclatures,D.C,D.doc,{uniteDessin:D.u,unites:D.NU,exclus:D.NA.ecartes.flatMap(e=>e.ids)});
  D.NL.forEach(({L},k)=>{const r=D.NR[k],a=dxnAS(L);if(!r.cotesT)r.cotes=dxnPre(k);if(!r.geoT)r.geo=a.statut==='trouvee'?String(a.options[0].c):''});dxnLinks()}
const DXN_AS0={statut:'absente',options:[],reperes:[],note:''};
const dxnAS=L=>DXI.AS&&DXI.AS[L.id]||DXN_AS0;   // ligne saisie ou ajoutée après le rapprochement : aucune géométrie
function dxnLinks(){DXI.lk=new Set(DXI.NR.filter(r=>r.geo!=='').map(r=>+r.geo))}
function dxnPane(){const D=DXI,NA=D.NA,pdf=D.fmt==='pdf';
  const vide=pdf&&!D.NL.length?`<div class="hint" style="margin:8px 0;border-left-color:var(--acct)"><b>Aucune nomenclature de réservations exploitable n'a été reconnue automatiquement.</b>
    Rien n'est inventé : aucune ligne n'est proposée. ${D.doc.pages.map(p=>`Page ${p.n} : ${esc(CPI.pdf.LIB_NAT[p.nature]||p.nature)}`).join(' · ')}.
    <br>Onglet <a href="#" onclick="dxiVue('p');return false">Aperçu du plan</a> : sélectionner la zone du tableau pour l'analyser, la reconnaître par OCR (textes dessinés ou numérisés), ou saisir les lignes en consultant le PDF (saisie assistée).</div>`:'';
  return `<div id="dxiPN"><div class="dxi-s" id="dxnS"></div>${vide}${NA.nomenclatures.map(N=>{const cs=N.colonnes.map(c=>`${esc((c.titre||'(sans titre)').replace(/\n/g,' '))} → ${CPI.nomenclatures.LIB[c.cle]}`).join(' · '),
      sansU=N.lignes.some(L=>L.dims&&!L.dims.unite)&&!N.unite;
    return `<div class="dxn-i"><b>${N.saisie?'Saisie assistée':'Tableau '+esc(N.id)+(N.ocr?' (OCR)':'')}</b>${N.titre&&!N.saisie?' « '+esc(N.titre.replace(/\n/g,' '))+' »':''} · ${dxnOu(N)}${N.zone&&!N.saisie?' (zone choisie)':''}
      ${N.calques.length?'· calque(s) '+esc(N.calques.join(', ')):''} · <b>${N.lignes.length} ligne(s)</b> · lecture : <b>${esc(N.qualite.niveau)}</b> (${esc(N.qualite.motifs.join(' ; '))})
      ${sansU?` · <span style="color:var(--acct)">unité des cotes non indiquée :</span> <select class="fi" data-nu="${esc(N.id)}" onchange="DXI.NU[this.dataset.nu]=this.value;dxnAssoc();dxnRows()"><option value="">— choisir —</option>${['mm','cm','m'].map(u=>`<option${D.NU[N.id]===u?' selected':''}>${u}</option>`).join('')}</select>`:N.unite?` · cotes en ${N.unite} (en-tête)`:''}
      <div class="mu">Colonnes : ${cs}</div></div>`}).join('')}
    <div class="hint" style="margin:6px 0">Toutes les lignes des tableaux sont proposées, quels que soient le type, le lot ou le fournisseur : rien n'est coché d'office.
    Cotes en mm (ex. 650x800 ou Ø250 ; tableau : ouverture l × h). Niveau et angle = position de la réservation : ils ne donnent ni la hauteur à coffrer ni la rotation du coffrage.</div>
    <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap"><button class="btn bs bo" onclick="dxnAll(true)">☑ Tout sélectionner</button><button class="btn bs bo" onclick="dxnAll(false)">Tout décocher</button>
    <button class="btn bs bo" onclick="dxnRefs(true)" title="Référence CoffraPlan = repère du tableau">Références du tableau</button><button class="btn bs bo" onclick="dxnRefs(false)" title="Références vides : numérotation automatique CoffraPlan">Références CoffraPlan automatiques</button></div>
    <div class="dxi-t"><table class="ser" id="dxnT"><thead><tr><th>Créer</th><th>Repère</th><th>Désignation</th><th>Ouverture · réseau</th><th>Niveau · angle</th><th>Forme</th><th>Cotes (mm)</th><th>h (mm)</th><th>Réf.</th><th>${pdf?'Source':'Géométrie du dessin'}</th><th>Statut</th></tr></thead><tbody></tbody></table></div>
    ${pdf?`<div class="hint" style="margin:6px 0 0">Source : ouvre la page du PDF avec la ligne encadrée. Les contours dessinés sur un PDF ne donnent pas de cotes (échelle de la page inconnue) : seules les cotes écrites dans le tableau ou saisies sont utilisées.</div></div>`
    :`<svg id="dxnV" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Correspondances possibles dans le dessin"></svg>
    <div class="hint" style="margin:6px 0 0">Schéma des géométries proposées pour les lignes (espace Objet) ; points : repères trouvés dans le dessin. Ligne sélectionnée : propositions en orange, un clic en choisit une.</div></div>`}`}
function dxiVue(v){const D=DXI;if(!D||!el('dxiPN'))return;D.vue=v;
  [['n','dxiPN','dxiTabN'],['g','dxiPG','dxiTabG'],['p','dxiPP','dxiTabP']].forEach(([k,z,t])=>{if(el(z))el(z).style.display=v===k?'':'none';if(el(t)){el(t).classList.toggle('on',v===k);el(t).setAttribute('aria-selected',v===k)}});
  if(v==='g')dxiRows();if(v==='p')dxpPage()}
function dxnRows(){const D=DXI,T=el('dxnT');if(!T)return;
  T.tBodies[0].innerHTML=D.NL.map(({N,L},k)=>{const r=D.NR[k],det=N.colonnes.map((c,j)=>L.cellules[j]?`${(c.titre||'colonne '+(j+1)).replace(/\n/g,' ')} : ${L.cellules[j].replace(/\n/g,' ')}`:'').filter(Boolean).join('\n'),
      ds=[L.description,L.type&&'Type : '+L.type,L.observations&&'Obs. : '+L.observations,L.lot&&'Lot : '+L.lot].filter(Boolean).join('\n');
    return `<tr data-n="${k}" onclick="dxnSel(${k})" title="${esc(N.id+' ligne '+L.rang+'\n'+det)}"><td><input type="checkbox" data-k="conf"${r.conf?' checked':''} aria-label="Créer ${esc(L.repere||L.id)}" onchange="DXI.NR[${k}].conf=this.checked;dxiUpd()"></td>
      <td><b>${esc(L.repere||'—')}</b><div class="mu">${esc(N.id)} · ${L.rang}</div></td><td>${esc(ds)}</td>
      <td>${esc(L.ouverture)}${L.reseau?`<div class="mu">réseau : ${esc(L.reseau)}</div>`:''}</td><td>${esc([L.niveau,L.angle].filter(Boolean).join(' · '))}</td>
      <td><select class="fi" data-k="forme" onchange="DXI.NR[${k}].forme=this.value;dxiUpd()"></select></td>
      <td><input class="fi" data-k="cotes" style="width:96px" value="${esc(r.cotes)}" placeholder="${esc(L.dims?L.dims.texte+(dxnU(N,L)?'':' (unité ?)'):'à saisir')}" oninput="DXI.NR[${k}].cotes=this.value;DXI.NR[${k}].cotesT=true;dxiUpd()"></td>
      <td><input class="fi" data-k="h" style="width:62px" value="${esc(r.h)}" placeholder="${esc(D.hCom.trim()||'à saisir')}" oninput="DXI.NR[${k}].h=this.value;dxiUpd()"></td>
      <td><input class="fi" data-k="ref" style="width:72px" value="${esc(r.ref)}" placeholder="auto" oninput="DXI.NR[${k}].ref=this.value;dxiUpd()"></td>
      <td>${D.fmt==='pdf'?`<button class="btn bs bo" onclick="event.stopPropagation();dxpVoir(${k})" title="Voir la ligne sur le PDF">p. ${N.page} ↗</button>${N.saisie?`<button class="btn bs bo" onclick="event.stopPropagation();dxpSuppr(${k})" title="Retirer cette ligne saisie" aria-label="Retirer la ligne saisie">✕</button>`:''}`
        :`<select class="fi" data-k="geo" style="max-width:190px" onchange="dxnGeo(${k},this.value)"></select><div class="gs"></div>`}</td><td class="st"></td></tr>`}).join('');
  dxiUpd()}
// Choix de la géométrie rattachée à une ligne (retirée de la vue « Géométries du dessin » ; aucune : elle y revient)
function dxnGeo(k,v){const r=DXI.NR[k];r.geo=v;r.geoT=true;dxnLinks();dxiUpd()}
function dxnSel(k){const D=DXI;if(!D)return;D.nsel=k;document.querySelectorAll('#dxnT tr[data-n]').forEach(t=>t.classList.toggle('on',+t.dataset.n===k));dxnSvg()}
function dxnAll(on){const D=DXI;if(!D)return;D.NR.forEach(r=>r.conf=on);document.querySelectorAll('#dxnT [data-k=conf]').forEach(e=>e.checked=on);dxiUpd()}
function dxnRefs(tab){const D=DXI;if(!D)return;D.NR.forEach((r,k)=>r.ref=tab?String(D.NL[k].L.repere||'').toUpperCase():'');
  document.querySelectorAll('#dxnT tr[data-n]').forEach(t=>t.querySelector('[data-k=ref]').value=D.NR[+t.dataset.n].ref);dxiUpd()}
// Lignes de nomenclature : cotes (mm) et forme saisies ou reprises du tableau → adaptateur (contrôles du moteur), comme les géométries
function dxnEval(moteur,hc){const D=DXI;if(!D.NL||!D.NL.length)return;
  D.NL.forEach(({N,L},k)=>{const r=D.NR[k],dm=dxnDims(r),fo=r.forme||dxnDef(dm);r.x=null;
    let h=hc;if(String(r.h).trim()!==''){try{h=parseCote(r.h,'mm')}catch(e){h=null}}
    const man=[];if(dm.etat!=='rect'&&dm.etat!=='circ')man.push(String(r.cotes).trim()?'cotes illisibles (ex. 650x800 ou Ø250)':L.dims&&!dxnU(N,L)?'unité des cotes du tableau':'cotes');
    if(!fo)man.push('forme');if(!(h>0))man.push(String(r.h).trim()?'hauteur illisible':'hauteur à coffrer');if(!String(D.ch||'').trim())man.push('chantier');
    if(man.length){r.st='ac';r.msg='à compléter : '+man.join(', ');return}
    const g=r.geo!==''?D.C[+r.geo]:null,x=CPI.adaptateur.versPlan(CPI.nomenclatures.candidat(N,L,{dims:dm,geo:g}),{confirme:true,forme:fo,h,unite:'mm',ref:r.ref.trim()},{moteur,modele:D.M[fo]});
    if(!x.ok){r.st='er';r.msg=x.message+(x.messages&&x.messages.length?' : '+x.messages.join(' · '):'');return}
    const p=x.plan;
    if(p.ref&&P.some(q=>chKey(q.ch)===chKey(p.ch)&&ouKey(q.ouv).toLowerCase()===ouKey(p.ouv).toLowerCase()&&String(q.ref||'').toUpperCase()===p.ref)){r.st='er';r.msg=`référence ${p.ref} déjà utilisée dans cet ouvrage`;return}
    r.x=x;r.st=x.alertes.length?'wn':'ok';r.msg=x.alertes.join(' · ')})}
function dxnProv(k){const D=DXI,{N,L}=D.NL[k],r=D.NR[k],a=dxnAS(L),g=r.geo!==''?D.C[+r.geo]:null,u=dxnU(N,L);
  return CPI.nomenclatures.provenance(N,L,{forme:r.x.plan.forme,cotes:r.cotes,dims:dxnDims(r),ref:r.ref.trim().toUpperCase(),uniteTableau:u||null,uniteDessin:D.u||null,
    uniteChoisie:!!(u&&!(L.dims&&L.dims.unite)&&!N.unite),geo:g?{c:g,statut:!r.geoT&&a.statut==='trouvee'?'trouvee':'choisie'}:null})}
// Statuts, formes possibles, géométries proposées, bilan (sans reconstruire la liste : garde la saisie en cours)
function dxnUpd(){const D=DXI;if(!D||!el('dxnT'))return;const lb={ok:'✓ prêt',wn:'⚠ prêt — ',ac:'… ',er:'⛔ non créé — '};
  document.querySelectorAll('#dxnT tr[data-n]').forEach(t=>{const k=+t.dataset.n,r=D.NR[k],{L}=D.NL[k],a=dxnAS(L),dm=dxnDims(r),F=dxnFormes(dm);
    if(r.forme&&!F.includes(r.forme))r.forme='';
    const sf=t.querySelector('[data-k=forme]'),fo=r.forme||dxnDef(dm),key=F.join();
    if(sf.dataset.f!==key){sf.dataset.f=key;sf.innerHTML=F.map(f=>`<option value="${f}">${f?esc(fmLb(f))+(/_fond$/.test(f)?' (choix explicite)':''):'— à choisir —'}</option>`).join('')}sf.value=fo;
    const sg=t.querySelector('[data-k=geo]'),O=a.options.slice(0,DXN_OPT),gk=O.map(o=>o.c).join()+'|'+D.u;
    if(sg){if(sg.dataset.g!==gk){sg.dataset.g=gk;sg.innerHTML=`<option value="">— aucune —</option>`+O.map(o=>{const c=D.C[o.c];
      return `<option value="${o.c}">${esc(c.id+' · '+dxiDims(c)+' · '+c.source.calque+(o.via==='cotes'?' · mêmes cotes':o.cotes==='diff'?' · cotes différentes':''))}</option>`}).join('')
      +(a.options.length>DXN_OPT?`<option disabled>… et ${a.options.length-DXN_OPT} autre(s)</option>`:'')}
    sg.value=r.geo;const gs=t.querySelector('.gs');gs.textContent=r.geo!==''&&r.geoT?DXN_ST.choisie:DXN_ST[a.statut];gs.title=a.note;
    gs.style.color=r.geo!==''||a.statut==='trouvee'?'var(--okt)':a.statut==='absente'?'var(--muted)':'var(--acct)'}
    const s=t.querySelector('.st');s.className='st '+(r.st==='ac'?'wn':r.st);
    s.innerHTML=esc(lb[r.st]+(r.st==='ok'?'':r.msg))+(L.a_verifier.length?`<div class="av">à vérifier : ${esc(L.a_verifier.join(' ; '))}</div>`:'')+(a.note?`<div class="mu">${esc(a.note)}</div>`:'')});
  const n={trouvee:0,probable:0,multiple:0,absente:0};D.NL.forEach(({L})=>n[dxnAS(L).statut]++);
  const NN=D.NA.nomenclatures.filter(N=>!N.saisie).length,cf=D.NR.filter(r=>r.conf).length,nS=D.NL.filter(x=>x.N.saisie).length;
  if(el('dxiTabN'))el('dxiTabN').textContent=`Nomenclature des réservations (${D.NL.length})`;
  if(D.fmt==='pdf'){const nO=D.NL.filter(x=>x.N.ocr).length;el('dxnS').innerHTML=`<b>${D.NL.length-nS-nO} ligne(s) lue(s)</b> dans ${NN} tableau${NN>1?'x':''} · ${nO} ligne(s) reconnue(s) par OCR · ${nS} ligne(s) saisie(s) · ${cf} sélectionnée(s) · <b>${dxnReady().length} à créer</b>`;return}
  el('dxnS').innerHTML=`<b>${D.NL.length} ligne(s) de nomenclature</b> dans ${NN} tableau${NN>1?'x':''} · géométries : ${n.trouvee} trouvée(s), ${n.probable} probable(s), ${n.multiple} à choisir parmi plusieurs, ${n.absente} non retrouvée(s)
    · ${cf} sélectionnée(s) · <b>${dxnReady().length} à créer</b>`;
  dxnSvg()}
// Schéma : géométries proposées (espace Objet, repère du DXF, Y vers le haut) et repères trouvés ; ligne sélectionnée en évidence
function dxnSvg(){const D=DXI,S=el('dxnV');if(!S)return;const G=new Set(),pts=[],R=[],k=D.nsel,a=k>=0?dxnAS(D.NL[k].L):null,on=new Set(a?a.options.map(o=>o.c):[]);
  D.NL.forEach(({L})=>{const x=dxnAS(L);x.options.slice(0,DXN_OPT).forEach(o=>G.add(o.c));x.reperes.forEach(p=>R.push([p,x===a]))});
  // cadrage : propositions et repères de la ligne sélectionnée s'il y en a, sinon tout
  const zG=on.size||(a&&a.reperes.length)?[...on]:[...G],zR=on.size||(a&&a.reperes.length)?R.filter(r=>r[1]):R;
  zG.forEach(i=>{const g=D.C[i].geometrie;if(g.type==='cercle')pts.push([g.centre[0]-g.r,g.centre[1]-g.r],[g.centre[0]+g.r,g.centre[1]+g.r]);else g.points.forEach(p=>pts.push(p))});
  zR.forEach(([p])=>pts.push([p.x,p.y]));
  if(!pts.length){S.removeAttribute('viewBox');S.innerHTML='<text x="50%" y="50%" text-anchor="middle" font-size="13">Aucune géométrie proposée</text>';return}
  const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),w=Math.max(x1-x0,1e-9),h=Math.max(y1-y0,1e-9),m=Math.max(w,h)*0.06,rr=Math.max(w,h)*0.008;
  S.setAttribute('viewBox',`${x0-m} ${-y1-m} ${w+2*m} ${h+2*m}`);const sel=k>=0?D.NR[k].geo:'';
  S.innerHTML=[...G].map(i=>{const c=D.C[i],g=c.geometrie,cl=`class="g${on.has(i)?' on':''}${String(i)===sel?' cf':''}" data-c="${i}"`+(on.has(i)?` onclick="dxnPick(${i})"`:''),t=`<title>${esc(c.id+' · '+c.source.calque+' · '+dxiDims(c))}</title>`;
    return g.type==='cercle'?`<circle ${cl} cx="${g.centre[0]}" cy="${-g.centre[1]}" r="${g.r}">${t}</circle>`:`<polygon ${cl} points="${g.points.map(p=>p[0]+','+(-p[1])).join(' ')}">${t}</polygon>`}).join('')
    +R.map(([p,o])=>`<circle class="rp${o?' on':''}" cx="${p.x}" cy="${-p.y}" r="${rr}"><title>repère ${esc(p.id)}</title></circle>`).join('')}
function dxnPick(i){const D=DXI;if(!D||D.nsel<0)return;const t=document.querySelector(`#dxnT tr[data-n="${D.nsel}"] [data-k=geo]`);dxnGeo(D.nsel,String(i));if(t)t.value=String(i)}

// ==== PDF : lecture, aperçu des pages, zone à analyser, saisie assistée (fonctions dxp*) ====
const dxnNR=L=>({conf:false,forme:'',cotes:'',cotesT:false,h:'',ref:String(L.repere||'').toUpperCase(),geo:'',geoT:false});
async function dxpFile(nom,b){if(el('dxiZ')){el('dxiN').innerHTML=`<b>${esc(nom)}</b> · lecture du PDF…`;el('dxiZ').innerHTML=''}
  const lu=await CPI.pdf.lire(b,nom);if(!lu.ok)return dxiErr(nom,lu);
  const v=CPI.lecteur.lirePlan({format:'normalise',nom,contenu:lu.document});if(!v.ok){CPI.pdf.fermer(lu.pdf);return dxiErr(nom,v)}
  dxiQuit();const doc=lu.document,cur=coll(),NA=CPI.nomenclatures.analyser(doc),NL=NA.nomenclatures.flatMap(N=>N.lignes.map(L=>({N,L})));
  DXI={fmt:'pdf',nom,doc,pdf:lu.pdf,C:[],R:[],lay:{},u:'',ch:cur.ch,ouv:cur.ouv,ind:'',hCom:'',sel:-1,M:null,NA,NL,NR:NL.map(({L})=>dxnNR(L)),NU:{},nsel:-1,
    vue:NL.length?'n':'p',lk:new Set(),page:NL.length?NL[0].N.page:1,zoom:1,zone:null,zm:false,hl:-1,nz:0,ns:0,tok:0,OC:null,ocJob:null,no:0,ohl:null};
  dxnAssoc();if(el('dxiZ'))dxiRender()}
// Nomenclature reconstruite (zone analysée, ligne saisie ou retirée) sans toucher à l'aperçu
function dxnRefresh(){const z=el('dxiPN');if(!z)return;const v=z.style.display;z.outerHTML=dxnPane();el('dxiPN').style.display=v;dxnRows();dxiHead()}
function dxpPane(){
  return `<div id="dxiPP" style="display:none"><div class="dxp"><div>
    <div class="dxp-b"><button class="btn bs bo" onclick="dxpGo(-1)" aria-label="Page précédente">◀</button><span id="dxpPg"></span><button class="btn bs bo" onclick="dxpGo(1)" aria-label="Page suivante">▶</button>
      <span style="width:10px"></span><button class="btn bs bo" onclick="dxpZoom(1/1.25)" aria-label="Zoom arrière">−</button><span id="dxpZ"></span><button class="btn bs bo" onclick="dxpZoom(1.25)" aria-label="Zoom avant">+</button>
      <button class="btn bs bo" onclick="dxpZoom(0)">Ajuster</button><span style="width:10px"></span><button class="btn bs bo" id="dxpZm" onclick="dxpZm()" aria-pressed="false">⬚ Sélectionner une zone</button></div>
    <div id="dxpW" style="margin-top:6px"><div id="dxpC"><canvas id="dxpCv"></canvas><svg id="dxpO" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tableaux reconnus et zone choisie"
      onpointerdown="dxpPd(event)" onpointermove="dxpPm(event)" onpointerup="dxpPu(event)"></svg></div></div>
    <div class="hint" style="margin:6px 0 0">Cadres verts en tirets : tableaux reconnus ; orange : ligne choisie ; bleu : zone. Pour choisir une zone : « Sélectionner une zone », puis cliquer-glisser sur la page.</div></div>
  <div class="dxp-s"><div id="dxpI"></div>
    <fieldset><legend>Zone du tableau</legend><div id="dxpZi" class="mu">Aucune zone choisie.</div>
      <div class="dxp-b" style="margin-top:6px"><button class="btn bs bo" id="dxpZa" onclick="dxpAnalyse()" disabled title="Textes extractibles du PDF : rapide, sans erreur de lecture">Analyser la zone</button>
      <button class="btn bs bo" id="dxpZo" onclick="dxoLancer()" disabled title="Reconnaissance visuelle locale (textes dessinés en tracés ou numérisés) : plus lente, à vérifier">Reconnaître le tableau (OCR)</button>
      <button class="btn bs bo" onclick="dxpZone(null)">Effacer la zone</button></div><div id="dxoP" style="margin-top:4px"></div><div id="dxpZr" style="margin-top:4px"></div></fieldset>
    <fieldset><legend>Saisie assistée</legend><div class="mu" style="margin-bottom:6px">Recopier une ligne du tableau visible sur la page (page affichée et zone choisie gardées dans la provenance). Rien n'est complété à votre place.</div>
      <div class="fd"><label for="dxpR">Repère</label><input class="fi" id="dxpR"></div><div class="fd"><label for="dxpD">Désignation</label><input class="fi" id="dxpD"></div>
      <div class="fd"><label for="dxpK">Cotes (mm) : l × h ou Ø</label><input class="fi" id="dxpK" placeholder="ex. 650x800 ou Ø250"></div>
      <div class="fd"><label for="dxpNv">Niveau (position, facultatif)</label><input class="fi" id="dxpNv"></div><div class="fd"><label for="dxpOb">Observations (facultatif)</label><input class="fi" id="dxpOb"></div>
      <button class="btn bs bpr" style="margin-top:6px" onclick="dxpAjout()">＋ Ajouter la ligne</button><div id="dxpSm" class="mu" style="margin-top:4px"></div></fieldset></div></div><div id="dxoG"></div></div>`}
// Rendu de la page affichée : échelle = largeur de la zone × zoom ; un rendu plus récent annule le précédent
async function dxpPage(){const D=DXI,cv=el('dxpCv'),W=el('dxpW');if(!D||!D.pdf||!cv||!W)return;const p=D.doc.pages[D.page-1],k=D.k=Math.max(0.05,(W.clientWidth-4)/p.w)*D.zoom,tok=++D.tok;
  el('dxpPg').textContent=` Page ${D.page} / ${D.doc.pages.length} `;el('dxpZ').textContent=` ${Math.round(D.zoom*100)} % `;
  el('dxpI').innerHTML=`<b>Page ${D.page}</b> : ${esc(CPI.pdf.LIB_NAT[p.nature]||p.nature)}<div class="mu">${p.textes} texte(s) lu(s), ${p.chemins} tracé(s), ${p.images} image(s)${p.rotation?` · page tournée de ${p.rotation}°`:''}${p.erreur?' · erreur : '+esc(p.erreur):''}</div>`;
  const O=el('dxpO');O.setAttribute('width',p.w*k);O.setAttribute('height',p.h*k);O.setAttribute('viewBox',`0 0 ${p.w} ${p.h}`);dxpZone(D.zone);
  if(D.rt)try{D.rt.promise.catch(()=>{});D.rt.cancel()}catch(e){}
  let t;try{t=await CPI.pdf.rendre(D.pdf,D.page,cv,k)}catch(e){return}
  if(tok!==D.tok){t.promise.catch(()=>{});t.cancel();return}D.rt=t;
  try{await t.promise}catch(e){if(!e||e.name!=='RenderingCancelledException')console.warn('Aperçu PDF :',e&&e.message)}
  if(tok===D.tok&&D.scroll){D.scroll=false;const h=O.querySelector('.hl');if(h)h.scrollIntoView({block:'center',inline:'center'})}}
function dxpGo(d){const D=DXI;if(!D)return;const n=Math.min(D.doc.pages.length,Math.max(1,D.page+d));if(n!==D.page){D.page=n;dxpPage()}}
function dxpZoom(f){const D=DXI;if(!D)return;D.zoom=f?Math.min(8,Math.max(0.25,D.zoom*f)):1;dxpPage()}
// Encadré d'une ligne : ses textes sources (lecture automatique) ou la zone de sa saisie
function dxpBox({N,L}){const D=DXI;if(L.box)return L.box;if(L.zone)return L.zone;if(!L.ids.length)return null;
  if(!D.tid)D.tid=new Map(D.doc.textes.map(t=>[t.id,t]));const T=L.ids.map(i=>D.tid.get(i)).filter(Boolean);if(!T.length)return null;const m=Math.max(...T.map(t=>t.h));
  return{page:N.page,x0:Math.min(...T.map(t=>t.x-t.w/2))-m,x1:Math.max(...T.map(t=>t.x+t.w/2))+m,y0:Math.min(...T.map(t=>t.y-t.h/2))-m,y1:Math.max(...T.map(t=>t.y+t.h/2))+m}}
function dxpOver(){const D=DXI,O=el('dxpO');if(!D||!O)return;const p=D.doc.pages[D.page-1],H=p.h,f=Math.max(6,p.w/90),
    r=(x0,y0,x1,y1,c)=>`<rect class="${c}" x="${Math.min(x0,x1)}" y="${H-Math.max(y0,y1)}" width="${Math.abs(x1-x0)}" height="${Math.abs(y1-y0)}"/>`;
  let h=D.NA.nomenclatures.filter(N=>N.page===D.page&&N.cadre&&!N.saisie).map(N=>r(N.cadre[0]-3,N.cadre[1]-3,N.cadre[2]+3,N.cadre[3]+3,'tb')+`<text x="${N.cadre[0]}" y="${H-N.cadre[3]-2}" font-size="${f}">${esc(N.id)}</text>`).join('');
  const b=D.hl>=0&&D.NL[D.hl]?dxpBox(D.NL[D.hl]):null;if(b&&b.page===D.page)h+=r(b.x0,b.y0,b.x1,b.y1,'hl');
  const z=D.zone;if(z&&z.page===D.page)h+=r(z.x0,z.y0,z.x1,z.y1,'zn');
  // OCR : cellules incertaines de la grille (tirets orange), cellule choisie (orange plein)
  if(D.OC&&D.OC.page===D.page)D.OC.rows.forEach(w=>Object.keys(w.box).forEach(k=>{const b=w.box[k];if(b&&w.doute[k]&&!w.edite.includes(k))h+=r(b.x0,b.y0,b.x1,b.y1,'od')}));
  const o=D.ohl;if(o&&o.page===D.page)h+=r(o.x0-1,o.y0-1,o.x1+1,o.y1+1,'hl');
  O.innerHTML=h}
function dxpVoir(k){const D=DXI;if(!D||!D.NL[k])return;D.hl=k;D.page=D.NL[k].N.page||1;D.scroll=true;dxnSel(k);dxiVue('p')}
// Zone : cliquer-glisser en mode « Sélectionner une zone » ; coordonnées en points PDF, Y vers le haut, comme les textes lus
function dxpZm(on){const D=DXI;if(!D)return;D.zm=on==null?!D.zm:on;el('dxpO').classList.toggle('zm',D.zm);el('dxpZm').setAttribute('aria-pressed',D.zm);el('dxpZm').classList.toggle('bpr',D.zm)}
function dxpPt(e){const D=DXI,b=el('dxpO').getBoundingClientRect(),p=D.doc.pages[D.page-1];return[Math.min(p.w,Math.max(0,(e.clientX-b.left)/D.k)),Math.min(p.h,Math.max(0,p.h-(e.clientY-b.top)/D.k))]}
function dxpPd(e){const D=DXI;if(!D||!D.zm)return;e.preventDefault();try{e.target.setPointerCapture(e.pointerId)}catch(x){}const a=dxpPt(e);D.zd=a;D.zone={page:D.page,x0:a[0],y0:a[1],x1:a[0],y1:a[1],unite:'pt'};dxpOver()}
function dxpPm(e){const D=DXI;if(!D||!D.zd)return;const a=dxpPt(e);Object.assign(D.zone,{x1:a[0],y1:a[1]});dxpOver()}
function dxpPu(e){const D=DXI;if(!D||!D.zd)return;D.zd=null;const z=D.zone,r=x=>Math.round(x*10)/10;
  dxpZone(Math.abs(z.x1-z.x0)<4||Math.abs(z.y1-z.y0)<4?null:{page:z.page,x0:r(Math.min(z.x0,z.x1)),y0:r(Math.min(z.y0,z.y1)),x1:r(Math.max(z.x0,z.x1)),y1:r(Math.max(z.y0,z.y1)),unite:'pt'});dxpZm(false)}
const dxpDans=(z,x,y)=>x>=z.x0&&x<=z.x1&&y>=z.y0&&y<=z.y1;
function dxpZone(z){const D=DXI;if(!D)return;D.zone=z;if(!el('dxpZi'))return;
  el('dxpZi').innerHTML=z?`Page ${z.page} : ${Math.round(z.x1-z.x0)} × ${Math.round(z.y1-z.y0)} pt · ${D.doc.textes.filter(t=>t.page===z.page&&dxpDans(z,t.x,t.y)).length} texte(s) dans la zone`:'Aucune zone choisie.';
  el('dxpZa').disabled=!z;el('dxpZo').disabled=!z||!!D.ocJob;if(!z)el('dxpZr').textContent='';dxpOver()}
// Analyse d'une zone : textes et traits de la zone seulement (traits coupés au bord) ; les tableaux lus automatiquement qui
// partagent des textes avec la zone sont remplacés par cette lecture ; rien n'est ajouté si aucune nomenclature n'y est reconnue
function dxpZoneTS(z){const D=DXI,cl=(v,a,b)=>Math.min(b,Math.max(a,v)),T=D.doc.textes.filter(t=>t.page===z.page&&dxpDans(z,t.x,t.y)),
    S=D.doc.traits.filter(s=>s.page===z.page&&Math.max(s.a[0],s.b[0])>=z.x0&&Math.min(s.a[0],s.b[0])<=z.x1&&Math.max(s.a[1],s.b[1])>=z.y0&&Math.min(s.a[1],s.b[1])<=z.y1)
      .map(s=>Object.assign({},s,{a:[cl(s.a[0],z.x0,z.x1),cl(s.a[1],z.y0,z.y1)],b:[cl(s.b[0],z.x0,z.x1),cl(s.b[1],z.y0,z.y1)]}));
  return{T,S,A:CPI.nomenclatures.analyser({fichier:D.doc.fichier,format:'pdf',textes:T,traits:S,signalements:[]})}}
function dxpAnalyse(){const D=DXI,z=D&&D.zone;if(!z)return;const msg=el('dxpZr'),{T,A}=dxpZoneTS(z);
  if(!A.nomenclatures.length){msg.innerHTML=T.length?`Aucune nomenclature de réservations reconnue dans la zone (${T.length} texte(s) lu(s)${A.ecartes.length?' ; écarté : '+esc(A.ecartes.map(e=>e.raison).join(' ; ')):''}). Rien n'est ajouté : essayer « Reconnaître le tableau (OCR) » ou saisir les lignes ci-dessous.`
    :'La zone ne contient aucun texte extractible (tableau probablement dessiné en tracés ou numérisé). Rien n\'est ajouté : utiliser « Reconnaître le tableau (OCR) » ou saisir les lignes ci-dessous.';return}
  const ids=new Set(T.map(t=>t.id)),vieux=new Set(D.NA.nomenclatures.filter(N=>!N.saisie&&!N.ocr&&N.page===z.page&&N.ids.some(i=>ids.has(i)))),
    keep=D.NL.map((x,k)=>vieux.has(x.N)?-1:k).filter(k=>k>=0);
  A.nomenclatures.forEach(N=>{const id='Z'+(++D.nz);N.lignes.forEach(L=>L.id=L.id.replace(/^N\d+/,id));N.id=id;N.zone=Object.assign({},z)});
  const NL2=A.nomenclatures.flatMap(N=>N.lignes.map(L=>({N,L})));
  D.NL=keep.map(k=>D.NL[k]).concat(NL2);D.NR=keep.map(k=>D.NR[k]).concat(NL2.map(({L})=>dxnNR(L)));
  D.NA.nomenclatures=D.NA.nomenclatures.filter(N=>!vieux.has(N)).concat(A.nomenclatures);D.hl=-1;D.nsel=-1;
  dxnAssoc();dxnRefresh();dxpOver();
  msg.innerHTML=`✓ ${NL2.length} ligne(s) lue(s) dans ${A.nomenclatures.length} tableau(x) de la zone`+(vieux.size?` (remplace la lecture automatique de ${[...vieux].map(N=>esc(N.id)).join(', ')})`:'')+' : voir l\'onglet Nomenclature.'}
// Saisie assistée : une ligne recopiée par l'utilisateur, rangée avec les lignes lues (mêmes contrôles, même création)
function dxpAjout(){const D=DXI;if(!D)return;const v=id=>el(id).value.trim(),rep=v('dxpR'),des=v('dxpD'),ct=v('dxpK'),niv=v('dxpNv'),obs=v('dxpOb'),m=el('dxpSm');
  if(!rep&&!ct){m.textContent='Saisir au moins le repère ou les cotes.';return}
  const n=D.page;let N=D.NA.nomenclatures.find(x=>x.saisie&&x.page===n);
  if(!N){N={id:'S'+n,saisie:true,fichier:D.doc.fichier,format:'pdf',espace:'papier',presentation:'Page '+n,page:n,titre:'Saisie assistée',nature:'reservations',
      colonnes:[['Repère','repere'],['Désignation','description'],['Cotes (mm)','ouverture'],['Niveau','niveau'],['Observations','observations']].map(([titre,cle])=>({titre,cle,unite:cle==='ouverture'?'mm':null})),
      cadre:null,ids:[],calques:[],lignes:[],unite:'mm',qualite:{niveau:'saisie',motifs:['lignes recopiées par l\'utilisateur en consultant le PDF']}};D.NA.nomenclatures.push(N)}
  const c=CPI.nomenclatures.cotes(ct,'mm',true),av=[],dims=c.etat==='rect'?{type:'rect',a:c.a,b:c.b,unite:c.unite||'mm',texte:ct,colonne:'Cotes (mm)'}
    :c.etat==='circ'?{type:'circ',D:c.D,unite:c.unite||'mm',texte:ct,colonne:'Cotes (mm)'}:null;
  if(!dims)av.push(!ct?'cotes non saisies':c.etat==='dn'?'DN du réseau : diamètre de la réservation à saisir':`cotes « ${ct} » non lues (ex. 650x800 ou Ø250)`);
  const rang=++D.ns,L={id:`S${n}-L${String(rang).padStart(2,'0')}`,rang,ids:[],calques:[],cellules:[rep,des,ct,niv,obs],repere:rep,description:des,type:'',observations:obs,lot:'',quantite:'',
    niveau:niv,angle:'',reseau:'',ouverture:ct,dims,a_verifier:av,zone:D.zone&&D.zone.page===n?Object.assign({},D.zone):null};
  N.lignes.push(L);D.NL.push({N,L});D.NR.push(dxnNR(L));dxnAssoc();dxnRefresh();
  ['dxpR','dxpD','dxpK','dxpNv','dxpOb'].forEach(i=>el(i).value='');el('dxpR').focus();
  m.textContent=`✓ ligne ${rep||'(sans repère)'} ajoutée (page ${n}) : hauteur à saisir puis ligne à cocher dans l'onglet Nomenclature.`}
function dxpSuppr(k){const D=DXI,x=D&&D.NL[k];if(!x||!x.N.saisie)return;const N=x.N;N.lignes=N.lignes.filter(L=>L!==x.L);if(!N.lignes.length)D.NA.nomenclatures=D.NA.nomenclatures.filter(y=>y!==N);
  D.NL.splice(k,1);D.NR.splice(k,1);D.hl=-1;D.nsel=-1;dxnRefresh();dxpOver()}

// ==== OCR d'une zone (ocr.js, fonctions dxo*) : reconnaissance, grille de vérification, ajout à la nomenclature ====
const dxoCle=w=>CPI.nomenclatures.cleRep(w.cells.repere||'');
const dxoChevauche=(a,b)=>a&&b&&a.page===b.page&&a.x0<b.x1&&b.x0<a.x1&&a.y0<b.y1&&b.y0<a.y1;
function dxoProg(t,f){const z=el('dxoP');if(!z)return;
  z.innerHTML=t==null?'':`<div class="mu">${esc(t)}</div><div style="display:flex;gap:6px;align-items:center"><progress max="1"${f!=null?` value="${Math.max(0,Math.min(1,f))}"`:''}></progress>
    <button class="btn bs bo" onclick="dxoStop()">Annuler</button></div>`}
// Lancement : demande confirmation si la zone est déjà lisible par le texte du PDF (inutile de lancer un traitement lourd)
function dxoLancer(force){const D=DXI,z=D&&D.zone;if(!z||D.ocJob)return;
  if(!force){const N=dxpZoneTS(z).A.nomenclatures.find(N=>N.qualite.niveau==='bonne'&&N.lignes.length);
    if(N)return uiConfirm(`Cette zone contient un tableau déjà lisible par le texte du PDF (${N.lignes.length} ligne(s), lecture « bonne ») : « Analyser la zone » suffit, sans erreur de lecture possible. Lancer quand même la reconnaissance optique ?`,()=>dxoLancer(true),{ok:'Lancer l\'OCR'})}
  const job={z:Object.assign({},z),stop:false,run:'o'+(++D.no),t0:Date.now()};D.ocJob=job;el('dxpZo').disabled=true;el('dxpZr').textContent='';
  dxoProg('Démarrage du moteur de reconnaissance (intégré au fichier, hors connexion)',null);
  const ici=()=>DXI===D&&D.ocJob===job;
  CPI.ocr.lireZone(D.pdf,job.z,{run:job.run,annule:()=>job.stop,progres:(t,f)=>{if(ici())dxoProg(t,f)}})
    .then(r=>{if(!ici())return;D.ocJob=null;dxoProg(null);dxpZone(D.zone);dxoResultat(job,r)})
    .catch(e=>{if(!ici())return;D.ocJob=null;dxoProg(null);dxpZone(D.zone);el('dxpZr').innerHTML=`⛔ Reconnaissance impossible : ${esc(String(e&&e.message||e))}. Rien n'a été modifié.`})}
// Annulation : le moteur est arrêté aussitôt (il sera relancé au prochain OCR) ; rien n'est modifié
function dxoStop(){const D=DXI;if(!D||!D.ocJob)return;D.ocJob.stop=true;D.ocJob=null;CPI.ocr.arreter();dxoProg(null);dxpZone(D.zone);
  el('dxpZr').textContent='Reconnaissance annulée : rien n\'a été modifié.'}
// Résultat : tableau(x) reconstruit(s) par nomenclatures.analyser sur les textes OCR → grille ; une grille déjà corrigée sur la
// même zone garde les corrections de l'utilisateur (cellules modifiées, lignes ajoutées, lignes retirées)
function dxoResultat(job,r){const D=DXI,z=job.z,A=CPI.nomenclatures.analyser({fichier:D.doc.fichier,format:'pdf',textes:r.textes,traits:r.traits,signalements:[]}),msg=el('dxpZr');
  const rows=A.nomenclatures.flatMap(N=>CPI.ocr.grille(N,r.textes)),p=r.mesures.passes[r.mesures.retenue-1],s=Math.round(r.mesures.ms/100)/10;
  rows.forEach(w=>Object.keys(w.cells).forEach(k=>{w.cells[k]=String(w.cells[k]).replace(/\n/g,' ')}));
  const E=A.ecartes.map(e=>`${e.titre?'« '+e.titre.replace(/\n/g,' ')+' » ':''}${e.raison}`);
  if(!rows.length){msg.innerHTML=`Reconnaissance terminée (${s} s, ${r.textes.length} texte(s) lu(s)) : <b>aucune nomenclature de réservations reconnue</b> dans la zone${E.length?' ; écarté : '+esc(E.join(' ; ')):''}. Rien n'est ajouté.
    <details class="mu"><summary>Textes reconnus</summary>${esc(r.textes.map(t=>t.texte).join(' · '))}</details>`;return}
  const O=D.OC&&dxoChevauche(D.OC.zone,z)?D.OC:null;let gard=0;
  if(O){rows.forEach(w=>{const o=O.rows.find(o=>o.edite.length&&o.src&&o.cle0&&o.cle0===w.cle0);if(o){o.edite.forEach(k=>{w.cells[k]=o.cells[k]});w.edite=o.edite.slice();w.notes=(o.notes||[]).slice();gard++}});
    O.rows.filter(o=>!o.src).forEach(o=>rows.push(o))}
  const sup=O?O.suppr:[],R2=rows.filter(w=>!sup.some(x=>x.w.src&&x.w.cle0&&x.w.cle0===w.cle0));
  D.OC={page:z.page,zone:z,mesures:r.mesures,titre:A.nomenclatures.map(N=>N.titre).filter(Boolean).join(' · '),unite:(A.nomenclatures.find(N=>N.unite)||{}).unite||'',
    uniteLue:(A.nomenclatures.find(N=>N.unite)||{}).unite||'',rows:R2,suppr:sup,ecartes:E,nT:r.textes.length,sel:-1};
  const nd=R2.reduce((n,w)=>n+Object.keys(w.doute).filter(k=>w.doute[k]&&!w.edite.includes(k)).length,0);
  msg.innerHTML=`✓ ${R2.length} ligne(s) reconnue(s) en ${s} s (${p.dpi} dpi) · <b>${nd} cellule(s) incertaine(s)</b> à vérifier dans la grille ci-dessous`
    +(gard?` · corrections gardées sur ${gard} ligne(s)`:'')+(sup.length?` · ${sup.length} ligne(s) retirée(s) laissée(s) de côté`:'')+(E.length?` · écarté : ${esc(E.join(' ; '))}`:'');
  D.ohl=null;dxoGrille();dxpOver()}
// Grille de vérification : toutes les cellules modifiables ; incertaines en orange (survol : texte brut et confiance) ;
// une cellule choisie est encadrée sur l'aperçu de la page
function dxoGrille(){const D=DXI,G=el('dxoG');if(!G||!D)return;const O=D.OC;if(!O){G.innerHTML='';return}
  const C=CPI.ocr.colonnes(O.rows),lg=k=>k==='description'||k==='observations'||k==='autre';
  const tip=(w,k)=>[w.brut[k]?`OCR brut : « ${w.brut[k]} »`:'',w.conf[k]!=null?`confiance ${w.conf[k]} %`:'',...(w.corr[k]||[]),w.edite.includes(k)?'corrigé par vous':''].filter(Boolean).join('\n');
  G.innerHTML=`<fieldset class="dxo"><legend>Vérification de la reconnaissance (OCR) · page ${O.page}${O.titre?' · « '+esc(O.titre.replace(/\n/g,' '))+' »':''}</legend>
    <div class="mu" style="margin-bottom:6px">Chaque cellule est modifiable. <span style="color:var(--acct)">Orange</span> : lecture incertaine ou corrigée automatiquement (survol : texte brut,
    confiance) ; cliquer une cellule l'encadre sur la page. Ligne en trop : ✕ ; ligne coupée en deux : ⇣ (fusion avec la suivante) ; ligne manquante : ＋. Rien n'est coché pour la création.</div>
    <div class="dxp-b" style="margin-bottom:6px">Unité des dimensions : <select class="fi" id="dxoU" style="width:auto" onchange="DXI.OC.unite=this.value">${['','mm','cm','m'].map(u=>`<option value="${u}"${O.unite===u?' selected':''}>${u||'— à choisir —'}</option>`).join('')}</select>
      <span class="mu">${O.uniteLue?`lue dans l'en-tête : ${esc(O.uniteLue)}`:'non indiquée par le tableau'}</span></div>
    <div class="dxi-t"><table class="ser" id="dxoT"><thead><tr><th>#</th>${C.map(([k,t])=>`<th>${esc(t)}</th>`).join('')}<th>État</th><th></th></tr></thead><tbody>
    ${O.rows.map((w,i)=>`<tr data-o="${i}"${O.sel===i?' class="on"':''}><td>${i+1}</td>${C.map(([k])=>{const v=esc(w.cells[k]||''),c=`fi${w.doute[k]&&!w.edite.includes(k)?' dt':''}${w.edite.includes(k)?' ed':''}`,
        a=`data-k="${k}" title="${esc(tip(w,k))}" aria-label="${esc(k+' ligne '+(i+1))}" oninput="dxoSet(${i},'${k}',this)" onfocus="dxoVoir(${i},'${k}')"`;
        return `<td>${lg(k)?`<textarea class="${c}" rows="1" ${a}>${v}</textarea>`:`<input class="${c}" value="${v}" ${a}>`}</td>`}).join('')}
      <td class="st">${dxoEtat(w)}</td><td class="ac"><button class="btn bs bo" title="Insérer une ligne vide après" aria-label="Insérer une ligne" onclick="dxoAjout(${i})">＋</button><button class="btn bs bo" title="Fusionner avec la ligne suivante" aria-label="Fusionner avec la suivante" onclick="dxoFusion(${i})"${i+1<O.rows.length?'':' disabled'}>⇣</button><button class="btn bs bo" title="Retirer cette ligne" aria-label="Retirer la ligne" onclick="dxoSuppr(${i})">✕</button></td></tr>`).join('')}
    </tbody></table></div>
    <div class="dxp-b" style="margin-top:6px"><button class="btn bs bo" onclick="dxoAjout(-1)">＋ Ajouter une ligne</button>${O.suppr.length?`<button class="btn bs bo" onclick="dxoRetablir()">Rétablir les ${O.suppr.length} ligne(s) retirée(s)</button>`:''}
      <button class="btn bs bpr" id="dxoV" onclick="dxoValider()">Ajouter à la nomenclature (${O.rows.length} ligne(s))</button><button class="btn bs bo" onclick="dxoFermer()">Fermer la grille</button></div><div id="dxoR" class="mu" style="margin-top:4px"></div></fieldset>`}
function dxoEtat(w){const n=Object.keys(w.doute).filter(k=>w.doute[k]&&!w.edite.includes(k)).length,c=w.edite.length;
  return [!w.src?'＋ ajoutée':'',!String(w.cells.repere||'').trim()?'<span style="color:var(--redt)">repère absent</span>':'',n?`<span style="color:var(--acct)">⚠ ${n} incertaine(s)</span>`:'',c?`✎ ${c} corrigée(s)`:'',(w.notes||[]).length?esc(w.notes.join(' · ')):'',
    w.src&&!n&&!c?'✓ lue':''].filter(Boolean).join('<br>')}
function dxoSet(i,k,e){const w=DXI.OC.rows[i];w.cells[k]=e.value;if(!w.edite.includes(k))w.edite.push(k);e.classList.remove('dt');e.classList.add('ed');
  const t=e.closest('tr').querySelector('.st');if(t)t.innerHTML=dxoEtat(w);dxpOver()}
function dxoVoir(i,k){const D=DXI,O=D.OC,w=O.rows[i];O.sel=i;document.querySelectorAll('#dxoT tr[data-o]').forEach(t=>t.classList.toggle('on',+t.dataset.o===i));
  const B=Object.values(w.box).filter(Boolean),b=w.box[k]||(B.length?{page:O.page,x0:Math.min(...B.map(b=>b.x0)),y0:Math.min(...B.map(b=>b.y0)),x1:Math.max(...B.map(b=>b.x1)),y1:Math.max(...B.map(b=>b.y1))}:null);
  D.ohl=b;if(!b)return dxpOver();if(D.page!==b.page){D.page=b.page;dxpPage()}else dxpOver();
  const h=el('dxpO')&&el('dxpO').querySelectorAll('.hl');if(h&&h.length)h[h.length-1].scrollIntoView({block:'nearest',inline:'nearest'})}
const dxoVide=()=>({cells:{},brut:{},conf:{},corr:{},doute:{},box:{},edite:[],src:null,notes:[]});
function dxoAjout(i){const O=DXI.OC;O.rows.splice(i<0?O.rows.length:i+1,0,dxoVide());dxoGrille();const r=el('dxoT').querySelector(`tr[data-o="${i<0?O.rows.length-1:i+1}"] .fi`);if(r)r.focus()}
function dxoFusion(i){const O=DXI.OC,a=O.rows[i],b=O.rows[i+1];if(!b)return;
  new Set(Object.keys(a.cells).concat(Object.keys(b.cells))).forEach(k=>{const v=[a.cells[k],b.cells[k]].filter(x=>String(x||'').trim());a.cells[k]=v.join(' ');
    a.brut[k]=[a.brut[k],b.brut[k]].filter(Boolean).join(' ');a.conf[k]=[a.conf[k],b.conf[k]].filter(x=>x!=null).reduce((m,x)=>Math.min(m,x),Infinity);if(a.conf[k]===Infinity)a.conf[k]=null;
    a.corr[k]=(a.corr[k]||[]).concat(b.corr[k]||[]);a.doute[k]=!!(a.doute[k]||b.doute[k]);
    const B=[a.box[k],b.box[k]].filter(Boolean);a.box[k]=B.length?{page:B[0].page,x0:Math.min(...B.map(x=>x.x0)),y0:Math.min(...B.map(x=>x.y0)),x1:Math.max(...B.map(x=>x.x1)),y1:Math.max(...B.map(x=>x.y1))}:null;
    if(b.edite.includes(k)&&!a.edite.includes(k))a.edite.push(k)});
  a.src=a.src||b.src;a.notes=(a.notes||[]).concat(b.notes||[],['deux lignes reconnues fusionnées']);O.rows.splice(i+1,1);dxoGrille();dxpOver()}
function dxoSuppr(i){const O=DXI.OC;O.suppr.push({w:O.rows[i],i});O.rows.splice(i,1);O.sel=-1;DXI.ohl=null;dxoGrille();dxpOver()}
function dxoRetablir(){const O=DXI.OC;O.suppr.sort((a,b)=>a.i-b.i).forEach(x=>O.rows.splice(Math.min(x.i,O.rows.length),0,x.w));O.suppr=[];dxoGrille();dxpOver()}
function dxoFermer(){const D=DXI;D.OC=null;D.ohl=null;dxoGrille();dxpOver()}
// Ajout à la nomenclature : lignes vérifiées → nomenclature OCR (même contrat, mêmes contrôles, aucune ligne cochée) ; une ligne dont
// le repère est déjà lu par le texte du PDF (ou saisi) sur la page n'est pas ajoutée ; un nouvel ajout depuis la même zone remplace
// le précédent en gardant les choix déjà faits dans l'onglet Nomenclature (forme, cotes, hauteur, référence, case cochée)
function dxoValider(){const D=DXI,O=D&&D.OC;if(!O)return;const R=el('dxoR'),cle=CPI.nomenclatures.cleRep;
  const deja=new Set(D.NL.filter(x=>!x.N.ocr&&x.N.page===O.page&&x.L.repere).map(x=>cle(x.L.repere)));
  const rows=O.rows.filter(w=>!(dxoCle(w)&&deja.has(dxoCle(w)))),dbl=O.rows.length-rows.length;
  if(!rows.length){R.textContent=dbl?`Toutes les lignes (${dbl}) sont déjà dans la nomenclature (lecture du texte ou saisie) : rien n'est ajouté.`:'Aucune ligne à ajouter.';return}
  const vieux=new Set(D.NA.nomenclatures.filter(N=>N.ocr&&dxoChevauche(N.zone,O.zone))),old=new Map();
  D.NL.forEach((x,k)=>{if(vieux.has(x.N)&&x.L.repere)old.set(cle(x.L.repere),D.NR[k])});
  const N=CPI.ocr.versNomenclature(rows,{id:'O'+(++D.nz),fichier:D.doc.fichier,page:O.page,zone:O.zone,titre:O.titre,unite:O.unite,mesures:O.mesures});
  const keep=D.NL.map((x,k)=>vieux.has(x.N)?-1:k).filter(k=>k>=0),NL2=N.lignes.map(L=>({N,L}));
  D.NL=keep.map(k=>D.NL[k]).concat(NL2);D.NR=keep.map(k=>D.NR[k]).concat(NL2.map(({L})=>{const o=L.repere&&old.get(cle(L.repere));return o?Object.assign(o,{x:null}):dxnNR(L)}));
  D.NA.nomenclatures=D.NA.nomenclatures.filter(N=>!vieux.has(N)).concat([N]);D.hl=-1;D.nsel=-1;
  dxnAssoc();dxnRefresh();dxpOver();
  R.innerHTML=`✓ ${rows.length} ligne(s) ajoutée(s) à la nomenclature (tableau ${esc(N.id)})`+(vieux.size?`, en remplacement de l'ajout précédent depuis cette zone`:'')
    +(dbl?` · ${dbl} ligne(s) déjà lue(s) par le texte du PDF ou saisie(s), non ajoutée(s)`:'')+` : hauteur et sélection dans l'onglet <a href="#" onclick="dxiVue('n');return false">Nomenclature</a>.`}

