"""v2.7 — revue de cohérence croisée : pour chaque plan (36 scénarios + plans aléatoires de toutes les formes), une même pièce
doit exister avec les mêmes quantités et cotes partout.
  1. débit ↔ pièces à découper (un exemplaire) : chaque repère CP découpé est au débit, aire découpée = q × a × b ;
  2. débit ↔ imbrication : aucune pièce non placée ;
  3. débit ↔ 3D : volume de CP et de bois du modèle 3D = volume du débit (± 1 %, facettes des formes courbes) ;
  4. débit ↔ 3D : repères CP sans pièce 3D repérée → rapport seulement (out/coherence.json), traité avec la nouvelle 3D ;
  5. débit ↔ CSV : chaque repère présent ;
  6. découpe ↔ DXF : chaque repère découpé présent dans le fichier.
Écarts connus et voulus : poutrelles de la dalle (étaiement, hors débit), dessinées en 3D pour situer le platelage."""
import json, os, sys
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE, OUT

N = int(os.environ.get('COH_N', '10'))
JS = r'''([kind,a,b])=>{
  const d0=kind==='scn'?T.mk(a[1],a[2],a[3]):AX.make(a,b);d0.date='2026-10-10';const d=canon(migr(d0)),g=d.forme==='voile'?voileGeo(d):null;
  if(badDims(checks(d,g))||limErr(d).length)return null;
  const R=debit(d,g),E=[],e=m=>E.push(m),cp=R.filter(r=>['j','fi','fs'].includes(r.k)),nf0=v=>Math.round(v);
  // 1. pièces à découper (un exemplaire)
  const PC=nestPieces(d,R),ar={};Object.values(PC).flat().forEach(p=>{const A2=P=>Math.abs(P.reduce((s,q,i)=>{const n=P[(i+1)%P.length];return s+q[0]*n[1]-n[0]*q[1]},0))/2,pa=(p.poly?A2(p.poly):p.w*p.h)-(p.hole&&p.hole.length>2?A2(p.hole):0);ar[p.ftag.replace(/[a-z]$/,'')]=(ar[p.ftag.replace(/[a-z]$/,'')]||0)+pa});
  Object.keys(ar).forEach(t=>{if(!R.some(r=>r.ftag===t))e('découpe : repère '+t+' absent du débit')});
  cp.forEach(r=>{if(nestSkip(d,r.k)||!(ar[r.ftag]>0))return;const ex=r.m2*1e6;if(Math.abs(ar[r.ftag]-ex)>Math.max(0.01*ex,100))e(`découpe : ${r.ftag} aire ${nf0(ar[r.ftag]/1e4)/100} m² ≠ débit ${nf0(ex/1e4)/100} m²`)});
  // 2. imbrication
  try{const C=cutNest(d,R);Object.values(C.N).forEach(n=>{if(n.fail&&n.fail.length)e('imbrication : '+n.fail.length+' pièce(s) non placée(s)')})}catch(x){e('imbrication : '+x.message)}
  // 3. volumes 3D
  const vol=o=>{let v=0;o.F.forEach(f=>{for(let i=1;i<f.length-1;i++){const p=f[0],q=f[i],s=f[i+1];v+=(p[0]*(q[1]*s[2]-q[2]*s[1])-p[1]*(q[0]*s[2]-q[2]*s[0])+p[2]*(q[0]*s[1]-q[1]*s[0]))/6}});return Math.abs(v)};
  const sc=model3(d,R),so=sc.solids.filter(o=>o.role!=='ctx'),CPC=[C3.j,C3.cl,C3.gs,C3.fi,C3.fs,C3.poche].filter(Boolean);
  const v3cp=so.filter(o=>CPC.includes(o.col)).reduce((s,o)=>s+vol(o),0),v3b=so.filter(o=>o.col===C3.bois&&!/poutrelle/i.test(o.nm)).reduce((s,o)=>s+vol(o),0);
  const vcp=cp.reduce((s,r)=>s+r.m2*1e6*cpOf(d,r.k).e,0),vb=(R.bois||[]).reduce((s,x)=>{const m=String(x.n).match(/(\d+)\s*[×x]\s*(\d+)/);return s+(m?x.q*x.L*m[1]*m[2]:0)},0);
  if(Math.abs(v3cp-vcp)>Math.max(0.01*vcp,2e4))e(`3D : volume CP ${nf0(v3cp/1e6*1000)/1000} dm³ ≠ débit ${nf0(vcp/1e6*1000)/1000} dm³`);
  if(Math.abs(v3b-vb)>Math.max(0.01*vb,2e4))e(`3D : volume bois ${nf0(v3b/1e6*1000)/1000} dm³ ≠ débit ${nf0(vb/1e6*1000)/1000} dm³`);
  // 4. repères portés en 3D
  const t3=new Set(sc.solids.map(o=>o.tag).filter(Boolean));const miss=cp.filter(r=>!t3.has(r.tag)).map(r=>r.tag);const info=miss.length?['3D : repère(s) sans pièce 3D : '+miss.join(', ')]:[];
  // 5. CSV, fiche atelier
  const csv=debitCSV([d0]);const mc=R.concat(R.bois||[]).filter(r=>!csv.includes(r.ftag)).map(r=>r.ftag);if(mc.length)e('CSV : repère(s) absent(s) : '+mc.join(', '));
  // 6. DXF : chaque repère découpé figure dans le fichier (calques CP)
  try{const fx=dxfPlanFile(d0);if(fx.err)e('DXF : '+fx.err);else{const tx=new TextDecoder('latin1').decode(fx.bytes),md=[...new Set(Object.values(PC).flat().map(p=>p.ftag))].filter(t=>!tx.includes(t));if(md.length)e('DXF : repère(s) découpé(s) absent(s) : '+md.slice(0,6).join(', '))}}catch(x){e('DXF : '+x.message)}
  return{f:d.forme,E,info}}'''


def t(s):
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        pg.add_script_tag(path=os.path.join(HERE, 'auditx.js'))
        jobs = [('scn ' + x[0], ['scn', x, 0]) for x in pg.evaluate('SCN')]
        jobs += [(f'{f} #{k}', ['aud', f, 7000 + k]) for f in pg.evaluate("[...el('iForme').options].map(o=>o.value)") for k in range(N)]
        rep = {}
        for k, arg in jobs:
            try:
                r = pg.evaluate(JS, arg)
            except Exception as ex:
                s.check(False, f'[{k}] exception', str(ex)[:300]); continue
            if r is None:
                continue
            rep[k] = {'erreurs': r['E'], 'info': r['info']}
            s.check(not r['E'], f'[{k}] cohérent', ' | '.join(r['E'])[:500])
        json.dump(rep, open(os.path.join(OUT, 'coherence.json'), 'w'), ensure_ascii=False, indent=1)
        s.check(not [e for e in errs if 'net::' not in e], 'aucune erreur JS', str(errs[:3]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_coh')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
