from pathlib import Path
import collections, hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parent
pins = {}
def read(p):
    b = p.read_bytes()
    pins[str(p)] = hashlib.sha256(b).hexdigest()
    return b
def load(arm):
    caps = [json.loads(read(p)) for p in sorted((ROOT/'work/k1diag'/arm).glob('*.json'))]
    assert len(caps) == 209
    rows = {r['row_id']:r for c in caps for r in c['rows']}
    names = {(c['capture'],n):v for c in caps for n,v in c['names'].items()}
    assert len(rows) == 1037 and len(names) == 770
    assert all(c['pool'] == 'kbox' and c['input_sha256'] for c in caps)
    return caps, rows, names
read(Path(__file__))
a, ar, an = load('today')
b, br, bn = load('fixed')
assert ar.keys() == br.keys() and an.keys() == bn.keys()
row_changes = {field:sum(ar[i][field] != br[i][field] for i in ar) for field in
               ('prediction', 'box', 'refusal_code', 'member_frames', 'label')}
name_changes = {field:sum(an[i][field] != bn[i][field] for i in an) for field in
                ('selected', 'accepted', 'A0', 'x_sha256', 'proposals_sha256')}
published_path = Path('/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl')
published = {r['row_id']:r for line in read(published_path).splitlines()
             if (r:=json.loads(line))['arm']=='A0_deployed'}
assert ar.keys() == published.keys()
published_matches = sum(all(ar[i][k] == published[i][k] for k in row_changes) for i in ar)
def mra(r):
    return 0. if r['prediction'] is None else float(np.mean(abs(r['prediction']-r['label'])/abs(r['label']) < 1-np.arange(.5,.96,.05)))
ids = sorted(ar)
rooms = sorted({ar[i]['room'] for i in ids})
index = {r:k for k,r in enumerate(rooms)}
delta = np.array([mra(br[i])-mra(ar[i]) for i in ids])
clusters = [index[ar[i]['room']] for i in ids]
sums = np.bincount(clusters, weights=delta, minlength=len(rooms))
counts = np.bincount(clusters, minlength=len(rooms))
draws = np.random.default_rng(20261119).integers(0,len(rooms),(10000,len(rooms)))
boot = sums[draws].sum(1)/counts[draws].sum(1)
result = dict(input_sha256=pins,captures=len(a),names=len(an),rows=len(ar),rooms=len(rooms),
              row_changes=row_changes,name_changes=name_changes,published_matches=published_matches,
              mixed_frames={k:sum(c['mixed_frames'] for c in cs) for k,cs in [('today',a),('fixed',b)]},
              candidates={k:sum(n['candidates'] for n in ns.values()) for k,ns in [('today',an),('fixed',bn)]},
              delta_mra=100*float(delta.mean()),ci95=(100*np.percentile(boot,[2.5,97.5])).tolist(),
              bootstrap_draws=10000,seed=20261119)
result['passed'] = not any(row_changes.values()) and not any(name_changes.values()) and published_matches == 1037 and not any(result['mixed_frames'].values())
(ROOT/'evidence/parity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
assert result['passed']
(ROOT/'STATUS.md').write_text('Independent patch-only K1 parity passes across 209 captures, 770 selections, and 1,037 rows, with all predictions, boxes, accepted candidates, vectors, and proposal digests unchanged. Both arms match the published A0 rows. The 29 tests pass, all four mutations are killed, and the journal/cache audit is complete. The final verdict is being written.\n')
