F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f
cd $F/rehearsal4/train
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'P'
import json,glob,os
for f in sorted(glob.glob('run_*.json')):
    v=json.load(open(f)); print(f,{k:v.get(k) for k in v if k!='steps'})
for f in sorted(glob.glob('attempt_*.json')):
    v=json.load(open(f)); print(f,json.dumps({k:v[k] for k in v if k not in('binding','init')})[:600])
for d in sorted(glob.glob('checkpoint_*'))+sorted(glob.glob('_superseded/*')):
    c=os.path.join(d,'complete.json')
    if os.path.exists(c): v=json.load(open(c)); print(d,json.dumps({k:v[k] for k in v if k not in('files','shards','tensors')})[:500])
    else: print(d, os.listdir(d)[:8])
for d in sorted(glob.glob('m*')):
    if os.path.isdir(d): print(d, sorted(os.listdir(d))[:6])
P
cd $F/rehearsal5; cat CHECK.json STAGES.json RUN_REFUSAL.json COPIER_SOURCE.json | head -c 5000
