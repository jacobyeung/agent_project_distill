G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
cd $G && /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import numpy as np, glob, json
for v in "41069054 41291643 42899535 45663051 47332598 41159782 45261332 43828368 43649603 44358634".split():
    f=glob.glob(f'gt/**/{v}*.npz',recursive=True) or glob.glob(f'gt/*{v}*.npz')
    if not f: print(v,'no npz'); continue
    z=np.load(f[0]); fi=z['frame_indices'].tolist(); print(v, f[0], len(fi), fi[:4], fi[-2:], 'K' in z.files and z['K'].tolist())
PY
ls /scratch/jjyeung/orch_n30/nvkey1/work 2>&1 | head; ls /scratch/jjyeung/orch_n30/nvkey1/work/c0 2>&1 | head
find /scratch/jjyeung -maxdepth 6 -name '*.safetensors' -size +100M 2>/dev/null | head -20
find /scratch/jjyeung -maxdepth 5 -type d -name 'f' -path '*/d/f' 2>/dev/null | head
ls /scratch/jjyeung | head -40
