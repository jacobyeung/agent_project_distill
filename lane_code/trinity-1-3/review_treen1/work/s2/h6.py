import json,os,sys,math,traceback
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c');K=W/'pkg';T=Path(sys.argv[1]);BASE=K/'work/base/tree_b01ce449'
os.chdir(T);sys.path[:0]=[str(T)]
from student_pilot import carrier_c1_run as run, r1_training as contract, r1_handover
from student_pilot.p3_provenance import digest,file_pin,load
from tests.test_r2_build_n1 import configuration,sampling,write
from tests.test_r2_n1fix import sealed_functions
from tests.test_carrier_c1 import fixture
OUT={}
def rec(name,f):
    try:OUT[name]=f()
    except Exception as e:OUT[name]='REFUSED '+type(e).__name__+': '+str(e)[:200]
    print(name,'=>',OUT[name],flush=True)
def make(root,ptweak=lambda p:None,preptweak=None,step=200):
    root.mkdir(parents=True,exist_ok=True);cfg=configuration()
    p=dict(base_identity='fixture',trace_program_version='3.13',training_mode='final',recipe=deepcopy(run.recipe_for(cfg)),streams={})
    p.update({k:deepcopy(cfg[k]) for k in ('mix','world_size','reference_world_size','steps','milestones')})
    p['scheduled_sampling']=deepcopy(p['recipe']['scheduled_sampling']);p['recipe']=run.recipe_for(p)
    ptweak(p);p['recipe']=run.recipe_for(p)
    streams={}
    for name,count in contract.STREAMS.items():
        db=dict(path=str(root/(name+'.db')),sha256=digest(name));pin=write(root/(name+'.json'),dict(database=db,count=count))
        p['streams'][name]=pin;streams[name]=dict(receipt=pin,database=db,count=count,source_count=count)
    ident=r1_handover.sealed_identity(p)
    prep=write(root/'preparation.json',dict(schema='c1-preparation-v1',config_sha256=ident,streams=streams,recipe=p['recipe'],training_mode='final'))
    p['preparation']=prep;ppin=write(root/'config.json',p)
    bound=dict(config_sha256=ident,preparation=prep,world_size=4,trainer_commit='fixture')
    fn=sealed_functions();fn['bind_output'](root,bound)
    model,_,_=fixture(4,training_mode='final');dest=root/f'm{step}'
    if not dest.exists():
        with patch.object(run.dist,'get_rank',return_value=0),patch.object(run.dist,'get_world_size',return_value=1),patch.object(run.dist,'barrier'),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
            fn['export'](dest,model,model,p,step)
    apin=file_pin(dest/'artifact.json');art=load(apin['path'])
    assert art['config_sha256']==fn['identity'](p) and 'r1_progress' not in art
    cfg['init_artifact']=dict(artifact=apin)
    cfg['r1_training'].update(donor_config_sha256=ident,p_run=dict(config=ppin,preparation=prep,binding=file_pin(root/'binding.json')))
    binding,counts=sampling(root/'n_sampler');cfg['r2_sampling']=binding
    cfg['r1_training'].update(continuation_identity='a'*64,store_hashes={'vqa':'b'*64},row_plan_sha256=digest(binding))
    return cfg,p,art,root
def mapping(cfg,art,root,name='map.json',source=None):
    actual=source or r1_handover.donor(cfg,art)[2];exp=contract.boundary(cfg,art['step'])
    cfg['r1_training']['handover_mapping']=write(root/name,dict(schema='r1-handover-map-v1',artifact_sha256=cfg['init_artifact']['artifact']['sha256'],step=art['step'],source=actual,target={k:exp[k] for k in actual}))
    return cfg
R=W/'tmp'/sys.argv[2]
cfg,p,art,root=make(R/'clean')
cx,px,ax,rx=make(R/'other',lambda p:p.update(weights={'pose':2.0}))
OUT['identities_differ']=art['config_sha256']!=ax['config_sha256']
c=deepcopy(cfg);c['init_artifact']=deepcopy(cx['init_artifact'])
src=r1_handover.sealed_identity(p)
fake=dict(config_identity=src,stores=r1_handover.donor(cfg,art)[2]['stores'],row_plan_sha256=r1_handover.donor(cfg,art)[2]['row_plan_sha256'])
mapping(c,ax,R,'map_h6.json',source=fake)
rec('export_from_other_config_paired_with_P_config',lambda:contract.start(c))
c2=deepcopy(cfg);b=load(c2['r1_training']['p_run']['binding']['path']);b['config_sha256']='f'*64;c2['r1_training']['p_run']['binding']=write(R/'bind_bad.json',b)
rec('binding_config_sha_wrong',lambda:contract.start(c2))
(W/('H6_'+sys.argv[2]+'.json')).write_text(json.dumps(OUT,indent=1,default=str))
