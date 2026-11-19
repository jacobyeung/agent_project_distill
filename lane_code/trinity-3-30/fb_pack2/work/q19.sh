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
c = collections.Counter(); ex = []; k1r = collections.Counter(); held = []
r0=json.loads(con.execute('SELECT row FROM rows LIMIT 1').fetchone()[0]); print('row keys', {k:(str(v)[:80]) for k,v in r0.items()})
keepfn = getattr(E, 'keep', None)
for (raw,) in con.execute('SELECT row FROM rows ORDER BY i'):
    row = json.loads(raw)
    st, can, how = rooms.status(row)
    cs = (row.get('provenance') or {}).get('canonical_scene')
    if st == 'unresolved' and cs:
        rr = rooms.room(cs); st = 'r0' if rr in rooms.r0 else 'k1_heldout' if rr in rooms.k1 else 'ok'; can = cs
        if st == 'k1_heldout': k1r[rr] += 1; held.append(dict(row_key=row['qid'], reason='k1_heldout_pointing', canonical=cs, room=rr))
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


O='/scratch/jjyeung/orch_n30/fb_pack/k1point'; os.makedirs(O, exist_ok=True)
L=O+'/REMOVE_POINTING_K1_HELDOUT.jsonl'
open(L,'w').write(''.join(json.dumps(r, sort_keys=True)+'\n' for r in sorted(held, key=lambda r: r['row_key'])))
h=hashlib.sha256(open(L,'rb').read()).hexdigest(); print('LIST', L, len(held), h)
print('remove_0 first line', open(cfg['remove_files'][0]['path']).readline()[:200])
R2=Removals(list(cfg['remove_files'])+[dict(path=L, sha256=h)])
E2=Ex(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
c2=collections.Counter()
for (raw,) in con.execute('SELECT row FROM rows ORDER BY i'):
    row=json.loads(raw); cs=(row.get('provenance') or {}).get('canonical_scene'); rr=rooms.room(cs)
    st='r0' if rr in rooms.r0 else 'k1_heldout' if rr in rooms.k1 else 'ok'
    k=R2.keep(row); s=E2.keep(row,'pointing') if k else None
    c2[(st, 'listed' if not k else 'kept', 'scene_ok' if s else 'scene_excl' if s is False else '-')]+=1
print('WITH LIST', sorted(c2.items()))
json.dump(dict(store='c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938', config='0e78d7f8', list=dict(path=L, sha256=h, rows=len(held)), rooms=dict(k1r), before={str(k):v for k,v in c.items()}, after={str(k):v for k,v in c2.items()}, tree='57a1f14d', script='fb_pack2/work/audit_point.py'), open(O+'/AUDIT_POINTING_K1.json','w'), indent=1)
print('AUDIT', hashlib.sha256(open(O+'/AUDIT_POINTING_K1.json','rb').read()).hexdigest())
PYEOF
cd /tmp && OMP_NUM_THREADS=4 nice -n 10 timeout 900 /scratch/jjyeung/envs/p1cpu/bin/python -B /tmp/fbp2_audit_point.py 2>&1 | tail -12
cp /tmp/fbp2_audit_point.py /scratch/jjyeung/orch_n30/fb_pack/k1point/audit_point.py; sha256sum /scratch/jjyeung/orch_n30/fb_pack/k1point/*
