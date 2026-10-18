"""Module d'import de plans (modules/import, hors appli) — contrat de données sur des objets fictifs :
  1. isolement : lecteur (A) et détecteur (B) chargés dans une page vide, sans l'appli ; aucun accès au DOM, au stockage ni
     au moteur dans les sources A, B et C ;
  2. lecteur : document normalisé accepté, formats non écrits (DXF, IFC, PDF) refusés explicitement, document invalide refusé ;
  3. détecteur : rectangle, rectangle tourné, cercle, géométrie non prise en charge (ellipse, trapèze, polyligne ouverte),
     hauteur absente, unité absente ; unités, cotes, coordonnées, calque et identifiant source conservés ; jamais « validé » ;
  4. adaptateur (dans l'appli, avec le vrai moteur) : refus sans confirmation, à compléter (h, unité), forme incompatible,
     cotes refusées par le moteur ; plans rect / carré / circ convertis en mm, contrôlés, exploitables par debit et gen ;
     aucune clé nouvelle dans le plan ; plans enregistrés, stockage et modèle inchangés."""
import copy, json, os, re, sys
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE

MOD = os.path.join(HERE, '..', 'modules', 'import')
JS = [os.path.join(MOD, f) for f in ('lecteur.js', 'detecteur.js', 'adaptateur.js')]

# Plan fictif en cm (unités du fichier source conservées par le détecteur)
DOC = {'format': 'normalise', 'fichier': 'R+1_fictif.dxf', 'unite': 'cm', 'entites': [
    {'id': '2A', 'calque': 'RESA_RECT', 'type': 'polyligne', 'ferme': True, 'points': [[1000, 500], [1120, 500], [1120, 560], [1000, 560]], 'h': 25},
    {'id': '2B', 'calque': 'RESA_CIRC', 'type': 'cercle', 'centre': [300, 400], 'r': 12.5},
    {'id': '2C', 'calque': 'RESA', 'type': 'autre', 'nature': 'ELLIPSE'},
    {'id': '2D', 'calque': 'RESA', 'type': 'polyligne', 'ferme': True, 'points': [[0, 0], [100, 0], [120, 50], [0, 50]]},
    {'id': '2E', 'calque': 'RESA', 'type': 'polyligne', 'ferme': False, 'points': [[0, 0], [100, 0], [100, 50], [0, 50]]},
    # carré de 40 cm tourné de 30°, contour refermé (5 points, le dernier = le premier)
    {'id': '2F', 'calque': 'RESA_RECT', 'type': 'polyligne', 'ferme': True, 'points': [[0, 0], [34.64101615, 20], [14.64101615, 54.64101615], [-20, 34.64101615], [0, 0]], 'h': 30},
]}


def near(a, b, e=1e-6):
    return a is not None and abs(a - b) <= e


def t(s):
    srcs = {os.path.basename(p): open(p, encoding='utf-8').read() for p in JS}
    for n, src in srcs.items():  # 1. isolement (sources)
        code = re.sub(r'//[^\n]*', '', src)
        s.check(not re.search(r'\b(document|window|localStorage|sessionStorage)\s*\.|\bfetch\s*\(|XMLHttpRequest', code), f'{n} : aucun accès DOM / stockage / réseau')
        s.check(not re.search(r'(?<![.\w])(migr|canon|checks|limErr|badDims|debit|gen|coll|el|P)\s*\(', code), f'{n} : aucun appel direct au moteur ou à l\'interface')
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('about:blank')
        for p in JS[:2]:
            pg.add_script_tag(path=p)
        r = pg.evaluate('''doc=>{const A=CPI.lecteur,B=CPI.detecteur,d0=JSON.stringify(doc);
          const lu=A.lirePlan({format:'normalise',contenu:JSON.stringify(doc)}),D=B.detecter(lu.document);
          const bad=JSON.parse(d0);bad.unite='pouce';bad.entites.push({type:'cercle',centre:[0,0],r:1},{id:'2A',type:'spline'});
          return {lu:{ok:lu.ok},D,inchange:JSON.stringify(lu.document)===d0,
            fmts:['dxf','ifc','pdf'].map(f=>A.lirePlan({format:f,nom:'x.'+f,contenu:''})),
            inval:A.lirePlan({format:'normalise',contenu:bad}),json:A.lirePlan({format:'normalise',contenu:'{pas du json'}),
            sansU:B.detecter(Object.assign(JSON.parse(d0),{unite:null})).candidats[0],
            presque:B.detecter({fichier:'x',format:'normalise',unite:'mm',entites:[{id:1,type:'polyligne',ferme:true,points:[[0,0],[1000,0],[1000,600],[0,620]]}]}).candidats[0],
            moteur:typeof canon,dom:document.body?document.body.innerHTML.length:0}}''', DOC)
        s.check(not errs, 'page vide : aucune erreur JS', '; '.join(errs))
        s.check(r['moteur'] == 'undefined' and r['dom'] == 0, 'A et B fonctionnent sans l\'appli et n\'écrivent rien dans la page')
        # 2. lecteur
        s.check(r['lu']['ok'], 'lecteur : document normalisé accepté')
        for x, f in zip(r['fmts'], ('dxf', 'ifc', 'pdf')):
            s.check(not x['ok'] and x['raison'] == 'format_non_pris_en_charge', f'lecteur : {f} refusé explicitement', json.dumps(x))
        e = ' | '.join(r['inval'].get('erreurs', []))
        s.check(not r['inval']['ok'] and r['inval']['raison'] == 'document_invalide' and 'pouce' in e and 'identifiant source absent' in e and 'en double' in e and 'spline' in e,
                'lecteur : unité inconnue, identifiant absent ou en double, type inconnu refusés', e)
        s.check(not r['json']['ok'] and r['json']['raison'] == 'document_invalide', 'lecteur : JSON illisible refusé sans exception')
        # 3. détecteur
        C = r['D']['candidats']
        s.check(r['inchange'], 'détecteur : document source non modifié')
        s.check(len(C) == 6 and r['D']['unite'] == 'cm' and r['D']['fichier'] == 'R+1_fictif.dxf', 'détecteur : un candidat par entité, unité et fichier du document')
        s.check(all(c['statut'] in ('a_confirmer', 'non_pris_en_charge') for c in C), 'détecteur : aucun candidat validé d\'office')
        rc = C[0]
        s.check(rc['type'] == 'rect' and rc['statut'] == 'a_confirmer' and near(rc['dims']['L'], 120) and near(rc['dims']['l'], 60) and near(rc['dims']['angle'], 0)
                and rc['centre'] == [1060, 530] and rc['h'] == 25 and rc['manquants'] == [] and rc['unite'] == 'cm', 'rectangle : cotes (cm), centre, hauteur', json.dumps(rc))
        s.check(rc['source'] == {'fichier': 'R+1_fictif.dxf', 'format': 'normalise', 'calque': 'RESA_RECT', 'id': '2A'} and rc['geometrie'] == DOC['entites'][0],
                'rectangle : provenance (calque, identifiant) et géométrie source conservées')
        cc = C[1]
        s.check(cc['type'] == 'circ' and cc['statut'] == 'a_confirmer' and near(cc['dims']['D'], 25) and cc['centre'] == [300, 400] and cc['h'] is None and cc['manquants'] == ['h'],
                'cercle : Ø, centre, hauteur absente signalée', json.dumps(cc))
        for c, why in ((C[2], 'ELLIPSE'), (C[3], 'non rectangulaire'), (C[4], 'ouverte')):
            s.check(c['type'] is None and c['statut'] == 'non_pris_en_charge' and why in ' '.join(c['remarques']) and c['geometrie'] == DOC['entites'][int(c['id'][1:]) - 1],
                    f'non pris en charge ({why}) : géométrie conservée, raison écrite', json.dumps(c))
        rt = C[5]
        s.check(rt['type'] == 'rect' and near(rt['dims']['L'], 40, 1e-5) and near(rt['dims']['l'], 40, 1e-5) and near(rt['dims']['angle'], 30, 1e-5)
                and near(rt['centre'][0], 7.320508, 1e-5) and near(rt['centre'][1], 27.320508, 1e-5), 'rectangle tourné (contour refermé) : cotes, angle, centre', json.dumps(rt))
        s.check(r['sansU']['manquants'] == ['unite'] and r['sansU']['unite'] is None, 'unité absente : signalée, pas devinée')
        s.check(r['presque']['statut'] == 'non_pris_en_charge', 'quadrilatère presque rectangle (écart 20 mm / 1 166 mm) : non pris en charge')
        b.close()

        # 4. adaptateur, dans l'appli
        b, pg, errs = open_app(pw)
        for p in JS:
            pg.add_script_tag(path=p)
        r = pg.evaluate('''doc=>{
          P.push({v:12,ch:'EXISTANT',ref:'A1',forme:'rect',L:500,l:400,h:200,ep:18,cp:{j:CPDEF},nb:1});svP();
          const P0=JSON.stringify(P),LS0=localStorage.getItem('resa3');
          const mod=f=>{el('iCh').value='CHANTIER FICTIF';el('iForme').value=f;updF();const d=coll();delete d.date;return d};
          const M={rect:mod('rect'),carre:mod('carre'),circ:mod('circ'),rect_fond:mod('rect_fond')},M0=JSON.stringify(M);
          const moteur={migr,canon,checks,limErr,badDims},cx=f=>({moteur,modele:M[f]}),A=CPI.adaptateur.versPlan;
          const C=CPI.detecteur.detecter(CPI.lecteur.lirePlan({format:'normalise',contenu:doc}).document).candidats;
          const ok=x=>{if(!x.ok)return x;const c=canon(migr(x.plan)),R=debit(c,null);return Object.assign(x,{nDebit:R.length,html:gen(x.plan).length})};
          const tiny=JSON.parse(JSON.stringify(C[0]));tiny.dims={L:0.2,l:0.2,angle:0};
          const sansU=CPI.detecteur.detecter(Object.assign(JSON.parse(JSON.stringify(doc)),{unite:null})).candidats[0];
          const res={
            nonConf:A(C[0],null,cx('rect')),nonConf2:A(C[0],{confirme:'oui'},cx('rect')),
            rect:ok(A(C[0],{confirme:true,ref:'t1',nb:2},cx('rect'))),
            rectFond:ok(A(C[0],{confirme:true,forme:'rect_fond'},cx('rect_fond'))),
            carre:ok(A(C[5],{confirme:true},cx('carre'))),
            circSansH:A(C[1],{confirme:true},cx('circ')),
            circ:ok(A(C[1],{confirme:true,h:300},cx('circ'))),
            ellipse:A(C[2],{confirme:true},cx('rect')),
            incompat:A(C[0],{confirme:true,forme:'circ'},cx('circ')),
            carreRect:A(C[0],{confirme:true,forme:'carre'},cx('carre')),
            sansModele:A(C[0],{confirme:true},cx('circ')),
            uniteManque:A(sansU,{confirme:true},cx('rect')),
            uniteDonnee:ok(A(sansU,{confirme:true,unite:'mm'},cx('rect'))),
            tiny:A(tiny,{confirme:true},cx('carre'))};
          res.inchange={P:JSON.stringify(P)===P0,LS:localStorage.getItem('resa3')===LS0,M:JSON.stringify(M)===M0};
          res.cles={rect:Object.keys(M.rect),circ:Object.keys(M.circ)};return res}''', DOC)
        for k in ('nonConf', 'nonConf2'):
            s.check(not r[k]['ok'] and r[k]['raison'] == 'non_confirme', f'adaptateur : refus sans confirmation explicite ({k})')
        x = r['rect']; p = x.get('plan', {})
        s.check(x['ok'] and p.get('forme') == 'rect' and p.get('L') == 1200 and p.get('l') == 600 and p.get('h') == 250 and p.get('ref') == 'T1' and p.get('nb') == 2
                and p.get('ch') == 'CHANTIER FICTIF', 'rect : converti en mm, référence et nombre, chantier du modèle', json.dumps(x)[:600])
        pv = x.get('provenance', {})
        s.check(pv.get('calque') == 'RESA_RECT' and pv.get('id') == '2A' and pv.get('fichier') == 'R+1_fictif.dxf' and pv.get('unite_source') == 'cm'
                and pv.get('centre') == [1060, 530] and pv.get('dims_source', {}).get('L') == 120, 'rect : provenance hors du plan (calque, identifiant, unité, centre, cotes source)')
        s.check(x.get('nDebit', 0) > 0 and x.get('html', 0) > 1000, 'rect : exploitable par debit et gen')
        s.check(set(p) <= set(r['cles']['rect']), 'rect : aucune clé nouvelle dans le plan (format de sauvegarde inchangé)', str(set(p) - set(r['cles']['rect'])))
        s.check(r['rectFond']['ok'] and r['rectFond']['plan']['forme'] == 'rect_fond' and r['rectFond'].get('nDebit', 0) > 0, 'rect : forme choisie par l\'utilisateur (avec fond)')
        x = r['carre']
        s.check(x['ok'] and x['plan']['forme'] == 'carre' and x['plan']['L'] == 400 and x['plan']['l'] == 400 and x['plan']['h'] == 300 and x['provenance']['h_saisie'] is False,
                'carré tourné : forme carrée par défaut, 400 mm, h du fichier', json.dumps(x)[:400])
        x = r['circSansH']
        s.check(not x['ok'] and x['raison'] == 'a_completer' and x['manquants'] == ['h'], 'cercle sans hauteur : à compléter (h)', json.dumps(x))
        x = r['circ']; p = x.get('plan', {})
        s.check(x['ok'] and p.get('forme') == 'circ' and p.get('D') == 250 and p.get('h') == 300 and x['provenance']['h_saisie'] is True and x.get('nDebit') is not None,
                'cercle + h saisie : fourreau Ø 250 mm, h 300 mm', json.dumps(x)[:400])
        s.check(set(p) <= set(r['cles']['circ']), 'cercle : aucune clé nouvelle dans le plan')
        s.check(not r['ellipse']['ok'] and r['ellipse']['raison'] == 'non_pris_en_charge' and 'ELLIPSE' in ' '.join(r['ellipse']['messages']), 'ellipse confirmée : non prise en charge, raison transmise')
        s.check(not r['incompat']['ok'] and r['incompat']['raison'] == 'forme_incompatible', 'rectangle → fourreau circulaire : refusé')
        s.check(not r['carreRect']['ok'] and r['carreRect']['raison'] == 'forme_incompatible', 'rectangle 1200 × 600 → carré : refusé')
        s.check(not r['sansModele']['ok'] and r['sansModele']['raison'] == 'modele_manquant', 'modèle d\'une autre forme : refusé')
        s.check(not r['uniteManque']['ok'] and r['uniteManque']['manquants'] == ['unite'], 'unité absente : à compléter (unité)')
        s.check(r['uniteDonnee']['ok'] and r['uniteDonnee']['plan']['L'] == 120 and r['uniteDonnee']['plan']['h'] == 25 and r['uniteDonnee']['provenance']['unite_source'] is None
                and r['uniteDonnee']['provenance']['unite'] == 'mm', 'unité donnée par l\'utilisateur : utilisée, absence d\'origine tracée')
        x = r['tiny']
        s.check(not x['ok'] and x['raison'] == 'invalide' and any('hors limites' in m for m in x['messages']), 'cotes de 2 mm : refusées par limErr du moteur', json.dumps(x)[:400])
        s.check(all(r['inchange'].values()), 'plans enregistrés, stockage du navigateur et modèles inchangés', json.dumps(r['inchange']))
        s.check(not [e for e in errs if 'net::' not in e], 'appli : aucune erreur JS', '; '.join(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_import')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
