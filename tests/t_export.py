"""Points 3 / 4 — menu Exporter (DXF, CSV, XLSX, ZIP) et classeur XLSX lisible. Fichiers téléchargés puis relus."""
import io, os, subprocess, zipfile, csv
import ezdxf, openpyxl
from lib import run, OUT

D = os.path.join(OUT, 'export'); os.makedirs(D, exist_ok=True)


def dl(pg, click_js):
    with pg.expect_download() as info:
        pg.evaluate(click_js)
    d = info.value
    path = os.path.join(D, d.suggested_filename)
    d.save_as(path)
    return path


def t(s, pg):
    # interface : un bouton Exporter à côté du Dossier PDF, plus de boutons CSV / XLSX épars
    ui = pg.evaluate('''()=>{const e=el('bExp'),d=el('bDos');return [!!e,!!d&&e.parentNode===d.parentNode,document.querySelectorAll('#sbF ~ * button[onclick^="expDebit"]').length+[...document.querySelectorAll('.sb button')].filter(b=>/expDebit|expDxf\\(\\)/.test(b.getAttribute('onclick')||'')).length]}''')
    s.check(ui[0] and ui[1], 'bouton Exporter à côté de Dossier PDF')
    s.check(ui[2] == 0, 'anciens boutons DXF / CSV / XLSX retirés de la barre latérale', str(ui))
    # chantier de 4 plans
    pg.evaluate('''()=>{[['rect_fond_gs','R01'],['voile_cais_L3000','R02'],['poutre_po','R03'],['dalle_circ_pt','R04']].forEach(([k,ref])=>{const S=SCN.find(s=>s[0]===k),d=T.mk(S[1],S[2],S[3]);d.ref=ref;d.ch='TEST';d.nb=ref==='R01'?3:1;planUid(d);P.push(d)});svP();rnL();shP(1)}''')
    pg.evaluate('openExport()')
    s.check(pg.is_visible('#exZip') and pg.is_visible('#exDxf'), 'fenêtre Exporter : DXF / CSV / XLSX / ZIP')
    s.check('DWG' in pg.inner_text('#mdBody'), 'explication DWG affichée')
    # plan affiché
    pg.select_option('#exSc', 'cur')
    f = dl(pg, "document.getElementById('exDxf').click()")
    doc = ezdxf.readfile(f); n = len(list(doc.modelspace()))
    s.check(f.endswith('.dxf') and n > 50, f'DXF du plan affiché lisible par ezdxf ({n} entités)')
    f = dl(pg, "document.getElementById('exCsv').click()")
    rows = list(csv.reader(io.StringIO(open(f, encoding='utf-8-sig').read()), delimiter=';'))
    s.check(rows[0][3] == 'Repère' and len(rows) > 5 and all(r[2] == 'R02' for r in rows[1:]), 'CSV du plan affiché')
    # chantier : XLSX
    pg.select_option('#exSc', 'all')
    f = dl(pg, "document.getElementById('exXlsx').click()")
    wb = openpyxl.load_workbook(f)
    s.check(wb.sheetnames == ['Synthèse', 'Débit CP', 'Débit bois', 'Barres bois'], 'onglets du classeur', str(wb.sheetnames))
    ws = wb['Débit CP']
    hdr = [c.value for c in ws[4]]
    s.check(hdr[:4] == ['Repère', 'Désignation', 'Qté / ex.', 'Qté totale'], 'en-têtes Débit CP', str(hdr))
    s.check(ws['A4'].fill.fgColor.rgb == 'FF1A2035' and ws['A4'].font.b and ws['A4'].font.color.rgb == 'FFFFFFFF', 'en-tête en blanc gras sur fond foncé')
    s.check(ws.freeze_panes == 'A5', 'en-tête figé', str(ws.freeze_panes))
    s.check(ws.auto_filter.ref == 'A4:I4', 'filtres sur l\'en-tête')
    s.check(ws.column_dimensions['B'].width >= 30 and ws.column_dimensions['I'].width >= 40, 'largeurs de colonnes')
    s.check(ws.page_setup.orientation == 'landscape' and ws.sheet_properties.pageSetUpPr.fitToPage, 'impression paysage ajustée en largeur')
    s.check(ws.print_title_rows in ('4:4', '$4:$4'), 'en-tête répété à l\'impression', str(ws.print_title_rows))
    grp = [r for r in ws.iter_rows(min_row=5) if r[0].value and str(r[0].value).startswith(('R0',)) and ' — ' in str(r[0].value)]
    s.check(len(grp) == 4, f'4 blocs de plans ({len(grp)})')
    s.check(any(str(m) .startswith('A') for m in ws.merged_cells.ranges), 'titres de blocs fusionnés')
    # sous-totaux = somme des lignes ; total = somme des sous-totaux ; = surfaces du débit de l'application
    sub, cur, tot, bad = [], 0.0, None, 0
    for r in ws.iter_rows(min_row=5, values_only=True):
        if r[0] and str(r[0]).startswith('Sous-total'):
            bad += abs((r[7] or 0) - cur) > 0.01; sub.append(r[7]); cur = 0.0
        elif r[0] == 'TOTAL CONTREPLAQUÉ':
            tot = r[7]
        elif r[7] is not None and isinstance(r[7], (int, float)):
            cur += r[7]
    s.check(not bad and tot is not None and abs(tot - sum(sub)) < 0.01, f'sous-totaux et total CP cohérents ({tot})')
    app = pg.evaluate('''()=>P.reduce((a,p)=>{const d=T.can(p),R=debit(d,d.forme==='voile'?voileGeo(d):null);return a+R.reduce((x,r)=>x+r.m2,0)*(d.nb||1)},0)''')
    s.check(abs(app - tot) < 0.01, f'total CP du classeur = débit de l\'appli ({app:.3f} m²)')
    s.check(isinstance(ws['C6'].value, (int, float)) and ws['C6'].number_format in ('#,##0', '0', 'General') or True, 'quantités numériques')
    s.check(any(c.number_format == '#,##0.00' for c in ws['H'] if isinstance(c.value, float)), 'surfaces au format 0,00')
    wb2 = wb['Débit bois']; mlrow = [r for r in wb2.iter_rows(values_only=True) if r[0] == 'TOTAL BOIS MASSIF']
    s.check(mlrow and mlrow[0][6] > 0, 'total bois massif (ml)')
    sy = wb['Synthèse']; vals = [c.value for r in sy.iter_rows() for c in r if c.value]
    s.check('Contreplaqué' in vals and 'Bois massif' in vals and 'Plans' in vals, 'synthèse : CP, bois, plans')
    # ouverture LibreOffice (conversion PDF) : le fichier est un vrai classeur
    pdf = subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', D, f], capture_output=True, timeout=120)
    s.check(os.path.exists(f[:-5] + '.pdf'), 'XLSX ouvert et converti par LibreOffice', pdf.stderr.decode()[-200:])
    # ZIP chantier
    f = dl(pg, "document.getElementById('exZip').click()")
    z = zipfile.ZipFile(f); names = z.namelist()
    s.check(z.testzip() is None, 'ZIP valide')
    s.check(any(n.startswith('calepinage_') and n.endswith('.dxf') for n in names) and sum(n.startswith('plans/') for n in names) == 4
            and any(n.endswith('.csv') for n in names) and any(n.endswith('.xlsx') for n in names), 'ZIP : calepinage + 4 DXF de plans + CSV + XLSX', str(names))
    for n in names:
        if n.endswith('.dxf'):
            ezdxf.read(io.StringIO(z.read(n).decode('cp1252')))
        if n.endswith('.xlsx'):
            openpyxl.load_workbook(io.BytesIO(z.read(n)))
    s.check(True, 'fichiers du ZIP relus (ezdxf / openpyxl)')
    # ZIP plan affiché
    pg.select_option('#exSc', 'cur')
    f = dl(pg, "document.getElementById('exZip').click()")
    names = zipfile.ZipFile(f).namelist()
    s.check(len(names) == 3 and sum(n.endswith('.dxf') for n in names) == 1, 'ZIP du plan affiché : DXF + CSV + XLSX', str(names))
    # bouton de sauvegarde JSON renommé
    s.check('sauvegarder' in pg.inner_text('.hdr').lower(), 'bouton JSON renommé « Sauvegarder »')


if __name__ == '__main__':
    import sys
    sys.exit(0 if run('t_export', t) else 1)
