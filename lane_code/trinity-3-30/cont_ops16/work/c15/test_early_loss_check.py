import json, subprocess, sys, tempfile, os
T = tempfile.mkdtemp(); PY = sys.executable; JOB = '170001'
src = [json.loads(l) for l in open('nm/source_metrics_23_rows.jsonl')]
base = json.load(open('BASELINE_ROWS_520_544.json'))
def row(step, sm=None, from_=None):
    r = json.loads(json.dumps(from_ or src[0])); r['step'] = step
    for k in r['ranks']:
        k['step'] = step; k['skipped_microsteps'] = []
        if sm: k['stream_means'].update(sm)
    return r
good = {s: b['sm'] for s, b in zip((545, 546, 547), [x for x in base if x['step'] in (542, 543, 544)])}
att_ok = dict(first_step=545, resume=dict(path='/x/runs/469ddece/checkpoint_000544_16d2a80ac22a411f8442277a87b53738/complete.json', sha256='0450e3a3c0265131175d4751329eba9f4605a5f391450a0c98b4e6fdefddc31c'))
def run(rows, att=att_ok, tail=b''):
    m, a = os.path.join(T, 'metrics_170001.jsonl'), os.path.join(T, 'attempt_170001.json')
    with open(m, 'wb') as f:
        for r in rows: f.write((json.dumps(r) if isinstance(r, dict) else r).encode() + b'\n')
        f.write(tail)
    if att is None:
        if os.path.exists(a): os.replace(a, a + '.gone')
    else: json.dump(att, open(a, 'w'))
    p = subprocess.run([PY, '-I', 'early_loss_check.py', JOB, m, a], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)['verdict']
cases = {
 'good 545-547': ([row(s, good[s]) for s in (545, 546, 547)], (0, 'PASS')),
 'cold start relabeled': ([row(545 + i, from_=src[i]) for i in range(3)], (2, 'ALARM')),
 'steps 548-550': ([row(s, good[545]) for s in (548, 549, 550)], (2, 'ALARM')),
 'gap 545,547,548': ([row(s, good[545]) for s in (545, 547, 548)], (2, 'ALARM')),
 'duplicate 545': ([row(545, good[545]), row(545, good[545]), row(546, good[546])], (2, 'ALARM')),
 'order 547,545,546': ([row(s, good[545]) for s in (547, 545, 546)], (2, 'ALARM')),
 'missing step key': ([{k: v for k, v in row(545, good[545]).items() if k != 'step'}], (2, 'ALARM')),
 'one valid + partial tail': ([row(545, good[545])], (3, 'PENDING')),
 'two valid': ([row(s, good[s]) for s in (545, 546)], (3, 'PENDING')),
 'empty': ([], (3, 'PENDING')),
 'nonfinite': ([row(545, dict(vqa=float('nan')))], (2, 'ALARM')),
}
fails = 0
for name, (rows, want) in cases.items():
    tail = b'{"step": 547, "ranks": [' if name == 'one valid + partial tail' else b''
    got = run(rows, tail=tail)
    fails += got != want; print('OK ' if got == want else 'BAD', name, got)
for name, att, want in (('wrong resume pin', dict(first_step=545, resume=dict(path='/x/checkpoint_000600_aa/complete.json')), (2, 'ALARM')),
                        ('first_step 1', dict(first_step=1, resume=None), (2, 'ALARM')),
                        ('attempt missing with rows', None, (2, 'ALARM')),
                        ('pin sha right, path wrong', dict(first_step=545, resume=dict(path='/x/checkpoint_000600_aa/complete.json', sha256='0450e3a3c0265131175d4751329eba9f4605a5f391450a0c98b4e6fdefddc31c', note='checkpoint_000544_16d2a80ac22a411f8442277a87b53738')), (2, 'ALARM')),
                        ('pin as string', dict(first_step=545, resume='checkpoint_000544_16d2a80ac22a411f8442277a87b53738'), (2, 'ALARM')),
                        ('attempt not object', [1, 2], (2, 'ALARM'))):
    got = run([row(s, good[s]) for s in (545, 546, 547)], att=att); fails += got != want; print('OK ' if got == want else 'BAD', name, got)
# malformed rows and wrong job file names
got = run(['{"step": 545, "ranks": [1, 2, 3, 4]}']); fails += got != (2, 'ALARM'); print('OK ' if got == (2, 'ALARM') else 'BAD', 'ranks not objects', got)
got = run(['[1, 2]']); fails += got != (2, 'ALARM'); print('OK ' if got == (2, 'ALARM') else 'BAD', 'row not object', got)
p = subprocess.run([PY, '-I', 'early_loss_check.py', '999', os.path.join(T, 'metrics_170001.jsonl'), os.path.join(T, 'attempt_170001.json')], capture_output=True, text=True)
fails += p.returncode != 2; print('OK ' if p.returncode == 2 else 'BAD', 'wrong job id', p.returncode)
print('FAILS', fails); sys.exit(1 if fails else 0)
