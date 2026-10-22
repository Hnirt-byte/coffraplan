"""Phase 9A : plans ENTIÈREMENT FICTIFS (repères, cotes, désignations inventés) pour tests/t_support.py.
PDF écrits octet par octet (déterministes), échelle 1:50 :
  - SUPPORT_PLAN.pdf : voile droit (épaisseur 200) avec R01 500×500 et R04 Ø200 (traversée dessinée en plan) ; voile circulaire
    (rayon intérieur 6000, épaisseur 250, faces en courbes de Bézier) avec R02 1200×1000 et R03 « 1000x500 » (largeur réelle 500
    suivant la paroi) ; nomenclature (texte extractible) ; cartouche ; titre d'échelle.
  - SUPPORT_CHARGE.pdf : même voile droit et R01, précédés de 410 000 petits traits (hachures) : plafond de lecture atteint.
DXF (ezdxf) : voile circulaire en ARC, en polylignes à bulge et dans un bloc inséré en miroir, voile droit en LINE.
fichiers(dossier) → {nom: (chemin, infos)}."""
import math, os, zlib
import pdf_fictifs as PF

ECH = 50
K = ECH * 25.4 / 72
pt = lambda mm: mm / K
RI, T_C, T_D = 6000, 250, 200


def bez(c, r, a0, a1):
    """Opérateurs PDF d'un arc en pièces de Bézier (≤ 90°), à la suite d'un « m »."""
    n = max(1, math.ceil((a1 - a0) / (math.pi / 2) - 1e-9)); d = (a1 - a0) / n; q = 4 / 3 * math.tan(d / 4); o = []
    P = lambda t: (c[0] + r * math.cos(t), c[1] + r * math.sin(t))
    for i in range(n):
        a, b = a0 + i * d, a0 + (i + 1) * d; p0, p3 = P(a), P(b)
        o.append('%.4f %.4f %.4f %.4f %.4f %.4f c' % (p0[0] - q * r * math.sin(a), p0[1] + q * r * math.cos(a), p3[0] + q * r * math.sin(b), p3[1] - q * r * math.cos(b), p3[0], p3[1]))
    return '%.4f %.4f m ' % P(a0) + ' '.join(o)


def arc(p, c, r, a0, a1, ep=0.8):
    p.ops.append(('%g w ' % ep + bez(c, r, a0, a1) + ' S').encode('latin-1'))


def poly(p, P, ep=0.5):
    p.ops.append(('%g w ' % ep + '%.4f %.4f m ' % P[0] + ' '.join('%.4f %.4f l' % q for q in P[1:]) + ' h S').encode('latin-1'))


def voile_droit(p, x0, x1, y, trous):
    """Faces y ± t/2 de x0 à x1, interrompues sur les ouvertures [(cx, largeur mm)] ; contour de chaque ouverture d'une face à l'autre."""
    t = pt(T_D); xs = sorted(trous)
    for f in (-t / 2, t / 2):
        a = x0
        for cx, w in xs:
            p.trait(a, y + f, cx - pt(w) / 2, y + f, 0.8); a = cx + pt(w) / 2
        p.trait(a, y + f, x1, y + f, 0.8)
    for cx, w in xs:
        p.rect(cx - pt(w) / 2, y - t / 2, pt(w), t, 0.5)


def voile_circ(p, c, trous, a0=math.radians(48), a1=math.radians(132)):
    """Faces de rayons RI et RI + t, interrompues sur les ouvertures [(angle°, largeur mm)] ; ouvertures à joues parallèles (corde)."""
    ri, re = pt(RI), pt(RI + T_C); out = []
    for r in (ri, re):
        I = []
        for ang, w in sorted(trous):
            g = math.asin(pt(w) / 2 / r); I.append((math.radians(ang) - g, math.radians(ang) + g))
        a = a0
        for u, v in I:
            arc(p, c, r, a, u); a = v
        arc(p, c, r, a, a1)
    for ang, w in trous:
        f = math.radians(ang); u, n = (-math.sin(f), math.cos(f)), (math.cos(f), math.sin(f)); hw = pt(w) / 2
        yi, ye = math.sqrt(ri * ri - hw * hw), math.sqrt(re * re - hw * hw)
        P = [(c[0] + s * hw * u[0] + d * n[0], c[1] + s * hw * u[1] + d * n[1]) for s, d in ((-1, yi), (1, yi), (1, ye), (-1, ye))]
        poly(p, P); out.append(P)
    return out


NOMENCL = [('R01', 'Trémie gaine voile droit', '500x500', '1'), ('R02', 'Trémie voile cuve ép. 250 mm', '1200x1000', '1'),
           ('R03', 'Baie technique cuve', '1000x500', '1'), ('R04', 'Fourreau EU', 'Ø200', '1')]
COLS = [('Repère', 34), ('Désignation', 140), ('Ouverture\n(mm)', 64), ('Quantité', 44)]


def plan(p, charge=False):
    p.rect(20, 20, 1150, 802)
    p.texte(40, 800, 'PLAN FICTIF DES RÉSERVATIONS — VUE EN PLAN — ÉCHELLE 1/50', 10)
    voile_droit(p, 60, 560, 620, [(200, 500), (400, 200)])
    for x, w, r in ((200, 500, 'R01'), (400, 200, 'R04')):
        p.texte(x - 6, 620 + pt(T_D) / 2 + 1, r, 7)
    if not charge:
        c = (850, 230)
        Ps = voile_circ(p, c, [(90, 1200), (68, 500)])
        for P, r in zip(Ps, ('R02', 'R03')):
            q = max(P, key=lambda z: z[1]); p.texte(q[0] + 3, q[1] + 3, r, 7)
        PF.tableau(p, 760, 780, COLS, [list(x) for x in NOMENCL], titre='NOMENCLATURE DES RÉSERVATIONS')
    # cartouche (cadre de coin et textes) : jamais un support
    p.rect(980, 30, 180, 90, 0.8)
    for i, s in enumerate(['CHANTIER FICTIF', 'PLAN GUIDE', 'Ech. 1/50', 'Indice A']):
        p.texte(990, 100 - 18 * i, s, 7)


def ecrire_z(chemin, pages, titre):
    """Comme pdf_fictifs.ecrire, flux compressés (plan chargé)."""
    obj = []; add = lambda b: obj.append(b) or len(obj)
    font = add(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    kids = []; root_pages = len(obj) + 2 * len(pages) + 1
    for p in pages:
        z = zlib.compress(b'\n'.join(p.ops), 6)
        c = add(b'<< /Length %d /Filter /FlateDecode >>\nstream\n' % len(z) + z + b'\nendstream')
        kids.append(add(b'<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %g %g] /Rotate 0 /Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>' % (root_pages, p.w, p.h, font, c)))
    assert add(b'<< /Type /Pages /Kids [' + b' '.join(b'%d 0 R' % k for k in kids) + b'] /Count %d >>' % len(kids)) == root_pages
    cat = add(b'<< /Type /Catalog /Pages %d 0 R >>' % root_pages); info = add(b'<< /Title (' + titre.encode('cp1252') + b') >>')
    out, off = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'), []
    for i, b in enumerate(obj, 1):
        off.append(len(out)); out += b'%d 0 obj\n' % i + b + b'\nendobj\n'
    x = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(obj) + 1) + b''.join(b'%010d 00000 n \n' % o for o in off)
    out += b'trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(obj) + 1, cat, info, x)
    with open(chemin, 'wb') as f:
        f.write(out)
    return chemin


def dxf(chemin, variante):
    """Voile circulaire (centre 0,0 ; rayons 6000 / 6250 mm) : 'arc' (ARC), 'bulge' (LWPOLYLINE à arcs), 'bloc' (ARC dans un bloc
    inséré en miroir et tourné) ; ouverture R02 1200 de large (corde) à 90° ; voile droit en LINE (épaisseur 200) avec R01 500."""
    import ezdxf
    d = ezdxf.new('R2010'); d.units = 4; m = d.modelspace(); ri, re = RI, RI + T_C
    def faces(sp, ins=lambda q: q):
        for r in (ri, re):
            g = math.degrees(math.asin(600 / r))
            for a0, a1 in ((48, 90 - g), (90 + g, 132)):
                if variante == 'bulge':
                    P = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (a0, a1)]
                    sp.add_lwpolyline([(P[0][0], P[0][1], 0, 0, math.tan(math.radians(a1 - a0) / 4)), (P[1][0], P[1][1], 0, 0, 0)], format='xyseb')
                else:
                    sp.add_arc((0, 0), r, a0, a1)
        yi, ye = math.sqrt(ri * ri - 600 ** 2), math.sqrt(re * re - 600 ** 2)
        sp.add_lwpolyline([(-600, yi), (600, yi), (600, ye), (-600, ye)], close=True)
    if variante == 'bloc':
        b = d.blocks.new('CUVE'); faces(b)
        m.add_blockref('CUVE', (20000, 5000), dxfattribs={'xscale': -1, 'rotation': 30})
    else:
        faces(m)
    # voile droit : faces y = 15000 ± 100, ouverture R01 de 500 en x = 0
    for y in (14900, 15100):
        m.add_line((-3000, y), (-250, y)); m.add_line((250, y), (3000, y))
    m.add_lwpolyline([(-250, 14900), (250, 14900), (250, 15100), (-250, 15100)], close=True)
    d.saveas(chemin)
    return chemin


def fichiers(d):
    os.makedirs(d, exist_ok=True); F = {}
    p = PF.Page(1190, 842); plan(p)
    F['SUPPORT_PLAN.pdf'] = (PF.ecrire(os.path.join(d, 'SUPPORT_PLAN.pdf'), [p], 'Support fictif'), {'K': K})
    q = PF.Page(1190, 842)
    q.ops.append(('0.1 w ' + ' '.join('%d %d m %d %d l' % (30 + (i % 600), 60 + (i // 600) % 300, 31 + (i % 600), 61 + (i // 600) % 300) for i in range(410000)) + ' S').encode('latin-1'))
    plan(q, charge=True)
    F['SUPPORT_CHARGE.pdf'] = (ecrire_z(os.path.join(d, 'SUPPORT_CHARGE.pdf'), [q], 'Support fictif charge'), {'K': K})
    for v in ('arc', 'bulge', 'bloc'):
        F['SUPPORT_%s.dxf' % v.upper()] = (dxf(os.path.join(d, 'SUPPORT_%s.dxf' % v.upper()), v), {})
    return F


if __name__ == '__main__':
    import sys
    for n, (c, _) in fichiers(sys.argv[1] if len(sys.argv) > 1 else 'support_fictif').items():
        print(c, os.path.getsize(c))
