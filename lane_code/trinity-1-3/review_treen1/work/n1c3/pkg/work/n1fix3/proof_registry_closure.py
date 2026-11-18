"""Execute staging/registry producers with source-fingerprinted statement monitoring."""
import ast,hashlib,json,os,sys,types
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';T=L/'work/tree_r1';O=B/'proofs/registry_closure'
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
from student_pilot.p3_provenance import file_pin,load
from student_pilot.r1_training import training_components
from student_pilot.r2_policy import slots,LINEAGE,EXTERNAL
from student_pilot.r1_loader import production_audit
from launch_r1.build import build,verify
from launch_r1.entry import admit
def write(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return file_pin(path)
records=[]
def case(name,fn):
    before=sum(inventory(L/'work/tmp').values());assert before<=200_000_000
    try:fn();result='PASS'
    except Exception as e:result=type(e).__name__+': '+str(e)
    after=sum(inventory(L/'work/tmp').values());assert after<=200_000_000
    records.append(dict(name=name,result=result,before_bytes=before,after_bytes=after))
def registry():
    root=O/'registry';root.mkdir(exist_ok=True)
    fixture=write(root/'fixture.json',{'synthetic_cpu_fixture':True});values=slots()
    for name in (*LINEAGE,*EXTERNAL,'data_rows_r2'):
        spec=values[name]
        value=dict(schema=spec['expected_schema'],component=name,component_class=spec['component_class'],phase=spec['phase'],inputs=[fixture],
            verdict='EXEMPT_FROZEN' if name in EXTERNAL else 'PROVEN_CLEAN',frozen=True,
            checked_banks=['VSI-Bench','VSTI','ReVSI'],overlaps=[],exclusions_complete=True)
        spec['record']=write(root/(name+'.json'),value)
    pin=write(root/'registry.json',values)
    actual=training_components(pin,{'geometry_connector':'none'})
    assert len(actual)==8 and 'heads_gf1_connector' not in actual
    try:training_components(pin,{'geometry_connector':'gf1'})
    except ValueError:pass
    else:raise AssertionError('fusion admitted')
    values['init_m544']['record']=None;pin=write(root/'registry.json',values)
    try:training_components(pin,{'geometry_connector':'none'})
    except ValueError:pass
    else:raise AssertionError('missing lineage admitted')
def kit():
    from student_pilot.source_seal import inventory as source_inventory
    from student_pilot.p3_provenance import digest
    root=O/('kit_'+digest(source_inventory(T))[:12])
    if root.exists():verify(root)
    else:
        result=build(B/'inputs/config.json',B/'inputs',root)
        assert result['GO'] is False and result['kit_sha256']==verify(root)
def refusals():
    cfg=load(B/'inputs/config.json')
    try:admit(cfg)
    except ValueError as e:assert 'processor_resolution_pin_missing' in str(e)
    else:raise AssertionError('unbound launch admitted')
    try:production_audit(cfg,O/'audit')
    except ValueError as e:assert 'FRAME_HOST' in str(e)
    else:raise AssertionError('local full store admitted')
case('registry_scope',registry);case('unbound_launch_and_local_full_store_refuse',refusals)
mon.set_events(4,0)
for name,value in [('source_hashes',snapshots),('hits',{k:sorted(v) for k,v in hits.items()}),
 ('results',dict(tests=len(records),passed=[r['name'] for r in records if r['result']=='PASS'],
  failures=[r for r in records if r['result']!='PASS'],errors=[],skips=[],complete=True,fatal=None,
  coverage_code_filter='compiled-source fingerprint',records=records))]:write(O/(name+'.json'),value)
print(json.dumps(records))
if any(r['result']!='PASS' for r in records):raise SystemExit(1)
