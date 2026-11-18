from pathlib import Path
from collections import defaultdict
import json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build10';N=L
prior=json.loads((N/'w9f/work/build9fix/proofs/suite_tree/results.json').read_text())
current=json.loads((L/'work/build12/proofs/suite_tree/legacy/results.json').read_text())
def key(name):return re.sub(r"(['\"])[^'\"]*/work/tmp/[^'\"]*\1","'<temporary path>'",name)
old=defaultdict(set)
for name,error in prior['errors']+prior['failures']:old[key(name)].add(error.strip().splitlines()[-1])
rows=[]
for name,error in current['errors']+current['failures']:
    last=error.strip().splitlines()[-1]
    if last not in old.get(key(name),set()):rows.append(dict(test=name,last=last,prior=sorted(old.get(key(name),set())),traceback=error))
(L/'work/build12/proofs/suite_tree/PRIOR_DIAGNOSTIC.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='traceback'} for r in rows],indent=2))
