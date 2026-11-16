import numpy as np, os, sys
G='/scratch/jjyeung/orch_n30/gt_build'
ups=set(open(G+'/work/ups.txt').read().split())
for c in open('/tmp/gb2_bad.txt').read().split()+['47115265','41126341','42898477']:
    a=f'{G}/out/rejected/arkit_gt/{c}.npz'; b=f'{G}/out/variants/all_r180_pose64/{c}.npz'
    if c=='47115265': a=f'{G}/out/dose_pool/out/arkit_gt/gt/{c}.npz'
    if c in ('41126341','42898477'): a=f'{G}/out/dose_pool/out/arkit_gt/gt/{c}.npz'; b=f'/dev/null'
    if c in ups or not os.path.exists(a) or not os.path.exists(b) or b=='/dev/null': continue
    A=np.load(a); B=np.load(b)
    diff={k:int((A[k]!=B[k]).sum()) for k in A.files if A[k].shape==B[k].shape and (A[k]!=B[k]).any()}
    print(c, diff, os.path.getsize(a)-os.path.getsize(b))
