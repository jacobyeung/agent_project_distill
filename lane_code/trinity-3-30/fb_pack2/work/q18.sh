cat > /tmp/fbp2_audit_point.py <<'PYEOF'
import json, sys, os, sqlite3, collections, inspect, hashlib
T = '/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1'
sys.path.insert(0, T)
RO = '/scratch/jjyeung/orch_n30/fb_pack/ro'
miss = set()
def m(x):
    if isinstance(x, dict): return {k: m(v) for k, v in x.items()}
    if isinstance(x, list): return [m(v) for v in x]
    if isinstance(x, str) and x.startswith('/scratch/') and not os.path.exists(x):
        y = RO + x[len('/scratch/jjyeung'):]
        if os.path.exists(y): return y
        miss.add(x)
    return x
cfgp = RO + '/orch_n30/tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json'
print('config sha', hashlib.sha256(open(cfgp, 'rb').read()).hexdigest()[:12])
cfg = m(json.load(open(cfgp)))
import student_pilot.s1_admission as adm
from student_pilot.row_removals import Removals
from student_pilot.r1_rooms import Rooms
import re as _re
_src=open(T+'/student_pilot/s1_admission.py').read()
print('import lines', [l for l in _src.splitlines() if 'Exclusions' in l and 'import' in l])
_mod=[l for l in _src.splitlines() if 'Exclusions' in l and 'import' in l][0].split('from')[1].split('import')[0].strip()
import importlib
Ex = getattr(importlib.import_module(_mod if not _mod.startswith('.') else 'student_pilot'+_mod), 'Exclusions')
print('keep sig', inspect.signature(Ex.keep))
print('streams.pointing', json.dumps(cfg['streams']['pointing'])[:300])
print('remove_files', [os.path.basename(p['path']) + ':' + p['sha256'][:8] for p in cfg['remove_files']])
print('missing paths', sorted(miss)[:20])
rooms = Rooms(cfg['r1_training']['room_authority'])
R = Removals(cfg['remove_files'])
E = Ex(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
db = '/scratch/jjyeung/orch_n30/fb_pack/in/pointing/rows_c09bb5ca.sqlite'
con = sqlite3.connect('file:' + db + '?mode=ro', uri=True)
cols = [r[1] for r in con.execute('PRAGMA table_info(rows)')]; print('cols', cols)
c = collections.Counter(); ex = []; k1r = collections.Counter()
r0=json.loads(con.execute('SELECT row FROM rows LIMIT 1').fetchone()[0]); print('row keys', {k:(str(v)[:80]) for k,v in r0.items()})
keepfn = getattr(E, 'keep', None)
for (raw,) in con.execute('SELECT row FROM rows ORDER BY i'):
    row = json.loads(raw)
    st, can, how = rooms.status(row)
    cs = (row.get('provenance') or {}).get('canonical_scene')
    if st == 'unresolved' and cs:
        rr = rooms.room(cs); st = 'r0' if rr in rooms.r0 else 'k1_heldout' if rr in rooms.k1 else 'ok'; can = cs
        if st == 'k1_heldout': k1r[rr] += 1
    gone = not R.keep(row)
    try:
        sx = (not keepfn(row, 'pointing')) if keepfn else 'NA'
    except Exception as e:
        sx = 'ERR:' + type(e).__name__ + ':' + str(e)[:60]
    c[(st, 'listed' if gone else 'kept', 'scene_excl' if sx is True else 'scene_ok' if sx is False else str(sx))] += 1
    if st == 'k1_heldout' and len(ex) < 6: ex.append((row.get('qid'), row.get('dataset'), row.get('scene'), can))
for k, v in sorted(c.items()): print(k, v)
print('k1 rooms', dict(k1r))
print('examples', ex)

PYEOF
cd /tmp && OMP_NUM_THREADS=4 nice -n 10 timeout 900 /scratch/jjyeung/envs/p1cpu/bin/python -B /tmp/fbp2_audit_point.py 2>&1 | tail -14
