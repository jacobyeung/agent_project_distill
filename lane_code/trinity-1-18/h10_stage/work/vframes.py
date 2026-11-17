import json,hashlib,os,sys
from pathlib import Path
R=Path('/scratch/jjyeung/devs1_frames')
X=Path('xa/b/work/meta/x/sj/orch_cd')
need={}
for f in [X/'legs1_reads/work/vendor/r3/FRAMES.json', X/'evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json']:
    d=json.load(open(f))
    n=0
    for c in d['captures']:
        for fr in c['frames']:
            p=fr['path']
            if p in need and need[p]!=fr['sha256']: sys.exit('conflict '+p)
            need[p]=fr['sha256']; n+=1
    print(f.name,len(d['captures']),n)
have={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file()}
print('need',len(need),'have',len(have),'missing',len(set(need)-have),'extra',len(have-set(need)))
bad=0
for p,h in need.items():
    if p in have and hashlib.sha256((R/p).read_bytes()).hexdigest()!=h: bad+=1
print('bad',bad)
open('frames_list.txt','w').write('\n'.join(sorted(need))+'\n')
