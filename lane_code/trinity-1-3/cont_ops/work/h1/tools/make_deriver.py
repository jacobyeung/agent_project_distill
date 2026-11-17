"""Build the stdlib deriver from the retained base and the selection equality gate."""
import hashlib, json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
s=(H/'evidence/fix7_before/tools/derive_kit_h1.py').read_text()
raw=json.loads((H/'evidence/derivation/d0/k/pool_selection.json').read_text())
base=json.loads((H/'payload/d_f232d4160d75b582.json').read_text())
# The native closure was measured by the local CPU audit and is pinned as data.
impl=json.loads((H/'evidence/fix7_selection/implementation.json').read_text())
inputs=json.loads((H/'evidence/fix7_selection/inputs.json').read_text())
constants=dict(SELECTION_REFERENCE=sha(H/'payload/d_f232d4160d75b582.json'),
 SELECTION_RAW_REFERENCE=sha(H/'evidence/derivation/d0/k/pool_selection.json'),
 SELECTION_CONTENT=digest({k:v for k,v in base.items() if k!='implementation'}),
 SELECTION_RAW_CONTENT=digest({k:v for k,v in raw.items() if k!='implementation'}),
 SELECTION_IMPLEMENTATION=digest(impl),SELECTION_TOOL=sha(H/'tools/selection_check.py'),
 SELECTION_INDICES={n:dict(equal=True,sha256=v['selection']['sha256'],count=v['retained']) for n,v in raw['sources'].items() if 'selection' in v},
 SELECTION_INPUT_SIZES={v['sha256']:v['bytes'] for v in inputs})
helper='\n'.join(k+' = '+repr(v) for k,v in constants.items())+'\n'+(H/'tools/selection_guard.py').read_text()
s=s.replace("'e00_listing', 'code_tree'}", "'e00_listing', 'code_tree', 'selection_equality'}")
s=s.replace("ADD_K = {'review.json', 'staging.json', '4.json'}", "ADD_K = {'review.json', 'staging.json', '4.json', 'selection_equality.json'}")
s=s.replace('def derive(kit, out, over):',helper+'\n\ndef derive(kit, out, over):')
s=s.replace('    validate_h1(over)\n','    validate_h1(over)\n    validate_selection_equality(over)\n')
for name in ('tools/derive_kit_h1.py','payload/d.py'):(H/name).write_text(s)
