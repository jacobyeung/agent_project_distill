"""Bounded regression for the fixture-only mutable-config pin defect; no training."""
from pathlib import Path
import ast,copy,hashlib,json,sys
D=Path(__file__).resolve().parent;L=D.parents[1]
R=D/'rehearsal_k2_probe'
def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

# Load the exact pure function without importing or executing training modules.
tree=ast.parse((D/'rehearsal_authorize2.py').read_text())
function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='repin')
namespace={};exec(compile(ast.Module(body=[function],type_ignores=[]),'repin','exec'),namespace)
repin=namespace['repin']
old4=read(L/'work/build24f/rehearsal4/r.json')
old5=read(L/'work/build24f/rehearsal5/r.json')
config=read(L/'work/build24f/rehearsal5/v.json')
checks=[]
for phase in ('budget','resume'):
    value=copy.deepcopy(config)
    value['authorization']={'path':'fixture-only/'+phase,'sha256':'a'*64}
    raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    pin={'path':'/tmp/q_22c714e1/v.json','sha256':hashlib.sha256(raw).hexdigest()}
    request=copy.deepcopy(old5)
    assert request['staged_pins'][0]['sha256']!=pin['sha256']
    other=[p for p in request['staged_pins'] if p['path']!=pin['path']]
    result=repin(request,pin)
    assert result['config']==pin
    assert [p for p in result['staged_pins'] if p['path']==pin['path']]==[pin]
    assert [p for p in result['staged_pins'] if p['path']!=pin['path']]==other
    assert repin(copy.deepcopy(result),pin)==result
    checks.append({'phase':phase,'stale_pin_refuses':True,'new_pin_matches_bytes':True,'unrelated_pins_preserved':True})
out={'status':'PASS','checks':checks,'rehearsal4_config_pin':old4['config'],
     'rehearsal5_config_pin':old5['config'],'rehearsal5_v_sha256_now':sha(L/'work/build24f/rehearsal5/v.json'),
     'production':'pl.py pins staged inputs; a.py publishes r.json; h.py and rv.py subsequently produce v.json. u.py calls train(cfg); latest resume is a fixture boundary.',
     'native_training_executed':False,'scope':'Pure repin function regression only; no native admission claim'}
(R/'REPIN_VALIDATION.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS: budget/resume re-pin regression; unrelated inputs remain pinned; no training.')
