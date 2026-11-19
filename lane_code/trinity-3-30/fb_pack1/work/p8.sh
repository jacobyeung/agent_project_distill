F=/scratch/jjyeung/orch_n30/fb_pack
cd $F && nice -n 10 env OMP_NUM_THREADS=4 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,gzip,collections
m={}
for l in gzip.open('in/pk/frame_map.jsonl.gz','rt'):
    r=json.loads(l); m[(r['d'],r['s'],r['i'])]=r['sha256']
print('map entries',len(m))
FR='/scratch/jjyeung/orch_n30/sb_fullinv/work/frames/'
allreq=set(); out={}
for n in ['recovery','absolute_distance','units','coverage_distance','coverage_units','camera_wording']:
    d=json.load(open(FR+n+'.json'))
    rows=d['rows']; req=set(); keys=set(rows[0].keys())
    for r in rows:
        st=r.get('scene_token'); 
        if st is None: continue
        dd,ss=st.split('/',1)
        for i in r.get('indices') or []: req.add((dd,ss,i))
    hit=sum(1 for k in req if k in m)
    out[n]=dict(rows=len(rows),req=len(req),in_map=hit,missing=len(req)-hit,keys=sorted(keys))
    allreq|=req
    print(n,out[n])
miss=[k for k in allreq if k not in m]
print('ALL req',len(allreq),'in map',len(allreq)-len(miss),'missing',len(miss), miss[:5])
json.dump(dict(per=out,all=len(allreq),missing=sorted(map(list,miss))),open('FRAME_COVERAGE.json','w'))
PY
