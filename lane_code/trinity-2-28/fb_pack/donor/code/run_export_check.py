import json,sys,types
from pathlib import Path
W=Path(__file__).resolve().parents[1];T=W/'work/new';sys.path.insert(0,str(T));p=types.ModuleType('tests');p.__path__=[str(T/'tests')];sys.modules['tests']=p
import torch
torch.set_num_threads(16)
from tests.test_scale_donor import fixture
from student_pilot.scale_donor_check import check
from student_pilot.p3_provenance import sha256
from student_pilot import scale_donor as D
O=W/'work/export_check';O.mkdir(exist_ok=True)
model,_,_=fixture();model.frame_layout='duplicate';model.auxiliary_heads.depth.config.p3['frame_layout']='duplicate'
invariance=json.loads((W/'out/K1_INVARIANCE.json').read_text())
inputs={str(W/'out/K1_INVARIANCE.json'):sha256(W/'out/K1_INVARIANCE.json'),str(T/'tests/test_carrier_c1_final.py'):sha256(T/'tests/test_carrier_c1_final.py')}
for name,value in [('model_config',model.config.to_dict()),('preparation',dict(depth=model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.settings,frame_layout='duplicate',frame_count=32,input_sha256=inputs))]:
 (O/(name+'.json')).write_text(json.dumps(value,sort_keys=True)+'\n')
for v in invariance['variants']:
 (O/('binding_'+v['variant']+'.json')).write_text(json.dumps(dict(scale_donor=v['settings'],input_sha256=inputs),sort_keys=True)+'\n')
 paths=dict(init_artifact=Path(v['settings']['checkpoint']['path']),after_artifact=Path(v['export']['path']),preparation=O/'preparation.json',model_config=O/'model_config.json',selection=W/'out/K1_SELECTION.json',binding=O/('binding_'+v['variant']+'.json'))
 values={k:str(p) for k,p in paths.items()};values.update({k+'_sha':sha256(p) for k,p in paths.items()})
 replicas=O/('replicas_'+v['variant']+'.json')
 hp=Path(v['settings']['checkpoint']['path']).parent/'heads.pt'
 replicas.write_text(json.dumps(dict(paths={sha256(hp):str(hp)},input_sha256=inputs),sort_keys=True)+'\n')
 result=check(types.SimpleNamespace(**values,replicas=str(replicas),replicas_sha=sha256(replicas),image_side=4,output=str(W/'out'/('EXPORT_CHECK_'+v['variant']+'.json'))))
 print(v['variant'],result['status'])
