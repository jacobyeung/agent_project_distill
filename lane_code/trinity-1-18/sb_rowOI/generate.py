"""Build 504 matched pairs from B12 GT inventories, without training or RGB reads."""
import os
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,json,hashlib,copy,itertools,collections,re,unicodedata,ctypes
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
sys.path.insert(0,str(TREE))
from student_pilot import ground_rows,trace_grammar
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
TEMPLATES=[
 'Across the clip, count distinct objects in these categories together: {cats}. Give the combined count as a single number.',
 'For the categories {cats}, what combined object count does the clip show? Respond with the total as a number.',
 'Consider {cats} throughout the clip. How many separate objects belong to these categories altogether? Give a numeric total.',
 'Report a single total for the distinct objects belonging to {cats} in the clip. Count each object only once.',
 'Using the entire clip, combine the object counts for {cats}. What number do they sum to? Give just the numeric total.',
 'Tally the separate objects in the clip for {cats}, then combine those tallies. Return the overall count as one number.'
]
UNCOUNTABLE={'furniture','toilet paper','paper','clothing','clothes','laundry','bedding','food','trash','garbage','clutter','equipment','luggage','cookware','cutlery','silverware','glassware','kitchenware'}
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def norm(s):return ' '.join(re.sub(r'[^\w\s]',' ',unicodedata.normalize('NFKC',s).casefold()).split())
def joined(cats):return ', '.join(cats[:-1])+' and '+cats[-1]
def allocate(scenes):
    """Integral flow reserves scarce clip capacity before any wording is selected."""
    graph=collections.defaultdict(list)
    def edge(a,b,cap):
        x=[b,cap,None];y=[a,0,x];x[2]=y;graph[a].append(x);graph[b].append(y);return x
    refs={};options={}
    for k in (4,3,2):
      for rep in (3,2):edge('S',('group',k,rep),84)
    for si,s in enumerate(scenes):
      edge(('scene',si),'T',min(12,2*len(s['source_qids'])))
      for k in (4,3,2):
        ones=sorted(c for c,v in s['categories'].items() if len(v)==1)
        sets=set()
        for rep in (3,2):
          many=sorted(c for c,v in s['categories'].items() if len(v)==rep);opts=[]
          for one in itertools.combinations(ones,k):
            for more in many:
              if all(not(set(a.split())&set(b.split())) for a,b in itertools.combinations((*one,more),2)):opts.append((one,more))
          options[k,rep,si]=opts;distinct={one for one,more in opts};sets|=distinct
          control_sets={tuple(sorted((*one[:j],*one[j+1:],more))) for one,more in opts for j in range(k)}
          refs[k,rep,si]=edge(('group',k,rep),('arity',k,si),min(12,len(distinct),len(control_sets)))
        edge(('arity',k,si),('scene',si),min(12,len(sets)))
    flow=0
    while True:
      parent={'S':None};queue=collections.deque(['S'])
      while queue and 'T' not in parent:
        a=queue.popleft()
        for e in graph[a]:
          if e[1]>0 and e[0] not in parent:parent[e[0]]=(a,e);queue.append(e[0])
      if 'T' not in parent:break
      node='T';amount=10000
      while node!='S':a,e=parent[node];amount=min(amount,e[1]);node=a
      node='T'
      while node!='S':a,e=parent[node];e[1]-=amount;e[2][1]+=amount;node=a
      flow+=amount
    assert flow==504,('allocation_short',flow)
    return {key:e[2][1] for key,e in refs.items()},options
def identity(r):return candidate_identity(dict(qid=r['qid'],scene=r['scene'],frame_indices=r['student_input']['frame_indices'],type=r['question_type'],question=r['student_input']['question'],options=[],trace_revision='3.14'))
def plan_pairs(scenes,allocation,options):
    """Match control sets to singleton sets jointly across both multiplicities."""
    plans=collections.defaultdict(list)
    for si,s in enumerate(scenes):
      for k in (4,3,2):
        quotas={rep:allocation[k,rep,si] for rep in (3,2)}
        if not sum(quotas.values()):continue
        graph=collections.defaultdict(list);refs=[];controls=set();ones=set()
        def edge(a,b,cap):
          x=[b,cap,None];y=[a,0,x];x[2]=y;graph[a].append(x);graph[b].append(y);return x
        for rep,n in quotas.items():
          edge('S',('rep',rep),n)
          if not n:continue
          for one,more in options[k,rep,si]:
            if one not in ones:edge(('one',one),'T',1);ones.add(one)
            for j in range(k):
              ctrl=tuple(sorted((*one[:j],*one[j+1:],more)));key=(rep,ctrl)
              if key not in controls:edge(('rep',rep),('ctrl',rep,ctrl),1);controls.add(key)
              refs.append((rep,one,more,one[j],edge(('ctrl',rep,ctrl),('one',one),1)))
        flow=0
        while True:
          parent={'S':None};queue=collections.deque(['S'])
          while queue and 'T' not in parent:
            a=queue.popleft()
            for e in graph[a]:
              if e[1] and e[0] not in parent:parent[e[0]]=(a,e);queue.append(e[0])
          if 'T' not in parent:break
          node='T'
          while node!='S':a,e=parent[node];e[1]-=1;e[2][1]+=1;node=a
          flow+=1
        assert flow==sum(quotas.values()),('local_matching_short',s['canonical'],k,quotas,flow)
        for rep,one,more,swapped,e in refs:
          if e[2][1]:plans[k,rep].append((si,one,more,swapped))
    assert all(len(plans[k,rep])==84 for k in (2,3,4) for rep in (2,3))
    return plans
def native(r):
    """Lossless direct-body adapter to ground_rows' mandatory answer-tag envelope.
    The delivered row remains in the store's direct schema and also passes its grammar.
    """
    errors=trace_grammar.validate_row(r)
    if errors:raise ValueError(str(errors))
    body=r['target'].split('\n</think>')[0]
    rec=dict(spec_version='3.14',qid=r['qid'],candidate_id=r.get('candidate_id') or identity(r),
             scene=r['scene'],frame_indices=r['student_input']['frame_indices'],type=r['question_type'],
             question=r['student_input']['question'],options=r['student_input']['options'],answer=r['answer'],
             gt_answer=r['answer'],gt_agrees=True,training_admitted=False,events=[],
             suffix=body+'\n</think>\n<answer>'+r['answer']+'</answer>')
    packed=ground_rows.pack(rec,r['provenance']);ground_rows.validate(packed)
    assert packed['target'].split('\n</think>')[0]==body
    assert packed['answer']==r['answer'] and packed['question']==r['student_input']['question']
    return packed
def main():
    inv=json.load(open('inputs/inventory.json')); refs=json.load(open('inputs/wordings.json'))
    inputs=dict(inv['input_sha256'])
    for p in ['inputs/inventory.json','inputs/wordings.json','inputs/sources.jsonl','generate.py','edit_distance.cpp',str(TREE/'student_pilot/ground_rows.py'),str(TREE/'student_pilot/trace_grammar.py'),str(TREE/'generator/derivgen_v7/derivgen/ground_v312_quality.py')]:inputs[str(Path(p).resolve())]=sha(p)
    sources={r['qid']:r for r in map(json.loads,open('inputs/sources.jsonl'))}
    words=[norm(q).encode() for q in refs['wordings']];array=(ctypes.c_char_p*len(words))(*words)
    lib=ctypes.CDLL(str(ROOT/'edit_distance.so'));lib.nearest.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_int];lib.nearest.restype=ctypes.c_double
    cachepins={str((ROOT/p).resolve()):sha(p) for p in ['inputs/wordings.json','edit_distance.cpp']}
    cache={}
    cachepath=ROOT/'distance_cache.jsonl'
    if cachepath.exists():
      for entry in map(json.loads,cachepath.open()):
        if entry['input_sha256']==cachepins:cache[entry['question']]=entry['distance']
    def distance(q):
      if q not in cache:
        cache[q]=lib.nearest(norm(q).encode(),array,len(words))
        with cachepath.open('a') as f:f.write(json.dumps(dict(input_sha256=cachepins,question=q,distance=cache[q]))+'\n')
      return cache[q]
    scenes=sorted(inv['scenes'],key=lambda s:digest(['sb_rowOI',s['canonical']]))
    scenes=copy.deepcopy(scenes)
    for s in scenes:s['categories']={c:v for c,v in s['categories'].items() if c not in UNCOUNTABLE}
    rowbasepins={str((ROOT/x).resolve()):inputs[str((ROOT/x).resolve())] for x in ('inputs/inventory.json','inputs/wordings.json','inputs/sources.jsonl','generate.py','edit_distance.cpp')}
    allocation,options=allocate(scenes)
    plans=plan_pairs(scenes,allocation,options)
    used=collections.Counter();sceneuses=collections.Counter();seen_sets=set();rows=[];proof=[];counts=collections.Counter();removed=collections.Counter();mind=1
    # Fill difficult cells first; singleton and control share source, template and k-1 categories.
    for k in (4,3,2):
      for rep in (3,2):
       for tid in range(6):
        cell=f'{k}|{rep}|{tid}';filled=0
        for si,selected,more,swapped in plans[k,rep][tid*14:(tid+1)*14]:
         s=scenes[si]
         assert sceneuses[s['canonical']]<12
         qids=sorted((q for q in s['source_qids'] if used[q]<4),key=lambda q:(used[q],q))
         assert qids
         for one in [selected]:
          one=list(one);pos=(tid*14+filled)%k
          j=one.index(swapped);one[pos],one[j]=one[j],one[pos]
          control=one.copy();control[pos]=more
          keys=[(s['canonical'],tuple(sorted(c))) for c in (one,control)]
          assert not any(key in seen_sets for key in keys)
          qs=[TEMPLATES[tid].format(cats=joined(c)) for c in (one,control)]
          ds=[distance(q) for q in qs]
          assert min(ds)>.20,('wording_refused',cell,qs,ds)
          src=sources[qids[0]]
          native(src)
          pair=digest([cell,src['qid'],one,more])[:24];new=[]
          for mode,cats,q,d in zip(('singleton','control'),(one,control),qs,ds):
           r=copy.deepcopy(src);r['qid']='sb_rowOI_'+pair+'_'+mode;r['answer']=str(sum(len(s['categories'][c]) for c in cats))
           r['student_input']['question']=q;r['count_kind']='total';r['count_arity']=k
           proc=[f'Step {i+1}: find each distinct {c}, across the frames, and count it once.' for i,c in enumerate(cats)]
           proc.append(f'Step {k+1}: the total is the sum of the {joined(cats)} counts.')
           r['target']='<think>\n'+'\n'.join(proc)+'\n</think>\n\n'+r['answer']
           # Replace only the old count evidence; preserve frame and license provenance.
           for field in ('instances','total_categories'):r['provenance'].pop(field,None)
           r['provenance']['count_kind']='total'
           r['provenance']['total_categories']=[dict(name=c,ids=[x['id'] for x in s['categories'][c]],frames=[x['first_pin'] for x in s['categories'][c]]) for c in cats]
           r['candidate_id']=identity(r)
           rowpins=dict(rowbasepins)
           rowpins[s['raster']]=s['raster_sha256']
           r['provenance']['sb_rowOI']=dict(source_qid=src['qid'],pair_id=pair,mode=mode,arity=k,repeated_count=rep if mode=='control' else 1,repeated_position=pos if mode=='control' else None,template_id=tid,raster=s['raster'],room=s['room'],normalized_edit_distance=d,input_sha256=rowpins)
           try:native(r)
           except ValueError as e:raise ValueError((r['qid'],str(e)))
           new.append(r);proof.append(dict(qid=r['qid'],source_qid=src['qid'],categories=cats,counts=[len(s['categories'][c]) for c in cats],raster=s['raster'],raster_sha256=s['raster_sha256']))
          rows+=new;mind=min(mind,*ds);seen_sets.update(keys);used[src['qid']]+=2;sceneuses[s['canonical']]+=1;filled+=1;counts[cell]+=1;allocation[k,rep,si]-=1
          break
        assert filled==14,('SHORT_CELL',cell,filled,dict(removed),len(scenes))
        print('cell',cell,filled,flush=True)
    assert len(rows)==1008 and max(used.values())<=4
    assert len({r['qid'] for r in rows})==len({r['candidate_id'] for r in rows})==1008
    Path('out/rows.jsonl').write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows))
    Path('out/BUILD.json').write_text(json.dumps(dict(input_sha256=inputs,cells=counts,removed=removed,min_normalized_edit_distance=mind,wordings=len(words),source_use_max=4,scene_pair_cap=12,scenes=len(sceneuses),rows_sha256=sha('out/rows.jsonl')),indent=1)+'\n')
    Path('out/evidence.json').write_text(json.dumps(dict(input_sha256=inputs,rows=proof),indent=1)+'\n')
    Path('STATUS.md').write_text('The generator produced 1,008 rows in 504 matched pairs, with every planned cell full. All rows and sources passed the sealed tree grammar and pack/validate adapter. Independent raster recount and field-diff checks are next.\n')
if __name__=='__main__':main()
