"""Point 2 / 5 — modèle 3D : pièces dans le volume, aucune interpénétration, vue éclatée complète."""
from lib import run

JS = r'''(k)=>{
  const out=[],ok=(c,m)=>out.push([!!c,k+' : '+m]);const S=SCN.find(s=>s[0]===k),d=T.can(T.mk(S[1],S[2],S[3])),g=d.forme==='voile'?voileGeo(d):null,R=debit(d,g);
  const sc=model3(d,R),SO=sc.solids.filter(o=>o.role!=='ctx');if(!ok(SO.length,'modèle 3D non vide'))return out;
  // 1) aucune interpénétration entre pièces (assemblé)
  const ov=overlap3(sc,0.5,6);ok(!ov.length,`aucune interpénétration (${ov.slice(0,3).map(x=>x.a+' / '+x.b+' @'+x.p.join(',')).join(' ; ')})`);
  // 2) voile : toutes les pièces dans l'épaisseur du voile (Ri ≤ r ≤ Re) et dans la hauteur
  if(d.forme==='voile'&&g.ok){const Rm=(g.Ri+g.Re)/2;let bad=[];SO.forEach(o=>o.F.forEach(f=>f.forEach(p=>{const r=Math.hypot(p[0],p[1]+Rm);
      if(r<g.Ri-0.6||r>g.Re+0.6||p[2]<-0.6||p[2]>d.h+0.6)bad.push(o.nm+' r='+nf(r-g.Ri,1)+'/'+nf(g.l))})));
    bad=[...new Set(bad)];ok(!bad.length,`pièces dans l'épaisseur du voile (${bad.slice(0,4).join(' ; ')})`)}
  // 3) vue éclatée : toutes les pièces non posées (hors fond / base) bougent, et rien ne s'interpénètre
  const E=explode3(sc,1),mv=(a,b)=>{const A=bb3(a),B=bb3(b);return Math.max(...[0,1,2].map(i=>Math.abs((A[i]+A[i+3])/2-(B[i]+B[i+3])/2)))};
  const ES=E.solids.filter(o=>o.role!=='ctx'),moved={},still={};
  if(sc.exMode!=='hide'){SO.forEach((o,i)=>{const e=ES[i];if(!e)return;const m=mv(o,e)>20;(m?moved:still)[o.role+':'+o.nm]=1});
    const st=Object.keys(still).filter(x=>!/^base:/.test(x));ok(!st.length,`éclaté : toutes les pièces non posées sont écartées (immobiles : ${st.join(', ')})`);
    const ov2=overlap3(E,0.5,5);ok(!ov2.length,`éclaté sans interpénétration (${ov2.slice(0,3).map(x=>x.a+' / '+x.b).join(' ; ')})`)}
  else{const st=SO.filter((o,i)=>o.role!=='top'&&o.role!=='base'&&ES[i]&&mv(o,ES[i])<20).map(o=>o.nm);ok(!st.length,`éclaté (platelage masqué) : coffrages écartés (immobiles : ${[...new Set(st)].join(', ')})`)}
  return out}'''


def t(s, pg):
    keys = pg.evaluate('SCN.map(s=>s[0])')
    for k in keys:
        if k == 'circ':
            continue
        for okk, m in pg.evaluate(JS, k):
            s.check(okk, m)


if __name__ == '__main__':
    import sys
    sys.exit(0 if run('t_3d', t) else 1)
