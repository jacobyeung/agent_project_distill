"""Inspect the real-mode FOV_RESULT from the producer-format tree: labels, provenance status, P5 totals and pin coverage."""
import json
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/crev/work')
r = json.loads((W / 'real_full/FOV_RESULT.json').read_text())
pre = json.loads((W / 'real_full/PREFLIGHT.json').read_text())
pins = r['input_sha256']
probe = str(W / 'tree/in/own_544_fov/native/probe')
print({k: r[k] for k in ('choice', 'synthetic', 'decision_usable', 'captures', 'pairs', 'distance_captures', 'distance_items')})
pc = r['provenance_checks']
print('provenance status', pc['status'], pc['checked'], pc['skipped'], 'P5', pc['P5_anchor_match'])
print('preflight', pre['status'], pre['decision_usable'])
per = {n: sum(1 for p in pins if p.startswith(probe) and p.endswith(n)) for n in ('fov.npz', 'FOV_RECEIPT.json', 'PHASE_COMPLETE.json')}
print('per-capture pins', per)
need = ['/scratch/jjyeung/orch_n30/fb_pack/fov/build3/score_fov.py', '/scratch/jjyeung/orch_n30/fb_pack/fov/BARS_FOV_544.json',
        '/scratch/jjyeung/orch_n30/fb_pack/fov/BARS_FOV_544_AMEND1.json', str(W / 'tree/in/own_544_fov/k1fwd2/FOV_CHECK.json'),
        '/scratch/jjyeung/orch_n30/sb_own400/out/BARS_FROZEN.json', '/scratch/jjyeung/orch_n30/sb_own400/kit/inputs/G3T_FOV.json',
        '/scratch/jjyeung/orch_n30/sb_own400/kit/score_400.py', '/scratch/jjyeung/orch_n30/sb_own400/kit/core.py']
print('required pins present', {Path(p).name: p in pins for p in need})
print('score_fov pin', pins.get(need[0]))
print('criteria', {a: {k: v['pass'] for k, v in c.items() if isinstance(v, dict)} for a, c in r['criteria'].items()})
print('heldout rows', sum(1 for x in json.loads(Path(need[3]).read_text())['rows'] if not x['scored']), 'no dirs under probe')
