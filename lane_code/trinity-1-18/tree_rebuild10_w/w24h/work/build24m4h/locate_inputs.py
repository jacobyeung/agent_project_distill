import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
x=J.load(D/'CONFIG_INPUTS.json');m=J.load(input_file(x['manifest']['sha256']))
a=J.load(W/'w24/work/build24m2c/PIN_AUDIT.json')['available']
for k,v in m['exclusions'].items():
 if isinstance(v,dict):
  for key,h in v.items():
   if key.endswith('_sha256'):
    print(k,key,h,'available',a.get(h))
p=D/'common.py';s=p.read_text().replace('W/"work/conf23d/pkg/work/build21/upload/u")','W/"work/conf23d/pkg/work/build21/upload/u",W/"w24/work/build24m3/hidden/inputs",W/"w24/work/build24m3/hidden/payload")')
s=s.replace(' raise ValueError("LOCAL_INPUT_MISSING:"+h)', ''' a=J.load(W/'w24/work/build24m2c/PIN_AUDIT.json')['available']
 if h in a:
  p=Path(a[h])
  if p.is_file() and J.sha(p)==h:return p
 raise ValueError("LOCAL_INPUT_MISSING:"+h)''')
replace(p,s)
