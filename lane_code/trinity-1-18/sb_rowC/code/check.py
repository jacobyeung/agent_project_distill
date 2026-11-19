"""Independent row audit: no generator arithmetic or census counts are trusted."""
from common import *
import numpy as np,collections,itertools
from concurrent.futures import ProcessPoolExecutor
from wordings import TEMPLATES,BUCKET_QUOTAS

def recompute(job):
 name,path,expected_sha=job;assert sha(path)==expected_sha
 with np.load(path,allow_pickle=False) as z:
  raster=z['inst'];labels=collections.defaultdict(list)
  for iid,label in zip(z['ids'],z['labels']):labels[norm(label)].append(int(iid))
  assert len(set(map(int,z['ids'])))==len(z['ids'])
  visible=collections.defaultdict(list);first={};den=raster.shape[1]*raster.shape[2]
  # Independent algorithm: np.unique per pin, instead of the generator's np.bincount.
  for t,frame in enumerate(raster):
   ids,pixels=np.unique(frame,return_counts=True)
   for iid,n in zip(ids,pixels):
    if iid>=0 and int(n)*1000>=2*den:visible[int(iid)].append(t+1)
  valid=z['valid'].astype(bool)&(z['depth']>0).any(axis=(1,2)) if 'valid' in z else np.ones(len(raster),bool)
  cats={}
  for cat,ids in labels.items():
   if all(i in visible and bool(np.all(valid[:min(visible[i])-1])) for i in ids):cats[cat]=dict(ids=sorted(ids),n=len(ids),first={str(i):min(visible[i]) for i in ids})
  return name,dict(categories=cats,frame_indices=list(map(int,z['frame_indices'])))

def diffs(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):
  out=[]
  for k in a.keys()|b.keys():
   path=p+'.'+k if p else k
   out.extend([path] if k not in a or k not in b else diffs(a[k],b[k],path))
  return out
 if isinstance(a,list):return [] if a==b else [p]
 return [] if a==b else [p]

def main():
 rows_path=ROOT/'out/relative_count.jsonl';pin(rows_path);build=jload(ROOT/'out/BUILD.json');cs=jload(ROOT/'in/CENSUS.json')
 for p,h in build['input_sha256'].items():assert sha(p)==h,('changed input',p)
 pin(__file__);pin(SRC);rows=list(map(json.loads,rows_path.open()));sources={x['qid']:x for x in map(json.loads,SRC.open())}
 rooms,status_room,blocked=setup_rooms();facts={};used={r['provenance']['raster'] for r in rows}
 jobs=[(name,cs['facts'][name]['path'],cs['facts'][name]['sha256']) for name in used]
 with ProcessPoolExecutor(max_workers=8) as pool:
  for name,f in pool.map(recompute,jobs):facts[name]=f
 c=collections.Counter();errors=collections.Counter();cells=collections.Counter();counts_a=collections.Counter();counts_b=collections.Counter();relations=collections.Counter();answers=collections.Counter();datasets=collections.Counter();source_use=collections.Counter();pair_use=collections.Counter();orientation_use=collections.Counter();scene_use=collections.Counter();changes=collections.Counter();grammar=collections.Counter();source_grammar=collections.Counter();validated_sources=set();qids=set();cids=set();sq=set();source_cids={identity(sources[r['provenance']['relative_count']['source_qid']]) for r in rows};gtpins={}
 allowed={'answer','qid','candidate_id','category','question_type','count_kind','count_arity','student_input.question','student_input.options','target','provenance.count_kind','provenance.total_categories','provenance.relative_count','provenance.input_sha256'}
 align={}
 for name in ('ARK_PIN_TS_CHECK.json','ARK_PIN_TS_CHECK_K1.json'):
  p=ROOT/'in/b12/out/PACKET_b12_v4'/name
  for alias,value in jload(p).items():align.setdefault(alias,[]).append(value)
 for r in rows:
  pv=r['provenance'];m=pv['relative_count'];s=sources[m['source_qid']];f=facts[pv['raster']];a,b=m['a'],m['b'];si=r['student_input']
  assert a!=b and not(set(a.split())&set(b.split()))
  assert pv['raster_sha256']==cs['facts'][pv['raster']]['sha256'];assert f['frame_indices']==si['frame_indices']
  fa,fb=f['categories'][a],f['categories'][b];n,k=fa['n'],fb['n'];assert n>=1 and k>=1
  assert (n,k)==(m['count_a'],m['count_b']);assert fa['ids']==sorted(m['ids_a']) and fb['ids']==sorted(m['ids_b'])
  want='more' if n>k else 'fewer' if n<k else 'tie';assert want==m['relation']
  content='equal number' if n==k else want;options={o[0]:o[3:] for o in si['options']}
  assert len(options)==3 and set(options.values())=={'more','fewer','equal number'};assert options[r['answer']]==content
  task=dict(answer_type='multiple_choice',options=si['options'],ground_truth=r['answer'],question_type='relative_count')
  scored=score_item(task,dict(text=r['target'],finish='eos'));assert scored['score']==1 and not scored['parse_failed'];c['scorer_pass']+=1
  assert r['target'].count('count each once across the frames.')==2
  assert f'instances of {a}; count each once across the frames. The count is {n}.' in r['target']
  assert f'instances of {b}; count each once across the frames. The count is {k}.' in r['target']
  assert not re.search(r'frame\s+\d|first.seen|first appearance|\blist\b',r['target'])
  assert si['question']==TEMPLATES[m['template_id']].format(a=a,b=b)
  payload=[r['qid'],r['scene'],si['frame_indices'],'relative_count',si['question'],si['options'],[],'3.14','phrases-v3']
  assert r['candidate_id']=='ground-'+hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()
  assert r['candidate_id']==identity(r) and r['candidate_id'] not in source_cids
  assert r['qid'] not in qids and r['candidate_id'] not in cids;qids.add(r['qid']);cids.add(r['candidate_id'])
  assert (pv['canonical'],si['question']) not in sq;sq.add((pv['canonical'],si['question']))
  delta=set(diffs(s,r));assert delta<=allowed,delta-allowed;changes.update(delta)
  assert m['source_row_sha256']==hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  assert status_room(r)=='ok' and status_room(s)=='ok';assert m['room']==rooms.room(pv['canonical'])
  if r['dataset']=='d3':assert align.get(r['dataset']+'/'+r['scene']) and all(v=='ok' for v in align[r['dataset']+'/'+r['scene']])
  native_pack_check(r);r1_counting.admit(r,'counting');r1_training.row_check(r,'vqa');c['native_pack_validate']+=1;c['N_procedure_admission']+=1;c['N_row_check']+=1
  for e in trace_grammar.validate_row(r):grammar[e.rule_id]+=1
  if s['qid'] not in validated_sources:
   native_pack_check(s);r1_training.row_check(s,'vqa')
   for e in trace_grammar.validate_row(s):source_grammar[e.rule_id]+=1
   for sc in s['provenance']['total_categories']:
    true=f['categories'][sc['name']];assert sorted(sc['ids'])==true['ids'];assert all(true['first'][str(i)]==t for i,t in zip(sc['ids'],sc['frames']))
   assert sum(f['categories'][sc['name']]['n'] for sc in s['provenance']['total_categories'])==int(s['answer'])
   validated_sources.add(s['qid'])
  c['independent_GT_rows']+=1;c['room_pass']+=1;c['field_diff_pass']+=1
  if max(n,k)>=5:c['at_least_one_side_ge_5']+=1
  bucket='tie' if n==k else str(min(max(n,k),10));assert bucket==m['bucket']
  cells[f"{m['template_id']:02}|{bucket}|{want}"]+=1;counts_a[n]+=1;counts_b[k]+=1;relations[want]+=1;answers[r['answer']]+=1;datasets[r['dataset']]+=1
  source_use[s['qid']]+=1;pair=(pv['canonical'],*sorted([a,b]));pair_use[pair]+=1;orientation_use[(pair,want)]+=1;scene_use[pv['canonical']]+=1
  gtpins[cs['facts'][pv['raster']]['path']]=cs['facts'][pv['raster']]['sha256']
 assert len(rows)==4000 and relations=={'more':1800,'fewer':1800,'tie':400};assert c['at_least_one_side_ge_5']>=1200
 for tid in range(20):
  for b,n in BUCKET_QUOTAS.items():
   for rel in ('more','fewer'):assert cells[f'{tid:02}|{b}|{rel}']==n
  assert cells[f'{tid:02}|tie|tie']==20
 assert max(source_use.values())<=8 and max(pair_use.values())<=4 and max(orientation_use.values())<=2 and max(scene_use.values())<=24
 assert not source_grammar
 assert all(counts_a[n]>0 and counts_b[n]>0 for n in range(1,11))
 # Repeat the entire corpus filter, and test its compiled implementation against a Python DP oracle.
 from generate import distance_filter,wording_normalized
 corpus=jload(ROOT/'in/WORDING_CORPUS.json');near=distance_filter(corpus['questions']);assert all(near(r['student_input']['question'])<0 for r in rows)
 def distance(a,b):
  prev=list(range(len(b)+1))
  for i,x in enumerate(a,1):
   cur=[i]
   for j,y in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
   prev=cur
  return prev[-1]
 import random
 rng=random.Random(12)
 for t in range(300):
  a=''.join(rng.choice('abc ') for _ in range(rng.randrange(1,80)));b=''.join(rng.choice('abc ') for _ in range(rng.randrange(1,80))) if t%2 else a[:len(a)//2]+'ab'+a[len(a)//2+2:]
  aa,bb=map(wording_normalized,(a,b));expected=distance(aa,bb)/max(len(aa),len(bb),1)<=.25
  assert (distance_filter([b])(a)>=0)==expected
 c['wording_filter_pass']=4000;c['edit_distance_oracle_cases']=300
 selected=[]
 for tid in range(20):selected.append(next(r for r in rows if r['provenance']['relative_count']['template_id']==tid))
 for predicate in [lambda m:m['relation']=='tie']*4+[lambda m:min(m['count_a'],m['count_b'])==1]*2+[lambda m:max(m['count_a'],m['count_b'])>=10]*4:
  selected.append(next(r for r in rows if r not in selected and predicate(r['provenance']['relative_count'])))
 (ROOT/'out/READ30.md').write_text('\n\n'.join(f"### {i+1}. {r['qid']}\n\n```json\n"+json.dumps(r,sort_keys=True,indent=2)+'\n```' for i,r in enumerate(selected))+'\n')
 (ROOT/'out/READ30_TEXT.md').write_text('\n\n'.join(f"### {i+1}. {r['qid']}\nRoom: {r['provenance']['relative_count']['room']}\nGT: {r['provenance']['relative_count']['a']}={r['provenance']['relative_count']['count_a']}; {r['provenance']['relative_count']['b']}={r['provenance']['relative_count']['count_b']}\nQ: {r['student_input']['question']}\n"+'\n'.join(r['student_input']['options'])+'\n'+r['target'] for i,r in enumerate(selected))+'\n')
 pin(ROOT/'out/READ30.md')
 result=dict(status='REVIEW_REQUIRED',required_checks='PASS',shared_direct_grammar='FAIL',shared_direct_grammar_violations=dict(grammar),input_sha256={**PINS,**gtpins},rows=4000,counts=dict(c),source_count=len(validated_sources),source_pack_validate=len(validated_sources),source_shared_grammar='PASS',cells=dict(cells),relation_counts=dict(relations),answer_letters=dict(answers),count_a_histogram=dict(counts_a),count_b_histogram=dict(counts_b),datasets=dict(datasets),training_scenes=len(scene_use),physical_rooms=len({r['provenance']['relative_count']['room'] for r in rows}),max_source_use=max(source_use.values()),max_unordered_pair_use=max(pair_use.values()),max_orientation_use=max(orientation_use.values()),max_scene_use=max(scene_use.values()),field_changes=dict(changes),wording_filter=dict(threshold=.25,normalization='NFKC, casefold, retain word tokens, whitespace collapse',metric='character Levenshtein / maximum normalized length',corpus_questions=len(corpus['questions']),skipped_files=corpus['skipped'],removed=build['counts']['refused'].get('normalized_edit_distance_le_0.25',0)),manual_read='PENDING',limitations=['The shared direct grammar requires a list before a stated numeric count; requested procedure traces fail it. No validator was modified.','ground_rows.pack/validate require ground-record serialization; an audited no-call adapter preserves thought bytes and changes only the answer wrapper. The delivered rows retain the v7 direct-row schema.','RGB-frame loading and full trainer preparation were not run.','Missing b12 rasters are excluded rather than replaced by unverified GT.'])
 dump(ROOT/'out/CHECKS.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','cells','field_changes')}))
 status('All 4,000 rows pass independent GT recomputation, room exclusions, exact cells, source-use caps, candidate identity, field diffs, scorer checks, and native pack/validate through the documented direct-row adapter. The shared direct grammar rejects stated procedure counts; the packet remains REVIEW_REQUIRED. The 30 complete sample rows are ready for manual reading.')
if __name__=='__main__':main()
