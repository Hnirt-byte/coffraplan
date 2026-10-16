"""Non-régression : débit v2.1 = débit v19 / v2.0 (ref_v19.json) sauf changements volontaires listés ici (documentés).
L'historique v17 → v18 reste dans tests_v18/t_regress.py."""
import json, os, subprocess, sys
from lib import Suite, HERE, APP

# Changements volontaires v19 (scénario → raison). Tout autre écart est une régression.
# 'puisard' : la forme est supprimée ; le scénario est reconstruit en « carré avec fond » et doit rester IDENTIQUE
# au puisard v18 (preuve que c'était un doublon) → il n'est volontairement PAS dans cette liste.
VOLONTAIRES = {
    # v2.6 : contrôle de flèche des joues (boîtes rectangulaires) ; CP filmé renommé « CP filmé bouleau »
    'rect_fond_gs': 'nouvelle alerte de flèche (boîte sans renforts, portée 1 464 mm)', 'puisard': 'nouvelle alerte de flèche (h 900 mm, portée 382 mm)',
    'dalle_rive': 'désignation « CP filmé bouleau » dans l\'alerte de cintrage',
    # v2.1 : messages sans incidence sur la fabrication retirés ; angle de coupe des joues reporté dans la ligne de débit
    'voile_man': 'alerte « joues parallèles : biais » retirée, angle dans la ligne « Joues pleine hauteur »',
    'voile_man_L3000': 'idem', 'voile_man_bois': 'idem',
    'dalle_circ_pt': 'alerte « joue > panneau → n longueurs » retirée (découpe déjà au débit)', 'poutre': 'idem', 'poutre_po': 'idem',
    'dalle_pt_lhs': 'idem', 'poutre_lhs': 'idem',
    'para_long': 'alerte « tronçons sur cadres de joint » retirée (déjà au plan et au débit)',
    # v2.1 : poteaux de la spéciale : base et fond sup. percés (texte de la ligne de débit)
    'special_rect': 'base et fond sup. percés au droit des poteaux',
    # v2.1 : conseil de flambement limité aux sections qui suppriment réellement le risque
    'rect_long': 'conseil de section de renfort recalculé (seules les sections suffisantes)', 'special_long': 'idem', 'circ_fond': 'idem', 'circ_sf': 'idem',
}


def main():
    s = Suite('t_regress')
    cur = os.path.join(HERE, 'out', 'cur.json')
    subprocess.run([sys.executable, os.path.join(HERE, 'capture.py'), APP, cur], check=True, capture_output=True)
    a, b = json.load(open(os.path.join(HERE, 'ref_v19.json'))), json.load(open(cur))
    for k in a:
        same = a[k] == b.get(k)
        if k in VOLONTAIRES:
            s.check(True, k)
            if not same:
                print(f'  ~ {k} modifié (volontaire : {VOLONTAIRES[k]})')
        else:
            diff = ''
            if not same:
                for part in ('W', 'cp', 'bois'):
                    if a[k].get(part) != b[k].get(part):
                        diff += f"{part}: v19={a[k].get(part)} | v20={b[k].get(part)} "
            s.check(same, f'{k} identique à v19', diff[:600])
    return s.report()


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
