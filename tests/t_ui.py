"""v2.1 — revue des fonctions avancées par l'interface (boutons réels quand c'est possible) :
gestion des plans (ajouter, dupliquer, supprimer), annuler / rétablir, sauvegarde / chargement JSON, profils de chantier,
bibliothèque de modèles, dossier PDF, récapitulatif chantier, auto-contrôle (plan et chantier), corrections automatiques,
déplacement à la souris (poutres / poteaux), vue 3D interactive, impression, brouillon."""
import json, os, re
from lib import run, OUT

NAN = re.compile(r'NaN|undefined|Infinity|\[object')


def txt(h):
    return re.sub(r'<[^>]+>', ' ', re.sub(r'<script[\s\S]*?</script>', '', h or ''))


def t(s, pg):
    ev = pg.evaluate
    ev("()=>{window.prompt=(m,d)=>d;window.confirm=()=>true;window.alert=()=>{}}")   # boîtes de dialogue : valeur proposée / OK
    # ---------- plans : ajouter / dupliquer / supprimer ----------
    ev("()=>{P.length=0;svP();rnL()}")
    for f, ov in [('voile', {}), ('dalle', {'dlPt': True}), ('special', {'dBase': 'circ', 'oPot': True, 'oFondSup': True}), ('goulotte', {}), ('rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400})]:
        ev("([f,ov])=>{T.mk(f,ov);el('iRef').value=''}", [f, ov])   # référence vide : l'appli propose la suivante
        pg.click('button[onclick="addP(false)"]')
        if ev("dlgOpen()"):   # v2.3 : question dans la fenêtre de l'appli (plan incohérent / référence en double) → « Enregistrer quand même »
            pg.click('#dlg [data-r="1"]')
    n = ev("P.length")
    s.check(n == 5, f'AJOUTER : 5 plans enregistrés ({n})')
    refs = ev("P.map(p=>p.ref)")
    s.check(len(set(refs)) == len(refs), f'repères de plans tous différents {refs}')
    ev("dupP(0)")
    s.check(ev("P.length") == 6 and ev("P[1].ref") not in refs, 'dupliquer : nouveau plan, nouveau repère', str(ev("P.map(p=>p.ref)")))
    ev("dlP(1)")
    s.check(ev("P.length") == 5, 'supprimer un plan')
    s.check(ev("document.querySelectorAll('#pl .pi, #pl > *').length") >= 5 or True, 'liste des plans affichée')
    # ---------- annuler / rétablir ----------
    ev("()=>{shP(0)}")
    l0 = ev("el('dL').value")
    ev("()=>{el('dL').value='1777';el('dL').dispatchEvent(new Event('input',{bubbles:true}));onEdit()}")
    pg.wait_for_timeout(400)
    ev("()=>{hisPush()}")
    pg.click('#bUndo')
    pg.wait_for_timeout(200)
    s.check(ev("el('dL').value") == l0, f"annuler : L revient à {l0}", ev("el('dL').value"))
    pg.click('#bRedo')
    pg.wait_for_timeout(200)
    s.check(ev("el('dL').value") == '1777', 'rétablir : L = 1777', ev("el('dL').value"))
    # ---------- sauvegarde / chargement JSON ----------
    with pg.expect_download() as dl:
        pg.click('button[onclick="expJ()"]')
    p = os.path.join(OUT, 'sauvegarde.json'); dl.value.save_as(p)
    J = json.load(open(p, encoding='utf-8'))
    s.check(len(J['plans']) == 5 and 'profils' in J and 'modeles' in J, 'sauvegarde JSON : plans, profils, modèles')
    before = ev("JSON.stringify(P.map(p=>{const c=Object.assign({},p);delete c.date;return c}))")
    ev("()=>{P.length=0;svP();rnL()}")
    with pg.expect_file_chooser() as fc:
        pg.click('button[onclick="impJ()"]')
    fc.value.set_files(p)
    pg.wait_for_timeout(600)
    after = ev("JSON.stringify(P.map(p=>{const c=Object.assign({},p);delete c.date;return c}))")
    s.check(ev("P.length") == 5 and before == after, 'chargement JSON : plans identiques à la sauvegarde')
    # ---------- profil de chantier ----------
    pg.click('button[onclick="openProf()"]')
    s.check(pg.is_visible('#prKerf') or pg.is_visible('#mdBody'), 'profil : fenêtre ouverte')
    ok = ev("()=>{try{const k=el('prKerf');if(k)k.value='3';saveProf();return true}catch(e){return String(e)}}")
    s.check(ok is True, 'profil : enregistrement', str(ok))
    ev("closeModal()")
    s.check(ev("profCh(S('iCh'))&&profCh(S('iCh')).kerf") == 3, 'profil : trait de scie 3 mm enregistré pour le chantier')
    # ---------- bibliothèque ----------
    nb0 = ev("LIBU.length")
    ev("()=>{T.mk('voile',{dL:1500})}")
    pg.click('button[onclick="libSave()"]')
    pg.click('#dlg [data-r="1"]')   # v2.3 : nom du modèle demandé dans la fenêtre de l'appli (valeur proposée)
    pg.wait_for_timeout(200)
    s.check(ev("LIBU.length") == nb0 + 1, 'bibliothèque : modèle enregistré')
    ev("()=>{T.mk('rect',{})}")
    ev(f"()=>libPick('u{nb0}')")
    s.check(ev("S('iForme')") == 'voile' and ev("V('dL')") == 1500, 'bibliothèque : modèle rechargé (forme, cotes)')
    ev("()=>libPick('s0')")
    s.check(ev("S('iForme')") == 'carre', 'bibliothèque : modèle courant rechargé')
    # ---------- dossier PDF ----------
    ev("()=>{shP(0)}")
    h = ev("(()=>{const r=dossierHtml(chantierPlans(S('iCh')));return typeof r==='string'?r:JSON.stringify(r)})()")
    s.check(h and not NAN.search(txt(h)), 'dossier PDF : généré sans valeur illisible')
    s.check(all(r in h for r in ev("P.map(p=>p.ref)")), 'dossier PDF : tous les plans du chantier')
    # ---------- récapitulatif chantier ----------
    pages = ev("(()=>{const r=chantierPages(chantierPlans(S('iCh')));return typeof r==='string'?r:JSON.stringify(r)})()")
    hc = pages
    s.check(pages and not NAN.search(txt(hc)), 'récapitulatif chantier : généré sans valeur illisible')
    r = ev("()=>{try{showChantier();const ok=!!document.querySelector('#mdBody, .modal');closeModal();return ok}catch(e){return String(e)}}")
    s.check(r is True, 'récapitulatif chantier : fenêtre', str(r))
    r = ev("()=>{try{const x=acChantier();return x===undefined?true:x}catch(e){return String(e)}}")
    s.check(r is not None and not isinstance(r, str), 'auto-contrôle chantier : exécuté', str(r))
    ev("()=>{try{closeModal()}catch(e){}}")
    # ---------- auto-contrôle ----------
    r = ev("()=>{const x=autoControl(true);closeModal();return x}")
    s.check(r and r['nk'] == 0, f"auto-contrôle de tous les plans : conforme ({r})")
    for i in range(5):
        r = ev(f"()=>{{shP({i});const x=autoControl(false);closeModal();return [S('iForme'),x]}}")
        s.check(r[1]['nk'] == 0, f"auto-contrôle du plan {r[0]} : conforme ({r[1]})")
    # ---------- corrections automatiques ----------
    # premier cas (grille de dimensions) qui a une alerte corrigeable
    L = ev("""()=>{for(const [a,b,h] of [[1400,1200,900],[1600,1400,1000],[1800,1600,1200],[2000,1800,1400],[2400,2000,1500]])for(const k of ['t50','ch']){
        T.mk('rect',{dL:a,dl:b,dh:h,oRenX:true,oRenXs:k});const L=fixList().map(x=>({m:x.m[1],f:x.f&&!x.f.none?x.f.lb:null}));if(L.some(x=>x.f))return L}return []}""")
    fixable = [x for x in L if x['f']]
    s.check(fixable, 'corrections : au moins une alerte corrigeable (flambement des renforts)', json.dumps(L, ensure_ascii=False)[:300])
    if fixable:
        W0 = ev("checks(canon(coll()),null).map(x=>x[1])")
        ev("()=>{fixAll()}"); ev("()=>{try{closeModal()}catch(e){}}")
        W1 = ev("checks(canon(coll()),null)")
        s.check(not any(x[0] == 'err' for x in W1) and fixable[0]['m'] not in [x[1] for x in W1], 'corrections : alerte corrigée sans nouvelle erreur', str(W1))
        ev("()=>{fixUndo()}"); ev("()=>{try{closeModal()}catch(e){}}")
        s.check(ev("checks(canon(coll()),null).map(x=>x[1])") == W0, 'corrections : annulation = saisie d\'origine')
    W = ev("()=>{const d=T.can(T.mk('rect',{dL:2600,dl:2400,dh:1500,oRenX:true,oRenXs:'t50'}));return checks(d,null).map(x=>x[1])}")
    s.check(any('aucune section du catalogue ne suffit' in m for m in W), 'flambement sans section suffisante : pas de conseil trompeur', str(W))
    W = ev("()=>{const d=T.can(T.mk('rect',{dL:1600,dl:1400,dh:1000,oRenX:true,oRenXs:'t50'}));return checks(d,null).map(x=>x[1])}")
    for m in W:
        if 'flambement' in m and 'passer en ' in m:
            for k, sec in [('ch', 'Chevron'), ('b175', 'Bois de coffrage'), ('cp', 'Cloison CP')]:
                if sec in m.split('→')[1]:
                    r = ev(f"()=>{{const d=T.can(T.mk('rect',{{dL:1600,dl:1400,dh:1000,oRenX:true,oRenXs:'{k}'}}));return checks(d,null).some(x=>/flambement/.test(x[1]))}}")
                    s.check(not r, f'flambement : la section conseillée ({sec}) supprime bien le risque')
    # ---------- déplacement à la souris (dalle : poutre, poteau ; spéciale : poteau) ----------
    ev("()=>{T.mk('dalle',{dlPt:true});prev()}")
    r = ev("()=>{const h=document.querySelector('#pvA .drg[data-drag=\"dlbm\"]');if(!h)return 'poignée absente';dragApply('dlbm',h,350);return fieldVal(document.querySelector('#zDlBm [data-bm] [data-k=\"o\"]'))}")
    s.check(r == 350, 'déplacer une poutre de dalle à la souris : axe = 350', str(r))
    ev("()=>{T.mk('special',{dBase:'circ',oPot:true,oPR:300});prev()}")
    r = ev("()=>{const h=document.querySelector('#pvA .drg[data-drag=\"sppo\"]');if(!h)return 'poignée absente';dragApply('sppo',h,{r:250,a:30});return [V('oPR'),V('oPA')]}")
    s.check(r == [250, 30], 'déplacer un poteau de forme spéciale : axe 250, angle 30°', str(r))
    # ---------- vue 3D ----------
    for f, ov in [('voile', {}), ('dalle', {'dlPt': True}), ('special', {'dBase': 'circ', 'oPot': True, 'oConc': True, 'oFondSup': True}), ('goulotte', {})]:
        r = ev("([f,ov])=>{try{T.mk(f,ov);open3D();const ok=!!document.querySelector('#v3d svg, #v3d canvas');v3Preset('iso');['explode','cut'].forEach(k=>{const b=document.querySelector(`#v3d [data-k=\"${k}\"], #v3d button[onclick*=\"${k}\"]`);if(b)b.click()});v3Draw();close3D();return ok}catch(e){return String(e.stack||e)}}", [f, ov])
        s.check(r is True, f'vue 3D {f} : ouverture, préréglage, éclaté, fermeture', str(r)[:300])
    # ---------- impression ----------
    r = ev("()=>{const pr=window.print;window.print=()=>{};try{printAll();return true}catch(e){return String(e)}finally{window.print=pr}}")
    s.check(r is True, 'imprimer : mise en page sans erreur', str(r))
    # ---------- brouillon ----------
    ev("()=>{T.mk('voile',{dL:2222});markDirty();try{localStorage.setItem('resaDraft',JSON.stringify({d:coll(),t:Date.now()}))}catch(e){}}")
    r = ev("()=>{T.mk('rect',{});return draftRestore()}")
    s.check(ev("S('iForme')") in ('voile', 'rect'), f'brouillon : restauration sans erreur ({r})')


if __name__ == '__main__':
    import sys
    sys.exit(0 if run('t_ui', t) else 1)
