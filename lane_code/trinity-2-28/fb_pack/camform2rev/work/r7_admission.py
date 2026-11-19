"""s1_admission.admit with a deferred config carrying camera_trace_form (child process; sets RLIMIT_AS).

Usage: r7_admission.py TREE
"""
from pathlib import Path
import sys, json, os
W = Path(__file__).resolve().parent
tree = sys.argv[1]
sys.path.insert(0, str(W/('tree_'+tree))); sys.dont_write_bytecode = True
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from student_pilot.p3_provenance import file_pin
from student_pilot import s1_admission
P = W/'probe'/('admit_'+tree); P.mkdir(parents=True)
cfg = {'r1_training': {'routing_slices': 'deferred_first_boundary', 'camera_trace_form': 'not-a-pin'}}
(P/'cfg.json').write_text(json.dumps(cfg))
out = P/'out'; out.mkdir()
try:
    s1_admission.admit(file_pin(P/'cfg.json'), out, [], threads=1, memory_gib=64)
    r = 'RETURNED'
except BaseException as e:
    r = type(e).__name__+':'+str(e)[:120]
created = sorted(str(p.relative_to(out)) for p in out.rglob('*'))
res = dict(tree=tree, outcome=r, created_under_output=created)
(W/('R7_ADMISSION_'+tree+'.json')).write_text(json.dumps(res, indent=1)); print(json.dumps(res))
