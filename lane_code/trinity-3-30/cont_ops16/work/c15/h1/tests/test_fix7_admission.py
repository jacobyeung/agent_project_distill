"""Native CPU routing beyond the stale binding, in isolated test-only directories."""
import contextlib,copy,json,sys,tempfile,traceback
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(H/'tests'),str(H/'tools'),str(H/'build/tree'),str(H/'build/fx/b')]
from fix7_fixtures import pool_fixture,routing_fixture,Processor,write,load,file_pin
from student_pilot import s1_pool,s1_routing,carrier_c1_run as run,h1_faithful,h1_r0,s1_exclusions,source_seal
import selection_check as sc
out=Path(tempfile.mkdtemp(prefix='audit_',dir=H/'evidence/fix7_admission'));results={}
def record(name,fn,expected=None):
 try:value=fn()
 except Exception as exc:
  if expected is None or expected not in str(exc):raise
  results[name]=dict(status='EXPECTED REFUSAL',message=str(exc),type=type(exc).__name__)
  return None
 else:
  assert expected is None,'expected refusal: '+name
  results[name]=dict(status='PASS',detail=value)
  return value
# Exercise the unchanged regenerated production selection bytes. Relocation and
# the model descriptor alone remain fixtures because production rows are absent.
launch=load(H/'build/fx/k/launch.json')
prod=load(H/'build/fx'/launch['config']['file'])
actual_path=H/'payload/d_eac5f9f01587803b.json'
actual=load(actual_path)
assert actual['implementation']==s1_pool.implementation()
assets=out/'assets';assets.mkdir();(assets/'tokenizer.json').write_text('{}\n')
write(out/'model.json',dict(kind='base',root=str(assets)))
# Existing production rows prevent relocation itself. Supply only its copied receipt
# to isolate the next native conditional; no content-bearing row function is mocked.
from student_pilot import s1_pool_relocate
from student_pilot import s1_route_policy
from student_pilot.p3_provenance import pinned
def policy_pin(pin):
 if pin==prod['s1_route_policy']['table']:
  return pinned(dict(path=str(H/'build/fx/k/routes.json'),sha256=pin['sha256']))
 return pinned(pin)
lines=set()
def trace(frame,event,arg):
 if frame.f_code.co_filename==s1_routing.__file__ and frame.f_code.co_name=='build' and event=='line':lines.add(frame.f_lineno)
 return trace
with patch.object(s1_pool_relocate,'relocate',return_value={'relocated':file_pin(actual_path)}),patch.object(s1_route_policy,'pinned',side_effect=policy_pin):
 sys.settrace(trace)
 try:record('production_after_215',lambda:s1_routing.build(prod,out/'production',{},file_pin(out/'model.json')),
            'Missing or changed pinned input')
 finally:sys.settrace(None)
assert 219 in lines,lines
results['production_after_215']['executed_lines']=sorted(lines)
results['production_after_215']['limits']='Real pinned selection, isolated relocation result and model manifest; real legacy receipt is missing. No production row materialization claimed.'
# Native prepare and relocation on small generated sensor-room and direct rows.
f=out/'synthetic';f.mkdir()
with (out/'native.log').open('x') as log,contextlib.redirect_stdout(log):
 selection,packed,direct=pool_fixture(f)
 cfg,division,model=routing_fixture(f,selection)
 # Supply an explicit character tokenizer; native training_text/suffix_mask still run.
 # Production processor, opener IDs and production token budgets remain untested.
 with patch.object(run,'processor_for_receipt',return_value=Processor()):
  routed=s1_routing.build(cfg,f/'routing',division,model)
 assert routed['count']==2
 report=load(routed['materialization']['path']);assert report['status']=='PASS' and not report['blockers']
 results['synthetic_build']=dict(status='PASS',count=routed['count'],types=routed['types'],
  limits='Synthetic room/direct rows, empty legacy DB, character processor; no RGB bytes or production tokenizer tested.')
 # Refuse later contracts individually, preserving one output directory per attempt.
 def build_variant(tag,change,expected):
  c=copy.deepcopy(cfg);d=division;change(c)
  with patch.object(run,'processor_for_receipt',return_value=Processor()):
   record(tag,lambda:s1_routing.build(c,f/tag,d,model),expected)
 bad=copy.deepcopy(selection);bad['blockers']=['synthetic'];write(f/'blocked.json',bad)
 build_variant('scene_blocker',lambda c:c['s1_routing'].update(selection=file_pin(f/'blocked.json')),'Routing pool scene integrity is blocked')
 legacy=load(f/'legacy.json');legacy['scene_role']='heldout';write(f/'heldout.json',legacy)
 build_variant('division_guard',lambda c:c['streams'].update(routing=file_pin(f/'heldout.json')),'native training division')
 legacy['scene_role']='train';legacy['count']=1;write(f/'bad_count.json',legacy)
 build_variant('legacy_count_guard',lambda c:c['streams'].update(routing=file_pin(f/'bad_count.json')),'Legacy routing count differs')
 build_variant('suffix_budget_guard',lambda c:c['recipe'].update(max_routing_suffix_tokens=1),'S1 routing materialization is blocked')
 # Real preparation checks that do not require missing production streams/models.
 filtered=dict(routing=dict(kind='rows',database=routed['database'],count=routed['count'],receipt=file_pin(f/'routing/receipt.json')))
 rule=s1_exclusions.Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
 scene=s1_exclusions.coverage_report(rule,filtered)
 record('scene_totals',lambda:s1_exclusions.totals(report['source_scene_exclusions'],rule))
 settings=copy.deepcopy(prod);settings['streams']['routing']=file_pin(f/'routing/receipt.json');settings['preparation_output']=str(f/'faithful')
 record('faithful_gate_zero_camera_rows',lambda:h1_faithful.prepare_identity(dict(streams=filtered),settings),
        'faithful identity >= 95%')
 reserve=h1_r0.prepare(dict(streams=filtered),settings)
 h1_r0.before_admission(reserve,settings)
 results['reserve_prepare_and_before_admission']=dict(status='PASS',report=reserve['h1_r0'])
 wrong=copy.deepcopy(reserve);wrong['h1_r0']['per_stream']['routing']['retained']+=1
 record('reserve_accounting_guard',lambda:h1_r0.before_admission(wrong,settings),'selections or accounting differ')
 code=load(H/'payload/7.json');seal=source_seal.binding(code,run.identity(prod))
 record('source_seal',lambda:source_seal.check_binding(seal,code,run.identity(prod)))
 bad=copy.deepcopy(seal);bad['config_sha256']='0'*64
 record('source_seal_guard',lambda:source_seal.check_binding(bad,code,run.identity(prod)),'differs')
results['not_tested']=dict(status='NOT RUN',checks=[
 'Full production relocation: all 13 source gzip files unavailable locally; Orchard equality report is pinned.',
 'Production legacy receipt/database, division contents and compatibility samples, real processor/base-model/token IDs.',
 'Production frame map/plan resolution against all rows, duplication/order/filter accounting and source census/coverage.',
 'Parent model/grounding and warm-start artifacts; pointing/VQA rebuilds; full carrier_c1_run.prepare and prepared.',
 'Faithful camera identity >=95% on real camera rows; reserve population counts and nonempty streams on production data.',
 'Complete data_receipt/phase journal publication, RGB byte audit, b/d.effective equality, CPU first batch.',
 'GPU allocation/model/init/FSDP/process groups/optimizer/first-step finite-loss gates; milestone gate disabled for this run.'])
(out/'results.json').write_text(json.dumps(results,indent=2,default=str)+'\n')
(H/'evidence/fix7_admission/latest.json').write_text(json.dumps(dict(path=str(out),results=results),indent=2,default=str)+'\n')
print(out)
