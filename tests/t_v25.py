"""v2.5 — mise en page des feuilles (Plan pleine page par défaut / Compacte / Vues uniquement), ligne d'hypothèses du
cartouche, feuille 1b (débit · informations · hypothèses), contenu des hypothèses, impression (ordre, débordements)."""
import os, re
from playwright.sync_api import sync_playwright
from lib import Suite, APP, HERE

ALLPRT = 'localStorage.setItem("resaPrint",JSON.stringify({cp:true,mt:true,fa:true}))'


def page(pw, prt=True):
    b = pw.chromium.launch()
    pg = b.new_context(viewport={'width': 1400, 'height': 900}).new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
    pg.goto('file://' + APP); pg.evaluate('localStorage.clear();' + (ALLPRT if prt else '')); pg.reload()
    pg.wait_for_function('typeof gen==="function" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
    return b, pg, errs


SHEETS = """([f,ov,lay])=>{PRT.lay=lay;T.mk(f,ov);const box=document.createElement('div');box.innerHTML=gen(coll());
  return [...box.querySelectorAll('.ps')].map(s=>({t:(s.querySelector('.ps-rf')||{}).textContent||'',side:!!s.querySelector('.ps-side'),
    cl:[...s.querySelectorAll('.ps-cl')].map(x=>x.textContent),hyp:(s.querySelector('.ps-hyp')||{}).textContent||'',svg:s.querySelectorAll('.ps-c > svg').length,
    full:!!s.querySelector('.ps-bd.lay-full'),inf:s.querySelectorAll('.inf').length}))}"""


def t(s):
    with sync_playwright() as pw:
        # réglage par défaut (navigateur neuf)
        b, pg, errs = page(pw, prt=False)
        ev = pg.evaluate
        s.check(ev("PRT.lay") == 'full' and ev("el('prLay').value") == 'full', 'mise en page par défaut : Plan pleine page')
        opts = ev("[...el('prLay').options].map(o=>o.value+'|'+o.text)")
        s.check([o.split('|')[0] for o in opts] == ['full', 'compact', 'views'], f'3 choix : {opts}')
        pg.select_option('#prLay', 'views'); b.close()
        b, pg, errs = page(pw, prt=False); ev = pg.evaluate
        b.close()

        b, pg, errs = page(pw)
        ev = pg.evaluate
        pg.select_option('#prLay', 'compact'); pg.reload(); pg.wait_for_function('_ready')
        s.check(ev("PRT.lay") == 'compact', 'choix de mise en page mémorisé')
        pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))

        # ---- formes à feuille standard ----
        for f, ov in [('rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400, 'oGs': True, 'oRenX': True}), ('voile', {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10}),
                      ('special', {'dBase': 'circ', 'oPot': True, 'oConc': True, 'oFondSup': True}), ('circ', {}), ('goulotte', {}), ('para', {})]:
            F = ev(SHEETS, [f, ov, 'full']); C = ev(SHEETS, [f, ov, 'compact']); W_ = ev(SHEETS, [f, ov, 'views'])
            s.check(F[0]['full'] and not F[0]['side'] and F[0]['inf'] == 0 and F[0]['svg'] >= 2, f'[{f}] pleine page : feuille 1 = vues seules ({F[0]["svg"]} vues, aucun tableau)', str(F[0]))
            s.check(len(F) == len(C) + 1 and 'FEUILLE 1b' in F[1]['t'] and F[1]['cl'] == ['Débit · traçage · contrôles', 'Informations', 'Hypothèses'],
                    f'[{f}] pleine page : feuille 1b juste après le plan (débit · informations · hypothèses)', str([x['t'] for x in F][:3]))
            s.check(C[0]['side'] and 'Informations' in C[0]['cl'] and not C[0]['full'], f'[{f}] compacte : comme avant (vues + débit + informations sur la feuille 1)')
            s.check(len(W_) == len(C) and W_[0]['full'] and W_[0]['inf'] == 0 and not any('1b' in x['t'] for x in W_), f'[{f}] vues uniquement : vues seules, pas de feuille 1b')
            s.check(all('Hypothèses' in x['hyp'] and 'kN/m³' in x['hyp'] for x in F + C + W_), f'[{f}] ligne d\'hypothèses dans le cartouche de toutes les feuilles, 3 modes')
            s.check(all('détail feuille 1b' in x['hyp'] for x in F) and not any('détail feuille 1b' in x['hyp'] for x in C + W_), f'[{f}] renvoi « détail feuille 1b » seulement en pleine page')
            s.check(F[2:] == [] or [x['t'].split('—')[-1] for x in F[2:]] == [x['t'].split('—')[-1] for x in C[1:]], f'[{f}] feuilles annexes (CP, montage, fiche) identiques dans les 3 modes')

        # ---- formes multi-feuilles (dalle) : tableaux des feuilles CP conservés, tableau du plan de pose déplacé ----
        F = ev(SHEETS, ['dalle', {'dlPt': True}, 'full']); C = ev(SHEETS, ['dalle', {'dlPt': True}, 'compact']); W_ = ev(SHEETS, ['dalle', {'dlPt': True}, 'views'])
        cpF = [x for x in F if 'CP À DÉCOUPER' in x['t']]; cpC = [x for x in C if 'CP À DÉCOUPER' in x['t']]
        s.check(cpF and all(a['inf'] == b_['inf'] for a, b_ in zip(cpF, cpC)), 'dalle : feuilles CP à découper gardent leur tableau des pièces (tous modes)')
        pose = [x for x in F if 'PLAN DE POSE' in x['t']][0]
        s.check(pose['inf'] == 0, 'dalle pleine page : plan de pose sans tableau latéral')
        info = ev("""()=>{PRT.lay='full';T.mk('dalle',{dlPt:true});const b=document.createElement('div');b.innerHTML=gen(coll());const s=[...b.querySelectorAll('.ps')].find(x=>/INFORMATIONS/.test(x.querySelector('.ps-rf').textContent));return s?s.textContent:''}""")
        s.check('Calage des rangées' in info and 'Hypothèses' in info and 'Platelage' in info, 'dalle pleine page : calage des rangées + hypothèses sur la feuille INFORMATIONS')
        s.check(len(W_) == len(C) - 1 and not any('INFORMATIONS' in x['t'] for x in W_), 'dalle vues uniquement : pas de feuille INFORMATIONS')

        # ---- contenu des hypothèses ----
        H = lambda f, ov: ev("([f,ov])=>{const d=T.can(T.mk(f,ov)),g=d.forme==='voile'?voileGeo(d):null,R=badDims(checks(d,g))?[]:debit(d,g);return hypRows(d,g,R)}", [f, ov])
        r = H('rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400, 'oGs': True, 'oRenX': True})
        lb = [x[0] for x in r]
        s.check(lb[0] == 'Poussée du béton frais' and '25 kN/m³' in r[0][1] and 'EN 1991-1-1' in r[0][2], 'hypothèse 1 : poussée hydrostatique 25 kN/m³ (EN 1991-1-1)')
        rx = ev("()=>{const d=T.can(T.mk('rect_fond',{dL:1200,dl:800,dh:400,oGs:true,oRenX:true}));const X=rxGeo(d);return [X.crit.N,X.crit.Ncr]}")
        row = [x for x in r if x[0] == 'Renforts en croix']
        s.check(row and 'coefficient 3' in row[0][1] and re.sub(r'\s', ' ', f'{rx[1]:.2f}'.replace('.', ',')) in row[0][1].replace(' ', ' ').replace('\xa0', ' '), f'renforts : flambement d\'Euler, coefficient 3, Ncr = calcul de l\'appli ({rx[1]:.2f} kN)', str(row))
        s.check(any(x[0] == 'Goussets d\'angle' and 'à valider' in x[2] for x in r), 'goussets automatiques : marqués « règle de l\'appli — à valider »')
        # v2.6 : la flèche du CP est calculée (contenu vérifié par t_v26) ; la ligne existe toujours, tolérances toujours renvoyées au CCTP
        s.check(any(x[0] == 'Flèche du CP' and 'portée' in x[1] for x in r) and any('CCTP' in x[1] for x in r), 'limites dites : flèche du CP (calcul v2.6), tolérances selon CCTP')
        r = H('voile', {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10})
        s.check(any(x[0] == 'Renfort minimal du mannequin' for x in r) and any('1 montant' in x[1] for x in r if x[0] == 'Cerces / montants'), 'voile : renfort minimal du mannequin et 1 montant (R03)', str(r))
        r = H('special', {'dBase': 'circ', 'oPot': True, 'oFondSup': True})
        s.check(any(x[0].startswith('Poteaux') and '+ 0 mm' in x[1] for x in r) and any(x[0] == 'Cintrage du CP' for x in r), 'spéciale : perçage Ø poteau + 0 mm (défaut v2.10), cintrage à vérifier')
        r = H('dalle', {'dlPt': True})
        s.check(any(x[0] == 'Raidisseurs des joues de poutre' for x in r) and any(x[0] == 'Platelage' for x in r), 'dalle avec poutres : raidisseurs (à valider) et platelage')

        # ---- impression pleine page : ordre et débordements ----
        ev("()=>{window.print=()=>{};PRT.lay='full';PRT.cp=PRT.mt=PRT.fa=true}")
        for f, ov in [('rect_fond', {'dL': 1200, 'dl': 800, 'dh': 400, 'oGs': True, 'oRenX': True}), ('voile', {'dL': 670, 'dl': 150, 'dh': 270, 'dDcuve': 10}),
                      ('special', {'dBase': 'circ', 'oPot': True, 'oConc': True, 'oFondSup': True}), ('dalle', {'dlPt': True})]:
            r = ev("""([f,ov])=>{T.mk(f,ov);P.length=0;el('toast').textContent='';printAll();const t=[...document.querySelectorAll('#pvA .ps .ps-rf')].map(x=>x.textContent);
              const bad=[...document.querySelectorAll('#pvA .ps-c')].filter(c=>c.scrollHeight>c.clientHeight+1).length;document.body.classList.remove('pm');return [t,bad,el('toast').textContent]}""", [f, ov])
            t_, bad, toast = r
            if f != 'dalle':
                s.check(re.search(r'FEUILLE 1(/\d+)? — PLAN', t_[0]) and 'FEUILLE 1b' in t_[1], f'[{f}] impression : plan puis feuille 1b (au dos en recto-verso)', str(t_[:3]))
            s.check(bad == 0, f'[{f}] impression pleine page : aucune case qui déborde ({bad})', toast)
        s.check(not errs, 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    import sys
    s = Suite('t_v25')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
