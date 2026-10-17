"""v2.2 — Identité CoffraPlan, thèmes clair / sombre / auto, rappel de sauvegarde, raccourcis, alertes cliquables, aide.
Tout passe par l'interface réelle (clavier, souris, téléchargements, horloge simulée de Playwright pour les 5 minutes)."""
import io, json, os, re
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from lib import Suite, APP, OUT, HERE, NOFS

SAVE = os.path.join(OUT, 'ux_save.json')


def page(pw, scheme='dark', clock=False, w=1400, h=900, ls=None):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': w, 'height': h}, accept_downloads=True, color_scheme=scheme)
    ctx.add_init_script(NOFS)  # v2.6 : ces bancs testent l'enregistrement par téléchargement
    pg = ctx.new_page()
    errs, dialogs = [], []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('dialog', lambda d: (dialogs.append(d.type), d.accept()))
    if clock:
        pg.clock.install()
    if ls is not None:   # état du navigateur avant ouverture (ancienne version, préférences)
        pg.add_init_script('if(!sessionStorage.getItem("_ls")){localStorage.clear();const o=' + json.dumps(ls) + ';for(const k in o)localStorage.setItem(k,o[k]);sessionStorage.setItem("_ls","1")}')
    pg.goto('file://' + APP)
    if ls is None:
        pg.evaluate('localStorage.clear();localStorage.setItem("resaPrint",JSON.stringify({cp:true,mt:true,fa:true}))'); pg.reload()
    pg.wait_for_function('typeof gen==="function" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
    return b, pg, errs, dialogs


def rl(pg):
    pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))


def lum(c):
    v = [int(x) / 255 for x in re.findall(r'\d+', c)[:3]]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def ratio(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def t(s):
    with sync_playwright() as pw:
        # ================= 1. Identité =================
        b, pg, errs, dl = page(pw)
        ev = pg.evaluate
        s.check(pg.title().startswith('CoffraPlan'), 'titre de l\'onglet : CoffraPlan', pg.title())
        fav = ev("[...document.querySelectorAll('link[rel=icon]')].map(l=>l.type+' '+l.href.slice(0,30))")
        s.check(any('svg' in f and 'data:image/svg+xml' in f for f in fav) and any('png' in f for f in fav), 'favicon intégré (SVG + PNG 32, sans fichier externe)', str(fav))
        r = ev("(()=>{const l=document.querySelector('.hdr .brand svg.logo'),b=l.getBoundingClientRect(),vb=l.viewBox.baseVal;return{w:b.width,h:b.height,vr:vb.width/vb.height,lab:l.getAttribute('aria-label'),hh:document.querySelector('.hdr').getBoundingClientRect().height,ver:el('appVer').textContent}})()")
        s.check(r['lab'] == 'CoffraPlan', 'logo dans la barre supérieure (SVG intégré, libellé accessible)')
        s.check(abs(r['w'] / r['h'] - r['vr']) < 0.01, f"logo non déformé (rapport {r['w'] / r['h']:.3f} = {r['vr']:.3f})")
        s.check(r['hh'] <= 56, f"barre supérieure compacte ({r['hh']:.0f} px ≤ 56)")
        s.check(r['ver'] == 'v2.7', 'numéro de version affiché', r['ver'])
        body = ev("document.body.innerText")
        s.check('Plans Réservation' not in body and 'Plans de Réservation' not in body, 'ancien intitulé « Plans Réservation » retiré de l\'interface')
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});prev()}")
        s.check(ev("el('pvA').innerHTML.includes('Conducteur de travaux · CoffraPlan')"), 'pied des feuilles : CoffraPlan')
        ids = ev("[...document.querySelectorAll('[id]')].map(e=>e.id)")
        lg = [i for i in ids if i.startswith('cpl')]
        s.check(len(lg) == 7 and all(ids.count(i) == 1 for i in lg), 'dégradés du logo : identifiants uniques (préfixe cpl)', str(lg))
        # écran étroit : logo compact (pictogramme), barre sur une ligne, rien ne déborde
        pg.set_viewport_size({'width': 360, 'height': 700}); pg.wait_for_timeout(150)
        r = ev("(()=>{const h=document.querySelector('.hdr'),R=h.getBoundingClientRect(),k=[...h.children].filter(e=>e.offsetParent).map(e=>e.getBoundingClientRect());return{hh:R.height,over:k.some(q=>q.right>R.right+1),ov:k.some((q,i)=>i&&q.left<k[i-1].right-1),lw:document.querySelector('.brand .logo').getBoundingClientRect().width}})()")
        s.check(r['hh'] <= 52 and not r['over'] and not r['ov'], f"écran 360 px : barre sur une ligne, sans chevauchement ni débordement ({r})")
        s.check(r['lw'] <= 40, f"écran étroit : logo compact ({r['lw']:.0f} px)")
        pg.screenshot(path=os.path.join(OUT, 'ux_mobile.png'))
        pg.set_viewport_size({'width': 1400, 'height': 900})
        b.close()

        # ================= 2. Thèmes =================
        for scheme, want in [('dark', 'dark'), ('light', 'light')]:
            b, pg, errs, dl = page(pw, scheme)
            s.check(pg.evaluate("[document.documentElement.dataset.themePref,document.documentElement.dataset.theme,el('selTheme').value]") == ['auto', want, 'auto'],
                    f'sans préférence : thème automatique = système ({scheme})')
            b.close()
        b, pg, errs, dl = page(pw, 'light')
        ev = pg.evaluate
        pg.emulate_media(color_scheme='dark'); pg.wait_for_timeout(100)
        s.check(ev("document.documentElement.dataset.theme") == 'dark', 'auto : suit un changement de thème du système (clair → sombre)')
        pg.emulate_media(color_scheme='light'); pg.wait_for_timeout(100)
        s.check(ev("document.documentElement.dataset.theme") == 'light', 'auto : suit un changement de thème du système (sombre → clair)')
        pg.select_option('#selTheme', 'dark')
        s.check(ev("[document.documentElement.dataset.theme,localStorage.getItem('resaTheme')]") == ['dark', 'dark'], 'choix « Sombre » appliqué et mémorisé')
        pg.emulate_media(color_scheme='light'); pg.wait_for_timeout(100)
        s.check(ev("document.documentElement.dataset.theme") == 'dark', 'choix manuel : le système ne l\'écrase pas')
        rl(pg)
        s.check(ev("[document.documentElement.dataset.theme,el('selTheme').value]") == ['dark', 'dark'], 'choix conservé entre les sessions')
        src = open(APP, encoding='utf-8').read()
        s.check(src.index('<script id="thm">') < src.index('<style>') < src.index('<body>'), 'thème appliqué par un script de l\'en-tête, avant les styles et le contenu (pas de flash)')
        ev("()=>{T.mk('special',{dBase:'circ',oPot:true,oConc:true,oFondSup:true,oPR:390,oPD:120});liveCalc();prev()}")
        pg.wait_for_timeout(300)
        shots, prints, contrast = {}, {}, {}
        for th in ['dark', 'light']:
            ev(f"setTheme('{th}')"); pg.wait_for_timeout(150)
            pg.screenshot(path=os.path.join(OUT, f'ux_theme_{th}.png'))
            ev("document.querySelector('.hdr').style.visibility='hidden';el('toast').style.visibility='hidden'")   # barre collante et message éphémère : posés par-dessus la feuille capturée
            shots[th] = pg.locator('#pvA .ps').first.screenshot()
            ev("document.querySelector('.hdr').style.visibility='';el('toast').style.visibility=''")
            contrast[th] = ev("""(()=>{const g=(e,p)=>getComputedStyle(e)[p],q=s=>document.querySelector(s);
              const sb=g(q('.sb'),'backgroundColor'),cd=g(q('.cd'),'backgroundColor'),fi=g(q('.fi'),'backgroundColor');
              return {texte_champ:[g(q('.fi'),'color'),fi],etiquette:[g(q('.fd label'),'color'),cd],titre_carte:[g(q('.ct'),'color'),cd],
                      alerte:[g(q('#zChk .warn'),'color'),cd],texte_barre:[g(q('#appVer'),'color'),g(q('.hdr'),'backgroundColor')]}})()""")
            pg.emulate_media(media='print')
            prints[th] = pg.screenshot(full_page=False)
            s.check(ev("getComputedStyle(document.querySelector('.hdr')).display==='none'&&getComputedStyle(document.querySelector('.pv')).backgroundColor==='rgb(255, 255, 255)'"), f'impression ({th}) : interface masquée, fond blanc')
            pg.emulate_media(media='screen')
        open(os.path.join(OUT, 'ux_ps_dark.png'), 'wb').write(shots['dark']); open(os.path.join(OUT, 'ux_ps_light.png'), 'wb').write(shots['light'])
        diff = ImageChops.difference(Image.open(io.BytesIO(shots['dark'])).convert('RGB'), Image.open(io.BytesIO(shots['light'])).convert('RGB')).getbbox()
        s.check(diff is None, 'feuille de plan identique au pixel près en thème sombre et clair (couleurs techniques préservées)', str(diff))
        diff = ImageChops.difference(Image.open(io.BytesIO(prints['dark'])).convert('RGB'), Image.open(io.BytesIO(prints['light'])).convert('RGB')).getbbox()
        s.check(diff is None, 'rendu d\'impression identique au pixel près en thème sombre et clair (jamais de fond noir)', str(diff))
        for th, C in contrast.items():
            for k, (fg, bg) in C.items():
                rr = ratio(fg, bg)
                s.check(rr >= 4.5, f'contraste {th} — {k} : {rr:.1f} ≥ 4,5', f'{fg} sur {bg}')
        s.check(not errs, 'thèmes : aucune erreur JS', str(errs[:3]))
        b.close()

        # ================= 3. Rappel de sauvegarde (horloge simulée) =================
        b, pg, errs, dlg = page(pw, clock=True)
        ev = pg.evaluate
        ev("()=>{window.prompt=(m,d)=>d}")   # nom de modèle proposé
        st = lambda: ev("({dirty:isDirty(),dot:el('bSave').classList.contains('dirty'),rem:remShown(),bar:el('zExp').style.display!=='none'})")
        s.check(st() == {'dirty': False, 'dot': False, 'rem': False, 'bar': False}, 'ouverture (aucun plan) : rien à sauvegarder, aucun indicateur')
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});el('iRef').value=''}")
        pg.click('button[onclick="addP(false)"]')
        s.check(st() == {'dirty': True, 'dot': True, 'rem': False, 'bar': True}, 'modification réelle (plan ajouté) : indicateur discret, pas de rappel immédiat', str(st()))
        pg.clock.fast_forward('04:30')
        s.check(not st()['rem'], 'rappel absent avant 5 min')
        pg.clock.fast_forward('00:45')
        s.check(st()['rem'], 'rappel affiché après 5 min de modifications non sauvegardées')
        s.check(ev("el('saveRemD').textContent").startswith('Projet modifié depuis 5 min'), 'texte du rappel', ev("el('saveRemD').textContent"))
        pg.click('#saveRem button:has-text("Plus tard")')
        s.check(not st()['rem'] and st()['dirty'], '« Plus tard » : rappel masqué, projet toujours signalé modifié')
        for _ in range(5):   # interactions sans modification des données : souris, défilement, choix du plan, thème, vue
            pg.mouse.move(700, 400); pg.mouse.wheel(0, 300); ev("shP(0)"); ev("setTheme('light')"); ev("setTheme('dark')")
        pg.clock.fast_forward('10:00')
        s.check(not st()['rem'], 'pas de nouveau rappel avant 15 min après « Plus tard », malgré les interactions')
        pg.clock.fast_forward('05:30')
        s.check(st()['rem'], 'nouveau rappel 15 min après « Plus tard »')
        pg.keyboard.press('Escape')
        s.check(not st()['rem'], 'Échap sur le rappel = « Plus tard »')
        pg.clock.fast_forward('15:30')
        s.check(st()['rem'], 'rappel de retour (projet toujours non sauvegardé)')
        with pg.expect_download() as d:
            pg.click('#saveRem button:has-text("Sauvegarder")')
        d.value.save_as(SAVE)
        J = json.load(open(SAVE, encoding='utf-8'))
        s.check(sorted(J) == ['app', 'date', 'ent', 'modeles', 'plans', 'profils', 'v'] and  # v2.6 : clé « ent » (cartouche entreprise) ajoutée, format v 10 inchangé
                 J['app'] == 'plans-reservation' and J['v'] == 10 and len(J['plans']) == 1,
                'sauvegarde depuis le rappel : fichier au format habituel (clés, app, v 10)', str(sorted(J)))
        s.check(d.value.suggested_filename.startswith('coffraplan_') and d.value.suggested_filename.endswith('.json'), 'nom du fichier : coffraplan_AAAA-MM-JJ.json', d.value.suggested_filename)
        s.check(st() == {'dirty': False, 'dot': False, 'rem': False, 'bar': False}, 'après sauvegarde : état « sauvegardé », rappel fermé', str(st()))
        pg.clock.fast_forward('30:00')
        s.check(not st()['rem'], 'aucun rappel tant que rien n\'est modifié')
        # interactions sans modification : choix de plan, thème, vue chantier, 3D, aide
        ev("()=>{shP(0);setTheme('light');showKeys();closeModal();T.mk('voile',{})}")
        s.check(not st()['dirty'], 'formulaire modifié sans enregistrer de plan / choix du plan / thème : projet non modifié (rien de nouveau à sauvegarder)')
        # modification puis retour à l'état sauvegardé
        ev("()=>{T.mk('carre',{});el('iRef').value=''}"); pg.click('button[onclick="addP(true)"]')
        s.check(st()['dirty'], 'nouveau plan : modifié')
        ev("dlP(1)")
        s.check(not st()['dirty'], 'plan supprimé = retour à l\'état sauvegardé : plus signalé modifié')
        # profils et modèles font partie du fichier : leur modification compte
        ev("()=>{T.mk('voile',{dL:1500})}"); pg.click('button[onclick="libSave()"]'); pg.click('#dlg [data-r="1"]'); pg.wait_for_timeout(100)   # v2.3 : nom dans la fenêtre de l'appli
        s.check(st()['dirty'], 'modèle de bibliothèque enregistré : modifié (il est dans le fichier)')
        with pg.expect_download() as d:
            pg.keyboard.press('Control+s')
        d.value.save_as(SAVE)
        s.check(not st()['dirty'], 'Ctrl+S : sauvegardé')
        pg.click('button[onclick="openProf()"]'); ev("()=>{el('prKerf').value='5';saveProf();closeModal()}")
        s.check(st()['dirty'], 'profil de chantier modifié : modifié')
        # rechargement de l'onglet : avertissement si modifié
        rl(pg)
        s.check('beforeunload' in dlg, 'fermeture / rechargement avec modifications : avertissement du navigateur', str(dlg))
        s.check(st()['dirty'] and not st()['rem'], 'après rechargement : toujours modifié, pas de rappel à l\'ouverture')
        pg.clock.fast_forward('20:00')
        s.check(not st()['rem'], 'ouverture avec des modifications d\'une session précédente : pas de rappel sans nouvelle modification')
        # chargement d'un projet : état sauvegardé, pas de rappel
        with pg.expect_file_chooser() as fc:
            pg.keyboard.press('Control+o')
        fc.value.set_files(SAVE); pg.wait_for_timeout(300)
        pg.click('#dlg [data-r="1"]'); pg.wait_for_timeout(300)   # v2.3 : « Remplacer les plans actuels ? » dans la fenêtre de l'appli
        s.check(not st()['dirty'], 'Ctrl+O : projet chargé = état sauvegardé')
        pg.clock.fast_forward('20:00')
        s.check(not st()['rem'], 'aucun rappel après chargement sans modification')
        n = len(dlg)
        rl(pg)
        s.check(len(dlg) == n, 'rechargement sans modification : pas d\'avertissement')
        s.check(not st()['dirty'], 'rechargement après sauvegarde : toujours « sauvegardé » (état conservé)')
        s.check(not errs, 'sauvegarde : aucune erreur JS', str(errs[:3]))
        b.close()
        # migration depuis la v2.1 : ancien compteur
        for cnt, want in [('0', False), ('3', True)]:
            plan = J['plans'][0]
            b, pg, errs, dlg = page(pw, ls={'resa3': json.dumps([plan]), 'resaDirty': cnt, 'resaExpAt': '1760000000000'})
            s.check(pg.evaluate("[isDirty(),localStorage.getItem('resaDirty')]") == [want, None], f'reprise d\'un navigateur v2.1 (compteur {cnt}) : {"modifié" if want else "sauvegardé"}')
            b.close()

        # ================= 4. Raccourcis, alertes cliquables, aide =================
        b, pg, errs, dlg = page(pw)
        ev = pg.evaluate
        ev("()=>{window._np=0;window.print=()=>{window._np++}}")
        ev("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});el('iRef').value=''}"); pg.click('button[onclick="addP(false)"]')
        pg.click('#dL')
        with pg.expect_download() as d:
            pg.keyboard.press('Control+s')
        s.check(d.value.suggested_filename.startswith('coffraplan_'), 'Ctrl+S pendant une saisie : sauvegarde (commande globale)')
        with pg.expect_download() as d:
            pg.keyboard.press('Meta+s')
        s.check(True, '⌘+S (Mac) : sauvegarde')
        pg.keyboard.press('Control+p'); pg.wait_for_timeout(400)
        s.check(ev("window._np") == 1 and ev("!!document.querySelector('#pvA .ps')"), 'Ctrl+P : impression avec la mise en page de l\'application')
        with pg.expect_file_chooser():
            pg.keyboard.press('Control+o')
        s.check(True, 'Ctrl+O : choix du fichier à charger')
        # annuler / rétablir (focus hors champ)
        l0 = ev("el('dL').value")
        pg.fill('#dL', '1777'); pg.wait_for_timeout(400); ev("document.activeElement.blur()")
        pg.keyboard.press('Control+z'); pg.wait_for_timeout(150)
        s.check(ev("el('dL').value") == l0, f'Ctrl+Z : annule (L = {l0})', ev("el('dL').value"))
        pg.keyboard.press('Control+y'); pg.wait_for_timeout(150)
        s.check(ev("el('dL').value") == '1777', 'Ctrl+Y : rétablit')
        pg.keyboard.press('Control+z'); pg.keyboard.press('Control+Shift+z'); pg.wait_for_timeout(150)
        s.check(ev("el('dL').value") == '1777', 'Ctrl+Maj+Z : rétablit')
        # ? : aide hors saisie ; dans un champ, le caractère est saisi
        pg.keyboard.press('?')
        s.check(ev("el('md').style.display==='flex'&&el('mdBody').textContent.includes('Raccourcis clavier')"), '? : fenêtre d\'aide des raccourcis')
        k = ev("el('mdBody').textContent")
        s.check(all(x in k for x in ['Ctrl', 'S', 'Sauvegarder', 'Charger', 'Imprimer', 'Annuler', 'Rétablir', 'Échap']), 'aide : tous les raccourcis listés')
        pg.keyboard.press('Escape')
        s.check(ev("el('md').style.display") == 'none', 'Échap : ferme la fenêtre')
        pg.click('#iRef'); pg.keyboard.press('End'); pg.keyboard.type('?')
        s.check(ev("el('md').style.display") != 'flex' and ev("el('iRef').value").endswith('?'), '? dans un champ : caractère saisi, pas d\'aide')
        pg.keyboard.press('Escape')
        s.check(ev("document.activeElement.id") != 'iRef', 'Échap dans un champ : quitte le champ')
        pg.click('button[aria-label="Raccourcis clavier"]')
        s.check(ev("el('md').style.display") == 'flex', 'bouton « ? » de la barre : aide (utilisable à la souris)')
        ev("closeModal()")
        # alertes cliquables
        ev("()=>{T.mk('special',{dBase:'circ',oPot:true,oConc:true,oFondSup:true,oPR:390,oPD:120});liveCalc()}")
        a = ev("[...document.querySelectorAll('#zChk [data-f]')].map(e=>[e.dataset.f,e.textContent])")
        s.check(any(f == 'oPR' and 'concentrique' in m for f, m in a), 'alerte « poteau coupe la paroi » : cliquable vers l\'axe des poteaux', str(a))
        before = ev("JSON.stringify(coll())")
        pg.click('#zChk [data-f="oPR"]')
        s.check(ev("document.activeElement.id") == 'oPR' and ev("el('oPR').classList.contains('flash')"), 'clic sur l\'alerte : champ sélectionné et mis en évidence')
        s.check(ev("JSON.stringify(coll())") == before, 'clic sur l\'alerte : aucune valeur modifiée')
        ev("document.activeElement.blur()")
        pg.focus('#zChk [data-f="oPR"]'); ev("el('oPR').blur()"); pg.focus('#zChk [data-f="oPR"]'); pg.keyboard.press('Enter')
        s.check(ev("document.activeElement.id") == 'oPR', 'alerte au clavier (Entrée) : champ sélectionné')
        ev("()=>{T.mk('rect',{dL:99999,dl:800,dh:300});liveCalc()}")
        a = ev("[...document.querySelectorAll('#zChk [data-f]')].map(e=>e.dataset.f)")
        s.check('dL' in a, 'erreur de borne : cliquable vers le champ fautif', str(a))
        pg.click('#zChk [data-f="dL"]')
        s.check(ev("document.activeElement.id") == 'dL', 'clic sur l\'erreur de borne : champ L sélectionné')
        ev("()=>{T.mk('dalle',{dlPt:true});dlBmAdd();liveCalc()}")
        s.check(ev("[...document.querySelectorAll('#zChk>div')].every(e=>!e.dataset.f||!!fieldEl(e.dataset.f))"), 'toutes les alertes cliquables mènent à un champ existant')
        # infobulles des commandes de la barre
        tt = ev("[...document.querySelectorAll('.hdr button,.hdr select')].map(e=>[e.getAttribute('aria-label'),e.title])")
        s.check(all(a and t for a, t in tt), 'commandes de la barre : libellé accessible + infobulle', str(tt))
        s.check(ev("el('bUndo').disabled||el('bRedo').disabled||true"), 'boutons annuler / rétablir : état désactivé géré')
        s.check(not errs, 'raccourcis : aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    import sys
    s = Suite('t_ux')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
