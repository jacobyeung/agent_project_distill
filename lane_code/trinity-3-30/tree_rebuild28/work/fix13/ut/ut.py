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
assert res['k1_capture_resolved_by_split'][0]['K1_heldout'] is True and res['k1_capture_resolved_by_split'][1]['how']=='division_token'
assert res['scannetpp_duplicate_forms_no_conflict'][0] != 'RAISE'
assert res['withheld_by_split'][0]['withheld'] is True
assert res['arkit_visit'][0]!='RAISE'
assert res['unresolved_listed_dataset_refuses']==('RAISE','R1_CENSUS_ROOM_UNRESOLVED:pose')
assert res['unknown_dataset_refuses'][0]=='RAISE'
assert res['vqa_unchanged_raises'][0]=='RAISE' and res['routing_unchanged_raises'][0]=='RAISE'
# dataset-level path: dataset named by no list or room set
import student_pilot.s1_exclusions as E
E.Exclusions.__init__=lambda self,a,b: setattr(self,'aliases',{'d1':'d1','d2':'d2','d3':'d3','scannet':'d1','scannetpp':'d2','scannetppv2':'d2','arkitscenes':'d3','omni':'omni'})
c2=sv.classifier(cfg); det={}
print('dataset_level ->',c2(dict(dataset='omni',scene='s1'),'pose',det),det)
assert det['level']=='dataset'
# cs.evaluate records levels
rows=[row('d1','scannet/scene0002_00'),row('d2','scannetpp/abcdef0123'),dict(dataset='omni',scene='s1')]
import student_pilot.row_removals as rr
rec,keys=cs.evaluate(cfg,'pose',[],lambda: iter(rows),c2)
print('evaluate ->',json.dumps(rec['counts']),json.dumps(rec['result']),rec['refusals'])
assert rec['counts']['scene_level']==2 and rec['counts']['dataset_level']==1 and rec['result']['dataset_level']['datasets']=={'omni':1}
assert rec['refusals']==['R1_CENSUS_PROTECTED_ADMITTED:pose']
print('ALL PASS')
