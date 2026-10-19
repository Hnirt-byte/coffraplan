"""Essai LOCAL des nomenclatures sur un plan réel (fichier confidentiel : jamais dans Git, ni dans une PR, ni dans un journal).
  python tests/essai_plan_reel.py "C:/chemin/plan.dxf"            → bilan anonyme (comptes seulement)
  python tests/essai_plan_reel.py "C:/chemin/plan.dxf" --attendu 23 → code de sortie 1 si le nombre de lignes diffère
N'affiche aucun texte du plan : ni repère, ni désignation, ni nom de présentation, de calque ou de fichier, ni coordonnée.
Le bilan peut être recopié tel quel dans le fil du projet."""
import os, sys
from playwright.sync_api import sync_playwright

MOD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'modules', 'import')

BILAN = '''txt=>{const lu=CPI.lecteur.lirePlan({format:'dxf',nom:'plan.dxf',contenu:txt});if(!lu.ok)return {erreur:lu.message};
  const d=lu.document,C=CPI.detecteur.detecter(d).candidats,A=CPI.nomenclatures.analyser(d),
    S=CPI.nomenclatures.associer(A.nomenclatures,C,d,{uniteDessin:d.unite,exclus:A.ecartes.flatMap(e=>e.ids)}),P=d.presentations;
  const ou=x=>x.espace==='objet'?'espace Objet':'présentation n° '+(P.indexOf(x.presentation)+1);
  return {version:d.version,unite:d.unite,presentations:P.length,textes:d.textes.length,traits:d.traits.length,signalements:A.signalements.length,
    geometries:C.filter(c=>c.statut==='a_confirmer').length,
    nomenclatures:A.nomenclatures.map(N=>({ou:ou(N),lignes:N.lignes.length,qualite:N.qualite.niveau,motifs:N.qualite.motifs.length,
      colonnes:N.colonnes.map(c=>c.cle+' : '+N.lignes.filter(l=>l.cellules[N.colonnes.indexOf(c)]).length+' cellule(s) remplie(s)'),
      repere:N.lignes.filter(l=>l.repere).length,cotes:N.lignes.filter(l=>l.dims).length,a_verifier:N.lignes.filter(l=>l.a_verifier.length).length,
      geo:['trouvee','probable','multiple','absente'].map(k=>k+' '+N.lignes.filter(l=>S[l.id].statut===k).length).join(', ')})),
    ecartes:A.ecartes.map(e=>({ou:ou(e),nature:e.nature,lignes:e.nLignes}))}}'''


def main(a):
    if not a or not os.path.isfile(a[0]):
        sys.exit(__doc__)
    att = int(a[a.index('--attendu') + 1]) if '--attendu' in a else None
    b = open(a[0], 'rb').read()
    try:
        txt = b.decode('utf-8')
    except UnicodeDecodeError:
        txt = b.decode('cp1252')
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(); pg.goto('about:blank')
        for f in ('lecteur.js', 'dxf.js', 'detecteur.js', 'nomenclatures.js'):
            pg.add_script_tag(path=os.path.join(MOD, f))
        r = pg.evaluate(BILAN, txt); br.close()
    if 'erreur' in r:
        sys.exit('fichier non lu : ' + r['erreur'])
    print(f"DXF {r['version']} · unité {r['unite']} · {r['presentations']} présentation(s) · {r['textes']} texte(s) · {r['traits']} trait(s) · "
          f"{r['geometries']} géométrie(s) proposée(s) · {r['signalements']} signalement(s)")
    for i, n in enumerate(r['nomenclatures'], 1):
        print(f"Nomenclature {i} ({n['ou']}) : {n['lignes']} ligne(s), lecture {n['qualite']}, repères {n['repere']}, cotes lues {n['cotes']}, "
              f"à vérifier {n['a_verifier']} ; géométries : {n['geo']}")
        for c in n['colonnes']:
            print('    ' + c)
    for e in r['ecartes']:
        print(f"Tableau écarté ({e['ou']}) : {e['nature']}, {e['lignes']} ligne(s)")
    tot = sum(n['lignes'] for n in r['nomenclatures'])
    print(f'Total : {tot} ligne(s) de nomenclature')
    if att is not None and tot != att:
        print(f'ÉCART : {att} ligne(s) attendue(s)')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
