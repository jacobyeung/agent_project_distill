import json, sys, tempfile
from pathlib import Path
kit=sys.argv[1]; sys.path[:0]=[str(Path(__file__).parent/'fake'), kit]
from student_pilot.carrier_c1_routing import alias_of
import sv, cs
d=Path(tempfile.mkdtemp()); 
split=d/'split.json'; split.write_text(json.dumps({'captures':['scannet/scene0002_00','scannetpp/abcdef0123','scannetppv2/abcdef0123','scannet/scene0003_00']}))
other=d/'x.json'; other.write_text('{}'); csv=d/'v.csv'; csv.write_text('video_id,visit_id\n111,NA\n')
cfg={'r1_training':{'room_authority':{'split':{'path':str(split)},'aliases':{'path':str(other)},'build':{'path':str(other)},'visits':{'path':str(csv)},'reserve':{'path':str(csv)}}},
     'dev_scene_exclusions':{'path':str(other)},'benchmark_scene_exclusions':{'path':str(other)},'exclusions':None}
classify=sv.classifier(cfg)
tok=lambda c: alias_of(c).split('/',1)[1]
def row(ds,c=None,scene=None): return dict(dataset=ds,scene=scene or tok(c))
res={}
def run(name,r,stream='pose'):
    det={}
    try: res[name]=(classify(r,stream,det),det)
    except ValueError as e: res[name]=('RAISE',str(e))
run('k1_capture_resolved_by_split',row('d1','scannet/scene0002_00'))
run('scannetpp_duplicate_forms_no_conflict',row('d2','scannetpp/abcdef0123'))
run('withheld_by_split',row('d1','scannet/scene0003_00'))
run('arkit_visit',row('d3','arkitscenes/111'))
run('unresolved_listed_dataset_refuses',row('d1',scene='vffffffffffff'))
run('unknown_dataset_refuses',dict(dataset='waymo',scene='abc'))
run('vqa_unchanged_raises',row('d1','scannet/scene0002_00'),'vqa')
run('routing_unchanged_raises',row('d1','scannet/scene0002_00'),'routing')
for k,v in res.items(): print(k,'->',v)
f,d=res['k1_capture_resolved_by_split']; assert f['K1_heldout'] is False and d['exposure']==['K1_heldout'] and d['how']=='aliases_token'
assert res['scannetpp_duplicate_forms_no_conflict'][0]!='RAISE'
assert res['withheld_by_split'][0]['withheld'] is True
assert res['unresolved_listed_dataset_refuses']==('RAISE','R1_CENSUS_ROOM_UNRESOLVED:pose')
assert res['vqa_unchanged_raises'][0]=='RAISE' and res['routing_unchanged_raises'][0]=='RAISE'
run('namespace_capture',row('d1','scannet/scene0500_01')); f,d=res['namespace_capture']; assert d['how']=='namespace_token' and not any(f.values())
run('sibling_of_listed_token_capture',row('d1','scannet/scene0007_01'))
f,d=res['sibling_of_listed_token_capture']; print('sibling',f,d); assert f['dev'] is True
run('k1_pointing_protected',dict(dataset='d1',scene='scene0002_00'),'pointing'); print(res['k1_pointing_protected'])
rows=[row('d1','scannet/scene0002_00'),row('d2','scannetpp/abcdef0123'),row('d1','scannet/scene0500_01')]
rec,keys=cs.evaluate(cfg,'pose',[],lambda: iter(rows),classify)
print('evaluate ->',json.dumps(rec['counts']),json.dumps(rec['result']),rec['refusals'])
assert rec['refusals']==[] and rec['result']['resolved']['namespace']==1 and rec['result']['exposure']['K1_heldout']['rows']==1
print('ALL PASS')
