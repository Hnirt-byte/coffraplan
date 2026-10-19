// CoffraPlan — module d'import de plans, composant D : fenêtre « Importer un plan DXF » (dans l'appli).
// Seul composant lié à l'appli : il appelle ses fonctions (modal, coll, setForm, P, svP, nextRef, toast…) au moment de
// l'action, jamais au chargement. Chaîne : fichier → A (lecteur + dxf.js) → B (détecteur) → choix de l'utilisateur ligne
// par ligne → C (adaptateur : contrôles du moteur) → ajout à P comme serCreate. Rien n'est créé avant « Créer les ouvrages
// sélectionnés ». Provenance gardée dans le plan : clé optionnelle origineImport (métadonnée, jamais lue par le moteur).
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
@media (max-width:820px){#dxi .dxi-w,#dxi .dxi-g{grid-template-columns:1fr}}
</style>`)}

function dxiOpen(){dxiCss();modal(`<div class="cd" style="margin:0" id="dxi"><div class="ct">📥 Importer un plan DXF</div>
  <div class="hint">Réservations lues dans le DXF : polylignes fermées rectangulaires (rectangles, carrés) et cercles. Chaque réservation est à
  confirmer ; aucun ouvrage n'est créé avant « Créer les ouvrages sélectionnés ». Les projets et plans déjà enregistrés ne sont pas modifiés.</div>
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
  const doc=lu.document,C=CPI.detecteur.detecter(doc).candidats,cur=coll(),lay={};
  C.forEach(c=>{lay[c.source.calque]=true});
  DXI={nom:f.name,doc,C,R:C.map(()=>({conf:false,forme:'',h:'',ref:''})),lay,u:doc.unite||'',ch:cur.ch,ouv:cur.ouv,ind:'',hCom:'',sel:-1,M:null};
  if(el('dxiZ'))dxiRender()}

// Plans modèles (chantier, CP, options) pour chaque forme visée : même méthode que serAnalyse, formulaire rétabli ensuite
function dxiModels(){const D=DXI,tpl=coll(),tplS=formSnap(),ei=EI,ho=_hisOff,M={},ch=String(D.ch||'').trim().toUpperCase(),ouv=String(D.ouv||'').trim();delete tpl.date;
  _hisOff=true;try{_loading=true;try{el('iCh').value=ch;el('iOuv').value=ouv}finally{_loading=false}
    ['rect','carre','rect_fond','carre_fond','circ'].forEach(f=>{let d;
      if(f===tpl.forme)d=JSON.parse(JSON.stringify(tpl));else{_loading=true;try{el('iForme').value=f;updF()}finally{_loading=false}applyProf(true);d=coll();delete d.date}
      M[f]=Object.assign(d,{ch,ouv})})}
  finally{_loading=true;try{setForm(JSON.parse(tplS))}finally{_loading=false}EI=ei;_hisOff=ho;syncVis()}
  D.M=M}
const dxiVis=i=>DXI.lay[DXI.C[i].source.calque];
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
  // références saisies en double dans le lot (lignes confirmées)
  const n={};D.R.forEach((r,i)=>{if(r.x&&r.conf&&dxiVis(i)&&r.x.plan.ref)n[r.x.plan.ref]=(n[r.x.plan.ref]||0)+1});
  D.R.forEach((r,i)=>{if(r.x&&r.conf&&dxiVis(i)&&n[r.x.plan.ref]>1){r.x=null;r.st='er';r.msg='référence en double dans l\'import'}})}
const dxiReady=()=>DXI?DXI.R.map((r,i)=>i).filter(i=>DXI.R[i].conf&&DXI.R[i].x&&dxiVis(i)):[];
function dxiBtn(){const b=el('dxiGo');if(!b)return;const n=dxiReady().length;b.disabled=!n;b.textContent=`Créer les ouvrages sélectionnés (${n})`}

function dxiRender(){const D=DXI,Z=el('dxiZ');if(!Z||!D)return;const d=D.doc;
  el('dxiN').innerHTML=`<b>${esc(D.nom)}</b>${d.version?' · DXF '+esc(d.version):''} · unité : ${d.unite?`<b>${d.unite}</b> (donnée par le fichier)`:'<b style="color:var(--redt)">absente du fichier</b>'}`;
  const L=[...new Set(D.C.map(c=>c.source.calque))].sort(_cmp),nb=k=>D.C.filter(c=>c.source.calque===k&&c.statut==='a_confirmer').length;
  Z.innerHTML=(d.unite?'':`<div class="dxi-u">⚠ Le fichier ne donne pas son unité ($INSUNITS absent ou nul, toujours le cas en R12). Unité des cotes du dessin :
    <select class="fi" id="dxiU" onchange="DXI.u=this.value;dxiRows()"><option value="">— choisir —</option>${['mm','cm','m'].map(u=>`<option${D.u===u?' selected':''}>${u}</option>`).join('')}</select></div>`)
  +`<div class="dxi-g"><div class="fd"><label>Chantier</label><input class="fi" id="dxiCh" value="${esc(D.ch)}" onchange="DXI.ch=this.value;DXI.M=null;dxiUpd()"></div>
    <div class="fd"><label>Ouvrage</label><input class="fi" id="dxiOuv" value="${esc(D.ouv)}" onchange="DXI.ouv=this.value;DXI.M=null;dxiUpd()"></div>
    <div class="fd"><label>Indice du plan source</label><input class="fi" id="dxiInd" value="${esc(D.ind)}" placeholder="ex. B" oninput="DXI.ind=this.value"></div>
    <div class="fd"><label>Hauteur commune (mm)</label><input class="fi" id="dxiH" value="${esc(D.hCom)}" placeholder="facultative" oninput="DXI.hCom=this.value;dxiHph();dxiUpd()"></div></div>
  <div class="dxi-l"><b>Calques analysés</b>${L.map(k=>`<label><input type="checkbox" data-lay="${esc(k)}"${D.lay[k]?' checked':''} onchange="DXI.lay[this.dataset.lay]=this.checked;dxiRows()"> ${esc(k)} (${nb(k)})</label>`).join('')}</div>
  <div class="dxi-s" id="dxiS"></div>
  <div class="dxi-w"><div><svg id="dxiV" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Schéma des réservations reconnues"></svg>
    <div class="hint" style="margin:6px 0 0">Schéma des réservations reconnues, à leur position et orientation dans le DXF (contours en tirets : polylignes non reconnues).
    Ce n'est pas un rendu complet du fichier : textes, lignes, blocs, hachures… ne sont pas dessinés.</div></div>
  <div><div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap"><button class="btn bs bo" onclick="dxiAll(true)" title="Cocher les lignes visibles prêtes (✓ ou ⚠)">✓ Confirmer les lignes prêtes</button><button class="btn bs bo" onclick="dxiAll(false)">Tout décocher</button></div>
  <div class="dxi-t"><table class="ser" id="dxiT"><thead><tr><th title="Confirmer">Créer</th><th>#</th><th>Entité DXF</th><th>Calque</th><th>Forme</th><th>Cotes (mm)</th><th>h (mm)</th><th>Réf.</th><th>Statut</th></tr></thead><tbody></tbody></table></div></div></div>
  <details id="dxiNP"><summary></summary><table class="ser"><thead><tr><th>#</th><th>Entité DXF</th><th>Calque</th><th>Raison</th></tr></thead><tbody></tbody></table></details>`;
  dxiRows()}
function dxiHph(){const v=DXI.hCom.trim();document.querySelectorAll('#dxiT input[data-k=h]').forEach(e=>{e.placeholder=v||'à saisir'})}
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
  el('dxiS').innerHTML=`<b>${ok.length} réservation(s) potentielle(s)</b> (${nr} rectangle(s) ou carré(s), ${ok.length-nr} cercle(s)) · ${pr} prête(s) · ${cf} confirmée(s) · <b>${n} à créer</b> · ${V.length-ok.length} géométrie(s) non prise(s) en charge`;
  dxiBtn()}

// Création : lignes confirmées et acceptées par le moteur seulement ; ajoutées à la suite (rien n'est remplacé), annulables
function dxiCreate(){const D=DXI;if(!D)return;dxiEval();const L=dxiReady();if(!L.length)return dxiBtn();
  const uids=[],today=new Date().toISOString().slice(0,10),ind=String(D.ind||'').trim().toUpperCase()||null;
  L.forEach(i=>{const x=D.R[i].x,d=JSON.parse(JSON.stringify(x.plan));if(!d.ref)d.ref=nextRef(d.ch,d.ouv);d.date=today;
    d.origineImport=Object.assign(JSON.parse(JSON.stringify(x.provenance)),{indice:ind,date:today});uids.push(planUid(d));P.push(d)});
  svP();profFromPlans(P.slice(-L.length));profLists();rnL();updBtn();closeModal();const nom=D.nom;DXI=null;
  toast(`${L.length} ouvrage(s) créé(s) depuis ${nom}`,'Annuler',()=>{const u=EI>=0&&P[EI]?P[EI].uid:null;P=P.filter(p=>!uids.includes(p.uid));EI=u?P.findIndex(p=>p.uid===u):-1;svP();rnL();updBtn();toast('Import annulé')})}
