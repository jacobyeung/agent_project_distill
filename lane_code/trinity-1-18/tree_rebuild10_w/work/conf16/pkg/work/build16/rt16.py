from pathlib import Path
from copy import deepcopy
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build16';T=L/'work/tree_r1';O=B/'proofs/runtime_lane';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
from student_pilot import r1_handover as H
from student_pilot.p3_provenance import load,file_pin
E=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/r1_ops/work')
R=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_runtime')
paths={'A_runtime':R/'A_runtime_673bc60f.json','Cprime_runtime':R/'prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'}
prep=E/'adm171377/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json'
old=load(L/'work/build14/proofs/real/RESULT.json')
assert file_pin(prep)['sha256']==old['preparation']['sha256']
cfg=load(B/'inputs/kit_config.json');parent=L/'work/n1fix2/inputs/init_artifact.json'
kwargs={'metadata':[file_pin(prep)],'replicas':{file_pin(parent)['sha256']:str(parent)}}
import glob
for f in glob.glob('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_runtime/okh7/**/*.json',recursive=True):kwargs['replicas'][file_pin(Path(f))['sha256']]=f
def compare(a,b):
    try:H.compare_configs(a,b,**kwargs);return 'ADMIT'
    except ValueError as e:return str(e)
out={'N':file_pin(B/'inputs/kit_config.json'),'preparation':file_pin(prep),'parent_replica':file_pin(parent),'real':{},'refuse':{}}
for name,path in paths.items():
    p=load(path);actual=compare(p,cfg)
    identity=H.export_identity(p)
    out['real'][name]={'config':file_pin(path),'config_identity':identity,'result':actual,
        'effective_camera_equal':H.effective_camera(p,kwargs['metadata'],kwargs['replicas'])==H.effective_camera(cfg,kwargs['metadata'],kwargs['replicas'])}
    
    variants={'depth_enabled':False,'align':{'cam':{'layer':'final','weight':1},'patch':None},
        'camera':{'trunk_depth':load(prep)['camera']['trunk_depth']+2},'camera_overrides':{'weight_focal':2.,'weight_scale':.08},
        'lm_lr_scale':.7,'unknown_extra':None}
    refusals={}
    for key,value in variants.items():
        bad=deepcopy(p);bad[key]=value
        reason=compare(bad,cfg)
        refusals[key]=reason
    bad=deepcopy(cfg);bad['routing_opener_init']='reset'
    refusals['N_reset']=compare(p,bad)
    out['refuse'][name]=refusals
(O/'RESULT.json').write_text(json.dumps(out,indent=2));m.save(O)
print(json.dumps(out,indent=2))
