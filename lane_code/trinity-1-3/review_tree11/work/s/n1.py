import json,os,sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
W=Path('/scratch/jjyeung/orch_n30/review_tree11/work/n1');K=W/'pkg';T=K/'work/tree_r1';BASE=K/'work/base/tree_b01ce449'
os.chdir(T);sys.path[:0]=[str(T)]
from student_pilot import carrier_c1_run as run, r1_training as contract, r1_handover as H
from student_pilot.p3_provenance import digest,file_pin,load
from tests.test_r2_build_n1 import configuration,sampling,write
from tests.test_r2_n1fix import sealed_functions
from tests.test_carrier_c1 import fixture
OUT={}
def rec(name,f):
    try:OUT[name]=f()
    except Exception as e:OUT[name]='REFUSED '+type(e).__name__+': '+str(e)[:160]
    print(name,'=>',OUT[name],flush=True)
FN=sealed_functions()
def make(root,ptweak=lambda p:None,step=200,ntweak=lambda c:None,same_streams=False):
    root.mkdir(parents=True,exist_ok=True);cfg=configuration();ntweak(cfg)
    p=dict(base_identity='fixture',trace_program_version='3.13',training_mode='final',recipe=deepcopy(run.recipe_for(cfg)),streams={})
    p.update({k:deepcopy(cfg[k]) for k in ('mix','world_size','reference_world_size','steps','milestones')})
    p['scheduled_sampling']=deepcopy(p['recipe']['scheduled_sampling'])
    p.update({k:cfg[k] for k in ('lm_lr_scale','pose_lr_scale') if k in cfg})
    ptweak(p);p['recipe']=run.recipe_for(p)
    streams={}
    for name,count in contract.STREAMS.items():
        db=dict(path=str(root/('P_'+name+'.db')),sha256=digest('P'+name));pin=write(root/('P_'+name+'.json'),dict(database=db,count=count))
        p['streams'][name]=pin;streams[name]=dict(receipt=pin,database=db,count=count,source_count=count)
    ident=H.export_identity(p)
    prep=write(root/'preparation.json',dict(schema='c1-preparation-v1',config_sha256=ident,streams=streams,recipe=p['recipe'],training_mode='final'))
    p['preparation']=prep;ppin=write(root/'config.json',p)
    bound=dict(config_sha256=ident,preparation=prep,world_size=4,trainer_commit='fixture')
    FN['bind_output'](root,bound)
    complete=write(root/'ckpt/complete.json',dict(schema='c1-checkpoint-v1',binding=bound,step=step,layouts=[],files={}))
    model,_,_=fixture(4,training_mode='final');dest=root/f'm{step}'
    if not dest.exists():
        with patch.object(run.dist,'get_rank',return_value=0),patch.object(run.dist,'get_world_size',return_value=1),patch.object(run.dist,'barrier'),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
            FN['export'](dest,model,model,p,step)
    apin=file_pin(dest/'artifact.json');art=load(apin['path'])
    assert art['config_sha256']==FN['identity'](p)
    cfg['init_artifact']=dict(artifact=apin)
    cfg['r1_training'].update(donor_config_sha256=ident,p_run=dict(config=ppin,preparation=prep,binding=file_pin(root/'binding.json'),checkpoint=complete))
    if same_streams: cfg['streams']=deepcopy(p['streams'])
    else:
        cfg['streams']={}
        for name in contract.STREAMS:
            db=dict(path=str(root/('N_'+name+'.db')),sha256=digest('N'+name))
            cfg['streams'][name]=write(root/('N_'+name+'.json'),dict(database=db,count=999))
    binding,_=sampling(root/'n_sampler');cfg['r2_sampling']=binding;cfg['r1_training']['row_plan_sha256']=digest(binding)
    t=contract.target_identity(cfg);cfg['r1_training'].update(continuation_identity=t['config_identity'],store_hashes=t['stores'])
    return cfg,p,art,root
def retarget(cfg):
    t=contract.target_identity(cfg);cfg['r1_training'].update(continuation_identity=t['config_identity'],store_hashes=t['stores']);return cfg
def mapping(cfg,art,root,name='map.json',target=None):
    cfg['r1_training'].pop('handover_mapping',None)
    if target is None: retarget(cfg)
    actual=H.donor(cfg,art)[2];exp=target or {k:contract.boundary(cfg,art['step'])[k] for k in actual}
    cfg['r1_training']['handover_mapping']=write(root/name,dict(schema='r1-handover-map-v1',artifact_sha256=cfg['init_artifact']['artifact']['sha256'],step=art['step'],source=actual,target=exp))
    return cfg
R=W/'tmp/n1r4'
# --- honest
cfg,p,art,root=make(R/'clean')
c0=deepcopy(cfg);rec('clean_no_mapping',lambda:contract.start(c0))
mapping(cfg,art,root);rec('clean_with_mapping',lambda:contract.start(cfg))
cs,ps,as_,rs=make(R/'clean_same',same_streams=True);mapping(cs,as_,rs);rec('clean_same_streams_with_mapping',lambda:contract.start(cs))
# --- N1a
N=configuration();OUT['N_kit_like_scales']=(N.get('lm_lr_scale'),N.get('pose_lr_scale'))
def sc(lm,po):
    def f(p):
        for k,v in (('lm_lr_scale',lm),('pose_lr_scale',po)):
            if v is None:p.pop(k,None)
            else:p[k]=v
    return f
n06=lambda c:c.update(lm_lr_scale=0.6,pose_lr_scale=0.6)
for tag,lm,po in (('absent',None,None),('one',1.0,1.0),('lm_only_1',1.0,0.6),('pose_only_1',0.6,1.0),('match',0.6,0.6)):
    c,pp,a,r=make(R/('sc_'+tag),sc(lm,po),ntweak=n06);rec('N1a_P_'+tag+'_vs_N_0.6',lambda:contract.start(mapping(c,a,r)))
# other optimizer inputs
base_c=H.optimizer_contract(load(cfg['r1_training']['p_run']['config']['path']))
OUT['N1a_contract_keys']=sorted(base_c)
for k,v in (('mdg',{'lr_scale':2.0,'lora_lr':1e-4}),('geometry_online',{'mode':'x'})):
    src0=load(cfg['r1_training']['p_run']['config']['path'])
    with patch('student_pilot.carrier_c1_sweep.recipe_for',side_effect=lambda c:run.recipe_for({kk:vv for kk,vv in c.items() if kk not in ('mdg','geometry_online')})):
        OUT['N1a_contract_detects_'+k]=H.optimizer_contract(dict(src0,**{k:v}))!=base_c
for tag,tw in (('warmup',lambda p:p.setdefault('recipe',{}).update(warmup_ratio=0.07)),
               ('steps',lambda p:p.update(steps=p['steps']+100,milestones=p['milestones']))):
    try:
        c,pp,a,r=make(R/('opt_'+tag),tw);rec('N1a_P_'+tag+'_differs',lambda:contract.start(mapping(c,a,r)))
    except Exception as e:OUT['N1a_P_'+tag+'_differs']='FIXTURE_REFUSED '+type(e).__name__+': '+str(e)[:160];print(tag,OUT['N1a_P_'+tag+'_differs'])
# mapping cannot override: forged mapping whose source claims matched scales
c,pp,a,r=make(R/'sc_mapover',sc(1.0,1.0),ntweak=n06)
rec('N1a_mapping_written_before_check',lambda:contract.start(mapping(c,a,r)))
# head_init / inherited groups are not in the contract
P_inh=dict(load(c['r1_training']['p_run']['config']['path']))
OUT['N1a_contract_ignores_init_artifact']=H.optimizer_contract(P_inh)==H.optimizer_contract(dict(P_inh,init_artifact={'artifact':{'path':'x','sha256':'0'*64},'heads':['pose'],'lm':'full'}))
model,_,_=fixture(4,training_mode='final')
names=[n.removeprefix('auxiliary_heads.pose.head.') for n,_ in model.named_parameters() if n.startswith('auxiliary_heads.pose.head.')][:3]
from student_pilot.carrier_c1 import parameter_groups
g0={g['name']:g['lr'] for g in parameter_groups(model,pose_lr_scale=0.6,lm_lr_scale=0.6)}
g1={g['name']:g['lr'] for g in parameter_groups(model,inherited=set(names),pose_lr_scale=0.6,lm_lr_scale=0.6)}
OUT['N1a_inherited_groups']=dict(names=names,without=g0,with_inherited=g1)
# --- N1b
cb=deepcopy(cfg);cb['r1_training'].pop('handover_mapping',None);cb['r1_training'].update(continuation_identity='7'*64,store_hashes={'vqa':'8'*64,'pose':'9'*64,'routing':'8'*64,'pointing':'9'*64})
actual=H.donor(cb,art)[2]
cb['r1_training']['handover_mapping']=None;mapping(cb,art,root,'map_forged.json',target=dict(config_identity='7'*64,stores=cb['r1_training']['store_hashes'],row_plan_sha256=cb['r1_training']['row_plan_sha256']))
rec('N1b_forged_789_with_copying_mapping',lambda:contract.start(cb))
cb2=deepcopy(cfg);cb2['r1_training']['continuation_identity']='7'*64;rec('N1b_forged_identity_only',lambda:contract.start(cb2))
cb3=deepcopy(cfg);cb3['r1_training']['store_hashes']=dict(cfg['r1_training']['store_hashes'],vqa='8'*64);rec('N1b_forged_vqa_store_only',lambda:contract.start(cb3))
# a config change after mapping: identity changes -> stale
cb4=deepcopy(cfg);cb4['pointing_weights']={'decision':1.0,'row_mean':1.0};retarget(cb4);rec('N1b_N_config_edit_after_mapping',lambda:contract.start(cb4))
# change N's stream receipt (different DB) -> stores differ
cb5=deepcopy(cfg);db=dict(path='x',sha256=digest('other'));cb5['streams']['vqa']=write(root/'N_vqa_other.json',dict(database=db,count=999));retarget(cb5)
rec('N1b_N_stream_swap_after_mapping',lambda:contract.start(cb5))
# excluded fields: N preparation, admission, authorization, milestone_gate, host_receipt, review do not change target
ex={}
for k,v in (('preparation',{'path':'p','sha256':'1'*64}),('admission',{'path':'a','sha256':'2'*64}),('milestone_gate',{'path':'m','sha256':'3'*64}),('authorization',{'path':'z','sha256':'4'*64})):
    cx=deepcopy(cfg);cx[k]=v;ex[k]=contract.target_identity(cx)['config_identity']==cfg['r1_training']['continuation_identity']
for k in ('host_receipt','review'):
    cx=deepcopy(cfg);cx['r1_training'][k]={'path':'h','sha256':'5'*64};ex['r1_training.'+k]=contract.target_identity(cx)['config_identity']==cfg['r1_training']['continuation_identity']
OUT['N1b_excluded_fields_leave_target_unchanged']=ex
# trainer identity of N also excludes preparation (same exclusions)
OUT['N1b_trainer_identity_excludes_preparation']=run.identity(dict(cfg,preparation={'path':'p','sha256':'1'*64}))==run.identity(cfg)
# step 200 honest: also step 137
c8,p8,a8,r8=make(R/'s137',step=137);rec('step137_with_mapping',lambda:contract.start(mapping(c8,a8,r8)))
# --- N1c
src=load(cfg['r1_training']['p_run']['config']['path']);prep=load(cfg['r1_training']['p_run']['preparation']['path'])
fp=deepcopy(prep);n=fp['streams']['vqa']['count']-1;fp['streams']['vqa']['count']=n;fp['streams']['vqa']['indices']=write(R/'forged_idx.json',list(range(1,n+1)))
fprep=write(R/'forged/preparation.json',fp);fsrc=dict(src,preparation=fprep);fcfg=write(R/'forged/config.json',fsrc)
fb=load(cfg['r1_training']['p_run']['binding']['path']);fb['preparation']=fprep;fbpin=write(R/'forged/binding.json',fb)
c7=deepcopy(cfg);c7['r1_training']['p_run'].update(config=fcfg,preparation=fprep,binding=fbpin)
OUT['N1c_export_identity_unchanged']=H.export_identity(fsrc)==art['config_sha256']
retarget(c7);rec('N1c_forged_prep_cfg_binding_honest_ckpt',lambda:contract.start(mapping(c7,art,R,'map7.json')))
c7b=deepcopy(c7);c7b['r1_training']['p_run']['checkpoint']=write(R/'forged/complete.json',dict(schema='c1-checkpoint-v1',binding=fb,step=200))
c7b['r1_training'].pop('handover_mapping',None)
rec('N1c_forged_prep_cfg_binding_AND_forged_ckpt',lambda:contract.start(mapping(c7b,art,R,'map7b.json')))
OUT['N1c_forged_donor_plan_counts']=dict(H.donor(c7b,art)[3]['counts']) if isinstance(OUT['N1c_forged_prep_cfg_binding_AND_forged_ckpt'],int) else None
OUT['N1c_artifact_training_source_seal']=art.get('training_source_seal','ABSENT')
# checkpoint step mismatch / missing
c9=deepcopy(cfg);c9['r1_training']['p_run'].pop('checkpoint');retarget(c9);rec('N1c_no_checkpoint',lambda:contract.start(c9))
c10=deepcopy(cfg);c10['r1_training']['p_run']['checkpoint']=write(R/'ck199/complete.json',dict(schema='c1-checkpoint-v1',binding=load(cfg['r1_training']['p_run']['binding']['path']),step=199));c10['r1_training'].pop('handover_mapping');mapping(c10,art,R,'map10.json') if False else retarget(c10);rec('N1c_ckpt_step_199',lambda:contract.start(c10))
# --- parent 544 with the real kit config
kc=load(K/'work/n1fix2/inputs/config.json');OUT['kit_init_sha']=kc['init_artifact']['artifact']['sha256'];OUT['PARENT']=contract.PARENT
ia=K/'work/n1fix2/inputs/init_artifact.json'
c11=deepcopy(kc);c11['init_artifact']=dict(kc['init_artifact'],artifact=dict(path=str(ia),sha256=kc['init_artifact']['artifact']['sha256']))
rec('parent_544_start',lambda:contract.start(c11))
(W/'N1.json').write_text(json.dumps(OUT,indent=1,default=str))
