"""Mode d'emploi PDF : captures d'écran sur l'application du dépôt, puis rendu Chromium.
  python docs/manuel/build.py            → captures + PDF
  python docs/manuel/build.py --sans-captures   → PDF seul (réutilise docs/manuel/img/)
Sortie : docs/manuel/CoffraPlan_v<version>_Mode_emploi.pdf (version lue dans l'application)."""
import os, subprocess, sys, datetime
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tests'))
from lib import APP

MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']

if '--sans-captures' not in sys.argv:
    subprocess.run([sys.executable, os.path.join(HERE, 'captures.py')], check=True)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.goto('file://' + APP)
    ver = pg.evaluate("document.getElementById('appVer').textContent").strip().lstrip('v')
    d = datetime.date.today()
    html = open(os.path.join(HERE, 'manuel.html'), encoding='utf-8').read().replace('{{VERSION}}', ver).replace('{{MOIS}}', f'{MOIS[d.month - 1]} {d.year}')
    tmp = os.path.join(HERE, '_rendu.html')  # dans le même dossier que img/ pour les chemins relatifs
    open(tmp, 'w', encoding='utf-8').write(html)
    pg.goto('file://' + tmp)
    pg.wait_for_load_state('networkidle')
    out = os.path.join(HERE, f'CoffraPlan_v{ver}_Mode_emploi.pdf')
    pg.pdf(path=out, prefer_css_page_size=True, print_background=True, display_header_footer=True, header_template='<span></span>',
           footer_template='<div style="width:100%;text-align:center;font:8px sans-serif;color:#8a93a6"><span class="pageNumber"></span></div>')
    b.close()
    os.remove(tmp)
print(out)
