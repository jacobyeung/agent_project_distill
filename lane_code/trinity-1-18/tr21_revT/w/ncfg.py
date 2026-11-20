import json, base64
from pathlib import Path
L = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v')
def cap(p):
    v = json.loads(Path(p).read_text())
    return json.loads(base64.b64decode(v['payload'])) if isinstance(v, dict) and v.get('encoding') == 'base64-json' else v
for kit in ('out/kit_n_go', 'work/build24/kits/q', 'out/kit_qd'):
    c = cap(L/kit/'k/c.json'); t = c.get('r1_training') or {}
    print('==', kit, 'run_name', c.get('run_name'), c.get('vehicle'), c.get('name'))
    for k in ('routing_slices', 'row_sources', 'routing_inputs', 'proof_mode', 'stop_after_step', 'p_run', 'p_tree', 'mix', 'review', 'room_authority'):
        print('  r1_training.%s =' % k, json.dumps(t.get(k))[:220])
    print('  s1_routing', json.dumps(c.get('s1_routing'))[:200])
    print('  streams.routing', json.dumps((c.get('streams') or {}).get('routing'))[:200])
    print('  top keys', sorted(c.keys())[:80])
