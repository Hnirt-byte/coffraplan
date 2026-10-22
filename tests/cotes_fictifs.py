"""Phase 10A : uniquement des plans inventés, bâtis avec les fixtures existantes."""
import os
import pdf_fictifs as PF
import support_fictifs as SF


def fichiers(dossier):
    out = {}
    for nom, annotation in [('COTES', 'R01 : épaisseur du voile = 20 cm'),
                             ('CONFLIT', 'R01 : épaisseur du voile = 30 cm'),
                             ('DETAIL', 'R01 : chanfrein 45 degrés, 10 cm')]:
        p = PF.Page(1190, 842)
        SF.plan(p)
        p.texte(70, 500, 'R01 : épaisseur du voile = 20 cm', 10)
        c = PF.Page(842, 595)
        c.texte(40, 540, 'COUPE FICTIVE — ÉCHELLE 1/20', 12)
        c.rect(60, 250, 250, 200)
        c.texte(80, 460, annotation, 10)
        c.texte(400, 200, 'Longueur non attribuée : 2 m', 10)
        out[nom] = PF.ecrire(os.path.join(dossier, nom+'.pdf'), [p, c])
    return out
