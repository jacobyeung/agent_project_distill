import hashlib,json,pathlib,tarfile
B=pathlib.Path(__file__).resolve().parents[1]; A=B.parents[1]; O=B/'out'; I=O/'inputs'
def load(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=load(A/'work/ret544/native/R1.json'); req=load(A/'work/ret544/native/paired/request.json'); by={x['key']:x for x in r['arms']['unflagged']};keys=req['keys']
sel=[]
for typ,n in [('camera_displacement',4),('camera_movement_direction',3),('camera_rotation',3)]:
 sel.extend([k for k in keys if by[k]['question_type']==typ and 'decode' in by[k]][:n])
for unit,n in [('meters',3),('centimeters',3),('feet',2),('inches',2)]:
 sel.extend([k for k in keys if by[k]['question_type']=='object_abs_distance' and by[k]['question_unit']['unit']==unit and 'decode' in by[k]][:n])
sel=[k for k in keys if k in sel]; assert len(sel)==20
canary=[]
for typ,n in [('camera_displacement',2),('camera_movement_direction',2),('camera_rotation',2),('object_abs_distance',3),('room_size_estimation',1)]:
 canary.extend([k for k in keys if by[k]['question_type']==typ][:n])
canary=[k for k in keys if k in canary];assert len(canary)==10
reference=[by[k] for k in sel]; dump(I/'reference.json',reference);dump(I/'items.json',dict(keys=keys,proof_keys=sel,canary_keys=canary))
mapping={k:'k'+hashlib.sha256(k.encode()).hexdigest()[:24] for k in keys};assert len(set(mapping.values()))==len(mapping)
dump(O/'TRINITY_KEY_MAP.json',mapping)
# Opaque reference projection is reviewable separately from the exact source records.
opaque=[dict(row,key=mapping[row['key']]) for row in reference];dump(I/'opaque_reference.json',opaque)
distance=A/'guard_kit/report/inputs/DISTANCE_LIST_DEVS1_150.jsonl';dl=[json.loads(s) for s in distance.read_text().splitlines()]
expected={ 'devrows:'+x['question_id'] for x in dl}; actual={k for k in keys if by[k]['question_type']=='object_abs_distance'}; assert actual==expected
assert len([k for k in keys if by[k]['question_type'].startswith('camera_')])==450
assert len([k for k in keys if by[k]['question_type']=='room_size_estimation'])==36
report=dict(reference_source=str(A/'work/ret544/native/R1.json'),request_source=str(A/'work/ret544/native/paired/request.json'),reference_sha256=sha(I/'reference.json'),reference_keys=sel,canary_keys=canary,counts=dict(camera=450,distance=150,room=36),distance_list=dict(path=str(distance),sha256=sha(distance)),selection_rule='First decoded records in accepted request order: camera types 4/3/3; distance meters/centimeters/feet/inches 3/3/2/2. Restore global request order. Canary: first 2/2/2 camera, 3 distance and 1 room; restore global order.')
dump(O/'ITEM_SELECTION.json',report)
# Small restoration metadata only. These are baseline evidence, never candidate substitutes.
f=load(O/'BASELINE_FAMILY.json');cfg=f['worker_contract']['config']['path']; prefix='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
with tarfile.open(A/'work/from113/work/obj/metadata_e10fbb95487f3baf.tar') as t:
 def get(path):return json.loads(t.extractfile('fsw/'+path.removeprefix(prefix)).read())
 c=get(cfg);receipt=get(c['preparation']['path']);seal=get(c['code']['path']);d=get(f['worker_contract']['data_receipt']['path'])
 for name,val in [('prepare_config',c),('preparation',receipt),('source_seal',seal),('data_receipt',d)]:dump(O/('BASELINE_'+name+'.json'),val)
print(json.dumps(report,indent=2))
