"""Reproduce the ladder contrast and partition it by explicit candidate labels."""
from pathlib import Path
from collections import defaultdict
import gzip
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
K = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
A = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4')
pins = {}


def read(path):
    path = Path(path)
    data = path.read_bytes()
    pins[str(path)] = hashlib.sha256(data).hexdigest()
    return data


def score(row):
    p, y = row['prediction'], row['label']
    return 0. if p is None else float(np.mean(abs(p-y)/abs(y) < 1-np.arange(.5, .96, .05)))


arms = defaultdict(dict)
p = K/'out/box_ladder/PER_ITEM.jsonl'
digest = hashlib.sha256()
with p.open('rb') as f:
    for line in f:
        digest.update(line)
        # Other arms are irrelevant; avoid materializing their JSON objects.
        if not (line.startswith(b'{"arm": "A0_deployed"') or line.startswith(b'{"arm": "A8_nonull_best1"')):
            continue
        row = json.loads(line)
        assert row['row_id'] not in arms[row['arm']]
        arms[row['arm']][row['row_id']] = row
pins[str(p)] = digest.hexdigest()
a8 = arms['A8_nonull_best1']
a0 = {k: arms['A0_deployed'][k] for k in a8}
ids = sorted(a8)
assert len(ids) == 883
assert all(a0[i]['label'] == a8[i]['label'] and a0[i]['room'] == a8[i]['room'] for i in ids)

# Names and capture identities come directly from the priced rows, not a new manifest.
labels = {}
for capture in sorted({r['capture'] for r in a0.values()}):
    path = K/'out/box_ladder/serving_tables'/(capture.replace('/', '__')+'.json.gz')
    rec = json.loads(gzip.decompress(read(path)))
    assert rec['capture'] == capture
    groups = defaultdict(list)
    for row in rec['rows']:
        assert row['y'] in (0, 1)
        groups[row['name']].append(row['y'])
    labels[capture] = groups


def summarize(keys):
    left = np.array([score(a8[i]) for i in keys])
    right = np.array([score(a0[i]) for i in keys])
    return dict(rows=len(keys), a0_mra=100*float(right.mean()) if keys else None,
                a8_mra=100*float(left.mean()) if keys else None,
                delta=100*float((left-right).mean()) if keys else None,
                contribution_to_overall=100*float((left-right).sum())/len(ids),
                wins=int((left>right).sum()), losses=int((left<right).sum()), ties=int((left==right).sum()),
                a0_refusals=sum(a0[i]['prediction'] is None for i in keys),
                a8_refusals=sum(a8[i]['prediction'] is None for i in keys))


groups = defaultdict(list)
row_records = []
for i in ids:
    row = a0[i]
    names = list(row['member_frames'])
    assert len(names) == 2 and set(names) == set(a8[i]['member_frames'])
    ys = [labels[row['capture']].get(n, []) for n in names]
    group = ('empty_operand_pool' if any(not y for y in ys) else
             'nonempty_operand_without_positive' if any(not any(y) for y in ys) else
             'positive_available_for_both_operands')
    groups[group].append(i)
    row_records.append(dict(row_id=i, capture=row['capture'], group=group,
                            a0_score=score(row), a8_score=score(a8[i])))

rooms = sorted({a0[i]['room'] for i in ids})
room_index = {r:k for k,r in enumerate(rooms)}
delta = np.array([score(a8[i])-score(a0[i]) for i in ids])
clusters = [room_index[a0[i]['room']] for i in ids]
sums = np.bincount(clusters, weights=delta, minlength=len(rooms))
counts = np.bincount(clusters, minlength=len(rooms))
draws = np.random.default_rng(20261119).integers(0, len(rooms), (10000, len(rooms)))
ci = (100*np.percentile(sums[draws].sum(1)/counts[draws].sum(1), [2.5,97.5])).tolist()
published = json.loads(read(K/'out/box_ladder/SUMMARY_TRAIN.json'))['contrasts']['A8_nonull_minus_A0_tables']
overall = summarize(ids)
assert np.isclose(overall['delta'], published['estimate']) and np.allclose(ci, published['ci95'])

for path in [K/'train_pricing.py', K/'train_nonull_v2.py', K/'selector_nonull.py',
             K/'math_v2.py', K/'summarize_train.py', K/'out/REPORT.md',
             A/'src/b/e2e_reader/stage1.py', A/'src/b/e2e_reader/parity.py',
             A/'ret/metadata/reads/0/metadata/0.json', ROOT/'analyze.py']:
    read(path)
record_hashes = json.loads(read(ROOT/'out/evidence/record_hashes.json'))['input_sha256']
for source, digest in record_hashes.items():
    assert hashlib.sha256(read(ROOT/'out/evidence'/Path(source).name)).hexdigest() == digest
pins.update(record_hashes)

result = dict(command='OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python analyze.py',
              overall=overall, ci95=ci, rooms=len(rooms), bootstrap_draws=10000, seed=20261119,
              groups={k:summarize(v) for k,v in sorted(groups.items())},
              limitation='Candidate-label coverage is not an observed null decision. Full null_argmax choices/logits for the 883 rows are MISSING from PER_ITEM.jsonl; the expected deployed selector weights at /scratch/jjyeung/b01ec87a6f29b/d/h/selector_head.safetensors are not bundled in the supplied A4 evidence. No null-on counterfactual was computed.',
              row_records=row_records, input_sha256=pins)
(ROOT/'out/ANALYSIS.json').write_text(json.dumps(result, indent=2)+'\n')
lines = [f'Overall: {overall}; CI95={ci}; rooms={len(rooms)}.']
lines += [f'{k}: {summarize(v)}.' for k,v in sorted(groups.items())]
lines += [result['limitation'], 'Command: '+result['command']]
(ROOT/'out/COUNTS.txt').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
