"""PDF entièrement fictifs (chantier, repères, lots et valeurs inventés) pour l'import PDF : tests/t_pdf.py et docs/manuel/captures.py.
Écrits octet par octet (PDF 1.4, Helvetica en WinAnsi : é, Ø, ×, ± lisibles), sans bibliothèque : résultat déterministe.
fichiers(dossier) → {nom: (chemin, infos)}."""
import os
import zlib


class Page:
    """Une page : w × h points (A4 paysage par défaut), rotation /Rotate, contenu en opérateurs PDF."""
    def __init__(self, w=842, h=595, rot=0):
        self.w, self.h, self.rot, self.ops, self.img = w, h, rot, [], False

    def texte(self, x, y, s, t=8, a=0):
        """Texte en (x, y) (ligne de base, coin gauche), corps t ; a = angle en degrés (0, 90, 180, 270 seulement)."""
        c, n = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[a % 360]
        b = s.encode('cp1252').replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)')
        self.ops.append(b'BT /F1 %g Tf %d %d %d %d %g %g Tm (' % (t, c, n, -n, c, x, y) + b + b') Tj ET')

    def trait(self, x0, y0, x1, y1, ep=0.5):
        self.ops.append(b'%g w %g %g m %g %g l S' % (ep, x0, y0, x1, y1))

    def rect(self, x, y, w, h, ep=0.5):
        self.ops.append(b'%g w %g %g %g %g re S' % (ep, x, y, w, h))

    def image(self, x, y, w, h):
        """Image en niveaux de gris (simule une page numérisée)."""
        self.img = True
        self.ops.append(b'q %g 0 0 %g %g %g cm /Im1 Do Q' % (w, h, x, y))

    def glyphes(self, x, y, s, t=8):
        """Texte DESSINÉ en tracés (comme un export de DAO qui vectorise ses polices) : aucun texte extractible."""
        k = t / 10
        for i, ch in enumerate(s):
            if ch == ' ':
                continue
            x0 = x + i * 6 * k
            # un petit « glyphe » de 3 traits par caractère, différent selon le caractère (illisible par une machine, visible à l'œil)
            v = ord(ch)
            self.ops.append(b'0.4 w %g %g m %g %g l %g %g l %g %g l S' % (x0, y, x0 + 2 * k + v % 3 * k, y + 7 * k, x0 + 4 * k, y + (v % 5) * k, x0 + 5 * k, y + 7 * k))


def ecrire(chemin, pages, titre='Plan fictif'):
    obj = []
    add = lambda b: obj.append(b) or len(obj)
    font = add(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    img = None
    if any(p.img for p in pages):
        px = bytes((x * 7 + y * 13) % 256 for y in range(64) for x in range(64))
        z = zlib.compress(px)
        img = add(b'<< /Type /XObject /Subtype /Image /Width 64 /Height 64 /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n' % len(z) + z + b'\nendstream')
    kids = []
    root_pages = len(obj) + 2 * len(pages) + 1
    for p in pages:
        data = '\n'.join(o.decode('latin-1') for o in p.ops).encode('latin-1')
        c = add(b'<< /Length %d >>\nstream\n' % len(data) + data + b'\nendstream')
        res = b'<< /Font << /F1 %d 0 R >>' % font + (b' /XObject << /Im1 %d 0 R >>' % img if img else b'') + b' >>'
        kids.append(add(b'<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %g %g] /Rotate %d /Resources ' % (root_pages, p.w, p.h, p.rot) + res + b' /Contents %d 0 R >>' % c))
    assert add(b'<< /Type /Pages /Kids [' + b' '.join(b'%d 0 R' % k for k in kids) + b'] /Count %d >>' % len(kids)) == root_pages
    cat = add(b'<< /Type /Catalog /Pages %d 0 R >>' % root_pages)
    info = add(b'<< /Title (' + titre.encode('cp1252') + b') /Producer (tests/pdf_fictifs.py) >>')
    out, off = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'), []
    for i, b in enumerate(obj, 1):
        off.append(len(out)); out += b'%d 0 obj\n' % i + b + b'\nendobj\n'
    x = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(obj) + 1) + b''.join(b'%010d 00000 n \n' % o for o in off)
    out += b'trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(obj) + 1, cat, info, x)
    with open(chemin, 'wb') as f:
        f.write(out)
    return chemin


def tableau(pg, x0, y0, cols, rows, t=7, grille=True, titre=None, ecrit=None):
    """Tableau : cols = [(titre, largeur)] (titre sur plusieurs lignes avec \\n), rows = [[cellule…]] (\\n = cellule multiligne) ;
    (x0, y0) = coin haut gauche (Y vers le haut). ecrit = pg.texte (défaut) ou pg.glyphes (tableau en tracés)."""
    ecrit = ecrit or pg.texte
    rh, pas = 2.2 * t, 1.25 * t
    xs = [x0]
    for _, w in cols:
        xs.append(xs[-1] + w)
    y, ys = y0, [y0]
    for k, cells in [('t', [c for c, _ in cols])] + [('d', r) for r in rows]:
        n = max([1] + [len(str(v).split('\n')) for v in cells])
        H = rh + (n - 1) * pas
        for j, v in enumerate(cells):
            L = str(v).split('\n') if v != '' else []
            for i, s in enumerate(L):
                yy = y - H / 2 + ((len(L) - 1) / 2 - i) * pas - 0.35 * t
                ecrit(xs[j] + 0.6 * t, yy, s, t)
        y -= H
        ys.append(y)
    if grille:
        for yy in ys:
            pg.trait(xs[0], yy, xs[-1], yy)
        for xx in xs:
            pg.trait(xx, ys[0], xx, ys[-1])
    if titre:
        ecrit(x0, y0 + 0.8 * t, titre, round(1.3 * t, 2))
    return xs, ys


COLS = [('Repère', 34), ('Désignation', 120), ('Ouverture\n(mm) l×h', 64), ('Réseau', 50), ('Niveau', 62), ('Lot', 58), ('Observations', 110)]
# Lignes fictives : rectangle, carré, Ø explicite, DN seul, SO, cotes manquantes, niveau ≠ hauteur, lots et types variés (rien à écarter)
L1 = [
    ['R01', 'Trémie gaine palière', '650x800', '', '+2,85 / dalle', 'CVC', ''],
    ['R02', 'Réservation carrée', '400 × 400', '', 'NGF 112,40', 'Plomberie', 'Prévoir cadre'],
    ['R03', 'Fourreau EU', 'Ø250', 'DN200', '-0,40', 'Plomberie', ''],
    ['R04', 'Traversée réseau EP', 'DN250', 'DN250', '', 'VRD', 'Ø à confirmer par le lot'],
    ['R05', 'Attente électrique', 'SO', '', '', 'Électricité', 'Sans objet'],
    ['R06', 'Réservation à définir', '', '', '±0,00', 'Gros œuvre', 'Cotes à venir'],
]
ACIERS = [('Repère', 34), ('Ø', 30), ('Nombre', 40), ('Longueur (m)', 60), ('Façonnage', 60), ('Poids (kg)', 50)]
LA = [['1', 'HA12', '24', '3,20', 'Droit', '68,2'], ['2', 'HA8', '40', '1,10', 'Cadre', '17,4']]
INDICES = [('Indice', 34), ('Date', 50), ('Modification', 150)]
LI = [['A', '02/03', 'Première diffusion'], ['B', '15/04', 'Ajout des trémies']]


def fichiers(d):
    os.makedirs(d, exist_ok=True)
    F = {}

    # 1. une page : plan sommaire, nomenclature des réservations à grille, tableau d'aciers et tableau d'indices à écarter
    p = Page()
    for i, (x, y, w, h) in enumerate([(60, 300, 80, 98), (200, 320, 49, 49)]):
        p.rect(x, y, w, h)
    p.texte(60, 410, 'R01', 8); p.texte(200, 380, 'R02', 8)
    p.texte(40, 560, 'CHANTIER DEMO — PLAN DE RÉSERVATIONS NIVEAU R+1', 11)
    tableau(p, 300, 520, COLS, L1, titre='NOMENCLATURE DES RÉSERVATIONS')
    tableau(p, 40, 200, ACIERS, LA, titre='NOMENCLATURE DES ACIERS')
    tableau(p, 600, 150, INDICES, LI)
    F['PDF_1_TABLEAU.pdf'] = (ecrire(os.path.join(d, 'PDF_1_TABLEAU.pdf'), [p]), {'lignes': L1})

    # 2. trois pages : plan seul ; tableau sans grille aux cellules multilignes ; deux tableaux sur une page, en-têtes différents
    p1 = Page()
    p1.rect(100, 100, 300, 200); p1.texte(110, 310, 'VUE EN PLAN — ÉCHELLE 1/50', 9)
    p2 = Page()
    L2 = [['T10', 'Trémie\nascenseur', '1200 x 1500', '', '+0,00', 'Ascenseur', 'Cadre bois\nà prévoir'],
          ['T11', 'Gaine\nVMC', '300x300', '', '+2,70', 'CVC', '']]
    tableau(p2, 60, 500, COLS, L2, grille=False, titre='TABLEAU DES TRÉMIES')
    p3 = Page()
    C3 = [('N°', 30), ('Élément', 90), ('Dimensions\n(cm)', 60), ('Hauteur / dalle', 70), ('Remarques', 110)]
    L3 = [['F1', 'Voile V3', '30x40', '+1,20', ''], ['F2', 'Poutre P2', 'Ø16', '+2,40', 'Fourreau PVC']]
    tableau(p3, 40, 520, C3, L3, titre='LISTE DES PERCEMENTS')
    C4 = [('Rep.', 30), ('Type', 70), ('Section', 60), ('Angle', 40)]
    L4 = [['P1', 'Carottage', 'Ø 160', '45°'], ['P2', 'Trémie', '500x500', '']]
    tableau(p3, 470, 520, C4, L4, titre='RÉSERVATIONS — BÂTIMENT B')
    F['PDF_2_MULTIPAGE.pdf'] = (ecrire(os.path.join(d, 'PDF_2_MULTIPAGE.pdf'), [p1, p2, p3]), {'L2': L2, 'L3': L3, 'L4': L4})

    # 3. page tournée (/Rotate 90) : contenu dessiné à 90° pour se lire droit à l'écran
    p = Page(595, 842, rot=90)
    L5 = [['M1', 'Trémie local technique', '900x700', '', '', 'CVC', '']]

    class Tourne:   # repère affiché (paysage 842 × 595) → repère de la page (595 × 842) : x' = y, y' = 842 − x ... tourné de +90°
        def texte(s, x, y, txt, t=8, a=0): p.texte(595 - y, x, txt, t, 90)
        def trait(s, x0, y0, x1, y1, ep=0.5): p.trait(595 - y0, x0, 595 - y1, x1, ep)
    tableau(Tourne(), 200, 450, COLS, L5, titre='NOMENCLATURE DES RÉSERVATIONS')
    F['PDF_3_TOURNEE.pdf'] = (ecrire(os.path.join(d, 'PDF_3_TOURNEE.pdf'), [p]), {'lignes': L5})

    # 4. deux pages : nomenclature DESSINÉE en tracés (pas de texte extractible), cartouche en vrai texte
    q1 = Page(); q1.rect(80, 80, 400, 300); q1.texte(40, 560, 'CHANTIER DEMO — PLAN DE COFFRAGE', 11)
    q2 = Page(); q2.texte(600, 40, 'Cartouche : indice C', 8)
    tableau(q2, 60, 500, COLS, L1, titre='NOMENCLATURE DES RÉSERVATIONS', ecrit=q2.glyphes)
    F['PDF_4_GRAPHIQUE.pdf'] = (ecrire(os.path.join(d, 'PDF_4_GRAPHIQUE.pdf'), [q1, q2]), {'lignes': L1})

    # 5. page numérisée : une image, aucun texte
    s = Page(); s.image(40, 40, 760, 515)
    F['PDF_5_SCAN.pdf'] = (ecrire(os.path.join(d, 'PDF_5_SCAN.pdf'), [s]), {})
    return F


if __name__ == '__main__':
    import sys
    for n, (c, _) in fichiers(sys.argv[1] if len(sys.argv) > 1 else 'pdf_fictifs').items():
        print(c, os.path.getsize(c))
