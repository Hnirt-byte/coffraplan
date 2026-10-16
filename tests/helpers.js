// Aides de test injectées dans la page (v18-v19)
window.T = {
  // Construit un plan à partir du formulaire : forme + valeurs de champs (id → valeur / booléen pour les cases)
  mk(forme, ov, extra) {
    el('iForme').value = forme; updF();
    el('iCh').value = 'TEST'; el('iRef').value = 'R01';
    const set = (id, v) => { const e = el(id); if (!e) throw new Error('champ absent ' + id + ' (' + forme + ')'); if (typeof v === 'boolean') e.checked = v; else e.value = v; };
    // les sélecteurs qui reconstruisent le formulaire d'abord
    Object.entries(ov || {}).forEach(([k, v]) => { if (k === 'dBase') { set(k, v); updSpecDims(); } });
    Object.entries(ov || {}).forEach(([k, v]) => { if (k !== 'dBase' && k !== 'oConstr') set(k, v); if (k === 'oConstr') { set(k, v); updCP(); } });
    syncVis();
    if (extra) extra();
    const d = coll(); d.date = '2026-10-10'; return d;
  },
  can(d) { return canon(migr(d)); },
  R(d) { const c = T.can(d), g = c.forme === 'voile' ? voileGeo(c) : null; return debit(c, g); },
  // résumé de débit (non-régression)
  sum(d) {
    const c = T.can(d), g = c.forme === 'voile' ? voileGeo(c) : null, W = checks(c, g), R = badDims(W) ? [] : debit(c, g);
    const r = x => Math.round(x * 10) / 10;
    return { W: W.map(x => x[0] + ':' + x[1]), cp: R.map(x => [x.ftag, x.n, x.q, r(x.a || 0), r(x.b || 0), r(x.m2 * 1000) / 1000, x.txt || '']),
      bois: (R.bois || []).map(b => [b.ftag, b.n, b.q, r(b.L)]) };
  },
};
// Scénarios : toutes les formes et variantes principales
window.SCN = [
  ['carre', 'carre', {}], ['carre_fond', 'carre_fond', {}], ['rect', 'rect', { dL: 1200, dl: 800, dh: 300 }],
  ['rect_fond_gs', 'rect_fond', { dL: 1500, dl: 1100, dh: 600, oGs: true, oRenX: true, oRenXs: 'ch' }],
  ['puisard', 'carre_fond', { dL: 800, dh: 900, oFeuil: true }], // v19 : ex-forme « puisard » (supprimée) = carré avec fond
  ['massif', 'massif', { dL: 1000, dl: 800, dh: 600, oRen: true, oFondMassif: true }],
  ['massif_sans', 'massif', { oRen: false }],
  ['rect_long', 'rect_fond', { dL: 3200, dl: 1600, dh: 1400, oGs: true, oRenX: true, oRenXs: 'ch' }],
  ['massif_long', 'massif', { dL: 3000, dl: 1200, dh: 1400, oRen: true, oFondMassif: true }],
  ['special_long', 'special', { dL: 3000, dl: 1400, dh: 1300, oFondSup: true, oGs: true }],
  ['circ', 'circ', {}],
  ['circ_fond', 'circ_fond', { oRenX: true }], ['circ_sf', 'circ_sf', { dDint: 0, oRenX: true }],
  ['voile_man', 'voile', {}], ['voile_man_rad', 'voile', { dJoues: 'rad' }],
  ['voile_man_L3000', 'voile', { dL: 3000, dDcuve: 12, dh: 2500 }], ['voile_man_L3000_rad', 'voile', { dL: 3000, dDcuve: 12, dh: 2500, dJoues: 'rad' }],
  ['voile_man_bois', 'voile', { dL: 1500, oCS: 't50', oMS: 'ch' }],
  ['voile_cais', 'voile', { oConstr: 'caisson', oRenV: true }], ['voile_cais_ferme', 'voile', { oConstr: 'caisson', oRenV: true, oFerme: true }],
  ['voile_cais_L3000', 'voile', { oConstr: 'caisson', oRenV: true, oFerme: true, dL: 3000, dl: 400, dh: 1500 }],
  ['voile_cais_rad', 'voile', { oConstr: 'caisson', oRenV: true, dJoues: 'rad', dL: 2000, dl: 300 }],
  ['special_rect', 'special', { oPot: true, oFondSup: true, oGs: true }],
  ['special_circ', 'special', { dBase: 'circ', oConc: true, oFondSup: true }],
  ['goulotte', 'goulotte', {}], ['goulotte_angle', 'goulotte', { gEt: 'angle', gAng: 120, gJE: true }],
  ['dalle_circ', 'dalle', {}], ['dalle_circ_pt', 'dalle', { dlPt: true }], ['dalle_rect', 'dalle', { dlF: 'rect' }],
  ['poutre', 'poutre', {}], ['poutre_po', 'poutre', { ptEL: 'po', ptER: 'vc', ptL: 9000, ptH: 700 }, () => { poAdd(el('zPtPo')); }],
  ['dalle_pt_lhs', 'dalle', { dlPt: true, bmLhs: true, bmHpt: 200 }, () => { const c = el('zDlBm').querySelector('[data-k="h"]'); c.value = 500; }],
  ['poutre_lhs', 'poutre', { ptDal: true, bmLhs: true, bmHpt: 175, ptH: 600 }],
  ['dalle_rive', 'dalle', { dlRv: true, dlEp: 220, dlRvE: 250 }],
  ['para', 'para', {}], ['para_long', 'para', { ppB: 600, ppH: 500, ppE: 3000, ppA: 40 }],
];
