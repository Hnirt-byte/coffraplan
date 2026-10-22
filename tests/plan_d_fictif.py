"""Plan entièrement fictif et anonyme « type D » (phase 8) : reproduit la disposition d'une vue en plan réelle où la lecture
automatique échouait, sans aucune de ses données. Repères, désignations, cotes et niveaux inventés.
PDF écrit octet par octet (déterministe), texte extractible, A0 paysage (3370 × 2384 pt), tableaux SANS traits (cas d'un plan dont
les traits ne sont pas relevés) :
  - nomenclature de 46 réservations (R01-R38, V01-V08), en-tête sur deux niveaux (« DIMENSIONS (mm) » sur Hauteur / Largeur,
    « FINITIONS » sur trois colonnes), cotes en mm, niveaux NGF ;
  - tableau de trappes juxtaposé à gauche, en-tête plus bas : ses lignes sont à la hauteur des lignes R18… de la nomenclature ;
  - bloc « NOTA GENERAL » sous le tableau de trappes ;
  - titre « Sous Toiture » avec son échelle « 1 : 25 » dessous, au-dessus d'un vrai dessin (murs, réservations repérées R01 à R05) ;
  - cartouche avec « VUE EN PLAN - SOUS TOITURE », « PLAN GUIDE », une autre échelle « 1 : 25 » (ne doit pas devenir une vue).
PLAN_D_NOTE.pdf (cas négatif) : même dessin, sans titre ; « Sous Toiture » seulement dans une note et en grand texte sans échelle.
fichiers(dossier) → {nom: (chemin, infos)}."""
import os
import pdf_fictifs as PF

W, H = 3370, 2384
K = 7.2 / 4.9   # hauteur de texte relevée par PDF.js / corps de la police (Helvetica) : corps choisi pour retrouver les hauteurs du plan
T = round(7.2 * K, 2)
PAS = 13.6

NATURES = ['ALIMENTATION EAU', 'DEPART EGOUTTURES', 'SIPHON DE SOL', 'PASSAGE FOURREAU', 'ARRIVEE RESEAU', 'SORTIE AIR', 'ENTREE AIR FRAIS']
LIEUX = ['LOCAL A', 'LOCAL B', 'ATELIER FICTIF', 'SALLE TECHNIQUE', 'LOCAL C']
COTES = [(100, 100), (250, 250), (450, 100), (400, 400), (200, 200), (300, 300), (500, 350), (600, 600)]


def tx(p, x, yc, s, h=7.2):
    """Texte de hauteur h (relevée) centré en yc ; x = bord gauche."""
    c = round(h * K, 2)
    p.texte(x, round(yc - 0.357 * c, 2), s, c)


def lignes():
    R = []
    reps = [f'R{i:02d}' for i in range(1, 39)] + [f'V{i:02d}' for i in range(1, 9)]
    for k, r in enumerate(reps):
        h, l = COTES[k % len(COTES)]
        niv = f'{110 + (k % 4)}.{(k * 37) % 1000:03d}'
        fin = [['Non', 'Oui', 'Non'], ['Non', 'Non', 'Oui'], ['Oui', 'Non', 'Non']][k % 3]
        R.append({'repere': r, 'desc': f'{NATURES[k % len(NATURES)]} {LIEUX[k % len(LIEUX)]} {k + 1}', 'H': h, 'L': l, 'niv': niv, 'fin': fin})
    return R


L46 = lignes()
TRAPPES = [('T01', 'REGARD FICTIF A', '0.360', '0.360', '', '0.070', '0.070', '110.500'),
           ('T02', 'REGARD FICTIF B', '', '', '0.460', '0.070', '0.070', '110.400'),
           ('T03', 'REGARD FICTIF C', '', '', '0.460', '0.070', '0.070', '110.400')]
NOTA = ['NOTA GENERAL :', '- Toutes les cotes de génie civil sont exprimées en mm et sont à', 'considérer enduits terminés.',
        '- Les cotes de niveau sont exprimées en mNGF.', '- Les feuillures béton sont de 70x70 mm de coté, sauf indication contraire.',
        '- Pente pour lavage des sols = 1.5% minimum vers les siphons.']


def nomenclature(p):
    """Nomenclature des réservations, sans traits ; x des colonnes (bord gauche des textes)."""
    X = {'id': 1714, 'com': 1784, 'H': 2244, 'L': 2314, 'axe': 2380, 'niv': 2452, 'f1': 2530, 'f2': 2601, 'f3': 2681}
    tx(p, 2131, 797, 'Nomenclature des réservations', 8.6)
    tx(p, 2247, 775, 'DIMENSIONS (mm)'); tx(p, 2594, 775, 'FINITIONS')
    tx(p, 1714, 762.1, 'IDENTIFIANT'); tx(p, 1961, 762.1, 'COMMENTAIRES')
    tx(p, 2233, 755.1, 'Hauteur'); tx(p, 2304, 755.1, 'Largeur')
    tx(p, 2389, 761, 'Axe'); tx(p, 2369, 749.6, 'réservations')
    tx(p, 2454, 768.1, 'Niveau'); tx(p, 2443, 756.7, 'réservation')
    tx(p, 2529, 761, 'Non'); tx(p, 2574, 761, 'Scellement non'); tx(p, 2664, 761, 'Scellement')
    tx(p, 2516, 749.6, 'rebouché'); tx(p, 2592, 749.6, 'étanche'); tx(p, 2671, 749.6, 'étanche')
    y = 735.6
    for r in L46:
        tx(p, 1736, y, r['repere']); tx(p, X['com'], y, r['desc'])
        tx(p, X['H'], y, str(r['H'])); tx(p, X['L'], y, str(r['L'])); tx(p, X['niv'], y, r['niv'])
        tx(p, X['f1'], y, r['fin'][0]); tx(p, X['f2'], y, r['fin'][1]); tx(p, X['f3'], y, r['fin'][2])
        y -= PAS
    return y


def trappes(p):
    tx(p, 1229, 527.4, 'Nomenclature des trappes', 8.6)
    tx(p, 1315, 499.5, 'DIMENSIONS (mm)'); tx(p, 1479, 505.4, 'DIMENSIONS FEUILLURE'); tx(p, 1527, 494, '(mm)')
    tx(p, 1616, 504.4, 'NIVEAU DE'); tx(p, 1629, 493, 'POSE'); tx(p, 1629, 481.5, '(NGF)')
    tx(p, 940, 492.6, 'IDENTIFIANT'); tx(p, 1088, 492.6, 'COMMENTAIRES')
    for x, s in [(1265, 'Longueur'), (1341, 'Largeur'), (1410, 'Diametre'), (1477, 'Profondeur'), (1557, 'Hauteur')]:
        tx(p, x, 479.7, s)
    y = 466
    for t in TRAPPES:
        for x, v in zip([963, 1040, 1270, 1345, 1415, 1485, 1560, 1625], t):
            if v:
                tx(p, x, y, v)
        y -= PAS


def note(p, x, y, L):
    for s in L:
        tx(p, x, y, s); y -= 11


def ligne(p, x0, y0, x1, y1, ep=0.8, pas=120):
    """Trait découpé en segments courts (comme un export de DAO) : un mur de 3 m n'est pas un trait unique."""
    n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) // pas) + 1)
    for i in range(n):
        p.trait(round(x0 + (x1 - x0) * i / n, 2), round(y0 + (y1 - y0) * i / n, 2), round(x0 + (x1 - x0) * (i + 1) / n, 2), round(y0 + (y1 - y0) * (i + 1) / n, 2), ep)


def boite(p, x, y, w, h, ep=0.8):
    ligne(p, x, y, x + w, y, ep); ligne(p, x + w, y, x + w, y + h, ep); ligne(p, x + w, y + h, x, y + h, ep); ligne(p, x, y + h, x, y, ep)


def dessin(p, avec_titre=True):
    """Vue en plan : murs doubles, cloisons, mobilier, cotes, 5 réservations repérées (R01-R05) ; titre « Sous Toiture » + « 1 : 25 »."""
    boite(p, 120, 900, 2900, 1300, 1.2); boite(p, 140, 920, 2860, 1260, 1.2)
    for x in (700, 1300, 1900, 2500):
        ligne(p, x, 920, x, 2180, 1.0); ligne(p, x + 15, 920, x + 15, 2180, 1.0)
    ligne(p, 140, 1500, 3000, 1500, 1.0); ligne(p, 140, 1515, 3000, 1515, 1.0)
    for k, (x, y) in enumerate([(300, 1700), (900, 1100), (1500, 1800), (2100, 1200), (2700, 1900)]):
        boite(p, x, y, 60, 60, 0.7); p.trait(x, y, x + 60, y + 60, 0.4); p.trait(x, y + 60, x + 60, y, 0.4)
        tx(p, x + 70, y + 70, f'R{k + 1:02d}', 14)
    for k in range(60):   # mobilier et équipements
        boite(p, 200 + 46 * k, 960 + (k % 7) * 70, 30, 20, 0.3)
    for k in range(0, 2900, 50):   # ligne de cote avec ses repères
        p.trait(120 + k, 2215, 120 + k, 2225, 0.3)
    ligne(p, 120, 2220, 3020, 2220, 0.3, 60)
    if avec_titre:
        tx(p, 100, 2258, 'Sous Toiture', 16.8)
        tx(p, 110, 2230, '1 : 25', 11.2)


def cartouche(p):
    boite(p, 2900, 40, 440, 380, 0.8); ligne(p, 2900, 230, 3340, 230, 0.5)
    for y, s in [(346, 'PLAN GUIDE GENIE CIVIL'), (300, 'ZONE FICTIVE'), (253, 'VUE EN PLAN - SOUS TOITURE')]:
        tx(p, 2930, y, s, 14)
    tx(p, 2930, 69, 'N° de plan :'); tx(p, 3200, 65, '1 : 25'); tx(p, 2930, 120, 'Chantier fictif')


def fichiers(d):
    os.makedirs(d, exist_ok=True)
    F = {}
    p = PF.Page(W, H)
    nomenclature(p); trappes(p); note(p, 1250, 300, NOTA); dessin(p); cartouche(p)
    F['PLAN_D_FICTIF.pdf'] = (PF.ecrire(os.path.join(d, 'PLAN_D_FICTIF.pdf'), [p], 'Plan fictif type D'), {'lignes': L46, 'trappes': [t[0] for t in TRAPPES]})
    q = PF.Page(W, H)
    nomenclature(q); dessin(q, avec_titre=False); cartouche(q)
    note(q, 1250, 300, ['NOTA :', '- Réservations Sous Toiture à confirmer par le lot CVC.', '- Voir plan Sous Toiture pour les trémies.'])
    tx(q, 160, 2300, 'Sous Toiture', 16.8)   # grand texte sans échelle : pas un titre de vue
    F['PLAN_D_NOTE.pdf'] = (PF.ecrire(os.path.join(d, 'PLAN_D_NOTE.pdf'), [q], 'Plan fictif type D, note'), {})
    return F


if __name__ == '__main__':
    import sys
    for n, (c, _) in fichiers(sys.argv[1] if len(sys.argv) > 1 else 'plan_d_fictif').items():
        print(c, os.path.getsize(c))
