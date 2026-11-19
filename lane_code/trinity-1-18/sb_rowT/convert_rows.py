"""Convert pinned removed counting rows; default tally, --form locate emits per-instance lines.

Run with a local Python >=3.10. N's validators are imported without modification.
No image reads, training, network, or writes outside this workspace.
"""
import argparse, collections, copy, ctypes, hashlib, json, re, sys, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent
I=ROOT/'inputs'
EXPECTED_MECHANICAL={'single':8678,'multiple':9201}
EXPECTED_ELIGIBLE={'single':8404,'multiple':9160}
EXPECTED_REFUSALS={'MISSING_independent_instance_annotations':84,'excluded_room_k1_heldout':228,'MISSING_canonical_room_mapping':3}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def jload(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def norm(x):return ' '.join(unicodedata.normalize('NFKC',x).casefold().split())
class Refusal(ValueError):pass

def need(v,why):
 if not v:raise Refusal(why)
LIST_PATTERNS=[
 r'list each distinct (.+?) once, by the frame where it first appears',
 r'locate each distinct (.+?) at its first appearance',
 r'list the distinct (.+?) instances by first appearance',
 r'find each distinct (.+?), using its first-seen frame',
]
QUESTION_PATTERNS=[
 r'How many (.+?) do we have in this room\?',
 r'How many (.+?) are there in this room\?',
 r'How many (.+?) are there in the room shown in the video\?',
 r'Count the (.+?) in this room\. How many are there\?',
 r'Based on the video, give the number of (.+?) in this room\.',
 r'Count the (.+?) in this room\. What is the total\?',
 r'What is the total count of (.+?) in the room depicted by the video\?',
 r'How many objects are there altogether among the (.+?) in this room\?',
 r'What is the total number of (.+?) in this room\?',
 r'Count the (.+?) in this room together\. How many are there in total\?',
 r'How many (.+?) are in this room in total\?',
]
ENTRY=re.compile(r'frame ([0-9]+)(?: \((left|middle|right)\))?')
def parse(r):
 question=r['student_input']['question'];ask=None
 for pat in QUESTION_PATTERNS:
  m=re.fullmatch(pat,question)
  if m:
   ask=m[1];break
 need(ask is not None,'unparsed_question')
 names=[s.removesuffix('(s)') for s in ask.split('(s) and ')]
 need(len(names)==len(set(names)),'duplicate_asked_category')
 cats={};text=r['target'].replace('\\n','\n')
 for line in text.splitlines():
  m=re.fullmatch(r'Step [0-9]+: (.*?): (frame .*?)\.',line)
  if not m:continue
  name=None
  for pat in LIST_PATTERNS:
   h=re.fullmatch(pat,m[1])
   if h:name=h[1];break
  need(name is not None,'unparsed_list_header')
  need(name not in cats,'duplicate_category_section')
  entries=[]
  for entry in m[2].split('; '):
   t=ENTRY.fullmatch(entry);need(t is not None,'unparsed_instance')
   frame=int(t[1]);need(1<=frame<=32,'frame_outside_1_32')
   entries.append((frame,t[2] or ''))
  cats[name]=entries
 need(set(cats)==set(names),'asked_category_missing_or_extra')
 need(all(cats.values()),'empty_category')
 need(re.fullmatch(r'[0-9]+',str(r['answer'])),'noninteger_answer')
 need(sum(map(len,cats.values()))==int(r['answer']),'sum_answer_mismatch')
 need(text.endswith('\n</think>\n\n'+str(r['answer'])),'source_final_answer_mismatch')
 if 'count_arity' in r:need(len(cats)==r['count_arity'],'count_arity_mismatch')
 return [(name,cats[name]) for name in names]

def independent_truth(r,cats):
 """Recount structured annotated identities, separately from text parsing/grouping."""
 p=r['provenance'];expected={};basis=''
 if 'total_categories' in p:
  basis='provenance.total_categories'
  for c in p['total_categories']:
   ids=c['ids'];frames=c['frames']
   need(len(ids)==len(set(ids))==len(frames),'annotation_duplicate_id_or_length')
   expected[c['name']]=collections.Counter(frames)
 elif 'instances' in p:
  basis='provenance.instances';inst=p['instances'];ids=[x['id'] for x in inst]
  need(len(ids)==len(set(ids)),'annotation_duplicate_id_or_length')
  need(len(cats)==1,'single_annotation_multiple_categories')
  expected[cats[0][0]]=collections.Counter(x['frame'] for x in inst)
  need(collections.Counter((x['frame'],x['region']) for x in inst)==collections.Counter(cats[0][1]),'region_annotation_mismatch')
 elif r.get('retrace_a2',{}).get('cited') is not None:
  basis='retrace_a2.cited';need(len(cats)==1,'single_annotation_multiple_categories')
  expected[cats[0][0]]=collections.Counter(r['retrace_a2']['cited'].values())
 else:raise Refusal('MISSING_independent_instance_annotations')
 need(set(expected)=={name for name,_ in cats},'annotation_category_mismatch')
 for name,entries in cats:
  need(expected[name]==collections.Counter(f for f,_ in entries),'annotation_frame_inventory_mismatch')
 need(sum(sum(v.values()) for v in expected.values())==int(r['answer']),'annotation_truth_mismatch')
 return basis

def alpha(n):
 s=''
 while True:
  s=chr(97+n%26)+s;n=n//26-1
  if n<0:return s

def render(cats,answer,form):
 lines=[];sums=[];step=1
 for name,entries in cats:
  sums.append(len(entries))
  if form=='tally':
   frames=collections.defaultdict(collections.Counter)
   for f,reg in entries:frames[f][reg]+=1
   parts=[]
   for f,regions in sorted(frames.items()):
    n=sum(regions.values());tags=', '.join(f'{key}: {regions[key]}' for key in ('left','middle','right') if regions[key])
    need(not tags or not regions[''],'mixed_missing_region')
    parts.append(f'frame {f}: {n}'+(f' ({tags})' if tags else ''))
   lines.append('TALLY '+name+': '+'; '.join(parts)+f' -> {len(entries)}.')
  else:
   labels=[]
   for n,(f,reg) in enumerate(sorted(entries)):
    label='tag_'+alpha(n);labels.append(label)
    lines.append(f'Locate: {name} instance {label} in frame {f}'+(f' ({reg})' if reg else '')+'.')
   lines.append(f'Step {step}: list distinct instances of {name}: '+'; '.join(labels)+'.');step+=1
   lines.append(f'Step {step}: So the count is {len(entries)}.');step+=1
 if len(sums)>1:
  if form=='tally':lines.append('Total: '+' + '.join(map(str,sums))+' = '+str(answer)+'.')
  else:
   value=sums[0];expr=[]
   for n in sums[1:]:expr.append(f'{value} + {n} = {value+n}');value+=n
   lines.append(f'Step {step}: add the category counts: '+'; '.join(expr)+'.')
 return '<think>\n'+'\n'.join(lines)+'\n</think>\n\n'+str(answer)

NED=ctypes.CDLL(str(ROOT/'ned_filter.so')).bounded_distance
NED.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int]
NED.restype=ctypes.c_int
def edit_distance(a,b,limit):
 """Exact thresholded character Levenshtein; max-length normalization."""
 if abs(len(a)-len(b))>limit:return limit+1
 if a.isascii() and b.isascii():
  result=NED(a.encode(),b.encode(),limit)
  if result<0:raise MemoryError('Levenshtein buffer allocation failed')
  return result
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  cur=[i]+[limit+1]*len(b)
  for j in range(max(1,i-limit),min(len(b),i+limit)+1):
   cur[j]=min(cur[j-1]+1,prev[j]+1,prev[j-1]+(x!=b[j-1]))
  if min(cur)>limit:return limit+1
  prev=cur
 return prev[-1]

def setup():
 manifest=jload(I/'INPUTS.json');sys.path.insert(0,manifest['tree']);sys.dont_write_bytecode=True
 from student_pilot.r1_rooms import Rooms
 from student_pilot.s1_exclusions import Exclusions
 pins=manifest['pins']
 for name in ['removed_rows.jsonl','scene_facts.json','source_ids.json','wording_corpus.json','z.json','split.json','reserve.json','aliases.json','build.json','visits.json','withheld.json','dev.json','bench.json']:
  assert sha(I/name)==pins[name]['sha256'],name
 authority={k:{'path':str(I/(k+'.json')),'sha256':pins[k+'.json']['sha256']} for k in ('split','reserve','aliases','build','visits')}
 rooms=Rooms(authority)
 ex=Exclusions({'path':str(I/'dev.json'),'sha256':pins['dev.json']['sha256']},{'path':str(I/'bench.json'),'sha256':pins['bench.json']['sha256']})
 return manifest,rooms,ex

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--form',choices=['tally','locate'],default='tally');ap.add_argument('--out',default='out');args=ap.parse_args()
 out=(ROOT/args.out).resolve();assert out.is_relative_to(ROOT);out.mkdir(exist_ok=True,parents=True)
 manifest,rooms,ex=setup()
 from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
 from student_pilot.trace_grammar import validate_row
 from student_pilot.r1_training import row_check
 from student_pilot.finetune_lane import validate_student_input
 from student_pilot import r1_counting,ground_rows
 from student_pilot.r2_contract import validate as native_validate
 facts=jload(I/'scene_facts.json')['facts'];withheld=set(jload(I/'withheld.json')['rooms'])
 source_ids=jload(I/'source_ids.json')['ids'];oldids={x[0] for x in source_ids};oldcids={x[1] for x in source_ids if x[1]}
 wordings=sorted({norm(q) for q in jload(I/'wording_corpus.json')['questions']});threshold=.1
 inputs={k:v['sha256'] for k,v in manifest['pins'].items()};inputs['convert_rows.py']=sha(Path(__file__));inputs['INPUTS.json']=sha(I/'INPUTS.json')
 inputs['ned_filter.c']=sha(ROOT/'ned_filter.c');inputs['ned_filter.so']=sha(ROOT/'ned_filter.so')
 counts=collections.Counter();refcounts=collections.Counter();mechanical=collections.Counter();admitted=collections.Counter();truth=collections.Counter();basiscounts=collections.Counter();newids=set();newcids=set();used=collections.Counter();validcounts=collections.Counter();examples={};eligible=[];refusals=[];audit=[]
 sourcecells=collections.Counter();validation_errors=collections.Counter();source_errors=collections.Counter();gate_errors=collections.Counter();pack_errors=collections.Counter();source_truth=collections.Counter();refused_truth=collections.Counter()
 for l in (I/'removed_rows.jsonl').open():
  r=json.loads(l);qid=r['qid'];counts['seen']+=1;sourcecells[r['pool']]+=1;source_truth[min(int(r['answer']),10)]+=1
  cell='multiple' if r.get('count_kind')=='total' else 'single'
  try:
   cats=parse(r);cell='single' if len(cats)==1 else 'multiple';mechanical[cell]+=1
   counts['mechanically_exact']+=1
   basis=independent_truth(r,cats)
   probe=copy.deepcopy(r);canonical,how=rooms.canonical(probe)
   if not canonical:
    recorded=facts.get(r['dataset']+'/'+r['scene'])
    need(recorded is not None,'MISSING_canonical_room_mapping')
    need(len(recorded)==1,'ambiguous_canonical_room_mapping');canonical=next(iter(recorded));how='store_recorded_field_plus_token_hash'
    probe['canonical']=canonical
   room=rooms.room(canonical);status=rooms.status(probe)[0]
   reasons=[]
   if status!='ok':reasons.append('excluded_room_'+status)
   if room in withheld:reasons.append('excluded_room_withheld80')
   hits=ex.matches(dict(probe,canonical=canonical,physical_group=room))
   if hits['dev']:reasons.append('excluded_room_devS1')
   if hits['benchmark']:reasons.append('excluded_room_BENCH_v2')
   if reasons:raise Refusal('|'.join(sorted(reasons)))
   target=render(cats,r['answer'],args.form)
   # No question is changed. Filter newly authored trace bodies against every
   # available corpus wording; do not silently relabel inherited questions as new.
   authored=norm(target.split('<think>\n',1)[1].split('\n</think>',1)[0])
   for q in wordings:
    limit=int(threshold*max(len(authored),len(q)))
    if edit_distance(authored,q,limit)<=limit:raise Refusal('new_trace_near_eval_wording')
   x=copy.deepcopy(r);x['qid']='sb_rowT_'+args.form+'_'+hashlib.sha256(qid.encode()).hexdigest()[:24];x['target']=target
   rec={'qid':x['qid'],'scene':r['scene'],'frame_indices':r['student_input']['frame_indices'],'type':r['question_type'],'question':r['student_input']['question'],'options':r['student_input']['options'],'trace_revision':'sb_rowT-v1-'+args.form}
   x['candidate_id']=candidate_identity(rec)
   x['provenance']['sb_rowT']={'source_qid':qid,'source_row_sha256':hashlib.sha256(l.rstrip('\n').encode()).hexdigest(),'source_target_sha256':hashlib.sha256(r['target'].encode()).hexdigest(),'input_sha256':{'store':inputs['store'],'z.json':inputs['z.json'],'generator':inputs['convert_rows.py'],'inputs_manifest':inputs['INPUTS.json'],'scene_facts':inputs['scene_facts.json'],'ned_filter.c':inputs['ned_filter.c'],'ned_filter.so':inputs['ned_filter.so']},'form':args.form,'canonical':canonical,'physical_room':room,'canonical_basis':how,'truth_basis':basis,'candidate_identity_record':rec}
   allowed={'qid','target','candidate_id','provenance'}
   assert {k:v for k,v in r.items() if k not in allowed}=={k:v for k,v in x.items() if k not in allowed}
   prov=copy.deepcopy(x['provenance']);prov.pop('sb_rowT');assert prov==r['provenance']
   assert x['qid'] not in newids and x['qid'] not in oldids
   assert x['candidate_id'] not in newcids and x['candidate_id'] not in oldcids
   for tag,row in [('source',r),('new',x)]:
    validate_student_input(row['student_input']);row_check(row,'vqa');validcounts[tag+'_row_check']+=1
    try:native_validate(row,'vqa');validcounts[tag+'_native_validate_pass']+=1
    except ValueError as err:
     validcounts[tag+'_native_validate_fail']+=1
     examples.setdefault(tag+'_native',{'qid':row['qid'],'error':str(err)})
    errs=validate_row(row)
    if not errs:validcounts[tag+'_trace_grammar_pass']+=1
    else:
     validcounts[tag+'_trace_grammar_fail']+=1
     (source_errors if tag=='source' else validation_errors).update({e.rule_id for e in errs})
     examples.setdefault(tag+'_grammar',{'qid':row['qid'],'errors':[e._asdict() for e in errs[:10]]})
    try:
     packed=ground_rows.pack(row,row['provenance']);ground_rows.validate(packed);validcounts[tag+'_ground_pack_pass']+=1
    except (KeyError,ValueError,TypeError) as err:pack_errors[tag+':'+type(err).__name__+':'+str(err)]+=1
   try:r1_counting.admit(x,'totals' if r.get('count_kind')=='total' else 'counting');validcounts['counting_admission_pass']+=1
   except ValueError as err:gate_errors[str(err).split(':')[0]]+=1
   newids.add(x['qid']);newcids.add(x['candidate_id']);used[qid]+=1;eligible.append(x);admitted[cell]+=1;truth[min(int(r['answer']),10)]+=1;basiscounts[basis]+=1
   audit.append({'old_qid':qid,'new_qid':x['qid'],'candidate_id':x['candidate_id'],'source_pool':r['pool'],'cell':cell,'canonical':canonical,'room':room,'truth':int(r['answer']),'categories':{name:len(entries) for name,entries in cats},'input_sha256':{'store':inputs['store'],'generator':inputs['convert_rows.py'],'inputs_manifest':inputs['INPUTS.json']}})
  except Refusal as err:
   refused_truth[min(int(r['answer']),10)]+=1
   reasons=str(err).split('|');refcounts.update(reasons);refusals.append({'old_qid':qid,'source_pool':r['pool'],'cell':cell,'truth':r['answer'],'reasons':reasons,'input_sha256':{'store':inputs['store'],'generator':inputs['convert_rows.py'],'inputs_manifest':inputs['INPUTS.json']}})
 assert counts['seen']==17879 and sourcecells==collections.Counter(manifest['source_cells'])
 assert len(eligible)+len(refusals)==17879
 assert max(used.values(),default=0)<=1
 assert len(newids)==len(newcids)==len(eligible)
 assert dict(mechanical)==EXPECTED_MECHANICAL,dict(mechanical)
 assert dict(admitted)==EXPECTED_ELIGIBLE,dict(admitted)
 assert dict(refcounts)==EXPECTED_REFUSALS,dict(refcounts)
 # Verify each actually imported kit module against the sealed source tree.
 sealed=jload(I/'TREE_SEAL.json')['files'];kit_root=Path(manifest['tree'])
 for module in list(sys.modules.values()):
  path=getattr(module,'__file__',None)
  if path and Path(path).is_relative_to(kit_root) and path.endswith('.py'):
   rel=str(Path(path).relative_to(kit_root));assert sha(path)==sealed[rel],rel
 # Census defines every cell exactly; no sampling target may silently fall short.
 census={'input_sha256':inputs,'source_cells':dict(sourcecells),'mechanically_exact_cells':dict(mechanical),'eligible_cells':dict(admitted),'refused_rows':len(refusals)}
 dump(out/'CENSUS.json',census)
 for name,rows in [('rows.jsonl',eligible),('QID_MAP.jsonl',audit),('REFUSALS.jsonl',refusals)]:
  with (out/name).open('w') as f:
   for row in rows:f.write(encoded(row)+'\n')
 histogram={'input_sha256':inputs,'row_truth':{str(i) if i<10 else '10+':truth[i] for i in range(11)},'definition':'One row per final stored answer, bucket 10+ includes all answers >=10.','by_cell':{c:{str(i) if i<10 else '10+':sum(a['cell']==c and min(a['truth'],10)==i for a in audit) for i in range(11)} for c in ('single','multiple')}}
 histogram['removed_input_row_truth']={str(i) if i<10 else '10+':source_truth[i] for i in range(11)}
 histogram['refused_row_truth']={str(i) if i<10 else '10+':refused_truth[i] for i in range(11)}
 dump(out/'TRUTH_HISTOGRAM.json',histogram)
 (out/'TRUTH_HISTOGRAM.tsv').write_text('truth\trows\tsingle\tmultiple\n'+''.join(f'{k}\t{v}\t{histogram["by_cell"]["single"][k]}\t{histogram["by_cell"]["multiple"][k]}\n' for k,v in histogram['row_truth'].items()))
 checks={'input_sha256':inputs,'form':args.form,'status':'KIT_ONLY_PENDING_TRACE_RULE_AND_VALIDATOR_AMENDMENT','counts':dict(counts),'eligible_rows':len(eligible),'eligible_cells':dict(admitted),'mechanically_exact_cells':dict(mechanical),'refused_rows':len(refusals),'refusal_reasons_overlapping':dict(refcounts),'source_reuse_max':max(used.values(),default=0),'unique_qids':len(newids),'unique_candidate_ids':len(newcids),'old_new_id_intersections':0,'field_diff_allowed':['qid','target','candidate_id','provenance.sb_rowT'],'truth_basis':dict(basiscounts),'validation':dict(validcounts),'source_grammar_errors':dict(source_errors),'new_grammar_errors':dict(validation_errors),'counting_admission_errors':dict(gate_errors),'ground_pack_errors':dict(pack_errors),'ground_pack_scope':'These direct store rows are not ground_record program rows; the unchanged pack API refuses them. No synthetic ground record is fabricated.','examples':examples,'wording_filter':{'normalized_edit_distance_threshold':threshold,'normalization':'Unicode NFKC, casefold, collapse whitespace; character Levenshtein/max length','reference_wordings':len(wordings),'new_questions':0,'questions_unchanged':len(eligible),'checked_text':'new complete think body','removed':refcounts['new_trace_near_eval_wording'],'scope':'All question/prompt fields found in sealed kit and fixtures; full external evaluation item corpora are not in the kit.'},'room_exclusion_pass':len(eligible),'room_unresolved_admitted':0,'artifact_sha256':{name:sha(out/name) for name in ('rows.jsonl','QID_MAP.jsonl','REFUSALS.jsonl','CENSUS.json','TRUTH_HISTOGRAM.json')}}
 dump(out/'CHECKS.json',checks)
 # Select a deterministic, stratified 30, including each pool and truth bucket.
 selected=[];seen=set()
 def add(r):
  if r['qid'] not in seen and len(selected)<30:selected.append(r);seen.add(r['qid'])
 for pool in sorted(sourcecells):
  for r in eligible:
   if r['pool']==pool:add(r);break
 for c in ('single','multiple'):
  for truthbin in range(11):
   for r,a in zip(eligible,audit):
    if a['cell']==c and min(a['truth'],10)==truthbin:add(r);break
 for r in sorted(eligible,key=lambda x:hashlib.sha256(x['qid'].encode()).hexdigest()):add(r)
 assert len(selected)==30
 with (out/'READ30.md').open('w') as f:
  f.write('Thirty full rows, selected by source pool, category arity, and truth bucket.\n\n')
  for n,r in enumerate(selected,1):
   f.write(f'## {n}. {r["qid"]}\n\nQuestion: {r["student_input"]["question"]}\n\n```text\n{r["target"]}\n```\n\n```json\n{encoded(r)}\n```\n\n')
 (ROOT/'STATUS.md').write_text(f'Conversion stage: {len(eligible):,} {args.form} rows emitted from {counts["seen"]:,} removed rows; {len(refusals):,} refused with explicit reasons. Questions, answers, images, and all source fields outside the declared edits remain identical. The unchanged N grammar and admission results are recorded separately from the arithmetic checks. Independent output audit and human reading remain.\n')
 print(json.dumps({k:checks[k] for k in ('form','eligible_rows','eligible_cells','refused_rows','refusal_reasons_overlapping','validation','source_grammar_errors','new_grammar_errors','counting_admission_errors')}))
if __name__=='__main__':main()
