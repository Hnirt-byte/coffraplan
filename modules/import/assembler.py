"""Intègre le module d'import dans app/CoffraPlan.html (bibliothèque standard seulement, résultat déterministe).
  python modules/import/assembler.py           → réécrit le bloc <script id="cpi-src"> du HTML depuis les sources
  python modules/import/assembler.py --check   → échoue (code 1) si le bloc du HTML diffère des sources (CI, tests)
Seul ce bloc est généré : le reste du HTML s'édite toujours à la main. Ne pas modifier le bloc dans le HTML."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, '..', '..', 'app', 'CoffraPlan.html')
ORDRE = ['lecteur.js', 'dxf.js', 'detecteur.js', 'adaptateur.js', 'fenetre.js']   # dxf.js après lecteur.js (DECODEURS)
DEBUT, FIN = '<script id="cpi-src">', '</script>'


def bloc():
    out = [DEBUT, '// Bloc généré par modules/import/assembler.py depuis modules/import/*.js : ne pas modifier ici.']
    for f in ORDRE:
        src = open(os.path.join(HERE, f), encoding='utf-8').read().replace('\r\n', '\n').rstrip('\n')
        if '</script' in src.lower():
            sys.exit(f'{f} : « </script » interdit dans une source intégrée au HTML')
        out += [f'// ==== modules/import/{f} ====', src]
    return '\n'.join(out) + '\n' + FIN


def main(check):
    html = open(HTML, encoding='utf-8', newline='').read()
    a = html.find(DEBUT)
    if a < 0:
        sys.exit(f'{DEBUT} absent de app/CoffraPlan.html')
    b = html.index(FIN, a) + len(FIN)
    neuf = bloc()
    if html[a:b] == neuf:
        print('module d\'import : HTML à jour')
        return
    if check:
        sys.exit('module d\'import : le bloc cpi-src de app/CoffraPlan.html diffère de modules/import/*.js '
                 '→ lancer python modules/import/assembler.py')
    with open(HTML, 'w', encoding='utf-8', newline='') as f:
        f.write(html[:a] + neuf + html[b:])
    print('module d\'import : bloc cpi-src réécrit')


if __name__ == '__main__':
    main('--check' in sys.argv[1:])
