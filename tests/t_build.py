"""Phase 8 : construction du livrable app/CoffraPlan.html depuis les sources (modules/import/assembler.py).
Demande de Kévin du 22/10/2026 : le HTML autonome n'est plus versionné ; il est construit (CI, tests, poste) de façon déterministe à
partir de app/CoffraPlan.source.html, des modules et des dépendances vérifiées par empreinte ; il reste un fichier unique qui
fonctionne en file://, sans réseau ni installation.
Contrôlé : source sans bloc généré ; construction reproductible et à jour ; dépendance altérée refusée ; livrable ignoré par git ;
essai réel du livrable en file:// (projets IndexedDB, PDF.js, PP-OCRv6, Tesseract, three.js, exports) sans aucune requête réseau."""
import hashlib, json, os, shutil, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, APP, HERE, NOFS
import pdf_ocr_fictifs as PO

ROOT = os.path.abspath(os.path.join(HERE, '..'))
ASM = os.path.join(ROOT, 'modules', 'import', 'assembler.py')
BLOCS = ['cpi-src', 'fonts-src', 'three-src', 'pdfjs-src', 'pdfjs-worker-src', 'tess-src', 'tess-worker-src', 'tess-core-src', 'tess-wasm', 'tess-fra',
         'ppocr-ort-src', 'ppocr-ort-mjs', 'ppocr-ort-wasm', 'ppocr-rec', 'ppocr-dict']


def t(s):
    src = open(os.path.join(ROOT, 'app', 'CoffraPlan.source.html'), encoding='utf-8').read()
    s.check(all(src.count(f'<!--@bloc {b}-->') == 1 for b in BLOCS) and 'id="ppocr-rec"' not in src and len(src.encode()) < 2_000_000,
            'source : un marqueur par bloc généré, aucune dépendance recopiée (source < 2 Mo)', f'{len(src.encode())} octets')
    s.check('id="appVer">v3.1<' in src, 'source : version affichée v3.1')
    # reproductible et à jour
    h1 = hashlib.sha256(open(APP, 'rb').read()).hexdigest()
    r = subprocess.run([sys.executable, ASM], capture_output=True, text=True)
    h2 = hashlib.sha256(open(APP, 'rb').read()).hexdigest()
    rc = subprocess.run([sys.executable, ASM, '--check'], capture_output=True, text=True)
    s.check(r.returncode == 0 and h1 == h2 and rc.returncode == 0 and 'inchangé' in r.stdout, 'construction déterministe : mêmes sources → mêmes octets ; --check vert', r.stdout + rc.stdout + rc.stderr)
    html = open(APP, encoding='utf-8').read()
    s.check(all(html.count(f'id="{b}"') == 1 for b in BLOCS) and '<!--@bloc' not in html, 'livrable : chaque bloc présent une fois, aucun marqueur restant')
    s.check('fonts.googleapis' not in html and 'fonts.gstatic' not in html and not __import__('re').search(r'<link[^>]+href="https?:', src) and not __import__('re').search(r'(?:src|href)="https?:', html), 'aucune feuille ni police distante (Google Fonts retiré, polices embarquées)')
    s.check(36_000_000 < len(html.encode()) < 40_000_000, f'livrable : taille attendue ({len(html.encode())} octets)')
    # --check détecte un livrable modifié à la main
    tmp = tempfile.mkdtemp()
    try:
        for d in ['app', os.path.join('modules', 'import')]:
            shutil.copytree(os.path.join(ROOT, d), os.path.join(tmp, d), ignore=shutil.ignore_patterns('CoffraPlan.html', '__pycache__'))
        a2 = os.path.join(tmp, 'modules', 'import', 'assembler.py')
        ok = subprocess.run([sys.executable, a2], capture_output=True, text=True).returncode == 0
        with open(os.path.join(tmp, 'app', 'CoffraPlan.html'), 'a', encoding='utf-8') as f:
            f.write('<!-- retouche -->')
        r = subprocess.run([sys.executable, a2, '--check'], capture_output=True, text=True)
        s.check(ok and r.returncode != 0 and 'différent' in r.stdout + r.stderr, '--check : livrable retouché à la main détecté', r.stdout + r.stderr)
        os.remove(os.path.join(tmp, 'app', 'CoffraPlan.html'))
        r = subprocess.run([sys.executable, a2, '--check'], capture_output=True, text=True)
        s.check(r.returncode != 0 and 'absent' in r.stdout + r.stderr, '--check : livrable absent signalé', r.stdout + r.stderr)
        # dépendance altérée (three.js) : refusée, aucun livrable écrit
        p3 = os.path.join(tmp, 'app', 'vendor', 'three', 'three.module.min.js')
        with open(p3, 'ab') as f:
            f.write(b'//x')
        r = subprocess.run([sys.executable, a2], capture_output=True, text=True)
        s.check(r.returncode != 0 and 'SHA-256' in r.stdout + r.stderr and not os.path.exists(os.path.join(tmp, 'app', 'CoffraPlan.html')),
                'dépendance altérée (three.js) : construction refusée (empreinte SHA-256), aucun livrable', r.stdout + r.stderr)
        # marqueur manquant dans la source
        p = os.path.join(tmp, 'app', 'CoffraPlan.source.html'); s2 = open(p, encoding='utf-8').read().replace('<!--@bloc tess-fra-->', '')
        open(p, 'w', encoding='utf-8').write(s2); shutil.copy(os.path.join(ROOT, 'app', 'vendor', 'three', 'three.module.min.js'), p3)
        r = subprocess.run([sys.executable, a2], capture_output=True, text=True)
        s.check(r.returncode != 0 and 'marqueurs' in r.stdout + r.stderr, 'source sans un marqueur : construction refusée', r.stdout + r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # git : livrable jamais versionné ; sources et dépendances versionnées
    ls = subprocess.run(['git', 'ls-files', 'app/CoffraPlan.html', 'app/CoffraPlan.source.html', 'app/vendor/three/three.module.min.js',
                         'modules/import/vendor/ppocr/PP-OCRv6_rec_small.onnx.gz'], cwd=ROOT, capture_output=True, text=True).stdout.split()
    ig = subprocess.run(['git', 'check-ignore', '-q', 'app/CoffraPlan.html'], cwd=ROOT).returncode
    s.check('app/CoffraPlan.html' not in ls and ig == 0, 'git : app/CoffraPlan.html ignoré, non versionné')
    s.check(set(ls) >= {'app/CoffraPlan.source.html', 'modules/import/vendor/ppocr/PP-OCRv6_rec_small.onnx.gz'},
            'git : source et dépendances (poids OCR compris) versionnées', ' '.join(ls))

    # essai réel du livrable en file://, réseau coupé
    F = PO.fichiers(tempfile.mkdtemp())
    with sync_playwright() as pw:
        # surveillance posée sur le contexte AVANT la 1re navigation : toute requête hors file: / blob: / data: est notée puis bloquée,
        # sans exception de domaine (polices comprises), workers et sous-ressources compris
        b = pw.chromium.launch(); ctx = b.new_context(viewport={'width': 1400, 'height': 1000}, accept_downloads=True); ctx.add_init_script(NOFS)
        net, errs = [], []
        ctx.on('request', lambda q: None if q.url.startswith(('file:', 'blob:', 'data:')) else net.append(q.url))
        ctx.route(lambda u: not u.startswith(('file:', 'blob:', 'data:')), lambda q: q.abort())
        pg = ctx.new_page(); J = pg.evaluate
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' else None)
        pg.on('dialog', lambda d: d.accept()); pg.on('filechooser', lambda f: None)
        pg.goto('file://' + APP); pg.wait_for_function('typeof gen==="function" && _ready')
        s.check(J('document.fonts.check("600 13px Barlow") && document.fonts.check("700 13px \'Barlow Condensed\'") && document.fonts.check("400 11px \'JetBrains Mono\'")')
                and J('[...document.fonts].filter(f=>f.status==="loaded").map(f=>f.family.replace(/["\']/g,"")).filter((v,i,a)=>a.indexOf(v)===i).sort().join()') == 'Barlow,Barlow Condensed,JetBrains Mono',
                'polices Barlow, Barlow Condensed, JetBrains Mono chargées depuis le livrable (aucune police distante)',
                J('[...document.fonts].map(f=>f.family+" "+f.weight+" "+f.status).join(" | ")'))
        pg.add_script_tag(path=os.path.join(HERE, 'helpers.js'))
        s.check(J('location.protocol') == 'file:' and J('[STO.mode,el("appVer").textContent]') == ['idb', 'v3.1'], 'file:// : application ouverte, projets IndexedDB, v3.1')
        J("()=>{T.mk('rect',{dL:1200,dl:800,dh:300});el('iRef').value='B1';addP(false);if(dlgOpen())dlgEnd(true)}")
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        s.check(J('P.length') == 1, 'file:// : projet retrouvé après rechargement')
        r = J("async()=>{const T3=await v3Three();return !!(T3&&T3.WebGLRenderer)}")
        s.check(r, 'three.js chargé depuis le livrable (vue 3D)')
        r = J("async()=>{const d=P[0],x=dxfPlanFile(d),i=ifcFile(d),g=await glbFile(d),c=debitCSV([d]);return [!!(x&&!x.err),!!(i&&!i.err),!!(g&&!g.err),typeof c==='string'&&c.length>20]}")
        s.check(r == [True, True, True, True], 'exports DXF, IFC, glTF, CSV depuis le livrable', json.dumps(r))
        r = J("async()=>{await CPI.ppocr.charger();await CPI.ocr.charger();return [CPI.ocr.moteur(),typeof Tesseract]}")
        s.check(r == ['ppocr', 'object'], 'PP-OCRv6 (par défaut) et Tesseract chargés depuis le livrable', json.dumps(r))
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['OCR_1_CONTOURS.pdf'][0])
        pg.wait_for_function('el("dxpPg")&&el("dxpPg").textContent.includes("/ 3")')
        s.check(True, 'PDF.js : PDF ouvert et rendu depuis le livrable')
        s.check(not net, 'aucune requête réseau, de la 1re navigation à la fin (aucun domaine exclu)', json.dumps(net[:5]))
        s.check(not errs, 'aucune erreur JS ni erreur console', json.dumps(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_build')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
