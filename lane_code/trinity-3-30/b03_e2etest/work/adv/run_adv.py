import json, sys
from pathlib import Path
from eat1 import run as R
from eat1.toy.adversarial import build_adversarial, EXPECT
W = Path(sys.argv[1]).resolve(); info = build_adversarial(W/'fx')
names = sys.argv[2:] or list(EXPECT)
for v in names:
    out = W/'runs'/v
    R.main(['--reader', 'eat1.toy.adversarial:make_reader', '--reader-kwargs', json.dumps(dict(workdir=str(W/'fx'), variant=v)),
            '--items', info['depth' if v == 'memo' else 'move'], '--out', str(out), '--allowlist-extra', 'eat1/toy/allowlist_toy.json',
            '--sandbox', '--perturb'])
    rep = json.loads((out/'EAT1_REPORT.json').read_text())
    st = {k: c['status'] for k, c in rep['clauses'].items()}
    ok = (rep['overall'] == 'PASS') if EXPECT[v] is None else st[EXPECT[v]] == 'FAIL'
    print('RESULT', v, 'OK' if ok else 'WRONG', rep['overall'], st, flush=True)
