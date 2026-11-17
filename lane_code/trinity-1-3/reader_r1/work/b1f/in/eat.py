import sys,json
from collections import Counter
sys.path.insert(0,'/scratch/jjyeung/orch_n30/reader_r1/work/b1/in')
from eat1 import scan as S
allow=S.load_allowlist()
files=['b/e2e_reader/grounding.py','b/e2e_reader/servers.py','b/e2e_reader/stage1.py','h1eval/h10/perception_own.py','h1eval/perception.py','b/e2e_reader/real.py','b/e2e_reader/parity.py']
def key(d):
    return (d["file"].split("/")[-1], d.get("function"), d["rule"], d["detail"])
def _unused(f):
    d=f if isinstance(f,dict) else f.__dict__
    return (d.get('path','').split('/')[-1] if 'path' in d else d.get('file',''), d.get('function'), d.get('rule'), d.get('detail'))
res={}
for side in ('old','new'):
    fs,_=S.scan([f'{side}/{x}' for x in files],allow=allow,root=side)
    res[side]=Counter(key(f) for f in fs)
    print(side,len(fs))
print('added',list((res['new']-res['old']).elements()))
print('removed',list((res['old']-res['new']).elements()))
