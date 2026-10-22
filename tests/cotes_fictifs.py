"""Phase 10A : uniquement des plans inventés, bâtis avec les fixtures existantes."""
import os
import pdf_fictifs as PF
import support_fictifs as SF


def fichiers(dossier):
    out = {}
    for nom, annotation in [('COTES', 'R01 : épaisseur du voile = 20 cm'),
                             ('CONFLIT', 'R01 : épaisseur du voile = 30 cm'),
                             ('DETAIL', 'R01 : chanfrein 45 degrés, 10 cm'),
                             ('AUTRE_DETAIL', 'R02 : chanfrein 10 mm'),
                             ('INDICE_DETAIL', 'chanfrein 10 mm'),
                             ('MULTI_DETAIL', 'R01 et R02 : chanfrein 10 mm'),
                             ('HOMONYME', 'R01 : chanfrein 10 mm'),
                             ('NUMERIQUE', 'R01 : hauteur = 1.200 mm'),
                             ('MILLIERS', 'R01 : hauteur = 1 200 mm')]:
        p = PF.Page(1190, 842)
        SF.plan(p)
        p.texte(70, 500, 'R01 : épaisseur du voile = 20 cm', 10)
        c = PF.Page(842, 595)
        c.texte(40, 540, 'COUPE FICTIVE — ÉCHELLE 1/20', 12)
        c.rect(60, 250, 250, 200)
        c.texte(80, 460, annotation, 10)
        if nom == 'HOMONYME':
            PF.tableau(c, 40, 180, SF.COLS, [['R01','Autre réservation fictive','500x500','1']], titre='NOMENCLATURE DES RÉSERVATIONS')
        c.texte(400, 200, 'Longueur non attribuée : 2 m', 10)
        out[nom] = PF.ecrire(os.path.join(dossier, nom+'.pdf'), [p, c])
    return out
