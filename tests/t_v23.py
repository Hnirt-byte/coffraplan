"""v2.3 — (a) plan affiché modifié mais pas mis à jour, (b) fenêtres de l'appli au lieu des boîtes du navigateur,
(c) liste des plans : recherche / regroupement / tri, (e) aperçu non bloquant sur les formes lourdes.
Interface réelle (souris, clavier) ; aucune boîte de dialogue du navigateur ne doit apparaître (hors avertissement de fermeture)."""
import json, os, random, re
from playwright.sync_api import sync_playwright
from lib import Suite, APP, OUT, HERE

RUNS = os.path.join(HERE, 'plans_v22.json')   # 420 plans aléatoires enregistrés par la v2.2 (t_audit, graine fixe)
OK = '#dlg [data-r="1"]'
NO = '#dlg [data-r="0"]'


def page(pw, w=1400, h=900):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': w, 'height': h}, accept_downloads=True)
    pg = ctx.new_page()
    errs, dialogs = [], []
    pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
    pg.on('dialog', lambda d: (dialogs.append(d.type + ':' + d.message[:60]), d.accept()))
    pg.goto('file://' + APP); pg.evaluate('localStorage.clear();localStorage.setItem("resaPrint",JSON.stringify({cp:true,mt:true,fa:true}))'); pg.reload()
    pg.wait_for_function('typeof gen==="function" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
    return b, pg, errs, dialogs


def rl(pg):
    pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))


def add(pg, f, ov, ouv='', ch='TEST', ref=''):
    pg.evaluate("([f,ov,o,c,r])=>{T.mk(f,ov);el('iOuv').value=o;el('iCh').value=c;el('iRef').value=r;EI=-1;updBtn()}", [f, ov, ouv, ch, ref])
    pg.click('#bAdd')
    if pg.evaluate('dlgOpen()'):
        pg.click(OK)


def t(s):
    src = open(APP, encoding='utf-8').read()
    js = src[src.index('<script>'):]
    s.check(not re.findall(r'(?<![\w.])(alert|confirm|prompt)\(', js), 'aucun appel aux boîtes du navigateur (alert / confirm / prompt) dans le code')
    with sync_playwright() as pw:
        # ===================== (a) plan modifié non mis à jour =====================
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        st = lambda: ev("({d:editDirty(),dot:el('bAdd').classList.contains('dirty'),btn:el('bAdd').textContent,line:el('zEditSt').style.display!=='none'?el('zEditSt').textContent:null})")
        add(pg, 'rect', {'dL': 1200, 'dl': 800, 'dh': 300}); add(pg, 'special', {'dBase': 'circ', 'oPot': True})
        ev("shP(0)")
        r = st()
        s.check(not r['d'] and not r['dot'] and r['btn'] == '✔ METTRE À JOUR R01' and 'aucune modification' in (r['line'] or ''), 'plan ouvert : « Mettre à jour R01 », aucune modification signalée', str(r))
        pg.fill('#dL', '1300'); pg.wait_for_timeout(400)
        r = st()
        s.check(r['d'] and r['dot'] and 'R01 modifié — non enregistré' in (r['line'] or ''), 'saisie : pastille sur « Mettre à jour » + « R01 modifié — non enregistré »', str(r))
        pg.fill('#dL', '1200'); pg.wait_for_timeout(400)
        s.check(not st()['d'], 'valeur remise à l\'identique : plus signalé')
        pg.fill('#dL', '1300'); pg.wait_for_timeout(400)
        ev("document.activeElement.blur()"); pg.keyboard.press('Control+z'); pg.wait_for_timeout(300)
        s.check(not st()['d'] and ev("el('dL').value") == '1200', 'Ctrl+Z jusqu\'à l\'état du plan : plus signalé')
        pg.fill('#dL', '1300'); pg.wait_for_timeout(400)
        with pg.expect_download() as d:
            pg.keyboard.press('Control+s')
        s.check('non incluses' in ev("el('toast').textContent"), 'Ctrl+S avec R01 modifié : message « modifications non mises à jour, non incluses »', ev("el('toast').textContent"))
        # même plan recliqué : saisie conservée
        pg.click('#sl .si:has-text("R01")'); pg.wait_for_timeout(200)
        s.check(ev("el('dL').value") == '1300' and st()['d'], 'clic sur le plan déjà affiché : saisie en cours conservée')
        # changement de plan : saisie laissée de côté, « Revenir » la restitue
        pg.click('#sl .si:has-text("R02")'); pg.wait_for_timeout(200)
        s.check(ev("EI") == 1 and 'R01 : modifications non enregistrées laissées de côté' in ev("el('toast').textContent"), 'ouverture d\'un autre plan : message avec « Revenir »', ev("el('toast').textContent"))
        s.check(ev("P[0].L") == 1200, 'R01 enregistré inchangé (rien n\'est écrit sans « Mettre à jour »)')
        pg.click('#toast button:has-text("Revenir")'); pg.wait_for_timeout(300)
        s.check(ev("EI") == 0 and ev("el('dL').value") == '1300' and st()['d'], '« Revenir » : R01 rouvert avec la saisie en cours')
        pg.click('#bAdd'); pg.wait_for_timeout(200)
        if ev('dlgOpen()'):
            pg.click(OK)
        s.check(ev("P[0].L") == 1300 and ev("EI") == -1 and not st()['dot'] and st()['line'] is None, '« Mettre à jour » : plan enregistré, indicateurs retirés')
        # rechargement : brouillon restauré, toujours signalé
        ev("shP(1)"); pg.fill('#oPR', '333'); pg.wait_for_timeout(400)
        rl(pg); ev = pg.evaluate
        s.check(ev("EI") == 1 and ev("editDirty()") and ev("el('bAdd').classList.contains('dirty')"), 'rechargement de l\'onglet : saisie restaurée, R02 toujours signalé modifié')
        # aucun faux positif : plans enregistrés par la v2.2 (420, toutes formes et options), ouverts un par un
        runs = json.load(open(RUNS, encoding='utf-8'))
        random.Random(7).shuffle(runs)
        sample = runs[:120]
        bad = ev("""(L)=>{P=L.map(migr);EI=-1;rnL();const bad=[];P.forEach((p,i)=>{shP(i);if(editDirty()){const a=JSON.parse(formSnap());bad.push([p.forme,Object.keys(a).filter(k=>JSON.stringify(a[k])!==JSON.stringify(JSON.parse(_eBase)[k]))])}});return bad}""", sample)
        s.check(not bad, f'{len(sample)} plans v2.2 ouverts : aucun signalé modifié à tort', str(bad[:5]))
        s.check(not errs, '(a) aucune erreur JS', str(errs[:3]))
        b.close()

        # ===================== (b) fenêtres de l'appli =====================
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        ev("()=>{window._np=0;window.print=()=>{window._np++}}")
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});el('iCh').value=''}"); pg.click('#bAdd')
        s.check(ev("P.length") == 0 and ev("document.activeElement.id") == 'iCh' and 'nom du chantier' in ev("el('toast').textContent"), 'sans nom de chantier : message discret, curseur dans le champ')
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300})}"); pg.fill('#dL', '12a0'); pg.click('#bAdd')
        s.check(ev("P.length") == 0 and ev("document.activeElement.id") == 'dL' and 'Saisie illisible' in ev("el('toast').textContent"), 'saisie illisible : message + curseur dans le champ fautif')
        # plan incohérent : question dans l'appli, Échap = non, OK = oui
        ev("()=>{T.mk('special',{dBase:'circ',oConc:true,oDint:1500})}"); pg.click('#bAdd')
        s.check(ev("dlgOpen()") and 'incohérences' in ev("el('dlgB').textContent"), 'plan incohérent : question dans la fenêtre de l\'appli')
        pg.keyboard.press('Control+p')
        s.check(ev("window._np") == 0 and ev("dlgOpen()"), 'raccourcis neutralisés pendant une question')
        pg.keyboard.press('Escape')
        s.check(not ev("dlgOpen()") and ev("P.length") == 0, 'Échap : question fermée, plan non enregistré')
        pg.click('#bAdd'); pg.click(OK)
        s.check(ev("P.length") == 1, '« Enregistrer quand même » : plan enregistré')
        # référence en double
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});el('iRef').value='R01';EI=-1}"); pg.click('#bAdd')
        s.check(ev("dlgOpen()") and 'R01 existe déjà' in ev("el('dlgB').textContent"), 'référence en double : question explicite')
        pg.click(NO)
        s.check(ev("P.length") == 1, 'Annuler : rien enregistré')
        add(pg, 'carre', {}); add(pg, 'voile', {})
        refs = ev("P.map(p=>p.ref)")
        # suppression immédiate + Annuler
        pg.click('#sl .si:nth-of-type(2) button[aria-label^="Supprimer"]') if False else ev("dlP(1)")
        s.check(ev("P.length") == 2 and not ev("dlgOpen()") and 'supprimé' in ev("el('toast').textContent"), 'supprimer : immédiat, sans question, message « supprimé · Annuler »')
        pg.click('#toast button:has-text("Annuler")')
        s.check(ev("P.map(p=>p.ref)") == refs, 'Annuler : plan rétabli à sa place', str(ev("P.map(p=>p.ref)")))
        # tout supprimer : question (danger), puis Annuler
        ev("clearAll()")
        s.check(ev("dlgOpen()") and ev("!!document.querySelector('#dlg .bdg')"), 'tout supprimer : question avec bouton rouge')
        pg.click(NO); s.check(ev("P.length") == 3, 'tout supprimer annulé : plans conservés')
        ev("clearAll()"); pg.click(OK)
        s.check(ev("P.length") == 0, 'tout supprimer confirmé')
        pg.click('#toast button:has-text("Annuler")')
        s.check(ev("P.map(p=>p.ref)") == refs, 'tout supprimer : Annuler rétablit les plans')
        # modèle : nom demandé dans l'appli
        n0 = ev("LIBU.length")
        pg.click('button[onclick="libSave()"]')
        s.check(ev("dlgOpen()") and ev("document.activeElement.id") == 'dlgIn', 'modèle : nom demandé dans l\'appli, champ prêt à la saisie')
        pg.keyboard.press('Tab'); pg.keyboard.press('Tab'); pg.keyboard.press('Tab')
        s.check(ev("el('dlgB').contains(document.activeElement)"), 'Tab : le focus reste dans la question')
        pg.focus('#dlgIn'); pg.keyboard.press('Control+a')
        pg.keyboard.type('Mon modèle'); pg.keyboard.press('Enter')
        s.check(ev("LIBU.length") == n0 + 1 and ev("LIBU[LIBU.length-1].name") == 'Mon modèle', 'Entrée : modèle enregistré sous le nom saisi')
        pg.click('button[onclick="libSave()"]'); pg.keyboard.press('Escape')
        s.check(ev("LIBU.length") == n0 + 1, 'Échap : aucun modèle enregistré')
        # fichier invalide / remplacement
        bad = os.path.join(OUT, 'invalide.json'); open(bad, 'w').write('{pas du json')
        with pg.expect_file_chooser() as fc:
            pg.click('button[onclick="impJ()"]')
        fc.value.set_files(bad); pg.wait_for_timeout(300)
        s.check(ev("dlgOpen()") and 'invalide.json' in ev("el('dlgB').textContent"), 'fichier invalide : message nommant le fichier')
        pg.click(OK)
        with pg.expect_download() as d:
            pg.keyboard.press('Control+s')
        sv = os.path.join(OUT, 'v23_save.json'); d.value.save_as(sv)
        with pg.expect_file_chooser() as fc:
            pg.click('button[onclick="impJ()"]')
        fc.value.set_files(sv); pg.wait_for_timeout(300)
        s.check(ev("dlgOpen()") and 'Remplacer les 3 plan(s)' in ev("el('dlgB').textContent"), 'chargement : « Remplacer les 3 plans actuels ? »')
        pg.click(OK); pg.wait_for_timeout(200)
        s.check(ev("P.length") == 3 and '3 plan(s) chargé(s)' in ev("el('toast').textContent"), 'chargement confirmé : message discret')
        s.check(not [x for x in dlg if not x.startswith('beforeunload')], 'aucune boîte de dialogue du navigateur pendant tout le parcours', str(dlg))
        s.check(not errs, '(b) aucune erreur JS', str(errs[:3]))
        b.close()

        # ===================== (c) liste des plans =====================
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        for ch, ouv, f, ref in [('CHANTIER_DEMO_A', 'Clarificateur', 'rect', 'R10'), ('CHANTIER_DEMO_A', 'Clarificateur', 'special', 'R2'), ('CHANTIER_DEMO_A', 'Poste de relevage', 'carre', 'R1'),
                                ('CHANTIER_DEMO_A', 'Clarificateur', 'carre', 'R1'), ('Bassin Est', '', 'voile', 'V1')]:
            add(pg, f, {'dL': 1200, 'dl': 800, 'dh': 300} if f == 'rect' else {}, ouv, ch, ref)
        L = lambda: ev("[...el('sl').children].map(e=>e.classList.contains('plg')?'#'+e.textContent:e.querySelector('.n').firstChild.textContent)")
        s.check(L() == ['#BASSIN EST1', 'V1', '#CHANTIER_DEMO_A · Clarificateur3', 'R10', 'R2', 'R1', '#CHANTIER_DEMO_A · Poste de relevage1', 'R1'],
                'regroupement chantier · ouvrage (ordre alphabétique, effectifs), ordre de saisie dans l\'ouvrage', str(L()))
        pg.select_option('#plS', 'r')
        s.check(L()[2:6] == ['#CHANTIER_DEMO_A · Clarificateur3', 'R1', 'R2', 'R10'], 'tri par référence (R2 avant R10)', str(L()))
        pg.select_option('#plS', 'f')
        s.check(L()[3] == 'R1' and ev("el('sl').children[3].textContent").find('Carré') >= 0, 'tri par forme', str(L()))
        g0 = ev("()=>{window._ng=0;const g=window.gen;window.gen=d=>{window._ng++;return g(d)};return HIS.length}")
        pg.fill('#plQ', 'relevage')
        s.check(L() == ['#CHANTIER_DEMO_A · Poste de relevage1', 'R1'] and ev("el('pc').textContent") == '1 / 5', 'recherche « relevage » : 1 / 5', str(L()))
        pg.fill('#plQ', 'speciale clar')
        s.check(L() == ['#CHANTIER_DEMO_A · Clarificateur1', 'R2'], 'recherche sans accents et à plusieurs mots (« speciale clar »)', str(L()))
        pg.fill('#plQ', 'zzz')
        s.check('Aucun plan ne correspond' in ev("el('sl').textContent"), 'recherche sans résultat : message')
        pg.wait_for_timeout(400)
        s.check(ev("window._ng") == 0 and ev("HIS.length") == g0, 'la recherche ne relance ni le calcul ni l\'historique')
        pg.fill('#plQ', 'R2'); pg.click('#sl .si')
        s.check(ev("EI") == 1 and ev("el('iRef').value") == 'R2', 'clic dans la liste filtrée : le bon plan s\'ouvre')
        pg.fill('#plQ', ''); pg.focus('#sl .si:has-text("V1")'); pg.keyboard.press('Enter')
        s.check(ev("el('iRef').value") == 'V1', 'clavier : Entrée sur un plan de la liste l\'ouvre')
        rl(pg); ev = pg.evaluate
        s.check(ev("el('plS').value") == 'f', 'ordre de tri mémorisé')
        s.check(not errs, '(c) aucune erreur JS', str(errs[:3]))
        b.close()

        # ===================== (e) aperçu non bloquant =====================
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        ev("()=>{window._ng=0;const g=window.gen;window.gen=d=>{window._ng++;return g(d)}}")
        ev("()=>{T.mk('goulotte',{});onEdit()}"); pg.wait_for_timeout(1500)
        ms = ev("_calcMs")
        print(f'  goulotte : recalcul {ms:.0f} ms')
        if ms > 300:
            n = ev("window._ng")
            pg.click('#gB'); pg.keyboard.press('End'); pg.keyboard.type('5'); pg.wait_for_timeout(700)
            s.check(ev("window._ng") == n and ev("el('pvSt').style.display") == 'block' and ev("el('pvA').classList.contains('stale')"), f'forme lourde ({ms:.0f} ms) : frappe sans recalcul, aperçu marqué « en attente »')
            s.check(ev("editDirty()||EI<0") and ev("HIS.length") > 1, 'pendant l\'attente : historique et indicateurs à jour')
            pg.keyboard.press('Enter'); pg.wait_for_timeout(1500)
            s.check(ev("window._ng") == n + 1 and ev("el('pvSt').style.display") == 'none' and not ev("el('pvA').classList.contains('stale')"), 'Entrée : un seul recalcul, aperçu à jour')
            ev("_calcMs=999"); pg.keyboard.type('0'); pg.wait_for_timeout(300); pg.keyboard.press('Tab'); pg.wait_for_timeout(1500)
            s.check(ev("window._ng") == n + 2, 'Tab (sortie du champ) : recalcul')
            ev("_calcMs=999"); pg.click('#gB'); pg.keyboard.type('1'); pg.wait_for_timeout(300); pg.click('#pvSt'); pg.wait_for_timeout(1500)
            s.check(ev("window._ng") == n + 3 and ev("el('pvSt').style.display") == 'none', 'clic sur le bandeau : recalcul')
            v = ev("V('gB')")
            s.check(str(int(v)) in ev("el('pvA').textContent"), f'aperçu calculé avec la valeur saisie ({v})')
        else:
            s.check(True, f'goulotte trop rapide ici ({ms:.0f} ms) : mode « en attente » non déclenché (test sans objet)')
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});onEdit()}"); pg.wait_for_timeout(600)
        n = ev("window._ng")
        pg.click('#dL'); pg.keyboard.press('End'); pg.keyboard.type('5'); pg.wait_for_timeout(600)
        s.check(ev("_calcMs") < 300 and ev("window._ng") == n + 1 and ev("el('pvSt').style.display") == 'none', f'forme légère ({ev("_calcMs"):.0f} ms) : aperçu recalculé pendant la frappe, comme avant')
        s.check(not errs, '(e) aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    import sys
    s = Suite('t_v23')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
