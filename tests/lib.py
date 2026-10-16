"""Outils communs du banc de tests (Playwright / Chromium). Application testée : app/CoffraPlan.html (ou variable APP)."""
import json, os, sys, time, traceback
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.environ.get('APP', os.path.join(HERE, '..', 'app', 'CoffraPlan.html')))
NOFS = 'window.showSaveFilePicker = undefined; window.showOpenFilePicker = undefined;'  # v2.6 : repli téléchargement
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)


class Suite:
    def __init__(self, name):
        self.name, self.ok, self.ko, self.msgs = name, 0, 0, []

    def check(self, cond, label, detail=''):
        if cond:
            self.ok += 1
        else:
            self.ko += 1
            self.msgs.append(f'  ✗ {label}' + (f' — {detail}' if detail else ''))
        return cond

    def report(self):
        print(f'[{self.name}] {self.ok} OK, {self.ko} KO')
        for m in self.msgs[:60]:
            print(m)
        res = {'suite': self.name, 'ok': self.ok, 'ko': self.ko, 'msgs': self.msgs}
        with open(os.path.join(OUT, self.name + '.json'), 'w') as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        return self.ko == 0


def open_app(pw, app=None, width=1400, height=1000):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': width, 'height': height}, accept_downloads=True)
    # v2.6 : l'appli écrit directement dans un fichier (File System Access) quand le navigateur le permet ; les bancs
    # existants testent le repli par téléchargement (t_v26 teste l'écriture directe avec un faux fichier)
    ctx.add_init_script(NOFS)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)+' @ '+(e.stack or '')[:400]))
    pg.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' and 'fonts.g' not in m.text else None)
    pg.on('dialog', lambda d: d.accept())
    pg.goto('file://' + (app or APP))
    pg.evaluate('localStorage.clear()')
    # v2.4 : feuilles annexes décochées par défaut dans l'appli ; les tests les activent pour en couvrir le contenu
    pg.evaluate('localStorage.setItem("resaPrint",JSON.stringify({cp:true,mt:true,fa:true}))')
    pg.reload()
    pg.wait_for_function('typeof gen==="function" && typeof _ready!=="undefined" && _ready')
    pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
    return b, pg, errs


def run(name, fn, app=None):
    s = Suite(name)
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, app)
        try:
            fn(s, pg)
        except Exception as e:
            s.check(False, 'exception', traceback.format_exc()[-1500:])
        s.check(not [e for e in errs if 'net::' not in e], 'erreurs JS de la page', '; '.join(errs[:5]))
        b.close()
    return s.report()
