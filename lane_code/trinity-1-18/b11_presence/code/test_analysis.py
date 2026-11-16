"""CPU tests for analysis.py on synthetic journals built from K1 GT visibility (no model output is read).
Checks: fit reads no held-out journal (held-out files are corrupted during fit), fit and price reproducible byte for byte,
GT program 100 on appearance order, torn tails tolerated, exact-match answer rule, decision only with full coverage,
price refuses a FROZEN.json written by other code. Each run writes a fresh work/synth/run_<epoch> folder."""
import json, shutil, subprocess, sys, hashlib, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import analysis as A

LANE = A.LANE
W = LANE / f'work/synth/run_{int(time.time())}'
PY = [sys.executable, str(Path(__file__).parent / 'analysis.py')]
caps = A.load_captures(LANE / 'out/prep')
items = A.load_items(LANE / 'out/prep')
rng = np.random.default_rng(1)
J = W / 'journals'
for sub in ('V', 'IY'):
    (J / sub).mkdir(parents=True)
for cname, c in sorted(caps.items()):
    rows = {'V': [], 'IY': []}
    for obj in c['scored']:
        vis = np.array(c['categories'][obj]['visible'])
        for arm, noise in (('V', 1.5), ('I', 2.5), ('Y', 3.5)):
            x = 3.0 * (2 * vis - 1) - 1.0 + rng.normal(0, noise, 32)
            for k in range(32):
                rows['V' if arm == 'V' else 'IY'].append(dict(arm=arm, capture=cname, obj=obj, frame=k + 1, logit=float(x[k])))
    for sub, rs in rows.items():
        with open(J / sub / (A.slug(cname) + '.jsonl'), 'w') as f:
            for r in rs:
                f.write(json.dumps(r) + '\n')
            f.write(json.dumps(dict(timing={sub: dict(seconds=10.0, queries=len(rs), prefix_tokens=100)}, n=len(rs))) + '\n')


import direct as D
IDENT = D.model_identity(LANE / 'work/model_m544')


def write_direct(path, drop=0, torn=False, bad=()):
    """bad: kinds of invalid rows to put in place of the first held-out appearance items: binding, score, mismatch."""
    bad = list(bad)
    with open(path, 'w') as f:
        for n, it in enumerate(sorted(items, key=lambda i: i['id'])):
            ho_app = it['split'] == 'heldout' and it['type'] == 'obj_appearance_order'
            if ho_app and drop and n % 7 == 0:
                drop -= 1
                continue
            sc = float(rng.random() < 0.6)
            row = dict(example_id=it['id'], status='complete', cell=D.CELL['name'],
                       binding=D.binding_for(it, caps[it['capture']], IDENT), score=sc, B2048=dict(score=sc))
            if ho_app and bad:
                kind = bad.pop(0)
                if kind == 'binding':
                    row['binding'] = '0' * 64
                elif kind == 'score':
                    row['score'] = row['B2048']['score'] = -1.0
                else:
                    row['score'] = 1.0 - sc
            f.write(json.dumps(row) + '\n')
        if torn:
            f.write('{"status":')


checks = {}
ho = sorted(c for c, v in caps.items() if v['split'] == 'heldout')
tr = sorted(c for c, v in caps.items() if v['split'] == 'train')
# --- fit with every held-out journal replaced by garbage (interior malformed lines) and one torn train file ---
backup = W / 'ho_backup'
for sub in ('V', 'IY'):
    (backup / sub).mkdir(parents=True)
    for c in ho:
        p = J / sub / (A.slug(c) + '.jsonl')
        shutil.copy(p, backup / sub / p.name)
        p.write_text('garbage\n{"x": 1}\n')
torn_p = J / 'V' / (A.slug(tr[0]) + '.jsonl')
torn_orig = torn_p.read_bytes()
torn_p.write_bytes(torn_orig + b'{"arm":')
fits = []
for i in range(2):
    od = W / f'an{i}'
    r = subprocess.run(PY + ['--journals', str(J), '--out-dir', str(od)], capture_output=True, text=True)
    checks[f'fit{i}_ok'] = r.returncode == 0
    if r.returncode:
        print(r.stderr[-2000:])
    fits.append((od / 'FROZEN.json').read_bytes())
f0, f1 = json.loads(fits[0]), json.loads(fits[1])
checks['fit_ignores_heldout_and_deterministic'] = {k: v for k, v in f0.items() if k != 'frozen_utc'} == \
    {k: v for k, v in f1.items() if k != 'frozen_utc'}
checks['torn_tail_flagged'] = f0['problems'].get('incomplete_file') == [f'V/{tr[0]}']
checks['primary_is_V'] = f0['primary_arm'] == 'V'
train_rep = json.loads((W / 'an0/ANALYSIS_train.json').read_text())
train_caps = set(tr)
checks['no_heldout_in_fit_outputs'] = all(json.loads(l)['id'].split(':', 1)[1].rsplit(':', 1)[0] in train_caps
                                          for l in open(W / 'an0/ANALYSIS_train.items.jsonl'))
checks['train_has_no_decision'] = 'decision' not in train_rep
for sub in ('V', 'IY'):
    for c in ho:
        shutil.copy(backup / sub / (A.slug(c) + '.jsonl'), J / sub / (A.slug(c) + '.jsonl'))
torn_p.write_bytes(torn_orig)
# --- price: incomplete direct -> no decision; complete (with torn tail) -> decision; reproducible ---
write_direct(W / 'direct_drop.jsonl', drop=3)
r = subprocess.run(PY + ['--journals', str(J), '--out-dir', str(W / 'an0'), '--direct', str(W / 'direct_drop.jsonl'),
                         '--read-heldout'], capture_output=True, text=True)
d = json.loads((W / 'an0/ANALYSIS_heldout.json').read_text())['decision']
checks['incomplete_no_decision'] = r.returncode == 0 and d['status'] == 'incomplete' and d['head_path'] is None and d['missing'] == 3
write_direct(W / 'direct_bad.jsonl', bad=['binding', 'score', 'mismatch'])
r = subprocess.run(PY + ['--journals', str(J), '--out-dir', str(W / 'an0'), '--direct', str(W / 'direct_bad.jsonl'),
                         '--read-heldout'], capture_output=True, text=True)
rb = json.loads((W / 'an0/ANALYSIS_heldout.json').read_text())
checks['invalid_direct_rejected'] = rb['decision']['status'] == 'incomplete' and rb['decision']['missing'] == 3 and \
    rb['direct_rejected'] == dict(binding=1, score=2, unknown_item=1093)
write_direct(W / 'direct.jsonl', torn=True)
outs = []
for i in range(2):
    subprocess.run(PY + ['--journals', str(J), '--out-dir', str(W / 'an0'), '--direct', str(W / 'direct.jsonl'),
                         '--read-heldout'], check=True, capture_output=True)
    outs.append((W / 'an0/ANALYSIS_heldout.json').read_bytes())
checks['price_deterministic'] = outs[0] == outs[1]
rep = json.loads(outs[0])
s = rep['summary']
checks['decided'] = rep['decision']['status'] == 'decided' and rep['decision']['n'] == 143
checks['gt_app_100'] = abs(s['obj_appearance_order']['gt_program']['mean'] - 100.0) < 1e-9
dd = s['obj_appearance_order']['primary_head_minus_direct']
checks['boot_brackets_mean'] = dd['lo'] <= dd['mean'] <= dd['hi']
checks['head_beats_chance'] = rep['arms']['V']['first_seen_heldout']['head']['exact'] > 0.3
# --- unit: exact-match answer rule and tie-break ---
it = dict(objects=['a', 'b', 'c', 'd'], option_orders=[list('abdc'), list('acbd'), list('bacd'), list('dcba')])
z = dict(a=0, b=0, c=0, d=0)
checks['unmatched_is_none'] = A.answer_order(it, dict(a=1, b=2, c=3, d=4), z)[0] is None
checks['matched_letter'] = A.answer_order(it, dict(a=1, b=2, c=4, d=3), z)[0] == 'A'
checks['tie_break_expected'] = A.answer_order(it, dict(a=1, b=1, c=3, d=4), dict(a=2.0, b=1.0, c=0, d=0))[0] == 'C'
# --- price refuses a FROZEN.json from other code ---
fzp = W / 'an1/FROZEN.json'
g = json.loads(fzp.read_text()); g['code_sha256'] = '0' * 64; fzp.write_text(json.dumps(g))
r = subprocess.run(PY + ['--journals', str(J), '--out-dir', str(W / 'an1'), '--read-heldout'], capture_output=True, text=True)
checks['refuse_stale_frozen'] = r.returncode != 0 and 'refit' in (r.stderr + r.stdout)
print(json.dumps(dict(checks=checks, cv=f0['cv_train_exact'], decision=rep['decision'], app=s['obj_appearance_order'],
                      cnt_gt=s['object_counting']['gt_program'], timing=rep['timing']), indent=1))
(LANE / 'out/tests/ANALYSIS_SYNTH.json').write_text(json.dumps(dict(checks=checks, run=str(W),
                                                                    heldout_sha256=hashlib.sha256(outs[0]).hexdigest()), indent=1) + '\n')
print('PASS' if all(checks.values()) else 'FAIL')
