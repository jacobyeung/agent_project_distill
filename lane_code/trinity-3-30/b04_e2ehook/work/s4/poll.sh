L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; R=$L/parity_kit/gpu_results/own_depth_p0
cat $L/work/gpu_launch.log; grep -v -i "warn\|fast path\|linear_sum" $L/work/gpu_own_depth_p0.log | tail -c 1500; echo
nvidia-smi -i 3 --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; ls $R 2>&1 | head; wc -l $R/items.jsonl 2>&1
/scratch/jjyeung/envs/vllm/bin/python -c "
import json
for l in open('$R/items.jsonl'):
    r=json.loads(l); c=(r.get('calls') or {}); print(r['key'], r['question_type'], r['scores'], r['finish'], round(r['seconds']), c.get('calls'), c.get('unserved'), r.get('scale'))
" 2>&1 | tail -6
tmux ls 2>&1 | grep b04_
cd /dev/shm/jjyeung/b04/host2/b04_e2ehook && bwrap --dev-bind / / --bind /dev/shm/jjyeung /scratch/jjyeung/b04shm bash -c 'cd /scratch/jjyeung/b04shm/b04/host2/b04_e2ehook && PYTHONPATH=/scratch/jjyeung/b04shm/b04/pyoverlay:. timeout 600 nice /scratch/jjyeung/envs/vllm/bin/python -B -m parity_kit.compare --new parity_kit/gpu_results/own_depth_p0/items.jsonl --out parity_kit/gpu_results/cmp_p0_interim' 2>&1 | grep -v -i warn | tail -c 2500
