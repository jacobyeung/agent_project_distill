from pathlib import Path
from copy import deepcopy
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build19';T=L/'work/tree_r1';O=B/'proofs/real';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
from student_pilot import r1_handover as H
from student_pilot.p3_provenance import load,file_pin
E=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/r1_ops/work')
paths={k:E/folder/'out/config.json' for k,folder in [('A','snap_fac07052'),('C','snap_6a5c7d00')]}
paths['Cprime']=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_configs/cprime_31abe087.json')
pins={'A':'9fd188164999788af36d5c6563d47b30351182ce68962b33703995c6ae45b0bb',
      'C':'2152828974490944a1713f5a539e87211f80179f0b5f9254ea9966fc65788733','Cprime':'31abe0871f35f9ca8d4a6445c5ee95ac03ec2324d37273e6b1f508acdbf246a1'}
prep=E/'adm171377/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json'
old=load(L/'work/build14/proofs/real/RESULT.json')
assert file_pin(prep)['sha256']==old['preparation']['sha256']
cfg=load(B/'inputs/kit_config.json');parent=L/'work/n1fix2/inputs/init_artifact.json'
kwargs={'metadata':[file_pin(prep)],'replicas':{file_pin(parent)['sha256']:str(parent)}}
def compare(a,b):
    try:H.compare_configs(a,b,**kwargs);return 'ADMIT'
    except ValueError as e:return str(e)
out={'N':file_pin(B/'inputs/kit_config.json'),'preparation':file_pin(prep),'parent_replica':file_pin(parent),'real':{},'refuse':{}}
for name,path in paths.items():
    assert file_pin(path)['sha256']==pins[name]
    p=load(path);actual=compare(p,cfg);assert actual=='ADMIT',actual
    identity=H.export_identity(p)
    out['real'][name]={'config':file_pin(path),'config_identity':identity,'result':actual,
        'effective_camera_equal':H.effective_camera(p,kwargs['metadata'],{})==H.effective_camera(cfg,kwargs['metadata'],{})}
    if name=='Cprime':out['real'][name]['matches_supplied_identity_prefix_774503e2']=identity.startswith('774503e2')
    variants={'depth_enabled':False,'align':{'cam':{'layer':'final','weight':1},'patch':None},
        'camera':{'trunk_depth':load(prep)['camera']['trunk_depth']+2},'camera_overrides':{'weight_focal':2.,'weight_scale':.08},
        'lm_lr_scale':.7,'unknown_extra':None}
    refusals={}
    for key,value in variants.items():
        bad=deepcopy(p);bad[key]=value
        reason=compare(bad,cfg);assert key in reason and reason!='ADMIT',reason
        refusals[key]=reason
    bad=deepcopy(cfg);bad['routing_opener_init']='reset'
    refusals['N_reset']=compare(p,bad)
    assert refusals['N_reset']=='P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init'
    out['refuse'][name]=refusals
(O/'RESULT.json').write_text(json.dumps(out,indent=2));m.save(O)
print(json.dumps(out,indent=2))
