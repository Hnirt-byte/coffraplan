"""Phase 6 : moteur de reconnaissance PP-OCRv6 (modules/import/ppocr.js, ONNX Runtime Web intégré) et son branchement dans
ocr.js (tableaux à grille, repères dessinés), sur l'interface réelle et des documents entièrement fictifs.
Demande de Kévin du 21/10/2026 (directive « modernisation du moteur de reconnaissance ») :
  moteur local et gratuit, exploitable commercialement, aucune requête réseau ; Tesseract gardé au choix ; texte, confiance et
  orientation ; textes verticaux ; en-têtes fusionnés ; cellules sur plusieurs lignes ; aucune cote inventée.
Les valeurs reconnues dépendent du rendu des polices : contrôles sur des textes choisis, comparés sans espaces ni casse."""
import json, os, re, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE
import pdf_ocr_fictifs as PO

ROOT = os.path.join(HERE, '..')
nz = lambda s: re.sub(r'\s+', '', str(s or '')).upper()


def page_reperes(d):
    """Plan fictif : deux repères en contours, l'un horizontal, l'autre écrit de bas en haut (comme un repère le long d'un voile)."""
    p = PO.Page()
    p.rect(100, 100, 300, 200)
    p.contours(120, 320, 'RB12', 9)
    p.ops.append(b'q 0 1 -1 0 460 150 cm')   # rotation de 90° : texte vertical, lu de bas en haut
    p.contours(0, 0, 'RV34', 9)
    p.ops.append(b'Q')
    return PO.ecrire(os.path.join(d, 'PP_REPERES.pdf'), [p])


def t(s):
    html = open(os.path.join(ROOT, 'app', 'CoffraPlan.html'), encoding='utf-8').read()
    s.check(all(f'id="{i}"' in html for i in ('ppocr-ort-src', 'ppocr-ort-mjs', 'ppocr-ort-wasm', 'ppocr-rec', 'ppocr-dict')),
            'HTML autonome : ONNX Runtime Web, wasm, modèle PP-OCRv6 et dictionnaire intégrés')
    rc = subprocess.run([sys.executable, os.path.join(ROOT, 'modules', 'import', 'assembler.py'), '--check'], capture_output=True, text=True)
    s.check(rc.returncode == 0, 'assemblage : blocs PP-OCR identiques aux fichiers publiés (empreintes SHA-256)', rc.stdout + rc.stderr)
    lic = os.path.join(ROOT, 'modules', 'import', 'vendor', 'ppocr')
    s.check(all(os.path.exists(os.path.join(lic, f)) for f in ('README.md', 'LICENSE-onnxruntime-web', 'LICENSE-Apache-2.0-PaddleOCR-RapidOCR')),
            'licences et provenance du moteur présentes (README, MIT, Apache-2.0)')
    tmp = tempfile.mkdtemp()
    F = PO.fichiers(tmp)
    R1 = page_reperes(tmp)
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        net = []
        pg.context.route(lambda u: not u.startswith('file:') and not u.startswith('blob:') and not u.startswith('data:'),
                         lambda r: (None if 'fonts.g' in r.request.url else net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = lambda x, *a: pg.evaluate(x, *a)

        # ---- moteur : chargement hors connexion, lecture d'une ligne, texte vertical
        s.check(J('CPI.ocr.moteur()') == 'ppocr', 'moteur par défaut : PP-OCRv6')
        J('CPI.ppocr.charger().then(()=>1)')
        lig = '''(t,deg)=>{const c=document.createElement('canvas'),x=c.getContext('2d');x.font='28px Arial';const w=Math.ceil(x.measureText(t).width)+24;
          const v=deg%180;c.width=v?48:w;c.height=v?w:48;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.fillStyle='#000';g.font='28px Arial';
          g.translate(c.width/2,c.height/2);g.rotate(deg*Math.PI/180);g.textAlign='center';g.textBaseline='middle';g.fillText(t,0,0);return c}'''
        r = J(f'''async()=>{{const L={lig};return CPI.ppocr.lire([L('RA01 650x800 +3,20',0),L('Fourreau évacuation',0)])}}''')
        s.check(nz(r[0]['texte']) in ('RA01650X800+3,20', 'RA01650×800+3,20') and 'ÉVACUATION' in nz(r[1]['texte']) and r[0]['conf'] >= 75 and r[0]['orientation'] == 0,
                'ligne lue : repère, cote, niveau, accents ; confiance 0-100 ; orientation 0', json.dumps(r, ensure_ascii=False)[:300])
        r = J(f'''async()=>{{const L={lig};return CPI.ppocr.lire([L('RV34',-90),L('RV34',90)],{{vertical:true}})}}''')
        s.check([nz(x['texte']) for x in r] == ['RV34', 'RV34'] and [x['orientation'] for x in r] == [90, 270],
                'texte vertical : lu dans les deux sens, le plus sûr gardé (bas en haut = 90°, haut en bas = 270°)', json.dumps([(x['texte'], x['orientation'], x['conf']) for x in r]))
        r = J(f'''async()=>{{const c=document.createElement('canvas');c.width=60;c.height=48;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,60,48);return CPI.ppocr.lire([c])}}''')
        s.check(r[0]['texte'] == '', 'image vide : texte vide (rien d\'inventé)', json.dumps(r))

        # ---- découpage d'une cellule : lignes, traits intérieurs d'un en-tête fusionné, lignes serrées
        r = J('''()=>{const c=document.createElement('canvas');c.width=400;c.height=120;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,400,120);g.fillStyle='#000';
            g.font='bold 26px Arial';g.fillText('DIMENSIONS (mm)',80,32);g.fillRect(0,46,400,3);g.fillRect(198,46,3,74);g.fillText('Hauteur',40,95);g.fillText('Largeur',240,95);
            const B=CPI.ocr.bandes(c).B;return B.map(b=>b.map(Math.round))}''')
        s.check(len(r) == 3 and r[0][1] < 46 and r[1][1] > 46 and r[1][2] <= 198 and r[2][0] >= 201,
                'en-tête fusionné : traits intérieurs effacés, une ligne puis deux sous-colonnes', json.dumps(r))
        r = J('''()=>{const c=document.createElement('canvas');c.width=420;c.height=70;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,420,70);g.fillStyle='#000';
            g.font='26px Arial';g.fillText('Selon le plan de',10,30);g.fillText('détail agitateur',10,58);g.fillRect(2,4,3,62);return CPI.ocr.bandes(c).B.length}''')
        s.check(r == 2, 'deux lignes sans interligne blanc (trait vertical à cheval) : séparées', str(r))

        # ---- tableau à grille (texte en contours) : PP-OCR puis Tesseract au choix
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['OCR_1_CONTOURS.pdf'][0])
        pg.wait_for_function('el("dxpPg")&&el("dxpPg").textContent.includes("/ 3")')
        s.check(J('el("dxoMot")&&el("dxoMot").value') == 'ppocr', 'fenêtre d\'import : choix du moteur OCR, PP-OCRv6 par défaut')
        inf = F['OCR_1_CONTOURS.pdf'][1]

        def ocr(z):
            J('z=>{dxiVue("p");DXI.page=z.page;dxpPage();dxpZone(Object.assign({unite:"pt"},z))}', z)
            pg.wait_for_function('!el("dxpZo").disabled'); pg.click('#dxpZo'); pg.wait_for_function('!DXI.ocJob', timeout=300000)
            return J('DXI.OC&&{m:DXI.OC.mesures,rows:DXI.OC.rows.map(w=>w.cells)}')
        G = ocr(inf['z1'])
        exp = [dict(repere=l[0], description=l[1].replace('\n', ' '), ouverture=l[3], niveau=l[5]) for l in PO.L1]
        got = [{k: w.get(k, '') for k in ('repere', 'description', 'ouverture', 'niveau')} for w in G['rows']] if G else []
        ok = sum(1 for a, e in zip(got, exp) for k in e if nz(a[k]) == nz(e[k]))
        s.check(G and 'PP-OCRv6' in G['m']['moteur'] and len(got) == 7 and ok >= 26, 'tableau à grille par PP-OCRv6 : 7 lignes, au moins 26 champs sur 28 exacts (repère, désignation sur deux lignes, cote, niveau)',
                f'{ok}/28 ' + json.dumps(got, ensure_ascii=False)[:600])
        s.check(nz(got[1]['ouverture']) in ('Ø250', '250') and (nz(got[1]['ouverture']) == 'Ø250' or 'ouverture' in J('Object.keys(DXI.OC.rows[1].doute).filter(k=>DXI.OC.rows[1].doute[k])')),
                'Ø : reconnu, sinon nombre brut signalé (jamais converti en Ø)', got[1]['ouverture'])
        s.check(J('DXI.OC.rows.flatMap(w=>Object.values(w.cells)).some(v=>/×|一|∅|[\\uFF01-\\uFF5E]/.test(v))') is False,
                'typographie du modèle multilingue ramenée (× entre nombres, ∅, « 一 », pleine chasse)')
        J('()=>{el("dxoMot").value="tesseract";el("dxoMot").onchange()}')
        G2 = ocr(inf['z1'])
        s.check(J('CPI.ocr.moteur()') == 'tesseract' and G2 and 'Tesseract' in G2['m']['moteur'] and len(G2['rows']) == 7 and J('localStorage.getItem("resaOcrMot")') == 'tesseract',
                'Tesseract toujours disponible au choix (gardé dans le navigateur)', json.dumps(G2 and G2['m'], ensure_ascii=False)[:300])
        J('()=>{el("dxoMot").value="ppocr";el("dxoMot").onchange()}')

        # ---- repères dessinés : bloc horizontal et bloc vertical
        pg.set_input_files('#dxiF', R1); pg.wait_for_function('DXI&&DXI.doc&&DXI.NA&&DXI.doc.fichier==="PP_REPERES.pdf"')
        r = J('''async()=>{const g=await dxrGeo(1),K=CPI.geometrie.blocsTexte(g,{verticaux:true}),r=await CPI.ocr.lireBlocs(DXI.pdf,1,K,{run:'b1'});
            return{K:K.map(k=>({v:!!k.vertical,x:Math.round((k.x0+k.x1)/2),y:Math.round((k.y0+k.y1)/2)})),T:r.textes.map(t=>({t:t.texte,rot:t.rot,o:t.ocr.orientation,m:t.ocr.moteur,x:Math.round(t.x),y:Math.round(t.y)})),M:r.mesures}}''')
        T = {nz(x['t']): x for x in r['T']}
        s.check('RB12' in T and T['RB12']['rot'] == 0 and 'RV34' in T and T['RV34']['rot'] == 90 and T['RV34']['m'] == 'ppocr' and r['M']['verticaux'] >= 1,
                'repères dessinés : horizontal lu, vertical (bas en haut) détecté et lu, orientation gardée', json.dumps(r, ensure_ascii=False)[:600])
        J('CPI.ocr.choisirMoteur("tesseract")')
        r2 = J('''async()=>{const g=await dxrGeo(1);return CPI.geometrie.blocsTexte(g,{}).some(k=>k.vertical)}''')
        s.check(r2 is False, 'sans PP-OCR : aucun bloc vertical proposé (Tesseract ne les lit pas)')
        J('CPI.ocr.choisirMoteur(null)')

        s.check(not net, 'aucune requête réseau (moteur, modèle et wasm lus dans le fichier)', json.dumps(net[:5]))
        s.check(not [e for e in errs if 'net::ERR_FAILED' not in e and 'diacritics' not in e], 'aucune erreur JS', json.dumps(errs[:5]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_ppocr')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
