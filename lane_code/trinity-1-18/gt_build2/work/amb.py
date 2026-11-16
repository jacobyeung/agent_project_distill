import numpy as np, glob, sys
from concurrent.futures import ProcessPoolExecutor
def one(p):
    with np.load(p) as z:
        if 'membership_instance_ids' not in z.files: return p,'single',0,0
        ids=z['membership_instance_ids']; off=z['membership_face_offsets']; idx=z['membership_face_indices']; nF=len(z['faces'])
    owner=np.full(nF,-1,np.int64); amb=np.zeros(nF,bool); dup=0
    for r,iid in enumerate(ids):
        s=idx[off[r]:off[r+1]]
        u,cn=np.unique(s,return_counts=True); dup+=int((cn>1).sum())
        prev=owner[u]; amb[u[(prev!=-1)&(prev!=iid)]]=True; owner[u]=np.where(prev==-1,iid,owner[u])
    return p,'csr',int(amb.sum()),dup
ps=glob.glob('/scratch/jjyeung/orch_n30/gt_build/stage/scannetpp/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/*/scene_assets/*/gt/instance_mesh.npz')
with ProcessPoolExecutor(8) as ex:
    for p,k,a,d in ex.map(one,ps): print(p.split('/')[-3],k,'ambiguous faces',a,'within-instance dup faces',d)
