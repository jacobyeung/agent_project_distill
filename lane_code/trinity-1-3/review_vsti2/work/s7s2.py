import sys,json,os,tempfile
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_vsti2/work/c')
from datetime import datetime,timezone
import budget as Bm
D='2026-11-16T16:15:00Z';Dt=Bm.timestamp(D)
def t(s):return datetime.fromtimestamp(s,timezone.utc).strftime('%H:%M:%S')
res={}
# outer (o.py) budget at job start 11:05Z
now=[Bm.timestamp('2026-11-16T11:05:00Z')]
outer=Bm.Budget(D,clock=lambda:now[0])
gpu_left=21600
rem=min(outer.remaining(),gpu_left)
res['outer_kill']=t(now[0]+rem);res['worker_deadline']=outer.worker_deadline(rem)
# inner worker budget with that deadline
for rates in ([],[('camera_displacement',7),('obj_obj_relative_pos_lr',60)],[('obj_obj_relative_pos_lr',300)]):
    clk=[0];b=Bm.Budget(res['worker_deadline'],clock=lambda:clk[0])
    for k,v in rates:b.observe(k,v)
    cut=b.item_cutoff()
    cases={}
    for off in (-1,0,1):
        clk[0]=cut+off;cases[t(clk[0])]=b.allows('obj_obj_relative_pos_lr')
    res[str(rates)]=dict(cutoff=t(cut),kill=t(b.deadline-b.return_seconds),slack_after_max_item=b.deadline-b.return_seconds-cut-b.max_item_seconds(),allows=cases)
# GPU cap binding case: job starts 10:00Z, gpu cap 6h-> 16:00Z < D-600
now[0]=Bm.timestamp('2026-11-16T10:30:00Z');gs=now[0]-(21600-19800)  # pretend 30 min GPU elapsed
rem=min(outer.remaining(),21600-1800)
res['capcase']=dict(kill=t(now[0]+rem),worker_deadline=outer.worker_deadline(rem))
clk=[0];b=Bm.Budget(res['capcase']['worker_deadline'],clock=lambda:clk[0]);res['capcase']['cutoff']=t(b.item_cutoff());res['capcase']['inner_kill']=t(b.deadline-b.return_seconds)
# S2: run_phase on a failing proof and failing read
import o
d=Path(tempfile.mkdtemp(dir='/scratch/jjyeung/orch_n30/review_vsti2/work'));(d/'p').mkdir()
with open(d/'log','w') as s:
    rc=o.run_phase([sys.executable,'-c','import sys;sys.exit(3)'],'/x/p.py',d,dict(os.environ),s,30)
    res['s2_proof_fail']=dict(rc=rc,receipt=json.load(open(d/'p/PROOF.json')))
    rc=o.run_phase([sys.executable,'-c','import time;time.sleep(5)'],'/x/p.py',d,dict(os.environ),s,1)
    res['s2_proof_timeout']=json.load(open(d/'p/PROOF.json'))['error']
    try:o.run_phase([sys.executable,'-c','import sys;sys.exit(3)'],'/x/a.py',d,dict(os.environ),s,30);res['s2_read_fail']='no raise'
    except Exception as e:res['s2_read_fail']=repr(e)
print(json.dumps(res,indent=1))
