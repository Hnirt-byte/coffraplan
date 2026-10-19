"""Lecteur DXF du module d'import (modules/import/dxf.js) sur de vrais fichiers DXF écrits par ezdxf (chantier fictif) :
  1. lecture : unités ($INSUNITS mm / cm / m, absente → null, pouces → refus), calques, identifiants (handles), versions R12
     (POLYLINE + VERTEX) et R2000 (LWPOLYLINE), cercle en repère miroir ;
  2. détection : rectangle, rectangle tourné, carré, cercle, plusieurs réservations sur plusieurs calques ; polyligne ouverte,
     polyligne avec arc, quadrilatère croisé, ligne, texte : conservés en « non pris en charge » avec la raison ;
  3. fichiers incomplets ou invalides : refus explicite, sans exception ;
  4. chaîne complète dans l'appli : DXF → détecteur → adaptateur (confirmation, h saisie) → plan accepté par le moteur."""
import json, math, os, re, sys, tempfile
import ezdxf
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE

MOD = os.path.join(HERE, '..', 'modules', 'import')
JS = [os.path.join(MOD, f) for f in ('lecteur.js', 'dxf.js', 'detecteur.js', 'adaptateur.js')]


def rect(cx, cy, L, l, a=0):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-L / 2, -l / 2), (L / 2, -l / 2), (L / 2, l / 2), (-L / 2, l / 2))]


def nouveau(u=4, v='R2000'):
    d = ezdxf.new(v)
    if v != 'R12':
        d.header['$INSUNITS'] = u
    return d, d.modelspace()


def fichiers(dossier):
    """Écrit les DXF d'essai ; renvoie {nom: (texte, {repère: handle})}."""
    F = {}

    def save(nom, d, H=None):
        p = os.path.join(dossier, nom)
        d.saveas(p)
        F[nom] = (open(p, encoding='cp1252' if d.dxfversion == 'AC1009' else 'utf-8', errors='replace').read(), H or {})

    d, m = nouveau(); save('CHANTIER_DEMO_A_rect.dxf', d, {'r': m.add_lwpolyline(rect(1600, 800, 1200, 600), close=True, dxfattribs={'layer': 'RESA_RECT'}).dxf.handle})
    d, m = nouveau(); save('CHANTIER_DEMO_A_tourne.dxf', d, {'r': m.add_lwpolyline(rect(0, 0, 800, 400, 30), close=True, dxfattribs={'layer': 'RESA_RECT'}).dxf.handle})
    d, m = nouveau(6); save('CHANTIER_DEMO_A_carre.dxf', d, {'r': m.add_lwpolyline(rect(2.5, 1.5, 0.4, 0.4, 45), close=True, dxfattribs={'layer': 'RESA_CARRE'}).dxf.handle})
    d, m = nouveau(); save('CHANTIER_DEMO_A_cercle.dxf', d, {'c': m.add_circle((300, 400), 125, dxfattribs={'layer': 'RESA_FOURREAU'}).dxf.handle})
    d, m = nouveau(5)
    for n in ('RESA_R+1', 'RESA_R+2', 'RESA_FOURREAUX', 'COTATION'):
        d.layers.add(n)
    H = {'r1': m.add_lwpolyline(rect(500, 300, 120, 60), close=True, dxfattribs={'layer': 'RESA_R+1'}).dxf.handle,
         'r2': m.add_lwpolyline(rect(900, 300, 40, 40), close=True, dxfattribs={'layer': 'RESA_R+2'}).dxf.handle,
         'c1': m.add_circle((700, 100), 10, dxfattribs={'layer': 'RESA_FOURREAUX'}).dxf.handle,
         'c2': m.add_circle((750, 100), 5, dxfattribs={'layer': 'RESA_FOURREAUX'}).dxf.handle,
         'ln': m.add_line((0, 0), (100, 0), dxfattribs={'layer': 'COTATION'}).dxf.handle,
         'tx': m.add_text('CHANTIER_DEMO_A', dxfattribs={'layer': 'COTATION'}).dxf.handle}
    save('CHANTIER_DEMO_A_multi.dxf', d, H)
    d, m = nouveau(v='R12')
    save('CHANTIER_DEMO_B_r12.dxf', d, {'p': m.add_polyline2d(rect(0, 0, 1000, 500), close=True, dxfattribs={'layer': 'RESA'}).dxf.handle,
                                         'c': m.add_circle((0, 0), 100, dxfattribs={'layer': 'RESA'}).dxf.handle})
    d, m = nouveau(); save('ouverte.dxf', d, {'o': m.add_lwpolyline(rect(0, 0, 1000, 500), close=False).dxf.handle})
    d, m = nouveau(); save('arc.dxf', d, {'a': m.add_lwpolyline([(0, 0, 0, 0, 0), (1000, 0, 0, 0, 0.5), (1000, 500, 0, 0, 0), (0, 500, 0, 0, 0)], format='xyseb', close=True).dxf.handle})
    d, m = nouveau(0); save('sans_unite.dxf', d, {'r': m.add_lwpolyline(rect(0, 0, 1000, 500), close=True).dxf.handle})
    d, m = nouveau(1); m.add_circle((0, 0), 5); save('pouces.dxf', d)
    d, m = nouveau(); save('miroir.dxf', d, {'c': m.add_circle((100, 50), 75, dxfattribs={'extrusion': (0, 0, -1)}).dxf.handle})
    d, m = nouveau(); save('papillon.dxf', d, {'p': m.add_lwpolyline([(0, 0), (1000, 0), (0, 500), (1000, 500)], close=True).dxf.handle})
    d, m = nouveau(); save('refermee.dxf', d, {'p': m.add_lwpolyline(rect(0, 0, 1000, 500) + [rect(0, 0, 1000, 500)[0]], close=False).dxf.handle})
    # polylignes lissées (R12, POLYLINE 70 bit 2 = courbe ajustée, bit 4 = spline ; VERTEX 70 bit 8 = sommet de spline)
    for nom, fl, vfl in (('r12_ajustee.dxf', 2, 0), ('r12_spline.dxf', 4, 0), ('r12_sommet_spline.dxf', 0, 8)):
        d, m = nouveau(v='R12'); p = m.add_polyline2d(rect(0, 0, 1000, 500), close=True)
        p.dxf.flags |= fl
        for v in p.vertices:
            v.dxf.flags |= vfl
        save(nom, d, {'p': p.dxf.handle})
    # largeur non nulle : 43 (constante), 40 / 41 (par sommet), POLYLINE R12 (largeur par défaut de l'en-tête, largeur d'un VERTEX)
    d, m = nouveau(); p = m.add_lwpolyline(rect(0, 0, 1000, 500), close=True); p.dxf.const_width = 20; save('lw_largeur_cst.dxf', d, {'p': p.dxf.handle})
    d, m = nouveau(); save('lw_largeur_som.dxf', d, {'p': m.add_lwpolyline([(x, y, 0, 15, 0) for x, y in rect(0, 0, 1000, 500)], format='xyseb', close=True).dxf.handle})
    d, m = nouveau(v='R12'); save('r12_largeur.dxf', d, {'p': m.add_polyline2d(rect(0, 0, 1000, 500), close=True, dxfattribs={'default_start_width': 10, 'default_end_width': 10}).dxf.handle})
    d, m = nouveau(v='R12'); p = m.add_polyline2d(rect(0, 0, 1000, 500), close=True); p.vertices[2].dxf.start_width = 5
    save('r12_largeur_sommet.dxf', d, {'p': p.dxf.handle})
    d, m = nouveau(); m.add_circle((0, 0), 5); p = os.path.join(dossier, 'binaire.dxf'); d.saveas(p, fmt='bin')
    F['binaire.dxf'] = (open(p, 'rb').read().decode('latin-1'), {})
    t = F['CHANTIER_DEMO_A_rect.dxf'][0]
    F['tronque.dxf'] = (t[:len(t) // 2], {})
    F['sans_entities.dxf'] = ('0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nEOF\n', {})
    F['texte.dxf'] = ('Ceci n\'est pas un DXF\nbonjour\n', {})
    F['vide.dxf'] = ('', {})
    return F


def near(a, b, e=1e-6):
    return a is not None and abs(a - b) <= e


def t(s):
    code = re.sub(r'//[^\n]*', '', open(JS[1], encoding='utf-8').read())
    s.check(not re.search(r'\b(document|window|localStorage|sessionStorage)\s*\.|\bfetch\s*\(|XMLHttpRequest', code), 'dxf.js : aucun accès DOM / stockage / réseau')
    with tempfile.TemporaryDirectory() as tmp:
        F = fichiers(tmp)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('about:blank')
        for p in JS[:3]:
            pg.add_script_tag(path=p)
        R = pg.evaluate('''F=>{const o={};for(const [n,[txt]] of Object.entries(F)){const lu=CPI.lecteur.lirePlan({format:'dxf',nom:n,contenu:txt});
          o[n]={lu,D:lu.ok?CPI.detecteur.detecter(lu.document):null}}return o}''', F)
        s.check(not errs, 'page vide : aucune erreur JS', '; '.join(errs))
        b.close()

        def doc(n):
            return R[n]['lu'].get('document') or {}

        def cand(n, i=0):
            return R[n]['D']['candidats'][i] if R[n]['D'] else {}

        # 1. lecture
        for n in F:
            if n in ('pouces.dxf', 'binaire.dxf', 'tronque.dxf', 'sans_entities.dxf', 'texte.dxf', 'vide.dxf'):
                continue
            s.check(R[n]['lu']['ok'], f'{n} : lu', json.dumps(R[n]['lu'])[:300])
        d = doc('CHANTIER_DEMO_A_rect.dxf')
        s.check(d.get('format') == 'dxf' and d.get('fichier') == 'CHANTIER_DEMO_A_rect.dxf' and d.get('unite') == 'mm' and d.get('version') == 'AC1015',
                'rect : format, fichier, unité mm ($INSUNITS 4), version', json.dumps({k: d.get(k) for k in ('format', 'fichier', 'unite', 'version')}))
        e = d.get('entites', [{}])[0]
        s.check(e.get('id') == F['CHANTIER_DEMO_A_rect.dxf'][1]['r'] and e.get('calque') == 'RESA_RECT' and e.get('ferme') is True and len(e.get('points', [])) == 4,
                'rect : identifiant = handle DXF, calque, contour fermé de 4 sommets', json.dumps(e))
        s.check(doc('CHANTIER_DEMO_A_carre.dxf').get('unite') == 'm' and doc('CHANTIER_DEMO_A_multi.dxf').get('unite') == 'cm', 'unités m ($INSUNITS 6) et cm (5)')
        dm = doc('CHANTIER_DEMO_A_multi.dxf'); Hm = F['CHANTIER_DEMO_A_multi.dxf'][1]
        s.check({'RESA_R+1', 'RESA_R+2', 'RESA_FOURREAUX', 'COTATION', '0'} <= set(dm.get('calques', [])), 'multi : calques de la table LAYER', str(dm.get('calques')))
        s.check([x['id'] for x in dm.get('entites', [])] == list(Hm.values()), 'multi : une entité par objet, identifiants = handles, ordre du fichier')
        s.check(doc('sans_unite.dxf').get('unite') is None and cand('sans_unite.dxf').get('manquants') == ['h', 'unite'], '$INSUNITS 0 : unité null, signalée à compléter, pas devinée')
        d12 = doc('CHANTIER_DEMO_B_r12.dxf'); H12 = F['CHANTIER_DEMO_B_r12.dxf'][1]
        s.check(d12.get('unite') is None and d12.get('version') == 'AC1009', 'R12 (pas de $INSUNITS) : unité null', json.dumps({k: d12.get(k) for k in ('unite', 'version')}))
        s.check([x.get('type') for x in d12.get('entites', [])] == ['polyligne', 'cercle'] and d12['entites'][0]['id'] == H12['p'] and d12['entites'][0]['ferme'],
                'R12 : POLYLINE + VERTEX lue comme une polyligne fermée, sommets non comptés comme entités', json.dumps(d12.get('entites'))[:300])
        x = R['pouces.dxf']['lu']
        s.check(not x['ok'] and x['raison'] == 'document_invalide' and 'pouces' in x['message'], 'unité en pouces : refusée, raison écrite', json.dumps(x))
        c = doc('miroir.dxf').get('entites', [{}])[0]
        s.check(c.get('centre') == [-100, 50] and c.get('r') == 75, 'cercle en repère miroir (extrusion 0,0,-1) : centre ramené au repère général', json.dumps(c))

        # 2. détection
        x = cand('CHANTIER_DEMO_A_rect.dxf')
        s.check(x.get('type') == 'rect' and x['statut'] == 'a_confirmer' and near(x['dims']['L'], 1200) and near(x['dims']['l'], 600) and near(x['dims']['angle'], 0)
                and x['centre'] == [1600, 800] and x['unite'] == 'mm' and x['manquants'] == ['h'], 'rectangle 1200 × 600 mm : cotes, centre, h à compléter', json.dumps(x)[:400])
        s.check(x.get('source') == {'fichier': 'CHANTIER_DEMO_A_rect.dxf', 'format': 'dxf', 'calque': 'RESA_RECT', 'id': F['CHANTIER_DEMO_A_rect.dxf'][1]['r']},
                'rectangle : provenance (fichier, format, calque, handle)')
        x = cand('CHANTIER_DEMO_A_tourne.dxf')
        s.check(x.get('type') == 'rect' and near(x['dims']['L'], 800, 1e-6) and near(x['dims']['l'], 400, 1e-6) and near(x['dims']['angle'], 30, 1e-6)
                and near(x['centre'][0], 0, 1e-9) and near(x['centre'][1], 0, 1e-9) and 'carré' not in ' '.join(x['remarques']), 'rectangle tourné de 30° : cotes, orientation, centre', json.dumps(x)[:400])
        x = cand('CHANTIER_DEMO_A_carre.dxf')
        s.check(x.get('type') == 'rect' and near(x['dims']['L'], 0.4, 1e-9) and near(x['dims']['l'], 0.4, 1e-9) and near(x['dims']['angle'] % 90, 45, 1e-6)
                and 'carré potentiel' in ' '.join(x['remarques']) and x['unite'] == 'm', 'carré 0,4 m tourné de 45° : carré potentiel signalé, unité m', json.dumps(x)[:400])
        x = cand('CHANTIER_DEMO_A_cercle.dxf')
        s.check(x.get('type') == 'circ' and x['dims'] == {'D': 250} and x['centre'] == [300, 400] and x['source']['calque'] == 'RESA_FOURREAU', 'cercle : Ø 250, centre, calque', json.dumps(x))
        C = R['CHANTIER_DEMO_A_multi.dxf']['D']['candidats']
        s.check([(c['type'], c['source']['calque']) for c in C] == [('rect', 'RESA_R+1'), ('rect', 'RESA_R+2'), ('circ', 'RESA_FOURREAUX'), ('circ', 'RESA_FOURREAUX'), (None, 'COTATION'), (None, 'COTATION')],
                'multi : 2 rectangles et 2 cercles sur 3 calques ; ligne et texte non pris en charge', json.dumps([(c['type'], c['source']['calque']) for c in C]))
        s.check([c['remarques'] for c in C[4:]] == [['géométrie non prise en charge : LINE'], ['géométrie non prise en charge : TEXT']], 'multi : nature de la ligne et du texte écrite')
        s.check(all(c['statut'] in ('a_confirmer', 'non_pris_en_charge') for n in R if R[n]['D'] for c in R[n]['D']['candidats']), 'aucun candidat validé d\'office, dans aucun fichier')
        s.check(cand('CHANTIER_DEMO_B_r12.dxf').get('type') == 'rect' and cand('CHANTIER_DEMO_B_r12.dxf', 1).get('type') == 'circ', 'R12 : rectangle et cercle détectés')
        for n, why in (('ouverte.dxf', 'polyligne ouverte'), ('arc.dxf', 'LWPOLYLINE avec arcs'), ('papillon.dxf', 'non rectangulaire'),
                       ('r12_ajustee.dxf', 'POLYLINE lissée'), ('r12_spline.dxf', 'POLYLINE lissée'), ('r12_sommet_spline.dxf', 'POLYLINE lissée'),
                       ('lw_largeur_cst.dxf', 'LWPOLYLINE avec largeur non nulle'), ('lw_largeur_som.dxf', 'LWPOLYLINE avec largeur non nulle'),
                       ('r12_largeur.dxf', 'POLYLINE avec largeur non nulle'), ('r12_largeur_sommet.dxf', 'POLYLINE avec largeur non nulle')):
            x = cand(n)
            s.check(x.get('type') is None and x['statut'] == 'non_pris_en_charge' and why in ' '.join(x['remarques']) and x['geometrie']['id'] == F[n][1][next(iter(F[n][1]))],
                    f'{n} : non pris en charge ({why}), géométrie et identifiant conservés', json.dumps(x)[:300])
        x = cand('refermee.dxf')
        s.check(x.get('type') == 'rect' and x['geometrie']['ferme'] is True, 'polyligne non marquée fermée mais refermée exactement : rectangle', json.dumps(x)[:300])

        # 3. fichiers invalides
        for n, why in (('binaire.dxf', 'binaire'), ('tronque.dxf', ''), ('sans_entities.dxf', 'ENTITIES'), ('texte.dxf', 'illisible'), ('vide.dxf', 'vide')):
            x = R[n]['lu']
            s.check(not x['ok'] and x['raison'] == 'document_invalide' and why in x['message'], f'{n} : refusé ({x.get("message")})', json.dumps(x)[:300])

        # 4. chaîne complète dans l'appli
        b, pg, errs = open_app(pw)
        for p in JS:
            pg.add_script_tag(path=p)
        r = pg.evaluate('''txt=>{
          const mod=f=>{el('iCh').value='CHANTIER_DEMO_A';el('iForme').value=f;updF();const d=coll();delete d.date;return d};
          const M={rect:mod('rect'),carre:mod('carre'),circ:mod('circ')},moteur={migr,canon,checks,limErr,badDims},A=CPI.adaptateur.versPlan;
          const C=CPI.detecteur.detecter(CPI.lecteur.lirePlan({format:'dxf',nom:'CHANTIER_DEMO_A_multi.dxf',contenu:txt}).document).candidats;
          const ok=x=>{if(!x.ok)return x;const c=canon(migr(x.plan));return Object.assign(x,{nDebit:debit(c,null).length})};
          return {sansH:A(C[0],{confirme:true},{moteur,modele:M.rect}),rect:ok(A(C[0],{confirme:true,h:300,ref:'r1'},{moteur,modele:M.rect})),
            carre:ok(A(C[1],{confirme:true,h:250},{moteur,modele:M.carre})),circ:ok(A(C[2],{confirme:true,h:200},{moteur,modele:M.circ})),
            ligne:A(C[4],{confirme:true,h:200},{moteur,modele:M.rect}),P:P.length}}''', F['CHANTIER_DEMO_A_multi.dxf'][0])
        s.check(not r['sansH']['ok'] and r['sansH']['manquants'] == ['h'], 'chaîne : hauteur absente du DXF → à compléter')
        x = r['rect']; p = x.get('plan', {})
        s.check(x['ok'] and p.get('forme') == 'rect' and p.get('L') == 1200 and p.get('l') == 600 and p.get('h') == 300 and p.get('ref') == 'R1' and x.get('nDebit', 0) > 0
                and x['provenance']['calque'] == 'RESA_R+1' and x['provenance']['id'] == Hm['r1'] and x['provenance']['unite_source'] == 'cm',
                'chaîne : rectangle 120 × 60 cm → plan rect 1200 × 600 mm, débit calculé, provenance', json.dumps(x)[:500])
        s.check(r['carre']['ok'] and r['carre']['plan']['forme'] == 'carre' and r['carre']['plan']['L'] == 400, 'chaîne : carré 40 cm → plan carré 400 mm', json.dumps(r['carre'])[:300])
        s.check(r['circ']['ok'] and r['circ']['plan']['D'] == 200 and r['circ'].get('nDebit') is not None, 'chaîne : cercle Ø 20 cm → fourreau Ø 200 mm', json.dumps(r['circ'])[:300])
        s.check(not r['ligne']['ok'] and r['ligne']['raison'] == 'non_pris_en_charge', 'chaîne : ligne confirmée → non prise en charge')
        s.check(r['P'] == 0, 'chaîne : aucun plan enregistré sans action de l\'utilisateur')
        s.check(not [e for e in errs if 'net::' not in e], 'appli : aucune erreur JS', '; '.join(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_dxf')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
