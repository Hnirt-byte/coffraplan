"""Plans entièrement fictifs (repères, cotes et textes inventés) pour le repérage des réservations sur le dessin (phase 4) :
tests/t_detection.py. PDF écrits octet par octet par pdf_fictifs (déterministes) ; DXF par ezdxf.
fichiers(dossier) → {nom: (chemin, infos)}.

PDF_6_DETECTION.pdf, page 1 (A4 paysage, dessin au 1/50 : 1 pt = 50 × 25,4 / 72 mm) :
  R10 rectangle « re » 1200 × 600 avec diagonales ; R11 carré 400 × 400 en 4 traits séparés, côté bas en 2 morceaux ;
  R12 cercle Ø250 en 4 courbes de Bézier ; deux rectangles 500 × 300 identiques de part et d'autre du repère R13 ;
  rectangle 900 × 500 sans texte (cotes impossibles sans échelle) ; R20 avec cote écrite « 300x200 mm » ; F1 cercle Ø160
  tracé deux fois ; parasites : cadre de feuille, cartouche subdivisé, quadrillage de légende, nomenclature R10 à R13 à grille.
  Page 2 tournée (/Rotate 90) : R30 rectangle 800 × 400 et cercle Ø200, sans échelle écrite.
DETECTION_LIGNES.dxf (mm) : rectangle en 4 LINE + diagonales ; 4 LINE qui doublent une polyligne ; quadrillage de LINE ;
  cadre en LINE subdivisé ; rectangle en LINE sur 2 calques ; carré en LINE avec un côté en 2 morceaux ; cercle et polyligne ;
  nomenclature R5 (1200x600) en textes et grille de LINE."""
import math, os
import pdf_fictifs as PF

ECH = 50
K = ECH * 25.4 / 72          # mm réels par point PDF au 1/50
pt = lambda mm: mm / K


def cercle(p, cx, cy, r, ep=0.5, op=b'S'):
    k = 0.5522847498 * r
    p.ops.append(b'%g w %g %g m %g %g %g %g %g %g c %g %g %g %g %g %g c %g %g %g %g %g %g c %g %g %g %g %g %g c ' % (
        ep, cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r, cx - k, cy + r, cx - r, cy + k, cx - r, cy,
        cx - r, cy - k, cx - k, cy - r, cx, cy - r, cx + k, cy - r, cx + r, cy - k, cx + r, cy) + op)


def boite(p, cx, cy, Lmm, lmm, diag=False):
    """Rectangle « re » centré en (cx, cy) points, cotes en mm réels."""
    w, h = pt(Lmm), pt(lmm)
    p.rect(cx - w / 2, cy - h / 2, w, h)
    if diag:
        p.trait(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2); p.trait(cx - w / 2, cy + h / 2, cx + w / 2, cy - h / 2)
    return w, h


NOMS = [('Repère', 34), ('Désignation', 110), ('Ouverture\n(mm) l×h', 64), ('Niveau', 50)]
NL = [['R10', 'Trémie gaine', '1200x600', '+0,00'], ['R11', 'Réservation carrée', '400x400', ''],
      ['R12', 'Fourreau EU', 'Ø250', '-0,40'], ['R13', 'Trémie VMC', '500x300', '']]


def fichiers(d):
    os.makedirs(d, exist_ok=True)
    F = {}
    p = PF.Page()
    p.rect(20, 20, 802, 555)                                         # cadre de feuille
    p.texte(40, 560, 'CHANTIER DEMO — PLAN DE RÉSERVATIONS — ÉCHELLE 1/50', 10)
    # R10 : rectangle « re » + diagonales
    w, h = boite(p, 120, 470, 1200, 600, diag=True); p.texte(120 - w / 2, 470 + h / 2 + 4, 'R10', 7)
    # R11 : carré en 4 traits séparés, côté bas en deux morceaux
    s = pt(400); x0, y0 = 220, 452
    p.trait(x0, y0, x0 + s / 2, y0); p.trait(x0 + s / 2, y0, x0 + s, y0); p.trait(x0 + s, y0, x0 + s, y0 + s)
    p.trait(x0 + s, y0 + s, x0, y0 + s); p.trait(x0, y0 + s, x0, y0)
    p.texte(x0, y0 + s + 4, 'R11', 7)
    # R12 : cercle Ø250
    cercle(p, 300, 470, pt(250) / 2); p.texte(300 + pt(250) / 2 + 3, 468, 'R12', 7)
    # R13 : deux rectangles identiques, repère entre les deux
    boite(p, 380, 470, 500, 300); boite(p, 430, 470, 500, 300); p.texte(400, 467, 'R13', 6)
    # sans texte : cotes impossibles sans échelle
    boite(p, 130, 360, 900, 500)
    # R20 : cote écrite avec son unité
    w, h = boite(p, 230, 360, 300, 200); p.texte(230 - w / 2, 360 + h / 2 + 4, 'R20', 7); p.texte(230 - w / 2, 360 - h / 2 - 9, '300x200 mm', 6)
    # F1 : cercle Ø160 tracé puis rempli (même contour deux fois)
    cercle(p, 320, 360, pt(160) / 2); cercle(p, 320, 360, pt(160) / 2, op=b'f'); p.texte(320 + pt(160) / 2 + 3, 357, 'F1', 7)
    # parasites : cartouche subdivisé avec textes, quadrillage de légende (cellules « re »), nomenclature à grille
    p.rect(600, 30, 210, 80); p.trait(600, 70, 810, 70); p.trait(700, 30, 700, 70)
    for x, y, t in ((605, 95, 'CHANTIER DEMO'), (605, 75, 'Plan de réservations'), (605, 50, 'Indice A'), (705, 50, 'Éch. 1/50')):
        p.texte(x, y, t, 7)
    for i in range(3):
        for j in range(2):
            p.rect(450 + 30 * i, 60 + 15 * j, 30, 15)
    PF.tableau(p, 480, 540, NOMS, NL, titre='NOMENCLATURE DES RÉSERVATIONS')
    # page 2 tournée de 90° : contenu écrit dans le repère de la page (595 × 842) pour se lire droit à l'écran (842 × 595)
    q = PF.Page(595, 842, rot=90)
    T = lambda x, y: (595 - y, x)                                   # affiché (x, y) → page
    a, b = T(300 - pt(800) / 2, 300 - pt(400) / 2), T(300 + pt(800) / 2, 300 + pt(400) / 2)
    q.rect(min(a[0], b[0]), min(a[1], b[1]), abs(b[0] - a[0]), abs(b[1] - a[1]))
    c = T(500, 300); cercle(q, c[0], c[1], pt(200) / 2)
    t = T(300 - pt(800) / 2, 300 + pt(400) / 2 + 4); q.texte(t[0], t[1], 'R30', 7, 90)
    F['PDF_6_DETECTION.pdf'] = (PF.ecrire(os.path.join(d, 'PDF_6_DETECTION.pdf'), [p, q], 'Repérage fictif'), {'K': K, 'nomenclature': NL})

    import ezdxf
    doc = ezdxf.new('R2000'); doc.header['$INSUNITS'] = 4; m = doc.modelspace()
    L = lambda a, b, cal='RESA': m.add_line(a, b, dxfattribs={'layer': cal})
    def r4(x, y, w, h, cal='RESA', diag=False):
        P = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        for i in range(4):
            L(P[i], P[(i + 1) % 4], cal)
        if diag:
            L(P[0], P[2], cal); L(P[1], P[3], cal)
    r4(0, 0, 1200, 600, diag=True)                                 # rectangle en 4 LINE + diagonales
    m.add_text('R5', height=100, dxfattribs={'layer': 'RESA'}).set_placement((0, 650))
    m.add_lwpolyline([(3000, 0), (3500, 0), (3500, 500), (3000, 500)], close=True, dxfattribs={'layer': 'RESA'})
    r4(3000, 0, 500, 500)                                           # double la polyligne
    for i in range(4):                                              # quadrillage 3 × 2 en LINE (cellules)
        L((6000 + 300 * i, 0), (6000 + 300 * i, 400), 'TABLEAU')
    for j in range(3):
        L((6000, 200 * j), (6900, 200 * j), 'TABLEAU')
    r4(0, 3000, 2000, 1000, 'CADRE'); L((1000, 3000), (1000, 4000), 'CADRE')   # cadre subdivisé (cartouche)
    L((9000, 0), (9400, 0), 'A'); L((9400, 0), (9400, 300), 'A'); L((9400, 300), (9000, 300), 'B'); L((9000, 300), (9000, 0), 'B')
    L((12000, 0), (12200, 0)); L((12200, 0), (12400, 0)); L((12400, 0), (12400, 400)); L((12400, 400), (12000, 400)); L((12000, 400), (12000, 0))
    m.add_circle((15000, 0), 125, dxfattribs={'layer': 'RESA'})
    import dxf_nomenclatures as DN                                  # nomenclature R5 (grille en LINE : ni cadre ni cellules proposés)
    DN.tableau(m, 0, -1000, [('Repère', 300), ('Désignation', 900), ('Ouverture\n(mm) l×h', 600)], [['R5', 'Trémie', '1200x600']], h=60,
               titre='NOMENCLATURE DES RÉSERVATIONS')
    p = os.path.join(d, 'DETECTION_LIGNES.dxf'); doc.saveas(p)
    F['DETECTION_LIGNES.dxf'] = (p, {})
    return F


if __name__ == '__main__':
    import sys
    for n, (c, _) in fichiers(sys.argv[1] if len(sys.argv) > 1 else 'detection_fictifs').items():
        print(c, os.path.getsize(c))
