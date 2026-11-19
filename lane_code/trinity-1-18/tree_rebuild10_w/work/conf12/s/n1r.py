import json,os,sys,shutil
from copy import deepcopy
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12');K=W/'pkg';T=K/'work/tree_r1'
os.environ.setdefault('TMPDIR',str(W/'tmp'));os.environ['R2_FIXTURES']=str(K/'fixtures');os.environ['R2_PROOFS']=str(W/'tmp/n1r_proofs')
os.chdir(T);sys.path[:0]=[str(T)]
from student_pilot import carrier_c1_run as run, r1_training as contract, r1_handover as H
from student_pilot.p3_provenance import digest,file_pin,load
from tests.test_r2_build_n1 import write
from tests.test_r2_n1fix import handover_fixture
from tests.test_carrier_c1 import fixture
from student_pilot.carrier_c1 import parameter_groups
OUT={}
def rec(name,f):
    try:OUT[name]=f()
    except Exception as e:OUT[name]='REFUSED '+type(e).__name__+': '+str(e)[:200]
    print(name,'=>',str(OUT[name])[:220],flush=True)
R=W/'tmp/n1r'
def hf(tag,**kw):
    return handover_fixture(R/tag,**kw)
both=lambda c,a:(H.progress(c,a)['step'],contract.start(c))
# honest
cfg,p,model,art=hf('honest');rec('honest_progress_and_start',lambda:both(cfg,art))
sc=dict(lm_lr_scale=cfg.get('lm_lr_scale',1.0),pose_lr_scale=cfg.get('pose_lr_scale',1.0))
# N1X(1): N has depth_init, P not
c=deepcopy(cfg);c['depth_init']={'path':'/scratch/fsw/x/step_400/heads.json','sha256':'f'*64};rec('N1X_N_depth_init_P_none',lambda:both(c,art))
# P has depth_init, N not
dp=dict(sc,depth_init={'path':'/x/heads.json','sha256':'f'*64})
c,pp,m,a=hf('p_depth',donor_scales=dp);rec('P_depth_init_N_none',lambda:both(c,a))
# equal depth pins -> admit ; same sha different path -> refuse
c2=deepcopy(c);c2['depth_init']=deepcopy(dp['depth_init']);rec('equal_depth_pins',lambda:both(c2,a))
c3=deepcopy(c);c3['depth_init']={'path':'/y/heads.json','sha256':'f'*64};rec('same_sha_other_path',lambda:both(c3,a))
# N1X(2): P initialised from a C1-r artifact with head_init (real file)
R.mkdir(parents=True,exist_ok=True)
hi=write(R/'c1r_artifact.json',dict(head_init=dict(prefix='global_camera_head.',copied=['trunk.0.ls1','token_norm.weight'],derived=['embed_pose.bias'])))
c,pp,m,a=hf('p_headinit',donor_scales=dict(sc,init_artifact=dict(artifact=hi,heads=['pose','depth'],lm='full')));rec('N1X_P_c1r_head_init',lambda:both(c,a))
c,pp,m,a=hf('p_headinit_fake',donor_scales=dict(sc,init_artifact=dict(artifact={'path':'c1r/artifact.json','sha256':'e'*64},heads=['pose','depth'],lm='full')));rec('N1X_P_head_init_unreadable(old input)',lambda:both(c,a))
# honest P initialised from the real kit init artifact (1d6eeb28, no head_init)
ia=K/'work/n1fix2/inputs/init_artifact.json';ip=file_pin(ia);OUT['kit_init_sha']=ip['sha256'];OUT['kit_init_has_head_init']='head_init' in load(str(ia))
c,pp,m,a=hf('p_from_544',donor_scales=dict(sc,init_artifact=dict(artifact=ip,heads=['pose','depth','frame_embeddings'],lm='full')));rec('P_from_1d6eeb28_readable',lambda:both(c,a))
moved=dict(sc,init_artifact=dict(artifact={'path':'/scratch/fsw/elsewhere/init_artifact.json','sha256':ip['sha256']},heads=['pose','depth','frame_embeddings'],lm='full'))
c,pp,m,a=hf('p_from_544_moved',donor_scales=moved);rec('P_from_1d6eeb28_path_absent_on_N_host',lambda:both(c,a))
# extra config inputs that change parameter groups (not in optimizer_contract)
OUT['contract_keys']=sorted(H.optimizer_contract(cfg))
mt,_,_=fixture(4,training_mode='final');mf,_,_=fixture(4,training_mode='final',depth_enabled=False)
gn=lambda mm:[(g['name'],len(g['params']),g['lr']) for g in parameter_groups(mm)]
OUT['groups_depth_enabled_true']=gn(mt);OUT['groups_depth_enabled_false']=gn(mf)
c,pp,m,a=hf('p_depth_disabled',donor_scales=dict(sc,depth_enabled=False));rec('EXTRA_P_depth_enabled_False',lambda:both(c,a))
rec('EXTRA_P_depth_enabled_False_native_table_equal',lambda:(lambda t:t['source']==t['target'])(H.verify_trainable_groups(c,m)))
al={'cam':{'layer':-1},'projector':{'width':'2H','depth':2}}
c,pp,m,a=hf('p_align',donor_scales=dict(sc,align=al));rec('EXTRA_P_align',lambda:both(c,a))
cam=deepcopy(cfg.get('camera') or {});
if cam: cam['trunk_depth']=cam.get('trunk_depth',4)+2
c,pp,m,a=hf('p_camera',donor_scales=dict(sc,camera=cam));rec('EXTRA_P_camera_trunk_depth',lambda:both(c,a))
# step-544 parent with the real kit config
kc=load(str(K/'work/n1fix2/inputs/config.json'));OUT['PARENT']=contract.PARENT
c11=deepcopy(kc);c11['init_artifact']=dict(kc['init_artifact'],artifact=dict(path=str(ia),sha256=kc['init_artifact']['artifact']['sha256']))
rec('parent_544_start',lambda:contract.start(c11))
rec('parent_544_verify_trainable_groups',lambda:H.verify_trainable_groups(c11,mt))
(W/'N1R.json').write_text(json.dumps(OUT,indent=1,default=str))
