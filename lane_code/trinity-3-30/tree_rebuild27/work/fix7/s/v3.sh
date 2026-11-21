W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w29f7; cd $W
cat > $W/v3.py <<'PY'
import sys, json, os, glob, sqlite3
W=sys.argv[1]; T=W+'/t'; L=W+'/lists'
sys.dont_write_bytecode=True; sys.path.insert(0,T)
from student_pilot.p3_provenance import load, pinned
from student_pilot import r1_persisted
cfgp=json.load(open(W+'/cfgpart.json'))
paths={os.path.basename(p):p for p in glob.glob(L+'/*')}
B18='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/inputs/'
for p in glob.glob(B18+'*.json'): paths.setdefault(os.path.basename(p)[:-5],p)
out=json.load(open(W+'/out601.json')); nei=[o for o in out if o['cls']=='NEITHER']
c=sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(c.execute('SELECT row FROM rows WHERE i=?',(o['i'],)).fetchone()[0]) for o in nei]
with r1_persisted.scope(paths):
    from student_pilot.r1_rooms import Rooms
    ra=load(pinned(cfgp['ra'])); pins={k:{'path':paths.get(v['sha256'],v['path']),'sha256':v['sha256']} for k,v in ra['authority'].items()}
    rooms=Rooms(pins)
    b=json.load(open(paths['3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970']))
    pg=set(b['physical_groups']); bs=set(b['scenes']); bt={a+'/'+s for a,s in b['rung1_tokens']}
    seen={}
    for r in rows:
        s=r['dataset']+'/'+r['scene']
        if s in seen: continue
        st,can,how=rooms.status(r); room=rooms.room(can)
        seen[s]=1
        print('SCENEROOM',s,can,room,'status',st,'bench_group',room in pg,'bench_scene',('d3/'+can.split('/')[1]) in bs or can in bs,'bench_token',s in bt,'k1',room in rooms.k1,'r0',room in rooms.r0)
print('DONE')
PY
OMP_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python3 -I -B $W/v3.py $W 2>&1 | tail -30
echo ==== arm_launch.py; sed -n 1,200p /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/out/arm_launch.py
echo ==== ARM_LAUNCH_24M4Z11B.md; cat /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/out/ARM_LAUNCH_24M4Z11B.md
