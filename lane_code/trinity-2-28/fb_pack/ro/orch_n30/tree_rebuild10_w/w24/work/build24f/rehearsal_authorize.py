from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/'work/build24'))
import joblib as J
root=Path('/tmp/q_22c714e1');cfg=J.load(root/'v.json');auth=J.load(cfg['authorization']['path'])
auth['job_id']='b24f_'+sys.argv[1]
cfg['authorization']=J.write(root/('authorization_'+sys.argv[1]+'.json'),auth)
J.write(root/'v.json',cfg)
