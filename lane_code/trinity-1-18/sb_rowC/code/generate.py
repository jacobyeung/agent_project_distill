from common import *
from wordings import TEMPLATES,BUCKET_QUOTAS
import collections,ctypes,itertools,unicodedata,random

def wording_normalized(s):return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',s).casefold()))
def distance_filter(corpus):
 lib=ctypes.CDLL(str(ROOT/'code/editdistance.so'));fn=lib.near_any
 fn.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_int,ctypes.c_double];fn.restype=ctypes.c_int
 texts=sorted(set(map(wording_normalized,corpus)));data=[q.encode() for q in texts];arr=(ctypes.c_char_p*len(data))(*data)
 def hit(q):return fn(wording_normalized(q).encode(),arr,len(data),.25)
 return hit

def main():
 census=jload(ROOT/'in/CENSUS.json');corp=jload(ROOT/'in/WORDING_CORPUS.json')
 pin(SRC);sources={r['qid']:r for r in map(json.loads,SRC.open())}
 for p in sorted((ROOT/'code').glob('*')):
  if p.suffix in ('.py','.cpp','.so'):pin(p)
 pin(ROOT/'in/procedure_source.json');seal=jload(W/'out/TREE_SEAL.json')
 for rel in ['student_pilot/ground_rows.py','student_pilot/r1_rooms.py','student_pilot/trace_grammar.py','student_pilot/r1_counting.py','student_pilot/r1_training.py','generator/derivgen_v7/derivgen/ground_v312_quality.py','evalpath/run.py','evalpath/official.py']:
  pp=pin(TREE/rel);assert pp['sha256']==seal['files'][rel],rel
 # Verify frozen w19 copies agree for the validator closure used here.
  assert sha(W/'work/build19/proofs/final/frozen/work/tree_r1'/rel)==pp['sha256']
 rooms,room_status,_=setup_rooms();hit=distance_filter(corp['questions'])
 pools=collections.defaultdict(list)
 for pair in census['pairs']:pools[pair['bucket']].append(pair)
 for k in pools:pools[k].sort(key=lambda p:hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest())
 source_use=collections.Counter();pair_use=collections.Counter();scene_use=collections.Counter();orientation_use=collections.Counter();refused=collections.Counter()
 selected=[];valid_source=set();cells=collections.Counter();spos={}
 def choose(tid,bucket,relation,ordinal):
  # Choose a minimally reused pair/source before the stable hash, subject to exact caps.
  candidates=sorted(pools[bucket],key=lambda p:(pair_use[pairkey(p)],source_use[p['source_qid']],scene_use[sources[p['source_qid']]['provenance']['canonical']],hashlib.sha256((str(tid)+p['source_qid']+p['a']+p['b']).encode()).hexdigest()))
  for p in candidates:
   src=sources[p['source_qid']];key=pairkey(p);scene=src['provenance']['canonical']
   if source_use[src['qid']]>=8 or pair_use[key]>=(1 if relation=='tie' else 4) or scene_use[scene]>=24 or orientation_use[(key,relation)]>=2:continue
   a,b,na,nb=p['a'],p['b'],p['na'],p['nb']
   if (relation=='more' and na<nb) or (relation=='fewer' and na>nb):a,b,na,nb=b,a,nb,na
   q=TEMPLATES[tid].format(a=a,b=b)
   if hit(q)>=0:refused['normalized_edit_distance_le_0.25']+=1;continue
   if src['qid'] not in valid_source:
    native_pack_check(src)
    errors=trace_grammar.validate_row(src)
    if errors:refused['source_grammar']+=1;continue
    valid_source.add(src['qid'])
   assert room_status(src)=='ok'
   answer_index=(tid*200+ordinal)%3
   content='equal number' if relation=='tie' else relation
   wrong=[s for s in ['more','fewer','equal number'] if s!=content]
   if int(hashlib.sha256(q.encode()).hexdigest()[:8],16)%2:wrong.reverse()
   opt=wrong[:answer_index]+[content]+wrong[answer_index:]
   opts=[chr(65+i)+'. '+s for i,s in enumerate(opt)];ans=chr(65+answer_index)
   x=copy.deepcopy(src)
   for field in ('count_kind','count_arity'):x.pop(field,None)
   qid='sb_rowC_'+hashlib.sha256(f'{tid}|{src["qid"]}|{a}|{b}|{ordinal}'.encode()).hexdigest()[:24]
   x.update(qid=qid,question_type='relative_count',category='relative_count',answer=ans)
   x['student_input'].update(question=q,options=opts)
   comparison=(f'So the {a} and {b} categories have equal counts.' if relation=='tie' else f'So the {a} category has {relation} instances than the {b} category.')
   x['target']=f'<think>\nStep 1: locate the distinct instances of {a}; count each once across the frames. The count is {na}.\nStep 2: locate the distinct instances of {b}; count each once across the frames. The count is {nb}.\nStep 3: {comparison}\n</think>\n\n{ans}'
   x['candidate_id']=identity(x)
   f=census['facts'][src['provenance']['raster']]
   pv=x['provenance'];pv.pop('count_kind');pv.pop('total_categories')
   pv['relative_count']=dict(source_qid=src['qid'],source_row_sha256=hashlib.sha256(json.dumps(src,sort_keys=True,separators=(',',':')).encode()).hexdigest(),template_id=tid,bucket=bucket,relation=relation,a=a,b=b,count_a=na,count_b=nb,ids_a=f['categories'][a]['ids'],ids_b=f['categories'][b]['ids'],room=rooms.room(scene),source_use_cap=8,unordered_pair_use_cap=4,orientation_use_cap=2,scene_use_cap=24)
   pv['input_sha256']={str(SRC):PINS[str(SRC)],f['path']:f['sha256'],str(ROOT/'code/generate.py'):PINS[str(ROOT/'code/generate.py')],str(ROOT/'code/wordings.py'):PINS[str(ROOT/'code/wordings.py')],str(ROOT/'in/CENSUS.json'):PINS[str(ROOT/'in/CENSUS.json')],str(ROOT/'in/WORDING_CORPUS.json'):PINS[str(ROOT/'in/WORDING_CORPUS.json')]}
   native_pack_check(x);r1_counting.admit(x,'counting');r1_training.row_check(x,'vqa')
   task=dict(answer_type='multiple_choice',options=opts,ground_truth=ans,question_type='relative_count')
   assert score_item(task,dict(text=x['target'],finish='eos'))['score']==1
   source_use[src['qid']]+=1;pair_use[key]+=1;scene_use[scene]+=1;orientation_use[(key,relation)]+=1
   cells[f'{tid:02}|{bucket}|{relation}']+=1;selected.append(x);return
  raise ValueError(f'SHORT_CELL {tid}|{bucket}|{relation} at {ordinal}')
 def pairkey(p):return (sources[p['source_qid']]['provenance']['canonical'],*sorted([p['a'],p['b']]))
 # Scarce large-count cells receive first access to sources. Quotas stay fixed.
 for tid in range(20):
  ordinal=0
  for bucket in ['10','9','8','7','6','5','4','3','2']:
   for relation in ['more','fewer']:
    for k in range(BUCKET_QUOTAS[bucket]):choose(tid,bucket,relation,ordinal);ordinal+=1
  for k in range(20):choose(tid,'tie','tie',ordinal);ordinal+=1
  assert ordinal==200
  print('template',tid,'rows',len(selected),flush=True)
 assert len(selected)==4000 and len({r['qid'] for r in selected})==len({r['candidate_id'] for r in selected})==4000
 for tid in range(20):
  for bucket,n in BUCKET_QUOTAS.items():
   for rel in ['more','fewer']:assert cells[f'{tid:02}|{bucket}|{rel}']==n
  assert cells[f'{tid:02}|tie|tie']==20
 # Stable mixed order avoids presenting curriculum blocks to a sequential reader.
 selected.sort(key=lambda r:hashlib.sha256(('shuffle|'+r['qid']).encode()).hexdigest())
 path=ROOT/'out/relative_count.jsonl'
 with path.open('w') as f:
  for x in selected:f.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')
 counts=dict(rows=len(selected),cells=dict(cells),source_rows=len(source_use),max_source_use=max(source_use.values()),max_pair_use=max(pair_use.values()),max_scene_use=max(scene_use.values()),refused=dict(refused),wording_templates=20,wording_corpus=len(corp['questions']),distance_threshold=.25,tree_seal=seal['tree_sha256'])
 dump(ROOT/'out/BUILD.json',dict(input_sha256=PINS,output=pin(path),counts=counts))
 status('The procedure-only relative_count family contains 4,000 rows. Exact template, relation, and count-range cells passed; independent GT recomputation, the complete field-diff audit, and the 30-row read remain pending. The shared direct grammar conflict is tracked separately from native pack/validate.')
 print(json.dumps(counts))
if __name__=='__main__':main()
