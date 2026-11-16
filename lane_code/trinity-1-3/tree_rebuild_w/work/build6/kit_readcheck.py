import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load
result=[]
for name in ('a2','a0'):
 root=B/'kits'/name;launch=load(root/'k/launch.json');cfg=load(root/launch['config']['file'])
 assert launch['production_authorized'] is False
 assert {key for key,value in cfg['route_table'].items() if value=='route'}=={'absolute_distance_object','object_abs_distance','camera_displacement','camera_movement_direction','camera_rotation'}
 assert all(value in ('route','direct') for value in cfg['route_table'].values())
 assert cfg['r2_identity']['init']==load(L/'out/INIT_INPUT.json')['identity']
 result.append(dict(kit=name,production_authorized=launch['production_authorized'],route_table=cfg['route_table'],init=cfg['r2_identity']['init']))
(B/'KIT_READCHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
