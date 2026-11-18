import json,os,sys,math,traceback
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c');K=W/'pkg';T=K/'work/tree_r1';BASE=K/'work/base/tree_b01ce449'
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
R=W/'tmp/n1'
cfg,p,art,root=make(R/'clean')
rec('clean_no_mapping',lambda:contract.start(cfg))
mapping(cfg,art,root)
rec('clean_with_mapping_start',lambda:contract.start(cfg))
pr=r1_handover.progress(cfg,art)
OUT['clean_positions']=pr['sampler_positions'];OUT['clean_donor_plan_sha']=digest(pr['donor_row_plan'])
# independent sampler: base tree's own mixed_indices in a subprocess
import subprocess
code=f"""
import sys,json;sys.path.insert(0,{str(BASE)!r})
from student_pilot.carrier_c1_data import mixed_indices
from student_pilot.p3_provenance import digest
from student_pilot.decoupled_v import learning_rate
from student_pilot.carrier_c1_sweep import recipe_for
plan=json.loads(sys.argv[1]);cfg=json.loads(sys.argv[2])
full=list(mixed_indices(dict(plan['counts']),201,training_mode=plan['training_mode'],mix=plan['mix'],world=plan['world']))
pos={{}}
for rows in full[:200]:
    for n,v in rows:pos[n]=pos.get(n,0)+len(v)
r=recipe_for(cfg)
print(json.dumps(dict(pos=pos,next=digest(full[200]),lr201=learning_rate(201,r),lr200=learning_rate(200,r))))
"""
b=json.loads(subprocess.run([sys.executable,'-I','-s','-B','-c',code,json.dumps(pr['donor_row_plan']),json.dumps(p)],capture_output=True,text=True,check=True).stdout)
from student_pilot.decoupled_v import learning_rate
rN=run.recipe_for(cfg)
OUT['base_sampler']=dict(positions_equal=b['pos']==pr['sampler_positions'],next_plan_equal=b['next']==pr['donor_next_plan_sha256'],
  lr201_base_P=b['lr201'],lr201_tree_N=learning_rate(contract.start(cfg)+1,rN),lr_equal=b['lr201']==learning_rate(contract.start(cfg)+1,rN))
print(OUT['base_sampler'],flush=True)
# old forged receipt (PEXPORT): continuation_receipt without p_run
f=deepcopy(cfg);f['r1_training'].pop('p_run');f['r1_training'].pop('handover_mapping')
f['r1_training']['continuation_receipt']=write(R/'forged.json',dict(contract.boundary(cfg,200),artifact_sha256=cfg['init_artifact']['artifact']['sha256']))
rec('forged_receipt_no_p_run',lambda:contract.start(f))
f2=deepcopy(cfg);f2['r1_training']['continuation_receipt']=f['r1_training']['continuation_receipt'];f2['init_artifact']['artifact']=dict(cfg['init_artifact']['artifact'])
art_r1=dict(art,r1_progress=contract.boundary(cfg,200))
rec('inline_r1_progress_ignored_mapping_removed',lambda:(lambda c:(c['r1_training'].pop('handover_mapping'),r1_handover.progress(c,art_r1)['step'])[1])(deepcopy(cfg)))
# P stores / config / row plan differ from N without mapping -> refuse; with stale mapping -> refuse
for key,val in [('store_hashes',{'vqa':'d'*64}),('continuation_identity','d'*64),('donor_config_sha256','d'*64)]:
    bad=deepcopy(cfg);bad['r1_training'][key]=val;rec('stale_mapping_'+key,lambda:contract.start(bad))
# P mix differs per step (vqa 96 routing 96) -> positions refuse even with mapping
def mx(p):
    m=deepcopy(p['mix']);OUT.setdefault('P_mix_original',m)
    ks=list(m) if isinstance(m,dict) else None
    if isinstance(m,dict) and 'vqa' in m and 'routing' in m:
        m['vqa'],m['routing']=m['routing'],m['vqa']
    p['mix']=m
c2,p2,a2,r2=make(R/'mix',mx);OUT['P_mix_tweaked']=p2['mix']
rec('P_mix_differs_with_mapping',lambda:contract.start(mapping(c2,a2,r2)))
# P LR recipe differs
def lr(p):p['warmup_ratio']=0.05;p['learning_rate']=p.get('learning_rate',1e-5)
c3,p3,a3,r3=make(R/'lr',lambda p:p.update(warmup_ratio=0.07))
rec('P_warmup_differs_with_mapping',lambda:contract.start(mapping(c3,a3,r3)))
# P lm_lr_scale / pose_lr_scale differ (cfg-level LR multipliers, outside recipe)
c4,p4,a4,r4=make(R/'lrscale',lambda p:p.update(lm_lr_scale=0.5,pose_lr_scale=3.0))
OUT['N_lm_lr_scale']=cfg.get('lm_lr_scale');OUT['N_pose_lr_scale']=cfg.get('pose_lr_scale')
rec('P_lr_scales_differ_with_mapping',lambda:contract.start(mapping(c4,a4,r4)))
# P has a row_start_step offset / r1_training -> unsupported
c5,p5,a5,r5=make(R/'offset',lambda p:p.update(row_start_step=10))
rec('P_offset_with_mapping',lambda:contract.start(mapping(c5,a5,r5)))
# N-side targets are operator values: arbitrary continuation_identity / store_hashes admit when the mapping copies them
c6=deepcopy(cfg);c6['r1_training'].update(continuation_identity='7'*64,store_hashes={'vqa':'8'*64,'pose':'9'*64});mapping(c6,art,root,'map6.json')
rec('N_target_arbitrary_identity_and_stores',lambda:contract.start(c6))
# forged preparation: P config preparation field is outside identity; forge vqa indices subset
src=load(cfg['r1_training']['p_run']['config']['path']);prep=load(cfg['r1_training']['p_run']['preparation']['path'])
fp=deepcopy(prep);n=fp['streams']['vqa']['count']-1;fp['streams']['vqa']['count']=n;fp['streams']['vqa']['indices']=write(R/'forged_idx.json',list(range(1,n+1)))
fprep=write(R/'forged_prep/preparation.json',fp);fsrc=dict(src,preparation=fprep);fcfgpin=write(R/'forged_prep/config.json',fsrc)
fb=load(cfg['r1_training']['p_run']['binding']['path']);fb['preparation']=fprep;fbpin=write(R/'forged_prep/binding.json',fb)
c7=deepcopy(cfg);c7['r1_training']['p_run']=dict(config=fcfgpin,preparation=fprep,binding=fbpin)
OUT['forged_prep_identity_unchanged']=r1_handover.sealed_identity(fsrc)==art['config_sha256']
mapping(c7,art,R,'map7.json')
rec('forged_preparation_admits',lambda:contract.start(c7))
OUT['forged_prep_donor_plan_differs']=digest(r1_handover.donor(c7,art)[3])!=OUT['clean_donor_plan_sha']
# artifact step 199 vs N; step 0
c8,p8,a8,r8=make(R/'s137',step=137)
rec('step137_admits_at',lambda:contract.start(mapping(c8,a8,r8)))
# step-544 parent unchanged
kc=load(K/'work/n1fix/inputs/config.json');OUT['kit_init_sha']=kc['init_artifact']['artifact']['sha256']
pa=dict(schema='carrier-c1-artifact-v1',step=544);pp=write(R/'parent/d.json',pa)
with patch.object(contract,'PARENT',pp['sha256']):
    c9=deepcopy(kc);c9['init_artifact']=dict(artifact=pp);rec('parent_544_start',lambda:contract.start(c9))
    c10=deepcopy(c9);pp2=write(R/'parent2/d.json',dict(pa,step=543));c10['init_artifact']=dict(artifact=pp2)
OUT['PARENT_constant']=contract.PARENT
(W/'N1_HANDOVER.json').write_text(json.dumps(OUT,indent=1,default=str))
