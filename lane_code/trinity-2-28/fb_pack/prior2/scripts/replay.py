"""Real direction extract in an explicitly synthetic full-card harness; never production proof."""
import sys,os,json,sqlite3,hashlib,math,random,importlib.util
from pathlib import Path
from collections import Counter
W=Path(__file__).resolve().parents[1];T=W/'work/new';sys.path.insert(0,str(T))
from student_pilot import r1_mix as M
from student_pilot import p3_provenance as P
from student_pilot.r1_direction_prior import Prior
from student_pilot.r1_loader import DirectionAudit
from student_pilot.r1_direction_twins import dimensions
from student_pilot.r1_training import STREAMS
root=W/'work/replay_delivery';root.mkdir(parents=True,exist_ok=True)
inputs=[]
def track(p):
 pin=P.file_pin(p);inputs.append(pin);return pin
def put(name,value):
 p=root/name;p.write_text(P.encoded(dict(value,inputs=list(inputs)))+'\n');return P.file_pin(p)
cardpin=track(W/'work/recovered/card.json');card=P.load(cardpin['path']);track(W/'out/WEIGHT_BUILD.json')
build=P.load(W/'out/WEIGHT_BUILD.json');dbpin=track(build['database']['path']);assert dbpin==build['database']
weightpin=track(W/'out/TOWARD_HARD_WEIGHTS.json');assert weightpin==build['weights'];track(__file__)
for name in ('r1_mix.py','r1_loader.py','r1_direction_prior.py','r1_direction_twins.py','r1_population.py','p3_provenance.py'):
 track(T/'student_pilot'/name)
track(W/'work/base/student_pilot/r1_mix.py');track(W/'work/base/student_pilot/r1_direction_twins.py');track(W/'work/base/student_pilot/r1_loader.py')
track(W/'out/BASE_SEAL.json');track(W/'out/FILES_TOUCHED.json')
conn=sqlite3.connect(Path(dbpin['path']).as_uri()+'?mode=ro&immutable=1',uri=True)
groups={c['type']:[] for c in card['cells']};rows={};prior=Prior(weightpin);metadata={}
for i,raw,kind in conn.execute('SELECT i,row,cell FROM rows ORDER BY i'):
 row=json.loads(raw);rows[i]=row;groups[kind].append(i);prior.observe(row,'vqa',kind,i);metadata[i]=dimensions(row)
conn.close()
# Synthetic offsets only support unrelated cells in this harness. They certify nothing about
# the actual missing populations or manifests and are never emitted as a production config.
next_offset=Counter(vqa=len(rows))
for cell in card['cells']:
 k,s=cell['type'],cell['stream']
 if k in ('direction','facing_pairs'):continue
 n=math.ceil(float(cell['rows_per_step'])*250)
 groups[k]=list(range(next_offset[s],next_offset[s]+n));next_offset[s]+=n
counts={k:len(v) for k,v in groups.items()}
evidence=put('fixture.json',dict(scope='SYNTHETIC_OTHER_CELLS_WITH_AUTHENTICATED_DIRECTION_EXTRACT',production_proof='MISSING',reason='Missing N removal lists, room inputs and non-VQA source populations. No production manifest is synthesized.'))
pop=put('population.json',dict(schema='r1-population-v1',complete=True,after_all_filters=True,card_sha256=cardpin['sha256'],counts=counts,evidence=[evidence],scope='UNIT_TEST_FIXTURE_ONLY'))
indices=put('indices.json',dict(population_sha256=pop['sha256'],cells=groups,scope='UNIT_TEST_FIXTURE_ONLY'))
binding=dict(schema='r1-sampling-v1',card=cardpin,population=pop,indices=indices)
bound=prior.bind(binding,root/'direction_prior.json');enabled=dict(binding,direction_prior=bound)
put('binding_fixture.json',enabled)
spec=importlib.util.spec_from_file_location('student_pilot.base_mix',W/'work/base/student_pilot/r1_mix.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
base=list(B.plans(binding,dict(next_offset),1000));absent=list(M.plans(binding,dict(next_offset),1000));after=list(M.plans(enabled,dict(next_offset),1000))
assert P.encoded(base)==P.encoded(absent)
ownership={(c['stream'],i):c['type'] for c in card['cells'] for i in groups[c['type']]}
sequence={label:{k:[] for k in groups} for label in ('base','absent','enabled')};audits={};maxrepeats={};totals={}
for label,plans in [('base',base),('absent',absent),('enabled',after)]:
 audit=DirectionAudit();repeats=Counter();cellcounts=Counter()
 for row in rows.values():audit.eligible(row)
 for plan in plans:
  for stream,offsets in plan:
   for i in offsets:
    kind=ownership[stream,i];sequence[label][kind].append(i);repeats[stream,i]+=1;cellcounts[kind]+=1
    if stream=='vqa' and i in rows:audit.observe(rows[i])
 audits[label]=audit.result();maxrepeats[label]=max(repeats.values());totals[label]=dict(cellcounts)
 assert maxrepeats[label]<=4
changed=Counter();unchanged_positions=Counter()
for old,new in zip(base,after):
 for (s,oi),(t,ni) in zip(old,new):
  assert s==t
  for a,b in zip(oi,ni):
   k=ownership[s,a];assert k==ownership[s,b]
   if s=='vqa' and a in metadata and metadata[a][:2]==('toward','hard'):
    assert metadata[b][:2]==('toward','hard');changed[k]+=a!=b
   else:assert a==b;unchanged_positions[k]+=1
for label in ('absent','enabled'):
 assert totals[label]==totals['base']
for kind in groups:
 if kind not in ('direction','facing_pairs'):assert sequence['enabled'][kind]==sequence['base'][kind]
base_groups={(r['clause'],r['difficulty']):r for r in audits['base']['answer_shares']}
after_groups={(r['clause'],r['difficulty']):r for r in audits['enabled']['answer_shares']}
for key in base_groups:
 if key!=('toward','hard'):assert base_groups[key]==after_groups[key]
assert base_groups['toward','hard']['draws']==after_groups['toward','hard']['draws']
assert abs(after_groups['toward','hard']['back']['share']-.5)<.001
assert after[723:]==list(M.plans(enabled,dict(next_offset),1000,start_step=723))
# Base ignores the optional field; demonstrate why the production change is necessary.
base_enabled=list(B.plans(enabled,dict(next_offset),1000));assert base_enabled==base
bad=root/'tampered_weights.json';bad.write_bytes(Path(weightpin['path']).read_bytes()+b' ')
bad_bound=P.load(bound['path']);bad_bound['policy']=dict(weightpin,path=str(bad));bad_pin=put('tampered_bound.json',bad_bound)
tampered=dict(binding,direction_prior=bad_pin)
base_tampered=list(B.plans(tampered,dict(next_offset),1));assert base_tampered==base[:1]
try:next(M.plans(tampered,dict(next_offset),1));raise AssertionError('tamper accepted')
except ValueError as e:tamper_error=str(e)
# Compare the full corrected parser to the sealed parser on the authenticated rows.
spec=importlib.util.spec_from_file_location('student_pilot.base_twins',W/'work/base/student_pilot/r1_direction_twins.py');BT=importlib.util.module_from_spec(spec);spec.loader.exec_module(BT)
parser_disagree=sum(BT.dimensions(row)[0]!=metadata[i][0] for i,row in rows.items());assert parser_disagree==23121
# Isolate the facing-pair omission in the actual production audit entrypoint.
# Host/preparation/reader are test doubles; actual authenticated source rows are used.
from unittest.mock import patch
from student_pilot import carrier_c1_run as C, r1_loader as L
spec=importlib.util.spec_from_file_location('student_pilot.base_loader',W/'work/base/student_pilot/r1_loader.py');BL=importlib.util.module_from_spec(spec);spec.loader.exec_module(BL)
chosen=[groups['direction'][0],groups['facing_pairs'][0]]
class AuditReader:
 def count(self,stream):return next_offset[stream]
 def row(self,stream,i):return rows[i],{}
 def close(self):pass
cfg=dict(r2_sampling=binding,r1_training=dict(row_plan_sha256=P.digest(binding)))
audit_counts={}
for label,module in [('base',BL),('new',L)]:
 with patch('os.uname',return_value=type('Host',(),dict(nodename='fixture-host'))()), patch.object(C,'prepared',return_value=({},None)), patch.object(C,'Rows',return_value=AuditReader()), patch.object(M,'plans',return_value=[[('vqa',chosen)]]):
  result=module.production_audit(cfg,root/('audit_inclusion_'+label))
 audit_counts[label]=sum(r['draws'] for r in result['direction']['answer_shares'])
assert audit_counts=={'base':1,'new':2}
cells={k:dict(draws=len(sequence['base'][k]),base_sha256=P.digest(sequence['base'][k]),absent_sha256=P.digest(sequence['absent'][k]),enabled_sha256=P.digest(sequence['enabled'][k])) for k in groups}
# Bind every imported local code dependency, including the loader audit entrypoint.
tracked={p['path'] for p in inputs}
for module in list(sys.modules.values()):
 path=getattr(module,'__file__',None)
 if path and Path(path).is_relative_to(T) and Path(path).is_file() and str(Path(path)) not in tracked:
  track(path);tracked.add(str(Path(path)))
record={'status':'DIAGNOSTIC_PASS_PRODUCTION_MISSING','production_population_test':'MISSING','scope':'N card and authenticated direction/facing_pairs extract; all other offsets are explicitly synthetic harness data, not N population evidence.','seed':card['seed'],'first_1000_steps_equals_full_schedule':card['steps']==1000,'first_1000_steps':audits,'full_schedule':{'same_as':'first_1000_steps','steps':1000},'cells':cells,'max_repeats':maxrepeats,'changed_toward_hard_draws':dict(changed),'unchanged_other_positions':dict(unchanged_positions),'parser_clause_corrections':parser_disagree,'production_audit_inclusion_fixture':audit_counts,'base_negative_controls':{'facing_pairs':'FAIL: base audit reports only one of the two actual drawn source rows','balance':'FAIL: optional field ignored','tamper':'FAIL: altered weight file ignored','parser':'FAIL: 23121 clause mismatches'},'new_tamper_refusal':tamper_error,'absent_plan_sha256':P.digest(absent),'base_plan_sha256':P.digest(base),'enabled_plan_sha256':P.digest(after),'inputs':inputs+[pop,indices,bound]}
(W/'out/CENSUS_LOADER.json').write_text(json.dumps(record,indent=2)+'\n')
summary={label:{'/'.join(k):v['back']['share'] for k,v in {(r['clause'],r['difficulty']):r for r in audit['answer_shares']}.items()} for label,audit in audits.items()}
print(json.dumps({'shares':summary,'max_repeats':maxrepeats,'changed':dict(changed),'cells':{k:v['draws'] for k,v in cells.items()}},indent=2),flush=True)
(W/'STATUS.md').write_text('The authenticated direction replay passes: toward-hard slots are balanced, every other diagnostic draw stays identical, and the four-draw cap and tamper refusal pass. The diagnostic uses N’s exact card but synthetic support offsets for unavailable cells; it does not satisfy the production all-cell gate. Full CPU base/new comparison and packaging remain in progress.\n')
