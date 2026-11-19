"""Generate the explicit feasible mix; fail if any declared cell is short.

The geometry and trace rules are room_v314 sensor and codeF/room_v4.
Image bindings come from exact-pin, non-excluded rows already in store v7.
Run: PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python generate.py
"""
import copy,json,hashlib,collections,sys
from pathlib import Path
from census import W,BASE,TREE,INPUTS,reg,sha,dump,rules,status
from wording import QUESTIONS
from student_pilot import r2_adapters,r2_contract,trace_grammar
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
CELLS={'scannet|10-20':12,'scannetpp|10-20':12,'scannet|20-40':8,'scannetpp|20-40':16,'scannet|40-60':2,'scannetpp|40-60':10,'scannet|60-100':2,'scannetpp|60-100':8,'scannetpp|>=100':2}
def digest(x):return hashlib.sha256(x.encode()).hexdigest()
def cell(e):
 a=e['measurement']['area_m2'];return e['canonical'].split('/')[0]+'|'+('10-20' if 10<=a<20 else e['band'])
def target(trace,qid,answer):
 lm=trace['landmarks'];rv=(int(digest(qid),16)//2)%2
 locate='Seen: '+'; '.join(x['label']+' in frame '+str(x['best_view']) for x in lm)+'.'
 rel=trace['relate'];a,c=[lm[j]['label'] for j in rel['pair']]
 line=[f'Of these, the {a} and the {c} are farthest apart',f'The {a} and the {c} are the farthest apart among these landmarks'][rv]
 if 'third' in rel:
  b=lm[rel['third']]['label'];line+=f', with the {b} '+('between them' if rel['decision']=='between' else ['off to the side','to the side of that pair'][rv])
 return '<think>\nThe question asks for the combined floor area in square meters.\n'+locate+'\n'+line+'.\n</think>\n\n'+answer

def main():
 prepared=json.load(open(W/'out/PREPARED.json'));INPUTS.update(prepared['input_sha256']);reg(W/'out/PREPARED.json');reg(W/'out/WORDING.json');reg(__file__);reg(W/'wording.py')
 wr=json.load(open(W/'out/WORDING.json'));assert all(q['accepted'] for q in wr['questions']) and [q['question'] for q in wr['questions']]==QUESTIONS
 rs,extra=rules();selected=[];physical=set()
 for wanted,n in CELLS.items():
  candidates=sorted((e for e in prepared['entries'] if e['buildable'] and cell(e)==wanted),key=lambda e:digest('sb_rowLR|'+e['canonical']))
  got=[]
  for e in candidates:
   if e['physical_room'] in physical:continue
   got.append(e);physical.add(e['physical_room'])
   if len(got)==n//2:break
  assert len(got)*2==n,('SHORT_CELL',wanted,n,len(got)*2)
  selected+=got
 rows=[];sources=[];used=collections.Counter()
 for e in selected:
  src=e['source'];sources.append(src);reg(e['path']);assert not status(e['canonical'],rs,extra)
  r2_contract.validate(r2_adapters.normalize(src),'vqa')
  for variant,question in enumerate(QUESTIONS):
   qid='sb_rowLR_'+digest(e['canonical'])[:16]+f'_q{variant}';answer=f"{e['measurement']['area_m2']:.2f}"
   row=copy.deepcopy(src)
   # These fields describe the new room task; image and license fields remain byte-identical.
   for k in ['events','ground_record','tool_output_spans','routing','routing_policy','response_source','head_layout','provisional_diagnostic','benchmark_trained_diagnostic','r2_source_sha256']:
    row.pop(k,None)
   row.update(qid=qid,answer=answer,question_type='room_size_estimation',category='room_size_estimation',form='direct',head_program=None,pool='sb_rowLR',result_status='verified traced room; candidate for intake',infrastructure_only=False,benchmark_improvement_claim=False,answer_unit='m2')
   row['student_input']['question']=question;row['student_input']['options']=[]
   if 'question' in row:row['question']=question
   if 'options' in row:row['options']=[]
   if 'type' in row:row['type']='room_size_estimation'
   row['target']=target(e['trace'],qid,answer)
   identity=dict(qid=qid,scene=e['canonical'],frame_indices=e['frame_indices'],type='room_size_estimation',question=question,options=[],trace_revision='3.14')
   row['candidate_id']=candidate_identity(identity)
   trace=copy.deepcopy(e['trace']);trace.update(raster_path=e['path'],raster_sha256=sha(e['path']),generator_sha256=sha(W/'prepare.py'),reference_generator_sha256=sha('/scratch/jjyeung/n30_mirror/rows_r1/work/codeF/build_room.py'),wording={'locate':'best_view','relate':(int(digest(qid),16)//2)%2})
   row['provenance']=dict(canonical=e['canonical'],alias=src['dataset']+'/'+src['scene'],physical_group=e['physical_room'],family='room',geometry_source='gt',mask_source='none',frame_indices=e['frame_indices'],details=dict(unit='square meters',cell=cell(e),question_variant=variant,source_use_cap=2),source_qid=src['qid'],source_store_sha256='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443',source_row_sha256=digest(json.dumps(src,sort_keys=True)),room_trace=trace,room_measurement=e['measurement'],candidate_identity_fields=identity,input_sha256={str(W/'out/PREPARED.json'):sha(W/'out/PREPARED.json'),str(W/'out/WORDING.json'):sha(W/'out/WORDING.json'),str(W/'generate.py'):sha(__file__),e['path']:sha(e['path'])})
   assert not trace_grammar.validate_row(row),(qid,trace_grammar.validate_row(row))
   r2_contract.validate(r2_adapters.normalize(row),'vqa')
   rows.append(row);used[src['qid']]+=1
 assert dict(collections.Counter(r['provenance']['details']['cell'] for r in rows))==CELLS
 assert len({r['qid'] for r in rows})==len(rows)==72 and len({r['candidate_id'] for r in rows})==72
 assert max(used.values())==2
 assert sum(r['provenance']['room_measurement']['area_m2']>=40 for r in rows)==24
 assert sum(r['provenance']['room_measurement']['area_m2']>=60 for r in rows)==12
 (W/'out/rows.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
 (W/'out/SOURCES.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in sources))
 # Review every large row and a deterministic sample of six controls.
 large=[r for r in rows if r['provenance']['room_measurement']['area_m2']>=40]
 mid=sorted((r for r in rows if r not in large),key=lambda r:digest(r['qid']))[:6]
 with open(W/'out/READ30.md','w') as f:
  f.write('Thirty complete generated records: all 24 large rows and six controls.\n\n')
  for r in large+mid:f.write('## '+r['qid']+'\n\n```json\n'+json.dumps(r,indent=2,sort_keys=True)+'\n```\n\n')
 dump(W/'out/BUILD.json',dict(status='BUILT_PENDING_INDEPENDENT_CHECK',rows=72,large_rows=24,ge60_rows=12,cells=CELLS,max_source_uses=2,max_capture_uses=2,max_physical_room_uses=2,sha256_rows=sha(W/'out/rows.jsonl'),selection='SHA256(sb_rowLR|canonical) within declared cells, unique physical rooms',review_qids=[r['qid'] for r in large+mid],native_validation='r2_adapters.normalize + r2_contract.validate(vqa) and trace_grammar.validate_row; direct store rows do not use ground_rows.pack'))
 (W/'STATUS.md').write_text('Build: generated 72 rows in exact declared cells: 24 large (12 at least 60 m²), 24 at 20–40 m², and 24 at 10–20 m². Every source and physical room is used twice. Native direct-row intake and grammar pass; independent geometry, field, and wording checks are next.\n')
 print('BUILT',len(rows),CELLS)
if __name__=='__main__':main()
