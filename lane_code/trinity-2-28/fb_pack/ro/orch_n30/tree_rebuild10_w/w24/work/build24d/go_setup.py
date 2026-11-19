from pathlib import Path
from copy import deepcopy
import json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';O=L/'work/build24/proofs/capacity'
sys.path[:0]=[str(D),str(L/'work/build24'),str(L/'work/tree_r1')]
from patch import reseal
import joblib as J
from launch_r2.build import capsule_json
k=L/'out/kit_n_go';shutil.copytree(L/'work/build24/kits/n',k)
c=J.load(k/'k/a.json');c['GO']=True;(k/'k/a.json').write_bytes(capsule_json(c));reseal(k,True)
root=D/'go';root.mkdir();ns='/tmp/q_22c714e1'
cfg=J.load(L/'work/build24b/proofs/capacity/n/h/config.json')
original=J.load(J.load(O/'400/request.json')['config']['path'])
cfg['output']=ns+'/train';cfg['r1_training']['stop_after_step']=2
cfg['streams']=original['streams'];cfg['r1_training'].pop('direction_augmented',None)
cfg['r1_training']['room_audit']=J.load(O/'400/request.json')['room_audit']
cfg.pop('preparation',None);cfg.pop('admission',None)
cfgpin=J.write(root/'input.json',cfg)
paths={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
request=J.load(O/'400/request.json');request.update(config=cfgpin,staged_pins=[cfgpin],routing_base=cfg['streams']['routing'],weights=True,device='cpu',memory_gib=18,_paths=paths)
J.write(root/'r.json',request);J.write(root/'n.json',cfg)
old=str(L.parent/'w21');args=[x.replace(old,str(L)) for x in J.load(L/'work/build21g/proofs/view/after.json')]
args+=['--bind',str(root),str(root),'--bind',str(root),ns,'--bind',str(k),str(k)]
J.write(D/'GO_VIEW.json',args)
J.write(D/'GO_SETUP.json',dict(kit=str(k),seal=J.seal(k),namespace=ns,fixture=dict(config=cfgpin,horizon=2,init_milestone=400),first_scheduled_export=100,gate_step=400))
