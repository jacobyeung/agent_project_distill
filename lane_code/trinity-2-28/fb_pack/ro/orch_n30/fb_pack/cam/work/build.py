from common import *
seen=start('build.py')
from student_pilot.carrier_c1_routing import render
from student_pilot.p3_provenance import digest
source=pin(SOURCE)
for p in [SBA/'build_camera_training.py',SBA/'out/CAMERA_LINEAGE.jsonl',SBA/'out/SOURCE_ADMISSION.jsonl']:
 pin(p)
counts=Counter();reasons=Counter();forms=Counter();rules=Counter();changes=[];failures=[];examples={};bindings={};changed=0
out=ROOT/'out/rows/camera_wording.jsonl';out.parent.mkdir(exist_ok=True)
with out.open('w') as f:
 for old in rows(SOURCE):
  q=old['qid'];typ=old['routing']['question_type'];counts[typ]+=1
  errs=shared_errors(old)
  if errs:
   reason='Shared grammar: '+','.join(e.rule_id for e in errs);reasons[reason]+=1
   fs=sorted({form(e.line) for e in errs});assert 'UNCLASSIFIED' not in fs,(q,errs)
   for name in fs:forms[name]+=1
   failures.append(dict(qid=q,type=typ,reason=reason,forms=fs,violations=[e._asdict() for e in errs]))
   for e in errs:examples.setdefault(form(e.line),dict(qid=q,violation=e._asdict()))
  new=copy.deepcopy(old);applied=[];edits=[]
  for i,e in enumerate(new['routing']['events']):
   if e['kind'] not in ('plan','canonical_text'):continue
   before=e['text'];e['text'],ids=rewrite_text(before)
   if ids:
    applied.extend(ids);edits.append(dict(event_index=i,before=before,after=e['text'],rule_ids=ids))
  if applied:
   changed+=1;rules.update(set(applied))
   new['target'],spans=render(new['routing']['events'],new['routing']['answer'])
   assert len(spans)==len(new['routing']['tool_output_spans'])
   for stored,s in zip(new['routing']['tool_output_spans'],spans):stored.update(start=s['start'],end=s['end'])
   note=dict(rule_ids=sorted(set(applied)),source_file=source,source_qid=q,source_row_digest=digest(old),source_target_sha256=hashlib.sha256(old['target'].encode()).hexdigest(),scope='Uniform prose rewrite; calls, responses, question, options, answer and GT unchanged; response offsets regenerated.')
   new.setdefault('provenance',{})['camera_trace_edit']=note
   changes.append(dict(qid=q,rule_ids=note['rule_ids'],edits=edits))
  # This also executes the unmodified native replay and event/span checks.
  assert not shared_errors(new),(q,shared_errors(new))
  assert new['student_input']==old['student_input']
  for k in ['answer','gt_answer','gt_pose9','gt_up']:assert new['routing'][k]==old['routing'][k]
  for a,b in zip(old['routing']['events'],new['routing']['events']):
   if a['kind'] not in ('plan','canonical_text'):assert a==b
  assert re.findall(r'<tool_response>.*?</tool_response>',old['target'],re.S)==re.findall(r'<tool_response>.*?</tool_response>',new['target'],re.S)
  bindings[q]=digest(new)
  f.write(json.dumps(new,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n')
  if sum(counts.values())%1000==0:print('rows',sum(counts.values()),flush=True)
assert sum(counts.values())==5979 and len(bindings)==5979
capture(seen)
write('out/CLASSIFICATION.json',dict(source=source,rows=sum(counts.values()),types=counts,grammar_refusals=sum(reasons.values()),refusals_by_reason=reasons,refused_rows_by_form=forms,examples=examples,refusals=failures))
write('out/EDITS.json',dict(rules={'CAM-ROT-WORDS-v1':dict(before=ROT_OLD,after=ROT_NEW),'CAM-DIR-SYMBOL-v1':dict(pattern=NEG.pattern,replacement=r'\1',scope='Only Scoring each option by the matching component lines')},rows_changed=changed,rows_by_rule=rules,changes=changes))
write('out/BUILD.json',dict(rows=pin(out),count=sum(counts.values()),types=counts,changed=changed,unchanged=sum(counts.values())-changed,shared_grammar_pass=5979,row_bindings=bindings,source=source))
status(1,f'All 5,979 rows pass the pinned shared grammar and native replay. Uniform rules changed {changed} traces. Calls, printed responses, questions, options, answers and GT remain unchanged; response offsets and QID digests are regenerated.')
print(dict(reasons),dict(forms),dict(rules),flush=True)
