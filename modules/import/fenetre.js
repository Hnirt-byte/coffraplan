// CoffraPlan — module d'import de plans, composant D : fenêtre « Importer un plan DXF » (dans l'appli).
// Seul composant lié à l'appli : il appelle ses fonctions (modal, coll, setForm, P, svP, nextRef, toast…) au moment de
// l'action, jamais au chargement. Chaîne : fichier → A (lecteur + dxf.js) → B (détecteur) → choix de l'utilisateur ligne
// par ligne → C (adaptateur : contrôles du moteur) → ajout à P comme serCreate. Rien n'est créé avant « Créer les ouvrages
// sélectionnés ». Provenance gardée dans le plan : clé optionnelle origineImport (métadonnée, jamais lue par le moteur).
// Nomenclatures de réservations (nomenclatures.js, fonctions dxn*) : vue par défaut quand le DXF en contient ; toutes les
// lignes proposées, aucune cochée d'office ; les géométries rattachées sont retirées de la vue « Géométries du dessin ».
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
@media (max-width:820px){#dxi .dxi-w,#dxi .dxi-g{grid-template-columns:1fr}}
</style>`)}

function dxiOpen(){dxiCss();modal(`<div class="cd" style="margin:0" id="dxi"><div class="ct">📥 Importer un plan DXF</div>
  <div class="hint">Réservations lues dans le DXF : nomenclatures de réservations (tableaux de l'espace Objet ou des présentations), polylignes
  fermées rectangulaires (rectangles, carrés) et cercles. Chaque réservation est à confirmer ; aucun ouvrage n'est créé avant « Créer les ouvrages
  sélectionnés ». Les projets et plans déjà enregistrés ne sont pas modifiés.</div>
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><label class="btn bs bo" style="cursor:pointer;display:inline-flex;align-items:center">📂 Choisir un fichier .dxf
  <input type="file" id="dxiF" accept=".dxf" hidden onchange="dxiFile(this.files[0]);this.value=''"></label><span id="dxiN" style="font-size:12px"></span></div>
  <div id="dxiZ"></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:10px"><button class="btn bs bo" onclick="closeModal()">Fermer</button>
  <button class="btn bs bpr" id="dxiGo" disabled onclick="dxiCreate()">Créer les ouvrages sélectionnés (0)</button></div></div>`,true);
  if(DXI)dxiRender()}

// Lecture : UTF-8 strict (R2007 et suivants), sinon CP-1252 (R12 à R2004)
async function dxiFile(f){if(!f)return;let txt;
  try{const b=await f.arrayBuffer();try{txt=new TextDecoder('utf-8',{fatal:true}).decode(b)}catch(e){txt=new TextDecoder('windows-1252').decode(b)}}
  catch(e){txt=null}
  const lu=txt==null?{ok:false,message:'fichier illisible'}:CPI.lecteur.lirePlan({format:'dxf',nom:f.name,contenu:txt});
  if(!lu.ok){DXI=null;if(!el('dxiZ'))return;el('dxiN').innerHTML=`<b>${esc(f.name)}</b>`;
    el('dxiZ').innerHTML=`<div class="hint" style="margin:10px 0 0;border-left-color:var(--red)">⛔ Fichier non lu : ${esc(lu.message)}${(lu.erreurs||[]).length?' — '+esc(lu.erreurs.slice(0,5).join(' · ')):''}</div>`;dxiBtn();return}
  const doc=lu.document,C=CPI.detecteur.detecter(doc).candidats,cur=coll(),lay={},NA=CPI.nomenclatures.analyser(doc);
  C.forEach(c=>{lay[c.source.calque]=true});
  const NL=NA.nomenclatures.flatMap(N=>N.lignes.map(L=>({N,L})));
  DXI={nom:f.name,doc,C,R:C.map(()=>({conf:false,forme:'',h:'',ref:''})),lay,u:doc.unite||'',ch:cur.ch,ouv:cur.ouv,ind:'',hCom:'',sel:-1,M:null,
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

function dxiRender(){const D=DXI,Z=el('dxiZ');if(!Z||!D)return;const d=D.doc;
  el('dxiN').innerHTML=`<b>${esc(D.nom)}</b>${d.version?' · DXF '+esc(d.version):''} · unité : ${d.unite?`<b>${d.unite}</b> (donnée par le fichier)`:'<b style="color:var(--redt)">absente du fichier</b>'}`;
  const L=[...new Set(D.C.map(c=>c.source.calque))].sort(_cmp),nb=k=>D.C.filter(c=>c.source.calque===k&&c.statut==='a_confirmer').length,
    NA=D.NA,E=NA.ecartes.map(e=>`${esc(e.id)}${e.titre?' « '+esc(e.titre.replace(/\n/g,' '))+' »':''} (${e.espace==='objet'?'espace Objet':'présentation « '+esc(e.presentation||'?')+' »'}, ${e.nLignes} ligne(s)) : ${esc(e.raison)}`).concat(NA.signalements.map(esc));
  Z.innerHTML=(d.unite?'':`<div class="dxi-u">⚠ Le fichier ne donne pas son unité ($INSUNITS absent ou nul, toujours le cas en R12). Unité des cotes du dessin :
    <select class="fi" id="dxiU" onchange="DXI.u=this.value;dxnAssoc();dxiRows()"><option value="">— choisir —</option>${['mm','cm','m'].map(u=>`<option${D.u===u?' selected':''}>${u}</option>`).join('')}</select></div>`)
  +`<div class="dxi-g"><div class="fd"><label>Chantier</label><input class="fi" id="dxiCh" value="${esc(D.ch)}" onchange="DXI.ch=this.value;DXI.M=null;dxiUpd()"></div>
    <div class="fd"><label>Ouvrage</label><input class="fi" id="dxiOuv" value="${esc(D.ouv)}" onchange="DXI.ouv=this.value;DXI.M=null;dxiUpd()"></div>
    <div class="fd"><label>Indice du plan source</label><input class="fi" id="dxiInd" value="${esc(D.ind)}" placeholder="ex. B" oninput="DXI.ind=this.value"></div>
    <div class="fd"><label>Hauteur commune (mm)</label><input class="fi" id="dxiH" value="${esc(D.hCom)}" placeholder="facultative" oninput="DXI.hCom=this.value;dxiHph();dxiUpd()"></div></div>
  ${E.length?`<details class="mu" id="dxiE" style="margin-top:8px"><summary>Tableaux non retenus et limites de lecture (${E.length})</summary><ul style="margin:4px 0">${E.map(x=>'<li>'+x+'</li>').join('')}</ul>
    <div>Ces tableaux sont signalés, pas utilisés : leurs lignes ne deviennent pas des réservations.</div></details>`:''}
  ${D.NL.length?`<div class="dxi-tab" role="tablist"><button id="dxiTabN" role="tab" onclick="dxiVue('n')">Nomenclature des réservations (${D.NL.length})</button>
    <button id="dxiTabG" role="tab" onclick="dxiVue('g')">Géométries du dessin</button></div>${dxnPane()}`:''}
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
  dxiRows();if(D.NL.length){dxnRows();dxiVue(D.vue)}}
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
  svP();profFromPlans(P.slice(-N.length));profLists();rnL();updBtn();closeModal();const nom=D.nom;DXI=null;
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
  D.AS=CPI.nomenclatures.associer(D.NA.nomenclatures,D.C,D.doc,{uniteDessin:D.u,unites:D.NU,exclus:D.NA.ecartes.flatMap(e=>e.ids)});
  D.NL.forEach(({L},k)=>{const r=D.NR[k],a=D.AS[L.id];if(!r.cotesT)r.cotes=dxnPre(k);if(!r.geoT)r.geo=a.statut==='trouvee'?String(a.options[0].c):''});dxnLinks()}
function dxnLinks(){DXI.lk=new Set(DXI.NR.filter(r=>r.geo!=='').map(r=>+r.geo))}
function dxnPane(){const D=DXI,NA=D.NA;
  return `<div id="dxiPN"><div class="dxi-s" id="dxnS"></div>${NA.nomenclatures.map(N=>{const cs=N.colonnes.map(c=>`${esc((c.titre||'(sans titre)').replace(/\n/g,' '))} → ${CPI.nomenclatures.LIB[c.cle]}`).join(' · '),
      sansU=N.lignes.some(L=>L.dims&&!L.dims.unite)&&!N.unite;
    return `<div class="dxn-i"><b>Tableau ${esc(N.id)}</b>${N.titre?' « '+esc(N.titre.replace(/\n/g,' '))+' »':''} · ${N.espace==='objet'?'espace Objet':'présentation « '+esc(N.presentation||'?')+' »'}
      · calque(s) ${esc(N.calques.join(', '))} · <b>${N.lignes.length} ligne(s)</b> · lecture : <b>${esc(N.qualite.niveau)}</b> (${esc(N.qualite.motifs.join(' ; '))})
      ${sansU?` · <span style="color:var(--acct)">unité des cotes non indiquée :</span> <select class="fi" data-nu="${esc(N.id)}" onchange="DXI.NU[this.dataset.nu]=this.value;dxnAssoc();dxnRows()"><option value="">— choisir —</option>${['mm','cm','m'].map(u=>`<option${D.NU[N.id]===u?' selected':''}>${u}</option>`).join('')}</select>`:N.unite?` · cotes en ${N.unite} (en-tête)`:''}
      <div class="mu">Colonnes : ${cs}</div></div>`}).join('')}
    <div class="hint" style="margin:6px 0">Toutes les lignes des tableaux sont proposées, quels que soient le type, le lot ou le fournisseur : rien n'est coché d'office.
    Cotes en mm (ex. 650x800 ou Ø250 ; tableau : ouverture l × h). Niveau et angle = position de la réservation : ils ne donnent ni la hauteur à coffrer ni la rotation du coffrage.</div>
    <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap"><button class="btn bs bo" onclick="dxnAll(true)">☑ Tout sélectionner</button><button class="btn bs bo" onclick="dxnAll(false)">Tout décocher</button>
    <button class="btn bs bo" onclick="dxnRefs(true)" title="Référence CoffraPlan = repère du tableau">Références du tableau</button><button class="btn bs bo" onclick="dxnRefs(false)" title="Références vides : numérotation automatique CoffraPlan">Références CoffraPlan automatiques</button></div>
    <div class="dxi-t"><table class="ser" id="dxnT"><thead><tr><th>Créer</th><th>Repère</th><th>Désignation</th><th>Ouverture · réseau</th><th>Niveau · angle</th><th>Forme</th><th>Cotes (mm)</th><th>h (mm)</th><th>Réf.</th><th>Géométrie du dessin</th><th>Statut</th></tr></thead><tbody></tbody></table></div>
    <svg id="dxnV" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Correspondances possibles dans le dessin"></svg>
    <div class="hint" style="margin:6px 0 0">Schéma des géométries proposées pour les lignes (espace Objet) ; points : repères trouvés dans le dessin. Ligne sélectionnée : propositions en orange, un clic en choisit une.</div></div>`}
function dxiVue(v){const D=DXI;if(!D||!el('dxiPN'))return;D.vue=v;el('dxiPN').style.display=v==='n'?'':'none';el('dxiPG').style.display=v==='g'?'':'none';
  el('dxiTabN').classList.toggle('on',v==='n');el('dxiTabG').classList.toggle('on',v==='g');el('dxiTabN').setAttribute('aria-selected',v==='n');el('dxiTabG').setAttribute('aria-selected',v==='g');
  if(v==='g')dxiRows()}
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
      <td><select class="fi" data-k="geo" style="max-width:190px" onchange="dxnGeo(${k},this.value)"></select><div class="gs"></div></td><td class="st"></td></tr>`}).join('');
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
function dxnProv(k){const D=DXI,{N,L}=D.NL[k],r=D.NR[k],a=D.AS[L.id],g=r.geo!==''?D.C[+r.geo]:null,u=dxnU(N,L);
  return CPI.nomenclatures.provenance(N,L,{forme:r.x.plan.forme,cotes:r.cotes,dims:dxnDims(r),ref:r.ref.trim().toUpperCase(),uniteTableau:u||null,
    uniteChoisie:!!(u&&!(L.dims&&L.dims.unite)&&!N.unite),geo:g?{c:g,statut:!r.geoT&&a.statut==='trouvee'?'trouvee':'choisie'}:null})}
// Statuts, formes possibles, géométries proposées, bilan (sans reconstruire la liste : garde la saisie en cours)
function dxnUpd(){const D=DXI;if(!D||!el('dxnT'))return;const lb={ok:'✓ prêt',wn:'⚠ prêt — ',ac:'… ',er:'⛔ non créé — '};
  document.querySelectorAll('#dxnT tr[data-n]').forEach(t=>{const k=+t.dataset.n,r=D.NR[k],{L}=D.NL[k],a=D.AS[L.id],dm=dxnDims(r),F=dxnFormes(dm);
    if(r.forme&&!F.includes(r.forme))r.forme='';
    const sf=t.querySelector('[data-k=forme]'),fo=r.forme||dxnDef(dm),key=F.join();
    if(sf.dataset.f!==key){sf.dataset.f=key;sf.innerHTML=F.map(f=>`<option value="${f}">${f?esc(fmLb(f))+(/_fond$/.test(f)?' (choix explicite)':''):'— à choisir —'}</option>`).join('')}sf.value=fo;
    const sg=t.querySelector('[data-k=geo]'),O=a.options.slice(0,DXN_OPT),gk=O.map(o=>o.c).join()+'|'+D.u;
    if(sg.dataset.g!==gk){sg.dataset.g=gk;sg.innerHTML=`<option value="">— aucune —</option>`+O.map(o=>{const c=D.C[o.c];
      return `<option value="${o.c}">${esc(c.id+' · '+dxiDims(c)+' · '+c.source.calque+(o.via==='cotes'?' · mêmes cotes':o.cotes==='diff'?' · cotes différentes':''))}</option>`}).join('')
      +(a.options.length>DXN_OPT?`<option disabled>… et ${a.options.length-DXN_OPT} autre(s)</option>`:'')}
    sg.value=r.geo;const gs=t.querySelector('.gs');gs.textContent=r.geo!==''&&r.geoT?DXN_ST.choisie:DXN_ST[a.statut];gs.title=a.note;
    gs.style.color=r.geo!==''||a.statut==='trouvee'?'var(--okt)':a.statut==='absente'?'var(--muted)':'var(--acct)';
    const s=t.querySelector('.st');s.className='st '+(r.st==='ac'?'wn':r.st);
    s.innerHTML=esc(lb[r.st]+(r.st==='ok'?'':r.msg))+(L.a_verifier.length?`<div class="av">à vérifier : ${esc(L.a_verifier.join(' ; '))}</div>`:'')+(a.note?`<div class="mu">${esc(a.note)}</div>`:'')});
  const n={trouvee:0,probable:0,multiple:0,absente:0};D.NL.forEach(({L})=>n[D.AS[L.id].statut]++);
  const NN=D.NA.nomenclatures.length,cf=D.NR.filter(r=>r.conf).length;
  el('dxnS').innerHTML=`<b>${D.NL.length} ligne(s) de nomenclature</b> dans ${NN} tableau${NN>1?'x':''} · géométries : ${n.trouvee} trouvée(s), ${n.probable} probable(s), ${n.multiple} à choisir parmi plusieurs, ${n.absente} non retrouvée(s)
    · ${cf} sélectionnée(s) · <b>${dxnReady().length} à créer</b>`;
  dxnSvg()}
// Schéma : géométries proposées (espace Objet, repère du DXF, Y vers le haut) et repères trouvés ; ligne sélectionnée en évidence
function dxnSvg(){const D=DXI,S=el('dxnV');if(!S)return;const G=new Set(),pts=[],R=[],k=D.nsel,a=k>=0?D.AS[D.NL[k].L.id]:null,on=new Set(a?a.options.map(o=>o.c):[]);
  D.NL.forEach(({L})=>{const x=D.AS[L.id];x.options.slice(0,DXN_OPT).forEach(o=>G.add(o.c));x.reperes.forEach(p=>R.push([p,x===a]))});
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
