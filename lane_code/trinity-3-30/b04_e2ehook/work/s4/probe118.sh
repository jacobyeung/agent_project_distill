df -h /scratch | tail -1; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';'; echo
ls /scratch/jjyeung/orch_n30/b04host/ /scratch/jjyeung/orch_n30/b04host/b04_e2ehook/parity_kit | head -40
ls /scratch/jjyeung/orch_n30/b05_owngrd/ /scratch/jjyeung/orch_n30/b05_owngrd/code 2>&1 | head; ls /scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd/vendor 2>&1 | head
ls /scratch/jjyeung/envs/ | head -30; ls /scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3*/site-packages | grep -i -E "^(sam3|scipy|torch|transformers|iopath|timm|pycocotools|ftfy)" | head
ls -la /scratch/jjyeung/k1/ | head -20; ls /scratch/jjyeung/devs1_frames | head -3
