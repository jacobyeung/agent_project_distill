"""Independently audit emitted counting inventories against annotated source identities."""
import argparse,collections,copy,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(4194304),b''):h.update(chunk)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def rows(p):
 with Path(p).open() as f:
  for line in f:
   if line.strip():yield json.loads(line)
def require(x,msg):
 if not x:raise ValueError(msg)
def audit(out):
 checks=load(out/'CHECKS.json');manifest=load(ROOT/'inputs/INPUTS.json');sys.path.insert(0,manifest['tree']);sys.dont_write_bytecode=True
 from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
 from student_pilot.r1_rooms import Rooms
 from student_pilot.s1_exclusions import Exclusions
 I=ROOT/'inputs';pins=manifest['pins'];authority={k:{'path':str(I/(k+'.json')),'sha256':pins[k+'.json']['sha256']} for k in ('split','reserve','aliases','build','visits')}
 rooms=Rooms(authority);ex=Exclusions({'path':str(I/'dev.json'),'sha256':pins['dev.json']['sha256']},{'path':str(I/'bench.json'),'sha256':pins['bench.json']['sha256']})
 withheld=set(load(I/'withheld.json')['rooms']);facts=load(I/'scene_facts.json')['facts']
 sources={r['qid']:r for r in rows(I/'removed_rows.jsonl')};mapping={r['new_qid']:r for r in rows(out/'QID_MAP.jsonl')}
 originals=load(I/'source_ids.json')['ids'];alloldids={x[0] for x in originals};alloldcids={x[1] for x in originals if x[1]}
 source_hashes={json.loads(line)['qid']:hashlib.sha256(line.rstrip('\n').encode()).hexdigest() for line in (I/'removed_rows.jsonl').open()}
 refused=list(rows(out/'REFUSALS.jsonl'));refids={r['old_qid'] for r in refused};newids=set();cids=set();used=set();c=collections.Counter();hist=collections.Counter();cells=collections.Counter();pools=collections.Counter()
 for r in rows(out/'rows.jsonl'):
  m=mapping[r['qid']];s=sources[m['old_qid']];p=s['provenance'];note=r['provenance']['sb_rowT']
  require(m['old_qid'] not in used,'source repeated');used.add(m['old_qid'])
  require(r['qid'] not in newids and r['candidate_id'] not in cids,'duplicate new id');newids.add(r['qid']);cids.add(r['candidate_id'])
  require(r['qid'] not in alloldids and r['candidate_id'] not in alloldcids,'new id is original')
  rr=copy.deepcopy(r);rr['qid']=s['qid'];rr['target']=s['target'];rr.pop('candidate_id');rr['provenance'].pop('sb_rowT')
  require(rr==s,'unexpected source field changed')
  require(r['candidate_id']==candidate_identity(note['candidate_identity_record']),'candidate formula differs')
  require(note['candidate_identity_record']['qid']==r['qid'] and note['candidate_identity_record']['question']==r['student_input']['question'],'candidate binding differs')
  require(note['candidate_identity_record']=={'qid':r['qid'],'scene':s['scene'],'frame_indices':s['student_input']['frame_indices'],'type':s['question_type'],'question':s['student_input']['question'],'options':s['student_input']['options'],'trace_revision':'sb_rowT-v1-'+checks['form']},'candidate input record differs')
  require(note['source_row_sha256']==source_hashes[s['qid']],'source byte hash differs')
  require(note['source_target_sha256']==hashlib.sha256(s['target'].encode()).hexdigest(),'source target hash differs')
  canonical=rooms.canonical(s)[0]
  if canonical is None:
   fact=facts[s['dataset']+'/'+s['scene']];require(len(fact)==1,'ambiguous fact');canonical=next(iter(fact))
  require(canonical==note['canonical'],'canonical unsupported')
  room=rooms.room(canonical);require(room==note['physical_room'],'room differs')
  probe=dict(s,canonical=canonical,physical_group=room)
  require(rooms.status(probe)[0]=='ok' and room not in withheld and not ex.excluded(probe),'excluded room admitted')
  annotation={};ids={};regions={}
  if 'total_categories' in p:
   for cat in p['total_categories']:
    annotation[cat['name']]=collections.Counter(cat['frames']);ids[cat['name']]=cat['ids']
  elif 'instances' in p:
   name=next(iter(m['categories']));annotation[name]=collections.Counter(x['frame'] for x in p['instances']);ids[name]=[x['id'] for x in p['instances']];regions[name]=collections.Counter((x['frame'],x['region']) for x in p['instances'])
  elif 'cited' in s.get('retrace_a2',{}):
   name=next(iter(m['categories']));annotation[name]=collections.Counter(s['retrace_a2']['cited'].values());ids[name]=list(s['retrace_a2']['cited'])
  else:raise ValueError('missing independent annotation')
  for name,values in ids.items():require(len(values)==len(set(values)),'duplicate annotation instance')
  all_instance_ids=[i for values in ids.values() for i in values]
  require(len(all_instance_ids)==len(set(all_instance_ids)),'instance counted across categories')
  expected_answer=sum(len(x) for x in ids.values());require(expected_answer==int(r['answer']),'independent answer differs')
  # Parse source inventory with a separate occurrence scanner. Region evidence
  # for multi-category rows exists in the source target, not the structured GT.
  source_regions={};source_sequence=[]
  for line in s['target'].replace('\\n','\n').splitlines():
   if ': frame ' not in line:continue
   header,inventory=line.rsplit(': ',1)
   for name in sorted(annotation,key=len,reverse=True):
    if 'distinct '+name+' ' in header or 'distinct '+name+',' in header:
     require(name not in source_regions,'duplicate source section')
     source_regions[name]=collections.Counter((int(f),reg or '') for f,reg in re.findall(r'frame (\d+)(?: \((left|middle|right)\))?',inventory));source_sequence.append(name);break
   else:raise ValueError('source category not matched')
  require(set(source_regions)==set(annotation),'source missing category')
  actual={};actual_regions={};declared={};lines=r['target'].splitlines()
  if checks['form']=='tally':
   for line in lines:
    if not line.startswith('TALLY '):continue
    name,body=line[6:].split(': ',1);inventory,total=body.rsplit(' -> ',1)
    require(name not in actual,'duplicate tally category');declared[name]=int(total.removesuffix('.'));actual[name]=collections.Counter();actual_regions[name]=collections.Counter();previous=0
    for entry in inventory.split('; '):
     mt=re.fullmatch(r'frame (\d+): (\d+)(?: \((.*)\))?',entry);require(mt is not None,'malformed tally entry')
     f,n=int(mt[1]),int(mt[2]);require(previous<f<=32 and n>0,'frame order/range or count');previous=f;actual[name][f]=n
     if mt[3]:
      parts=mt[3].split(', ');tags={}
      for pair in parts:
       region,value=pair.split(': ');require(region in ('left','middle','right') and region not in tags,'bad region');tags[region]=int(value);require(tags[region]>0,'nonpositive region')
      require(sum(tags.values())==n,'region sum differs')
      actual_regions[name].update({(f,reg):v for reg,v in tags.items()})
     else:actual_regions[name][(f,'')]=n
    require(sum(actual[name].values())==declared[name],'category sum differs')
  else:
   labels=collections.defaultdict(set)
   for line in lines:
    if not line.startswith('Locate: '):continue
    mt=re.fullmatch(r'Locate: (.+) instance (tag_[a-z]+) in frame (\d+)(?: \((left|middle|right)\))?\.',line);require(mt is not None,'malformed Locate')
    name,label,f,reg=mt[1],mt[2],int(mt[3]),mt[4] or '';require(1<=f<=32 and label not in labels[name],'Locate frame/id');labels[name].add(label)
    actual.setdefault(name,collections.Counter())[f]+=1;actual_regions.setdefault(name,collections.Counter())[(f,reg)]+=1
   for index,line in enumerate(lines):
    mt=re.fullmatch(r'Step \d+: list distinct instances of (.+): (.+)\.',line)
    if mt:
     name=mt[1];ls=mt[2].split('; ')
     count=re.fullmatch(r'Step \d+: So the count is (\d+)\.',lines[index+1]);require(count is not None,'missing Locate count')
     require(set(ls)==labels[name] and len(ls)==len(set(ls))==int(count[1]),'Locate count list differs');declared[name]=int(count[1])
  require(actual==annotation,'output differs from independent frame annotation')
  require(actual_regions==source_regions,'output loses or changes source region evidence')
  for name,reg in regions.items():require(reg==actual_regions[name],'instance region annotation differs')
  require(set(declared)==set(annotation),'category count missing')
  require(sum(declared.values())==expected_answer,'row sum differs')
  if checks['form']=='locate':
   for mt in re.finditer(r'(\d+) \+ (\d+) = (\d+)',r['target']):require(int(mt[1])+int(mt[2])==int(mt[3]),'bad addition')
  if checks['form']=='tally' and len(annotation)>1:
   total=next(line for line in lines if line.startswith('Total: '));left,right=total[7:-1].split(' = ');terms=[int(x) for x in left.split(' + ')]
   require(terms==list(declared.values()) and sum(terms)==int(right)==expected_answer,'bad total')
  require(r['target'].startswith('<think>\n') and r['target'].endswith('\n</think>\n\n'+str(expected_answer)),'target envelope')
  cell='single' if len(annotation)==1 else 'multiple';cells[cell]+=1;pools[s['pool']]+=1;hist[str(min(expected_answer,10)) if expected_answer<10 else '10+']+=1;c['rows']+=1
  c['instances']+=expected_answer;c['category_inventories']+=len(annotation);c['region_tagged_rows']+=int(any(reg for inv in actual_regions.values() for _,reg in inv));c['passed']+=1
 require(used.isdisjoint(refids) and used|refids==set(sources),'coverage mismatch')
 require(cells==checks['eligible_cells'],'cell mismatch')
 require(c['rows']==checks['eligible_rows']==len(mapping),'row count mismatch')
 reported=load(out/'TRUTH_HISTOGRAM.json')['row_truth'];require(all(hist[k]==v for k,v in reported.items()),'histogram mismatch')
 result={'input_sha256':{'checker':sha(Path(__file__)),'rows':sha(out/'rows.jsonl'),'mapping':sha(out/'QID_MAP.jsonl'),'sources':sha(I/'removed_rows.jsonl'),'refusals':sha(out/'REFUSALS.jsonl'),'inputs':sha(I/'INPUTS.json')},'status':'PASS','counts':dict(c),'cells':dict(cells),'pools':dict(pools),'checks':['Source-use bound 1','qid/candidate uniqueness','candidate kit formula','only allowed fields changed','complete removed-qid accounting','independent instance IDs and frame inventory','per-frame region preservation','frame range/order','category and final sums','stored answer','K1/R0/withheld80/devS1/BENCH rooms','histogram recount']}
 (out/'INDEPENDENT_CHECKS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result['counts']))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='out');args=ap.parse_args();audit(ROOT/args.out)
