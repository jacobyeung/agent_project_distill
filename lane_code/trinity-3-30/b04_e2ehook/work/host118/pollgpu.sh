L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; R=$L/parity_kit/gpu_results/own_depth_p0
cat $L/work/gpu_launch.log; grep -v -i "warn\|fast path\|linear_sum" $L/work/gpu_own_depth_p0.log | tail -c 1500; echo
nvidia-smi -i 3 --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; ls $R 2>&1 | head; wc -l $R/items.jsonl 2>&1
/scratch/jjyeung/envs/vllm/bin/python -c "
import json
for l in open('$R/items.jsonl'):
    r=json.loads(l); c=(r.get('calls') or {}); print(r['key'], r['question_type'], r['scores'], r['finish'], round(r['seconds']), c.get('calls'), c.get('unserved'), r.get('scale'))
" 2>&1 | tail -6
