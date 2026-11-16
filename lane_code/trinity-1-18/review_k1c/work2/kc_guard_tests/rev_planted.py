import copy,sys
from pathlib import Path
WORK=Path('/scratch/jjyeung/orch_n30/review_k1c/work2/kc_guard/k1_build/work/kit_k1a/work')
sys.path.insert(0,str(WORK))
import k1_pipeline as K
K._native();B=K.B
import k1_guard as guard
T=Path('/scratch/jjyeung/orch_n30/review_k1c/work2/kc_guard_tests')
m=B.load('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json')
c=copy.deepcopy(m['captures'][0])
c['rows']=[dict(id='refused-distance', type='object_abs_distance',question='Distance between chair and table?', operands=['chair', 'table'],
  unit='m', gt_value=1., fallback=dict(visual_evidence_verified=True,trace='The image shows a gap.', answer='1.00')),
  dict(id='refused-room', type='room_size_estimation', question='Room area?',operands=[], unit='m2', gt_value=10.)]
key=B.digest(c['canonical'])[:16]
dest=T/sys.argv[1]/'refusal'/key
if sys.argv[2]=='planted':
  raw,geo,r=K.cached(c,dest);print('planted', geo is None, guard.verdict(c), r['gravity_verdict'], sorted(r['files']))
for i in (range(3) if sys.argv[2]=='canary' else []):
    cc=m['captures'][i];raw,geo,r=K.cached(cc,T/'canary'/B.digest(cc['canonical'])[:16])
    print('canary',cc['canonical'],geo is not None,guard.verdict(cc))
print(guard.GG.report()['K1']['reviewed_refused'])
