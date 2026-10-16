"""Point 6 — poutres : lisses basse + haute 63×75 contre la joue, raidisseurs entre les lisses, lisse haute sous les poutrelles (option)."""
from lib import run

JS = r'''(k)=>{
  const out=[],ok=(c,m)=>out.push([!!c,k+' : '+m]);const S=SCN.find(s=>s[0]===k),d=T.can(T.mk(S[1],S[2],S[3])),R=debit(d,null),sc=model3(d,R),SO=sc.solids;
  const BG=d.forme==='poutre'?ptGeo(d).BG:dalGeo(d).BG,bm=BG.beams[0],P=bmPar(d),zTop=d.forme==='poutre'?0:dalGeo(d).ePl,zB=zTop-bm.h-BG.eF,hJ=bm.hJ;
  const LB=SO.filter(o=>o.nm==='lisse basse'),LH=SO.filter(o=>o.nm==='lisse haute'),RD=SO.filter(o=>o.nm==='raidisseur'),J=SO.filter(o=>o.nm==='joue de poutre');
  ok(LB.length&&LH.length&&RD.length,`lisses basses ${LB.length}, hautes ${LH.length}, raidisseurs ${RD.length}`);
  // section 63 (épaisseur, contre la joue) × 75 (hauteur)
  const dims=o=>{const b=bb3(o);return[b[3]-b[0],b[4]-b[1],b[5]-b[2]]};
  ok(LB.concat(LH).every(o=>Math.abs(dims(o)[1]-63)<0.5&&Math.abs(dims(o)[2]-75)<0.5),'lisses 63 × 75 (63 contre la joue, 75 de haut)');
  // lisses et raidisseurs plaqués contre la face extérieure de la joue
  const face=o=>{const b=bb3(o);return b[1]<bm.o?b[4]:b[1]},jf=[bm.o-bm.b/2-BG.eJ,bm.o+bm.b/2+BG.eJ];
  ok(LB.concat(LH,RD).every(o=>jf.some(f=>Math.abs(face(o)-f)<0.5)),'lisses et raidisseurs contre la joue');
  const zLH=P.lhs?hJ-P.hpt:hJ;
  ok(LB.every(o=>Math.abs(bb3(o)[2]-zB)<0.5),'lisse basse en pied de joue');
  ok(LH.every(o=>Math.abs(bb3(o)[5]-(zB+zLH))<0.5),`lisse haute : dessus à ${P.lhs?'−'+P.hpt+' sous le dessus des joues':'dessus des joues'}`);
  // raidisseurs entre les lisses
  ok(RD.every(o=>{const b=bb3(o);return Math.abs(b[5]-(zB+zLH-75))<0.5&&(Math.abs(b[2]-(zB+75))<0.5||Math.abs(b[2]-(zB+BG.eF))<0.5)}),'raidisseurs entre lisse basse et lisse haute');
  // débit : longueurs des raidisseurs et des lisses
  const rd=(R.bois||[]).filter(b=>/^Raidisseurs/.test(b.n));ok(rd.some(b=>Math.abs(b.L-(zLH-150))<1),`raidisseurs au débit L = ${nf(zLH-150,0)}`);
  ok((R.bois||[]).some(b=>/^Lisses hautes/.test(b.n))&&(R.bois||[]).some(b=>/^Lisses basses/.test(b.n)),'lisses basses + hautes au débit');
  // poutrelles (dalle) : contre la joue et posées sur la lisse haute (option), sinon dégagées des lisses
  if(d.forme==='dalle'){const PT=SO.filter(o=>o.nm==='poutrelle').map(bb3);
    const near=PT.filter(b=>Math.abs(b[4]-jf[0])<200||Math.abs(b[1]-jf[1])<200);
    ok(near.length,'poutrelles au voisinage de la poutre');
    if(P.lhs){ok(near.every(b=>Math.abs(b[2]-(zB+zLH))<0.5),'poutrelles posées sur la lisse haute (dessous = dessus de lisse)');
      ok(near.every(b=>Math.min(Math.abs(b[4]-jf[0]),Math.abs(b[1]-jf[1]))<1.01),'poutrelles en butée contre la joue')}
    else ok(near.every(b=>Math.min(Math.abs(b[4]-jf[0]),Math.abs(b[1]-jf[1]))>=63),'poutrelles dégagées des lisses (option non cochée)');
    ok(near.every(b=>Math.abs(b[5]-(zB+hJ))<0.5),'dessus des poutrelles = dessus des joues (sous le platelage)')}
  // contrôle bloquant si la poutrelle ne laisse pas de place aux raidisseurs
  return out}'''

JS_CHK = r'''()=>{const d=T.mk('poutre',{ptDal:true,bmLhs:true,bmHpt:400,ptH:500});const W=checks(T.can(d),null);return W.some(x=>/lisse haute sous les poutrelles/.test(x[1]))}'''


def t(s, pg):
    for k in ['poutre', 'poutre_lhs', 'dalle_circ_pt', 'dalle_pt_lhs', 'poutre_po']:
        for okk, m in pg.evaluate(JS, k):
            s.check(okk, m)
    s.check(pg.evaluate(JS_CHK), 'contrôle : poutrelle trop haute pour la joue signalé')
    # option conservée à l'enregistrement / rechargement du formulaire
    r = pg.evaluate('''()=>{const d=T.mk('dalle',{dlPt:true,bmLhs:true,bmHpt:225});setForm(d);const e=coll();return [e.bmP.lhs,e.bmP.hpt,el('zBmLhs').style.display]}''')
    s.check(r[0] is True and r[1] == 225 and r[2] == '', 'option lisse haute rechargée dans le formulaire', str(r))


if __name__ == '__main__':
    import sys
    sys.exit(0 if run('t_poutre', t) else 1)
