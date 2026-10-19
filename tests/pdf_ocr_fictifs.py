"""PDF entièrement fictifs (repères, désignations et valeurs inventés) pour la reconnaissance OCR : tests/t_ocr.py.
Textes DESSINÉS : contours vectoriels des glyphes (police Liberation Sans ou DejaVu Sans du système, lue par fontTools),
comme un export de DAO qui vectorise ses polices, ou tableau numérisé (image en niveaux de gris dessinée par Pillow).
Aucun texte extractible dans les tableaux : seule une reconnaissance visuelle peut les lire.
fichiers(dossier) → {nom: (chemin, infos)} ; infos = lignes attendues et zones des tableaux (points PDF, Y vers le haut)."""
import os
import zlib
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pdf_fictifs as PF

POLICES = ['/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
           '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/freefont/FreeSans.ttf']


def police():
    for p in POLICES:
        if os.path.exists(p):
            return p
    raise SystemExit('pdf_ocr_fictifs : aucune police TrueType trouvée (' + ', '.join(POLICES) + ')')


class _Pen(BasePen):
    def __init__(self, gs, k, x, y):
        super().__init__(gs)
        self.o, self.k, self.x, self.y = [], k, x, y

    def p(self, pt):
        return b'%.2f %.2f' % (self.x + pt[0] * self.k, self.y + pt[1] * self.k)

    def _moveTo(self, a): self.o.append(self.p(a) + b' m')
    def _lineTo(self, a): self.o.append(self.p(a) + b' l')
    def _curveToOne(self, a, b, c): self.o.append(self.p(a) + b' ' + self.p(b) + b' ' + self.p(c) + b' c')
    def _closePath(self): self.o.append(b'h')


class Page(PF.Page):
    """Page de pdf_fictifs avec, en plus, des textes en contours de glyphes et des images de taille quelconque."""
    _F = None

    def __init__(self, w=842, h=595, rot=0):
        super().__init__(w, h, rot)
        self.imgs = []
        if Page._F is None:
            f = TTFont(police())
            Page._F = (f, f.getGlyphSet(), f.getBestCmap(), f['hmtx'], f['head'].unitsPerEm)

    def contours(self, x, y, s, t=8):
        """Texte en (x, y) (ligne de base), corps t, dessiné en contours remplis : aucun texte extractible."""
        f, gs, cmap, hmtx, upm = Page._F
        k = t / upm
        for ch in s:
            g = cmap.get(ord(ch))
            if g is None:
                g = '.notdef'
            pen = _Pen(gs, k, x, y)
            gs[g].draw(pen)
            if pen.o:
                self.ops.append(b' '.join(pen.o) + b' f')
            x += hmtx[g][0] * k

    def image(self, x, y, w, h, im=None):
        if im is None:
            return super().image(x, y, w, h)
        self.imgs.append(im.convert('L'))
        self.ops.append(b'q %g 0 0 %g %g %g cm /Im%d Do Q' % (w, h, x, y, len(self.imgs)))


def ecrire(chemin, pages, titre='Plan fictif OCR'):
    obj = []
    add = lambda b: obj.append(b) or len(obj)
    font = add(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    root_pages = len(obj) + sum(2 + len(p.imgs) for p in pages) + 1
    kids = []
    for p in pages:
        im = []
        for m in p.imgs:
            z = zlib.compress(m.tobytes(), 9)
            im.append(add(b'<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n'
                          % (m.width, m.height, len(z)) + z + b'\nendstream'))
        data = zlib.compress('\n'.join(o.decode('latin-1') for o in p.ops).encode('latin-1'), 9)
        c = add(b'<< /Length %d /Filter /FlateDecode >>\nstream\n' % len(data) + data + b'\nendstream')
        xo = b' /XObject << ' + b' '.join(b'/Im%d %d 0 R' % (i + 1, n) for i, n in enumerate(im)) + b' >>' if im else b''
        kids.append(add(b'<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %g %g] /Rotate %d /Resources << /Font << /F1 %d 0 R >>' % (root_pages, p.w, p.h, p.rot, font)
                        + xo + b' >> /Contents %d 0 R >>' % c))
    assert add(b'<< /Type /Pages /Kids [' + b' '.join(b'%d 0 R' % k for k in kids) + b'] /Count %d >>' % len(kids)) == root_pages
    cat = add(b'<< /Type /Catalog /Pages %d 0 R >>' % root_pages)
    info = add(b'<< /Title (' + titre.encode('cp1252') + b') /Producer (tests/pdf_ocr_fictifs.py) >>')
    out, off = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'), []
    for i, b in enumerate(obj, 1):
        off.append(len(out)); out += b'%d 0 obj\n' % i + b + b'\nendobj\n'
    x = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(obj) + 1) + b''.join(b'%010d 00000 n \n' % o for o in off)
    out += b'trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(obj) + 1, cat, info, x)
    with open(chemin, 'wb') as f:
        f.write(out)
    return chemin


class Scan:
    """Tableau dessiné dans une image (page numérisée) : mêmes appels que Page (texte, trait), en points de la zone."""
    def __init__(self, x0, y0, w, h, dpi=200):
        self.x0, self.y0, self.k = x0, y0, dpi / 72
        self.im = Image.new('L', (round(w * self.k), round(h * self.k)), 255)
        self.d = ImageDraw.Draw(self.im)
        self.f = {}

    def px(self, x, y):
        return (x - self.x0) * self.k, (self.y0 - y) * self.k

    def texte(self, x, y, s, t=8, a=0):
        f = self.f.get(t) or self.f.setdefault(t, ImageFont.truetype(police(), round(t * self.k)))
        self.d.text(self.px(x, y), s, font=f, fill=0, anchor='ls')

    def trait(self, x0, y0, x1, y1, ep=0.5):
        self.d.line([self.px(x0, y0), self.px(x1, y1)], fill=0, width=max(1, round(ep * self.k)))

    def poser(self, pg, flou=0.6):
        im = self.im.filter(ImageFilter.GaussianBlur(flou)) if flou else self.im   # numérisation : léger flou
        pg.image(self.x0, self.y0 - self.im.height / self.k, self.im.width / self.k, self.im.height / self.k, im)


COLS = [('Repère', 38), ('Désignation', 150), ('Type', 78), ('Ouverture\n(mm) l×h', 66), ('Réseau', 48), ('Niveau', 64), ('Observations', 104)]
# Lignes fictives : rectangle, Ø, DN seul, SO, cellule vide, description longue (multiligne), autres types (membrane, carottage) : rien à écarter
L1 = [
    ['RA01', 'Trémie gaine palière', 'Trémie dalle', '650x800', '', 'NGF +12,50', ''],
    ['RA02', 'Fourreau évacuation EU', 'Fourreau', 'Ø250', 'DN200', '+3,20', ''],
    ['RA03', 'Traversée réseau EP', 'Traversée voile', '', 'DN160', '-0,40', 'Ø à confirmer'],
    ['RA04', 'Attente électrique', 'Incorporation', 'SO', '', '', 'Sans objet'],
    ['RA05', 'Réservation à définir', 'Trémie', '', '', '±0,00', 'Cotes à venir'],
    ['RB10', 'Gaine de désenfumage\navec cadre bois côté palier', 'Trémie voile', '1200x500', '', '+0,95', 'Cadre à prévoir\npar le lot CVC'],
    ['C7', 'Carottage membrane étanchéité', 'Carottage', 'Ø120', '', '+1,10 / dalle', 'Lot étanchéité'],
]
ACIERS = [('Repère', 34), ('Ø', 30), ('Nombre', 40), ('Longueur (m)', 60), ('Façonnage', 60), ('Poids (kg)', 50)]
LA = [['1', 'HA12', '24', '3,20', 'Droit', '68,2'], ['2', 'HA8', '40', '1,10', 'Cadre', '17,4']]
COLS2 = [('N°', 30), ('Désignation', 130), ('Dimensions\n(cm)', 62), ('Niveau', 56), ('Remarques', 110)]
L2 = [['S1', 'Trémie local technique', '90x70', '+0,00', ''], ['S2', 'Fourreau gaz', 'Ø16', '+1,20', 'Gaine PE'],
      ['S3', 'Réservation porte coupe-feu', '93x210', '+0,00', ''], ['S4', 'Ventilation basse', 'SO', '', 'Supprimée indice B']]
COLS3 = [('Rep.', 34), ('Élément', 90), ('Section', 60), ('Niveau', 56), ('Obs.', 90)]
L3 = [['P1', 'Carottage voile', 'Ø160', '+2,10', ''], ['P2', 'Trémie dalle', '500x500', '', 'Garde-corps'], ['P3', 'Fourreau', 'DN100', '+0,60', '']]


def zone(xs, ys, m=6, titre=12):
    return {'x0': xs[0] - m, 'y0': ys[-1] - m, 'x1': xs[-1] + m, 'y1': ys[0] + m + titre}


def fichiers(d):
    os.makedirs(d, exist_ok=True)
    F = {}
    # 1. trois pages : plan avec cartouche en vrai texte ; nomenclature à grille en contours + aciers en contours ;
    #    page tournée (/Rotate 90) avec un tableau sans bordures en contours
    p1 = Page(); p1.rect(100, 100, 300, 200); p1.texte(40, 560, 'CHANTIER DEMO — PLAN DE RÉSERVATIONS', 11)
    p2 = Page(); p2.texte(600, 40, 'Cartouche : indice C', 8)
    xs, ys = PF.tableau(p2, 40, 520, COLS, L1, t=7, titre='NOMENCLATURE DES RÉSERVATIONS', ecrit=p2.contours)
    xa, ya = PF.tableau(p2, 40, 200, ACIERS, LA, t=7, titre='NOMENCLATURE DES ACIERS', ecrit=p2.contours)
    p3 = Page(595, 842, rot=90)

    class Tourne:   # repère affiché (paysage 842 × 595) → repère de la page (595 × 842), comme PDF_3_TOURNEE de pdf_fictifs
        def texte(s, x, y, txt, t=8, a=0):
            k = t / Page._F[4]
            p3.ops.append(b'q 0 1 -1 0 %g %g cm' % (595 - y, x))
            p3.contours(0, 0, txt, t)
            p3.ops.append(b'Q')

        def trait(s, x0, y0, x1, y1, ep=0.5): p3.trait(595 - y0, x0, 595 - y1, x1, ep)
    x3, y3 = PF.tableau(Tourne(), 120, 450, COLS3, L3, t=8, grille=False, titre='LISTE DES PERCEMENTS')
    F['OCR_1_CONTOURS.pdf'] = (ecrire(os.path.join(d, 'OCR_1_CONTOURS.pdf'), [p1, p2, p3]),
                               {'L1': L1, 'z1': dict(zone(xs, ys), page=2), 'za': dict(zone(xa, ya), page=2), 'L3': L3, 'z3': dict(zone(x3, y3), page=3)})
    # 2. une page numérisée : nomenclature à grille dans une image (cotes en cm), légèrement floue
    s = Page()
    sc = Scan(30, 560, 420, 200)
    x2, y2 = PF.tableau(sc, 40, 540, COLS2, L2, t=8, titre='TABLEAU DES TRÉMIES')
    sc.poser(s)
    F['OCR_2_SCAN.pdf'] = (ecrire(os.path.join(d, 'OCR_2_SCAN.pdf'), [s]), {'L2': L2, 'z2': dict(zone(x2, y2), page=1)})
    return F


if __name__ == '__main__':
    import sys
    for n, (c, _) in fichiers(sys.argv[1] if len(sys.argv) > 1 else 'pdf_ocr_fictifs').items():
        print(c, os.path.getsize(c))
