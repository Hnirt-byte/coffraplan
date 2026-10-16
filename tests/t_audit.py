"""v2.1 — revue complète : plans aléatoires plausibles de toutes les formes (graine fixe) passés dans toutes les fonctions.
KO : exception JS, valeur illisible dans un plan (NaN / undefined / Infinity), auto-contrôle intégré en échec, rechargement du
formulaire qui modifie la saisie. Le catalogue des messages (erreurs / alertes) est écrit dans out/audit_messages.json pour revue."""
import json, os, re, sys, collections, time
from lib import run, HERE, OUT

N = int(os.environ.get('AUDIT_N', '30'))
# v2.1 : messages retirés (information déjà portée par le débit / le plan, ou simple conseil sans incidence sur la fabrication)
RETIRES = [r'joints au droit d.un raidisseur$', r'tronçon de coffrage de .* \(très court\)', r'raidisseurs très courts', r"sans gousset d.angle : à envisager",
           r'^Biais \+ pente', r'^Angle > ', r'cadre\(s\) de joint 50 × 50 \(voir plan\)', r'^Goussets : sans objet', r'ramené en tête', r'aucun gousset',
           r'^Goussets > 1/3', r'^Aucune joue', r'^Planches recoupées', r'^Option poutres cochée', r'^Cerces : hauteur intérieure', r'^Joues parallèles : extrémités',
           r'montants coupés au droit des cerces', r'bandes raboutées en hauteur', r'Hauteur poteau > hauteur intérieure', r'entrent dans le fond supérieur', r'les angles font foi',
           r'^Poteau \d+ en conflit avec la forme concentrique']


def t(s, pg):
    pg.add_script_tag(path=os.path.join(HERE, 'auditx.js'))
    forms = pg.evaluate("[...el('iForme').options].map(o=>o.value)")
    cat, res = collections.defaultdict(lambda: collections.Counter()), []
    t0 = time.time()
    for f in forms:
        for k in range(N):
            r = pg.evaluate('([f,s])=>AX.run(f,s)', [f, 1000 + k])
            res.append(r)
            tag = f'{f} #{k}'
            for lvl, m in r['W']:
                cat[lvl + ' | ' + re.sub(r'\d+(?:[,.]\d+)?', '#', m)][f] += 1
            s.check(not r['ex'], f'[{tag}] aucune exception', ' | '.join(r['ex'])[:900])
            bad = [m for _, m in r['W'] if any(re.search(x, m) for x in RETIRES)]
            s.check(not bad, f'[{tag}] aucun message retiré en v2.1 (sans incidence sur la fabrication)', str(bad))
            s.check(not r['nan'], f'[{tag}] aucune valeur illisible dans le plan', ' | '.join(r['nan'])[:400])
            if not r['bad']:
                s.check(not r['ac'], f'[{tag}] auto-contrôle intégré conforme', ' | '.join(r['ac'])[:500])
    json.dump({k: dict(v) for k, v in sorted(cat.items(), key=lambda kv: -sum(kv[1].values()))}, open(os.path.join(OUT, 'audit_messages.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump(res, open(os.path.join(OUT, 'audit_runs.json'), 'w'), ensure_ascii=False)
    ok = sum(1 for r in res if not r['bad'])
    print(f'  {len(res)} plans ({ok} cohérents, {len(res)-ok} bloqués par une erreur de saisie) en {time.time()-t0:.0f} s')
    tt = collections.defaultdict(list)
    for r in res:
        for k, v in r['t'].items():
            tt[k].append(v)
    print('  temps max (ms) : ' + ', '.join(f'{k} {max(v)}' for k, v in tt.items()))


if __name__ == '__main__':
    sys.exit(0 if run('t_audit', t) else 1)
