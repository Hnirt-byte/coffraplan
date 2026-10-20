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
// Repérage sur le dessin d'un PDF (geometrie.js, fonctions dxr*) : rectangles et cercles de la page ou de la zone, superposés à
// l'aperçu ; cotes en mm par une échelle choisie par l'utilisateur (2 points et une distance, ou échelle écrite sur la page) ou
// par une cote écrite à côté du contour ; rattachement aux lignes de nomenclature ; même création, rien de coché d'office.
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
#dxpO .rs{fill:rgba(123,77,255,.10);stroke:#7b4dff;stroke-width:1.5px;vector-effect:non-scaling-stroke;cursor:pointer}
#dxpO .rs.cf{stroke:var(--okt);fill:rgba(46,204,113,.22)}#dxpO .rs.on{stroke:var(--accent);stroke-width:3px;fill:rgba(232,130,12,.30)}
#dxpO .rs.lk{stroke:var(--okt);stroke-dasharray:4 2;fill:none;cursor:default}#dxpO .rs.pr{stroke:var(--accent);stroke-dasharray:5 2;stroke-width:2.5px}
#dxpO .rl{fill:#7b4dff;pointer-events:none}#dxpO .ca{fill:var(--redt)}#dxpO .cl{stroke:var(--redt);stroke-width:1.5px;vector-effect:non-scaling-stroke}#dxpO.cm{cursor:crosshair}
#dxpO .vu{fill:none;stroke:#1f77b4;stroke-width:1.2px;vector-effect:non-scaling-stroke;stroke-dasharray:8 4;pointer-events:none}#dxpO .vl{fill:#1f77b4;pointer-events:none}
#dxpO .oc{fill:rgba(232,130,12,.12);stroke:var(--accent);stroke-width:1.5px;vector-effect:non-scaling-stroke;stroke-dasharray:3 2}#dxpO .ot{stroke:var(--accent);stroke-width:1.2px;vector-effect:non-scaling-stroke;stroke-dasharray:4 3}
#dxnT .rp{font-size:11px;margin-top:3px;line-height:1.35}#dxnT .rp .btn{padding:1px 5px;font-size:11px;margin:1px 2px 1px 0}#dxnT .cc-forte{color:var(--okt)}#dxnT .cc-partielle{color:var(--okt)}
#dxnT .cc-probable,#dxnT .cc-conflit{color:var(--acct)}#dxnT .cc-conflit{font-weight:600}#dxnT .cc-absente,#dxnT .cc-rejete{color:var(--muted)}
#dxrT tr{cursor:pointer}#dxrT tr.on td{background:rgba(232,130,12,.16)}#dxrT .fi{padding:3px 5px;font-size:12px;min-width:0}#dxrT th{position:sticky;top:0;background:var(--surface);z-index:1}
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
const dxiVis=i=>(DXI.fmt==='pdf'||DXI.lay[DXI.C[i].source.calque])&&!(DXI.lk&&DXI.lk.has(i));   // géométrie rattachée à une ligne de nomenclature : dans l'autre vue
function dxiDef(c){if(c.type==='circ')return 'circ';const k=DXI_MM[DXI.u];return (k?(c.dims.L-c.dims.l)*k<0.5:c.dims.L-c.dims.l<=1e-6*c.dims.L)?'carre':'rect'}
function dxiFormes(c){return c.type==='circ'?['circ']:dxiDef(c)==='carre'?['carre','carre_fond']:['rect','rect_fond']}
function dxiDims(c){const pdf=DXI.fmt==='pdf',k=pdf?dxrK(c):DXI_MM[DXI.u],v=x=>dxiNum(k?x*k:x),u=k?'':pdf?' pt (échelle ?)':' (unité ?)';
  return (c.type==='circ'?'Ø '+v(c.dims.D)+u:v(c.dims.L)+' × '+v(c.dims.l)+u)+(c.dims.angle?' · '+dxiNum(c.dims.angle)+'°':'')}

// État de chaque ligne : np (non pris en charge) · ac (à compléter) · er (refusé) · wn / ok (prêt) ; x = sortie de versPlan
function dxiEval(){const D=DXI;if(!D.M)dxiModels();const hc=parseCote(D.hCom,'mm'),moteur={migr,canon,limErr,checks,badDims};
  D.R.forEach((r,i)=>{const c=D.C[i];r.x=null;
    if(D.fmt==='pdf'&&c.statut==='a_confirmer')return dxrEval(r,i,hc,moteur);
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
  dxnUpd();if(D.fmt==='pdf')dxrUpd();dxiParams();dxiBtn()}
// Rappel des réglages repris du formulaire / du profil du chantier pour les formes à créer
function dxiParams(){const D=DXI,z=el('dxiP');if(!z||!D.M)return;const F=[...new Set(dxiReady().map(i=>D.R[i].x.plan.forme).concat(dxnReady().map(k=>D.NR[k].x.plan.forme)))];
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
const DXN_CC={forte:'✓✓ concordance forte',partielle:'✓ concordance partielle',probable:'≈ correspondance probable',conflit:'⚠ conflit à examiner',absente:'∅ non retrouvée sur le dessin',rejete:'✕ rapprochement rejeté'};
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
  // PDF : seulement après « Analyser le dessin » (contours de la page, cotes comparées si la page a une échelle)
  // PDF : seulement après « Analyser le dessin » : rapprochement multi-indices (rapprochement.js), toutes pages
  const ex=D.NA.ecartes.flatMap(e=>e.ids);
  if(D.fmt==='pdf'){D.AS={};D.HR=[];if(D.ana){const RP=CPI.rapprochement.rapprocher(D.NL.map(({N,L})=>({id:L.id,repere:L.repere,dims:L.dims,unite:dxnU(N,L)||null,quantite:L.quantite,page:N.page})),
      dxrTextes(),D.C,{mm:dxrK,rappels:dxrRappels,vue:dxrVue,exclus:new Set(ex.concat(D.NA.nomenclatures.flatMap(N=>N.ids)))});D.AS=RP.lignes;D.HR=RP.hors;D.ana.colonnes=RP.colonnes;
      // occurrences physiques : quantité du tableau = référence, vues comptées une fois
      D.CS={};D.NL.forEach(({L})=>D.CS[L.id]=CPI.vues.consolider(L,D.AS[L.id],dxrVues()))}}
  else D.AS=CPI.nomenclatures.associer(D.NA.nomenclatures,D.C,D.doc,{uniteDessin:D.u,unites:D.NU,exclus:ex});
  D.NL.forEach(({L},k)=>{const r=D.NR[k],a=dxnAS(L);if(!r.cotesT)r.cotes=dxnPre(k);if(!r.geoT)r.geo=a.statut==='trouvee'&&!r.rej?String(a.principal!=null?a.principal:a.options[0].c):''});dxnLinks()}
const DXN_AS0={statut:'absente',options:[],reperes:[],note:''};
const dxnAS=L=>DXI.AS&&DXI.AS[L.id]||DXN_AS0;   // ligne saisie ou ajoutée après le rapprochement : aucune géométrie
// Contours rattachés : celui choisi pour chaque ligne et toutes les vues désignées par son repère (preuves d'une même entrée :
// pas de doublon dans « hors nomenclature ») ; sauf ligne au rapprochement rejeté ou sans contour choisi par l'utilisateur
function dxnLinks(){const D=DXI;D.lk=new Set(D.NR.filter(r=>r.geo!=='').map(r=>+r.geo));
  if(D.fmt==='pdf')D.NL.forEach(({L},k)=>{const r=D.NR[k];if(r.rej||r.geoT&&r.geo==='')return;(dxnAS(L).preuves||[]).forEach(i=>D.lk.add(i))})}
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
    <div class="dxi-t"><table class="ser" id="dxnT"><thead><tr><th>Créer</th><th>Repère</th><th>Désignation</th><th>Ouverture · réseau</th><th>Niveau · angle</th><th>Forme</th><th>Cotes (mm)</th><th title="Nombre d'ouvrages identiques (nb) : quantité du tableau par défaut">Nb</th><th>h (mm)</th><th>Réf.</th><th>${pdf?'Source':'Géométrie du dessin'}</th><th>Statut</th></tr></thead><tbody></tbody></table></div>
    ${pdf?`<div class="hint" style="margin:6px 0 0">Source : ouvre la page du PDF avec la ligne encadrée. Après « Analyser le dessin » (onglet Aperçu du plan) : concordance avec le dessin,
    localisations du repère (clic : voir sur le plan ; « ? » : lecture incertaine), cotes du tableau confirmées, contredites ou non vérifiables. Les ouvrages sont créés avec les cotes du
    tableau (ou saisies), jamais avec une mesure du dessin ; une cote absente du dessin n'est pas un défaut.</div></div>`
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
      <td><input class="fi" data-k="nb" style="width:44px" value="${esc(r.nb)}" aria-label="Nombre ${esc(L.repere||L.id)}" title="${esc(L.nb?'quantité du tableau : '+L.quantite:'quantité non indiquée par le tableau')}" oninput="DXI.NR[${k}].nb=this.value;dxiUpd()">${L.nb?`<div class="mu">tableau : ${L.nb}</div>`:''}</td>
      <td><input class="fi" data-k="h" style="width:62px" value="${esc(r.h)}" placeholder="${esc(D.hCom.trim()||'à saisir')}" oninput="DXI.NR[${k}].h=this.value;dxiUpd()"></td>
      <td><input class="fi" data-k="ref" style="width:72px" value="${esc(r.ref)}" placeholder="auto" oninput="DXI.NR[${k}].ref=this.value;dxiUpd()"></td>
      <td>${D.fmt==='pdf'?`<button class="btn bs bo" onclick="event.stopPropagation();dxpVoir(${k})" title="Voir la ligne sur le PDF">p. ${N.page} ↗</button>${N.saisie?`<button class="btn bs bo" onclick="event.stopPropagation();dxpSuppr(${k})" title="Retirer cette ligne saisie" aria-label="Retirer la ligne saisie">✕</button>`:''}`
        +(D.ana?`<select class="fi" data-k="geo" style="max-width:190px;margin-top:3px" aria-label="Contour du dessin" onclick="event.stopPropagation()" onchange="dxnGeo(${k},this.value)"></select><div class="gs"></div><div class="rp"></div>`:'')
        :`<select class="fi" data-k="geo" style="max-width:190px" onchange="dxnGeo(${k},this.value)"></select><div class="gs"></div>`}</td><td class="st"></td></tr>`}).join('');
  dxiUpd()}
// Choix de la géométrie rattachée à une ligne (retirée de la vue « Géométries du dessin » ; aucune : elle y revient)
function dxnGeo(k,v){const r=DXI.NR[k];r.rej=v==='rej';r.geo=r.rej?'':v;r.geoT=true;r.perdu='';dxnLinks();dxiUpd()}
function dxnSel(k){const D=DXI;if(!D)return;D.nsel=k;document.querySelectorAll('#dxnT tr[data-n]').forEach(t=>t.classList.toggle('on',+t.dataset.n===k));dxnSvg();if(D.fmt==='pdf')dxpOver()}
function dxnAll(on){const D=DXI;if(!D)return;D.NR.forEach(r=>r.conf=on);document.querySelectorAll('#dxnT [data-k=conf]').forEach(e=>e.checked=on);dxiUpd()}
function dxnRefs(tab){const D=DXI;if(!D)return;D.NR.forEach((r,k)=>r.ref=tab?String(D.NL[k].L.repere||'').toUpperCase():'');
  document.querySelectorAll('#dxnT tr[data-n]').forEach(t=>t.querySelector('[data-k=ref]').value=D.NR[+t.dataset.n].ref);dxiUpd()}
// Lignes de nomenclature : cotes (mm) et forme saisies ou reprises du tableau → adaptateur (contrôles du moteur), comme les géométries
function dxnEval(moteur,hc){const D=DXI;if(!D.NL||!D.NL.length)return;
  D.NL.forEach(({N,L},k)=>{const r=D.NR[k],dm=dxnDims(r),fo=r.forme||dxnDef(dm);r.x=null;
    let h=hc;if(String(r.h).trim()!==''){try{h=parseCote(r.h,'mm')}catch(e){h=null}}
    const man=[];if(dm.etat!=='rect'&&dm.etat!=='circ')man.push(String(r.cotes).trim()?'cotes illisibles (ex. 650x800 ou Ø250)':L.dims&&!dxnU(N,L)?'unité des cotes du tableau':'cotes');
    const nb=/^\s*\d{1,4}\s*$/.test(r.nb==null?'1':String(r.nb))?parseInt(r.nb==null?'1':r.nb,10):0;
    if(!fo)man.push('forme');if(!(h>0))man.push(String(r.h).trim()?'hauteur illisible':'hauteur à coffrer');if(!(nb>=1))man.push('nombre (entier ≥ 1)');if(!String(D.ch||'').trim())man.push('chantier');
    if(man.length){r.st='ac';r.msg='à compléter : '+man.join(', ');return}
    const g=r.geo!==''?D.C[+r.geo]:null,x=CPI.adaptateur.versPlan(CPI.nomenclatures.candidat(N,L,{dims:dm,geo:g}),{confirme:true,forme:fo,h,unite:'mm',ref:r.ref.trim(),nb},{moteur,modele:D.M[fo]});
    if(!x.ok){r.st='er';r.msg=x.message+(x.messages&&x.messages.length?' : '+x.messages.join(' · '):'');return}
    const p=x.plan;
    if(p.ref&&P.some(q=>chKey(q.ch)===chKey(p.ch)&&ouKey(q.ouv).toLowerCase()===ouKey(p.ouv).toLowerCase()&&String(q.ref||'').toUpperCase()===p.ref)){r.st='er';r.msg=`référence ${p.ref} déjà utilisée dans cet ouvrage`;return}
    r.x=x;r.st=x.alertes.length?'wn':'ok';r.msg=x.alertes.join(' · ')})}
function dxnProv(k){const D=DXI,{N,L}=D.NL[k],r=D.NR[k],a=dxnAS(L),g=r.geo!==''?D.C[+r.geo]:null,u=dxnU(N,L);
  return CPI.nomenclatures.provenance(N,L,{forme:r.x.plan.forme,nb:r.x.plan.nb,cotes:r.cotes,dims:dxnDims(r),ref:r.ref.trim().toUpperCase(),uniteTableau:u||null,uniteDessin:D.fmt==='pdf'?'pt':D.u||null,
    uniteChoisie:!!(u&&!(L.dims&&L.dims.unite)&&!N.unite),geo:g?{c:g,statut:!r.geoT&&a.statut==='trouvee'?'trouvee':'choisie'}:null,rapprochement:D.fmt==='pdf'&&D.ana?dxrRapProv(a,r,D.CS[L.id]):null})}
// Statuts, formes possibles, géométries proposées, bilan (sans reconstruire la liste : garde la saisie en cours)
function dxnUpd(){const D=DXI;if(!D||!el('dxnT'))return;const lb={ok:'✓ prêt',wn:'⚠ prêt — ',ac:'… ',er:'⛔ non créé — '};
  document.querySelectorAll('#dxnT tr[data-n]').forEach(t=>{const k=+t.dataset.n,r=D.NR[k],{L}=D.NL[k],a=dxnAS(L),dm=dxnDims(r),F=dxnFormes(dm);
    if(r.forme&&!F.includes(r.forme))r.forme='';
    const sf=t.querySelector('[data-k=forme]'),fo=r.forme||dxnDef(dm),key=F.join();
    if(sf.dataset.f!==key){sf.dataset.f=key;sf.innerHTML=F.map(f=>`<option value="${f}">${f?esc(fmLb(f))+(/_fond$/.test(f)?' (choix explicite)':''):'— à choisir —'}</option>`).join('')}sf.value=fo;
    const sg=t.querySelector('[data-k=geo]'),O=a.options.slice(0,DXN_OPT),pdf=D.fmt==='pdf',gk=O.map(o=>o.c).join()+'|'+D.u+'|'+Object.values(D.cal||{}).map(x=>x.k).join();
    if(sg){if(sg.dataset.g!==gk){sg.dataset.g=gk;sg.innerHTML=`<option value="">— ${pdf?'aucun contour':'aucune'} —</option>`+O.map(o=>{const c=D.C[o.c];
      return `<option value="${o.c}">${esc(c.id+' · '+dxiDims(c)+' · '+(pdf?'p. '+c.source.page:c.source.calque)+(o.via==='cotes'?' · mêmes cotes':o.cotes==='diff'?' · cotes différentes':o.ambigu?' · près du repère':''))}</option>`}).join('')
      +(a.options.length>DXN_OPT?`<option disabled>… et ${a.options.length-DXN_OPT} autre(s)</option>`:'')+(pdf?'<option value="rej">✕ rejeter le rapprochement</option>':'')}
    sg.value=r.rej?'rej':r.geo;const gs=t.querySelector('.gs');
    if(pdf){const cc=r.rej?'rejete':a.concordance||'absente';gs.className='gs cc-'+cc;gs.textContent=(DXN_CC[cc]||cc)+(r.geo!==''&&r.geoT?' · contour choisi':'');gs.title=a.note;t.querySelector('.rp').innerHTML=dxrRap(k,a,r)}
    else{gs.textContent=r.geo!==''&&r.geoT?DXN_ST.choisie:DXN_ST[a.statut];gs.title=a.note;
    gs.style.color=r.geo!==''||a.statut==='trouvee'?'var(--okt)':a.statut==='absente'?'var(--muted)':'var(--acct)'}}
    const s=t.querySelector('.st');s.className='st '+(r.st==='ac'?'wn':r.st);
    s.innerHTML=esc(lb[r.st]+(r.st==='ok'?'':r.msg))+(r.perdu?`<div class="av">${esc(r.perdu)}</div>`:'')+(L.a_verifier.length?`<div class="av">à vérifier : ${esc(L.a_verifier.join(' ; '))}</div>`:'')+(a.note&&D.fmt!=='pdf'?`<div class="mu">${esc(a.note)}</div>`:'')});
  const n={trouvee:0,probable:0,multiple:0,absente:0};D.NL.forEach(({L})=>n[dxnAS(L).statut]++);
  const NN=D.NA.nomenclatures.filter(N=>!N.saisie).length,cf=D.NR.filter(r=>r.conf).length,nS=D.NL.filter(x=>x.N.saisie).length;
  if(el('dxiTabN'))el('dxiTabN').textContent=`Nomenclature des réservations (${D.NL.length})`;
  if(D.fmt==='pdf'){const nO=D.NL.filter(x=>x.N.ocr).length;el('dxnS').innerHTML=`<b>${D.NL.length-nS-nO} ligne(s) lue(s)</b> dans ${NN} tableau${NN>1?'x':''} · ${nO} ligne(s) reconnue(s) par OCR · ${nS} ligne(s) saisie(s) · ${cf} sélectionnée(s) · <b>${dxnReady().length} à créer</b>`
    +(D.ana?`<div style="margin-top:3px">Rapprochement avec le dessin : ${dxrBilan().txt}</div>`:'<div class="mu" style="margin-top:3px">Onglet Aperçu du plan : « Analyser le dessin » pour retrouver ces réservations sur le plan.</div>');return}
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
const dxnNR=L=>({conf:false,forme:'',cotes:'',cotesT:false,h:'',nb:String(L.nb||1),ref:String(L.repere||'').toUpperCase(),geo:'',geoT:false,rej:false,perdu:''});
async function dxpFile(nom,b){if(el('dxiZ')){el('dxiN').innerHTML=`<b>${esc(nom)}</b> · lecture du PDF…`;el('dxiZ').innerHTML=''}
  const lu=await CPI.pdf.lire(b,nom);if(!lu.ok)return dxiErr(nom,lu);
  const v=CPI.lecteur.lirePlan({format:'normalise',nom,contenu:lu.document});if(!v.ok){CPI.pdf.fermer(lu.pdf);return dxiErr(nom,v)}
  dxiQuit();const doc=lu.document,cur=coll(),NA=CPI.nomenclatures.analyser(doc),NL=NA.nomenclatures.flatMap(N=>N.lignes.map(L=>({N,L})));
  DXI={fmt:'pdf',nom,doc,pdf:lu.pdf,C:[],R:[],lay:{},u:'',ch:cur.ch,ouv:cur.ouv,ind:'',hCom:'',sel:-1,M:null,NA,NL,NR:NL.map(({L})=>dxnNR(L)),NU:{},nsel:-1,
    vue:NL.length?'n':'p',lk:new Set(),page:NL.length?NL[0].N.page:1,zoom:1,zone:null,zm:false,hl:-1,nz:0,ns:0,tok:0,OC:null,ocJob:null,no:0,ohl:null,
    cal:{},GP:{},GI:{},OT:{},OM:{},VU:{},CS:{},calm:null,rsel:-1,rn:0,ana:null,rJob:null,HR:[]};
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
    <div class="hint" style="margin:6px 0 0">Cadres verts en tirets : tableaux reconnus ; orange : ligne choisie ; bleu : zone ; violet : réservations repérées (clic : ligne du tableau). Pour choisir une zone : « Sélectionner une zone », puis cliquer-glisser sur la page.</div></div>
  <div class="dxp-s"><div id="dxpI"></div>
    <fieldset><legend>Réservations dessinées</legend><div class="mu">Toutes les pages (ou la zone choisie) : repères lus (texte du PDF, ou OCR des repères dessinés en traits),
      rectangles et cercles, rapprochés de la nomenclature. Simples propositions : rien n'est coché ni créé.</div>
      <label style="display:block;margin-top:4px"><input type="checkbox" id="dxrOcr" checked> lire les repères dessinés en traits (OCR local, quelques secondes par page)</label>
      <div class="dxp-b" style="margin-top:6px"><button class="btn bs bpr" id="dxrGo" onclick="dxrGo()">🔎 Analyser le dessin</button><button class="btn bs bo" id="dxrStop" onclick="dxrStop()" style="display:none">Arrêter</button><button class="btn bs bo" id="dxrJ" onclick="dxrExport()" disabled title="Tableaux, vues, observations, occurrences, associations, preuves et incertitudes, en JSON (fichier local)">⬇ Analyse (JSON)</button></div><div id="dxrM" style="margin-top:4px"></div>
      <div id="dxrE" style="margin-top:6px"></div></fieldset>
    <fieldset><legend>Zone du tableau</legend><div id="dxpZi" class="mu">Aucune zone choisie.</div>
      <div class="dxp-b" style="margin-top:6px"><button class="btn bs bo" id="dxpZa" onclick="dxpAnalyse()" disabled title="Textes extractibles du PDF : rapide, sans erreur de lecture">Analyser la zone</button>
      <button class="btn bs bo" id="dxpZo" onclick="dxoLancer()" disabled title="Reconnaissance visuelle locale (textes dessinés en tracés ou numérisés) : plus lente, à vérifier">Reconnaître le tableau (OCR)</button>
      <button class="btn bs bo" onclick="dxpZone(null)">Effacer la zone</button></div>
      <label class="mu" style="display:block;margin-top:4px">Sens du tableau (OCR) : <select class="fi" id="dxoRot" style="width:auto"><option value="">automatique</option><option value="0">horizontal</option>
        <option value="1">tourné de 90° (lu de bas en haut)</option><option value="3">tourné de 270° (lu de haut en bas)</option><option value="2">à l'envers (180°)</option></select></label><div id="dxoP" style="margin-top:4px"></div><div id="dxpZr" style="margin-top:4px"></div></fieldset>
    <fieldset><legend>Saisie assistée</legend><div class="mu" style="margin-bottom:6px">Recopier une ligne du tableau visible sur la page (page affichée et zone choisie gardées dans la provenance). Rien n'est complété à votre place.</div>
      <div class="fd"><label for="dxpR">Repère</label><input class="fi" id="dxpR"></div><div class="fd"><label for="dxpD">Désignation</label><input class="fi" id="dxpD"></div>
      <div class="fd"><label for="dxpK">Cotes (mm) : l × h ou Ø</label><input class="fi" id="dxpK" placeholder="ex. 650x800 ou Ø250"></div>
      <div class="fd"><label for="dxpNv">Niveau (position, facultatif)</label><input class="fi" id="dxpNv"></div><div class="fd"><label for="dxpOb">Observations (facultatif)</label><input class="fi" id="dxpOb"></div>
      <button class="btn bs bpr" style="margin-top:6px" onclick="dxpAjout()">＋ Ajouter la ligne</button><div id="dxpSm" class="mu" style="margin-top:4px"></div></fieldset></div></div><div id="dxrZ"></div><div id="dxoG"></div></div>`}
// Rendu de la page affichée : échelle = largeur de la zone × zoom ; un rendu plus récent annule le précédent
async function dxpPage(){const D=DXI,cv=el('dxpCv'),W=el('dxpW');if(!D||!D.pdf||!cv||!W)return;const p=D.doc.pages[D.page-1],k=D.k=Math.max(0.05,(W.clientWidth-4)/p.w)*D.zoom,tok=++D.tok;
  el('dxpPg').textContent=` Page ${D.page} / ${D.doc.pages.length} `;el('dxpZ').textContent=` ${Math.round(D.zoom*100)} % `;
  dxrEch();if(D.C.length&&!el('dxrT'))dxrRender();
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
  O.innerHTML=h+dxrOver(H,f)}
function dxpVoir(k){const D=DXI;if(!D||!D.NL[k])return;D.hl=k;D.hlo=null;D.page=D.NL[k].N.page||1;D.scroll=true;dxnSel(k);dxiVue('p')}
// Zone : cliquer-glisser en mode « Sélectionner une zone » ; coordonnées en points PDF, Y vers le haut, comme les textes lus
function dxpZm(on){const D=DXI;if(!D)return;D.zm=on==null?!D.zm:on;if(D.zm&&D.calm){D.calm=null;dxrEch()}el('dxpO').classList.toggle('zm',D.zm);el('dxpZm').setAttribute('aria-pressed',D.zm);el('dxpZm').classList.toggle('bpr',D.zm)}
function dxpPt(e){const D=DXI,b=el('dxpO').getBoundingClientRect(),p=D.doc.pages[D.page-1];return[Math.min(p.w,Math.max(0,(e.clientX-b.left)/D.k)),Math.min(p.h,Math.max(0,p.h-(e.clientY-b.top)/D.k))]}
function dxpPd(e){const D=DXI;if(D&&D.calm)return dxrPt(e);if(!D||!D.zm)return;e.preventDefault();try{e.target.setPointerCapture(e.pointerId)}catch(x){}const a=dxpPt(e);D.zd=a;D.zone={page:D.page,x0:a[0],y0:a[1],x1:a[0],y1:a[1],unite:'pt'};dxpOver()}
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
function dxpAnalyse(){const D=DXI,z=D&&D.zone;if(!z)return;const msg=el('dxpZr'),{T,S,A}=dxpZoneTS(z);
  if(!A.nomenclatures.length&&!A.ecartes.length&&T.length){const G=CPI.nomenclatures.textesEnGrille(S,z,T);   // en-tête non reconnu (tableau écarté : non) : la grille de traits suffit à ranger les textes
    if(G&&G.textes.length>=3)return dxoGrilleLue({z:Object.assign({},z)},{G,textes:G.textes,mesures:{ms:0,rangees:G.rangees,colonnes:G.lignes[0].length,source:'textes et traits du PDF',dpi:null}},true)}
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
// bouton « Annuler » créé une seule fois par opération : le recréer à chaque progression pouvait perdre un clic
function dxoProg(t,f){const z=el('dxoP');if(!z)return;
  if(t==null){z.innerHTML='';return}
  if(!z.querySelector('progress'))z.innerHTML=`<div class="mu"></div><div style="display:flex;gap:6px;align-items:center"><progress max="1"></progress>
    <button class="btn bs bo" onclick="dxoStop()">Annuler</button></div>`;
  z.querySelector('.mu').textContent=t;const p=z.querySelector('progress');
  if(f!=null)p.value=Math.max(0,Math.min(1,f));else p.removeAttribute('value')}
// Lancement : demande confirmation si la zone est déjà lisible par le texte du PDF (inutile de lancer un traitement lourd)
function dxoLancer(force){const D=DXI,z=D&&D.zone;if(!z||D.ocJob||D.rJob)return;
  if(!force){const N=dxpZoneTS(z).A.nomenclatures.find(N=>N.qualite.niveau==='bonne'&&N.lignes.length);
    if(N)return uiConfirm(`Cette zone contient un tableau déjà lisible par le texte du PDF (${N.lignes.length} ligne(s), lecture « bonne ») : « Analyser la zone » suffit, sans erreur de lecture possible. Lancer quand même la reconnaissance optique ?`,()=>dxoLancer(true),{ok:'Lancer l\'OCR'})}
  const job={z:Object.assign({},z),stop:false,run:'o'+(++D.no),t0:Date.now()};D.ocJob=job;el('dxpZo').disabled=true;el('dxpZr').textContent='';
  dxoProg('Démarrage du moteur de reconnaissance (intégré au fichier, hors connexion)',null);
  const ici=()=>DXI===D&&D.ocJob===job,op={run:job.run,annule:()=>job.stop,progres:(t,f)=>{if(ici())dxoProg(t,f)}};
  // grille de traits d'abord (lecture cellule par cellule), sinon lecture de toute la zone (tableau sans grille)
  (async()=>{const g=await dxrGeo(job.z.page).catch(()=>null);if(!ici())throw new Error('annulé');
    const rot=el('dxoRot')&&el('dxoRot').value!==''?+el('dxoRot').value:null;
    return await CPI.ocr.lireGrille(D.pdf,job.z,Object.assign({segments:g?g.segments:[],rot},op))||await CPI.ocr.lireZone(D.pdf,job.z,op)})()
    .then(r=>{if(!ici())return;D.ocJob=null;dxoProg(null);dxpZone(D.zone);dxoResultat(job,r)})
    .catch(e=>{if(!ici())return;D.ocJob=null;dxoProg(null);dxpZone(D.zone);el('dxpZr').innerHTML=`⛔ Reconnaissance impossible : ${esc(String(e&&e.message||e))}. Rien n'a été modifié.`})}
// Annulation : le moteur est arrêté aussitôt (il sera relancé au prochain OCR) ; rien n'est modifié
function dxoStop(){const D=DXI;if(!D||!D.ocJob)return;D.ocJob.stop=true;D.ocJob=null;CPI.ocr.arreter();dxoProg(null);dxpZone(D.zone);
  el('dxpZr').textContent='Reconnaissance annulée : rien n\'a été modifié.'}
// Résultat : tableau(x) reconstruit(s) par nomenclatures.analyser sur les textes OCR → grille ; une grille déjà corrigée sur la
// même zone garde les corrections de l'utilisateur (cellules modifiées, lignes ajoutées, lignes retirées)
function dxoResultat(job,r){const D=DXI,z=job.z,msg=el('dxpZr'),s=Math.round(r.mesures.ms/100)/10;
  if(r.G)return dxoGrilleLue(job,r);
  const A=CPI.nomenclatures.analyser({fichier:D.doc.fichier,format:'pdf',textes:r.textes,traits:r.traits,signalements:[]});
  const rows=A.nomenclatures.flatMap(N=>CPI.ocr.grille(N,r.textes)),p=r.mesures.passes[r.mesures.retenue-1];
  rows.forEach(w=>Object.keys(w.cells).forEach(k=>{w.cells[k]=String(w.cells[k]).replace(/\n/g,' ')}));
  const E=A.ecartes.map(e=>`${e.titre?'« '+e.titre.replace(/\n/g,' ')+' » ':''}${e.raison}`);
  if(!rows.length)return dxoRien(s,r,E);
  const O=D.OC&&dxoChevauche(D.OC.zone,z)?D.OC:null,{R2,sup,gard}=dxoGarder(rows,O,'cle0');
  D.OC={page:z.page,zone:z,mesures:r.mesures,titre:A.nomenclatures.map(N=>N.titre).filter(Boolean).join(' · '),unite:(A.nomenclatures.find(N=>N.unite)||{}).unite||'',
    uniteLue:(A.nomenclatures.find(N=>N.unite)||{}).unite||'',rows:R2,suppr:sup,ecartes:E,nT:r.textes.length,sel:-1};
  const nd=R2.reduce((n,w)=>n+Object.keys(w.doute).filter(k=>w.doute[k]&&!w.edite.includes(k)).length,0);
  msg.innerHTML=`✓ ${R2.length} ligne(s) reconnue(s) en ${s} s (${p.dpi} dpi) · <b>${nd} cellule(s) incertaine(s)</b> à vérifier dans la grille ci-dessous`
    +(gard?` · corrections gardées sur ${gard} ligne(s)`:'')+(sup.length?` · ${sup.length} ligne(s) retirée(s) laissée(s) de côté`:'')+(E.length?` · écarté : ${esc(E.join(' ; '))}`:'');
  D.ohl=null;dxoGrille();dxpOver()}
// Corrections d'une grille précédente reportées sur une nouvelle lecture : cellules modifiées (ligne retrouvée par son repère lu
// (cle0) après une nouvelle OCR, ou par sa rangée (src) après une réaffectation de colonnes), lignes ajoutées, lignes retirées
function dxoGarder(rows,O,par){let gard=0;if(!O)return{R2:rows,sup:[],gard};
  rows.forEach(w=>{const o=O.rows.find(o=>o.edite.length&&o.src&&o[par]&&o[par]===w[par]);if(o){o.edite.forEach(k=>{w.cells[k]=o.cells[k]});w.edite=o.edite.slice();w.notes=(o.notes||[]).slice();gard++}});
  O.rows.filter(o=>!o.src).forEach(o=>rows.push(o));
  const sup=O.suppr,R2=rows.filter(w=>!sup.some(x=>x.w.src&&x.w[par]&&x.w[par]===w[par]));return{R2,sup,gard}}
// Tableau lu cellule par cellule (grille de traits : OCR, ou textes du PDF) → nomenclature (depuisGrille : en-tête lu, ou colonnes
// à affecter) → grille de vérification. Colonnes réaffectées par l'utilisateur gardées pour une nouvelle lecture de la même zone.
// Un tableau d'aciers est écarté ; un tableau sans en-tête reconnu est montré quand même (jamais « aucune nomenclature » seul).
// Zone sans nomenclature de réservations : rien n'est ajouté ; la grille précédente reste (corrections), marquée comme telle
function dxoRien(s,r,E){const D=DXI,msg=el('dxpZr');
  msg.innerHTML=`Reconnaissance terminée (${s} s, ${r.textes.length} texte(s) lu(s)) : <b>aucune nomenclature de réservations reconnue</b> dans la zone${E.length?' ; écarté : '+esc(E.join(' ; ')):''}. Rien n'est ajouté.
    <details class="mu"><summary>Textes reconnus</summary>${esc(r.textes.map(t=>t.texte).join(' · '))}</details>`;
  if(D.OC){const n=D.OC.rows.filter(w=>w.edite.length||!w.src).length;D.OC.ancienne=true;
    msg.innerHTML+=`<div style="color:var(--acct)">La grille ci-dessous est celle de la reconnaissance précédente (page ${D.OC.page}, ${D.OC.rows.length} ligne(s)${n?`, ${n} modifiée(s) ou ajoutée(s) par vous`:''}) : elle n'est pas le résultat de cette zone. Gardez-la pour l'ajouter, ou « Fermer la grille ».</div>`;dxoGrille()}}
function dxoGrilleLue(job,r,pdfTexte){const D=DXI,z=job.z,msg=el('dxpZr'),s=Math.round(r.mesures.ms/100)/10,O0=D.OC&&dxoChevauche(D.OC.zone,z)?D.OC:null;
  const G=Object.assign({fichier:D.doc.fichier,format:'pdf',id:'G'},r.G),cles=O0&&O0.src&&O0.src.nc===Math.max(0,...r.G.lignes.map(l=>l.length))?O0.src.cles:null;
  const {N,entete}=CPI.nomenclatures.depuisGrille(G,cles);
  if(N.nature==='aciers')return dxoRien(s,r,[`${N.titre?'« '+N.titre.replace(/\n/g,' ')+' » ':''}tableau reconnu comme nomenclature d'aciers (ferraillage)`]);
  if(!N.lignes.length){msg.innerHTML=`Lecture terminée (${s} s) : grille de ${r.mesures.rangees} rangée(s) × ${r.mesures.colonnes} colonne(s) trouvée(s), mais aucune cellule lisible sous l'en-tête. Rien n'est ajouté : saisie assistée possible ci-dessous.`;return}
  const rows=dxoLignesGrille(N,r.textes),{R2,sup,gard}=dxoGarder(rows,O0,'cle0');
  D.OC={page:z.page,zone:z,mesures:r.mesures,titre:N.titre,unite:N.unite||'',uniteLue:N.unite||'',rows:R2,suppr:sup,ecartes:[],nT:r.textes.length,sel:-1,pdfTexte:!!pdfTexte,
    src:{G,textes:r.textes,cles:N.colonnes.map(c=>c.cle),nc:N.colonnes.length,colonnes:N.colonnes,entete,nature:N.nature}};
  const nd=R2.reduce((n,w)=>n+Object.keys(w.doute).filter(k=>w.doute[k]&&!w.edite.includes(k)).length,0),m=r.mesures;
  msg.innerHTML=`✓ ${R2.length} ligne(s) ${pdfTexte?'lue(s) dans la grille du tableau':`reconnue(s) cellule par cellule en ${s} s (${m.dpi} dpi${m.rotation?`, tableau tourné de ${m.rotation}°`:''})`}`
    +` · grille ${m.rangees} × ${m.colonnes} (${esc(m.source)}) · <b>${nd} cellule(s) incertaine(s)</b> à vérifier`
    +(entete?'':` · <b style="color:var(--acct)">en-tête non reconnu : affecter les colonnes ci-dessous</b>`)+(N.nature!=='reservations'&&entete?' · <span style="color:var(--acct)">nature du tableau non confirmée (pas de titre « réservations »)</span>':'')
    +(gard?` · corrections gardées sur ${gard} ligne(s)`:'')+(sup.length?` · ${sup.length} ligne(s) retirée(s) laissée(s) de côté`:'');
  D.ohl=null;dxoGrille();dxpOver()}
const dxoLignesGrille=(N,T)=>{const R=CPI.ocr.grille(N,T);R.forEach(w=>Object.keys(w.cells).forEach(k=>{w.cells[k]=String(w.cells[k]).replace(/\n/g,' ')}));return R};
// Réaffectation d'une colonne du tableau (titre mal lu ou absent) : lignes reconstruites, corrections de chaque rangée gardées
function dxoCol(j,v){const D=DXI,O=D&&D.OC;if(!O||!O.src)return;O.src.cles[j]=v;
  const {N,entete}=CPI.nomenclatures.depuisGrille(O.src.G,O.src.cles),{R2,sup}=dxoGarder(dxoLignesGrille(N,O.src.textes),O,'src');
  Object.assign(O,{rows:R2,suppr:sup,unite:O.unite||N.unite||'',sel:-1});Object.assign(O.src,{colonnes:N.colonnes,entete,nature:N.nature});D.ohl=null;dxoGrille();dxpOver()}
// Grille de vérification : toutes les cellules modifiables ; incertaines en orange (survol : texte brut et confiance) ;
// une cellule choisie est encadrée sur l'aperçu de la page
function dxoGrille(){const D=DXI,G=el('dxoG');if(!G||!D)return;const O=D.OC;if(!O){G.innerHTML='';return}
  const C=CPI.ocr.colonnes(O.rows),lg=k=>k==='description'||k==='observations'||k==='autre';
  const tip=(w,k)=>[w.brut[k]?`OCR brut : « ${w.brut[k]} »`:'',w.conf[k]!=null?`confiance ${w.conf[k]} %`:'',...(w.corr[k]||[]),w.info&&w.info[k]||'',w.edite.includes(k)?'corrigé par vous':''].filter(Boolean).join('\n');
  G.innerHTML=`<fieldset class="dxo"><legend>${O.pdfTexte?'Vérification du tableau (textes du PDF rangés dans sa grille)':'Vérification de la reconnaissance (OCR)'} · page ${O.page}${O.titre?' · « '+esc(O.titre.replace(/\n/g,' '))+' »':''}</legend>
    ${O.ancienne?`<div id="dxoA" style="color:var(--acct);font-weight:600;margin-bottom:6px">⚠ Grille de la reconnaissance précédente : la dernière zone analysée n'a donné aucune nomenclature.</div>`:''}
    <div class="mu" style="margin-bottom:6px">Chaque cellule est modifiable. <span style="color:var(--acct)">Orange</span> : lecture incertaine ou corrigée automatiquement (survol : texte brut,
    confiance) ; cliquer une cellule l'encadre sur la page. Ligne en trop : ✕ ; ligne coupée en deux : ⇣ (fusion avec la suivante) ; ligne manquante : ＋. Rien n'est coché pour la création.</div>
    <div class="dxp-b" style="margin-bottom:6px">Unité des dimensions : <select class="fi" id="dxoU" style="width:auto" onchange="DXI.OC.unite=this.value">${['','mm','cm','m'].map(u=>`<option value="${u}"${O.unite===u?' selected':''}>${u||'— à choisir —'}</option>`).join('')}</select>
      <span class="mu">${O.uniteLue?`lue dans l'en-tête : ${esc(O.uniteLue)}`:'non indiquée par le tableau'}</span></div>
    ${O.src?`<div class="dxp-b" id="dxoC" style="margin-bottom:6px;flex-wrap:wrap"><span class="mu">Colonnes du tableau${O.src.entete?'':' (en-tête non reconnu)'} :</span>${O.src.colonnes.map((c,j)=>`<label class="mu" style="display:inline-flex;gap:3px;align-items:center">« ${esc(c.titre.replace(/\n/g,' '))} »
      <select class="fi" style="width:auto" data-c="${j}" aria-label="${esc('Champ de la colonne '+(j+1))}" onchange="dxoCol(${j},this.value)">${DXO_CH.map(([k,t])=>`<option value="${k}"${c.cle===k?' selected':''}>${t}</option>`).join('')}</select>${c.deduite?'<span title="titre illisible : nature déduite des valeurs">ⓘ</span>':''}</label>`).join('')}</div>`:''}
    <div class="dxi-t"><table class="ser" id="dxoT"><thead><tr><th>#</th>${C.map(([k,t])=>`<th>${esc(t)}</th>`).join('')}<th>État</th><th></th></tr></thead><tbody>
    ${O.rows.map((w,i)=>`<tr data-o="${i}"${O.sel===i?' class="on"':''}><td>${i+1}</td>${C.map(([k])=>{const v=esc(w.cells[k]||''),c=`fi${w.doute[k]&&!w.edite.includes(k)?' dt':''}${w.edite.includes(k)?' ed':''}`,
        a=`data-k="${k}" title="${esc(tip(w,k))}" aria-label="${esc(k+' ligne '+(i+1))}" oninput="dxoSet(${i},'${k}',this)" onfocus="dxoVoir(${i},'${k}')"`;
        return `<td>${lg(k)?`<textarea class="${c}" rows="1" ${a}>${v}</textarea>`:`<input class="${c}" value="${v}" ${a}>`}</td>`}).join('')}
      <td class="st">${dxoEtat(w)}</td><td class="ac"><button class="btn bs bo" title="Insérer une ligne vide après" aria-label="Insérer une ligne" onclick="dxoAjout(${i})">＋</button><button class="btn bs bo" title="Fusionner avec la ligne suivante" aria-label="Fusionner avec la suivante" onclick="dxoFusion(${i})"${i+1<O.rows.length?'':' disabled'}>⇣</button><button class="btn bs bo" title="Retirer cette ligne" aria-label="Retirer la ligne" onclick="dxoSuppr(${i})">✕</button></td></tr>`).join('')}
    </tbody></table></div>
    <div class="dxp-b" style="margin-top:6px"><button class="btn bs bo" onclick="dxoAjout(-1)">＋ Ajouter une ligne</button>${O.suppr.length?`<button class="btn bs bo" onclick="dxoRetablir()">Rétablir les ${O.suppr.length} ligne(s) retirée(s)</button>`:''}
      <button class="btn bs bpr" id="dxoV" onclick="dxoValider()">Ajouter à la nomenclature (${O.rows.length} ligne(s))</button><button class="btn bs bo" onclick="dxoFermer()">Fermer la grille</button></div><div id="dxoR" class="mu" style="margin-top:4px"></div></fieldset>`}
const DXO_CH=[['repere','Repère'],['quantite','Quantité (Nb)'],['largeur','Largeur'],['hauteur','Hauteur (de l\'ouverture)'],['diametre','Diamètre Ø'],['ouverture','Ouverture l × h'],
  ['description','Désignation / fonction'],['type','Type ou nature'],['reseau','Réseau (DN)'],['niveau','Niveau ou altitude'],['angle','Angle'],['observations','Observations'],['lot','Lot / entreprise'],['autre','Autre (gardée telle quelle)']];
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
  const deja=new Set(D.NL.filter(x=>!x.N.ocr&&!x.N.grilleTexte&&x.N.page===O.page&&x.L.repere).map(x=>cle(x.L.repere)));
  const rows=O.rows.filter(w=>!(dxoCle(w)&&deja.has(dxoCle(w)))),dbl=O.rows.length-rows.length;
  if(!rows.length){R.textContent=dbl?`Toutes les lignes (${dbl}) sont déjà dans la nomenclature (lecture du texte ou saisie) : rien n'est ajouté.`:'Aucune ligne à ajouter.';return}
  const vieux=new Set(D.NA.nomenclatures.filter(N=>(N.ocr||N.grilleTexte)&&dxoChevauche(N.zone,O.zone))),old=new Map();
  D.NL.forEach((x,k)=>{if(vieux.has(x.N)&&x.L.repere)old.set(cle(x.L.repere),D.NR[k])});
  const N=CPI.ocr.versNomenclature(rows,{id:(O.pdfTexte?'Z':'O')+(++D.nz),fichier:D.doc.fichier,page:O.page,zone:O.zone,titre:O.titre,unite:O.unite,mesures:O.mesures,texte:O.pdfTexte});
  const keep=D.NL.map((x,k)=>vieux.has(x.N)?-1:k).filter(k=>k>=0),NL2=N.lignes.map(L=>({N,L}));
  D.NL=keep.map(k=>D.NL[k]).concat(NL2);D.NR=keep.map(k=>D.NR[k]).concat(NL2.map(({L})=>{const o=L.repere&&old.get(cle(L.repere));return o?Object.assign(o,{x:null}):dxnNR(L)}));
  D.NA.nomenclatures=D.NA.nomenclatures.filter(N=>!vieux.has(N)).concat([N]);D.hl=-1;D.nsel=-1;
  dxnAssoc();dxnRefresh();dxpOver();
  R.innerHTML=`✓ ${rows.length} ligne(s) ajoutée(s) à la nomenclature (tableau ${esc(N.id)})`+(vieux.size?`, en remplacement de l'ajout précédent depuis cette zone`:'')
    +(dbl?` · ${dbl} ligne(s) déjà lue(s) par le texte du PDF ou saisie(s), non ajoutée(s)`:'')+` : hauteur et sélection dans l'onglet <a href="#" onclick="dxiVue('n');return false">Nomenclature</a>.`}

// ==== PDF : repérage des réservations sur le dessin (geometrie.js, fonctions dxr*) ====
// Échelle d'une page : mm réels par point PDF, choisie par l'utilisateur (2 points + distance, ou échelle écrite sur la page)
const dxrK=c=>{const e=DXI&&DXI.cal&&DXI.cal[c&&c.source?c.source.page:c];return e?e.k:null};
const DXR_PT=25.4/72;   // mm de papier par point PDF
async function dxrGeo(n){const D=DXI;if(!D.GP[n])D.GP[n]=await CPI.pdf.chemins(D.pdf,n);return D.GP[n]}
// Analyse du dessin : toutes les pages (ou la zone choisie, sur sa page) ; par page : tracés, repères dessinés lus par OCR
// (blocs de texte en traits, CPI.geometrie.blocsTexte → CPI.ocr.lireBlocs, gardés pour les analyses suivantes), contours ;
// puis rapprochement avec la nomenclature (toutes pages). Une erreur ou un arrêt laisse l'état précédent, bouton rendu.
const DXR_BL=3000;   // shortcut: au plus 3000 blocs de texte lus par page (les plus proches des contours d'abord) ; à relever si un vrai plan l'exige
const dxrCad=n=>DXI.NA.nomenclatures.filter(N=>N.page===n&&!N.saisie).map(N=>N.zone?[N.zone.x0,N.zone.y0,N.zone.x1,N.zone.y1]:N.cadre).filter(Boolean)
  .concat(DXI.NA.ecartes.filter(e=>e.page===n&&e.cadre).map(e=>e.cadre));
const dxrDans=(b,t)=>t.x>=b[0]&&t.x<=b[2]&&t.y>=b[1]&&t.y<=b[3];
// Textes du dessin : ceux du PDF et ceux lus par OCR, hors tableaux reconnus (cadres, zones OCR)
function dxrTextes(n){const D=DXI,P=n?[n]:D.doc.pages.map(p=>p.n),T=[];
  P.forEach(m=>{const cad=dxrCad(m);D.doc.textes.filter(t=>t.page===m).concat(D.OT[m]||[]).forEach(t=>{if(!cad.some(b=>dxrDans(b,t)))T.push(t)})});return T}
function dxrRappels(t){const D=DXI,g=D.GP[t.page];if(!g)return[];if(!D.GI[t.page])D.GI[t.page]=CPI.geometrie.index(g);return CPI.geometrie.rappels(g,t,D.GI[t.page])}
// Vues techniques (toutes pages analysées) et vue d'un point
const dxrVues=()=>Object.values(DXI.VU).flatMap(x=>x.vues);
const dxrVue=(p,x,y)=>{const v=DXI.VU[p];return v?CPI.vues.situer(v.carte,x,y):null};
const dxrVueDe=id=>dxrVues().find(v=>v.id===id)||null;
function dxrStop(){const D=DXI;if(!D||!D.rJob)return;D.rJob.stop=true;CPI.ocr.arreter()}
async function dxrGo(){const D=DXI;if(!D||!D.pdf||D.rJob||D.ocJob)return;const z=D.zone&&D.zone.page===D.page?Object.assign({},D.zone):null,
    pages=z?[z.page]:D.doc.pages.filter(p=>!p.erreur).map(p=>p.n),M=el('dxrM'),b=el('dxrGo'),job=D.rJob={stop:false},ocr=!el('dxrOcr')||el('dxrOcr').checked,B=[];
  const ici=()=>DXI===D&&D.rJob===job,fin=m=>{if(DXI!==D)return;if(D.rJob===job)D.rJob=null;if(el('dxrGo')){el('dxrGo').disabled=false;el('dxrStop').style.display='none'}if(m!=null&&el('dxrM'))el('dxrM').innerHTML=m};
  b.disabled=true;el('dxrStop').style.display='';const msg=t=>{if(ici()&&el('dxrM'))el('dxrM').textContent=t};
  try{for(const n of pages){if(job.stop)throw new Error('annulé');msg(`Page ${n} : lecture des tracés…`);const g=await dxrGeo(n);if(!ici())return fin();
      const cad=dxrCad(n);
      if(ocr&&!D.OT[n]){const K=CPI.geometrie.blocsTexte(g,{cadres:cad});
        msg(`Page ${n} : ${K.length} bloc(s) de texte dessiné à lire…`);
        const pf=[...new Set(D.NL.map(({L})=>(CPI.nomenclatures.cleRep(L.repere||'').match(/^[A-Z]{1,4}/)||[''])[0]).filter(Boolean))];
        const r=await CPI.ocr.lireBlocs(D.pdf,n,K.slice(0,DXR_BL),{run:'b'+n,prefixes:pf,annule:()=>job.stop||!ici(),progres:(t,f)=>msg(`Page ${n} : ${t}${f?' ('+Math.round(f*100)+' %)':''}`)});
        if(!ici())return fin();D.OT[n]=r.textes;D.OM[n]=Object.assign(r.mesures,{trouves:K.length})}
      const res=CPI.geometrie.detecterPage(g,{fichier:D.doc.fichier,textes:dxrTextes(n),cadres:cad,zone:z});
      // vues techniques de la page (titres, régions) : contours rattachés à leur vue
      D.VU[n]=CPI.vues.detecter(g,dxrTextes(n),{cadres:cad});res.candidats.forEach(c=>c.vue=CPI.vues.situer(D.VU[n].carte,c.centre[0],c.centre[1]));
      dxrFusion(n,res,z);B.push({n,res})}}
  catch(e){const a=job.stop||String(e&&e.message||e)==='annulé';   // arrêt : le moteur OCR est détruit, son erreur n'en est pas une
    fin(a?'Analyse arrêtée : résultats des pages déjà analysées gardés.':'⛔ Analyse impossible : '+esc(String(e&&e.message||e))+'. Les résultats précédents sont gardés.');
    if(a&&B.length&&DXI===D){D.ana={pages:B.map(x=>x.n),zone:z,ocr};dxnAssoc();dxnRefresh();dxrRender();dxpOver()}return}
  if(!ici())return fin();
  D.ana={pages:pages,zone:z,ocr};
  try{dxnAssoc()}catch(e){D.ana=null;D.AS={};fin('⛔ Rapprochement impossible : '+esc(String(e&&e.message||e)));return}
  const ok=B.flatMap(x=>x.res.candidats.filter(c=>c.statut==='a_confirmer')),nc=ok.filter(c=>c.type==='circ').length,nE=B.reduce((s,x)=>s+x.res.candidats.length,0)-ok.length,
    nO=pages.reduce((s,n)=>s+(D.OT[n]||[]).length,0),cp=B.some(x=>x.res.coupe);
  fin(`✓ ${z?'Zone de la page '+z.page:pages.length+' page(s)'} : <b>${ok.length} forme(s) possible(s)</b> (${ok.length-nc} rectangle(s), ${nc} cercle(s)) · ${nE} contour(s) écarté(s)`
    +(ocr?` · ${nO} texte(s) dessiné(s) lu(s) par OCR`:'')+(cp?' · <span style="color:var(--acct)">page très chargée : une partie des traits n\'est pas lue</span>':'')
    +(D.NL.length?` · <b>rapprochement : ${dxrBilan().txt}</b>`:'')+(pages.some(n=>!dxrK(n))?' · <span style="color:var(--acct)">page(s) sans échelle : cotes des formes hors nomenclature à saisir</span>':''));
  if(el('dxrJ'))el('dxrJ').disabled=false;dxnRefresh();dxrRender();dxpOver()}
// Identité stable d'un contour (page, forme, emprise à 0,5 pt) : une nouvelle analyse garde les corrections du même contour
// (cotes, hauteur, forme, référence, coche, rattachement à une ligne) ; un contour disparu ne les transmet à aucun autre
const dxrCle=c=>[c.source.page,c.type].concat(c.bbox.map(v=>Math.round(v*2)/2)).join('|');
// D.RK : corrections de tous les contours déjà vus (un contour sorti d'une analyse par zone puis retrouvé les reprend)
function dxrFusion(n,res,z){const D=DXI,old=D.RK||(D.RK=new Map()),run=++D.rn;D.C.forEach((c,i)=>{if(c.source.page===n)old.set(dxrCle(c),{c,r:D.R[i]})});
  const gk=D.NR.map(r=>r.geo!==''&&D.C[+r.geo]?{k:dxrCle(D.C[+r.geo]),id:D.C[+r.geo].id}:null),keep=D.C.map((c,i)=>c.source.page===n?-1:i).filter(i=>i>=0);
  const vieux=new Set([...old.values()].filter(o=>o.c.source.page===n).map(o=>o.c.id)),R=res.candidats.map(c=>{c.zone=z;const o=old.get(dxrCle(c));if(o){c.id=o.c.id;return o.r}return null});
  res.candidats.forEach((c,j)=>{if(!R[j]&&vieux.has(c.id))c.id+='.'+run});
  D.C=keep.map(i=>D.C[i]).concat(res.candidats);
  D.R=keep.map(i=>D.R[i]).concat(res.candidats.map((c,j)=>R[j]||{conf:false,forme:'',h:'',ref:c.annot.repere?c.annot.repere.texte.toUpperCase().replace(/\s+/g,''):'',cotes:'',cotesT:false,pre:null}));
  D.NR.forEach((r,k)=>{const g=gk[k];if(!g)return;const j=D.C.findIndex(c=>dxrCle(c)===g.k);if(j>=0){r.geo=String(j);return}
    r.geo='';if(r.geoT)r.perdu=`contour ${g.id} absent de la nouvelle analyse : rattachement retiré (aucun autre contour ne le remplace d'office)`;r.geoT=false});
  D.rsel=-1;D.C.forEach((c,i)=>{if(c.source.page===n)dxrPre(i)})}
// Détail du rapprochement d'une ligne (onglet Nomenclature) : localisations cliquables, cotes vérifiées, quantité, doutes
function dxrRap(k,a,r){const D=DXI,O=a.occurrences||[],dm=a.dims||{},f=dxiNum;let h='';
  if(r.perdu)h+=`<div class="av">${esc(r.perdu)}</div>`;
  const cs=D.CS[D.NL[k].L.id],role=j=>cs&&(cs.roles.find(x=>x.occurrence===j)||{}).role;
  if(O.length)h+='<div>'+O.map((o,j)=>{const v=o.vue&&dxrVueDe(o.vue),lv=v?`${v.id} ${v.libelle}${v.partie?' '+v.partie:''}`:'hors vue';
    return `<button class="btn bs bo" onclick="event.stopPropagation();dxrLoc(${k},${j})" title="${esc((o.source==='ocr'?`lu par OCR « ${o.brut} », confiance ${o.conf} %`:'texte du PDF')+' · vue : '+(v?v.id+(v.titre?' « '+v.titre+' »':' (sans titre)'):'aucune')+(role(j)==='physique'?' · occurrence comptée':' · représentation (non comptée)')+(o.contour?' · contour '+o.contour:'')+(o.doutes.length?' · '+o.doutes.join(' ; '):''))}">${o.fiable?'':'? '}${role(j)==='physique'?'●':'○'} p. ${o.page} · ${esc(o.texte)}${o.source==='ocr'?' (OCR)':''} · ${esc(lv)} ↗</button>`}).join('')+'</div>';
  const E={confirmee:'✓ confirmée',mesuree:'≈ mesurée',conflit:'⚠ contredite',non_verifiable:'non vérifiable'},V=Object.values(dm);
  if(V.length)h+='<div>Cotes du tableau : '+V.map(x=>`<span title="${esc(x.preuves.join(' ; '))}">${esc(x.libelle)} ${E[x.etat]}</span>`).join(' · ')+'</div>';
  else if(O.length)h+='<div class="mu">pas de cotes l × h ou Ø dans le tableau : rien à vérifier sur le dessin</div>';
  if(cs)h+=`<div><b>Quantité attendue ${cs.attendue==null?'non indiquée':cs.attendue}</b> · localisée(s) : ${cs.localisees} · représentation(s) : ${cs.representations}${cs.restantes==null?'':' · restante(s) : <b>'+cs.restantes+'</b>'}${cs.depasse?' <span style="color:var(--acct)">⚠ plus que la quantité</span>':''}</div>`;
  // la lecture de la quantité par page (rapprochement) est remplacée par le décompte par vue
  const old=(a.quantite||{}).lecture,M=String(a.note||'').split(' ; ').filter(x=>x&&x!==old).concat(cs?cs.notes:[],[...new Set(O.flatMap(o=>o.doutes))]);
  if(M.length)h+=`<div class="mu">${esc(M.join(' ; '))}</div>`;
  return h}
function dxrLoc(k,j){const D=DXI,o=(dxnAS(D.NL[k].L).occurrences||[])[j];if(!o)return;D.hl=-1;D.hlo={k,j};D.page=o.page;D.scroll=true;dxnSel(k);dxiVue('p')}
// Provenance du rapprochement (clé origineImport.rapprochement) : concordance, localisations (page, position, texte brut OCR,
// confiance, corrections, contour), état de chaque cote du tableau, quantité, rejet par l'utilisateur ; les cotes créées restent celles retenues
function dxrRapProv(a,r,cs){const q=x=>Math.round(x*100)/100,vu=id=>{const v=id&&dxrVueDe(id);return v?{id:v.id,type:v.type,titre:v.titre,partie:v.partie}:null};
  return{concordance:r.rej?'rejete':a.concordance||'absente',rejete:!!r.rej,note:a.note||'',
    localisations:(a.occurrences||[]).map((o,j)=>({page:o.page,x:q(o.x),y:q(o.y),texte:o.texte,source:o.source,brut:o.brut,confiance:o.conf,corrections:o.corrections.slice(),
      zone:o.box?{page:o.box.page,x0:q(o.box.x0),y0:q(o.box.y0),x1:q(o.box.x1),y1:q(o.box.y1),unite:'pt'}:null,vue:vu(o.vue),role:cs?(cs.roles.find(x=>x.occurrence===j)||{}).role||null:null,fiable:o.fiable,doutes:o.doutes.slice(),contour:o.contour,cotes_voisines:o.cotes.slice()})),
    cotes:Object.fromEntries(Object.entries(a.dims||{}).map(([n,x])=>[n,{valeur:x.valeur,etat:x.etat,preuves:x.preuves.slice()}])),quantite:a.quantite?JSON.parse(JSON.stringify(a.quantite)):null,
    occurrences:cs?{attendue:cs.attendue,localisees:cs.localisees,representations:cs.representations,restantes:cs.restantes,notes:cs.notes.slice()}:null}}
// Analyse du plan en JSON (préparée pour une future IA locale : aucune IA ici) : tableaux, lignes, vues, observations
// graphiques (contours, repères localisés), occurrences physiques, associations, preuves des cotes, incertitudes
function dxrJSON(){const D=DXI,q=x=>Math.round(x*100)/100,bx=b=>b?b.map(q):null,J={format:'coffraplan-analyse-plan',v:1,fichier:D.doc.fichier,
    tables:D.NA.nomenclatures.map(N=>({id:N.id,page:N.page,titre:N.titre||null,cadre:bx(N.cadre||(N.zone?[N.zone.x0,N.zone.y0,N.zone.x1,N.zone.y1]:null)),rotation:N.rotation||0,
      source:N.saisie?'saisie':N.ocr?'ocr':N.grilleTexte?'grille':'pdf',colonnes:N.colonnes.map(c=>({titre:c.titre,cle:c.cle,unite:c.unite||null})),qualite:N.qualite})),
    tableRows:D.NL.map(({N,L},k)=>({id:L.id,table:N.id,rang:L.rang,repere:L.repere||null,designation:L.description||null,quantite:{texte:L.quantite||null,valeur:L.nb||null},
      dims:L.dims?{type:L.dims.type,texte:L.dims.texte,unite:dxnU(N,L)||null}:null,cellules:L.cellules.slice(),a_verifier:(L.a_verifier||[]).slice()})),
    views:dxrVues().map(v=>({id:v.id,page:v.page,region:v.region,titre:v.titre,type:v.type,partie:v.partie,echelle:v.echelle,niveau:v.niveau,confiance:v.confiance,motifs:v.motifs})),
    graphicalObservations:[],physicalOccurrences:[],associations:[],evidence:[],uncertainties:[]};
  D.C.forEach((c,i)=>{const cl=c.statut==='a_confirmer'&&!D.lk.has(i)?dxrCl(i):null;
    J.graphicalObservations.push({id:c.id,type:'contour',forme:c.type,page:c.source.page,vue:c.vue||null,bbox:bx(c.bbox),statut:c.statut,rattache:D.lk.has(i),
      classement:cl,repere:c.annot&&c.annot.repere?c.annot.repere.texte:null,cotes:c.annot&&c.annot.cotes?c.annot.cotes.texte:null,remarques:c.remarques.slice()})});
  D.NL.forEach(({L},k)=>{const a=dxnAS(L),cs=D.CS[L.id],r=D.NR[k];
    (a.occurrences||[]).forEach((o,j)=>{const id=`${L.id}/O${j+1}`,role=cs?(cs.roles.find(x=>x.occurrence===j)||{}).role:null;
      J.graphicalObservations.push({id,type:'repere',page:o.page,vue:o.vue||null,x:q(o.x),y:q(o.y),texte:o.texte,source:o.source,brut:o.brut,confiance:o.conf,fiable:o.fiable});
      J.associations.push({ligne:L.id,observation:id,type:'repere',role,contour:o.contour});if(o.contour)J.associations.push({ligne:L.id,observation:o.contour,type:'contour',via:id});
      o.doutes.forEach(m=>J.uncertainties.push({ligne:L.id,observation:id,message:m}))});
    if(cs){cs.physiques.forEach(p=>J.physicalOccurrences.push({id:`${L.id}#${p.n}`,ligne:L.id,n:p.n,vue:p.vue,page:p.page,x:q(p.x),y:q(p.y),fiable:p.fiable,
        representations:p.representations.map(j=>`${L.id}/O${j+1}`)}));
      J.tableRows[k].occurrences={attendue:cs.attendue,localisees:cs.localisees,representations:cs.representations,restantes:cs.restantes};
      cs.notes.forEach(m=>J.uncertainties.push({ligne:L.id,message:m}))}
    Object.entries(a.dims||{}).forEach(([n,x])=>J.evidence.push({ligne:L.id,dimension:n,valeur:x.valeur,etat:x.etat,preuves:x.preuves.slice()}));
    if(r.rej)J.uncertainties.push({ligne:L.id,message:'rapprochement rejeté par l\'utilisateur'})});
  return J}
function dxrExport(){const D=DXI;if(!D||!D.ana)return;dlBlob(new Blob([JSON.stringify(dxrJSON(),null,1)],{type:'application/json'}),String(D.nom||'plan').replace(/\.[^.]+$/,'').replace(/[^\w\-]+/g,'_')+'_analyse.json')}
// Bilan du rapprochement (comptes des concordances, repères lus, doublons évités, formes hors nomenclature)
function dxrBilan(){const D=DXI,n={forte:0,partielle:0,probable:0,conflit:0,absente:0,rejete:0};let vues=0;
  D.NL.forEach(({L},k)=>{const a=dxnAS(L);n[D.NR[k].rej?'rejete':a.concordance||'absente']++;vues+=Math.max(0,(a.preuves||[]).length-1)});
  const hors=D.C.filter((c,i)=>c.statut==='a_confirmer'&&!D.lk.has(i)).length,nr=D.NL.reduce((s,{L})=>s+(dxnAS(L).occurrences||[]).length,0);
  const o={...n,reperes:nr,doublons:D.lk.size,vues,hors,horsReperes:D.HR.length,colonnes:D.ana&&D.ana.colonnes||0};
  o.txt=`${n.forte} forte(s), ${n.partielle} partielle(s), ${n.probable} probable(s), ${n.conflit} conflit(s), ${n.absente} non retrouvée(s)${n.rejete?`, ${n.rejete} rejetée(s)`:''}`
    +` · ${nr} localisation(s) de repère · ${D.lk.size} contour(s) rattaché(s) (pas de doublon) · ${hors} forme(s) hors nomenclature`
    +(D.HR.length?` · repère(s) hors nomenclature : ${D.HR.slice(0,12).map(x=>esc(x.texte)+' (p. '+x.page+')').join(', ')}${D.HR.length>12?'…':''}`:'');
  return o}
// Cotes proposées (mm) : cote écrite à côté du contour (unité écrite, ou déduite de la mesure à 10 % près), sinon mesure à l'échelle
function dxrPre(i){const D=DXI,c=D.C[i],r=D.R[i],k=dxrK(c),A=c.annot&&c.annot.cotes,f=dxiNum,circ=c.type==='circ';
  const mes=k?(circ?[c.dims.D*k]:[c.dims.L*k,c.dims.l*k]):null,pres=(v,m)=>v.every((y,j)=>Math.abs(y*m-mes[j])<=0.1*mes[j]);let p={cotes:'',origine:null,note:''};
  if(A&&(A.etat==='circ')===circ){const v=circ?[A.D]:[Math.max(A.a,A.b),Math.min(A.a,A.b)],u=A.unite||(mes&&['mm','cm','m'].find(x=>pres(v,DXI_MM[x])));
    if(u){const m=DXI_MM[u];p={cotes:circ?'Ø'+f(A.D*m):f(A.a*m)+'x'+f(A.b*m),origine:'annotation',texte:A.texte,unite:u,note:mes&&!pres(v,m)?'écart de plus de 10 % avec la mesure sur le dessin':A.unite?'':'unité déduite de la mesure'}}
    else p.note=`cote écrite « ${A.texte} » sans unité : choisir l'échelle de la page ou saisir les cotes`}
  else if(A)p.note=`cote écrite « ${A.texte} » d'une autre forme : ignorée`;
  if(!p.origine&&mes)Object.assign(p,{cotes:circ?'Ø'+Math.round(mes[0]):Math.round(mes[0])+'x'+Math.round(mes[1]),origine:'mesure'});
  r.pre=p;if(!r.cotesT)r.cotes=p.cotes}
function dxrApres(){const D=DXI;D.C.forEach((c,i)=>{if(c.statut==='a_confirmer')dxrPre(i)});dxrEch();dxnAssoc();if(el('dxnT'))dxnRows();dxrRender();dxpOver()}
// Contrôle d'une ligne repérée : cotes (mm) → candidat en mm → adaptateur (mêmes contrôles du moteur que les autres lignes)
function dxrEval(r,i,hc,moteur){const D=DXI,c=D.C[i],dm=CPI.nomenclatures.cotes(r.cotes,'mm',true),circ=c.type==='circ';
  const F=circ?['circ']:dxnFormes(dm).filter(f=>f!=='circ');if(r.forme&&!F.includes(r.forme))r.forme='';const fo=r.forme||(dm.etat==='rect'?dxnDef(dm):circ?'circ':'');
  let h=hc;if(String(r.h).trim()!==''){try{h=parseCote(r.h,'mm')}catch(e){h=null}}
  const man=[];
  if(dm.etat!=='rect'&&dm.etat!=='circ')man.push(String(r.cotes).trim()?'cotes illisibles (ex. 650x800 ou Ø250)':'cotes (choisir l\'échelle de la page ou les saisir)');
  else if((dm.etat==='circ')!==circ)man.push(circ?'cotes d\'un cercle (Ø…)':'cotes d\'un rectangle (l × h)');
  else if(!fo)man.push('forme');
  if(!(h>0))man.push(String(r.h).trim()?'hauteur illisible':'hauteur à coffrer');if(!String(D.ch||'').trim())man.push('chantier');
  if(man.length){r.st='ac';r.msg='à compléter : '+man.join(', ');return}
  const cand={id:c.id,type:c.type,statut:'a_confirmer',unite:'mm',source:c.source,geometrie:null,centre:c.centre,
    dims:circ?{D:dm.D}:{L:Math.max(dm.a,dm.b),l:Math.min(dm.a,dm.b),angle:c.dims.angle||0},h:null,manquants:[],remarques:[]};
  const x=CPI.adaptateur.versPlan(cand,{confirme:true,forme:fo,h,unite:'mm',ref:r.ref.trim()},{moteur,modele:D.M[fo]});
  if(!x.ok){r.st='er';r.msg=x.message+(x.messages&&x.messages.length?' : '+x.messages.join(' · '):'');return}
  const p=x.plan;
  if(p.ref&&P.some(q=>chKey(q.ch)===chKey(p.ch)&&ouKey(q.ouv).toLowerCase()===ouKey(p.ouv).toLowerCase()&&String(q.ref||'').toUpperCase()===p.ref)){r.st='er';r.msg=`référence ${p.ref} déjà utilisée dans cet ouvrage`;return}
  x.provenance=dxrProv(i,dm,fo);r.x=x;r.st=x.alertes.length?'wn':'ok';r.msg=x.alertes.join(' · ')}
// Provenance d'un ouvrage repéré sur le dessin (clé origineImport) : page, contour, position et cotes sur la page (pt), échelle,
// cote écrite, cotes proposées et retenues, corrections de l'utilisateur ; rien du PDF au-delà
function dxrProv(i,dm,fo){const D=DXI,c=D.C[i],r=D.R[i],n=c.source.page,e=D.cal[n],p=r.pre||{},q=x=>Math.round(x*100)/100,A=c.annot||{},corrige=[];
  if(r.cotesT&&r.cotes.trim()!==p.cotes)corrige.push('cotes');if(r.forme&&r.forme!==(c.type==='circ'?'circ':dxnDef(dm)))corrige.push('forme');
  if(r.ref.trim().toUpperCase()!==String(A.repere?A.repere.texte:'').toUpperCase().replace(/\s+/g,''))corrige.push('ref');
  const dims={};Object.keys(c.dims).forEach(k=>dims[k]=q(c.dims[k]));
  return{fichier:D.doc.fichier,format:'pdf',type:'detection',page:n,presentation:'Page '+n,id:c.source.id,candidat:c.id,forme_detectee:c.type,
    unite_source:'pt',unite:'mm',vue:c.vue||null,centre:c.centre.map(q),boite:{page:n,x0:q(c.bbox[0]),y0:q(c.bbox[1]),x1:q(c.bbox[2]),y1:q(c.bbox[3]),unite:'pt'},dims_source:dims,zone:c.zone||null,
    echelle:e?Object.assign({mm_par_pt:e.k},e.mode==='points'?{mode:'points',a:e.a.map(q),b:e.b.map(q),distance_pt:q(e.pt),distance_mm:e.mm}:{mode:'echelle',echelle:e.ech,texte:e.texte}):null,
    repere:A.repere?A.repere.texte:null,annotation:A.cotes?A.cotes.texte:null,
    cotes:{origine:r.cotesT?'saisie':p.origine||null,proposees:p.cotes||'',retenues:r.cotes.trim()},choix:{forme:fo,ref:r.ref.trim().toUpperCase()},
    corrige,a_verifier:c.remarques.slice(),h_saisie:true}}

// Panneau « échelle » de la page affichée : état, calibration par 2 points, échelle écrite sur la page (1/50…), effacement
function dxrEchelles(n){const R=new Map();DXI.doc.textes.forEach(t=>{if(t.page!==n)return;const m=t.texte.match(/[ée]ch(?:elle)?\.?\s*:?\s*1\s*[\/:]\s*(\d{1,4})(?!\d)/i);if(m&&+m[1]>0&&!R.has(+m[1]))R.set(+m[1],t.texte)});return[...R]}
function dxrEch(msg){const D=DXI,z=el('dxrE');if(!D||!z)return;const n=D.page,e=D.cal[n],S=dxrEchelles(n);
  z.innerHTML=`<b>Échelle de la page ${n}</b> : `+(e?`1 pt = ${String(Math.round(e.k*100)/100).replace('.',',')} mm (≈ 1/${Math.round(e.k/DXR_PT)} sur une feuille à taille réelle) · `
      +(e.mode==='points'?`${dxiNum(e.mm)} mm entre 2 points choisis`:`1/${e.ech} lue sur la page`)
    :'<span style="color:var(--acct)">non définie</span> : les contours n\'ont pas de cotes en mm (seules les cotes écrites à côté sont reprises).')
    +`<div class="dxp-b" style="margin-top:4px"><button class="btn bs bo${D.calm?' bpr':''}" id="dxrCal" onclick="dxrCal()" aria-pressed="${!!D.calm}">📏 ${D.calm?'Annuler la mesure':'Calibrer : 2 points + distance'}</button>`
    +S.map(([v,t])=>`<button class="btn bs bo" onclick="dxrEchLue(${v})" title="${esc('lu sur la page : « '+t+' » ; valable si le PDF est à la taille réelle de la feuille')}">Échelle 1/${v} lue sur la page</button>`).join('')
    +(e?'<button class="btn bs bo" onclick="dxrEchEff()">Effacer l\'échelle</button>':'')+'</div>'
    +(D.calm?`<div style="color:var(--acct);margin-top:4px">${esc(msg||(D.calm.pts.length?'Cliquer le 2e point.':'Cliquer le 1er point d\'une distance connue (accroché au sommet de trait le plus proche).'))}</div>`:'')}
async function dxrCal(){const D=DXI;if(!D)return;if(D.calm){D.calm=null;el('dxpO').classList.remove('cm');dxrEch();return dxpOver()}
  dxpZm(false);try{await dxrGeo(D.page)}catch(e){}D.calm={page:D.page,pts:[]};el('dxpO').classList.add('cm');dxrEch()}
// point cliqué, accroché au sommet de trait (ou de contour repéré) le plus proche à moins de 8 px
function dxrPt(e){const D=DXI,m=D.calm;e.preventDefault();if(m.page!==D.page){D.calm=null;return dxrEch()}
  let p=dxpPt(e),best=8/D.k;const g=D.GP[D.page];
  if(g)g.segments.forEach(s=>[s.a,s.b].forEach(q=>{const d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<best){best=d;p=q.slice()}}));
  m.pts.push(p);dxpOver();if(m.pts.length<2)return dxrEch();
  const [a,b]=m.pts,d=Math.hypot(b[0]-a[0],b[1]-a[1]);D.calm=null;el('dxpO').classList.remove('cm');dxrEch();
  if(!(d>1)){dxpOver();return dxrEch('Points confondus : recommencer.')}
  uiPrompt(`Distance réelle entre les deux points choisis (${dxiNum(d)} pt sur la page), en mm :`,'',v=>{let mm=null;try{mm=parseCote(v,'mm')}catch(x){}
    if(!(mm>0))return uiAlert('Distance illisible : saisir un nombre de millimètres (ex. 1200).');
    D.cal[m.page]={k:mm/d,mode:'points',a,b,pt:d,mm};dxrApres()},{ok:'Appliquer l\'échelle'});dxpOver()}
function dxrEchLue(v){const D=DXI,t=(dxrEchelles(D.page).find(x=>x[0]===v)||[])[1]||'';D.cal[D.page]={k:v*DXR_PT,mode:'echelle',ech:v,texte:t};dxrApres()}
function dxrEchEff(){const D=DXI;delete D.cal[D.page];dxrApres()}

// Superposition : contours repérés de la page (violet ; vert : coché ; tirets verts : rattaché à une ligne de nomenclature ;
// tirets orange : proposés pour la ligne de nomenclature choisie) et points de la calibration
function dxrOver(H,f){const D=DXI;let h='';const P=D.nsel>=0&&D.NL[D.nsel]?new Set(dxnAS(D.NL[D.nsel].L).options.map(o=>o.c)):new Set();
  // vues techniques de la page : cadre bleu en tirets et identifiant
  ((D.VU[D.page]||{}).vues||[]).forEach(v=>{const r=v.region;h+=`<rect class="vu" x="${r[0]}" y="${H-r[3]}" width="${r[2]-r[0]}" height="${r[3]-r[1]}"><title>${esc(v.id+(v.titre?' « '+v.titre+' »':' (sans titre)'))}</title></rect><text class="vl" x="${r[0]+2}" y="${H-r[3]+f}" font-size="${f}">${esc(v.id+' '+v.libelle+(v.partie?' '+v.partie:''))}</text>`});
  // localisations (repères) de la ligne de nomenclature choisie : cadre orange, lignes de rappel suivies en tirets ; repère demandé : surligné
  if(D.nsel>=0&&D.NL[D.nsel])(dxnAS(D.NL[D.nsel].L).occurrences||[]).forEach((o,j)=>{if(o.page!==D.page)return;const w=o.box?o.box.x1-o.box.x0:(o.h||4)*2,m=(o.h||4)*0.4,x0=o.x-w/2-m,y1=o.y+(o.h||4)/2+m;
    h+=`<rect class="${D.hlo&&D.hlo.k===D.nsel&&D.hlo.j===j?'hl':'oc'}" x="${x0}" y="${H-y1}" width="${w+2*m}" height="${(o.h||4)+2*m}"><title>${esc('repère « '+o.texte+' »'+(o.source==='ocr'?' (OCR, confiance '+o.conf+' %)':''))}</title></rect>`
      +(o.rappels||[]).map(q=>`<line class="ot" x1="${o.x}" y1="${H-o.y}" x2="${q[0]}" y2="${H-q[1]}"/>`).join('')});
  D.C.forEach((c,i)=>{if(c.source.page!==D.page||c.statut!=='a_confirmer')return;const g=c.geometrie,lk=D.lk.has(i),
      cl=`rs${i===D.rsel?' on':''}${D.R[i].conf?' cf':''}${lk?' lk':''}${P.has(i)?' pr':''}`,t=`<title>${esc(c.id+' · '+dxiDims(c)+(lk?' · rattaché à la nomenclature':''))}</title>`,a=`class="${cl}" data-r="${i}"${lk?'':` onclick="dxrSel(${i},1)"`}`;
    h+=(g.type==='cercle'?`<circle ${a} cx="${g.centre[0]}" cy="${H-g.centre[1]}" r="${g.r}">${t}</circle>`:`<polygon ${a} points="${g.points.map(p=>p[0]+','+(H-p[1])).join(' ')}">${t}</polygon>`)
      +`<text class="rl" x="${c.bbox[0]}" y="${H-c.bbox[3]-1}" font-size="${f*0.8}">${esc(c.id.replace(/^P\d+-/,''))}</text>`});
  const e=D.cal[D.page],Q=D.calm&&D.calm.page===D.page?D.calm.pts:e&&e.mode==='points'?[e.a,e.b]:[],rr=f*0.35;
  if(Q.length===2)h+=`<line class="cl" x1="${Q[0][0]}" y1="${H-Q[0][1]}" x2="${Q[1][0]}" y2="${H-Q[1][1]}"/>`;
  Q.forEach(q=>h+=`<circle class="ca" cx="${q[0]}" cy="${H-q[1]}" r="${rr}"/>`);
  return h}
function dxrSel(i,fromSvg){const D=DXI;if(!D||D.zm||D.calm||!D.C[i])return;D.rsel=i;
  document.querySelectorAll('#dxrT tr[data-r]').forEach(t=>t.classList.toggle('on',+t.dataset.r===i));
  if(fromSvg){const t=document.querySelector(`#dxrT tr[data-r="${i}"]`);if(t)t.scrollIntoView({block:'nearest'});return dxpOver()}
  if(D.C[i].source.page!==D.page){D.page=D.C[i].source.page;D.scroll=false;dxpPage()}else dxpOver();
  const s=el('dxpO')&&el('dxpO').querySelector('.rs.on');if(s)s.scrollIntoView({block:'nearest',inline:'nearest'})}

// Tableau des réservations repérées (toutes pages) ; contours rattachés à la nomenclature : dans l'onglet Nomenclature
function dxrRender(){const D=DXI,Z=el('dxrZ');if(!Z||!D)return;if(!D.C.length){Z.innerHTML='';return}
  // avec une nomenclature : formes hors nomenclature en section secondaire repliée (rien n'est supprimé) ; sans : liste principale
  const nl=D.NL.length,V=dxrVues(),ouv=el('dxrH')&&el('dxrH').open;   // section ouverte par l'utilisateur : le reste après un nouveau rendu
  Z.innerHTML=`<fieldset class="dxo"><legend>${nl?'Formes du dessin hors nomenclature':'Réservations repérées sur le dessin'}</legend>
    ${V.length?`<div class="mu" style="margin-bottom:4px" id="dxrVu"><b>${V.length} vue(s) reconnue(s)</b> (cadres bleus sur l'aperçu) : ${V.map(v=>`<span title="${esc((v.titre?'« '+v.titre+' »':'sans titre')+' · confiance '+v.confiance+(v.motifs.length?' · '+v.motifs.join(' ; '):'')+(v.echelle?' · échelle 1/'+v.echelle.valeur:''))}">${esc(v.id)} ${esc(v.libelle)}${v.partie?' '+esc(v.partie):''}</span>`).join(' · ')}</div>`:''}
    <${nl?'details id="dxrH"'+(ouv?' open':''):'div'}>${nl?'<summary id="dxrHs"></summary>':''}<div id="dxrS" style="margin-bottom:4px"></div>
    <div class="mu" style="margin-bottom:6px">${nl?'Contours non rattachés à une ligne de la nomenclature (les réservations du tableau sont dans l\'onglet Nomenclature), avec la raison de leur proposition ; parasites probables en fin de liste. ':''}Formes du dessin, pas encore des réservations : vérifier chaque ligne sur l'aperçu (clic sur une ligne : contour en orange),
    corriger forme, cotes, hauteur et référence, puis cocher. Cotes proposées : cote écrite à côté du contour, ou mesure à l'échelle de la page (à vérifier).</div>
    <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap"><button class="btn bs bo" onclick="dxrAll(false)">Tout décocher</button></div>
    <div class="dxi-t"><table class="ser" id="dxrT"><thead><tr><th>Créer</th><th>#</th><th>Page · vue</th><th>Repère</th><th>Raison</th><th>Forme</th><th>Cotes (mm)</th><th>Origine des cotes</th><th>h (mm)</th><th>Réf.</th><th>État</th></tr></thead><tbody></tbody></table></div>
    </${nl?'details':'div'}>
    <details id="dxrNP"><summary></summary><table class="ser"><thead><tr><th>#</th><th>Page</th><th>Forme</th><th>Dessin</th><th>Raison</th></tr></thead><tbody></tbody></table></details></fieldset>`;
  dxrRows();dxiUpd()}
// Classement d'un contour hors nomenclature (à examiner ou parasite probable, avec sa raison) ; à examiner en tête
const dxrCl=i=>CPI.vues.classer(DXI.C[i],DXI.C[i].vue?dxrVueDe(DXI.C[i].vue):null,new Set(DXI.NL.map(({L})=>CPI.nomenclatures.cleRep(L.repere||'')).filter(Boolean)));
const DXR_NIV={examiner:0,representation:1,parasite:2};
const dxrVis=()=>{const I=DXI.C.map((c,i)=>i).filter(i=>DXI.C[i].statut==='a_confirmer'&&!DXI.lk.has(i)),n=new Map(I.map(i=>[i,DXR_NIV[dxrCl(i).niveau]]));return I.sort((a,b)=>n.get(a)-n.get(b)||a-b)};
function dxrRows(){const D=DXI,T=el('dxrT');if(!T)return;const V=dxrVis(),np=D.C.map((c,i)=>i).filter(i=>D.C[i].statut!=='a_confirmer');T.dataset.v=V.join();
  T.tBodies[0].innerHTML=V.length?V.map(i=>{const c=D.C[i],r=D.R[i],A=c.annot||{},cl=dxrCl(i);
    return `<tr data-r="${i}" onclick="dxrSel(${i})"${i===D.rsel?' class="on"':''}><td><input type="checkbox" data-k="conf"${r.conf?' checked':''} aria-label="Créer ${esc(c.id)}" onchange="DXI.R[${i}].conf=this.checked;dxiUpd()"></td>
      <td>${esc(c.id)}</td><td>${c.source.page}${c.vue?' · '+esc(c.vue):''}</td><td>${esc(A.repere?A.repere.texte:'—')}</td><td class="mu">${esc(cl.raison)}</td><td><select class="fi" data-k="forme" onchange="DXI.R[${i}].forme=this.value;dxiUpd()"></select></td>
      <td><input class="fi" data-k="cotes" style="width:96px" value="${esc(r.cotes)}" placeholder="${esc(A.cotes?A.cotes.texte:'à saisir')}" oninput="DXI.R[${i}].cotes=this.value;DXI.R[${i}].cotesT=true;dxiUpd()">
        <div class="mu">dessin : ${esc(dxiDims(c))}</div></td><td class="og"></td>
      <td><input class="fi" data-k="h" style="width:62px" value="${esc(r.h)}" placeholder="${esc(D.hCom.trim()||'à saisir')}" oninput="DXI.R[${i}].h=this.value;dxiUpd()"></td>
      <td><input class="fi" data-k="ref" style="width:72px" value="${esc(r.ref)}" placeholder="auto" oninput="DXI.R[${i}].ref=this.value;dxiUpd()"></td><td class="st"></td></tr>`}).join('')
    :`<tr><td colspan="11" style="color:var(--muted)">Aucune réservation proposée${D.lk.size?' (contours rattachés à la nomenclature : onglet Nomenclature)':''}.</td></tr>`;
  const N=el('dxrNP');N.querySelector('summary').textContent=`Contours écartés, non exploitables (${np.length})`;
  N.querySelector('tbody').innerHTML=np.slice(0,DXI_NP).map(i=>{const c=D.C[i];return `<tr class="np"><td>${esc(c.id)}</td><td>${c.source.page}</td><td>${c.type==='circ'?'cercle':'rectangle'}</td><td>${esc(dxiDims(c))}</td><td>${esc(c.remarques.join(' · '))}</td></tr>`}).join('')
    +(np.length>DXI_NP?`<tr class="np"><td colspan="5">… et ${np.length-DXI_NP} autre(s)</td></tr>`:'')}
function dxrAll(on){const D=DXI;dxrVis().forEach(i=>D.R[i].conf=on);document.querySelectorAll('#dxrT [data-k=conf]').forEach(e=>e.checked=on);dxiUpd()}
// États lisibles : repérée (prête, sans doute) · à confirmer (prête, doute ou cotes mesurées) · à compléter · refusée ; non exploitable : liste à part
function dxrUpd(){const D=DXI,T=el('dxrT');if(!T)return;if(T.dataset.v!==dxrVis().join())dxrRows();
  const poss={};D.NL.forEach(({L})=>dxnAS(L).options.forEach(o=>{(poss[o.c]=poss[o.c]||[]).push(L.repere||L.id)}));const n={rep:0,conf:0,ac:0,er:0};
  document.querySelectorAll('#dxrT tr[data-r]').forEach(t=>{const i=+t.dataset.r,c=D.C[i],r=D.R[i],p=r.pre||{},dm=CPI.nomenclatures.cotes(r.cotes,'mm',true);
    const F=c.type==='circ'?['circ']:dxnFormes(dm).filter(f=>f!=='circ'),sf=t.querySelector('[data-k=forme]'),key=F.join();
    if(sf.dataset.f!==key){sf.dataset.f=key;sf.innerHTML=F.map(f=>`<option value="${f}">${f?esc(fmLb(f))+(/_fond$/.test(f)?' (choix explicite)':''):'— à choisir —'}</option>`).join('')}
    sf.value=r.forme||(c.type==='circ'?'circ':dm.etat==='rect'?dxnDef(dm):'');
    const ci=t.querySelector('[data-k=cotes]');if(document.activeElement!==ci&&ci.value!==r.cotes)ci.value=r.cotes;
    t.querySelector('.og').innerHTML=esc(r.cotesT&&r.cotes.trim()!==(p.cotes||'')?'saisie':p.origine==='annotation'?`cote écrite « ${p.texte} »`:p.origine==='mesure'?`mesure à l'échelle (p. ${c.source.page})`:'—')
      +(p.note?`<div class="av" style="color:var(--acct);font-size:11px">${esc(p.note)}</div>`:'');
    const doute=c.remarques.concat(poss[i]?[`correspond peut-être à la ligne ${poss[i].join(', ')} de la nomenclature (à rattacher dans l'onglet Nomenclature pour éviter un doublon)`]:[])
      .concat(p.origine==='mesure'&&!(r.cotesT&&r.cotes.trim()!==p.cotes)?['cotes mesurées sur le dessin']:[]),pr=r.st==='ok'||r.st==='wn';
    const et=r.st==='ac'?'ac':r.st==='er'?'er':doute.length||r.st==='wn'?'conf':'rep';n[et]++;
    const s=t.querySelector('.st');s.className='st '+(et==='rep'?'ok':et==='er'?'er':'wn');
    s.innerHTML=esc(et==='rep'?'✓ repérée':et==='conf'?'≈ à confirmer':et==='ac'?'… '+r.msg:'⛔ non créé — '+r.msg)+(pr&&(doute.length||r.msg)?`<div class="mu">${esc(doute.concat(r.msg?[r.msg]:[]).join(' · '))}</div>`:'')});
  const V=dxrVis(),cf=V.filter(i=>D.R[i].conf).length,nE=D.C.filter(c=>c.statut!=='a_confirmer').length;
  const nv={examiner:0,representation:0,parasite:0};V.forEach(i=>nv[dxrCl(i).niveau]++);
  const cl=`${nv.examiner} à examiner, ${nv.representation} représentation(s) d'une ligne du tableau, ${nv.parasite} parasite(s) probable(s)`;
  if(el('dxrHs'))el('dxrHs').textContent=`Formes hors nomenclature (${V.length}) : ${cl} · ${V.filter(i=>D.R[i].conf).length} cochée(s)`;
  el('dxrS').innerHTML=`<b>${V.length} réservation(s) proposée(s)</b> (${cl}) : ${n.rep} repérée(s), ${n.conf} à confirmer, ${n.ac} à compléter${n.er?`, ${n.er} refusée(s)`:''} · ${nE} non exploitable(s)`
    +(D.lk.size?` · ${D.lk.size} rattachée(s) à la nomenclature`:'')+` · ${cf} cochée(s) · <b>${dxiReady().length} à créer</b>`;
  dxpOver()}
