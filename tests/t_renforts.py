"""Point 5 — chaque renfort du débit est dessiné en 3D (même nombre) et aucun renfort 3D n'est absent du débit (orphelin)."""
from lib import run

JS = r'''(k)=>{
  const out=[],ok=(c,m)=>out.push([!!c,k+' : '+m]);const S=SCN.find(s=>s[0]===k),d=T.can(T.mk(S[1],S[2],S[3])),g=d.forme==='voile'?voileGeo(d):null,R=debit(d,g);
  const sc=model3(d,R),SO=sc.solids;
  // correspondance pièce 3D ↔ ligne de débit (CP ou bois)
  const MAP=[[/^lisse$/,/^Lisses 50×50/],[/^feuillure$/,/^Tasseaux de feuillure/],[/^croix$/,/^(Cloisons CP|Tasseau 50|Chevron 63|Bois de coffrage)/],
    [/^gousset$/,/^Goussets/],[/^montant$/,/^Montants/],[/^cerce$/,/^Cerces/],[/^traverse de cerce/,/^Traverses de cerce/],
    [/^raidisseur$/,/^Raidisseurs/],[/^lisse basse$/,/^Lisses basses/],[/^lisse haute$/,/^Lisses hautes/],[/^cadre d'about$/,/^Cadres d'about/],[/^lisse de raccord$/,/^Lisses de raccord/],
    [/^traverse$/,/^Traverses (horiz|vert)/],[/^cadre de joint$/,/^Cadres de joint/],[/^équerre de rive$/,/^Équerres de rive/],
    [/^couvre-joint$/,/^Couvre-joints/],[/^lisse de joint$/,/^Lisses de joint/],[/^tasseau de joint$/,/^Tasseaux de joint/]];
  const NONDEBIT=/^(poutrelle|tube carton|tube PVC)$/; // non fournis (poutrelles) ou réservations (tubes)
  const isRenf=o=>o.col===C3.bois||o.col===C3.gs||o.col===C3.cl;
  // nombre de pièces 3D (segments d'une même paroi cintrée regroupés ; cerces évidées du caisson = 1 pièce par niveau)
  const count3=re=>{const seen=new Set();let n=0;SO.forEach(o=>{if(!re.test(o.nm))return;const key=o.rg?o.rg:(o.nm==='cerce'&&d.constr==='caisson')?'z'+Math.round(bb3(o)[2]):o;if(seen.has(key))return;seen.add(key);n++});return n};
  const lines=R.concat(R.bois||[]),countD=re=>lines.filter(l=>re.test(l.n)).reduce((a,l)=>a+l.q,0);
  MAP.forEach(([a,b])=>{const n3=count3(a),nD=countD(b);if(n3||nD)ok(n3===nD,`${String(b).slice(2,-1)} : 3D ${n3} = débit ${nD}`)});
  // orphelins : renfort dessiné sans ligne de débit
  const orph=[...new Set(SO.filter(o=>isRenf(o)&&!NONDEBIT.test(o.nm)&&!MAP.some(([a])=>a.test(o.nm))).map(o=>o.nm))];
  ok(!orph.length,`aucun renfort 3D orphelin (${orph.join(', ')})`);
  // manquants : ligne bois du débit sans pièce 3D
  const miss=(R.bois||[]).filter(l=>!MAP.some(([a,b])=>b.test(l.n)&&count3(a)>0)).map(l=>l.n);
  ok(!miss.length,`aucun renfort du débit absent de la 3D (${miss.join(' ; ')})`);
  // longueurs : chaque renfort de joint du débit correspond à une pièce 3D de même longueur
  if(R.jg&&R.jg.length){const L3=R.jg.map(b=>Math.round(b.L)).sort((a,b)=>a-b),LD=(R.bois||[]).filter(l=>/joint/.test(l.n)).flatMap(l=>Array(l.q).fill(l.L)).sort((a,b)=>a-b);
    ok(JSON.stringify(L3)===JSON.stringify(LD),`renforts de joint : longueurs débit = 3D (${LD.length} pièces)`)}
  // côté des renforts de joint : dans le vide d'une réservation, à l'extérieur d'un coffrage de béton
  if(R.jg&&R.jg.length){const ep=d.ep||0,C=b=>b.geo.t==='box'?b.geo.c:[b.geo.cx+Math.cos((b.geo.a1+b.geo.a2)/2)*(b.geo.r1+b.geo.r2)/2,b.geo.cy+Math.sin((b.geo.a1+b.geo.a2)/2)*(b.geo.r1+b.geo.r2)/2,b.geo.z0];let side=null;
    if(RECT.includes(d.forme)&&d.forme!=='massif')side=c=>c[0]>ep&&c[0]<d.L-ep&&c[1]>ep&&c[1]<d.l-ep;
    else if(d.forme==='massif')side=c=>c[0]<0||c[0]>d.L+2*ep||c[1]<0||c[1]>d.l+2*ep||c[2]<0;
    else if(d.forme==='special'&&d.base!=='circ')side=c=>Math.abs(c[0])<d.L/2-ep&&Math.abs(c[1])<d.l/2-ep;
    else if(d.forme==='special')side=c=>Math.hypot(c[0],c[1])<d.D/2-ep;
    else if(d.forme==='circ_fond'||d.forme==='circ_sf')side=c=>{const r=Math.hypot(c[0],c[1]);return r<d.Dext/2-ep&&r>(d.Dint>0?d.Dint/2+ep:0)};
    else if(d.forme==='voile'&&g.ok){const Rm=(g.Ri+g.Re)/2;side=c=>{const r=Math.hypot(c[0],c[1]+Rm);return r>g.Ri+ep-0.5&&r<g.Re-ep+0.5}}
    else if(d.forme==='dalle'&&d.dlRv){const Rv=riveGeo(d);if(Rv.t==='circ')side=c=>Math.hypot(c[0],c[1])>Rv.Rr+Rv.ep}
    if(side){const bad=R.jg.filter(b=>!side(C(b)));ok(!bad.length,`renforts de joint du bon côté (${bad.length} mal placés : ${bad.slice(0,3).map(b=>b.kind+b.tag).join(', ')})`)}}
  // tags : le repère porté en 3D existe au débit
  const tags=new Set(lines.map(l=>l.tag)),bad=[...new Set(SO.filter(o=>o.tag&&/^[JFSB]\d+[a-z]?$/.test(o.tag)&&!tags.has(o.tag.replace(/[a-z]$/,''))).map(o=>o.tag))];
  ok(!bad.length,`repères 3D présents au débit (${bad.join(', ')})`);
  return out}'''


def t(s, pg):
    for k in pg.evaluate('SCN.map(s=>s[0])'):
        for okk, m in pg.evaluate(JS, k):
            s.check(okk, m)


if __name__ == '__main__':
    import sys
    sys.exit(0 if run('t_renforts', t) else 1)
