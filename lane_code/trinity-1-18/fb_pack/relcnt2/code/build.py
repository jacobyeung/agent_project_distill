"""Render balanced templates from selected, pinned total-count sources."""
from common import *
from wordings import TEMPLATES
from priors import evaluate
import collections,copy,random
PREVIOUS=ROOT.parent/'relcnt'

def allocate(selected,quotas):
 result=collections.defaultdict(list)
 for bucket in [str(i) for i in range(10,1,-1)]+['tie']:
  ps=[p for p in selected if p['bucket']==bucket]
  q=20 if bucket=='tie' else quotas[bucket]
  for attempt in range(100):
   rng=random.Random(1000*int(bucket if bucket!='tie' else 11)+attempt)
   loads=collections.Counter();assign=[];odd=0;ok=True
   rng.shuffle(ps);ps.sort(key=lambda p:-p['uses'])
   for p in ps:
    if bucket=='tie':rels=['tie']
    else:
     rels=['more','fewer']*(p['uses']//2)
     if p['uses']%2:rels.append('more' if odd%2==0 else 'fewer');odd+=1
    used=set()
    for rel in rels:
     tids=[tid for tid in range(20) if tid not in used and loads[(tid,rel)]<q]
     if not tids:ok=False;break
     tid=min(tids,key=lambda t:(loads[t,rel],rng.random()))
     loads[tid,rel]+=1;used.add(tid);assign.append((tid,rel,p))
    if not ok:break
   if ok:
    assert all(loads[t,rel]==q for t in range(20) for rel in (['tie'] if bucket=='tie' else ['more','fewer']))
    for t,rel,p in assign:result[t].append((rel,p))
    break
  else:raise ValueError('Cannot allocate bucket '+bucket)
 return result

def main():
 prev=load(PREVIOUS/'out/BUILD.json');original=list(rows(PREVIOUS/'out/relative_count.jsonl'))
 assert PINS[str(PREVIOUS/'out/relative_count.jsonl')]==prev['output']['sha256']
 procedure=prev['procedure_body'];source_procedure=load(BASE/'in/procedure_source.json')
 assert thought(source_procedure).strip()=='Step 1: '+procedure.format(category='box')
 roommap={r['provenance']['canonical']:r['provenance']['relative_count']['room'] for r in original}
 census=load(BASE/'in/CENSUS.json');sources={r['qid']:r for r in rows(SRC)}
 seal=load(TREE.parent.parent/'out/TREE_SEAL.json')
 results={};selections={}
 for label,cap in [('65',.65),('60',.60)]:
  choice=load(ROOT/f'out/SELECTION_{label}.json');selected=choice['selected'];assert selected
  data=[dict(qid=p['source_qid'],a=p['a'],b=p['b'],na=p['na'],nb=p['nb'],relation='tie' if p['na']==p['nb'] else 'more' if p['na']>p['nb'] else 'fewer') for p in selected for _ in range(p['uses'])]
  scores=evaluate(data)
  gate=scores['mean_unequal']['accuracy']<=cap and scores['pair_majority']['accuracy_tie_upper']<=cap
  results[label]=dict(**choice['summary'],measured_priors=scores,gate='PASS' if gate else 'FAIL',surviving_rows=len(data) if gate else 0)
  selections[label]=choice
 chosen='60' if results['60']['surviving_rows']>=3000 else '65'
 assert results[chosen]['gate']=='PASS',results
 selected=selections[chosen]['selected'];quotas=selections[chosen]['summary']['per_template_bucket_quota'];assigned=allocate(selected,quotas)
 for name in ['build.py','common.py','wordings.py','priors.py','solve.py']:pin(ROOT/'code'/name)
 pin(ROOT/'code/run.sh');identity(original[0]);code_pins();inputs=dict(PINS)
 rendered=[];ntemplate=20+2*sum(quotas.values())
 for tid in range(20):
  tieindex=0;letter_counts=collections.Counter();wrong_counts=collections.Counter()
  for ordinal,(relation,p) in enumerate(assigned[tid]):
   src=sources[p['source_qid']];a,b,na,nb=p['a'],p['b'],p['na'],p['nb']
   cats={x['name']:x for x in src['provenance']['total_categories']}
   assert (na,nb)==(len(cats[a]['ids']),len(cats[b]['ids']))
   if relation=='tie':
    if a>b:a,b,na,nb=b,a,nb,na
    if tieindex%2:a,b,na,nb=b,a,nb,na
    tieindex+=1
   elif (relation=='more' and na<nb) or (relation=='fewer' and na>nb):a,b,na,nb=b,a,nb,na
   question=TEMPLATES[tid].format(a=a,b=b)
   index=(tid+{'more':0,'fewer':1,'tie':2}[relation]+letter_counts[relation])%3;letter_counts[relation]+=1;content='equal number' if relation=='tie' else relation
   wrong=[x for x in ['more','fewer','equal number'] if x!=content]
   if (tid+wrong_counts[relation,index])%2:wrong.reverse()
   wrong_counts[relation,index]+=1
   options=wrong[:index]+[content]+wrong[index:];options=[chr(65+i)+'. '+x for i,x in enumerate(options)];answer=chr(65+index)
   r=copy.deepcopy(src)
   for field in ('count_kind','count_arity'):r.pop(field,None)
   qid='fbp_relcnt2_'+hashlib.sha256(f'{tid}|{src["qid"]}|{a}|{b}|{ordinal}'.encode()).hexdigest()[:24]
   r.update(qid=qid,question_type='relative_count',category='relative_count',answer=answer)
   r['student_input'].update(question=question,options=options)
   comparison=(f'So there are as many {a} instances as {b} instances.' if relation=='tie' else f'So there are {relation} {a} instances than {b} instances.')
   r['target']='<think>\n'+procedure.format(category=a)+'\n'+procedure.format(category=b)+'\n'+comparison+'\n</think>\n\n'+answer
   r['candidate_id']=identity(r)
   pv=r['provenance'];pv.pop('count_kind');pv.pop('total_categories');fact=census['facts'][pv['raster']]
   assert fact['sha256']==pv['raster_sha256']
   pv['relative_count']=dict(source_qid=src['qid'],source_row_sha256=digest(src),template_id=tid,bucket=p['bucket'],relation=relation,a=a,b=b,count_a=na,count_b=nb,ids_a=cats[a]['ids'],ids_b=cats[b]['ids'],room=roommap[pv['canonical']],source_use_cap=8,unordered_pair_use_cap=4,orientation_use_cap=2,scene_use_cap=24)
   # Direct dependencies only; full transitive receipts remain in the audit files.
   pv['input_sha256']={str(SRC):inputs[str(SRC)],str(BASE/'in/CENSUS.json'):inputs[str(BASE/'in/CENSUS.json')],fact['path']:fact['sha256'],str(ROOT/'code/build.py'):inputs[str(ROOT/'code/build.py')],str(ROOT/'code/wordings.py'):inputs[str(ROOT/'code/wordings.py')],str(ROOT/f'out/SELECTION_{chosen}.json'):inputs[str(ROOT/f'out/SELECTION_{chosen}.json')],str(PREVIOUS/'out/BUILD.json'):inputs[str(PREVIOUS/'out/BUILD.json')],str(BASE/'in/procedure_source.json'):inputs[str(BASE/'in/procedure_source.json')]}
   rendered.append(r)
  assert tieindex==20 and len(assigned[tid])==ntemplate
 rendered.sort(key=lambda r:hashlib.sha256(('shuffle|'+r['qid']).encode()).hexdigest())
 out=ROOT/'out/relative_count.jsonl'
 with out.open('w') as f:
  for r in rendered:f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
 result=dict(status='BUILT',input_sha256=inputs,command='bash code/run.sh code/build.py',output=pin(out),rows=len(rendered),per_template_rows=ntemplate,per_template_bucket_quota=quotas,chosen_cap=float(chosen)/100,cap_trials=results,tree_seal=seal,procedure_body=procedure,procedure_store_qid=prev['procedure_store_qid'],procedure_authentication='Exact equality to pinned procedure_source.json and the prior authenticated packet BUILD.json; the large production store is not re-read.',recovery='No excluded source is used; selection uses only the eligible census.')
 dump(ROOT/'out/BUILD.json',result)
 status(f'The packet contains {len(rendered)} rows at the {result["chosen_cap"]:.2f} prior cap, with {ntemplate} rows per template and ten ties in each category order per template. Both measured leave-one-out prior gates pass. Independent validators, raster pins, wording distance, room audit, and the forty-row read remain pending.')
 print(json.dumps(dict(rows=len(rendered),chosen_cap=result['chosen_cap'],quotas=quotas,cap_trials={k:dict(rows=v['rows'],gate=v['gate'],mean=v['measured_priors']['mean_unequal'],pair=v['measured_priors']['pair_majority']) for k,v in results.items()})),flush=True)
if __name__=='__main__':main()
