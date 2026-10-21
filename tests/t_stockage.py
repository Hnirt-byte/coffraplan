"""Phase 7 : stockage fiable des projets (IndexedDB), migration non destructive de l'ancien stockage (localStorage), copie de
secours à la fermeture, conflits (onglets, anciennes versions), sauvegarde et restauration par fichier.
Demande de Kévin du 22/10/2026 : aucune perte silencieuse ; migration copiée, relue, comparée, jamais destructive ; erreurs
visibles et export toujours possible ; enregistrement local distinct de la sauvegarde externe ; essais réels en file://.
Navigateurs réels : profils Chromium persistants (fermeture et réouverture), HTML copié sous un autre nom dans un autre dossier.
Projet fictif construit par l'appli elle-même (formes, quantités, CP, profil, modèle, cartouche)."""
import json, os, shutil, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, APP, NOFS, HERE

PRET = 'typeof gen==="function" && typeof _ready!=="undefined" && _ready'
CLES = ['resa3', 'resaProf', 'resaLib', 'resaEnt']


def projet_fictif(pw):
    """Projet construit dans l'appli : 4 formes, quantités, CP non par défaut, profil, modèle, cartouche avec logo."""
    b, pg, errs = open_app(pw); J = pg.evaluate
    J("""()=>{const add=(f,o,ref,nb)=>{T.mk(f,o);el('iCh').value='CHANTIER_FICTIF';el('iOuv').value='OUVRAGE_'+f.toUpperCase();el('iRef').value=ref;
        if(el('iNb'))el('iNb').value=nb;addP(false);if(dlgOpen())dlgEnd(true)};
      add('rect',{dL:1200,dl:800,dh:300},'R01',2);add('circ',{dD:400,dh:250},'F01',5);add('voile',{dL:1500},'V01',1);add('goulotte',{},'G01',3);
      PROF['CHANTIER_FICTIF']=Object.assign({},PROF['CHANTIER_FICTIF'],{kerf:5});svProf();
      LIBU.push({name:'Modèle fictif',d:JSON.parse(JSON.stringify(P[0]))});svLib();
      const c=document.createElement('canvas');c.width=8;c.height=4;ENT=entOk({nom:'ENTREPRISE FICTIVE',des:'K. T.',logo:c.toDataURL('image/png')});svEnt()}""")
    o = json.loads(J('stoAttendre().then(()=>projJson())'))
    b.close()
    return o


class Nav:
    """Profil Chromium persistant (fermeture / réouverture réelles)."""
    def __init__(self, pw, dossier, init=None):
        self.pw, self.dossier, self.init, self.c = pw, dossier, init, None

    def ouvrir(self, app=APP, init=None, attendre=True):
        self.c = self.pw.chromium.launch_persistent_context(self.dossier, viewport={'width': 1400, 'height': 1000}, accept_downloads=True)
        self.c.add_init_script(NOFS)
        for x in (self.init, init):
            if x:
                self.c.add_init_script(x)
        self.errs, self.dlg = [], []
        pg = self.c.pages[0] if self.c.pages else self.c.new_page()
        self.brancher(pg)
        pg.goto('file://' + app)
        if attendre:
            pg.wait_for_function(PRET); pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
        return pg

    def brancher(self, pg):
        pg.on('pageerror', lambda e: self.errs.append(str(e)))
        pg.on('dialog', lambda d: (self.dlg.append(d.type), d.accept()))

    def onglet(self, app=APP):
        pg = self.c.new_page(); self.brancher(pg); pg.goto('file://' + app); pg.wait_for_function(PRET); pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
        return pg

    def fermer(self):
        self.c.close(); self.c = None


def semer(pg, o, brut=None):
    """Écrit un ancien stockage (versions ≤ v3.1) comme le faisait CoffraPlan : resa3 = plans, resaProf, resaLib, resaEnt."""
    v = brut or {'resa3': json.dumps(o['plans']), 'resaProf': json.dumps(o['profils']), 'resaLib': json.dumps(o['modeles']), 'resaEnt': json.dumps(o['ent'])}
    pg.evaluate('v=>{for(const k in v)localStorage.setItem(k,v[k])}', v)
    return v


def t(s):
    tmp = tempfile.mkdtemp()
    seme = os.path.join(tmp, 'semer.html'); open(seme, 'w').write('<!doctype html><meta charset="utf-8"><title>semer</title>')
    with sync_playwright() as pw:
        O = projet_fictif(pw)
        s.check(len(O['plans']) == 4 and O['ent'].get('logo', '').startswith('data:image/png') and O['modeles'] and O['profils'].get('CHANTIER_FICTIF', {}).get('kerf') == 5,
                'projet fictif : 4 plans, profil, modèle, cartouche avec logo', json.dumps([len(O['plans']), list(O['ent']), len(O['modeles'])]))
        metier = lambda o: json.dumps([o['plans'], o['profils'], o['modeles'], o['ent']], sort_keys=True)

        # ---- 1-3. migration d'un ancien stockage, conservation des données, réouverture
        N = Nav(pw, os.path.join(tmp, 'p1'))
        pg = N.ouvrir(app=seme, attendre=False); V = semer(pg, O); N.fermer()
        pg = N.ouvrir(); J = pg.evaluate
        r = J('stoAttendre().then(()=>stoEnregistre()).then(r=>({r,meta:STO.meta,mode:STO.mode,migre:STO.migre,st:el("stoSt").title,toast:el("toast").textContent}))')
        enr = r['r']
        s.check(r['mode'] == 'idb' and r['migre'] and r['meta']['migration']['etat'] == 'ok' and r['meta']['migration']['plans'] == 4,
                '1. migration : ancien stockage copié dans IndexedDB, relu, comparé, marqué réussi', json.dumps(r['meta']))
        s.check(J('v=>Object.keys(v).every(k=>localStorage.getItem(k)===v[k])', V), '1. ancien stockage laissé intact (aucune clé modifiée ni supprimée)')
        s.check('transféré' in r['toast'] and 'conservé' in r['toast'], '1. migration annoncée à l\'utilisateur', r['toast'])
        got = {'plans': enr['plans'], 'profils': enr['profils'], 'modeles': enr['modeles'], 'ent': enr['ent']}
        s.check(metier(got) == metier(O), '2. dimensions, quantités, matériaux, modèles, profils et cartouche identiques après migration',
                json.dumps([p.get('ref') for p in enr['plans']]))
        s.check([p.get('nb') for p in enr['plans']] == [p.get('nb') for p in O['plans']] and [json.dumps(p.get('cp'), sort_keys=True) for p in enr['plans']] == [json.dumps(p.get('cp'), sort_keys=True) for p in O['plans']],
                '2. quantités (nb) et CP de chaque plan conservés', json.dumps([p.get('nb') for p in enr['plans']]))
        N.fermer()
        pg = N.ouvrir(); J = pg.evaluate
        s.check(J('[P.length,STO.migre,STO.mode,!!STO.ancien,el("md").style.display==="flex"]') == [4, False, 'idb', False, False] and J('JSON.stringify([P,PROF,LIBU,ENT])') == J('stoEnregistre().then(r=>JSON.stringify([r.plans,r.profils,r.modeles,r.ent]))'),
                '3. fermeture et réouverture du navigateur : projet retrouvé, migration non refaite, aucun conflit', json.dumps(J('[P.length,STO.migre,STO.mode,STO.ancien&&STO.ancien.cas,el("md").style.display,STO.meta]')))

        # ---- 4. création, modification, suppression ; 5. modifications rapides successives
        J("""()=>{T.mk('rect',{dL:900,dl:600,dh:200});el('iCh').value='CHANTIER_FICTIF';el('iOuv').value='OUVRAGE_B';el('iRef').value='R99';addP(false);if(dlgOpen())dlgEnd(true)}""")
        J("()=>{P[0].desc='modifié';svP();dlP(1)}")
        J('stoAttendre()'); N.fermer(); pg = N.ouvrir(); J = pg.evaluate
        s.check(J('[P.length,P[0].desc,P.some(p=>p.ref==="R99"),P.some(p=>p.ref==="F01")]') == [4, 'modifié', True, False], '4. création, modification et suppression retrouvées après réouverture')
        r0 = J('STO.rev')
        J("()=>{for(let i=0;i<40;i++){P[0].dL=1000+i;svP()}}")
        r = J('stoAttendre().then(()=>stoEnregistre()).then(r=>[r.plans[0].dL,r.rev,STO.rev,STO.etat])')
        s.check(r[0] == 1039 and r[1] == r[2] and r[1] > r0 and r[1] <= r0 + 3 and r[3] == 'ok', '5. 40 modifications rapides : dernière valeur enregistrée, écritures regroupées, jamais une version ancienne', json.dumps([r0] + r))
        J("()=>{P[0].dL=1500;svP()}"); pg.reload(); pg.wait_for_function(PRET); pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
        s.check(J('P[0].dL') == 1500 and J('Object.keys(localStorage).some(k=>k.startsWith("resaSecours."))') is False,
                '5. rechargement juste après une modification : rien perdu (copie de secours reprise puis effacée)')

        # ---- 11. rappel de sauvegarde : enregistrement local ≠ sauvegarde externe
        st = lambda: J("({dirty:isDirty(),bar:el('zExp').style.display!=='none',sto:el('stoSt').textContent.trim()})")
        x = st()
        s.check(x['dirty'] and x['bar'] and 'Enregistré' in x['sto'], '11. projet enregistré dans le navigateur mais jamais sauvegardé en fichier : rappel de sauvegarde affiché', json.dumps(x, ensure_ascii=False))
        with pg.expect_download() as d:
            J('expJ()')
        fic = os.path.join(tmp, 'sauvegarde.json'); d.value.save_as(fic)
        x = st()
        s.check(not x['dirty'] and not x['bar'] and 'Enregistré' in x['sto'] and 'Téléchargements' in J("el('toast').textContent"),
                '11. après la sauvegarde fichier : plus de rappel, enregistrement local toujours indiqué ; message prudent (téléchargement)', J("el('toast').textContent"))
        J("()=>{P[0].desc='après sauvegarde';svP()}")
        s.check(st()['dirty'], '11. modification après la sauvegarde : rappel de nouveau actif')
        N.fermer()

        # ---- 10. export JSON puis import dans un autre profil : données métier identiques ; contrôle avant remplacement
        F = json.load(open(fic))
        s.check(F['app'] == 'plans-reservation' and F['v'] == 10 and set(['plans', 'profils', 'modeles', 'ent']) <= set(F), '10. format du fichier inchangé {app, v:10, plans, profils, modeles, ent}', str(list(F)))
        N2 = Nav(pw, os.path.join(tmp, 'p10')); pg = N2.ouvrir(); J = pg.evaluate
        J("()=>{T.mk('rect',{dL:500,dl:500,dh:200});el('iRef').value='X1';addP(false);if(dlgOpen())dlgEnd(true)}")
        J('t=>loadText(t,"sauvegarde.json",null)', open(fic).read())
        m = J("dlgOpen()?el('dlgB').textContent:''")
        s.check('Remplacer les 1 plan(s)' in m and 'Contenu du fichier : 4 plan(s)' in m and 'modèle(s)' in m and 'ENTREPRISE FICTIVE' in m and 'aucun fichier' in m,
                '10. restauration : contenu vérifié et annoncé avant remplacement ; projet actuel non sauvegardé signalé', m)
        J('dlgEnd(false)')
        s.check(J('[P.length,P[0].ref]') == [1, 'X1'], '10. « Annuler » : projet actuel inchangé')
        J('t=>loadText(t,"sauvegarde.json",null)', open(fic).read()); J('dlgEnd(true)')
        r = J('stoAttendre().then(()=>stoEnregistre()).then(r=>({r,t:el("toast").textContent}))')
        e = r['r']
        s.check(json.dumps([e['plans'], e['ent']], sort_keys=True) == json.dumps([F['plans'], F['ent']], sort_keys=True) and all(m['name'] in [x['name'] for x in e['modeles']] for m in F['modeles'])
                and all(k in e['profils'] for k in F['profils']) and 'enregistré(s) dans ce navigateur' in r['t'],
                '10. import : plans et cartouche identiques au fichier, profils et modèles ajoutés, enregistrement dans le navigateur confirmé', r['t'])
        N2.fermer()

        # ---- 12. HTML renommé et déplacé dans un autre dossier (même navigateur, même profil)
        d2 = os.path.join(tmp, 'autre_dossier'); os.makedirs(d2); app2 = os.path.join(d2, 'CoffraPlan_copie_renommee.html'); shutil.copy(APP, app2)
        pg = N.ouvrir(app=app2); J = pg.evaluate
        s.check(J('[P.length,P[0].desc,STO.mode]') == [4, 'après sauvegarde', 'idb'],
                '12. HTML renommé et déplacé : mêmes projets (Chromium : une seule origine file:// pour tous les fichiers locaux)')
        N.fermer()
        N3 = Nav(pw, os.path.join(tmp, 'p12b')); pg = N3.ouvrir(); J = pg.evaluate
        s.check(J('P.length') == 0, '12. nouveau profil de navigateur : aucun projet (seul le fichier de sauvegarde les transporte)')
        N3.fermer()

        # ---- 13. deux onglets : aucun écrasement silencieux
        pg = N.ouvrir(); pgB = N.onglet(); JA, JB = pg.evaluate, pgB.evaluate
        JA("()=>{P[0].desc='onglet A';svP()}"); JA('stoAttendre()'); pgB.wait_for_timeout(300)
        s.check(JB('STO.perime') and 'autre onglet' in JB("el('zSto').innerText"), '13. onglet B prévenu que le projet a été modifié dans l\'onglet A', JB("el('zSto').innerText"))
        JB("()=>{P[1].desc='onglet B';svP()}"); r = JB('stoAttendre().then(()=>stoEnregistre()).then(r=>[r.plans[0].desc,r.plans[1].desc||"",STO.etat,P[1].desc])')
        s.check(r == ['onglet A', '', 'conflit', 'onglet B'] and 'ne sont pas enregistrées' in JB("el('zSto').innerText"),
                '13. écriture de l\'onglet B refusée (projet de A conservé), modifications de B gardées dans la page et signalées', json.dumps(r))
        JB('stoRecharger()'); pgB.wait_for_timeout(200)
        s.check(JB('[P[0].desc,STO.etat,STO.perime]') == ['onglet A', 'ok', False], '13. « Recharger le projet enregistré » : onglet B à jour')
        JB("()=>{P[1].desc='B après rechargement';svP()}"); r = JB('stoAttendre().then(()=>stoEnregistre()).then(r=>[r.plans[0].desc,r.plans[1].desc])')
        s.check(r == ['onglet A', 'B après rechargement'], '13. après rechargement : modifications de B enregistrées par-dessus celles de A, sans perte', json.dumps(r))
        pgB.close(); N.fermer()

        # ---- 9. ancien stockage différent du projet enregistré : rien d'écrasé, choix explicite
        pg = N.ouvrir(app=seme, attendre=False); O2 = json.loads(json.dumps(O)); O2['plans'] = O2['plans'][:2]; O2['plans'][0]['desc'] = 'écrit par une ancienne version'
        V2 = semer(pg, O2); N.fermer()
        pg = N.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(700)
        s.check(J('[P.length,STO.ancien&&STO.ancien.cas,el("md").style.display]') == [4, 'conflit', 'flex'] and 'Rien n\'a été remplacé' in J("el('mdBody').innerText"),
                '9. deux versions différentes : projet enregistré ouvert, choix proposé, rien remplacé', J("el('mdBody').innerText")[:200])
        s.check(J('v=>Object.keys(v).every(k=>localStorage.getItem(k)===v[k])', V2), '9. ancien stockage différent : conservé intact')
        with pg.expect_download() as d:
            J('stoExportAncien()')
        d.value.save_as(os.path.join(tmp, 'ancien.json')); A = json.load(open(os.path.join(tmp, 'ancien.json')))
        s.check(A['app'] == 'plans-reservation' and len(A['plans']) == 2 and A['plans'][0]['desc'] == 'écrit par une ancienne version', '9. ancien stockage exportable en fichier CoffraPlan lisible')
        J('closeModal()'); N.fermer(); pg = N.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(700)
        s.check(J('el("md").style.display') == 'flex', '9. « Décider plus tard » : question reposée à l\'ouverture suivante')
        J('stoReprendre()'); J('dlgEnd(true)'); pg.wait_for_function('STO.ancien===null&&!STO.cours'); J('stoAttendre()')
        s.check(J('[P.length,P[0].desc]') == [2, 'écrit par une ancienne version'] and J('stoEnregistre().then(r=>r.plans.length)') == 2,
                '9. « Reprendre l\'ancien stockage » (confirmé) : ancien stockage repris et enregistré')
        N.fermer(); pg = N.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(500)
        s.check(J('[P.length,!!STO.ancien,el("md").style.display==="flex"]') == [2, False, False], '9. choix retenu : plus de question à l\'ouverture suivante', json.dumps(J('[P.length,STO.ancien&&STO.ancien.cas,el("md").style.display,STO.meta]')))
        N.fermer()
        pg = N.ouvrir(app=seme, attendre=False); O3 = json.loads(json.dumps(O)); O3['plans'] = O3['plans'][:1]; V3 = semer(pg, O3); N.fermer()
        pg = N.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(700)
        s.check(J('[P.length,STO.ancien&&STO.ancien.cas]') == [2, 'conflit'], '9. nouvel ancien stockage différent : question posée de nouveau')
        J('stoIgnorer()'); pg.wait_for_function('STO.ancien===null'); N.fermer(); pg = N.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(500)
        s.check(J('[P.length,!!STO.ancien,el("md").style.display==="flex"]') == [2, False, False] and J('v=>Object.keys(v).every(k=>localStorage.getItem(k)===v[k])', V3),
                '9. « Garder le projet enregistré » : projet gardé, ancien stockage conservé intact, plus de question')
        N.fermer()

        # ---- 6-7. erreurs d'écriture simulées (erreur inconnue, quota) : rien perdu, erreur visible, export possible, reprise
        CASSE = """window.__casse=null;(()=>{const o=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(v,k){if(window.__casse&&k==='courant')throw new DOMException('simulé',window.__casse);return o.apply(this,arguments)}})();"""
        pg = N.ouvrir(init=CASSE); J = pg.evaluate
        base = J('stoEnregistre()')
        for nom, msg, lab in [('UnknownError', 'simulé', '6. erreur de stockage simulée'), ('QuotaExceededError', 'espace de stockage insuffisant', '7. quota insuffisant simulé')]:
            J(f"()=>{{window.__casse='{nom}';STO.alerte=false;P[0].desc='{nom}';svP()}}"); J('stoAttendre()'); pg.wait_for_timeout(100)
            r = J("({st:el('stoSt').textContent,b:el('zSto').innerText,d:dlgOpen()?el('dlgB').textContent:'',e:STO.etat,mem:P[0].desc})")
            rec = J('stoEnregistre()')
            s.check(r['e'] == 'erreur' and 'Non enregistré' in r['st'] and msg in r['b'] and msg in r['d'] and 'Ctrl+S' in r['d'] and r['mem'] == nom,
                    f'{lab} : erreur visible (indicateur, bandeau, message), modification gardée en mémoire', json.dumps(r, ensure_ascii=False)[:300])
            s.check(rec['rev'] == base['rev'] and json.dumps(rec['plans']) == json.dumps(base['plans']), f'{lab} : projet enregistré intact (jamais remplacé par un état partiel ou vide)')
            if J('dlgOpen()'):
                J('dlgEnd(false)')
            with pg.expect_download() as d:
                J('expJ()')
            d.value.save_as(os.path.join(tmp, 'urgence.json'))
            s.check(json.load(open(os.path.join(tmp, 'urgence.json')))['plans'][0]['desc'] == nom, f'{lab} : export du projet en mémoire toujours possible')
        J("window.__casse=null"); J('stoReessayer()'); r = J('stoAttendre().then(()=>stoEnregistre()).then(r=>[r.plans[0].desc,STO.etat,el("zSto").style.display])')
        s.check(r == ['QuotaExceededError', 'ok', 'none'], '6-7. « Réessayer » une fois le problème levé : enregistré, bandeau retiré', json.dumps(r))
        N.fermer()

        # ---- 8. migration interrompue (écriture de la marque refusée), puis relancée
        N8 = Nav(pw, os.path.join(tmp, 'p8'))
        pg = N8.ouvrir(app=seme, attendre=False); V = semer(pg, O); N8.fermer()
        MCASSE = """(()=>{const o=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(v,k){if(k==='meta')throw new DOMException('coupure simulée','AbortError');return o.apply(this,arguments)}})();"""
        pg = N8.ouvrir(init=MCASSE); J = pg.evaluate
        r = J("({mode:STO.mode,etat:STO.etat,b:el('zSto').innerText,n:P.length,meta:STO.meta})")
        s.check(r['mode'] == 'local' and r['etat'] == 'migration' and 'Réessayer' in r['b'] and 'Exporter' in r['b'] and 'intacts' in r['b'] and r['n'] == 4,
                '8. migration interrompue : erreur visible, export et nouvelle tentative proposés, projets toujours ouverts', json.dumps(r, ensure_ascii=False)[:300])
        s.check(J('v=>Object.keys(v).every(k=>localStorage.getItem(k)===v[k])', V), '8. migration interrompue : ancien stockage intact')
        N8.fermer()
        pg = N8.ouvrir(); J = pg.evaluate
        r = J("stoEnregistre().then(r=>({mode:STO.mode,m:STO.meta.migration,n:P.length,anc:!!STO.ancien,eq:JSON.stringify([r.plans,r.profils,r.modeles,r.ent])===JSON.stringify([P,PROF,LIBU,ENT])}))")
        s.check(r['mode'] == 'idb' and r['m'] and r['m']['etat'] == 'ok' and r['n'] == 4 and not r['anc'] and r['eq'],
                '8. relance : migration terminée (copie déjà faite reconnue identique), aucun conflit, données identiques', json.dumps(r))
        N8.fermer()

        # ---- IndexedDB indisponible : mode de secours annoncé, ancien enregistrement, export possible
        N9 = Nav(pw, os.path.join(tmp, 'p9')); pg = N9.ouvrir(init='Object.defineProperty(window,"indexedDB",{value:undefined,configurable:true});'); J = pg.evaluate
        J("()=>{T.mk('rect',{dL:700,dl:700,dh:200});el('iRef').value='S1';addP(false);if(dlgOpen())dlgEnd(true)}")
        r = J("({mode:STO.mode,st:el('stoSt').textContent,b:el('zSto').innerText,ls:JSON.parse(localStorage.getItem('resa3')||'[]').length})")
        s.check(r['mode'] == 'local' and 'secours' in r['st'] and 'fiable indisponible' in r['b'] and 'Sauvegarder' in r['b'] and r['ls'] == 1,
                'IndexedDB indisponible : enregistrement automatique fiable annoncé indisponible, ancien enregistrement maintenu, sauvegarde proposée', json.dumps(r, ensure_ascii=False)[:300])
        N9.fermer()

        # ---- ancien stockage illisible : non transféré, non modifié, exportable tel quel
        N10 = Nav(pw, os.path.join(tmp, 'p10b')); pg = N10.ouvrir(app=seme, attendre=False); V = semer(pg, O, {'resa3': '[{"forme":"rect",'}); N10.fermer()
        pg = N10.ouvrir(); J = pg.evaluate
        r = J("({n:P.length,c:STO.ancien&&STO.ancien.cas,b:el('zSto').innerText,m:STO.meta.migration||null})")
        s.check(r['n'] == 0 and r['c'] == 'illisible' and 'illisible' in r['b'] and 'exporter' in r['b'] and r['m'] is None and J("localStorage.getItem('resa3')") == V['resa3'],
                'ancien stockage illisible : signalé, non transféré, laissé intact', json.dumps(r, ensure_ascii=False)[:300])
        with pg.expect_download() as d:
            J('stoExportAncien()')
        d.value.save_as(os.path.join(tmp, 'brut.json'))
        s.check(json.load(open(os.path.join(tmp, 'brut.json')))['cles']['resa3'] == V['resa3'], 'ancien stockage illisible : exporté tel quel (texte brut) pour récupération')
        N10.fermer()

        # ==== Relecture de la PR #17 : corrections A (projet vide ≠ absence de projet), B (copies de secours concurrentes), forçage ====
        # A1. projet enregistré vidé de ses plans + ancien stockage de 4 plans : aucun remplacement d'office
        NA = Nav(pw, os.path.join(tmp, 'pA1')); pg = NA.ouvrir(); J = pg.evaluate
        J("()=>{T.mk('rect',{dL:600,dl:600,dh:200});el('iRef').value='A1';addP(false);if(dlgOpen())dlgEnd(true);dlP(0)}"); J('stoAttendre()')
        r1 = J('stoEnregistre().then(r=>[r.rev,r.plans.length,r.modeles.length])'); pg.goto('file://' + seme); V = semer(pg, O); NA.fermer()
        pg = NA.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(700)
        r = J('stoEnregistre().then(r=>({n:P.length,rev:r.rev,nr:r.plans.length,cas:STO.ancien&&STO.ancien.cas,md:el("md").style.display==="flex",migre:STO.migre}))')
        s.check(r1[1:] == [0, 0] and r == {'n': 0, 'rev': r1[0], 'nr': 0, 'cas': 'conflit', 'md': True, 'migre': False}
                and J('v=>Object.keys(v).every(k=>localStorage.getItem(k)===v[k])', V),
                'A1. projet enregistré sans plan + ancien stockage de 4 plans : rien remplacé, choix proposé, ancien stockage intact', json.dumps([r1, r]))
        NA.fermer()
        # A2. zéro plan mais profil et cartouche enregistrés + ancien stockage différent : profil et cartouche gardés, choix proposé
        NA2 = Nav(pw, os.path.join(tmp, 'pA2')); pg = NA2.ouvrir(); J = pg.evaluate
        J("()=>{PROF['CHANTIER_A2']={kerf:7};svProf();ENT=entOk({nom:'CARTOUCHE A2'});svEnt()}"); J('stoAttendre()')
        pg.goto('file://' + seme); semer(pg, O); NA2.fermer()
        pg = NA2.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(700)
        r = J("stoEnregistre().then(r=>({n:P.length,prof:(PROF.CHANTIER_A2||{}).kerf,ent:ENT.nom,rprof:(r.profils.CHANTIER_A2||{}).kerf,rent:r.ent.nom,cas:STO.ancien&&STO.ancien.cas}))")
        s.check(r == {'n': 0, 'prof': 7, 'ent': 'CARTOUCHE A2', 'rprof': 7, 'rent': 'CARTOUCHE A2', 'cas': 'conflit'},
                'A2. zéro plan, profil et cartouche enregistrés : conservés, ancien stockage proposé au choix, jamais migré d\'office', json.dumps(r))
        NA2.fermer()
        # A3. migration initiale contrôlée : création refusée si un projet existe déjà (onglets démarrés en même temps)
        NA3 = Nav(pw, os.path.join(tmp, 'pA3')); pg = NA3.ouvrir(); J = pg.evaluate
        J("()=>{T.mk('rect',{dL:800,dl:500,dh:200});el('iRef').value='A3';addP(false);if(dlgOpen())dlgEnd(true)}"); J('stoAttendre()')
        avant = J('stoEnregistre()')
        r = J("""(o)=>{localStorage.setItem('resa3',JSON.stringify(o.plans));const A=stoAncien();STO.rev=0;
              return stoMigrer(A,true).then(()=>stoEnregistre()).then(r=>({rev:r.rev,refs:r.plans.map(p=>p.ref),cas:STO.ancien&&STO.ancien.cas,mode:STO.mode,mem:P.map(p=>p.ref)}))}""", O)
        s.check(r['rev'] == avant['rev'] and r['refs'] == ['A3'] and r['cas'] == 'conflit' and r['mode'] == 'idb' and r['mem'] == ['A3'],
                'A3. migration initiale lancée alors qu\'un projet vient d\'être créé par un autre onglet : refusée, projet existant ouvert, choix proposé', json.dumps(r))
        J("()=>{localStorage.setItem('resa3',JSON.stringify(P));localStorage.setItem('resaProf',JSON.stringify(PROF));localStorage.setItem('resaLib',JSON.stringify(LIBU));localStorage.setItem('resaEnt',JSON.stringify(ENT));STO.rev=0}")
        r = J("stoMigrer(stoAncien(),true).then(()=>stoEnregistre()).then(r=>({rev:r.rev,cas:STO.ancien&&STO.ancien.cas,m:(STO.meta.migration||{}).etat}))")
        s.check(r == {'rev': avant['rev'], 'cas': None, 'm': 'ok'}, 'A3. même cas, données identiques : migration simplement marquée, rien réécrit', json.dumps(r))
        NA3.fermer()

        # B. deux copies de secours différentes, même révision de départ : aucune reprise, aucune suppression, choix explicite
        NB = Nav(pw, os.path.join(tmp, 'pB')); pg = NB.ouvrir(); J = pg.evaluate
        J("()=>{T.mk('rect',{dL:900,dl:500,dh:200});el('iRef').value='B0';addP(false);if(dlgOpen())dlgEnd(true)}"); J('stoAttendre()')
        rev = J('STO.rev')
        J("""(rev)=>{const pr=x=>Object.assign(JSON.parse(JSON.stringify({plans:P,profils:PROF,modeles:LIBU,ent:ENT})),{});
              const a=pr(),b=pr();a.plans[0].desc='copie onglet 1';b.plans[0].desc='copie onglet 2';b.plans.push(Object.assign({},b.plans[0],{ref:'B9',uid:'b9'}));
              localStorage.setItem('resaSecours.ong1',JSON.stringify({base:rev,date:'2026-10-22T08:00:00Z',projet:a}));
              localStorage.setItem('resaSecours.ong2',JSON.stringify({base:rev,date:'2026-10-22T08:01:00Z',projet:b}))}""", rev)
        NB.fermer(); pg = NB.ouvrir(); J = pg.evaluate; pg.wait_for_timeout(800)
        r = J("stoEnregistre().then(r=>({mem:P.map(p=>p.desc||''),rec:r.plans.map(p=>p.desc||''),rev:r.rev,cles:Object.keys(localStorage).filter(k=>k.startsWith('resaSecours.')).sort(),n:STO.secours.length,md:el('mdBody').textContent,b:el('zSto').textContent}))")
        s.check(r['mem'] == [''] and r['rec'] == [''] and r['rev'] == rev and r['cles'] == ['resaSecours.ong1', 'resaSecours.ong2'] and r['n'] == 2,
                'B. deux copies de secours différentes de même révision : aucune reprise, aucune suppression, projet enregistré intact', json.dumps(r, ensure_ascii=False)[:400])
        s.check('Rien n\'a été remplacé' in r['md'] and r['md'].count('Exporter') >= 2 and 'Reprendre' in r['md'] and 'copie(s) de secours' in r['b'],
                'B. récupération explicite proposée (fenêtre et bandeau), une ligne par copie', r['md'][:300])
        with pg.expect_download() as d:
            J('stoSecoursExport(1)')
        d.value.save_as(os.path.join(tmp, 'sec2.json')); c2 = json.load(open(os.path.join(tmp, 'sec2.json')))
        s.check(len(c2['plans']) == 2 and c2['plans'][0]['desc'] == 'copie onglet 2', 'B. chaque copie exportable séparément (fichier CoffraPlan lisible)')
        J('stoSecoursReprendre(1)'); s.check(J('dlgOpen()'), 'B. reprise d\'une copie : confirmation demandée avant remplacement')
        J('dlgEnd(true)'); pg.wait_for_timeout(300); J('stoAttendre()')
        r = J("stoEnregistre().then(r=>({rec:r.plans.map(p=>p.desc||''),rev:r.rev,cles:Object.keys(localStorage).filter(k=>k.startsWith('resaSecours.'))}))")
        s.check(r['rec'] == ['copie onglet 2', 'copie onglet 2'] and r['rev'] == rev + 1 and r['cles'] == ['resaSecours.ong1'],
                'B. copie choisie reprise et enregistrée ; l\'autre copie conservée', json.dumps(r, ensure_ascii=False))
        NB.fermer()

        # F. forçage : autorisation consommée par une écriture en échec, jamais réutilisée contre une révision plus récente
        NF = Nav(pw, os.path.join(tmp, 'pF'), init=CASSE); pg = NF.ouvrir(); J = pg.evaluate
        J("()=>{T.mk('rect',{dL:900,dl:500,dh:200});el('iRef').value='F0';addP(false);if(dlgOpen())dlgEnd(true)}"); J('stoAttendre()')
        pgB = NF.onglet(); JB = pgB.evaluate
        J("()=>{P[0].desc='A1';svP()}"); J('stoAttendre()')
        JB("()=>{P[0].desc='B1';svP()}"); JB('stoAttendre()')
        s.check(JB('STO.etat') == 'conflit', 'F. onglet B en conflit après l\'écriture de A')
        JB("()=>{window.__casse='UnknownError';STO.alerte=true;stoForcer()}"); JB('dlgEnd(true)'); JB('stoAttendre()'); JB("window.__casse=null")
        s.check(JB('[STO.etat,STO.forcer]') == ['erreur', None], 'F. remplacement confirmé mais écriture en échec : autorisation de forçage retirée', json.dumps(JB('[STO.etat,STO.forcer]')))
        J("()=>{P[0].desc='A2';svP()}"); J('stoAttendre()')
        JB("()=>{P[0].desc='B2';svP()}"); r = JB('stoAttendre().then(()=>stoEnregistre()).then(r=>[r.plans[0].desc,STO.etat])')
        s.check(r == ['A2', 'conflit'], 'F. écriture suivante de B : refusée, la nouvelle révision de A n\'est pas écrasée', json.dumps(r))
        JB("()=>stoForcer()"); JB('dlgEnd(true)'); r = JB('stoAttendre().then(()=>stoEnregistre()).then(r=>[r.plans[0].desc,STO.etat,STO.forcer])')
        s.check(r == ['B2', 'ok', None], 'F. nouveau choix explicite sur la révision vue : version de B enregistrée, autorisation consommée', json.dumps(r))
        pgB.close(); NF.fermer()

        s.check(not [e for e in N.errs + N8.errs + N9.errs + N10.errs + NA.errs + NB.errs + NF.errs], 'aucune erreur JS', json.dumps((N.errs + N8.errs + NB.errs + NF.errs)[:3]))


if __name__ == '__main__':
    s = Suite('t_stockage')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
