// v19 — extraction BRUTE des dessins (feuilles CP À DÉCOUPER, gabarits 1:1, pages d'impression) pour une vérification
// géométrique indépendante côté Python (shapely). Aucune valeur calculée par l'appli n'est réutilisée pour juger :
// seules les entrées du calepinage (cellules, placement des pièces sur les panneaux) sont lues, tout le reste est relu
// dans les SVG tels qu'ils sont dessinés / imprimés.
window.GX = {
  els(svg) {
    const doc = new DOMParser().parseFromString(svg.startsWith('<svg') ? svg : `<svg xmlns="http://www.w3.org/2000/svg">${svg}</svg>`, 'image/svg+xml');
    const err = doc.querySelector('parsererror'); if (err) return { err: err.textContent.slice(0, 200) };
    const A = (e, k) => e.getAttribute(k), N = (e, k) => +e.getAttribute(k);
    const st = e => ({ fill: A(e, 'fill'), stroke: A(e, 'stroke'), sw: N(e, 'stroke-width'), cls: A(e, 'class') || '', da: A(e, 'stroke-dasharray') || '' });
    const o = { rect: [], path: [], circle: [], line: [], text: [], polyline: [] };
    doc.querySelectorAll('rect').forEach(e => o.rect.push(Object.assign(st(e), { x: N(e, 'x'), y: N(e, 'y'), w: N(e, 'width'), h: N(e, 'height') })));
    doc.querySelectorAll('path').forEach(e => { if (e.closest('marker') || e.closest('pattern')) return; o.path.push(Object.assign(st(e), { d: A(e, 'd') })) });
    doc.querySelectorAll('circle').forEach(e => o.circle.push(Object.assign(st(e), { x: N(e, 'cx'), y: N(e, 'cy'), r: N(e, 'r'), data: Object.assign({}, e.dataset) })));
    doc.querySelectorAll('line').forEach(e => { if (e.closest('pattern')) return; o.line.push(Object.assign(st(e), { x1: N(e, 'x1'), y1: N(e, 'y1'), x2: N(e, 'x2'), y2: N(e, 'y2'), data: Object.assign({}, e.dataset) })) });
    doc.querySelectorAll('polyline').forEach(e => o.polyline.push(Object.assign(st(e), { pts: A(e, 'points').trim().split(/\s+/).map(s => s.split(',').map(Number)) })));
    doc.querySelectorAll('text').forEach(e => o.text.push({ x: N(e, 'x'), y: N(e, 'y'), an: A(e, 'text-anchor') || 'start', fill: A(e, 'fill'), fs: N(e, 'font-size'), fw: A(e, 'font-weight'), t: e.textContent, tr: A(e, 'transform') || '' }));
    return o;
  },
  // cfg : {ov: champs du formulaire, set: propriétés imposées au plan après saisie, gm: band|full|arc, mode: roll|A3|A4, roll: 914...}
  run(cfg) {
    const t0 = performance.now();
    const d = T.can(T.mk('dalle', cfg.ov || {})); Object.assign(d, cfg.set || {}); GX.last = d;
    el('iGabDal').value = cfg.gm || 'band'; el('iRoll').value = String(cfg.roll || 914);
    const W = checks(d, null), bad = badDims(W);
    const G = dalGeo(d); if (!G.ok) return { ok: false, W: W.map(x => x.join(':')), bad };
    const sh = G.shL;
    const items = G.sheets.map(s => s.items.map(it => ({ id: it.pc.id, rot: !!it.rot, ox: it.ox, oy: it.oy, cell: [it.pc.cx1, it.pc.cy1, it.pc.cx2, it.pc.cy2] })));
    const all = G.pcs.map(p => ({ id: p.id, full: !!p.full, cell: [p.cx1, p.cy1, p.cx2, p.cy2] }));
    const cut = dalCutPages(d, G).map(s => GX.els(s));
    const plan = GX.els(dalPlanSvg(d, G, 1000, 700, true));
    const GP = gabPieces(d, cfg.mode || 'roll');
    const gab = GP.msg ? { msg: GP.msg } : { title: GP.title, fb: GP.fb || 0, pieces: GP.pieces.map(pc => ({ id: pc.id, title: pc.title, kind: pc.kind || '', note: pc.note || '', w: pc.w, h: pc.h, sheet: pc.sheet, el: GX.els(pc.svg) })) };
    let pages = null;
    const H = gabHtml(d, cfg.mode || 'roll');
    if (H.html) {
      const dc = new DOMParser().parseFromString(H.html, 'text/html');
      pages = [...dc.querySelectorAll('.pg svg')].map(s => ({ w: s.getAttribute('width'), h: s.getAttribute('height'), vb: s.getAttribute('viewBox'), piece: s.dataset.piece, rot: s.dataset.rot,
        tr: (s.querySelector(':scope > g') || { getAttribute: () => '' }).getAttribute('transform'), div: (s.parentNode.getAttribute('style') || '') }));
      pages = { list: pages, big: (H.html.match(/pièce\(s\) trop grande\(s\) pour une page[^:]*:([^<]*)</) || [, ''])[1].trim() };
    }
    return { ok: true, W: W.map(x => x.join(':')), bad, P: G.P, Q: G.Q, kerf: G.kerf, e: G.e, rot: !!G.rot, sh: { t: sh.t, R: sh.R || 0, A: sh.A, B: sh.B },
      zones: G.zones.map(z => [z.Z1, z.Z2]), deb: debit(d, null).filter(x => /^Planches/.test(x.n)).map(x => ({ n: x.n, q: x.q, m2: x.m2, txt: x.txt || '' })), items, all, nE: G.nE, nD: G.nD, cut, plan, gab, pages, ms: Math.round(performance.now() - t0) };
  },
};
