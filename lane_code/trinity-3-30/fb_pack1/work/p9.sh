cd /scratch/jjyeung/orch_n30/fb_pack && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,gzip
m={}
for l in gzip.open('in/pk/frame_map.jsonl.gz','rt'):
    r=json.loads(l); m[(r['d'],r['s'],r['i'])]=r['sha256']
d=json.load(open('/scratch/jjyeung/orch_n30/sb_fullinv/work/frames/camera_wording.json'))
print({k:(v if not isinstance(v,(list,dict)) else type(v).__name__) for k,v in d.items()})
r0=d['rows'][0]; print(json.dumps(r0)[:700])
same=diff=nos=0; ex=[]
for r in d['rows']:
    dd,ss=r['scene_token'].split('/',1)
    fr=r['frames']
    for i,f in zip(r['indices'],fr):
        sh=f.get('sha256') if isinstance(f,dict) else None
        if sh is None: nos+=1; continue
        if m.get((dd,ss,i))==sh: same+=1
        else:
            diff+=1
            if len(ex)<3: ex.append((dd,ss,i,sh,m.get((dd,ss,i)),f))
print('camera frame refs same-as-k6tk',same,'diff',diff,'nosha',nos); print(ex)
PY
