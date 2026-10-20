"""Plan entièrement fictif (repères, désignations, cotes inventés) pour le rapprochement nomenclature ↔ dessin (phase 4,
finalisation) : tests/t_rapprochement.py. PDF écrit octet par octet (déterministe) ; dessin au 1/50 (1 pt = 50 × 25,4 / 72 mm).
fichiers(dossier) → {nom: (chemin, infos)}.

PDF_7_RAPPROCHEMENT.pdf
  page 1 (A3 paysage, « ÉCHELLE 1/50 ») : nomenclature en texte (repère, désignation, ouverture (mm), quantité) R12 à R20, et
    R12 : repère + ligne de rappel + une seule cote « 600 », aucun contour (dimension partielle, scénario A) ;
    R14 et R15 : deux rectangles 600 × 400 de repères différents (scénario E), R14 avec la cote écrite « 600x400 » ;
    R16 : repère + cote écrite « 900x500 » pour 800 × 500 au tableau (conflit réel, scénario F) ;
    R17 : deux cercles Ø200, chacun son repère, quantité 2 au tableau (occurrences physiques, scénario J) ;
    R18 : rectangle 500 × 300 en plan ; R21 : rectangle et repère absents du tableau (hors nomenclature) ; R20 : nulle part.
  page 2 (« COUPE A-A ») : R18 vue en coupe (500 × 200 : autre vue, scénario C) ; R13 : repère seul, aucune géométrie
    (scénarios B et D) ; R19 : repère DESSINÉ en contours de glyphes (OCR) au-dessus d'un carré 400 × 400 (scénario D)."""
import os
import pdf_fictifs as PF
import pdf_ocr_fictifs as PO

ECH = 50
K = ECH * 25.4 / 72
pt = lambda mm: mm / K

COLS = [('Repère', 34), ('Désignation', 120), ('Ouverture\n(mm) l×h', 64), ('Quantité', 44)]
NL = [['R12', 'Trémie gaine', '600x400', '1'], ['R13', 'Fourreau EU', 'Ø250', '1'], ['R14', 'Trémie VMC', '600x400', '1'],
      ['R15', 'Trémie désenfumage', '600x400', '1'], ['R16', 'Trémie gaine palière', '800x500', '1'], ['R17', 'Fourreau EP', 'Ø200', '2'],
      ['R18', 'Réservation poutre', '500x300', '1'], ['R19', 'Réservation carrée', '400x400', '1'], ['R20', 'Trémie sans dessin', '300x300', '1']]


def boite(p, cx, cy, Lmm, lmm):
    w, h = pt(Lmm), pt(lmm)
    p.rect(cx - w / 2, cy - h / 2, w, h)
    return w, h


def fichiers(d):
    os.makedirs(d, exist_ok=True)
    p = PO.Page(1190, 842)
    p.rect(20, 20, 1150, 802)
    p.texte(40, 800, 'CHANTIER DEMO — PLAN DES RÉSERVATIONS — ÉCHELLE 1/50', 10)
    PF.tableau(p, 760, 760, COLS, NL, titre='NOMENCLATURE DES RÉSERVATIONS')
    # R12 : repère, ligne de rappel vers la trémie (non dessinée dans cette vue), une seule cote écrite « 600 »
    p.texte(80, 700, 'R12', 7); p.trait(94, 698, 150, 650); p.texte(80, 688, '600', 6)
    # R14 et R15 : mêmes cotes, repères différents ; R14 cotée « 600x400 »
    w, h = boite(p, 250, 690, 600, 400); p.texte(250 - w / 2, 690 + h / 2 + 4, 'R14', 7); p.texte(250 - w / 2, 690 - h / 2 - 9, '600x400', 6)
    w, h = boite(p, 420, 690, 600, 400); p.texte(420 - w / 2, 690 + h / 2 + 4, 'R15', 7)
    # R16 : cote écrite contradictoire (900 au lieu de 800), pas de contour
    p.texte(560, 700, 'R16', 7); p.texte(560, 688, '900x500', 6)
    # R17 : deux occurrences physiques (quantité 2)
    for x in (100, 220):
        _cercle(p, x, 540, pt(200) / 2)
        p.texte(x + pt(200) / 2 + 3, 538, 'R17', 7)
    # R18 en plan ; R21 hors nomenclature
    w, h = boite(p, 360, 540, 500, 300); p.texte(360 - w / 2, 540 + h / 2 + 4, 'R18', 7)
    w, h = boite(p, 520, 540, 300, 200); p.texte(520 - w / 2, 540 + h / 2 + 4, 'R21', 7)
    # page 2 : coupe
    q = PO.Page(1190, 842)
    q.rect(20, 20, 1150, 802)
    q.texte(40, 800, 'COUPE A-A', 10)
    w, h = boite(q, 200, 600, 500, 200); q.texte(200 - w / 2, 600 + h / 2 + 4, 'R18', 7)
    q.texte(400, 600, 'R13', 7)
    w, h = boite(q, 600, 560, 400, 400); q.contours(600 - w / 2, 560 + h / 2 + 5, 'R19', 9)
    c = PO.ecrire(os.path.join(d, 'PDF_7_RAPPROCHEMENT.pdf'), [p, q], 'Rapprochement fictif')
    return {'PDF_7_RAPPROCHEMENT.pdf': (c, {'K': K, 'nomenclature': NL})}


def _cercle(p, cx, cy, r):
    k = 0.5522847498 * r
    p.ops.append(b'0.5 w %g %g m %g %g %g %g %g %g c %g %g %g %g %g %g c %g %g %g %g %g %g c %g %g %g %g %g %g c S' % (
        cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r, cx - k, cy + r, cx - r, cy + k, cx - r, cy,
        cx - r, cy - k, cx - k, cy - r, cx, cy - r, cx + k, cy - r, cx + r, cy - k, cx + r, cy))


if __name__ == '__main__':
    import sys
    for n, (c, _) in fichiers(sys.argv[1] if len(sys.argv) > 1 else 'rapprochement_fictifs').items():
        print(c, os.path.getsize(c))
