from common import *
from decimal import Decimal
seen=start('verify.py')
build=load(ROOT/'out/BUILD.json');intakes=load(ROOT/'out/INTAKE.json');pin(SOURCE,build['source']['sha256']);pin(build['rows']['path'],build['rows']['sha256'])
from student_pilot.p3_provenance import digest
# Reuse sb_rowA's normalization and exact compiled distance filter unchanged.
sys.path.insert(0,str(SBA))
from fast_wording import near
from build_camera import normalized,THRESHOLD,digest as heldout_digest
for name in ['fast_wording.py','build_camera.py','wordings.py','wording_distance.cpp','out/wording_distance.so','build_camera_training.py']:
 pin(SBA/name)
held=load(SBA/'out/HELDOUT_CAMERA_ITEMS.json');wordings=load(SBA/'out/WORDINGS.json')
lineage={r['qid']:r for r in rows(SBA/'out/CAMERA_LINEAGE.jsonl')};pin(SBA/'out/CAMERA_LINEAGE.jsonl')
admissions={r['i']:r for r in rows(SBA/'out/SOURCE_ADMISSION.jsonl')};pin(SBA/'out/SOURCE_ADMISSION.jsonl')
# Frozen held-out file schema is inspected explicitly below.
twins=load(SBA/'out/HELDOUT_CAMERA_TWINS.json')
allheld=held['items'];item_by_id={r['id']:r for r in allheld}
heldrows=[item_by_id[t['reworded_id']] for t in twins['twins']]
assert len(allheld)==900 and len(heldrows)==450
for t in twins['twins']:
 for arm in ['original','reworded']:
  assert heldout_digest(item_by_id[t[arm+'_id']])==t[arm+'_item_sha256']
pin(SBA/'out/HELDOUT_CAMERA_ITEMS.json','2b90676111c229965d91132ad65b0f019703556c5934123fa0734bc6bffb3bdf')
pin(SBA/'out/HELDOUT_CAMERA_TWINS.json','5ec7e2a62e54f56a3bdc8f1de51f0a96d98dd14da8dd5326bc92618654f7b104')
pin(SBA/'out/WORDINGS.json','0b6f8eb3fe99a1ccb011195778e0ecec89dce90ff13f0b6d90321c85955d6b86')
heldquestions=[]
for r in heldrows:
 heldquestions.append(r.get('question') or r.get('student_input',{}).get('question') or r.get('question_text'))
assert len(heldquestions)==450 and all(isinstance(q,str) for q in heldquestions)
corpus=sorted(set(map(normalized,heldquestions)))
excluded={r['qid'] for r in intakes['refusals']};cells=Counter();admitted_cells=Counter();types=Counter();gt_errors=[];wording_hits=[];template_hits=[];unique=set();records=[];samples=defaultdict(list)
for old,new in zip(rows(SOURCE),rows(build['rows']['path']),strict=True):
 q=new['qid'];typ=new['routing']['question_type'];lin=lineage[q];t=lin['wording_id'];cell=typ+'|'+t
 assert lin['source_row_sha256']==admissions[lin['source_i']]['row_sha256'] and admissions[lin['source_i']]['keep']
 assert q==old['qid'] and q not in unique;unique.add(q);types[typ]+=1;cells[cell]+=1
 if q not in excluded:admitted_cells[cell]+=1
 assert digest(new)==build['row_bindings'][q]
 assert new['student_input']==old['student_input']
 for k in ['answer','gt_answer','gt_pose9','gt_up','candidate_id','source_row_sha256']:
  assert new['routing'][k]==old['routing'][k]
 for k in ['candidate_id','category','dataset','scene']:assert new[k]==old[k]
 # Strip only authorized changes and prove complete equality of all remaining fields.
 stripped=copy.deepcopy(new);stripped['target']=old['target'];stripped['routing']['tool_output_spans']=old['routing']['tool_output_spans']
 for a,b in zip(old['routing']['events'],stripped['routing']['events']):
  if a['kind'] in ('plan','canonical_text'):b['text']=a['text']
 if 'camera_trace_edit' in stripped.get('provenance',{}):
  stripped['provenance'].pop('camera_trace_edit')
  if not stripped['provenance']:stripped.pop('provenance')
 assert stripped==old,q
 for a,b in zip(old['routing']['tool_output_spans'],new['routing']['tool_output_spans']):
  assert old['target'][a['start']:a['end']]==new['target'][b['start']:b['end']]
 responses=[e['text'] for e in new['routing']['events'] if e['kind']=='tool_response'];assert len(responses)==1
 text=responses[0];rt=new['routing'];options=new['student_input']['options']
 if typ=='camera_displacement':
  val=re.search(r'distance = ([+-]?\d+\.\d+) m',text)[1];expected=val;detail=dict(printed_distance=val)
 elif typ=='camera_rotation':
  val=re.search(r'turn = ([+-]?\d+) deg',text)[1];expected=str(int(val));detail=dict(printed_turn=val)
 else:
  values={k:Decimal(v) for k,v in re.findall(r'(d[xyz]) = ([+-]?\d+\.\d+) m',text)}
  scores=dict(right=values['dx'],left=-values['dx'],up=values['dy'],down=-values['dy'],forward=values['dz'],backward=-values['dz'])
  labels=[re.sub(r'^[A-Z]\.\s*','',o).strip().casefold() for o in options]
  winner=max(range(len(labels)),key=lambda i:scores[labels[i]])
  expected=options[winner].split('.',1)[0];detail=dict(printed_components={k:str(v) for k,v in values.items()},scores={label:str(scores[label]) for label in labels},ties=[label for label in labels if scores[label]==scores[labels[winner]]],tie_rule='first option in printed order')
 if str(rt['answer'])!=expected or str(rt['gt_answer'])!=expected or new['target'].rsplit('</think>',1)[1].strip()!=expected:
  gt_errors.append(dict(qid=q,expected=expected,answer=rt['answer'],gt=rt['gt_answer'],detail=detail))
 hit=near(new['student_input']['question'],corpus)
 if hit:wording_hits.append(dict(qid=q,hit=hit))
 # Check all held-out templates instantiated with each row's exact frames/options, using the same filter.
 decision=next(e for e in rt['events'] if e['kind']=='decision');b=decision['binding']
 hc=[normalized(h.format(i=b['i'],j=b['j'],n=b['M'],unit='meters',options='; '.join(options))) for hs in wordings['heldout'].values() for h in hs]
 # near caches on id(corpus), so keep these per-row corpora alive until all calls finish.
 records.append(hc)
 hit=near(new['student_input']['question'],hc)
 if hit:template_hits.append(dict(qid=q,hit=hit))
 rule_ids=new.get('provenance',{}).get('camera_trace_edit',{}).get('rule_ids',[])
 key=typ+'|'+','.join(rule_ids)
 # Reservoir of deterministic examples across template IDs, with all trace bytes.
 samples[key].append(dict(qid=q,type=typ,template=t,rules=rule_ids,question=new['student_input']['question'],options=options,answer=rt['answer'],gt=rt['gt_answer'],before=old['target'],after=new['target'],recomputed=detail))
assert len(unique)==5979
capture(seen)
write('out/VERIFY.json',dict(rows=len(unique),types=types,unchanged_questions_answers_gt_calls_responses=len(unique),only_authorized_field_changes=len(unique),gt_recomputed=len(unique),gt_failures=gt_errors,wording_threshold=THRESHOLD,heldout_items=len(heldrows),normalized_heldout_wordings=len(corpus),wording_hits=wording_hits,instantiated_heldout_template_hits=template_hits,cells={k:dict(before_exclusions=cells[k],admitted=admitted_cells[k],refused=cells[k]-admitted_cells[k],short_of_50=50-admitted_cells[k]) for k in sorted(cells)},cells_short_of_50=sum(admitted_cells[k]<50 for k in cells)))
# Select 40 complete trace pairs, covering all types, both edit rules, and untouched direction cases.
selected=[]
for key,group in sorted(samples.items()):
 budget=12 if 'camera_displacement' in key else 12 if 'camera_rotation' in key else 12 if 'CAM-DIR' in key else 4
 ordered=sorted(group,key=lambda r:(r['template'],r['qid']))
 if len(ordered)<=budget:chosen=ordered
 else:chosen=[ordered[i*(len(ordered)-1)//(budget-1)] for i in range(budget)]
 selected.extend(chosen)
assert len(selected)==40,len(selected)
read=['# Forty camera trace pairs','All questions, options, calls, responses, answers and GT are unchanged. Complete targets appear below.']
for i,r in enumerate(selected,1):
 read.extend([f'\n## {i}. {r["qid"]}',f'Type: {r["type"]}; template: {r["template"]}; rules: {", ".join(r["rules"]) or "none"}.',f'Question: {r["question"]}',f'Options: {json.dumps(r["options"])}',f'Answer / GT: {r["answer"]} / {r["gt"]}',f'Printed-response recomputation: {json.dumps(r["recomputed"])}','\nBefore:\n```text\n'+r['before']+'\n```','\nAfter:\n```text\n'+r['after']+'\n```'])
(ROOT/'out/READ40.md').write_text('\n\n'.join(read)+'\n')
write('out/READ40_INDEX.json',dict(rows=selected,read40=pin(ROOT/'out/READ40.md'),count=40,scope='Complete before/after targets and unchanged question/options/answer/GT; frame arrays remain in the rows file.'))
status(4,f'All {len(unique)} rows retain questions, calls, responses, answers and GT. Printed-response GT mismatches: {len(gt_errors)}; held-out wording hits: {len(wording_hits)} actual items and {len(template_hits)} instantiated templates. All 120 cell counts and 40 complete trace pairs are written.')
assert not gt_errors and not wording_hits and not template_hits,(len(gt_errors),len(wording_hits),len(template_hits))
