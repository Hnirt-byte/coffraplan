"""Construit le livrable app/CoffraPlan.html (fichier unique, hors connexion) à partir des sources versionnées (phase 8).
  python modules/import/assembler.py           → construit app/CoffraPlan.html (non versionné : .gitignore)
  python modules/import/assembler.py --check   → échoue (code 1) si app/CoffraPlan.html est absent ou différent de ce que
                                                 donnent les sources (CI, tests) ; ne l'écrit pas
Source : app/CoffraPlan.source.html (HTML, CSS, script principal : s'édite à la main) ; chaque marqueur <!--@bloc ID--> y est
remplacé par son bloc généré : <script id="cpi-src"> (modules/import/*.js, dans l'ordre ORDRE) ; dépendances publiées, copiées
sans modification et vérifiées par empreinte SHA-256, dans des <script type="text/plain" id="…"> chargés au premier besoin :
three.js r170 (app/vendor/three), PDF.js (vendor/pdfjs), Tesseract.js (vendor/tesseract), ONNX Runtime Web + PP-OCRv6
(vendor/ppocr) ; fichiers .gz en base64. Bibliothèque standard Python seulement ; résultat déterministe (mêmes sources, mêmes
octets). Ne jamais modifier app/CoffraPlan.html à la main : il est réécrit à chaque construction."""
import base64, gzip, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APPD = os.path.join(HERE, '..', '..', 'app')
HTML = os.path.join(APPD, 'CoffraPlan.html')
SOURCE = os.path.join(APPD, 'CoffraPlan.source.html')
ORDRE = ['lecteur.js', 'dxf.js', 'pdf.js', 'ocr.js', 'ppocr.js', 'detecteur.js', 'nomenclatures.js', 'geometrie.js', 'rapprochement.js', 'vues.js', 'adaptateur.js', 'fenetre.js']   # dxf.js après lecteur.js (DECODEURS)
DEBUT, FIN = '<script id="cpi-src">', '</script>'
# PDF.js 6.4.299 (Apache-2.0), fichiers legacy/build/ (compatibles navigateurs plus anciens) du paquet npm pdfjs-dist@6.4.299, copiés sans modification
PDFJS = [('pdfjs-src', 'pdf.min.mjs', 'bccc24ea711db8e44503629519904a5292d73b9daaa214bbe7cdcc282b0f4259'),
         ('pdfjs-worker-src', 'pdf.worker.min.mjs', '145d2dd3ab0c86151011dba95acfa2d5336e2accd59388ea43dbee0efddaaec6')]

# Tesseract.js 7.0.0, tesseract.js-core 7.0.0, @tesseract.js-data/fra 1.0.0 (Apache-2.0) : (bloc, fichier, SHA-256 du fichier, SHA-256
# du contenu décompressé pour un .gz). Le .wasm.gz est le tesseract-core-simd-lstm.wasm publié, compressé par gzip -9 -n.
TESS = [('tess-src', 'tesseract.min.js', '000c27d9cd0def655f77b36c72a389c0ab13793aa31cb4d7aab56d09c0afbc7e', None),
        ('tess-worker-src', 'worker.min.js', '576b7df7e3393e137e51849357c9adb53fe7ac1bb69bfa06cf3d61520f182c6d', None),
        ('tess-core-src', 'tesseract-core-simd-lstm.js', 'e48e2f02ddae3716c8dd24bf41cd290d4efa96892d689cdc4013c2545d63f469', None),
        ('tess-wasm', 'tesseract-core-simd-lstm.wasm.gz', 'bad86ecb17527e1725a505a34f7ad44fbe0ccec9013080532997d189d7849f79',
         '34e8d50cac216427d86bf397d610fdd9f49492539bbcdfbfccc4eda20c810bea'),
        ('tess-fra', 'fra.traineddata.gz', 'd611139672b3752c7097e671e4a1d9209dfd37f2aeb081ef6487fba3351e9255', None)]

# Moteur PP-OCR (phase 6) : ONNX Runtime Web 1.30.0 (Microsoft, MIT ; fichiers dist/ du paquet npm onnxruntime-web@1.30.0) et modèle
# PP-OCRv6 small de reconnaissance (PaddleOCR, Apache-2.0 ; ONNX officiel redistribué par RapidOCR 3.10.0, SHA-256 6f3272… identique à
# celui publié) ; dictionnaire = métadonnée « character » du modèle. .gz : gzip -9 -n du fichier publié (2e empreinte : contenu décompressé).
PPOCR = [('ppocr-ort-src', 'ort.min.js', '7ae472a8ec976bcb69ad46b89b0a6ec8f3c5dbea4477674a26958672d1f3322d', None),
         ('ppocr-ort-mjs', 'ort-wasm-simd-threaded.mjs', 'e13f7f94fc51b4ca72b12faeb1ee95f4ace6dfbc8939bc718aabdc0a27c4299b', None),
         ('ppocr-ort-wasm', 'ort-wasm-simd-threaded.wasm.gz', 'bf933930bc90cf4f613f36cdc41616b54cfd2e9930478b574aed6ed4ef9ff8ca', '3398c10d07d229bd91b364548e130e0e51a8e5704b88c7c083ebbeb78842dee2'),
         ('ppocr-rec', 'PP-OCRv6_rec_small.onnx.gz', 'de992e86c5af5515a4709c43d22a6bc49033259736c2835859e6cd88040e76b7',
          '6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884'),
         ('ppocr-dict', 'PP-OCRv6_rec_small.dict.txt', 'f7aa897ca828a4c7c9e2739c30f9161a33306d532f020bcdb91dcfb664a5507e', None)]

# three.js r170 (MIT) : build/three.module.min.js du paquet npm three@0.170.0, sans modification ; chargé à la 1re vue 3D (v3Three)
THREE = ('three-src', 'three.module.min.js', '08fd7545d13d2c7fb65ab691530a802dafefd638596501854f267d0fb13c39e7')


def bloc():
    out = [DEBUT, '// Bloc généré par modules/import/assembler.py depuis modules/import/*.js : ne pas modifier ici.']
    for f in ORDRE:
        src = open(os.path.join(HERE, f), encoding='utf-8').read().replace('\r\n', '\n').rstrip('\n')
        if '</script' in src.lower():
            sys.exit(f'{f} : « </script » interdit dans une source intégrée au HTML')
        out += [f'// ==== modules/import/{f} ====', src]
    return '\n'.join(out) + '\n' + FIN


def pdfjs(ident, nom, sha):
    b = open(os.path.join(HERE, 'vendor', 'pdfjs', nom), 'rb').read()
    if hashlib.sha256(b).hexdigest() != sha:
        sys.exit(f'vendor/pdfjs/{nom} : empreinte SHA-256 inattendue (fichier modifié ou autre version)')
    src = b.decode('utf-8').rstrip('\n')
    if '</script' in src.lower() or '<!--' in src:
        sys.exit(f'{nom} : « </script » ou « <!-- » interdit dans un bloc du HTML')
    return f'<script type="text/plain" id="{ident}">' + src + '\n</script>'


def tess(ident, nom, sha, sha_gz, dossier='tesseract'):
    b = open(os.path.join(HERE, 'vendor', dossier, nom), 'rb').read()
    if hashlib.sha256(b).hexdigest() != sha or (sha_gz and hashlib.sha256(gzip.decompress(b)).hexdigest() != sha_gz):
        sys.exit(f'vendor/{dossier}/{nom} : empreinte SHA-256 inattendue (fichier modifié ou autre version)')
    if nom.endswith('.gz'):
        t = base64.b64encode(b).decode('ascii')
        src = '\n'.join(t[i:i + 120] for i in range(0, len(t), 120))
    else:
        src = b.decode('utf-8').rstrip('\n')
        if '</script' in src.lower() or '<!--' in src:
            sys.exit(f'{nom} : « </script » ou « <!-- » interdit dans un bloc du HTML')
    return f'<script type="text/plain" id="{ident}">' + src + '\n</script>'


def tous():
    """Blocs générés : identifiant → texte complet du bloc (<script …>…</script>)."""
    B = {'cpi-src': bloc()}
    i, n, h = THREE
    B[i] = tess(i, n, h, None, os.path.join('..', '..', '..', 'app', 'vendor', 'three'))
    B.update({i: pdfjs(i, n, h) for i, n, h in PDFJS})
    B.update({i: tess(i, n, h, g) for i, n, h, g in TESS})
    B.update({i: tess(i, n, h, g, 'ppocr') for i, n, h, g in PPOCR})
    return B


def construire():
    src = open(SOURCE, encoding='utf-8', newline='').read()
    B = tous()
    vus = re.findall(r'<!--@bloc ([\w-]+)-->', src)
    if sorted(vus) != sorted(B) or len(set(vus)) != len(vus):
        sys.exit(f'app/CoffraPlan.source.html : marqueurs <!--@bloc …--> attendus une fois chacun : {sorted(B)} ; trouvés : {vus}')
    for i, t in B.items():
        if t in src:
            sys.exit(f'bloc {i} déjà présent dans la source : la source ne doit contenir que son marqueur')
    return re.sub(r'<!--@bloc ([\w-]+)-->', lambda m: B[m.group(1)], src)


def main(check):
    html = construire()
    if check:
        try:
            cur = open(HTML, encoding='utf-8', newline='').read()
        except FileNotFoundError:
            sys.exit('app/CoffraPlan.html absent → lancer python modules/import/assembler.py')
        if cur != html:
            sys.exit('app/CoffraPlan.html différent de ce que donnent les sources (app/CoffraPlan.source.html, modules/import, '
                     'vendor) → lancer python modules/import/assembler.py ; ne jamais modifier app/CoffraPlan.html à la main')
        print(f'CoffraPlan.html à jour ({len(html.encode())} octets, SHA-256 {hashlib.sha256(html.encode()).hexdigest()[:16]}…)')
        return
    # écriture atomique (fichier temporaire puis remplacement) et seulement si le contenu change : un navigateur ou une suite de tests
    # qui ouvre le livrable pendant une construction ne lit jamais un fichier à moitié écrit
    try:
        same = open(HTML, encoding='utf-8', newline='').read() == html
    except FileNotFoundError:
        same = False
    if not same:
        tmp = HTML + '.tmp'
        with open(tmp, 'w', encoding='utf-8', newline='') as f:
            f.write(html)
        os.replace(tmp, HTML)
    print(f'CoffraPlan.html {"inchangé" if same else "construit"} ({len(html.encode())} octets, SHA-256 {hashlib.sha256(html.encode()).hexdigest()[:16]}…)')


if __name__ == '__main__':
    main('--check' in sys.argv[1:])
