"""Independent semantic and source checks for the relative-count tally rows.
The native direct validator runs unchanged; failure prevents an overall PASS.
"""
import collections, hashlib, json, pathlib, re, sys, itertools, sqlite3
import build_rows as g
import tally_gate
from evalpath.run import score_item
ROOT=g.ROOT;OUT=ROOT/'out'
def read(p):return json.loads(pathlib.Path(p).read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def parse_tally(row):
 # The renderer has no blank line before </think>; enforce that exact layout.
 lines=row['target'].splitlines()
 assert len(lines)==8 and lines[0]=='<think>' and lines[1]=='Tally new instances at their first sampled frame:'
 assert lines[5]=='</think>' and lines[6]=='' and lines[7]==row['answer']
 cats=[];totals=[];hist=[]
 for text in lines[2:4]:
  m=re.fullmatch(r'([a-z][a-z -]*): (.+) -> ([1-9][0-9]*)\.',text);assert m,text
  cat,entries,total=m.groups();pairs=[]
  for entry in entries.split('; '):
   match=re.fullmatch(r'frame ([1-9][0-9]*): ([1-9][0-9]*)',entry);assert match,entry
   pairs.append(tuple(map(int,match.groups())))
  frames=[f for f,n in pairs]
  assert 1<=len(frames)<=32 and all(1<=f<=32 for f in frames)
  assert frames==sorted(set(frames)),frames
  assert sum(n for f,n in pairs)==int(total)
  cats.append(cat);totals.append(int(total));hist.append(dict(pairs))
 m=re.fullmatch(r'([1-9][0-9]*) ([<>=]) ([1-9][0-9]*)\.',lines[4]);assert m,lines[4]
 assert [int(m[1]),int(m[3])]==totals
 return cats,totals,hist,m[2]

def source_truth(row,cat):
 # Derive GT independently from structured source instance IDs, not output totals.
 p=row['provenance']
 if p.get('count_kind')=='single':
  hits=[line for line in row['target'].splitlines() if re.search(r'\bdistinct '+re.escape(cat)+r'(?: once|,| instances| at)',line)]
  assert len(hits)==1,(hits,cat)
  entries=p['instances'];ids=[v['id'] for v in entries];frames=[v['frame'] for v in entries]
  assert len(ids)==int(row['answer'])
 else:
  allcats=p['total_categories'];assert len({v['name'] for v in allcats})==len(allcats)
  assert sum(len(v['ids']) for v in allcats)==int(row['answer'])
  v=next(v for v in allcats if v['name']==cat);ids=v['ids'];frames=v['frames']
 assert len(set(ids))==len(ids)==len(frames)>0
 assert all(type(x)==int and 1<=x<=32 for x in frames)
 return set(ids),collections.Counter(frames),len(ids)

def diff(a,b,p=''):
 if a==b:return []
 if isinstance(a,dict) and isinstance(b,dict):
  return [v for k in sorted(set(a)|set(b)) for v in ([p+k] if k not in a or k not in b else diff(a[k],b[k],p+k+'.'))]
 return [p.rstrip('.')]

def run():
 generation=read(OUT/'GENERATION.json');audit=read(OUT/'AUDIT.json');manifest=read(OUT/'INPUTS.json')
 assert g.filehash(OUT/'INPUTS.json')==generation['input_manifest']['sha256']
 # Verify computational input pins again, including the exact store database.
 for path,pin in manifest['inputs'].items():assert g.filehash(path)==pin['sha256'],path
 rows=[json.loads(l) for l in open(OUT/'sb_rowC2.jsonl')];sources={r['qid']:r for l in open(OUT/'SOURCE_ROWS.jsonl') if (r:=json.loads(l))};audits={a['qid']:a for a in audit['rows']}
 assert g.filehash(OUT/'sb_rowC2.jsonl')==generation['rows_sha256']
 assert g.filehash(OUT/'SOURCE_ROWS.jsonl')==generation['source_rows_sha256']
 assert len(rows)==len(audits)==4000
 conn=sqlite3.connect('file:'+str(g.DB)+'?mode=ro',uri=True)
 ranges=read(g.STORE/'FAMILY_INDEX_RANGES.json')['families']['object_counting'];matched=set()
 for lo,hi in ranges:
  for raw, in conn.execute('select row from rows where i between ? and ?',(lo,hi)):
   original=json.loads(raw)
   if original['qid'] in sources:
    assert original==sources[original['qid']];matched.add(original['qid'])
 conn.close();assert matched==set(sources)
 cells=collections.Counter();directions=collections.Counter();usage=collections.Counter();letters=collections.Counter();pairs=set();native_fail=collections.Counter();native_examples=[];max_entries=0;high=0;changes=collections.Counter();clip_count=set();rooms=set();max_total=0
 # Instantiate actual room rule, independent from the generator's gate implementation.
 cfg=read(g.CFG);rr=g.Rooms(cfg['r1_training']['room_authority']);wh=g.Withheld()
 dev=read(g.W/'fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json')
 bench=read(g.W/'fixtures/work/records/revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json')
 def allnames(value):
  if isinstance(value,str):return {g.normroom(value)} if re.match(r'^(d[123]|scannet|scannetpp|scannetppv2|arkitscenes)/',value) else set()
  if isinstance(value,list):return set().union(*(allnames(v) for v in value)) if value else set()
  if isinstance(value,dict):return set().union(*(allnames(k)|allnames(v) for k,v in value.items())) if value else set()
  return set()
 devset=allnames({k:dev[k] for k in ['aliases','canonical','natives','rooms','physical_groups'] if k in dev})
 benchset=allnames({k:bench[k] for k in ['scenes','physical_groups','other_corpora']});benchset.update(g.normroom('/'.join(x)) for x in bench['rung1_tokens'])
 for r in rows:
  a=audits[r['qid']];p=r['provenance']['relative_count_tally'];s1,s2=[sources[q] for q in a['source_qids']]
  assert a['source_qids']==p['source_qids']
  for s in (s1,s2):assert digest(s)==p['source_row_sha256'][s['qid']]==a['source_row_sha256'][s['qid']]
  cats,totals,hists,op=parse_tally(r)
  assert tally_gate.validate(r)['totals']==totals
  assert cats==p['categories']==a['categories'] and totals==p['totals']
  question=r['student_input']['question']
  assert all(question.count('"'+cat+'"')==1 for cat in cats)
  assert question==g.TEMPLATES[p['template_id']].format(a=cats[0],b=cats[1])
  allids=[]
  for index,(cat,s) in enumerate(zip(cats,(s1,s2))):
   ids,frames,count=source_truth(s,cat);allids.append(ids)
   assert dict(frames)==hists[index] and count==totals[index]
   if s['provenance']['count_kind']=='total':
    component=next(v for v in s['provenance']['total_categories'] if v['name']==cat)
    expected_pairs=list(zip(component['ids'],component['frames']))
   else:expected_pairs=[(v['id'],v['frame']) for v in s['provenance']['instances']]
   assert sorted(map(tuple,a['ids_and_first_frames'][index]))==sorted(expected_pairs)
   # Separately count frame entries in the original textual evidence.
   source_line=next(line for line in s['target'].splitlines() if re.search(r'\bdistinct '+re.escape(cat)+r'(?: once|,| instances| at)',line))
   oldframes=list(map(int,re.findall(r'frame (\d+)',source_line)))
   assert collections.Counter(oldframes)==frames
  assert not (allids[0]&allids[1])
  n1,n2=totals;relation='more' if n1>n2 else 'fewer' if n1<n2 else 'equal number'
  assert op==('>' if n1>n2 else '<' if n1<n2 else '=')
  options=r['student_input']['options'];contents={x[0]:x.split('. ',1)[1] for x in options}
  assert sorted(contents.values())==['equal number','fewer','more'] and contents[r['answer']]==relation
  assert g.parse_answer(r['target'],options)['answer']==r['answer']
  score=score_item({'question_type':'relative_count','options':options,'ground_truth':r['answer']},{'text':r['target'],'finish':'eos'})
  assert score['score']==1.0 and score['official_fuzzy_pred']==r['answer'] and not score['parse_failed']
  assert r['question_type']==r['category']=='relative_count' and r['count_kind']=='relative' and r['count_arity']==2
  cf=lambda s:{k:v for k,v in s['student_input'].items() if k not in ('question','options')}
  assert cf(r)==cf(s1)==cf(s2)
  assert (r['dataset'],r['scene'])==(s1['dataset'],s1['scene'])==(s2['dataset'],s2['scene'])
  assert len(cf(r)['frames'])==32
  identity=dict(qid=r['qid'],scene=r['scene'],frame_indices=cf(r)['frame_indices'],type='relative_count',question=question,options=options,trace_revision='3.14')
  assert g.candidate_identity(identity)==r['candidate_id']
  assert r['candidate_id'] not in {s.get('candidate_id') for s in sources.values()}
  expected='sb_rowC2_'+hashlib.sha256(g.jbytes([p['template_id'],p['clip_sha256'],*cats])).hexdigest()[:24];assert r['qid']==expected
  d=diff(s1,r);assert d==a['field_diff'];assert set(d)<={'qid','question_type','category','answer','target','candidate_id','count_kind','count_arity','student_input.question','student_input.options','provenance.relative_count_tally'}
  changes.update(d)
  for q in set(a['source_qids']):usage[q]+=1
  status,canonical,how=rr.status(r);assert status=='ok';room=rr.room(canonical);names={g.normroom(v) for v in [canonical,room,r['dataset']+'/'+r['scene']]}
  assert not wh.touches(r,{'names':[canonical,room]}) and not names&devset and not names&benchset
  assert (canonical,room)==(a['canonical'],a['room']);rooms.add(room)
  pair=(p['clip_sha256'],*sorted(cats));assert pair not in pairs;pairs.add(pair);clip_count.add(pair[0])
  size='high' if max(totals)>=5 else 'low';high+=size=='high';max_total=max(max_total,*totals)
  assert [relation,size]==a['cell'] and relation==p['relation'] and size==p['size_cell']
  cells[f'{p["template_id"]:02d}|{relation}|{size}']+=1;directions[relation]+=1;letters[r['answer']]+=1
  max_entries=max(max_entries,*map(len,hists))
  g.native_envelope(r);error=g.native_direct(r)
  assert error==a['native_direct_error']
  if error:
   native_fail[error]+=1
   if len(native_examples)<3:native_examples.append({'qid':r['qid'],'error':error,'target':r['target']})
 assert max(usage.values())<=g.REUSE_CAP and dict(usage)==audit['source_usage']
 assert len({r['qid'] for r in rows})==len({r['candidate_id'] for r in rows})==4000
 assert high==1600 and directions=={'more':1800,'fewer':1800,'equal number':400}
 for tid in range(20):
  for (rel,size),n in g.QUOTAS.items():assert cells[f'{tid:02d}|{rel}|{size}']==n
 assert dict(cells)==generation['cells']
 srcfails=collections.Counter()
 for q,s in sources.items():
  g.native_envelope(s);error=g.native_direct(s);assert error==audit['source_native_direct'][q]
  if error:srcfails[error]+=1
 # Test the exact edit-distance implementation against conventional dynamic programming.
 def dp(a,b):
  row=list(range(len(b)+1))
  for i,x in enumerate(a):
   nxt=[i+1]
   for j,y in enumerate(b):nxt.append(min(nxt[-1]+1,row[j+1]+1,row[j]+(x!=y)))
   row=nxt
  return row[-1]
 words=['','a','b','ab','aa','aba','abb','bbb','chair','chairs','equal number']
 for a,b in itertools.product(words,repeat=2):assert g.levenshtein(a,b)==dp(a,b)
 refs,paths=g.collect_questions();threshold=generation['wording_filter']['reject_threshold_inclusive'];tested=0
 assert threshold==0.25
 from novelty import Filter
 fast=Filter(refs)
 for r in rows:
  q=g.normalized(r['student_input']['question'])
  assert fast.match(q)==-1
  tested+=1
 # Negative mutations exercise the mathematical checker, not the old lexical grammar.
 import copy
 sample=rows[0];negative={}
 mutations={
  'duplicate_frame':lambda t:re.sub(r'(frame \d+: \d+)',r'\1; \1',t,count=1),
  'frame_33':lambda t:re.sub(r'frame \d+:','frame 33:',t,count=1),
  'wrong_sum':lambda t:re.sub(r'-> \d+\.', '-> 999.',t,count=1),
  'zero_increment':lambda t:re.sub(r'(frame \d+: )\d+',r'\g<1>0',t,count=1),
 }
 for label,mutate in mutations.items():
  bad=copy.deepcopy(sample);bad['target']=mutate(bad['target'])
  try:parse_tally(bad)
  except AssertionError:negative[label]='PASS (refused)'
  else:raise AssertionError('Mutation accepted: '+label)
 report={'schema':'sb-rowC2-checks-v1','status':'BLOCKED_NATIVE_GRAMMAR' if native_fail or srcfails else 'PASS',
  'required_all_checks_pass':not(native_fail or srcfails),'rows':4000,'semantic_checks':'PASS','exact_cells':'PASS','cells':dict(cells),'directions':dict(directions),'tie_share':.10,'five_or_more_rows':high,'five_or_more_share':high/4000,'unique_pairs':len(pairs),'clips':len(clip_count),'rooms':len(rooms),'unique_source_rows':len(sources),'max_source_reuse':max(usage.values()),'source_reuse_cap':g.REUSE_CAP,'source_reuse_histogram':dict(collections.Counter(usage.values())),'max_entries_per_category':max_entries,'max_category_total':max_total,'answer_letters':dict(letters),'unique_qids':4000,'unique_candidate_ids':4000,'candidate_id_recomputed':4000,'fields_changed':dict(changes),'ground_truth_independently_recomputed':4000,'same_clip_and_exact_frame_metadata':4000,'room_exclusion_hits':{'K1':0,'R0':0,'withheld80':0,'devS1':0,'BENCHv2':0},'native_pack_envelope':{'new_pass':4000,'source_pass':len(sources),'scope':'Normalized adapter to ground_rows.pack/validate; this does not certify direct VQA intake.'},'native_vqa_intake':{'new_pass':4000-sum(native_fail.values()),'new_fail':sum(native_fail.values()),'source_pass':len(sources)-sum(srcfails.values()),'source_fail':sum(srcfails.values()),'new_errors':dict(native_fail),'source_errors':dict(srcfails),'examples':native_examples},'wording_filter':generation['wording_filter'],'wording_independent_checked_rows':tested,'distance_algorithm_dp_crosschecks':len(words)**2,'negative_tally_tests':negative,'manual_read30':'PENDING','input_sha256':{p:v['sha256'] for p,v in manifest['inputs'].items()},'input_manifest':generation['input_manifest'],'artifact_sha256':{p.name:g.filehash(p) for p in [OUT/'sb_rowC2.jsonl',OUT/'SOURCE_ROWS.jsonl',OUT/'AUDIT.json',OUT/'GENERATION.json',pathlib.Path(__file__)]}}
 from test_tally_gate import exercise
 report['standalone_gate_tests']=exercise()
 report['artifact_sha256']['test_tally_gate.py']=g.filehash(ROOT/'test_tally_gate.py')
 (OUT/'CHECKS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:report[k] for k in ['status','rows','semantic_checks','unique_pairs','clips','rooms','unique_source_rows','max_source_reuse','max_entries_per_category','native_vqa_intake']},indent=2))
 (ROOT/'STATUS.md').write_text('Independent semantic checks pass for all 4,000 rows: GT instance IDs, per-frame tallies, sums, option answers, clip identity, exact cells, source reuse, IDs, and room exclusions. Native pack-envelope checks pass, but the unchanged N direct VQA intake rejects the tally syntax. The packet remains unadmitted. Manual review of 30 full rows and packaging remain.\n')
if __name__=='__main__':run()
