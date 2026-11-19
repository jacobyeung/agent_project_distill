from pathlib import Path
import json
P=Path('/scratch/jjyeung/orch_n30/r1_ops/work/adm171377')
for p in P.glob('prepare_9b0c4b095487492a80bd5e9030d5bbc0/*/receipt.json'):
    d=json.loads(p.read_text());print(str(p),{k:d[k] for k in ('schema','count','streams') if k in d and k!='streams'})
    for k,v in d.get('streams',{}).items():print(k,{a:v[a] for a in ('kind','count','source_count','sources') if a in v})
p=Path('/scratch/jjyeung/orch_n30/r1_pkt/work/derive_7fh23bg8/b/k/8957d119.json')
if p.is_file():
    d=json.loads(p.read_text());print('pose schema',d.get('schema'),'keys',list(d))
