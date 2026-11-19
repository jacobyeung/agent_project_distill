"""Independent checks derive comparison answers from b12 total-category instance sets."""
from common import *
import collections,copy,ctypes,unicodedata,random
from wordings import TEMPLATES
from priors import evaluate,records
from student_pilot import trace_grammar,r1_counting,r1_training,r1_population
from evalpath.run import score_item

def normalized(s):return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',s).casefold()))
def scalar_distance(a,b):
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  cur=[i]
  for j,y in enumerate(b,1):cur.append(min(prev[j]+1,cur[j-1]+1,prev[j-1]+(x!=y)))
  prev=cur
 return prev[-1]/max(len(a),len(b),1)
def distances(rs):
 corpus=load(BASE/'in/WORDING_CORPUS.json')
 names=corpus['file_question_counts']
 dev=next(p for p in names if p.endswith('/legs1_reads/work/vendor/r3/TASKS.jsonl'))
 r0=next(p for p in names if p.endswith('/inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl'))
 devrows=list(rows(dev));r0rows=list(rows(r0))
 for p in (dev,r0):assert PINS[p]==corpus['input_sha256'][p]
 references={};counts={}
 for name,data in [('dev-S1',devrows),('R0-dev',r0rows)]:
  refs=[r['question'] for r in data if r.get('question_type',r.get('type'))=='relative_count']
  counts[name]={'total_items':len(data),'relative_count_items':len(refs),'unique_relative_count_wordings':len(set(refs))}
  references[name]=refs
 ref=sorted(set(q for v in references.values() for q in v));assert set(ref)==set(corpus['relative_count_wordings'])
 texts=[normalized(s).encode('ascii') for s in ref]
 lib=ctypes.CDLL(str(ROOT/'code/nearest.so'));fn=lib.nearest
 fn.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_int,ctypes.POINTER(ctypes.c_int)];fn.restype=ctypes.c_double
 pin(ROOT/'code/nearest.cpp');pin(ROOT/'code/nearest.so')
 arr=(ctypes.c_char_p*len(texts))(*texts)
 mins={};failed=[];per_template={};all_questions=set()
 for r in rs:
  q=r['student_input']['question'];tid=str(r['provenance']['relative_count']['template_id']);all_questions.add(q)
  if q not in mins:
   idx=ctypes.c_int();d=fn(normalized(q).encode('ascii'),arr,len(texts),ctypes.byref(idx));mins[q]=(d,idx.value)
  d,idx=mins[q]
  if d<0.4:failed.append({'qid':r['qid'],'distance':d,'question':q,'reference':ref[idx]})
  if tid not in per_template or d<per_template[tid]['minimum']:
   per_template[tid]={'minimum':d,'qid':r['qid'],'question':q,'reference':ref[idx]}
 rng=random.Random(11)
 for i in range(300):
  a=''.join(rng.choice('abc ') for _ in range(rng.randrange(1,90)));b=''.join(rng.choice('abc ') for _ in range(rng.randrange(1,90)))
  idx=ctypes.c_int();one=(ctypes.c_char_p*1)(b.encode());assert abs(fn(a.encode(),one,1,ctypes.byref(idx))-scalar_distance(a,b))<1e-12
 result=dict(status='PASS' if not failed else 'FAIL',threshold=0.4,comparison='distance >= threshold',metric='Levenshtein / max normalized character length',normalization='NFKC, casefold, word-token extraction, whitespace collapse; all normalized text is ASCII',sources=counts,reference_wordings=len(ref),rows=len(rs),unique_questions=len(all_questions),minimum=min(d for d,i in mins.values()),below_threshold=len(failed),failures=failed,per_template=per_template,oracle_cases=300,input_sha256=dict(PINS))
 dump(ROOT/'out/WORDING_CHECK.json',result)
 return result

def main():
 build=load(ROOT/'out/BUILD.json');seal=load(TREE.parent.parent/'out/TREE_SEAL.json');assert seal==build['tree_seal']
 treefiles=TREE.parent.parent/'out/TREE_FILES.sha256';pin(treefiles)
 for line in treefiles.read_text().splitlines():
  h,name=line.split(maxsplit=1)
  if name in ['student_pilot/trace_grammar.py','student_pilot/r1_counting.py','student_pilot/r1_training.py','student_pilot/ground_rows.py','student_pilot/r1_population.py','generator/derivgen_v7/derivgen/ground_v312_quality.py','evalpath/run.py','evalpath/official.py']:
   assert pin(TREE/name)['sha256']==h,name
 rs=list(rows(ROOT/'out/relative_count.jsonl'));assert len(rs)==build['rows'];quotas=build['per_template_bucket_quota'];per_direction=sum(quotas.values())
 needed={r['provenance']['relative_count']['source_qid'] for r in rs}
 sources={r['qid']:r for r in rows(SRC) if r['qid'] in needed};assert len(sources)==len(needed)
 counts=collections.Counter();relations=collections.Counter();letters=collections.Counter();cells=collections.Counter();template=collections.defaultdict(lambda:dict(relations=collections.Counter(),option_letters=collections.Counter(),tie_order=collections.Counter(),alphabetical_relation=collections.Counter()))
 sourceuse=collections.Counter();pairs=collections.Counter();orient=collections.Counter();scenes=collections.Counter();datasets=collections.Counter();qids=set();cids=set();sourcevalidated=set();gt=[]
 procedure=build['procedure_body']
 for r in rs:
  m=r['provenance']['relative_count'];s=sources[m['source_qid']];a,b=m['a'],m['b'];si=r['student_input']
  cats={x['name']:x for x in s['provenance']['total_categories']};assert len(cats)==len(s['provenance']['total_categories'])
  sets={k:set(v['ids']) for k,v in cats.items()};assert all(len(sets[k])==len(v['ids']) for k,v in cats.items())
  assert sum(map(len,sets.values()))==int(s['answer'])
  assert not (sets[a]&sets[b])
  assert r['scene']==s['scene'] and r['provenance']['canonical']==s['provenance']['canonical']
  assert all(r['provenance'][k]==v for k,v in s['provenance'].items() if k not in ('count_kind','total_categories'))
  counts['preserved_source_metadata']+=1
  n,k=len(sets[a]),len(sets[b]);want='more' if n>k else 'fewer' if n<k else 'tie'
  assert (n,k)==(m['count_a'],m['count_b']) and set(m['ids_a'])==sets[a] and set(m['ids_b'])==sets[b]
  assert m['relation']==want and m['source_row_sha256']==digest(s)
  opts={o[0]:o[3:] for o in si['options']};assert set(opts)==set('ABC') and set(opts.values())=={'more','fewer','equal number'}
  assert opts[r['answer']]==('equal number' if n==k else want)
  assert si['question']==TEMPLATES[m['template_id']].format(a=a,b=b)
  for key in ('frames','frame_indices','timestamps','fps','total_num_frames'):assert si[key]==s['student_input'][key]
  th=thought(r);lines=th.strip().splitlines();assert len(lines)==3
  assert lines[:2]==[procedure.format(category=a),procedure.format(category=b)]
  expected=(f'So there are as many {a} instances as {b} instances.' if n==k else f'So there are {want} {a} instances than {b} instances.')
  assert lines[2]==expected
  assert not re.search(r'\d|\blist\b|first.seen|first appearance|<tool|<ground',th,re.I)
  assert not trace_grammar.WORD_NUMBER.search(th)
  assert r['target'].endswith('</think>\n\n'+r['answer']) and r['answer'] in 'ABC'
  assert not trace_grammar.validate_trace(th,form='direct',question=si['question'],options=si['options'],answer=r['answer'],n_frames=len(si['frames']),qtype='relative_count')
  assert not trace_grammar.validate_row(r)
  r1_counting.admit(r,'counting');r1_training.row_check(r,'vqa');native_pack_check(r)
  assert r1_population.family(r,'vqa')=='counting'
  for key in ['validate_trace','validate_row','r1_counting.admit','r1_training.row_check','ground_rows.pack_validate','no_numbers_or_lists','independent_b12_totals','letter_matches_GT']:counts[key]+=1
  task=dict(answer_type='multiple_choice',options=si['options'],ground_truth=r['answer'],question_type='relative_count');scored=score_item(task,dict(text=r['target'],finish='eos'));assert scored['score']==1 and not scored['parse_failed'];counts['scorer_pass']+=1
  payload=[r['qid'],r['scene'],si['frame_indices'],'relative_count',si['question'],si['options'],[],'3.14','phrases-v3']
  assert r['candidate_id']=='ground-'+hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()==identity(r)
  assert r['qid'] not in qids and r['candidate_id'] not in cids;qids.add(r['qid']);cids.add(r['candidate_id'])
  counts['candidate_formula']+=1
  tid=str(m['template_id']);relations[want]+=1;letters[r['answer']]+=1;template[tid]['relations'][want]+=1;template[tid]['option_letters'][r['answer']]+=1
  template[tid]['alphabetical_relation'][f'{a < b}|{want}']+=1
  if want=='tie':template[tid]['tie_order']['ascending' if a<b else 'descending']+=1
  bucket='tie' if n==k else str(min(max(n,k),10));assert m['bucket']==bucket;cells[f'{int(tid):02}|{bucket}|{want}']+=1
  sourceuse[s['qid']]+=1;pair=(r['provenance']['canonical'],*sorted((a,b)));pairs[pair]+=1;orient[(pair,want)]+=1;scenes[r['provenance']['canonical']]+=1;datasets[r['dataset']]+=1
  if s['qid'] not in sourcevalidated:native_pack_check(s);sourcevalidated.add(s['qid'])
  gt.append(dict(qid=r['qid'],source_qid=s['qid'],source_row_sha256=digest(s),category_a=a,category_b=b,count_a=n,count_b=k,relation=want,answer=r['answer']))
 assert relations==dict(more=20*per_direction,fewer=20*per_direction,tie=400);assert max(letters.values())-min(letters.values())<=1
 for tid in range(20):
  assert template[str(tid)]['relations']==dict(more=per_direction,fewer=per_direction,tie=20)
  assert template[str(tid)]['tie_order']==dict(ascending=10,descending=10)
  assert max(template[str(tid)]['option_letters'].values())-min(template[str(tid)]['option_letters'].values())<=1
  for b,n in quotas.items():
   for rel in ('more','fewer'):assert cells[f'{tid:02}|{b}|{rel}']==n
  assert cells[f'{tid:02}|tie|tie']==20
 assert max(sourceuse.values())<=8 and max(pairs.values())<=4 and max(orient.values())<=2 and max(scenes.values())<=24
 prior=evaluate(records(rs));cap=build['chosen_cap']
 assert prior['mean_unequal']['accuracy']<=cap and prior['pair_majority']['accuracy_tie_upper']<=cap
 assert all(v['majority_fraction']<=cap+1e-12 for v in prior['categories'].values())
 assert len({digest([r['student_input']['question'],r['student_input']['options'],r['student_input']['frames']]) for r in rs})==len(rs)
 code_pins()
 dump(ROOT/'out/NAME_PRIOR.json',dict(status='PASS',input_sha256=dict(PINS),command='bash code/run.sh code/check.py',cap=cap,**prior))
 dump(ROOT/'out/GT_CHECK.json',dict(status='PASS',method='Independent category instance-set cardinalities from b12 count_total.jsonl; no generated counts or comparison labels used as ground truth.',input_sha256=dict(PINS),rows=gt))
 wording=distances(rs)
 selected=[]
 for tid in range(20):selected.append(next(r for r in rs if r['provenance']['relative_count']['template_id']==tid and r['provenance']['relative_count']['relation']!='tie'))
 for tid in range(20):selected.append(next(r for r in rs if r['provenance']['relative_count']['template_id']==tid and r['provenance']['relative_count']['relation']=='tie' and (r['provenance']['relative_count']['a']<r['provenance']['relative_count']['b'])==(tid%2==0)))
 (ROOT/'out/READ40.md').write_text('Forty complete rows follow: one unequal case and one tie for each template. Counts are audit metadata only.\n\n'+'\n\n'.join(f"### {i+1}. {r['qid']}\n\n```json\n"+json.dumps(r,sort_keys=True,indent=2)+'\n```' for i,r in enumerate(selected))+'\n')
 (ROOT/'out/READ40_TEXT.md').write_text('\n\n'.join(f"{i+1}. Template {r['provenance']['relative_count']['template_id']}; {r['qid']}\nGT: {r['provenance']['relative_count']['a']}={r['provenance']['relative_count']['count_a']}; {r['provenance']['relative_count']['b']}={r['provenance']['relative_count']['count_b']}\nQ: {r['student_input']['question']}\n"+'\n'.join(r['student_input']['options'])+'\n'+r['target'] for i,r in enumerate(selected))+'\n')
 result=dict(status='REVIEW_PENDING' if wording['status']=='PASS' else 'FAIL_WORDING',input_sha256=dict(PINS),tree_seal=seal,rows=len(rs),counts=counts,unique_qids=len(qids),unique_candidate_ids=len(cids),relation_counts=relations,option_letters=letters,per_template=template,cells=cells,name_prior=prior,chosen_cap=cap,cap_trials={k:dict(rows=v['rows'],surviving_rows=v['surviving_rows'],gate=v['gate'],per_template_bucket_quota=v['per_template_bucket_quota'],mean=v['measured_priors']['mean_unequal'],pair=v['measured_priors']['pair_majority']) for k,v in build['cap_trials'].items()},source_rows=len(sources),captures=len(scenes),datasets=datasets,max_source_reuse=max(sourceuse.values()),max_pair_reuse=max(pairs.values()),max_orientation_reuse=max(orient.values()),max_capture_reuse=max(scenes.values()),wording={k:wording[k] for k in ('status','minimum','below_threshold','reference_wordings','sources','oracle_cases')},room_audit='PENDING',manual_read='PENDING',cross_family_review='PENDING',command='bash code/run.sh code/check.py')
 dump(ROOT/'out/ROW_CHECKS.json',result)
 status(f"All {len(rs)} rows pass independent b12 totals and option-letter checks, N's w24 grammar/admission/row checks, native pack/validate, candidate identity, preservation, and balance checks. Wording distance is {wording['status']} with minimum {wording['minimum']:.6f}. Room audit and the prepared 40-row manual review remain pending.")
 print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','per_template','cells','name_prior','cap_trials')}))
if __name__=='__main__':main()
