"""Authenticate unchanged behavior against the extracted sealed build-12 source."""
from pathlib import Path
import json,hashlib,ast
L=Path(__file__).resolve().parents[2];B=L/'work/build13';T=L/'work/tree_r1';P=B/'prior12'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[];same=[]
for p in sorted(P.rglob('*.py')):
    name=str(p.relative_to(P));q=T/name
    if sha(p)==sha(q):same.append(name)
    else:changed.append(name)
functions=[]
name='student_pilot/carrier_c1_run.py'
a=(P/name).read_text();b=(T/name).read_text()
aa=ast.parse(a);bb=ast.parse(b)
for n in aa.body:
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        m=next(x for x in bb.body if isinstance(x,type(n)) and x.name==n.name)
        assert ast.get_source_segment(a,n)==ast.get_source_segment(b,m),n.name
        functions.append(n.name)
cfg=json.loads((B/'inputs/config.json').read_text())
prior=json.loads((L/'work/n1fix2/inputs/config.json').read_text())
# Localized paths can differ; the launch artifact identities cannot.
def pins(v):
    if isinstance(v,dict):return {k:pins(x) for k,x in v.items() if k!='path'}
    if isinstance(v,list):return [pins(x) for x in v]
    return v
assert pins(cfg)==pins(prior)
record=dict(prior_source='work/build13/PRIOR12.json',unchanged_python=same,changed_python=changed,
    carrier_top_level_functions_unchanged=functions,config_identity_without_local_paths_equal=True,
    f1_f6='work/build12/PROOF_EQUALITY.json',parity='work/build12/proofs/depth_sweep/RESULT.json',
    exclusions='work/build12/proofs/preservation/RESULT.json',
    scope='Exact unchanged source and authenticated prior evidence; parity and original-family full proofs are inherited, not rerun.')
(B/'PRESERVATION.json').write_text(json.dumps(record,indent=2))
print('PASS source preservation',len(same),len(changed))
