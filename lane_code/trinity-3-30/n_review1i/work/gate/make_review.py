#!/usr/bin/env python3
"""Write review.json for vehicle N's gate from a run_gate.sh output dir, only if gate.out ends GATE ALL PASS.
Usage: python3 -I make_review.py <run_gate out dir> <kit seal> <output review.json>
rv.py:290-297 accepts only keys verdict, config_identity, evidence (a dict); verdict must be PASS and
config_identity must equal the job's identity.txt. Install at X/n_r/review.json (dir 700, file 600) is n_ops10's."""
import hashlib, json, sys
from pathlib import Path

out, seal, dest = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
gate = (out / 'gate.out').read_text()
lines = [l for l in gate.splitlines() if l.startswith('GATE ')]
if not lines or lines[-1].split()[:3] != ['GATE', 'ALL', 'PASS']:
    sys.exit('gate.out does not end GATE ALL PASS; no review.json')
ids = sorted((out / 'x').rglob('identity.txt')); vs = sorted((out / 'x').rglob('v.json'))
if len(ids) != 1 or len(vs) != 1: sys.exit('need exactly one identity.txt and one v.json under x/, found %d and %d' % (len(ids), len(vs)))
ident = ids[0].read_text().strip()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
here = Path(__file__).resolve().parent
evidence = dict(gate_out_sha256=sha(out / 'gate.out'), gate_py_sha256=sha(here / 'gate.py'),
                v_json_sha256=sha(vs[0]), admit_sha256=sha(out / 'ADMIT.json'), kit_seal=seal,
                points=[l.split()[1] for l in lines[:-1]], reviewer='n_review1i')
raw = (json.dumps(dict(verdict='PASS', config_identity=ident, evidence=evidence), sort_keys=True) + '\n').encode()
dest.write_bytes(raw)
print(dest, len(raw), 'B sha256', hashlib.sha256(raw).hexdigest(), 'identity', ident)
