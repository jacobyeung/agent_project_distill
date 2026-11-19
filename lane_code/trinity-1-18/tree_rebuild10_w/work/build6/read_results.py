import collections,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
for folder in sys.argv[1:]:
    p=B/'proofs'/folder/'results.json'
    if not p.exists():print(folder,'pending');continue
    value=json.loads(p.read_text())
    if 'tests' in value:
        print(folder,json.dumps({k:len(v) if isinstance(v,list) else v for k,v in value.items() if k not in ('groups',)}))
        for name,error in value['errors']+value['failures']:print(name,error[-2200:])
    else:
        print(folder,dict(collections.Counter(r['outcome'] for r in value.values())))
        groups={}
        for name,r in value.items():
            if r['outcome']=='failed':groups.setdefault(r['detail'].splitlines()[-1],[]).append(name)
        print(json.dumps(groups,indent=2))
