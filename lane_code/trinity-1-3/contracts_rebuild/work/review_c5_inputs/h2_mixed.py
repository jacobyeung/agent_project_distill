"""Mixed ground + depth_at points in one live registry under a near-nadir reference: ON invariance to frame-1 yaw, and ON vs OFF metric agreement."""
import sys, json, tempfile
import numpy as np
T=sys.argv[1]; sys.path[:0]=[T,'/scratch/jjyeung/orch_n30/contracts_rebuild/work/tests_r6']
from trace_format.contracts import contract_epoch
import fixtures_contracts as F
def Rz(d):
    a=np.radians(d); return np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
CALLS=['<ground obj="chair">','<ground obj="table">','<depth_at frame=2 pts=[[300,500],[700,450]]>',
       '<dist P1 P2>','<dist P1 P3>','<dist P2 P4>','<closest A=P1,P2 B=P3,P4>','<angle S=P1 F=P2 Q=P3 rule=hard>',
       '<angle S=P3 F=P1 Q=P4 rule=medium>','<turn from=P1 at=P3 to=P2>','<area C=P1,P2,P3,P4>',
       '<pose frame=1>','<pose frame=3>','<move from=1 to=3>','<move from=3 to=1>','<turn from=1 to=3>','<gap a="chair" b="table">']
def run(kind, yaw, on, pitch=-88, all_yaw=0):
    contract, make = F.fixture(kind)
    C=contract.camera_to_world
    C[0,:3,:3]=Rz(yaw)@F.rotations(pitch,0)
    if all_yaw: C[:,:3,:3]=Rz(all_yaw)@C[:,:3,:3]; C[:,:3,3]=(Rz(all_yaw)@C[:,:3,3].T).T
    out={}
    with contract_epoch(on, heading_plane_min=.3):
        s=F.session(make(), tempfile.mkdtemp(dir='/scratch/jjyeung/orch_n30/contracts_rebuild/work/review_c5_inputs/tmp'))
        for c in CALLS:
            try: out[c]=F.response(s,c)
            except Exception as e: out[c]='EXC '+type(e).__name__+' '+str(e)[:100]
    return out
res={}
for on in (True, False):
    for yaw in (0,40,130,250):
        res[f'{"on" if on else "off"} yaw{yaw}']=run('nadir_positive',yaw,on)
res['on allyaw70']=run('nadir_positive',0,True,all_yaw=70)
json.dump(res,open(sys.argv[2],'w'),indent=1)
for c in CALLS:
    vals={k:v[c].replace('\n',' | ') for k,v in res.items()}
    on=[v for k,v in vals.items() if k.startswith('on yaw')]
    print('==',c,'| ON invariant:',len(set(on))==1)
    for k in ('on yaw0','on yaw130','off yaw0','off yaw130','on allyaw70'): print('   ',k,':',vals[k][:230])
