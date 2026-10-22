"""Phase 8 (demande de Kévin du 22/10/2026) : défauts relevés sur un plan réel « type D » (hors dépôt), reproduits sur un plan
entièrement fictif (tests/plan_d_fictif.py) et corrigés :
  1. tableaux juxtaposés : la nomenclature (46 lignes) et le tableau de trappes voisin, dont les lignes sont aux mêmes hauteurs,
     étaient mêlés (lecture automatique coupée après R14, suite prise par le tableau voisin) → couloirs des en-têtes ;
  2. titre « Sous Toiture » avec son échelle « 1 : 25 », sans « vue » ni « plan » : non reconnu (dessin sans titre, rien compté) →
     titre reconnu par son échelle, vue en plan déduite du niveau nommé et du dessin.
Cas négatif : « Sous Toiture » seulement dans une note, ou en grand texte sans échelle : jamais une vue. Cartouche « VUE EN PLAN -
SOUS TOITURE » : jamais une vue. Aucune occurrence déduite du nombre de lignes du tableau."""
import json, os, sys, tempfile
from playwright.sync_api import sync_playwright
from lib import Suite, open_app
import plan_d_fictif as PD


def t(s):
    tmp = tempfile.mkdtemp()
    F = PD.fichiers(tmp)
    s.check(open(F['PLAN_D_FICTIF.pdf'][0], 'rb').read() == open(PD.fichiers(tempfile.mkdtemp())['PLAN_D_FICTIF.pdf'][0], 'rb').read(), 'PDF fictif : écriture déterministe')
    L46 = F['PLAN_D_FICTIF.pdf'][1]['lignes']
    with sync_playwright() as pw:
        b, pg, errs = open_app(pw, width=1500)
        net = []
        pg.context.route(lambda u: not u.startswith(('file:', 'blob:', 'data:')), lambda r: (None if 'fonts.g' in r.request.url else net.append(r.request.url), r.abort()))
        pg.reload(); pg.wait_for_function('typeof gen==="function" && _ready')
        J = pg.evaluate

        # ---- 1. tableaux juxtaposés : lecture automatique, sans zone
        pg.click('#bDxi'); pg.set_input_files('#dxiF', F['PLAN_D_FICTIF.pdf'][0]); pg.wait_for_function('DXI&&DXI.NA&&DXI.doc')
        A = J('''({N:DXI.NA.nomenclatures.map(N=>({titre:N.titre,lignes:N.lignes.map(L=>({r:L.repere,d:L.dims,c:L.cellules}))})),
                 E:DXI.NA.ecartes.map(e=>({titre:e.titre,nature:e.nature,n:e.nLignes,reps:(e.lignes||[]).map(l=>l.repere)}))})''')
        N = [n for n in A['N'] if 'réservations' in n['titre']]
        s.check(len(A['N']) == 1 and len(N) == 1, 'une seule nomenclature de réservations', json.dumps([n['titre'] for n in A['N']], ensure_ascii=False))
        L = N[0]['lignes'] if N else []
        reps = [l['r'] for l in L]
        s.check(reps == [x['repere'] for x in L46], '46 lignes, dans l\'ordre, avec leurs vrais repères (R01-R38, V01-V08) ; aucune perdue, inventée ni dupliquée', json.dumps(reps))
        ok_d = sum(1 for l, x in zip(L, L46) if l['d'] and l['d'].get('type') == 'rect' and sorted([l['d']['a'], l['d']['b']]) == sorted([x['H'], x['L']]) and l['d'].get('unite') == 'mm')
        ok_n = sum(1 for l, x in zip(L, L46) if x['niv'] in l['c'] and ' | '.join(x['fin']) in ' | '.join(l['c']) and x['desc'] in l['c'])
        s.check(ok_d == 46 and ok_n == 46, f'cotes en mm ({ok_d}/46), niveaux, finitions et désignations ({ok_n}/46) exacts')
        s.check(not any('NOTA' in ' '.join(l['c']) or 'feuillures' in ' '.join(l['c']) or 'REGARD' in ' '.join(l['c']) for l in L),
                'aucune note (« NOTA GENERAL ») ni ligne de trappe dans les lignes de la nomenclature')
        T = [e for e in A['E'] if e['nature'] == 'trappes']
        s.check(len(T) == 1 and T[0]['n'] == 3 and T[0]['reps'] == ['T01', 'T02', 'T03'], 'tableau de trappes distinct : 3 lignes T01-T03, écarté (jamais créé)', json.dumps(A['E'], ensure_ascii=False)[:300])

        # ---- 2. vue « Sous Toiture » + « 1 : 25 » ; cartouche jamais une vue ; occurrences dans la vue
        J('()=>{dxiVue("p");el("dxrOcr")&&(el("dxrOcr").checked=false)}')
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob&&!!el("dxrT")', timeout=300000)
        V = J('dxrVues().map(v=>({id:v.id,type:v.type,titre:v.titre,echelle:v.echelle,region:v.region,confiance:v.confiance,incertaine:!!v.incertaine,motifs:v.motifs}))')
        st = [v for v in V if v['titre'] == 'Sous Toiture']
        s.check(len(st) == 1 and st[0]['type'] == 'plan' and st[0]['echelle'] and st[0]['echelle']['valeur'] == 25 and not st[0]['incertaine'] and st[0]['confiance'] != 'forte',
                '« Sous Toiture » + « 1 : 25 » : vue en plan (confiance au plus moyenne), échelle 1:25 rattachée à cette vue', json.dumps(V, ensure_ascii=False)[:600])
        s.check(st and any('déduite' in m for m in st[0]['motifs']), 'motif lisible : vue en plan déduite du niveau nommé, de l\'échelle et du dessin', json.dumps(st[0]['motifs'] if st else None, ensure_ascii=False))
        r = st[0]['region'] if st else [0, 0, 0, 0]
        s.check(r[0] <= 130 and r[2] >= 3000 and r[1] <= 910 and r[3] >= 2200, 'vue associée au dessin (murs et réservations), pas au cartouche', json.dumps(r))
        s.check(not any(v['titre'] and 'VUE EN PLAN' in v['titre'] for v in V) and len([v for v in V if v['echelle']]) == 1,
                'cartouche « VUE EN PLAN - SOUS TOITURE » et son « 1 : 25 » : ni vue, ni échelle de la planche', json.dumps([(v['titre'], v['echelle']) for v in V], ensure_ascii=False))
        CS = J('Object.fromEntries(DXI.NL.map(({L})=>[L.repere,DXI.CS[L.id]?DXI.CS[L.id].localisees:null]))')
        s.check(all(CS.get(f'R{k:02d}') == 1 for k in range(1, 6)), 'repères R01-R05 du dessin : une occurrence physique chacun, dans la vue « Sous Toiture »', json.dumps({k: CS.get(k) for k in ['R01', 'R02', 'R03', 'R04', 'R05', 'R06']}))
        s.check(sum(v or 0 for v in CS.values()) == 5, 'aucune occurrence déduite du nombre de lignes : 5 repères dessinés → 5 occurrences (pas 46)', str(sum(v or 0 for v in CS.values())))

        # ---- 3. cas négatif : « Sous Toiture » dans une note, ou en grand sans échelle
        pg.set_input_files('#dxiF', F['PLAN_D_NOTE.pdf'][0]); pg.wait_for_function('DXI&&DXI.NA&&DXI.doc&&DXI.doc.fichier==="PLAN_D_NOTE.pdf"')
        J('()=>{dxiVue("p");el("dxrOcr")&&(el("dxrOcr").checked=false)}')
        pg.click('#dxrGo'); pg.wait_for_function('!DXI.rJob&&!!el("dxrT")', timeout=300000)
        V2 = J('dxrVues().map(v=>({type:v.type,titre:v.titre}))')
        CS2 = J('DXI.NL.reduce((s,{L})=>s+((DXI.CS[L.id]||{}).localisees||0),0)')
        s.check(not any(v['titre'] and 'Toiture' in v['titre'] for v in V2) and not any(v['type'] == 'plan' for v in V2) and CS2 == 0,
                'cas négatif : « Sous Toiture » dans une note ou sans échelle : aucune vue, aucune occurrence comptée', json.dumps(V2, ensure_ascii=False) + f' · {CS2}')

        # ---- 4. titres : règles sur textes seuls
        R = J('''()=>{const T=[];for(let i=0;i<30;i++)T.push({id:'p'+i,texte:'x'+i,x:20*i,y:10,h:5,w:10});
          const g=(id,texte,x,y,h)=>T.push({id,texte,x,y,h,w:texte.length*0.6*h});
          g('a','Sous dalle',100,900,14);g('ae','1 : 50',100,880,9);g('b','Dessus toiture',600,900,14);g('be','1/20',610,881,9);
          g('c','Locaux techniques',1000,900,14);g('ce','1 : 100',1000,880,9);g('d','Sous Toiture',1500,900,14);g('e','Plan de toiture',2000,900,14);
          return CPI.vues.titres(T).map(t=>[t.texte,t.type,!!t.deduit])}''')
        d = {x[0]: x for x in R}
        s.check(d.get('Sous dalle', [0, 0])[1] == 'plan' and d.get('Dessus toiture', [0, 0])[1] == 'plan' and d['Sous dalle'][2],
                'titres sans « vue » : « Sous dalle 1 : 50 », « Dessus toiture 1/20 » → vue en plan déduite', json.dumps(R, ensure_ascii=False))
        s.check(d.get('Locaux techniques', [0, 0])[1] == 'autre' and 'Sous Toiture' not in d and d.get('Plan de toiture', [0, 0, 1])[1] == 'plan' and not d['Plan de toiture'][2],
                'titre avec échelle sans niveau nommé : « autre » (jamais compté) ; sans échelle : pas un titre ; « Plan de toiture » : mot-clé habituel', json.dumps(R, ensure_ascii=False))

        s.check(not net, 'aucune requête réseau', json.dumps(net[:3]))
        s.check(not [e for e in errs if 'net::ERR_FAILED' not in e], 'aucune erreur JS', json.dumps(errs[:3]))
        b.close()


if __name__ == '__main__':
    s = Suite('t_plan_d')
    try:
        t(s)
    except Exception:
        import traceback
        s.check(False, 'exception', traceback.format_exc()[-1500:])
    sys.exit(0 if s.report() else 1)
