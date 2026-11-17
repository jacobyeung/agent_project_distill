"""Execute staging/registry producers with source-fingerprinted statement monitoring."""
import ast,hashlib,json,os,sys,types
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build_n1';T=L/'work/tree_r1';O=B/'proofs/p_format'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(B)]
from compact_tmp import inventory
# Reuse the copied runner's code-object fingerprint algorithm verbatim.
parsed=ast.parse((B/'test_runner.py').read_text())
node=next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='code_digest')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(B/'test_runner.py'),'exec'))
snapshots={};expected={};hits={}
for p in T.rglob('*.py'):
    if set(p.relative_to(T).parts)&{'artifacts','__pycache__','.git'}:continue
    raw=p.read_bytes();snapshots[str(p.relative_to(T))]=hashlib.sha256(raw).hexdigest()
    try:pending=[compile(raw,str(p),'exec',dont_inherit=True)]
    except SyntaxError:continue
    expected[str(p)]=set()
    while pending:
        code=pending.pop();expected[str(p)].add(code_digest(code));pending.extend(v for v in code.co_consts if isinstance(v,types.CodeType))
mon=sys.monitoring;mon.use_tool_id(4,'r1-proof')
def started(code,offset):
    if code.co_filename in expected and code_digest(code) in expected[code.co_filename]:mon.set_local_events(4,code,mon.events.LINE)
    return mon.DISABLE
def line(code,number):
    hits.setdefault(str(Path(code.co_filename).relative_to(T)),set()).add(number);return mon.DISABLE
mon.register_callback(4,mon.events.PY_START,started);mon.register_callback(4,mon.events.LINE,line);mon.set_events(4,mon.events.PY_START)
from copy import deepcopy
from unittest.mock import patch
import torch
from student_pilot.p3_provenance import file_pin,load
from student_pilot import carrier_c1_run as native,r1_training as contract
from student_pilot.decoupled_v import learning_rate
from tests.test_carrier_c1 import fixture
before=sum(inventory(L/'work/tmp').values());assert before<=200_000_000
model,_,_=fixture(4)
destination=O/'m200'
donor=dict(base_identity='fixture',trace_program_version='3.13')
if not destination.exists():
    with patch.object(native.dist,'get_rank',return_value=0),patch.object(native.dist,'get_world_size',return_value=1),patch.object(native.dist,'barrier'),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
        native.export(destination,model,model,donor,200)
pin=file_pin(destination/'artifact.json');artifact=load(pin['path'])
assert artifact['schema']=='carrier-c1-artifact-v1' and 'r1_progress' not in artifact
fresh,_,_=fixture(4);native.load_artifact(fresh,pin)
for name,tensor in fresh.state_dict().items():
    torch.testing.assert_close(tensor,model.state_dict()[name].to(tensor.dtype),rtol=0,atol=0)
cfg=load(B/'inputs/config.json');cfg['init_artifact']={'artifact':pin}
cfg['r1_training'].update(continuation_identity='a'*64,row_plan_sha256='c'*64,
    store_hashes={s:'b'*64 for s in contract.STREAMS},donor_config_sha256=artifact['config_sha256'])
try:contract.start(cfg)
except ValueError as error:assert 'PROGRESS_RECEIPT_MISSING' in str(error)
else:raise AssertionError('P export without progress was admitted')
progress=dict(contract.boundary(cfg,200),artifact_sha256=pin['sha256'])
(O/'boundary.json').write_text(json.dumps(progress,sort_keys=True,indent=2)+'\n')
cfg['r1_training']['continuation_receipt']=file_pin(O/'boundary.json')
assert contract.start(cfg)==200
for key,value in [('donor_config_sha256','d'*64),('continuation_identity','d'*64),('row_plan_sha256','d'*64),('store_hashes',{s:'d'*64 for s in contract.STREAMS})]:
    bad=deepcopy(cfg);bad['r1_training'][key]=value
    try:contract.start(bad)
    except ValueError as error:assert 'P_EXPORT_' in str(error)
    else:raise AssertionError('Mismatched P boundary was admitted: '+key)
bad=dict(progress,artifact_sha256='d'*64)
(O/'bad_boundary.json').write_text(json.dumps(bad)+'\n')
wrong=deepcopy(cfg);wrong['r1_training']['continuation_receipt']=file_pin(O/'bad_boundary.json')
try:contract.start(wrong)
except ValueError as error:assert 'ARTIFACT_MISMATCH' in str(error)
else:raise AssertionError('Foreign artifact boundary was admitted')
recipe=native.recipe_for(cfg);lr=learning_rate(contract.start(cfg)+1,recipe)
assert lr==learning_rate(201,recipe)
after=sum(inventory(L/'work/tmp').values());assert after<=200_000_000
mon.set_events(4,0)
result=dict(artifact=pin,format_has_inline_progress=False,sidecar=file_pin(O/'boundary.json'),
    absolute_step=200,next_lr_step=201,learning_rate=lr,reader_loaded=True,
    mismatches_refused=['donor config','continuation config','store','row plan','artifact'],
    scope='Synthetic metadata and tiny native weights; no real P export or production identity claimed.',
    stand_ins='Seeded tiny native model replaces pretrained GPU weights; local stand-ins cover FSDP publication and rank/barrier collectives. Native export without R1 extensions, native artifact reader, tensor reload, sidecar authentication, progress checks and LR functions execute unchanged.',
    before_bytes=before,after_bytes=after)
for name,value in [('RESULT',result),('source_hashes',snapshots),('hits',{k:sorted(v) for k,v in hits.items()}),
 ('results',dict(tests=1,passed=['native_P_format_with_bound_sidecar'],failures=[],errors=[],skips=[],complete=True,fatal=None,coverage_code_filter='compiled-source fingerprint'))]:
    (O/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(result))
