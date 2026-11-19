import re,json,collections
import route as R
from route import ROOT,TREE,BASE,load,pin,rows,write
R.COMMAND=R.PREFIX+'work/diagnose.py'
pin(__file__);pin(ROOT/'work/route.py')
from student_pilot.r2_adapters import normalize
from student_pilot.r2_grammar import legacy_program,shared
from student_pilot.r1_coverage import source_names,EXTRA_PINS
results=load(ROOT/'out/INTAKE_RESULTS.json');acc=load(ROOT/'out/EXCLUSION_ACCOUNTING.json')
output={}
for name in ['recovery','camera_wording','camera_B']:
 failures={}
 for shard in results['slices'][name]['shards']:
  report=load(shard['result']['report']['path']);failures.update({r['qid']:r['reason'] for r in report['refusals']})
 types=collections.defaultdict(collections.Counter);examples={};recovery_probes=collections.Counter()
 for raw in rows(acc['slices'][name]['rows']['path']):
  why=failures.get(raw['qid'])
  if not why:continue
  kind=raw.get('question_type',raw.get('type',raw.get('routing',{}).get('question_type','routing')));types[kind][why]+=1
  if name=='recovery' and 'fallback' in why:
   events=raw['ground_record']['events'];failed=None
   for i,e in enumerate(events):
    if re.search(r'not seen|failed|no linked candidate',e['response'],re.I):failed=i;break
   subsequent=[e['call'] for e in events[failed+1:]]
   recovery_probes['rows']+=1
   recovery_probes['subsequent_call_different_from_failed']+=all(c!=events[failed]['call'] for c in subsequent)
  if why in examples:continue
  ex=dict(qid=raw['qid'],question_type=kind,source=acc['slices'][name]['rows'],refusal=why)
  if name.startswith('camera') and why.startswith('Shared grammar:'):
   row=normalize(raw);target,spans=legacy_program(row);body=re.search(r'<think>(.*?)</think>',target,re.S).group(1);body=re.sub(r'Call: measure ','I will measure ',body)
   for e in row['events']:
    if e['kind'] in ('ground_call','tool_call','calculator_call'):body=body.replace(e['token'].strip(),'<call>')
   errs=shared.validate_trace(body,form='program',question=row['question'],n_frames=len(row['student_input']['frames']))
   ex['grammar_diagnostics']=[vars(e) if hasattr(e,'__dict__') else str(e) for e in errs]
  elif name=='recovery' and 'fallback' in why:ex['calls']=raw['ground_record']['events']
  examples[why]=ex
 output[name]=dict(refusals_by_question_type=types,examples=examples,recovery_probe_check=dict(recovery_probes))
write('out/BLOCKER_DIAGNOSTICS.json',dict(slices=output,tree_actions=[dict(owner='tree_rebuild and recovery contract owner',path=str(TREE/'student_pilot/r2_contract.py'),line=248,required='Resolve the conflict between the sealed two-operand recovery events and the blanket refusal of every call after the first failed response. All observed later calls name a different operand. Do not fabricate a receipt or silently bypass the guard.'),dict(owner='tree_rebuild and camera source owner',path=str(TREE/'student_pilot/r2_grammar.py'),line=183,shared_path=str(TREE/'student_pilot/trace_grammar.py'),shared_lines=[502,509],required='Make the sealed camera event rendering/adaptation satisfy the pinned a41ba191 shared grammar, or regenerate authenticated camera source rows and their bindings. Existing movement prose has signed arithmetic quantities; turn prose introduces range constants and units not accepted by this grammar. No shared validator edit was made.'),dict(owner='tree_rebuild',path=str(TREE/'student_pilot/r1_coverage.py'),line=190,required='Bind the selected filtered camera source hash in EXTRA_PINS, update first-boundary source/catalog/config/request pins, and reseal. source_names already includes camera_wording at lines 135-141; adding it again is unnecessary.')],camera_family_present='camera_wording' in source_names({n:{} for n in R.NAMES}),camera_pinned_source=EXTRA_PINS['camera_wording']))
print(json.dumps({k:dict(v['refusals_by_question_type']) for k,v in output.items()}),flush=True)
