import offline_guard
from pathlib import Path
import json
import sys
from unittest.mock import patch
import uuid
ROOT=Path(__file__).resolve().parents[1]
K=ROOT/'kit'
for p in ('reader','reader/out','parity','proof'):sys.path.insert(0,str(K/p))
import fakes
fakes.install()
import prove_prompts
original=Path.read_text

def read(path,*args,**kwargs):
    text=original(path,*args,**kwargs)
    if path==K/'launcher/MODELS.json':
        v=json.loads(text);v['cp1m200']['sha256']='a'*64;return json.dumps(v)
    return text

with patch.object(Path,'read_text',read):
    result=prove_prompts.prove(ROOT/'evidence'/('parity_'+uuid.uuid4().hex),kit_root=K/'reader')
print(json.dumps(result))
