"""Build a reproducible, unadmitted relative-count tally packet from v7 GT rows.
Run with /scratch/jjyeung/envs/p1cpu/bin/python -B build_rows.py.
No image reads, network, training, source-tree writes, or deletion.
"""
import ast, collections, copy, hashlib, itertools, json, pathlib, re, sqlite3, sys, unicodedata
from novelty import Filter
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT/'out'; IN = ROOT/'in'
TREE = pathlib.Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
W = TREE.parent.parent
STORE = pathlib.Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
DB = STORE/'vqa/rows.sqlite'
Z = pathlib.Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/z.json')
CFG = W/'work/build19/inputs/config.json'
R0 = pathlib.Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A/src/inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl')
sys.path.insert(0,str(TREE))
from student_pilot import ground_rows, r2_contract, trace_grammar
from student_pilot.r1_rooms import Rooms, STORE as STORE_SHA
from student_pilot.r2_withheld import Withheld, room as normroom
from student_pilot.benchmark_eval.answers import parse_answer
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

TEMPLATES = [
 'Compare the distinct objects labelled "{a}" with those labelled "{b}" across this clip. Is the first category more numerous, less numerous, or equal in number?',
 'Use the full clip to compare the size of the "{a}" group to the "{b}" group. Which count relationship holds for the first group relative to the second?',
 'Consider each physical object only once: does category "{a}" contain more objects than category "{b}", fewer objects, or the same number?',
 'For the categories "{a}" and "{b}", compare their separate totals in the video. Select the relation of the first total to the second.',
 'Look at the collection of "{a}" objects and the collection of "{b}" objects in this clip. How does the number in the first collection compare with the number in the second?',
 'After counting distinct "{a}" objects and distinct "{b}" objects throughout the video, classify the first count as higher, lower, or equal.',
 'Judge the numerical balance between category "{a}" and category "{b}" in this scene. Does the first category outnumber the second, fall short, or tie?',
 'Separate the visible objects into the "{a}" category and the "{b}" category. Is the first category greater in count, smaller in count, or tied with the second?',
 'The comparison concerns the total number of "{a}" objects versus the total number of "{b}" objects. Which relation describes the first total in this clip?',
 'Across all views in the clip, compare unique "{a}" objects against unique "{b}" objects. Is the count for the first label above, below, or equal to the count for the second?',
 'Using distinct objects rather than repeated sightings, compare the "{a}" count with the "{b}" count. Choose more, fewer, or equal number for the first category.',
 'Which numerical relationship holds when the number of "{a}" objects is compared to the number of "{b}" objects in the video?',
 'Check whether the "{a}" group has a surplus, a deficit, or no difference in object count relative to the "{b}" group across the clip.',
 'Take the clip-wide count of category "{a}" as the first quantity and category "{b}" as the second. Is the first quantity greater, smaller, or equal?',
 'Count the distinct members of category "{a}" and category "{b}" seen during this clip. Which option correctly compares the first category with the second?',
 'For this video, assess the count of objects called "{a}" relative to objects called "{b}". Decide whether the former has more, fewer, or an equal number.',
 'A comparison is needed between all visible "{a}" objects and all visible "{b}" objects in the clip. Which option describes the count of the first group relative to the second?',
 'Focus on object totals for "{a}" and "{b}" over the entire video. Is the total for the first label larger, smaller, or identical to the total for the second?',
 'When repeated views of the same object are counted only once, how does the number of "{a}" objects compare to the number of "{b}" objects?',
 'Determine whether the distinct "{a}" objects seen in the clip outnumber, are fewer than, or match the distinct "{b}" objects. Select the corresponding count relation.'
]
# 200 rows per wording; 10% ties, 40% with max(category totals) >= 5.
QUOTAS = {('more','high'):39,('more','low'):51,('fewer','high'):39,('fewer','low'):51,('equal number','high'):2,('equal number','low'):18}
REUSE_CAP = 4
INPUTS = {}
def sha(data): return hashlib.sha256(data).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def filehash(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p,expected=None):
 p=pathlib.Path(p); h=filehash(p)
 if expected:assert h==expected,(str(p),h,expected)
 INPUTS[str(p)]={'sha256':h};return p

def load(p,expected=None): return json.loads(pin(p,expected).read_bytes())
def normalized(s):return ' '.join(re.findall(r'[\w]+',unicodedata.normalize('NFKC',s).casefold()))

def levenshtein(a,b):
 # Exact bit-vector Levenshtein distance; no third-party package.
 if not a:return len(b)
 masks={}
 for i,c in enumerate(a):masks[c]=masks.get(c,0)|(1<<i)
 vp=(1<<len(a))-1;vn=0;score=len(a);top=1<<(len(a)-1);mask=(1<<len(a))-1
 for c in b:
  eq=masks.get(c,0);x=eq|vn;d=(((eq&vp)+vp)^vp)|eq
  hp=vn|~(d|vp);hn=vp&d
  score+=bool(hp&top)-bool(hn&top)
  hp=(hp<<1)|1;hn<<=1;vp=(hn|~(x|hp))&mask;vn=(hp&x)&mask
 return score

def collect_questions():
 paths=[R0, pathlib.Path('/scratch/jjyeung/n30_mirror/rows_r1/out/vsti_rel_dev_r0/R0DEV_VSTI_QUESTIONS.jsonl'),
  pathlib.Path('/scratch/jjyeung/n30_mirror/rows_r1/out/vsti_rel_dev_r0/items.jsonl'),
  W/'work/contracts_r6/tests_r6/real_relative_count_r4.json']
 paths += sorted((TREE/'tests/fixtures/benchmark_eval').rglob('*.json'))
 paths += sorted((TREE/'tests/fixtures/benchmark_eval').rglob('*.jsonl'))
 found=set();sources={}
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k in ('question','question_text','prompt') and isinstance(v,str):found.add(v)
    else:walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 for p in paths:
  before=len(found);raw=pin(p).read_text()
  try:
   if p.suffix=='.jsonl':
    for l in raw.splitlines():
     if l.strip():walk(json.loads(l))
   else:walk(json.loads(raw))
  except json.JSONDecodeError:raise
  sources[str(p)]=len(found)-before
 # Include all question literals in the kit's question binding implementation.
 p=TREE/'generator/derivgen_v7/derivgen/bindings.py';source=pin(p).read_text()
 for node in ast.walk(ast.parse(source)):
  if isinstance(node,ast.Constant) and isinstance(node.value,str) and '?' in node.value and len(node.value)>35:found.add(node.value)
 sources[str(p)]='question-pattern literals'
 return sorted({normalized(q) for q in found}),sources

def parse_lists(row):
 pats=[r'list each distinct (.+?) once, by the frame where it first appears: (.+)\.',
       r'find each distinct (.+?), using its first-seen frame: (.+)\.',
       r'list the distinct (.+?) instances by first appearance: (.+)\.',
       r'locate each distinct (.+?) at its first appearance: (.+)\.']
 out={}
 for line in row['target'].splitlines():
  for pat in pats:
   m=re.fullmatch(r'Step \d+: '+pat,line)
   if m:
    cat,items=m.groups();entries=items.split('; ')
    assert cat not in out
    assert all(re.fullmatch(r'frame (\d+)(?: \((?:left|middle|right)\))?',e) for e in entries)
    out[cat]=[int(re.search(r'frame (\d+)',e)[1]) for e in entries]
 assert out and sum(map(len,out.values()))==int(row['answer'])
 assert all(1<=v<=32 for f in out.values() for v in f)
 return out

def gt_categories(row):
 p=row['provenance'];lists=parse_lists(row)
 if p['count_kind']=='single':
  assert len(lists)==1;cat=next(iter(lists));data={cat: [(x['id'],x['frame']) for x in p['instances']]}
 else:data={x['name']:list(zip(x['ids'],x['frames'])) for x in p['total_categories']}
 assert set(lists)==set(data)
 for c,pairs in data.items():
  assert len({x[0] for x in pairs})==len(pairs)
  assert sorted(lists[c])==sorted(x[1] for x in pairs)
  assert re.fullmatch(r'[a-z][a-z -]*',c),c
 assert len(set(x[0] for pairs in data.values() for x in pairs))==sum(map(len,data.values()))
 return data

def clip_key(row):
 s=row['student_input'];return sha(jbytes([row['dataset'],row['scene'],{k:v for k,v in s.items() if k not in ('question','options')}]))

def native_envelope(row):
 """Schema round-trip only; native VQA intake is checked separately, without patches."""
 s=row['student_input'];suffix=row['target'].split('</think>')[0]+'\n</think>\n<answer>'+str(row['answer'])+'</answer>'
 # Strip a possible trailing newline immediately before </think>.
 suffix=suffix.replace('\n\n</think>','\n</think>')
 rec=dict(qid=row['qid'],type=row['question_type'],scene=row['scene'],frame_indices=s['frame_indices'],question=s['question'],options=s.get('options') or [],answer=str(row['answer']),gt_answer=str(row['answer']),spec_version='3.14',trace_revision='3.14',suffix=suffix,events=[],gt_agrees=True,training_admitted=False)
 if rec['options']:rec['answer_content']=rec['options'][ord(rec['answer'])-65].split('. ',1)[1]
 rec['candidate_id']=row.get('candidate_id') or candidate_identity(rec)
 packed=ground_rows.pack(rec,row['provenance']);ground_rows.validate(packed)
 assert packed['target']==suffix and packed['question']==s['question']
 return True

def native_direct(row):
 try:r2_contract.validate(row,'vqa');return None
 except Exception as e:return type(e).__name__+': '+str(e)

def source_pool():
 cfg=load(CFG);pins=cfg['r1_training']['room_authority']
 for p in pins.values():pin(p['path'],p['sha256'])
 rooms=Rooms(pins);withheld=Withheld();pin(TREE/'student_pilot/r2_withheld.json', '634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed')
 dp=W/'fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json'
 dev=load(dp,'969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986')
 bp=W/'fixtures/work/records/revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json'
 bench=load(bp,'3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970')
 # Use only explicit names and aliases recorded in each authority.
 def names(x):
  out=set()
  if isinstance(x,str) and re.match(r'^(d[123]|scannet|scannetpp|scannetppv2|arkitscenes)/',x):out.add(normroom(x))
  elif isinstance(x,dict):
   for k,v in x.items():out.update(names(k));out.update(names(v))
  elif isinstance(x,list):
   for v in x:out.update(names(v))
  return out
 dn=names({k:dev[k] for k in ('aliases','canonical','natives','rooms','physical_groups') if k in dev})
 bn=names({k:bench[k] for k in ('scenes','physical_groups','other_corpora')})
 bn.update(normroom('/'.join(x)) for x in bench['rung1_tokens'])
 def gate(r):
  status,canonical,_=rooms.status(r)
  if status!='ok':return status,canonical,None
  room=rooms.room(canonical);ns={normroom(canonical),normroom(room),normroom(r['dataset']+'/'+r['scene'])}
  if withheld.touches(r,{'names':[canonical,room]}):return 'withheld80',canonical,room
  if ns&dn:return 'devS1',canonical,room
  if ns&bn:return 'BENCHv2',canonical,room
  return 'ok',canonical,room
 # Store pin authenticates the GT source; extraction uses the family index only.
 pin(DB,STORE_SHA);pin(STORE/'BUILD_MANIFEST.json');idx=load(STORE/'FAMILY_INDEX_RANGES.json')
 zs=pin(Z,'caba6a5695781491036de5b3acdb20db2d42ab581e5775fec3fe07fbd2114aad').read_bytes()
 removed={x['row_key'] for l in zs.splitlines() if (x:=json.loads(l))['reason']=='count_diag_first_seen_list_form'}
 conn=sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True)
 rows={};clips=collections.defaultdict(lambda:collections.defaultdict(list));excluded=collections.Counter();removed_count=0;all_qids=set()
 # Narrow count-family indexed reads; a streamed identity scan protects qid collisions.
 for lo,hi in idx['families']['object_counting']:
  for raw, in conn.execute('select row from rows where i between ? and ?',(lo,hi)):
   r=json.loads(raw)
   if r['qid'] not in removed:continue
   removed_count+=1
   if r.get('pool')!='b12_cntapp_gt_v1':excluded['not_b12_provenance']+=1;continue
   status,canonical,room=gate(r)
   if status!='ok':excluded[status]+=1;continue
   if len(r['student_input']['frames'])!=32:excluded['not_32_frames']+=1;continue
   cats=gt_categories(r);ck=clip_key(r);rows[r['qid']]=r
   for cat,ids in cats.items():clips[ck][cat].append((r['qid'],tuple(sorted(ids))))
 conn.close()
 # Refuse whole (clip,category) groups when any underlying instance/frame evidence differs.
 valid={};conflicts=[]
 for ck,cats in clips.items():
  keep={}
  for cat,entries in cats.items():
   if len({ids for q,ids in entries})!=1:conflicts.append([ck,cat]);continue
   keep[cat]={'ids':entries[0][1],'sources':sorted({q for q,ids in entries})}
  if len(keep)>1:valid[ck]=keep
 return rows,valid,gate,{'removed_rows':removed_count,'eligible_b12_rows':len(rows),'eligible_pair_clips':len(valid),'refusals':dict(excluded),'conflicting_category_groups':conflicts}

def build():
 OUT.mkdir(exist_ok=True);IN.mkdir(exist_ok=True)
 pin(__file__);seal=load(W/'out/TREE_SEAL.json')
 for name in ('novelty.py','edit_filter.c','edit_filter.so','tally_gate.py'):
  pin(ROOT/name)
 for rel in ['student_pilot/ground_rows.py','student_pilot/trace_grammar.py','student_pilot/r2_grammar.py','student_pilot/r2_contract.py','student_pilot/r1_rooms.py','student_pilot/r2_withheld.py','student_pilot/r2_exclusions.py','student_pilot/benchmark_eval/answers.py','generator/derivgen_v7/derivgen/ground_v312_quality.py','evalpath/run.py','evalpath/official.py','evalpath/items.py']:
  pin(TREE/rel,seal['files'][rel])
 pin(IN/'COVERAGE_V2_PUB.tar')
 qs,qpaths=collect_questions();src,clips,gate,poolstats=source_pool()
 print('POOL',json.dumps(poolstats),flush=True)
 (ROOT/'STATUS.md').write_text('The GT pool and room exclusions are verified. The generator pairs categories only on identical 32-frame clips and refuses inconsistent instance evidence. The requested tally syntax fails the unchanged w19 direct-trace grammar; row generation and independent checks will continue, with native admission reported separately.\n')
 pools=collections.defaultdict(list)
 for ck,cats in clips.items():
  for a,b in itertools.combinations(sorted(cats),2):
   # Reject overlapping words, IDs, and nested categories.
   if set(a.split())&set(b.split()):continue
   ga,gb=cats[a],cats[b]
   if {i for i,f in ga['ids']}&{i for i,f in gb['ids']}:continue
   na,nb=len(ga['ids']),len(gb['ids']);kind='tie' if na==nb else 'unequal';size='high' if max(na,nb)>=5 else 'low'
   pools[kind,size].append((ck,a,b))
 for k in pools:pools[k].sort(key=lambda x:sha(jbytes(['sb_rowC2',*x])))
 print('PAIR_POOLS',{str(k):len(v) for k,v in pools.items()},flush=True)
 usage=collections.Counter();seen_pairs=set();counts=collections.Counter();novel_reject=0;novel_tested=0;similar=[];output=[];audit=[];source_checks={};min_novel=1.;positions=collections.Counter()
 # Sort length once; the length lower bound skips impossible near-matches exactly.
 qs=sorted(qs,key=len);threshold=.25;wording_filter=Filter(qs)
 def novel(q):
  nonlocal novel_tested,novel_reject,min_novel
  n=normalized(q);novel_tested+=1
  index=wording_filter.match(n)
  if index>=0:
   ref=qs[index];d=levenshtein(n,ref)/max(len(n),len(ref),1)
   assert d<=threshold
   novel_reject+=1;similar.append({'question':q,'reference':ref,'distance':d});return False
  return True
 # Fill scarce high-count tie cells first, then the remaining exact cells.
 order=[('equal number','high'),('equal number','low'),('more','high'),('fewer','high'),('more','low'),('fewer','low')]
 for relation,size in order:
  bucket=pools['tie' if relation=='equal number' else 'unequal',size]
  ptr=0
  for tid,template in enumerate(TEMPLATES):
   needed=QUOTAS[relation,size];got=0
   for ck,a,b in bucket:
    pair=(ck,a,b)
    if pair in seen_pairs:continue
    ca,cb=clips[ck][a],clips[ck][b]
    if relation!='equal number' and ((len(ca['ids'])>len(cb['ids']))!=(relation=='more')):a,b=b,a;ca,cb=cb,ca
    elif relation=='equal number' and int(sha(jbytes(pair)),16)%2:a,b=b,a;ca,cb=cb,ca
    qa=sorted(ca['sources'],key=lambda q:(usage[q],q));qb=sorted(cb['sources'],key=lambda q:(usage[q],q));chosen=None
    for sa in qa:
     if usage[sa]>=REUSE_CAP:continue
     for sb in qb:
      if usage[sb]<REUSE_CAP:chosen=(sa,sb);break
     if chosen:break
    if not chosen:continue
    question=template.format(a=a,b=b)
    if not novel(question):continue
    sa,sb=chosen;r=src[sa];s=src[sb]
    assert clip_key(r)==clip_key(s)==ck
    assert {k:v for k,v in r['student_input'].items() if k not in ('question','options')}=={k:v for k,v in s['student_input'].items() if k not in ('question','options')}
    for q in set(chosen):
     if q not in source_checks:
      native_envelope(src[q]);source_checks[q]=native_direct(src[q])
    qid='sb_rowC2_'+sha(jbytes([tid,ck,a,b]))[:24]
    # Cycle all six option permutations; letter balance is independent of GT direction.
    options_order=list(itertools.permutations(['more','fewer','equal number']))[(tid+got)%6]
    options=[chr(65+i)+'. '+v for i,v in enumerate(options_order)]
    answer=chr(65+options_order.index(relation));n1,n2=len(ca['ids']),len(cb['ids'])
    tally=[]
    for cat,c in ((a,ca),(b,cb)):
     hist=collections.Counter(f for i,f in c['ids']);entries='; '.join(f'frame {f}: {hist[f]}' for f in sorted(hist))
     tally.append(f'{cat}: {entries} -> {len(c["ids"])}.')
    op='>' if n1>n2 else '<' if n1<n2 else '='
    target='<think>\nTally new instances at their first sampled frame:\n'+'\n'.join(tally)+f'\n{n1} {op} {n2}.\n</think>\n\n{answer}'
    x=copy.deepcopy(r);x.update(qid=qid,question_type='relative_count',category='relative_count',answer=answer,target=target,count_kind='relative',count_arity=2)
    x['student_input']['question']=question;x['student_input']['options']=options
    item=dict(qid=qid,scene=x['scene'],frame_indices=x['student_input']['frame_indices'],type='relative_count',question=question,options=options,trace_revision='3.14')
    x['candidate_id']=candidate_identity(item)
    # Preserve all original source provenance; explicit derivation identifies its scope.
    x['provenance']['relative_count_tally']={'schema':'sb-rowC2-tally-v1','source_qids':list(chosen),'source_row_sha256':{q:sha(jbytes(src[q])) for q in set(chosen)},'input_sha256':{str(DB):STORE_SHA,str(Z):INPUTS[str(Z)]['sha256'],str(pathlib.Path(__file__)):INPUTS[str(pathlib.Path(__file__))]['sha256']},'template_id':tid,'categories':[a,b],'totals':[n1,n2],'clip_sha256':ck,'relation':relation,'size_cell':size,'training_admitted':False}
    native_envelope(x);assert parse_answer(target,options)['answer']==answer
    assert gate(x)[0]=='ok'
    native_error=native_direct(x)
    # A strict list of changed leaf fields protects every image and other source field.
    allowed={'qid','question_type','category','answer','target','candidate_id','count_kind','count_arity','student_input.question','student_input.options','provenance.relative_count_tally'}
    def diffs(u,v,p=''):
     if u==v:return []
     if isinstance(u,dict) and isinstance(v,dict):
      return [d for k in sorted(set(u)|set(v)) for d in ([p+k] if k not in u or k not in v else diffs(u[k],v[k],p+k+'.'))]
     return [p.rstrip('.')]
    delta=diffs(r,x);assert set(delta)<=allowed,delta
    output.append(x);audit.append({'qid':qid,'source_qids':list(chosen),'source_row_sha256':{q:sha(jbytes(src[q])) for q in set(chosen)},'template_id':tid,'cell':[relation,size],'categories':[a,b],'ids_and_first_frames':[ca['ids'],cb['ids']],'canonical':gate(x)[1],'room':gate(x)[2],'field_diff':delta,'native_direct_error':native_error})
    for q in set(chosen):usage[q]+=1
    counts[f'{tid:02d}|{relation}|{size}']+=1;seen_pairs.add(pair);got+=1;positions[answer]+=1
    if got==needed:break
   assert got==needed,('SHORT CELL',tid,relation,size,got,needed)
   print('CELL',tid,relation,size,got,flush=True)
 print('SELECTED',len(output),'reuse',max(usage.values()),'native_failures',sum(a['native_direct_error'] is not None for a in audit),flush=True)
 assert len(output)==4000 and len({r['qid'] for r in output})==4000 and len({r['candidate_id'] for r in output})==4000
 # Deterministic mixed order; cells remain explicit in provenance and audit.
 order=sorted(range(len(output)),key=lambda i:sha(output[i]['qid'].encode()))
 output=[output[i] for i in order];audit=[audit[i] for i in order]
 with open(OUT/'sb_rowC2.jsonl','wb') as f:
  for r in output:f.write(jbytes(r)+b'\n')
 with open(OUT/'SOURCE_ROWS.jsonl','wb') as f:
  for q in sorted(usage):f.write(jbytes(src[q])+b'\n')
 # Each JSON output binds the complete computational input manifest.
 manifest={'schema':'sb-rowC2-inputs-v1','inputs':INPUTS,'tree':str(TREE),'tree_seal_sha256':INPUTS[str(W/'out/TREE_SEAL.json')]['sha256']}
 (OUT/'INPUTS.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 manifest_sha=filehash(OUT/'INPUTS.json')
 common={'input_manifest':{'path':'out/INPUTS.json','sha256':manifest_sha},'input_sha256':{p:v['sha256'] for p,v in INPUTS.items()}}
 def dump(name,data):(OUT/name).write_text(json.dumps({**data,**common},indent=2,sort_keys=True)+'\n')
 dump('AUDIT.json',{'rows':audit,'source_usage':dict(usage),'source_native_direct':source_checks})
 dump('GENERATION.json',{'status':'GENERATED_NOT_ADMITTED','rows':4000,'pool':poolstats,'pair_pools':{str(k):len(v) for k,v in pools.items()},'cells':dict(counts),'templates':TEMPLATES,'quotas':{'|'.join(k):v for k,v in QUOTAS.items()},'max_source_reuse':max(usage.values()),'source_reuse_cap':REUSE_CAP,'answer_letters':dict(positions),'wording_filter':{'metric':'character Levenshtein distance / max(normalized lengths), NFKC/casefold/alphanumeric words','reject_threshold_inclusive':threshold,'comparisons_cover':'all discovered local wording records and kit binding patterns','references':len(qs),'paths':qpaths,'candidate_questions_tested':novel_tested,'removed':novel_reject,'removed_examples':similar[:10],'missing_full_corpora':['dev-S1 item texts (not present in named local kit/input directories)','complete benchmark item texts beyond local fixtures (not present in named directories)']},'rows_sha256':filehash(OUT/'sb_rowC2.jsonl'),'source_rows_sha256':filehash(OUT/'SOURCE_ROWS.jsonl'),'native_pack_roundtrip_pass':4000,'native_direct_fail':sum(a['native_direct_error'] is not None for a in audit)})
 # 30 full rows, stratified across all wording templates and both tails.
 sample=[]
 for tid in range(20):
  choices=[i for i,a in enumerate(audit) if a['template_id']==tid]
  rel=['more','fewer','equal number'][tid%3];i=next(i for i in choices if audit[i]['cell'][0]==rel);sample.append(i)
 for rel,size in order_cells():
  ids=[i for i,a in enumerate(audit) if a['cell']==[rel,size] and i not in sample];sample.extend(ids[:2 if len(sample)<28 else 1])
 sample=sample[:30]
 while len(sample)<30:sample.append(next(i for i in range(len(output)) if i not in sample))
 text=['# Thirty complete rows','Each JSON block is the complete store-schema row. A readable question/target precedes it.']
 for n,i in enumerate(sample,1):
  r=output[i];text += [f'\n## {n}. {r["qid"]}',r['student_input']['question'],'\n'.join(r['student_input']['options']),'```text\n'+r['target']+'\n```','```json\n'+json.dumps(r,ensure_ascii=False,indent=2)+'\n```']
 (OUT/'READ30.md').write_text('\n\n'.join(text)+'\n')
 dump('READ30_INDEX.json',{'qids':[output[i]['qid'] for i in sample],'read30_sha256':filehash(OUT/'READ30.md')})
 (ROOT/'STATUS.md').write_text('The generator produced exactly 4,000 unadmitted rows across 120 asserted cells: 1,800 first-category larger, 1,800 smaller, and 400 ties; 1,600 rows have a category count of at least five. Each source row has a four-use cap. Full-row samples and source audit are written. Independent validation and manual sample review remain.\n')

def order_cells():return list(QUOTAS)
if __name__=='__main__':build()
