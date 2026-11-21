echo "--- hf snapshot candidates on scratch"
timeout 90 find /scratch/jjyeung -maxdepth 5 -type d -name 'models--Qwen--Qwen3.5-9B' 2>/dev/null | head
timeout 60 find /scratch/jjyeung -maxdepth 7 -type d -name 'c202236235762e1c871ad0ccb60c8ee5ba337b9a' 2>/dev/null | head
echo "--- p1cpu"; /scratch/jjyeung/envs/p1cpu/bin/python -I -c 'import sys;print(sys.version)'
ls /scratch/jjyeung/envs/p1cpu/lib/python3*/site-packages | grep -i -E "^(trace_format|fla|triton|peft|accelerate|safetensors|numpy|PIL|pillow|torchvision|av|decord|cv2|opencv)" | tr '\n' ' '
echo; echo "--- trace_format anywhere"; timeout 60 find /scratch/jjyeung/orch_n30/tree_rebuild10_w -maxdepth 4 -type d -name 'trace_format' 2>/dev/null | head -5
nproc; uptime
