"""Intègre le module d'import dans app/CoffraPlan.html (bibliothèque standard seulement, résultat déterministe).
  python modules/import/assembler.py           → réécrit les blocs générés du HTML depuis les sources
  python modules/import/assembler.py --check   → échoue (code 1) si un bloc du HTML diffère des sources (CI, tests)
Blocs générés : <script id="cpi-src"> (modules/import/*.js) et PDF.js tel que publié (vendor/pdfjs, empreintes SHA-256
vérifiées) dans <script type="text/plain" id="pdfjs-src"> et id="pdfjs-worker-src", chargés seulement à l'ouverture d'un PDF.
Le reste du HTML s'édite toujours à la main. Ne pas modifier ces blocs dans le HTML."""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, '..', '..', 'app', 'CoffraPlan.html')
ORDRE = ['lecteur.js', 'dxf.js', 'pdf.js', 'detecteur.js', 'nomenclatures.js', 'adaptateur.js', 'fenetre.js']   # dxf.js après lecteur.js (DECODEURS)
DEBUT, FIN = '<script id="cpi-src">', '</script>'
# PDF.js 6.4.299 (Apache-2.0), fichiers legacy/build/ (compatibles navigateurs plus anciens) du paquet npm pdfjs-dist@6.4.299, copiés sans modification
PDFJS = [('pdfjs-src', 'pdf.min.mjs', 'bccc24ea711db8e44503629519904a5292d73b9daaa214bbe7cdcc282b0f4259'),
         ('pdfjs-worker-src', 'pdf.worker.min.mjs', '145d2dd3ab0c86151011dba95acfa2d5336e2accd59388ea43dbee0efddaaec6')]


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


def main(check):
    html = open(HTML, encoding='utf-8', newline='').read()
    blocs = [(DEBUT, bloc(), 'cpi-src')] + [(f'<script type="text/plain" id="{i}">', pdfjs(i, n, h), i) for i, n, h in PDFJS]
    faits = []
    for debut, neuf, nom in blocs:
        a = html.find(debut)
        if a < 0:   # premier assemblage d'un bloc PDF.js : ajouté en fin de document
            if nom == 'cpi-src':
                sys.exit(f'{DEBUT} absent de app/CoffraPlan.html')
            a = b = html.rindex('</body>')
            neuf += '\n'
        else:
            b = html.index(FIN, a) + len(FIN)
        if html[a:b] != neuf:
            faits.append(nom)
            html = html[:a] + neuf + html[b:]
    if not faits:
        print('module d\'import : HTML à jour')
        return
    if check:
        sys.exit(f'module d\'import : bloc(s) {", ".join(faits)} de app/CoffraPlan.html différent(s) des sources '
                 '→ lancer python modules/import/assembler.py')
    with open(HTML, 'w', encoding='utf-8', newline='') as f:
        f.write(html)
    print('module d\'import : bloc(s) réécrit(s) : ' + ', '.join(faits))


if __name__ == '__main__':
    main('--check' in sys.argv[1:])
