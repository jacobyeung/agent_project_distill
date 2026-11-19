"""Power check for s4: own token function reproduces the lists' published tokens, and
synthetic rows on listed scenes are caught by both the own matcher and the tree's."""
import json, random, re, sys
from pathlib import Path
import s4_legal as L

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W/'new'))
from student_pilot.s1_exclusions import Exclusions
from student_pilot.r0_exclusion import Reserve


def main():
    expanded, natives, venue = L.build({})
    tok2nat = {(d, t): (d, sc) for d, sc in natives for t in L.tokens(d, sc)}
    out = {}
    b = json.loads(L.F['bench'].read_text())
    pub = {(L.DS.get(d, d), t) for d, t in b['rung1_tokens']}
    out['bench_published_tokens'] = len(pub)
    out['bench_published_tokens_resolved'] = sum(k in tok2nat for k in pub)
    dev = json.loads(L.F['dev_s1'].read_text())
    dt = {L.norm(x) for vs in dev['aliases'].values() for x in vs if re.search(r'/v[0-9a-f]{12}$', x)}
    out['dev_alias_tokens'] = len(dt)
    out['dev_alias_tokens_resolved'] = sum(k in tok2nat for k in dt)
    pin = lambda p: dict(path=str(p), sha256=L.sha(p))
    ex = Exclusions(pin(L.F['dev_s1']), pin(L.F['bench']))
    rs = Reserve(L.F['r0'])
    rng = random.Random(0)
    lists = dict(dev_s1=[L.norm(x) for x in dev['natives']],
                 bench=[L.norm(x) for x in b['scenes']],
                 r0=[L.norm(x) for x in json.loads(L.F['r0'].read_text())['captures']],
                 test=[L.norm(x) for x in json.loads(L.F['test'].read_text())['names']])
    for name, members in lists.items():
        sample = rng.sample(members, min(200, len(members)))
        own = tree = 0
        for d, sc in sample:
            tok = 'v'+__import__('hashlib').sha256(('rung1 scene '+L.NS[d][0]+'/'+sc).encode()).hexdigest()[:12]
            row = dict(dataset=d, scene=tok, qid='x')
            nat = tok2nat.get((d, tok))
            keys = {(d, tok)} | ({nat} if nat else set())
            if nat and L.room(*nat): keys.add(L.room(*nat))
            own += bool(keys & expanded[name])
            if name in ('dev_s1', 'bench'):
                tree += ex.matches(row)['dev' if name == 'dev_s1' else 'benchmark']
            elif name == 'r0':
                tree += bool(rs.matches(dict(dataset=d, scene=sc)))
        out[name] = dict(sampled=len(sample), own_hits=own, tree_hits=tree)
    (W/'S4C_POWER.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
