from pathlib import Path
from copy import deepcopy
import sys,json,hashlib,os
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=L/'work/tree_r1';O=B/'proofs/real';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
from student_pilot import r1_handover as H
from student_pilot.p3_provenance import load,file_pin
paths={k:Path('/scratch/jjyeung/orch_n30/r1_ops/work')/folder/'out/config.json' for k,folder in [('A','snap_fac07052'),('C','snap_6a5c7d00')]}
prep=Path('/scratch/jjyeung/orch_n30/r1_ops/work/adm171377/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json')
cfg=load(B/'inputs/kit_config.json');parent=L/'work/n1fix2/inputs/init_artifact.json'
kwargs={'metadata':[file_pin(prep)],'replicas':{file_pin(parent)['sha256']:str(parent)}}
def compare(a,b):
    try:H.compare_configs(a,b,**kwargs);return 'ADMIT'
    except ValueError as e:return str(e)
out={'N':file_pin(B/'inputs/kit_config.json'),'preparation':file_pin(prep),'parent_replica':file_pin(parent),'real':{},'refuse':{},'refuse_against_kit':{}}
for name,path in paths.items():
    p=load(path);actual=compare(p,cfg)
    counterfactual=deepcopy(cfg);counterfactual['routing_opener_init']='reset'
    cf=compare(p,counterfactual)
    assert actual=='P_EXPORT_CONFIG_DIFFERENCE:routing_opener_init',actual
    assert cf=='ADMIT',cf
    out['real'][name]={'config':file_pin(path),'config_identity':H.export_identity(p),'result':actual,'counterfactual_only_N_reset':cf,
        'effective_camera_equal':H.effective_camera(p,kwargs['metadata'],{})==H.effective_camera(cfg,kwargs['metadata'],{})}
    variants={'depth_enabled':False,'align':{'cam':{'layer':'final','weight':1},'patch':None},
        'camera':{'trunk_depth':load(prep)['camera']['trunk_depth']+2},'camera_overrides':{'weight_focal':2.,'weight_scale':.08},
        'lm_lr_scale':.7,'unknown_extra':None}
    refusals={};against_kit={}
    for key,value in variants.items():
        bad=deepcopy(p);bad[key]=value
        reason=compare(bad,counterfactual);assert key in reason and reason!='ADMIT',reason
        refusals[key]=reason
        against_kit[key]=compare(bad,cfg);assert against_kit[key]!='ADMIT'
    out['refuse'][name]=refusals
    out['refuse_against_kit'][name]=against_kit
(O/'RESULT.json').write_text(json.dumps(out,indent=2));m.save(O)
print(json.dumps(out,indent=2))
