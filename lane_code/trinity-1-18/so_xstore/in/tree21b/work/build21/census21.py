"""Full authorized census, bounded traces, and deterministic 1000-step arithmetic."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
import sys,json,sqlite3,itertools,os
L=Path(__file__).resolve().parents[2];B=L/'work/build21';I=B/'inputs';O=B/'proofs/census'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
m=Monitor(L/'work/tree_r1')
from student_pilot.p3_provenance import file_pin,pinned,load,digest
def write(path,value):
 path=Path(path);assert path.is_relative_to(B)
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
from student_pilot import r1_rooms as R,r1_coverage as C,r1_mix
from student_pilot.r1_routing import Filters
from student_pilot.r1_population import family
from student_pilot.carrier_c1_run import Rows
from student_pilot.r1_counting import admit
from student_pilot.r2_adapters import normalize
from student_pilot.r2_intake import intake
from student_pilot import carrier_c1_routing as routing
from tests.test_r2_build9_recovery import envelope
cfg=load(I/'config.json');value=cfg['r1_training'];guard=C.validate_binding(cfg)
audit,_=R.census(cfg);write(I/'room_audit.json',audit);value['room_audit']=file_pin(I/'room_audit.json')
R.verify_audit(cfg,value['room_audit']);print('PASS full room and wording census',flush=True)
filters=Filters(cfg,cfg['scene_division']);rooms=R.Rooms(value['room_authority'])
v=load(pinned(cfg['streams']['vqa']));reader=Rows(dict(streams={'vqa':v},r1_training=value),None)
counts=Counter();refused=Counter();examples=defaultdict(list);found=set()
union={r['row_key'] for r in C.read_list(value['v7_k1_removal'])}
for i,raw in reader.connections['vqa'].execute('SELECT i,row FROM rows ORDER BY i'):
 row=json.loads(raw);guard.check(row);cell=family(row,'vqa')
 if row['qid'] in union:found.add(row['qid'])
 why=filters.reason(row,'vqa')
 if why is None:
  try:row,_=reader.row('vqa',i);admit(row,cell)
  except (ValueError,KeyError,TypeError) as error:why='reader:'+type(error).__name__+':'+str(error)
 if why:refused[why]+=1
 else:
  counts[cell]+=1
  if len(examples[cell])<20:examples[cell].append(dict(qid=row['qid'],row_sha256=digest(row),target=row.get('target')))
reader.close();assert found==union
print('PASS full v7 census',dict(counts),flush=True)
sources=load(pinned(value['row_sources']));chunk=O/'chunk';chunk.mkdir(exist_ok=True)
memory=sqlite3.connect(':memory:');memory.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
reader=Rows(dict(streams={},r1_training=value,extent_receipt=cfg['extent_receipt']),None);reader.connections['routing']=memory
slice_counts={}
for kind in C.source_names(sources):
 pin=sources[kind]['source'];n=Counter();errors=Counter();cell='coverage' if kind in C.PINS else kind
 with pinned(pin).open() as f:
  while lines:=list(itertools.islice(f,200)):
   normalized=[]
   for line in lines:
    raw=json.loads(line);guard.check(raw);p=raw.get('provenance',{});si=raw.get('student_input',{})
    indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    frames={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,
     total_num_frames=indices[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
    row=normalize(raw,frames);row.update(answer_form='routed',response_heads=['pose','depth']);normalized.append(row)
   mp=envelope(chunk,normalized,'routing',kind);manifest=load(mp);manifest['extent_receipt']=cfg['extent_receipt'];write(mp,manifest)
   items,report=intake(mp);n['read']+=len(lines);n['intake_admitted']+=len(items)
   errors.update('intake:'+r['reason'] for r in report['refusals'])
   for item in items:
    row=item['row']
    if row.get('events') and not row.get('routing'):
     si=row['student_input'];rgb=dict(si,frames=[dict(p,source_index=i) for i,p in zip(si['frame_indices'],si['frames'],strict=True)])
     row=routing.c1_row(row,rgb)
    row['r1_source']=dict(family=kind,sha256=pin['sha256']);why=filters.reason(row,'routing')
    if why:errors['filter:'+why]+=1;continue
    memory.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),json.dumps(item.get('target',{}))))
    try:rooms.admit(row);bound,_=reader.row('routing',0)
    except (ValueError,KeyError,TypeError) as error:errors['reader:'+str(error)]+=1;continue
    n['eligible']+=1
    if len(examples[cell])<20:examples[cell].append(dict(qid=bound['qid'],row_sha256=digest(bound),target=bound['target']))
 assert n['read']==n['eligible']+sum(errors.values())
 slice_counts[kind]=dict(source=pin,counts=dict(n),refused=dict(errors))
 print(kind,dict(n),dict(errors),flush=True)
reader.close()
previous=load(L/'work/build18/proofs/rooms/RESULT.json')['allocation']['eligible']
eligible=dict(previous)
for cell in load(L/'work/build16/proofs/census/CENSUS.json')['vqa']['eligible_by_cell']:eligible[cell]=counts[cell]
for name in ('recovery','absolute_distance','units'):eligible[name]=slice_counts[name]['counts'].get('eligible',0)
eligible['coverage']=sum(slice_counts[name]['counts'].get('eligible',0) for name in C.PINS)
card=load(I/'mix.json');allocation=r1_mix.allocate(card,eligible)
for cell in card['cells']:
 cell['rows_per_step']=allocation['draws'][cell['type']]/1000
 cell['ceiling_rows_per_step']=4*eligible[cell['type']]/1000
 assert Fraction(str(cell['rows_per_step']))<=Fraction(4*eligible[cell['type']],1000)
write(I/'mix.json',card);value['mix']=file_pin(I/'mix.json')
for name in ('config.json','kit_config.json'):write(I/name,cfg)
write(O/'CENSUS.json',dict(vqa=dict(database=v['database'],read=v['count'],eligible_by_cell=dict(counts),refused=dict(refused)),
 slices=slice_counts,room_audit=value['room_audit'],heldout_wording_hits=0,k1_union_found=len(found),examples=dict(examples),
 stand_in='Frame metadata /u and GUESS 24 FPS where source FPS absent; geometry and printed responses unchanged. Independent host RGB/coverage envelopes remain required.',
 inherited_counts=dict(source=str(L/'work/build18/proofs/rooms/RESULT.json'),cells={k:eligible[k] for k in ('pose','pointing','camera_displacement','camera_movement_direction','camera_rotation')})))
pop=dict(schema='r1-population-v1',complete=True,after_all_filters=True,card_sha256=value['mix']['sha256'],
 counts=eligible,evidence=[file_pin(O/'CENSUS.json')],scope='Census arithmetic; virtual disjoint offsets, not a production store binding')
write(O/'population.json',pop);pop_pin=file_pin(O/'population.json');indices={};ends=Counter()
for cell in card['cells']:
 k=cell['type'];s=cell['stream'];indices[k]=list(range(ends[s],ends[s]+eligible[k]));ends[s]+=eligible[k]
write(O/'indices.json',dict(population_sha256=pop_pin['sha256'],cells=indices))
binding=dict(schema='r1-sampling-v1',card=value['mix'],population=pop_pin,indices=file_pin(O/'indices.json'))
write(O/'binding.json',binding);owner={(c['stream'],i):c['type'] for c in card['cells'] for i in indices[c['type']]}
repeat=Counter();draws=Counter();resume={}
for step,plan in enumerate(r1_mix.plans(binding,dict(ends),1000)):
 for stream,offsets in plan:
  for i in offsets:repeat[stream,i]+=1;draws[owner[stream,i]]+=1
 if step in (400,600):resume[str(step)]=digest(plan)
for step in (400,600):assert digest(next(r1_mix.plans(binding,dict(ends),1000,start_step=step)))==resume[str(step)]
percell={c['type']:dict(eligible=eligible[c['type']],ceiling=4*eligible[c['type']]/1000,quota=c['rows_per_step'],
 draws=draws[c['type']],largest_repeat=max((n for key,n in repeat.items() if owner[key]==c['type']),default=0)) for c in card['cells']}
assert max(repeat.values())<=4
write(O/'PLAN_RUN.json',dict(binding=binding,allocation=allocation,cells=percell,steps=1000,largest_repeat=max(repeat.values()),
 total_draws=sum(draws.values()),resumed=resume,scope=pop['scope']))
m.save(O);print('PASS census and 1000-step plan',max(repeat.values()),flush=True)
