"""Captures d'écran du mode d'emploi, prises sur l'application du dépôt (app/CoffraPlan.html ou variable APP).
Appelé par build.py ; écrit docs/manuel/img/*.png. Plans d'exemple sur un chantier fictif."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tests'))
from lib import open_app, APP
from playwright.sync_api import sync_playwright
D = os.path.join(HERE, 'img') + os.sep
os.makedirs(D, exist_ok=True)
BADGE = """(L)=>{document.querySelectorAll('.mbadge').forEach(b=>b.remove());L.forEach(([sel,n,dx,dy])=>{const e=document.querySelector(sel);if(!e)return;const r=e.getBoundingClientRect();
 const b=document.createElement('div');b.className='mbadge';b.textContent=n;Object.assign(b.style,{position:'fixed',left:(r.left+(dx||0))+'px',top:(r.top+(dy||0))+'px',width:'26px',height:'26px',borderRadius:'50%',
 background:'#d62828',color:'#fff',font:'700 15px Arial',display:'flex',alignItems:'center',justifyContent:'center',zIndex:9999,boxShadow:'0 0 0 3px #fff'});document.body.appendChild(b)})}"""
OK = '#dlg [data-r="1"]'
with sync_playwright() as p:
    b, pg, errs = open_app(p, APP, width=1440, height=900)
    ev = pg.evaluate
    ev("()=>{window.print=()=>{};setTheme('light')}")
    shot = lambda n, **k: pg.screenshot(path=D + n + '.png', **k)
    # accueil
    shot('01_accueil', clip={'x': 0, 'y': 0, 'width': 1440, 'height': 900})
    # plans d'exemple
    ev("()=>{el('zWel').style.display='none'}")
    for ch, ouv, f, ov, ref, ind in [('CHANTIER DÉMO', 'Clarificateur', 'special', {'dBase': 'circ', 'oPot': True, 'oConc': True, 'oFondSup': True}, 'R01', 'A'),
                                     ('CHANTIER DÉMO', 'Clarificateur', 'rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400, 'oGs': True, 'oRenX': True}, 'R02', 'A'),
                                     ('CHANTIER DÉMO', 'Bassin tampon', 'voile', {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10}, 'R03', '0'),
                                     ('CHANTIER DÉMO', 'Bassin tampon', 'circ', {}, 'F01', ''),
                                     ('CHANTIER DÉMO', 'Clarificateur', 'rect_fond', {'dL': 1300, 'dl': 800, 'dh': 400, 'oGs': True, 'oRenX': True}, 'R02', 'B')]:
        ev("([ch,ouv,f,ov,ref,ind])=>{T.mk(f,ov);el('iCh').value=ch;el('iOuv').value=ouv;el('iRef').value=ref;el('iInd').value=ind;EI=-1;updBtn()}", [ch, ouv, f, ov, ref, ind])
        pg.click('#bAdd')
        if ev("dlgOpen()"): pg.click(OK)
    ev("()=>{shP(0)}"); pg.wait_for_timeout(500)
    ev("()=>{document.querySelector('.sb').scrollTo(0,0);el('toast').style.opacity='0'}"); pg.wait_for_timeout(200)
    ev(BADGE, [['.brand', 1, 168, 12], ['#bUndo', 2, -32, 2], ['#bSave', 3, -32, 2], ['#selTheme', 4, -32, 2], ['#sbF .cd', 5, 270, 8], ['#pvA .ps', 6, 860, 8]])
    shot('02_interface')
    ev("document.querySelectorAll('.mbadge').forEach(b=>b.remove())")
    shot('03_barre', clip={'x': 0, 'y': 0, 'width': 1440, 'height': 52})
    # formulaire + alerte cliquable
    ev("()=>{shP(0);el('oPR').value='390';el('oPD').value='120';onEdit()}"); pg.wait_for_timeout(600)
    ev("document.getElementById('zChk').scrollIntoView({block:'center'})"); pg.wait_for_timeout(200)
    shot('04_alertes', clip={'x': 0, 'y': 52, 'width': 360, 'height': 848})
    ev("()=>{shP(0)}"); pg.wait_for_timeout(400)
    # pastille modifié
    pg.fill('#dD', '1100'); pg.wait_for_timeout(500)
    ev("el('bAdd').scrollIntoView({block:'center'})"); pg.wait_for_timeout(150)
    bx = pg.locator('#bAdd').bounding_box()
    shot('05_modifie', clip={'x': 0, 'y': bx['y'] - 120, 'width': 360, 'height': 260})
    ev("()=>{shP(0)}"); pg.wait_for_timeout(300)
    # cartes repliées
    pg.click('#sbF .cd:nth-of-type(1) > .ct'); pg.click('#sbF .cd:nth-of-type(2) > .ct')
    ev("document.querySelector('.sb').scrollTo(0,0)"); pg.wait_for_timeout(150)
    shot('06_replie', clip={'x': 0, 'y': 52, 'width': 360, 'height': 420})
    pg.click('#sbF .cd:nth-of-type(1) > .ct'); pg.click('#sbF .cd:nth-of-type(2) > .ct')
    # feuilles du plan
    ev("()=>{PRT.cp=PRT.mt=PRT.fa=true;shP(1);prev()}"); pg.wait_for_timeout(600)
    ev("async()=>{await glSheets(el('pvA'))}"); pg.wait_for_timeout(200)  # v2.10 : vues 3D des feuilles en WebGL
    ev("document.querySelector('.hdr').style.visibility='hidden';el('toast').style.visibility='hidden'")
    S = pg.locator('#pvA .ps')
    T = ev("[...document.querySelectorAll('#pvA .ps')].map(s=>(s.querySelector('.ps-rf')||{}).textContent||'')")
    idx = lambda k: next(i for i, t in enumerate(T) if k in t)  # feuilles repérées par leur titre (l'ordre dépend de la mise en page)
    S.nth(0).screenshot(path=D + '07_feuille_plan.png')
    S.nth(idx('FEUILLE 1b')).screenshot(path=D + '07b_feuille_1b.png')
    S.nth(idx('CP À DÉCOUPER')).screenshot(path=D + '08_feuille_cp.png')
    S.nth(idx('MONTAGE')).screenshot(path=D + '09_feuille_montage.png')
    S.nth(len(T) - 1).screenshot(path=D + '10_fiche_atelier.png')
    ev("document.querySelector('.hdr').style.visibility='';el('toast').style.visibility=''")
    ev("()=>{PRT.cp=PRT.mt=PRT.fa=false;prev()}")
    # liste des plans
    ev("document.querySelector('.sb').scrollTo(0,99999)"); pg.fill('#plQ', ''); pg.wait_for_timeout(200)
    bx = pg.locator('#sl').bounding_box()
    shot('11_liste', clip={'x': 0, 'y': bx['y'] - 70, 'width': 360, 'height': bx['height'] + 190})
    # dialogue + toast annuler
    ev("clearAll()"); pg.wait_for_timeout(150)
    bx = pg.locator('#dlgB').bounding_box(); shot('12_question', clip={'x': bx['x'] - 10, 'y': bx['y'] - 10, 'width': bx['width'] + 20, 'height': bx['height'] + 20})
    pg.keyboard.press('Escape')
    # rappel de sauvegarde
    ev("()=>{el('saveRemD').textContent='Projet modifié depuis 5 min sans sauvegarde (5 plans).';el('saveRem').style.display='block'}")
    bx = pg.locator('#saveRem').bounding_box(); shot('13_rappel', clip={'x': bx['x'] - 10, 'y': bx['y'] - 10, 'width': bx['width'] + 20, 'height': bx['height'] + 20})
    ev("remHide()")
    # profil chantier
    ev("()=>{shP(0);openProf()}"); pg.wait_for_timeout(200)
    bx = pg.locator('#mdBody').bounding_box(); shot('14_profil', clip={'x': bx['x'] - 6, 'y': bx['y'] - 6, 'width': bx['width'] + 12, 'height': bx['height'] + 12}); ev("closeModal()")
    # série
    ev("openSeries()"); pg.fill('#serT', 'Réf\tForme\tL\tl\th\tNombre\nT1\tRectangulaire\t1000\t600\t250\t2\nF1\tFourreau\t\t\t200\t4\nT2\t\t800\t800\t300\t\nX1\tbidule\t1\t1\t1\t1'); ev("serAnalyse()"); pg.wait_for_timeout(300)
    bx = pg.locator('#mdBody').bounding_box(); shot('15_serie', clip={'x': bx['x'] - 6, 'y': bx['y'] - 6, 'width': bx['width'] + 12, 'height': bx['height'] + 12}); ev("closeModal()")
    # comparaison
    ev("()=>{shP(4);showCmp(1,4)}"); pg.wait_for_timeout(400)
    ev("document.querySelector('.hdr').style.visibility='hidden'")
    pg.locator('#pvA .ps').first.screenshot(path=D + '16_comparaison.png')
    ev("document.querySelector('.hdr').style.visibility=''")
    ev("()=>{VIEW='plan';shP(0)}"); pg.wait_for_timeout(300)
    # auto-contrôle avec corrections
    ev("()=>{T.mk('rect',{dL:1600,dl:1400,dh:1000,oRenX:true,oRenXs:'t50'});EI=-1;updBtn();autoControl(false)}"); pg.wait_for_timeout(400)
    bx = pg.locator('#mdBody').bounding_box(); shot('17_autocontrole', clip={'x': bx['x'] - 6, 'y': bx['y'] - 6, 'width': bx['width'] + 12, 'height': min(bx['height'] + 12, 860)}); ev("closeModal()")
    # export
    ev("()=>{shP(0);openExport()}"); pg.wait_for_timeout(200)
    bx = pg.locator('#mdBody').bounding_box(); shot('18_export', clip={'x': bx['x'] - 6, 'y': bx['y'] - 6, 'width': bx['width'] + 12, 'height': bx['height'] + 12}); ev("closeModal()")
    # raccourcis
    ev("showKeys()"); pg.wait_for_timeout(150)
    bx = pg.locator('#mdBody').bounding_box(); shot('19_raccourcis', clip={'x': bx['x'] - 6, 'y': bx['y'] - 6, 'width': bx['width'] + 12, 'height': bx['height'] + 12}); ev("closeModal()")
    # 3D
    ev("()=>{shP(0);open3D()}"); pg.wait_for_function("V3D.gl===true", timeout=20000); ev("()=>{v3Preset('iso')}"); pg.wait_for_timeout(300)
    shot('20_3d'); ev("close3D()")
    # récap chantier
    ev("showChantier()"); pg.wait_for_timeout(500)
    ev("document.querySelector('.hdr').style.visibility='hidden'")
    pg.locator('#pvA .ps').first.screenshot(path=D + '21_recap.png')
    ev("document.querySelector('.hdr').style.visibility=''")
    ev("()=>{VIEW='plan';shP(0)}")
    # gabarit 1:1 (fenêtre dédiée)
    html = ev("()=>{shP(2);const d=canon(coll());const r=gabHtml(d,'a4');return typeof r==='string'?r:(r.html||'')}")
    if html:
        g = pg.context.new_page(); g.set_viewport_size({'width': 1200, 'height': 900}); g.set_content(html); g.wait_for_timeout(500); g.screenshot(path=D + '22_gabarit.png'); g.close()
    # mode chantier
    pg.set_viewport_size({'width': 1180, 'height': 820})
    ev("()=>{shP(1);openChm();el('chm').classList.add('kon');chmFit()}"); pg.wait_for_timeout(500)
    pg.click('#chmC input[data-t]'); pg.wait_for_timeout(100)
    shot('23_chantier'); ev("closeChm()")
    # thème sombre
    pg.set_viewport_size({'width': 1440, 'height': 900}); ev("()=>{setTheme('dark');shP(0)}"); pg.wait_for_timeout(400)
    shot('24_sombre'); ev("setTheme('light')")
    # mobile
    pg.set_viewport_size({'width': 390, 'height': 760}); pg.wait_for_timeout(300); shot('25_mobile')
    # v2.6 : cartouche entreprise + note d'hypothèses (entreprise fictive)
    pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(200)
    ev("""()=>{const c=document.createElement('canvas');c.width=120;c.height=40;const x=c.getContext('2d');x.fillStyle='#1f5fbf';x.fillRect(0,0,120,40);x.fillStyle='#fff';x.font='bold 20px Arial';x.fillText('DÉMO BTP',8,27);
      ENT={nom:'DÉMO BTP',ligne:'Agence Est — 03 00 00 00 00',des:'K. TRINH',logo:c.toDataURL('image/png')};VIEW='plan';shP(1);prev()}"""); pg.wait_for_timeout(400)
    ev("document.querySelector('.hdr').style.visibility='hidden'")
    pg.locator('#pvA .ps').first.locator('.ps-h').screenshot(path=D + '26_cartouche.png')
    ev("document.querySelector('.hdr').style.visibility=''")
    ev("showNote()"); pg.wait_for_timeout(300)
    ev("document.querySelector('.hdr').style.visibility='hidden'")
    pg.locator('#pvA .ps').nth(2).screenshot(path=D + '27_note.png')
    ev("document.querySelector('.hdr').style.visibility='';VIEW='plan';ENT={}")
    # v3.0 : cotes d'implantation (vue de dessus de la forme spéciale avec poteaux)
    ev("()=>{shP(0);VIEW='plan';prev()}"); pg.wait_for_timeout(400)
    ev("document.querySelector('.hdr').style.visibility='hidden'")
    pg.locator('#pvA .ps').first.locator('.ps-c').first.screenshot(path=D + '28_implantation.png')
    ev("document.querySelector('.hdr').style.visibility=''")
    errs = [e for e in errs if 'net::' not in e]
    assert not errs, errs
    b.close()
