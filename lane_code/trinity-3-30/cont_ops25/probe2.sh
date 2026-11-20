ls /scratch/jjyeung/devs1_frames | head; ls /scratch/jjyeung/devs1_frames/* | head -8
d=$(ls -d /scratch/jjyeung/devs1_frames/*/ 2>/dev/null | head -1); ls $d | head -5
find /scratch/jjyeung/devs1_frames -maxdepth 4 -name '*41069054*' | head -5
ls -la /scratch/jjyeung/k1/g3t/ | head; sha256sum /scratch/jjyeung/k1/g3t/model.safetensors
ls /scratch/jjyeung/envs/; ls /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python* 2>/dev/null | head -2
/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -c "import torch;print(torch.__version__, torch.version.cuda)" 2>&1 | tail -1
nvidia-smi --query-compute-apps=pid,used_memory --format=csv | head -12
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader | head -8); do ps -o user=,pid=,etime=,cmd= -p $p | cut -c1-150; done
grep -n 'g3t\|safetensors' /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/e2e_reader/real.py | head -10
