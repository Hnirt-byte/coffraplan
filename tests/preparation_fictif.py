"""PDF de préparation entièrement fictif, aucune donnée de chantier réel."""
import os
import pdf_fictifs as PF

def fichier(dossier):
    p=PF.Page(1190,842)
    cols=[('Repère',65),('Désignation',230),('Largeur (mm)',95),('Hauteur (mm)',95),('Quantité',65)]
    PF.tableau(p,40,780,cols,[[f'R{i:02}', 'Réservation fictive', '600','800','1'] for i in range(1,9)],titre='NOMENCLATURE DES RÉSERVATIONS')
    lignes=[
      'R01 : épaisseur du voile = 240 mm',
      'R03 : épaisseur du voile = 240 mm','R03 : épaisseur du voile = 250 mm',
      'R04 : épaisseur du voile = 240 mm','R04 : feuillure périphérique rectangulaire',
      'R04 : largeur feuillure = 40 mm','R04 : profondeur feuillure = 30 mm','R04 : départ feuillure = 20 mm',
      'R05 : épaisseur du voile = 240 mm','R05 : chanfrein 45 degrés, retrait 40 mm',
      'R06 : épaisseur du voile = 240 mm','R06 : chanfrein 45 degrés, retrait 40 mm',
      'R07 : plusieurs sections, géométrie variable','R08 : épaisseur du voile = 240 mm']
    for i,s in enumerate(lignes):p.texte(670,780-i*30,s,9)
    return PF.ecrire(os.path.join(dossier,'PREPARATION_FICTIVE.pdf'),[p])
