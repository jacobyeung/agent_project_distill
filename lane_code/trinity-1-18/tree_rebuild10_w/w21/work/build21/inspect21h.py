from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';W=L.parent
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.p3_provenance import load,pinned
c=J.load(B/'kits/q/k/n.json')
for key in ('extent_receipt','scene_coverage','s1_routing'):
    v=c.get(key)
    if key=='s1_routing':v={k:x for k,x in v.items() if k!='catalog'}
    print(key,json.dumps(v))
for key in ('row_sources','source_membership','room_authority'):
    print(key,json.dumps(c['r1_training'].get(key)))
s=load(pinned(c['r1_training']['row_sources']))
for name,v in s.items():
    print('SOURCE',name,json.dumps(v))
    if name in ('recovery','absolute_distance','units','coverage_units','coverage_distance'):
        p=pinned(v['source'])
        with p.open() as f:r=json.loads(next(f))
        print('ROW',name,json.dumps({k:v for k,v in r.items() if k in ('qid','dataset','scene','canonical','provenance','frames_pending','student_input','frame_indices')})[:1800])
for p in (W/'inputs/p_runtime').glob('*.json'):
    v=J.load(p)
    print('P',p.name,'r1_training',bool(v.get('r1_training')),'keys',list(v)[:12])
    if 'streams' in v:print('P_STREAMS',json.dumps(v['streams']))
r=J.load(W/'ext/m400real/r.json');c=J.load(W/'ext/m400real'/('files'+r['config']['path']))
print('REAL_P','r1_training' in c,'s1_routing' in c,json.dumps(c['streams']))
print('REQUEST',json.dumps(J.load(B/'kits/q/k/r.json'))[:4000])
