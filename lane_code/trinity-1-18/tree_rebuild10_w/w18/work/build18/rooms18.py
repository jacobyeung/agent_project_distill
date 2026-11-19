"""Stream the authorized v7 census; retain the exact exclusion keys, counts and bounded traces."""
from pathlib import Path
from collections import Counter,defaultdict
from copy import deepcopy
from fractions import Fraction
import sys,json,sqlite3
L=Path(__file__).resolve().parents[2];B=L/'work/build18';I=B/'inputs';O=B/'proofs/rooms'
I.mkdir(exist_ok=True);O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(L/'work/tree_r1')
from student_pilot.p3_provenance import file_pin,pinned,load,digest
from tests.test_r2_build_n1 import write
from student_pilot import r1_rooms as R
from student_pilot.r1_routing import Filters
from student_pilot.r1_population import family
from student_pilot.carrier_c1_run import Rows
from student_pilot.r1_counting import admit
from student_pilot.r1_mix import allocate
cfg=load(L/'work/build17/inputs/config.json')
hits=[];audit,_=R.census(cfg,store_hits=hits)
hits.sort(key=lambda r:r['row_key'])
assert len(hits)==len({r['row_key'] for r in hits})==2637
assert audit['store']['canonical_from']['row_field']==43779 and audit['store']['canonical_from']['alias']==41259
path=I/'u.json';path.write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in hits))
pin=file_pin(path)
idx=next(i for i,p in enumerate(cfg['remove_files']) if p['sha256']==R.N_LIST)
cfg['remove_files'].insert(idx,pin);cfg['r1_training']['v7_k1_removal']=pin
# Bind one deterministic list to the already pinned store and room authorities.
source=L/'work/tree_r1/student_pilot/r1_rooms.py'
text=source.read_text();text=text.replace("V7_K1_LIST = 'pending-bound-census'",'V7_K1_LIST = '+repr(pin['sha256']));source.write_text(text)
R.V7_K1_LIST=pin['sha256']
post,post_hits=R.census(cfg);assert post['store']['unremoved_hits']==0
ap=write(I/'room_audit.json',post);cfg['r1_training']['room_audit']=ap
R.verify_audit(cfg,ap)
filters=Filters(cfg,cfg['scene_division'])
value=load(pinned(cfg['streams']['vqa']))
reader=Rows(dict(streams={'vqa':dict(database=value['database'],count=value['count'])},r1_training=cfg['r1_training']),None)
counts=Counter();refused=Counter();examples=defaultdict(list);delta=Counter();old=load(L/'work/build16/proofs/census/CENSUS.json')
for i,raw in reader.connections['vqa'].execute('SELECT i,row FROM rows ORDER BY i'):
    row=json.loads(raw);cell=family(row,'vqa');why=filters.reason(row,'vqa')
    if why is None:
        try:row,target=reader.row('vqa',i);admit(row,cell)
        except (ValueError,KeyError,TypeError) as error:why='reader:'+type(error).__name__+':'+str(error)
    if why:refused[why]+=1
    else:
        counts[cell]+=1
        if len(examples[cell])<20:examples[cell].append(dict(row_key=row['qid'],row_sha256=digest(row),target=row.get('target')))
reader.close()
previous=load(L/'work/build16/proofs/census/PLAN_RUN.json')['allocation']['eligible']
slice_intersections={}
keys={r['row_key'] for r in hits}
for kind,spec in load(pinned(cfg['r1_training']['row_sources'])).items():
    if kind not in ('recovery','units','absolute_distance'):continue
    with pinned(spec['source']).open() as source:
        slice_intersections[kind]=sum(json.loads(line)['qid'] in keys for line in source)
assert not any(slice_intersections.values())
eligible=dict(previous)
for cell in old['vqa']['eligible_by_cell']:eligible[cell]=counts[cell]
card=load(pinned(cfg['r1_training']['mix']));original_cells=deepcopy(card['cells'])
allocation=allocate(card,eligible)
if allocation['cuts']:
    for cell in card['cells']:cell['rows_per_step']=allocation['draws'][cell['type']]/1000
    for cell in card['cells']:cell['ceiling_rows_per_step']=4*eligible[cell['type']]/1000
    cfg['r1_training']['mix']=write(I/'mix.json',card)
assert allocate(card,eligible)['cuts']=={}
cells={c['type']:dict(eligible=eligible[c['type']],previous_eligible=previous[c['type']],
    delta=eligible[c['type']]-previous[c['type']],rows_per_step=c['rows_per_step'],ceiling=4*eligible[c['type']]/1000,
    measured=c['stream']=='vqa',source=str((O/'RESULT.json').relative_to(L)) if c['stream']=='vqa' else 'work/build16/proofs/census/PLAN_RUN.json') for c in card['cells']}
for c in card['cells']:assert Fraction(str(c['rows_per_step']))<=Fraction(4*eligible[c['type']],1000)
cfg['r1_training']['mix']=write(I/'mix.json',card)
for key in ('row_sources','source_membership'):
    cfg['r1_training'][key]=write(I/(key+'.json'),load(pinned(cfg['r1_training'][key])))
cfg['streams']['vqa']=write(I/'v7_receipt.json',value)
cfg['r1_training']['store_parameter']=cfg['streams']['vqa']
for key,pin0 in cfg['r1_training']['room_authority'].items():
    local=I/(pin0['sha256']+'.json');local.write_bytes(pinned(pin0).read_bytes())
    cfg['r1_training']['room_authority'][key]=file_pin(local)
post['row_sources']=cfg['r1_training']['row_sources'];post['authority']=cfg['r1_training']['room_authority']
post['store']['certification']=post['authority']['build']
cfg['r1_training']['room_audit']=write(I/'room_audit.json',post)
R.verify_audit(cfg,cfg['r1_training']['room_audit'])
for name in ('config.json','kit_config.json'):write(I/name,cfg)
result=dict(status='PASS',GO=False,removal=pin,removal_rows=len(hits),audit_before=audit,audit_after=post,
    eligible_by_cell=cells,card_cells_changed=card['cells']!=original_cells,allocation=allocation,slice_v7_key_intersections=slice_intersections,
    vqa_refusals=dict(refused),examples=dict(examples),
    qualification='VQA eligible counts and room audits use complete source streams. Routing eligibility and unavailable pose/camera/pointing counts retain the explicitly qualified build-16 census; their payloads were not rerun.')
write(O/'RESULT.json',result);m.save(O)
(B/'STATUS.md').write_text('Build 18: GO=false. Mode q reaches native preparation but the parent component evidence is missing. The pinned v7 K1 list and room census are complete; see proofs/rooms/RESULT.json. Final checks remain.\n')
print(json.dumps(dict(rows=len(hits),sha256=pin['sha256'],cells=cells,card_cells_changed=result['card_cells_changed']),indent=2))
