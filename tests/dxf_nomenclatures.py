"""Jeux DXF entièrement fictifs (ezdxf) pour les nomenclatures de réservations : chantier, repères, lots et valeurs inventés.
Utilisés par tests/t_nomenclature.py et docs/manuel/captures.py. fichiers(dossier) → {nom: (chemin, infos)}."""
import math, os, re
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf.math import Vec2


def rect(cx, cy, L, l, a=0):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-L / 2, -l / 2), (L / 2, -l / 2), (L / 2, l / 2), (-L / 2, l / 2))]


def tableau(lay, x0, y0, cols, rows, h=2.5, grille=True, mtext=False, bas=False, calque='NOMENC', titre=None):
    """Tableau dessiné : cols = [(titre, largeur)] (titre sur plusieurs lignes avec \\n), rows = [[cellule…]] ;
    (x0, y0) = coin haut gauche ; bas=True : en-tête en bas, lignes empilées au-dessus (ligne 1 juste au-dessus)."""
    at = {'layer': calque}
    rh, pas = 3.2 * h, 1.6 * h
    nl = lambda c: max([1] + [len(str(v).split('\n')) for v in c])
    blocs = [('t', [t for t, _ in cols])] + [('d', r) for r in rows]
    if bas:
        blocs = [('d', r) for r in reversed(rows)] + blocs[:1]
    xs = [x0]
    for _, w in cols:
        xs.append(xs[-1] + w)
    y, ys = y0, [y0]
    for k, cells in blocs:
        H = rh + (nl(cells) - 1) * pas
        for j, v in enumerate(cells):
            L = str(v).split('\n') if v != '' else []
            if not L:
                continue
            cy = y - H / 2
            if mtext:
                lay.add_mtext('\\P'.join(L), dxfattribs=dict(at, char_height=h, insert=((xs[j] + xs[j + 1]) / 2 if k == 't' else xs[j] + 0.8 * h, cy),
                                                              attachment_point=5 if k == 't' else 4))
            else:
                for i, s in enumerate(L):
                    yy = cy + ((len(L) - 1) / 2 - i) * pas
                    if k == 't':
                        lay.add_text(s, height=h, dxfattribs=at).set_placement(((xs[j] + xs[j + 1]) / 2, yy), align=TA.MIDDLE_CENTER)
                    else:
                        lay.add_text(s, height=h, dxfattribs=at).set_placement((xs[j] + 0.8 * h, yy), align=TA.MIDDLE_LEFT)
        y -= H
        ys.append(y)
    if grille:
        for yy in ys:
            lay.add_line((xs[0], yy), (xs[-1], yy), dxfattribs=at)
        for xx in xs:
            lay.add_line((xx, ys[0]), (xx, ys[-1]), dxfattribs=at)
    if titre:
        lay.add_text(titre, height=1.4 * h, dxfattribs=at).set_placement((x0, (ys[0] + 1.2 * h) if not bas else (ys[-1] - 2.6 * h)))
    return xs, ys


COLS23 = [('Repère', 18), ('Désignation', 46), ('Type', 24), ('Ouverture\n(mm) l×h', 26), ('Diamètre\nréseau', 20), ('Niveau', 26),
          ('Angle', 14), ('Lot', 28), ('Observations', 44)]
# 23 lignes fictives : repères de formats variés, types, lots et observations divers (aucune ligne ne doit être écartée)
L23 = [
    ['D01', 'Trémie gaine technique', 'Trémie', '650x800', '', '+5,60 m', '', 'Plomberie', ''],
    ['R+1-D02', 'Passage canalisation EU', 'Fourreau', 'Ø300', 'DN250', '560 cm / dalle', '45°', 'Plomberie', 'PVC'],
    ['D03', 'Carottage VMC', 'Carottage', 'Ø160', 'DN125', '+2,80 m', '', 'CVC', ''],
    ['D04', 'Boîte électricité', 'Incorporation', '400x200', '', 'SO', '', 'Électricité', ''],
    ['D05', 'Trémie escalier', 'Trémie', '1200x2400', '', '+0,00', '', 'Gros œuvre', 'Voir coupe A'],
    ['D06', 'Membrane étanchéité', 'Membrane', 'à définir', '', '/', '', 'Étanchéité', ''],
    ['D07', 'Fourreau courant faible', 'Fourreau', '', 'DN100', '+0,35 m', '90°', 'Courants faibles', ''],
    ['RES-08', 'Passage gaine ventilation', 'Trémie', '500 x 500', '', '+3,10 m', '', 'CVC', ''],
    ['D09', 'Réservation sanitaire', 'Trémie', '300x300', '', '+1,20 m', '', 'Plomberie', ''],
    ['D10', 'Fourreau arrosage', 'Fourreau', 'Ø110', 'DN90', '-0,40 m', '', 'Espaces verts', ''],
    ['D11', 'Platine ancrage', 'Insert', 'SO', '', '+4,00 m', '', 'Serrurerie', 'Pas de coffrage nécessaire'],
    ['D-12', 'Passage câbles', 'Fourreau', '%%c90', '', '+0,50 m', '', 'Électricité', ''],
    ['d13', 'Trémie désenfumage', 'Trémie', '600x600', '', '+6,20 m', '', 'CVC', 'Coupe-feu 2 h'],
    ['D 14', 'Évacuation EP', 'Carottage', 'Ø200', 'DN160', '+5,60 m', '30°', 'Plomberie', ''],
    ['D15', 'Rail fixation', 'Insert', '/', '', '', '', 'Façades', 'Fourni par le lot façades'],
    ['D16', 'Réservation ascenseur', 'Trémie', '1800x2000', '', '+0,00', '', 'Ascenseur', ''],
    ['D17', 'Fourreau gaz', 'Fourreau', 'Ø63', 'DN50', '+1,00 m', '', 'Gaz', ''],
    ['D18', 'Passage chauffage', 'Fourreau', 'Ø125', '', '+0,30 m', '', 'Chauffage', ''],
    ['D19', 'Trou d\'homme', 'Trémie', '800x800', '', '+7,50 m', '', 'Gros œuvre', ''],
    ['D20', 'Ventouse chaudière', 'Carottage', 'Ø100', '', '+2,10 m', '', 'Chauffage', ''],
    ['D21', 'Siphon de sol', 'Incorporation', '250x250', '', '-0,05 m', '', 'Plomberie', ''],
    ['D22', 'Réservation fibre', 'Fourreau', 'Ø40', '', '+0,60 m', '', 'Courants faibles', ''],
    ['D23', 'Passage PVC', 'Fourreau', 'Ø75', '', '+0,80 m', '', 'Plomberie', 'Dernière ligne'],
]
ACIERS = ([('Repère', 16), ('Ø', 10), ('Nombre', 16), ('Longueur', 20), ('Forme', 20), ('Poids (kg)', 20)],
          [['1', 'HA10', '12', '2,40', 'Droite', '17,8'], ['2', 'HA12', '8', '3,10', 'U', '22,0'], ['3', 'HA8', '20', '1,20', 'Cadre', '9,5']])


def nouveau(v='R2018'):
    d = ezdxf.new(v, setup=True)
    d.header['$INSUNITS'] = 4
    return d, d.modelspace()


def fichiers(dossier):
    F = {}
    # 1. nomenclature de 23 lignes dans une présentation (TEXT + LINE), tableau d'aciers à côté ; géométries et repères en espace Objet
    d, m = nouveau()
    for n in ('RESA', 'REPERES', 'NOMENC', 'COUPE'):
        d.layers.add(n)
    G = {}
    G['D01'] = m.add_lwpolyline(rect(10000, 5000, 650, 800), close=True, dxfattribs={'layer': 'RESA'}).dxf.handle
    m.add_text('D01', height=150, dxfattribs={'layer': 'REPERES'}).set_placement((10000, 5650), align=TA.MIDDLE_CENTER)
    G['R+1-D02'] = m.add_circle((14000, 5000), 150, dxfattribs={'layer': 'RESA'}).dxf.handle
    ml = m.add_multileader_mtext('Standard', dxfattribs={'layer': 'REPERES'})
    ml.set_content('R+1-D02', char_height=150)
    ml.add_leader_line(ezdxf.render.ConnectionSide.left, [Vec2(14150, 5000)])
    ml.build(Vec2(15200, 6000))
    G['D03'] = m.add_circle((16000, 5000), 80, dxfattribs={'layer': 'RESA'}).dxf.handle
    m.add_text('D03', height=150, dxfattribs={'layer': 'REPERES'}).set_placement((16000, 5300), align=TA.MIDDLE_CENTER)
    G['D04'] = m.add_lwpolyline(rect(18000, 5000, 450, 200), close=True, dxfattribs={'layer': 'RESA'}).dxf.handle   # cotes ≠ tableau
    m.add_text('D04', height=150, dxfattribs={'layer': 'REPERES'}).set_placement((18000, 5300), align=TA.MIDDLE_CENTER)
    G['D05a'] = m.add_lwpolyline(rect(20000, 8000, 1200, 2400), close=True, dxfattribs={'layer': 'RESA'}).dxf.handle
    m.add_text('D05', height=150, dxfattribs={'layer': 'REPERES'}).set_placement((20000, 9450), align=TA.MIDDLE_CENTER)
    G['D05b'] = m.add_lwpolyline(rect(40000, 8000, 1200, 2400), close=True, dxfattribs={'layer': 'COUPE'}).dxf.handle   # même repère en coupe
    m.add_text('D05', height=150, dxfattribs={'layer': 'COUPE'}).set_placement((40000, 9450), align=TA.MIDDLE_CENTER)
    b = d.blocks.new('REPERE')
    b.add_circle((0, 0), 2, dxfattribs={'layer': '0'})
    b.add_attdef('REF', (0, -0.5), dxfattribs={'height': 1})
    G['RES-08'] = m.add_lwpolyline(rect(24000, 5000, 500, 500), close=True, dxfattribs={'layer': 'RESA'}).dxf.handle
    m.add_blockref('REPERE', (24000, 5450), dxfattribs={'layer': 'REPERES', 'xscale': 100, 'yscale': 100}).add_auto_attribs({'REF': 'RES-08'})
    m.add_text('D10', height=150, dxfattribs={'layer': 'REPERES'}).set_placement((60000, 60000))   # repère loin de tout contour
    for i, (x, y) in enumerate(((30000, 2000), (32000, 2000), (34000, 2000))):
        m.add_lwpolyline(rect(x, y, 300, 300), close=True, dxfattribs={'layer': 'RESA'})   # D09 : mêmes cotes, pas de repère → plusieurs
    m.add_circle((36000, 2000), 37.5, dxfattribs={'layer': 'RESA'})   # D23 Ø75 : une seule géométrie de mêmes cotes, sans repère
    m.add_line((0, 0), (50000, 0), dxfattribs={'layer': 'COUPE'})
    ps = d.layouts.new('NOMENCLATURE')
    ps.add_lwpolyline([(5, 5), (415, 5), (415, 292), (5, 292)], close=True)   # cadre de la feuille : rectangle de présentation
    tableau(ps, 20, 280, COLS23, L23, titre='NOMENCLATURE DES RÉSERVATIONS')
    tableau(ps, 300, 280, *ACIERS, titre='NOMENCLATURE DES ACIERS')
    d.paperspace('Layout1').add_text('Cartouche fictif', height=3)
    F['NOMENC_23_PRESENTATION.dxf'] = d, G
    # 2. 7 lignes en MTEXT dans l'espace Objet, sans grille, cotes en cm, en-tête sur deux lignes, cellules vides et multilignes
    d, m = nouveau('R2000')
    rows = [['T1', 'Trémie local technique', '65 x 80', '+2,50 m', ''], ['T2', 'Fourreau\nchauffage', '%%c 20', '', 'à confirmer'],
            ['T3', '', 'S.O.', '+1,00 m', ''], ['T4', 'Passage gaine', '30x30', '+2,50 m', ''], ['T5', 'Carottage', 'Ø 12,5', '', ''],
            ['T6', 'Réservation\nboîtier\nincendie', '40 x 40', '+1,30 m', 'Lot SSI'], ['T7', 'Trémie', '', '', 'Dimensions à venir']]
    tableau(m, 0, -20000, [('Rép.', 1800), ('Désignation', 4500), ('Ouverture\n(cm)', 2600), ('Altimétrie', 2600), ('Remarques', 4000)], rows,
            h=150, grille=False, mtext=True, titre='TABLEAU DES RÉSERVATIONS')
    G = {'T1': m.add_lwpolyline(rect(5000, 5000, 650, 800), close=True, dxfattribs={'layer': 'RESA'}).dxf.handle}
    m.add_text('T1', height=150).set_placement((5000, 5000), align=TA.MIDDLE_CENTER)   # repère au centre du contour
    F['NOMENC_7_OBJET_MTEXT.dxf'] = d, G
    # 3. plusieurs tableaux dans la présentation active (ENTITIES, code 67) : 12 lignes avec grille, 7 lignes en-tête en bas sans grille
    d, m = nouveau()
    ps = d.paperspace('Layout1')
    tableau(ps, 20, 280, [('Repère', 16), ('Dimensions (mm)', 30), ('Niveau', 22)],
            [[f'A{i}', f'{200 + 50 * i}x{300 + 10 * i}' if i % 4 else 'Ø' + str(100 + 10 * i), f'+{i},00'] for i in range(1, 13)])
    tableau(ps, 120, 200, [('Réf.', 14), ('Désignation', 40), ('Ø (mm)', 18), ('Altimétrie', 22), ('Entreprise', 28)],
            [[f'B-{i}', f'Fourreau {i}', str(50 + 25 * i), f'+0,{i}0', 'Lot ' + 'ABCDEFG'[i - 1]] for i in range(1, 8)], grille=False, bas=True, titre='LISTE DES FOURREAUX')
    tableau(ps, 260, 280, *ACIERS)
    F['NOMENC_PLUSIEURS.dxf'] = d, {}
    # 4. tableau dans un bloc inséré (échelle 10) et tableau AutoCAD natif (ACAD_TABLE) lu par son bloc de rendu *T…
    d, m = nouveau()
    b = d.blocks.new('TAB_RESA')
    tableau(b, 0, 0, [('Repère', 16), ('Désignation', 36), ('Ouverture (mm)', 26)], [['P1', 'Trémie', '500x400'], ['P2', 'Fourreau', 'Ø150'], ['P3', 'Trémie', '']], calque='0')
    m.add_blockref('TAB_RESA', (1000, 2000), dxfattribs={'xscale': 10, 'yscale': 10, 'layer': 'NOMENC'})
    t = d.blocks.new_anonymous_block('T')
    tableau(t, 0, 0, [('Repère', 16), ('Description', 36), ('Dimensions', 26)], [['Q1', 'Trémie', '200x200'], ['Q2', 'Carottage', 'Ø80']], calque='0', titre='Réservations')
    m.add_blockref(t.name, (5000, 2000), dxfattribs={'layer': 'TABLE'})
    F['NOMENC_BLOC_TABLE.dxf'] = d, {'acad_table': t.name}
    out = {}
    for nom, (d, G) in F.items():
        p = os.path.join(dossier, nom)
        d.saveas(p)
        if nom == 'NOMENC_BLOC_TABLE.dxf':
            # entité ACAD_TABLE minimale (codes lus : 2 bloc de rendu, 10/20 insertion, 11/21 direction) : l'INSERT du bloc *T… devient ACAD_TABLE
            txt = open(p, encoding='utf-8').read()
            i = re.search(r'\n *2\n' + re.escape(G['acad_table']) + r'\n', txt[txt.index('ENTITIES'):]).start() + txt.index('ENTITIES')
            j = txt.rindex('\nINSERT\n', 0, i)
            txt = txt[:j] + '\nACAD_TABLE\n' + txt[j + len('\nINSERT\n'):]
            open(p, 'w', encoding='utf-8').write(txt)
        out[nom] = (p, G)
    return out
