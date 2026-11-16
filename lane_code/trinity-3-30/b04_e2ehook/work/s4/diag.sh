R=/dev/shm/jjyeung/b04/host2/b04_e2ehook/parity_kit/gpu_results/own_depth_p0
uptime; nproc; free -g | head -2
P=$(pgrep -f "run_parity" | head -5 | tr '\n' ' '); echo "pids $P"
for p in $P; do ps -o pid,ppid,%cpu,%mem,etime,nlwp,cmd -p $p | cut -c1-200; done
top -b -n1 -o %CPU | sed -n 7,22p | cut -c1-150
which py-spy 2>/dev/null; ls /scratch/jjyeung/envs/vllm/bin/py-spy 2>/dev/null
prev=$(wc -l < $R/items.jsonl); t0=$(date +%s)
for i in $(seq 1 40); do sleep 6; n=$(wc -l < $R/items.jsonl); if [ "$n" != "$prev" ]; then echo "$(( $(date +%s)-t0 ))s line $n"; prev=$n; fi; nvidia-smi -i 3 --query-gpu=utilization.gpu --format=csv,noheader | tr '\n' ' '; done; echo
python3 -c "
import json
for l in open('$R/items.jsonl').readlines()[-6:]:
    r=json.loads(l); print(r['key'], round(r['seconds']), r.get('generated_tokens'), len(r.get('tokens',[])) if isinstance(r.get('tokens'),list) else None, r.get('decode_budget'))
" | cut -c1-300
