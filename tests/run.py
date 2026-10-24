"""Lance les suites de tests et résume.
  python tests/run.py               → suites rapides (≈ quelques minutes)
  python tests/run.py complet       → toutes les suites (revue 420 plans, gabarits, avant / après : bien plus long)
  python tests/run.py t_v25 t_ux    → suites nommées
  option -j N : N suites en parallèle (défaut 1)
Code de sortie 0 seulement si toutes les suites passent. Détail de chaque suite : tests/out/<suite>.json"""
import os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
RAPIDE = ['t_v32', 't_recette_pdf', 't_preparation_chantier', 't_chanfrein_fabrication', 't_geometries_particulieres', 't_cotes', 't_creation', 't_contours', 't_import', 't_dxf', 't_dxf_ui', 't_nomenclature', 't_pdf', 't_ocr', 't_detection', 't_rapprochement', 't_vues', 't_phase51', 't_ppocr', 't_stockage', 't_build', 't_plan_d', 't_support', 't_v30', 't_coh', 't_v210', 't_v29', 't_v28', 't_v26', 't_v25', 't_v24', 't_ux', 't_v23', 't_ui', 't_regress', 't_special', 't_3d', 't_renforts', 't_poutre', 't_export', 't_forme']
LONG = ['t_avap', 't_audit', 't_gab_ident', 't_gab_dalle']


def one(name):
    t0 = time.time()
    p = subprocess.run([sys.executable, name + '.py'], cwd=HERE, capture_output=True, text=True)
    out = (p.stdout + p.stderr).strip()
    return name, p.returncode, time.time() - t0, out


def main(args):
    j = 1
    if '-j' in args:
        i = args.index('-j'); j = int(args[i + 1]); del args[i:i + 2]
    names = RAPIDE + LONG if args == ['complet'] else (args or RAPIDE)
    if 'APP' not in os.environ:   # phase 8 : livrable construit une fois depuis les sources, puis utilisé par toutes les suites
        subprocess.run([sys.executable, os.path.join(HERE, '..', 'modules', 'import', 'assembler.py')], check=True)
        os.environ['CP_CONSTRUIT'] = '1'
    ko = []
    with ThreadPoolExecutor(j) as ex:
        for name, rc, dt, out in ex.map(one, names):
            head = next((l for l in out.splitlines() if l.startswith('[' + name + ']')), out.splitlines()[-1] if out else '(aucune sortie)')
            print(f'{"✓" if rc == 0 else "✗"} {head}  ({dt:.0f} s)', flush=True)
            if rc:
                ko.append(name); print('\n'.join('    ' + l for l in out.splitlines()[-25:]))
                if os.environ.get('GITHUB_ACTIONS'):  # annotation visible sur GitHub (onglet Actions, résumé du run)
                    msg = ' | '.join(l.strip() for l in out.splitlines() if l.strip().startswith('✗'))[:900] or out.splitlines()[-1][:900]
                    if 'Traceback' in out:  # exception : fin de la pile d'appels (les journaux complets ne sont pas toujours lisibles)
                        msg = (msg[:300] + ' ⏎ ' + ' ⏎ '.join(l.strip() for l in out.splitlines()[-14:] if l.strip()))[:1800]
                    print(f'::error title={name}::{msg}')
    print(f'\n{len(names) - len(ko)}/{len(names)} suites OK' + (f' — en échec : {", ".join(ko)}' if ko else ''))
    return not ko


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1:]) else 1)
