from common import *
OUT=L/'out/away_opp_v1';RA=L/'work/b13/renderings/facing_ra.jsonl';PHRASE='facing in the opposite direction of';SEED='rows_r1_opp_v1'
def rewrite(source):
 r=copy.deepcopy(source);q=r['student_input']['question'];t=r['target']
 q2,n=re.subn(r'\b(?:turned away from|facing away from|with my back to)\b',PHRASE,q,count=1);assert n==1
 t2,n=re.subn(r'The question has me face away from the ',f'The question has me {PHRASE} the ',t,count=1);assert n==1
 r['student_input']['question']=q2;r['target']=t2
 r['provenance']['rendering']=dict(kind='ra',phrase=PHRASE,source_question_sha256=digest(q),source_target_sha256=digest(t),version='b13_v1')
 return r
def main():
 assert not OUT.exists();assert sha(RA)=='9d7080aec48017dfff9ae35f8f734b06424eddd5b9eb4714cfce217e49f8e5fc'
 assert sha(V6)=='0608dd985243e5e68dfd8206cbd474350b97b3af8d238cab5b562bd4354b3092'
 base=con(V6);proof=0;rendered={};mismatches=[]
 for line in open(RA):
  e=json.loads(line);r=e['row']
  if PHRASE not in r['student_input']['question']:continue
  source=json.loads(base.execute('select row from rows where i=?',(e['i'],)).fetchone()[0]);rewritten=rewrite(source)
  if rewritten['student_input']['question']!=r['student_input']['question'] or rewritten['target']!=r['target']:mismatches.append(e['i'])
  assert rewritten['provenance']['rendering']==r['provenance']['rendering']
  proof+=1;rendered[e['i']]=r
 dump(W/'AWAY_REWRITE_PROOF.json',dict(status='PASS' if not mismatches and proof==3013 else 'FAIL',rows=proof,mismatches=mismatches,code_sha256=sha(__file__)))
 assert proof==3013 and not mismatches,('STOP: ra rewrite mismatch',proof,mismatches)
 groups=collections.defaultdict(list)
 for i,raw in base.execute('select i,row from rows order by i'):
  r=json.loads(raw)
  if r.get('facing')=='away':groups[r['question_type']].append((digest(SEED+r['qid']),i,r['qid']))
 total=sum(map(len,groups.values()));assert total==17479
 quota={k:len(v)*8740//total for k,v in groups.items()};left=8740-sum(quota.values())
 for k in sorted(groups,key=lambda k:(-(len(groups[k])*8740%total),k))[:left]:quota[k]+=1
 selected=sorted([x for k,v in groups.items() for x in sorted(v)[:quota[k]]]);out=[];counts=collections.Counter();ra_used=0
 for h,i,qid in selected:
  if i in rendered:r=copy.deepcopy(rendered[i]);ra_used+=1
  else:r=rewrite(json.loads(base.execute('select row from rows where i=?',(i,)).fetchone()[0]))
  r['qid']=qid+'_opp';r['pool']='r1_away_opp';assert r['facing']=='away'
  r['provenance']['rendering'].update(derived_from_v6_i=i,derived_from_v6_qid=qid,selection_seed=SEED)
  assert not grammar.validate_row(r),(qid,grammar.validate_row(r));out.append(r);counts[(r['question_type'],r['dataset'])]+=1
 OUT.mkdir();db=newdb(OUT/'rows.sqlite')
 for i,r in enumerate(out):db.execute('insert into rows values(?,?,?)',(i,json.dumps(r,sort_keys=True),'{}'))
 db.commit();db.close()
 dump(OUT/'COUNTS.json',dict(rows=len(out),cells=[dict(question_type=t,dataset=d,rows=n) for (t,d),n in sorted(counts.items())],type_quota=quota,source_type_counts={k:len(v) for k,v in groups.items()},seed=SEED,selection_rule='largest remainder proportional type quotas; ascending sha256(seed+qid) within type; output globally sorted by selection hash',ra_reused=ra_used,new_rewrites=8740-ra_used,away_fraction='8740/26219',rewrite_proof=json.load(open(W/'AWAY_REWRITE_PROOF.json'))))
 samples(OUT/'SAMPLES_20.md',out,20,'away_samples_v1');print('AWAY BUILT',len(out),quota,flush=True)
if __name__=='__main__':main()
