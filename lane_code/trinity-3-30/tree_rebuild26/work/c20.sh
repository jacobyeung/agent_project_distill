K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8/armed/kits/n_go
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$K" <<'PY'
import sys;sys.path.insert(0,sys.argv[1]+'/b');from z import load,screen
from pathlib import Path
K=Path(sys.argv[1]);w=load(K/'k/g.json');h=load(K/'b/wh.json')
print(type(w).__name__, (len(w) if hasattr(w,'__len__') else ''), type(h).__name__)
names=['mem.txt','df.txt','gate.txt','alarm.txt','live.json','t_q.log','t_q.steps','t_j2.log','t_j2.err','t_s.err','NOTES.txt','SHA256SUMS','population.json.gz','indices.json.gz','reader_filters.json.gz','binding.json.gz','receipt.json.gz','f.json.gz','174083_live','174083_gate','j6.py','jn6.sh','MEM_ALARM','OOM_EVENT','gate_copy','waiting_since','review.json']
for n in names:
    s=screen(n,w,h)
    if s!=n: print('SCREENED',n,'->',s)
print('checked',len(names))
PY
