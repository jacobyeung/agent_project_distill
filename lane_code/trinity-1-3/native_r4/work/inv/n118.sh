set +e
cd /scratch/jjyeung/k1/g3t || exit 3
ls -la
sha256sum model.safetensors config.json
tar cf - model.safetensors config.json | timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-3.ib 'cd /scratch/jjyeung/orch_n30/native_r4/dl/g3t_ib && tar xf - && echo XF_OK'
