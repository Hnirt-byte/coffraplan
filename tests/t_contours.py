"""Phase 9B : reconstruction contextuelle, protections et provenance (géométries fictives).
Les plans réels de validation restent hors du dépôt ; aucun extrait ni tracé réel ici.
"""
import json, os, sys
from playwright.sync_api import sync_playwright
from lib import Suite, open_app, HERE


def t(s):
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw)
        pg.add_script_tag(path=os.path.join(HERE, 'support_cas.js'))
        pg.evaluate('''()=>{
          window.fixture9b=(circ=false,scale=1)=>{
            const x=circ?SC.voileCirc({Ri:200,t:8,w:24,k:1,ouverture:'rect'}):SC.voileDroit({t:8,w:24,k:1,ouverture:'rect'}),
              P=x.obs.candidat.geometrie.points,pt=p=>p.map(v=>v*scale),S=x.env.segments.filter(s=>!/^k/.test(s.id));
            // Traverses interrompues, sans cycle rectangle indépendant.
            [1,3].forEach(i=>{const a=P[i],b=P[(i+1)%4],q=t=>a.map((v,j)=>v+t*(b[j]-v));
              S.push({id:'tr'+i+'a',a,b:q(.4)},{id:'tr'+i+'b',a:q(.6),b})});
            S.push({id:'diag1',a:P[0],b:P[2]},{id:'diag2',a:P[1],b:P[3]});
            const c=x.obs.candidat.centre,T=[{id:'label',texte:'R1',page:1,x:c[0]*scale,y:c[1]*scale,w:4*scale,h:2*scale}];
            return {g:{page:1,w:800*scale,h:800*scale,segments:S.map(s=>({...s,a:pt(s.a),b:pt(s.b)})),contours:[],
              courbes:x.env.courbes.map(s=>({...s,c:s.c.map(pt)})),petits:[]},ctx:{reperes:['R1'],textes:T,cadres:[]}}};
          window.run9b=x=>CPI.contours.reconstruire(x.g,x.ctx);
        }''')
        J = pg.evaluate
        for circ in [False, True]:
            for scale in [.25, 1, 4]:
                r = J('(a)=>run9b(fixture9b(a[0],a[1]))', [circ, scale])
                s.check(len(r) == 1, f'{"circulaire" if circ else "droit"}, facteur graphique {scale} : une ouverture reconstruite', json.dumps(r)[:300])
                if not r:
                    continue
                c = r[0]
                s.check(c['geometrie']['ferme'] is False and c['reconstruction']['explicite'] is False
                        and len(c['reconstruction']['diagonales']) == 2 and len(c['reconstruction']['traverses']) == 2,
                        'limites inférées distinguées du contour fermé, traits sources et couvertures conservés')
        for code, label in [
            ("x.ctx.reperes=[]", 'sans nomenclature'),
            ("x.ctx.textes=[]", 'sans repère'),
            ("x.ctx.textes[0].ocr={conf:40}", 'repère OCR incertain'),
            ("x.ctx.cadres=[[-100,-100,100,100]]", 'dans un tableau ou cartouche'),
            ("x.ctx.zone={x0:200,y0:200,x1:300,y1:300}", 'hors de la zone choisie'),
            ("x.ctx.zone={x0:-1,y0:-1,x1:1,y1:1}", 'dépasse la zone choisie'),
            ("x.g.segments=x.g.segments.filter(s=>!s.id.startsWith('tr'))", 'croix seule sans traverses'),
            ("x.g.segments=x.g.segments.filter(s=>!s.id.startsWith('f'))", 'sans parements'),
            ("x.g.segments=x.g.segments.filter(s=>s.id!=='diag2')", 'une seule diagonale'),
            ("for(let i=-2;i<=2;i++)x.g.segments.push({id:'grille'+i,a:[-100,i*8],b:[100,i*8]})", 'quadrillage régulier'),
        ]:
            n = J('()=>{const x=fixture9b();' + code + ';return run9b(x).length}')
            s.check(n == 0, label + ' : aucune ouverture promue', n)
        s.check(J('()=>{const x=fixture9b();x.ctx.textes[0].h=6;return run9b(x).length}') == 1,
                'petits fragments de traverse gardés même avec un grand repère OCR')
        r = J('''()=>{const x=fixture9b(true),c=run9b(x)[0];
          return CPI.support.analyser({repere:'R1',candidat:c,page:1},CPI.support.envPdf(x.g,[]),{ligne:SC.ligne({a:24,b:40}),sag:GEO.sag})}''')
        s.check(r['support']['type'] == 'voile_circulaire' and r['support']['confiance'] == 'faible'
                and r['support']['rayon_interieur_mm'] is None and r['support']['epaisseur_mm'] is None
                and r['coffrage']['solution_proposee'] == 'a_determiner' and r['coffrage']['fleche_interieure_mm'] is None,
                'support reconnu géométriquement, sans échelle : aucune mesure physique ou solution inventée')
        s.check(any(p['type'] == 'contour_reconstruit' for p in r['preuves']) and r['validation_utilisateur_requise'],
                'reconstruction et confirmation obligatoire conservées dans les preuves du support')
        r = J('''()=>{const x=fixture9b(),c=run9b(x)[0];c.id='REC';
          const L={id:'L',repere:'{R1',page:1,unite:'mm',dims:{type:'rect',a:24,b:40}},
            a=CPI.rapprochement.rapprocher([L],x.ctx.textes,[c],{mm:()=>100}).lignes.L;
          return {a,brut:L.repere}}''')
        s.check(r['a']['concordance'] == 'partielle' and r['a']['occurrences'][0]['contour'] == 'REC'
                and r['brut'] == '{R1' and 'ponctuation' in r['a']['note'],
                'repère entre accolades : rapprochement traçable sans écraser le brut, aucune cote confirmée par reconstruction', r)
        r = J('''()=>{const x=fixture9b(),c=run9b(x)[0];c.id='REC';
          const t={...x.ctx.textes[0],id:'autre',texte:'R2',x:1};
          return CPI.rapprochement.rapprocher([{id:'L1',repere:'R1',page:1},{id:'L2',repere:'R2',page:1}],
            x.ctx.textes.concat(t),[c],{}).lignes}''')
        s.check(r['L1']['occurrences'][0]['contour'] == 'REC' and r['L2']['occurrences'][0]['contour'] is None,
                'un repère voisin ne récupère pas le contour reconstruit pour un autre repère')
        r = J('''()=>{const pts=Array.from({length:121},(_,i)=>[100*Math.cos(i*2*Math.PI/120),100*Math.sin(i*2*Math.PI/120)]),
          e=CPI.support.envPdf({contours:[{id:'anneau',pts,courbes:[]}],segments:[],courbes:[]},[]),
          q=CPI.support.envPdf({contours:[{id:'cadre',pts:Array.from({length:4},()=>[[0,0],[10,0],[10,10],[0,10]]).flat(),courbes:[]}],segments:[]},[]);
          return [e.arcs.length,q.arcs.length,e.arcs[0].d]}''')
        s.check(r[0:2] == [1, 0] and abs(r[2] - 2 * 3.141592653589793) < 1e-8,
                'cercle fermé segmenté : arc complet ; coins de rectangle sur un cercle : refusés')
        # Garde interface : l'échelle ne transforme pas les limites inférées en cotes de fabrication.
        r = J('''()=>{dxiOpen();const x=fixture9b(),c=run9b(x)[0];
          DXI={fmt:'pdf',C:[c],R:[{cotes:'',cotesT:false}],cal:{1:{k:100}}};dxrPre(0);
          const r={cotes:DXI.R[0].cotes,ouvrages:P.length};dxiQuit();closeModal();return r}''')
        s.check(r == {'cotes': '', 'ouvrages': 0}, 'aucune cote issue des limites reconstruites, aucun ouvrage créé', r)
        s.check(not errs, 'aucune erreur JavaScript', '; '.join(errs))
        b.close()


if __name__ == '__main__':
    s = Suite('t_contours')
    t(s)
    sys.exit(0 if s.report() else 1)
