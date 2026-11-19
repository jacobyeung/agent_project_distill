R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal4; date -u +%TZ; cd $R
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,hashlib
from pathlib import Path
R=Path('.')
st=json.load(open('states_fresh.json')); print('states', [(v['kind'],v['step'],v.get('passed')) for v in st])
m=R/'train/m2/artifact.json'; print('marker', m.exists())
if m.exists():
    d=hashlib.sha256(m.read_bytes()).hexdigest(); r=R/'train/persist'/(d+'.local.json'); print('receipt',r.exists())
    rc=json.load(open(r)) if r.exists() else {}
    print({k:rc.get(k) for k in ('durable','parts')}, rc.get('source',{}).get('sha256')==d, rc.get('archive',{}).get('sha256'))
done=R/'target/o/rehearsal/live/gcs_m2.done'; print('done', done.exists())
if done.exists(): print(json.load(open(done)))
PY
ls train | head -30 | tr '\n' ' '; echo; ls train/persist 2>/dev/null | head; find target -maxdepth 5 | head -20; ls live_spool | head; ls export_probe | head
grep -n -iE "copier|gcs_m|live" $R/../go_rehearsal.sh $R/../rehearsal_runner.py | head -20 | cut -c1-300
