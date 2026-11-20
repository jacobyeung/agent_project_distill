cd /scratch/jjyeung/orch_n30/sb_own400/in/own_544_fov || exit 1
OMP_NUM_THREADS=2 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,hashlib,numpy as np,os
D='native/probe';n=eq=0;v2=0
for k in sorted(os.listdir(D)):
  if len(k)!=16:continue
  rec=json.load(open(f'{D}/{k}/FOV_RECEIPT.json'))
  with np.load(f'/scratch/jjyeung/k1/own_170235/native/probe/{k}/own.npz') as z:d=np.ascontiguousarray(z['depth'])
  with np.load(f'{D}/{k}/fov.npz') as f:keys=sorted(f.files);g2=f['fov_V2'];dv=f['depth_V1']
  n+=1;eq+=hashlib.sha256(d.tobytes()).hexdigest()==rec['served_depth_sha256'];v2+=keys==['depth_V1','depth_V2','fov_B','fov_V1','fov_V2'] and dv.dtype==np.float64 and g2.dtype==np.float32
print('captures',n,'served_sha_equal_own170235',eq,'keys_dtypes_ok',v2)
PY
