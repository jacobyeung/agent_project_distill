B=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook
grep -o "stage_restore[^;]*" $B/work/host_run.sh | head -2 | cut -c1-500
for e in sam3_capretry_native_v1 sam3_scipy_ovl; do for f in /scratch/jjyeung/envs/$e/lib/python3*/site-packages/sam3/model_builder.py; do [ -f $f ] && echo "$f $(sha256sum $f | cut -c1-8)"; done; done
ls /scratch/jjyeung/envs/sam3_scipy_ovl/lib/python3.12/site-packages | head -40 | tr '\n' ' '; echo; cat /scratch/jjyeung/envs/sam3_scipy_ovl/pyvenv.cfg
/scratch/jjyeung/envs/vllm/bin/python -V; ls -d /scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3*; ls /scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3*/site-packages/sam3/ | head; ls -d /scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3*/site-packages/sam3/assets 2>&1
ls /scratch/jjyeung/envs/p1cpu/lib/python3*/site-packages | grep -i scipy
