from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
for name in ['INPUTS.json','proofs/census/CLASSIFIER.json','proofs/traces/INDEX.json','proofs/float/RESULT.json','proofs/preserve/RESULT.json','proofs/real/RESULT.json','CHANGED_COVERAGE.json','DELTA_COVERAGE.json','KIT_RESULT.json','SUITE_RUNS.json','proofs/operator/STAGING.json']:
    p=B/name
    if not p.exists():print(name,'ABSENT');continue
    x=json.loads(p.read_text())
    print(name)
    if name=='INPUTS.json':
        print(json.dumps({k:v for k,v in x.items() if k not in ('pins','hits','remove_rows')},indent=2)[:12000])
    elif name.endswith('STAGING.json'):print(type(x).__name__,list(x)[:12] if isinstance(x,dict) else len(x))
    elif name in ('CHANGED_COVERAGE.json','DELTA_COVERAGE.json'):print({k:v for k,v in x.items() if k not in ('files','statements','sources','coverage')})
    elif name=='KIT_RESULT.json':print({k:v.get('kit_sha256') for k,v in x.items()})
    else:print(json.dumps(x,indent=2)[:11000])
