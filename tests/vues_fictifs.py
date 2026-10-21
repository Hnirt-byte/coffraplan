"""Plan entièrement fictif (repères, fonctions, cotes inventés) pour la phase 5 : vues techniques, occurrences physiques,
lecture des tableaux (tests/t_vues.py). PDF écrit octet par octet (déterministe) ; dessin au 1/50 (1 pt = 50 × 25,4 / 72 mm).
fichiers(dossier) → {nom: (chemin, infos)}.

PDF_8_VUES.pdf (A3 paysage)
  page 1 : nomenclature en texte (Repère, Fonction, Nb, Largeur (mm), Hauteur mm, Ø (mm), Observations) V1 à V5 :
    V1 Ø « - » → Largeur × Hauteur, quantité 2 ; V2 Ø seul ; V3 DN dans les observations (jamais une cote) ; V4 « Ø50 » dans la
    fonction, Ø65 dans la colonne ; V5 Ø et Largeur × Hauteur tous deux renseignés (ambigu).
    « VUE EN PLAN DALLE » : V1 dessiné 2 fois (quantité 2), V2, V3, V4, V5, contour de la dalle ;
    « COUPE A-A » : V1 et V3 vus en coupe (représentations, jamais comptées) ;
    « FERRAILLAGE DALLE Partie inférieure » : V1 à la même position relative que la 1re occurrence du plan (représentation),
    6 petits cadres d'armatures sans repère (parasites probables), barres.
  page 2 : nomenclature dessinée en contours de glyphes (OCR), texte magenta, grille bleue, nuage de révision orange sur la
    ligne R3 : tableau R1 à R4 (colonne « Qté »).
PDF_9_TOURNEES.pdf : la nomenclature de PDF_8 tournée de 90°, 270° et 180° dans la page (une page chacune)."""
import math
import os
import pdf_fictifs as PF
import pdf_ocr_fictifs as PO

ECH = 50
K = ECH * 25.4 / 72
pt = lambda mm: mm / K

COLS = [('Repère', 34), ('Fonction', 110), ('Nb', 26), ('Largeur\n(mm)', 44), ('Hauteur mm', 48), ('Ø (mm)', 36), ('Observations', 90)]
NL = [['V1', 'Trémie gaine', '2', '600', '400', '-', ''], ['V2', 'Fourreau EU', '1', '', '', '200', ''],
      ['V3', 'Traversée réseau', '1', '500', '300', '', 'DN100'], ['V4', 'Sonde - Ø50', '1', '', '', '65', ''],
      ['V5', 'Réservation', '1', '300', '300', '150', '']]
COLS5 = [('Repère', 34), ('Désignation', 100), ('Qté', 26), ('Ouverture (mm)', 70)]
NL5 = [['R1', 'Trémie gaine', '2', '250x250'], ['R2', 'Fourreau', '1', 'Ø160'], ['R3', 'Trémie VMC', '1', '400x400'], ['R4', 'Trémie EP', '1', '300x300']]


def boite(p, cx, cy, Lmm, lmm, rep=None, dedans=True):
    w, h = pt(Lmm), pt(lmm)
    p.rect(cx - w / 2, cy - h / 2, w, h)
    if rep:
        p.texte(cx - 5, cy - 2, rep, 6) if dedans else p.texte(cx - w / 2, cy + h / 2 + 3, rep, 6)
    return w, h


def cercle(p, cx, cy, r):
    k = 0.5522847498 * r
    p.ops.append(b'0.5 w %g %g m %g %g %g %g %g %g c %g %g %g %g %g %g c %g %g %g %g %g %g c %g %g %g %g %g %g c S' % (
        cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r, cx - k, cy + r, cx - r, cy + k, cx - r, cy,
        cx - r, cy - k, cx - k, cy - r, cx, cy - r, cx + k, cy - r, cx + r, cy - k, cx + r, cy))


class Tourne:
    """Tableau tourné de a degrés (90, 180, 270) autour de (cx, cy) dans la page : textes et traits."""
    def __init__(self, p, a, cx, cy):
        self.p, self.a, self.cx, self.cy = p, a, cx, cy

    def m(self, x, y):
        c, s = round(math.cos(math.radians(self.a))), round(math.sin(math.radians(self.a)))
        dx, dy = x - self.cx, y - self.cy
        return self.cx + c * dx - s * dy, self.cy + s * dx + c * dy

    def texte(self, x, y, s, t=8, a=0):
        X, Y = self.m(x, y)
        self.p.texte(X, Y, s, t, (a + self.a) % 360)

    def trait(self, x0, y0, x1, y1, ep=0.5):
        self.p.trait(*self.m(x0, y0), *self.m(x1, y1), ep)


def nuage(p, x0, y0, x1, y1, r=4):
    """Nuage de révision : arcs orange le long d'un rectangle."""
    p.ops.append(b'1 0.5 0 RG')
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        n = max(1, int(math.hypot(bx - ax, by - ay) / (2 * r)))
        for i in range(n):
            px, py = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            qx, qy = ax + (bx - ax) * (i + 1) / n, ay + (by - ay) * (i + 1) / n
            nx, ny = -(qy - py), (qx - px)   # bosse vers l'extérieur (sens trigonométrique)
            p.ops.append(b'0.5 w %g %g m %g %g %g %g %g %g c S' % (px, py, px + 0.6 * nx, py + 0.6 * ny, qx + 0.6 * nx, qy + 0.6 * ny, qx, qy))
    p.ops.append(b'0 G')


def fichiers(d):
    os.makedirs(d, exist_ok=True)
    p = PO.Page(1190, 842)
    p.rect(20, 20, 1150, 802)
    xs, ys = PF.tableau(p, 40, 800, COLS, NL, titre='NOMENCLATURE DES RÉSERVATIONS')
    # vue en plan : dalle, V1 ×2, V2, V3, V4, V5 (repères écrits dans ou à côté de leur contour)
    p.texte(560, 640, 'VUE EN PLAN DALLE', 14)
    p.rect(500, 390, 300, 220)
    boite(p, 550, 560, 600, 400, 'V1'); boite(p, 550, 450, 600, 400, 'V1')
    cercle(p, 640, 560, pt(200) / 2); p.texte(650, 558, 'V2', 6)
    boite(p, 720, 560, 500, 300, 'V3')
    cercle(p, 640, 450, pt(65) / 2); p.texte(646, 448, 'V4', 6)
    boite(p, 720, 450, 300, 300, 'V5', dedans=False)
    # coupe : V1 et V3 vus en coupe (la dalle en élévation, ouvertures dessinées)
    p.texte(930, 640, 'COUPE A-A', 14)
    p.rect(880, 540, 260, 20)
    boite(p, 930, 550, 600, 200); boite(p, 1060, 550, 500, 200)
    p.texte(925, 568, 'V1', 6); p.texte(1055, 568, 'V3', 6)
    # ferraillage : barres, 6 petits cadres d'armatures, V1 à la position relative de sa 1re occurrence en plan
    p.texte(520, 330, 'FERRAILLAGE DALLE Partie inférieure', 14)
    p.rect(500, 80, 300, 220)
    for i in range(1, 10):
        p.trait(500 + 30 * i, 80, 500 + 30 * i, 300, 0.3)
    for i in range(6):
        p.rect(610 + 25 * i, 120, 8, 8)
    boite(p, 550, 250, 600, 400, 'V1')
    # page 2 : glyphes dessinés, texte magenta, grille bleue, nuage de révision sur R3
    q = PO.Page(842, 595)

    class Couleur:
        def texte(s, x, y, txt, t=8, a=0):
            q.ops.append(b'1 0 1 rg'); q.contours(x, y, txt, t); q.ops.append(b'0 g')

        def trait(s, x0, y0, x1, y1, ep=0.5):
            q.ops.append(b'0 0 1 RG'); q.trait(x0, y0, x1, y1, ep); q.ops.append(b'0 G')
    x5, y5 = PF.tableau(Couleur(), 60, 500, COLS5, NL5, t=8, titre='NOMENCLATURE DES RÉSERVATIONS')
    nuage(q, x5[0] - 3, y5[4] - 2, x5[-1] + 3, y5[3] + 2)
    c = PO.ecrire(os.path.join(d, 'PDF_8_VUES.pdf'), [p, q], 'Vues fictives')
    T = []
    for a in (90, 270, 180):
        t = PO.Page(1190, 842)
        PF.tableau(Tourne(t, a, 595, 421), 400, 480, COLS, NL, titre='NOMENCLATURE DES RÉSERVATIONS')
        T.append(t)
    c9 = PO.ecrire(os.path.join(d, 'PDF_9_TOURNEES.pdf'), T, 'Tableaux tournés fictifs')
    return {'PDF_8_VUES.pdf': (c, {'K': K, 'nomenclature': NL, 'NL5': NL5, 'z5': dict(PO.zone(x5, y5), page=2)}),
            'PDF_9_TOURNEES.pdf': (c9, {'rotations': [90, 270, 180]})}


if __name__ == '__main__':
    import sys
    for n, (c, _) in fichiers(sys.argv[1] if len(sys.argv) > 1 else 'vues_fictifs').items():
        print(c, os.path.getsize(c))
