// v2.1 — revue complète : générateur de plans aléatoires plausibles (toutes formes, toutes options) et passage de chaque plan
// dans toutes les fonctions de l'application (plan, contrôles, débit, imbrication, 3D, gabarits, exports, auto-contrôle,
// auto-correction, rechargement du formulaire). Rien n'est jugé ici : tout est remonté au test Python.
window.AX = {
  rnd: null,
  seed(s) { let x = s >>> 0 || 1; AX.rnd = () => { x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0; return x / 4294967296 }; },
  pick(a) { return a[Math.floor(AX.rnd() * a.length)] },
  uni(a, b, st) { const v = a + AX.rnd() * (b - a); return st ? Math.round(v / st) * st : Math.round(v) },
  // plages « chantier » (mm sauf mention) — à défaut : bornes LIM
  TYP: {
    '*': { dL: [300, 3000, 10], dl: [200, 2500, 10], dh: [150, 2500, 5], dD: [100, 2500, 10], dDext: [600, 4000, 10], dDint: [0, 1800, 10] },
    voile: { dL: [500, 3500, 10], dl: [150, 500, 10], dh: [600, 3000, 10], dDcuve: [4, 40, 0.5], oEC: [400, 900, 50], oEM: [400, 1000, 50], oGous: [80, 300, 10] },
    special: { dL: [500, 3000, 10], dl: [400, 2500, 10], dh: [200, 1500, 5], dD: [500, 3000, 10], oDint: [150, 1500, 10], oHint: [0, 800, 10], oNiv: [0, 200, 10], oPN: [1, 6, 1], oPD: [80, 400, 10], oPH: [0, 1500, 10], oPR: [0, 1200, 10], oPA: [0, 90, 5], oFSN: [0, 1500, 10] },
    goulotte: { gD: [2, 30, 0.5], gB: [150, 800, 10], gAng: [20, 300, 5], gArc: [1, 20, 0.5], gHE: [100, 900, 10], gHI: [100, 900, 10], gKerf: [3, 5, 1] },
    dalle: { dlD: [2, 16, 0.1], dlL: [2000, 12000, 50], dlW: [2000, 9000, 50], dlE: [300, 800, 25], dlMin: [200, 700, 50], dlK: [3, 5, 1], dlEp: [150, 300, 10], dlRvE: [150, 400, 10], dlRvD: [0, 100, 10] },
    poutre: { ptL: [2000, 12000, 50], ptB: [200, 500, 10], ptH: [300, 900, 10], ptDL: [250, 600, 10], ptDR: [250, 600, 10], ptDc: [6, 30, 0.5], ptO: [-2000, 2000, 50], ptEpl: [15, 27, 1] },
    para: { ppB: [150, 1500, 10], ppH: [150, 1500, 10], ppE: [150, 500, 10], ppA: [0, 60, 1], ppBe: [0, 45, 1] },
  },
  rangeOf(f, id) {
    const T = (AX.TYP[f] || {})[id] || AX.TYP['*'][id]; if (T) return T;
    const L = LIM.find(x => x[0] === id); if (L) return [L[2], Math.min(L[3], L[2] * 50 + 100), 1];
    return null;
  },
  // plan aléatoire d'une forme : sélecteurs puis cases puis nombres (deux passes : les options révèlent des champs)
  make(f, seed) {
    AX.seed(seed); el('iForme').value = f; updF(); el('iCh').value = 'AUDIT'; el('iRef').value = 'A' + seed;
    // Gel des entrées historiques : l'option 10B est couverte par t_geometries_particulieres.
    // Son tirage consommerait une valeur aléatoire et changerait les plans avant/après.
    const box = () => [...el('zDim').querySelectorAll('input,select'), ...el('zOpt').querySelectorAll('input,select')]
      .filter(e => !['ppFeuil','ppFL','ppFH','ppFNiv'].includes(e.id));
    for (let pass = 0; pass < 3; pass++) {
      box().forEach(e => {
        if (e.offsetParent === null && pass > 0) return; // caché
        if (e.tagName === 'SELECT') { if (pass === 0 || AX.rnd() < 0.15) { const o = [...e.options].map(x => x.value); e.value = AX.pick(o); if (e.id === 'dBase') updSpecDims(); if (e.id === 'oConstr') updCP() } }
        else if (e.type === 'checkbox') { if (pass === 0) e.checked = AX.rnd() < 0.5 }
        else if (e.id) { const r = AX.rangeOf(f, e.id); if (r) e.value = String(AX.uni(r[0], r[1], r[2])).replace('.', ',') }
      });
      syncVis();
      if (f === 'dalle' && C('dlPt') && el('zDlBm')) { if (AX.rnd() < 0.5) dlBmAdd(); }
    }
    // lignes dynamiques (poutres de dalle, poteaux de poutre) : valeurs plausibles
    document.querySelectorAll('#zDlBm [data-bm]').forEach((r, i) => { const s = (k, v) => { const e = r.querySelector(`[data-k="${k}"]`); if (e) e.value = v }; s('o', AX.uni(-1500, 1500, 50)); s('b', AX.uni(200, 400, 10)); s('h', AX.uni(300, 600, 10)) });
    const d = coll(); d.date = '2026-10-14'; return d;
  },
  // passage dans toutes les fonctions ; retourne erreurs (exceptions), alertes, anomalies
  run(f, seed) {
    const out = { f, seed, ex: [], W: [], bad: false, nan: [], ac: [], fix: [], t: {} };
    let d; try { d = AX.make(f, seed) } catch (e) { out.ex.push('make: ' + (e.stack || e).toString().slice(0, 300)); return out }
    out.d = JSON.parse(JSON.stringify(d));
    const T = (nm, fn) => { const t0 = performance.now(); try { const r = fn(); out.t[nm] = Math.round(performance.now() - t0); return r } catch (e) { out.ex.push(nm + ': ' + String(e && e.stack || e).slice(0, 400)); return null } };
    const c = T('canon', () => canon(migr(d))); if (!c) return out;
    const g = c.forme === 'voile' ? voileGeo(c) : null;
    out.LE = limErr(c).map(x => x.msg);
    const W = T('checks', () => checks(c, g)) || []; out.W = W; out.bad = badDims(W) || out.LE.length > 0;
    const h = T('gen', () => gen(d)) || '';
    const txt = h.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ');
    ['NaN', 'undefined', 'Infinity', 'null mm', '[object'].forEach(k => { if (txt.includes(k)) out.nan.push(k + ' : …' + txt.slice(Math.max(0, txt.indexOf(k) - 60), txt.indexOf(k) + 30).replace(/\s+/g, ' ') + '…') });
    if (out.bad) return out;
    const R = T('debit', () => debit(c, g)) || [];
    // cohérence du débit : quantités entières > 0, cotes finies ≥ 0, surfaces > 0, bois de longueur > 0, repères uniques
    R.forEach(r => { if (!(Number.isInteger(r.q) && r.q > 0)) out.ex.push(`débit : quantité ${r.q} (${r.n})`); if (![r.a, r.b, r.m2].every(v => v == null || (isFinite(v) && v >= 0))) out.ex.push(`débit : cote / surface illisible (${r.n} ${r.a}×${r.b} ${r.m2})`); if (!(r.m2 > 0)) out.ex.push(`débit : surface nulle (${r.n})`) });
    (R.bois || []).forEach(b => { if (!(Number.isInteger(b.q) && b.q > 0 && b.L > 0 && isFinite(b.L))) out.ex.push(`débit bois : ${b.q} × ${b.L} (${b.n})`) });
    { const tg = R.map(r => r.ftag).concat((R.bois || []).map(b => b.ftag)); if (new Set(tg).size !== tg.length) out.ex.push('débit : repères en double') }
    T('nest', () => cutNest(c, R));
    T('cutPages', () => cpCutPages(c, R));
    T('3d', () => model3(c, R));
    T('gab', () => { const r = gabHtml(c, 'roll'); return r });
    T('dxf', () => { const r = dxfPlanFile(d); if (r.err) throw new Error(r.err); return r });
    T('xlsx', () => debitXlsx([d]));
    T('csv', () => debitCSV([d]));
    T('fix', () => { out.fix = (fixMsgs(d) || []).map(x => x.lb || x.msg || JSON.stringify(x).slice(0, 80)) });
    T('autoctl', () => { out.ac = acPlan(d, false).filter(x => !x[0]).map(x => x[1] + (x[2] ? ' — ' + x[2] : '')) });
    // rechargement du formulaire : coll → setForm → coll identique
    T('reload', () => { const a = JSON.parse(JSON.stringify(d)); delete a.date; setForm(a); const b = coll(); delete b.date; const A = JSON.stringify(a), B = JSON.stringify(b); if (A !== B) { const ka = Object.keys(a).filter(k => JSON.stringify(a[k]) !== JSON.stringify(b[k])); out.ex.push('reload: champs modifiés ' + ka.map(k => k + '=' + JSON.stringify(a[k]) + '→' + JSON.stringify(b[k])).join(' ; ').slice(0, 300)) } });
    return out;
  },
};
