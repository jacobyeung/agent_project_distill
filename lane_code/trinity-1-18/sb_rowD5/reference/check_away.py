"""Check source preservation and the type-specific half-turn consistency rule."""
from common import *
OUT=L/'out/away_opp_v1'
def options(r):
 result={}
 for option in r['student_input']['options']:
  m=re.fullmatch(r'([A-Z])\.\s*(.+)',option);assert m,option
  result[m[1]]=m[2].strip().lower()
 return result

def main():
 before_sha=sha(OUT/'rows.sqlite');base=con(V6);twins={};qids=set();sources={};groups=collections.defaultdict(list)
 assert sha(V6)=='0608dd985243e5e68dfd8206cbd474350b97b3af8d238cab5b562bd4354b3092'
 for i,raw in base.execute('select i,row from rows order by i'):
  r=json.loads(raw);qids.add(r['qid'])
  if r.get('facing')=='toward':assert r['pair_id'] not in twins;twins[r['pair_id']]=r
  elif r.get('facing')=='away':sources[i]=r;groups[r['question_type']].append((digest('rows_r1_opp_v1'+r['qid']),i))
 n=sum(map(len,groups.values()));quota={k:8740*len(v)//n for k,v in groups.items()}
 for k in sorted(groups,key=lambda k:(-(8740*len(groups[k])%n),k))[:8740-sum(quota.values())]:quota[k]+=1
 expected=sorted(x for k,v in groups.items() for x in sorted(v)[:quota[k]])
 actual=[];count=0;newids=set();counts=collections.Counter();failures=[];passed=set();cells=collections.Counter()
 phrase='facing in the opposite direction of'
 for i,raw,t in con(OUT/'rows.sqlite').execute('select * from rows order by i'):
  r=json.loads(raw);p=r['provenance']['rendering'];s=sources[p['derived_from_v6_i']];typ=r['question_type']
  assert i==count and t=='{}';count+=1
  assert r['qid']==s['qid']+'_opp' and r['qid'] not in qids and r['qid'] not in newids;newids.add(r['qid'])
  assert r['pool']=='r1_away_opp' and r['facing']=='away' and p['selection_seed']=='rows_r1_opp_v1'
  assert p['derived_from_v6_qid']==s['qid']
  unchanged=copy.deepcopy(r)
  for key in ('qid','pool','target'):unchanged[key]=s[key]
  unchanged['student_input']['question']=s['student_input']['question']
  unchanged['provenance'].pop('rendering');assert unchanged==s,(r['qid'],'source fields changed')
  q,nq=re.subn(r'\b(?:turned away from|facing away from|with my back to)\b',phrase,s['student_input']['question'],count=1)
  target,nt=re.subn(r'The question has me face away from the ',f'The question has me {phrase} the ',s['target'],count=1)
  assert nq==nt==1 and r['student_input']['question']==q and r['target']==target
  assert p['source_question_sha256']==digest(s['student_input']['question']) and p['source_target_sha256']==digest(s['target'])
  twin=twins[r['pair_id']];assert twin['question_type']==typ
  forward=options(twin)[twin['answer']];away=options(r)[r['answer']]
  if typ=='object_rel_direction_medium':
   assert set(options(r).values())=={'left','right','back'}
   allowed={'left':{'right','back'},'right':{'left','back'},'back':{'left','right'}}[forward]
  else:
   assert typ in ('object_rel_direction_easy','object_rel_direction_hard')
   flip={'left':'right','right':'left','front':'back','back':'front'}
   allowed={re.sub(r'\b(left|right|front|back)\b',lambda m:flip[m[0]],forward)}
  ok=away in allowed;counts[typ,'passed' if ok else 'failed']+=1;cells[typ,r['dataset']]+=1
  if ok:passed.add(r['qid'])
  else:failures.append(dict(qid=r['qid'],source_qid=s['qid'],dataset=r['dataset'],question_type=typ,pair_id=r['pair_id'],toward_answer_text=forward,allowed_away_texts=sorted(allowed),actual_away_text=away))
  assert not grammar.validate_row(r),(r['qid'],grammar.validate_row(r))
  actual.append((digest('rows_r1_opp_v1'+s['qid']),p['derived_from_v6_i']))
 assert count==8740 and actual==expected
 old=json.load(open(OUT/'HALF_TURN_FAILURES.json'))['failures'];assert len(old)==1299
 recovered=[r['qid'] for r in old if r['qid'] in passed]
 proof=json.load(open(W/'AWAY_REWRITE_PROOF.json'));assert proof['status']=='PASS' and proof['rows']==3013
 assert proof['code_sha256']==sha(W/'build_away.py')
 after_sha=sha(OUT/'rows.sqlite');assert before_sha==after_sha
 dump(OUT/'CHECK_HALF_TURN_V2.json',dict(status='FAIL' if failures else 'PASS',rows=count,source_preservation_passed=count,
  source_preservation_rule='All fields equal v6 source except exact question phrase and clause-line substitutions, qid, pool and rendering provenance. Answers, options, option letters, frames, pins and pair_id are exact.',
  per_type={typ:dict(passed=counts[typ,'passed'],failed=counts[typ,'failed']) for typ in sorted(groups)},
  cells=[dict(question_type=typ,dataset=ds,rows=n) for (typ,ds),n in sorted(cells.items())],
  medium_rule={'left':['back','right'],'right':['back','left'],'back':['left','right']},
  failures=failures,validator_failures=0,qid_collisions_v6=0,duplicate_new_qids=0,stratified_selection='PASS',
  previously_excluded=1299,previously_excluded_now_pass=len(recovered),previously_excluded_still_fail=[r['qid'] for r in old if r['qid'] not in passed],
  packet_unchanged=True,packet_sha256=before_sha,rewrite_proof=proof,checker_sha256=sha(__file__)))
 assert len(recovered)==1299 and not failures
 progress(f'Part 2 PASS: all {count:,} away rows preserve their v6 source labels and pass the corrected half-turn check, including all 1,299 specified medium rows. The existing away packet is unchanged; canonical exclusions still apply at merge.')
 print('AWAY V2 PASS',count,dict(counts),'RECOVERED',len(recovered),flush=True)
if __name__=='__main__':main()
