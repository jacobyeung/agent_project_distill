L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; ls -la $L/parity_kit/gpu_results/own_depth_p1/ 2>&1 | head; tail -5 $L/work/gpu_own_depth_p1.log 2>&1 | cut -c1-200
cd $L && bwrap --dev-bind / / --bind /dev/shm/jjyeung /scratch/jjyeung/b04shm bash -c 'cd /scratch/jjyeung/b04shm/b04/host2/b04_e2ehook && PYTHONPATH=/scratch/jjyeung/b04shm/b04/pyoverlay:. timeout 600 nice /scratch/jjyeung/envs/vllm/bin/python -B -m parity_kit.compare --new parity_kit/gpu_results/own_depth_p0/items.jsonl --out parity_kit/gpu_results/cmp_p0_51' 2>&1 | grep -v -i warn | tail -c 2500
/scratch/jjyeung/envs/vllm/bin/python -c "
import json,collections
rs=[json.loads(l) for l in open('$L/parity_kit/gpu_results/own_depth_p0/items.jsonl')]
print(collections.Counter(r['question_type'] for r in rs)); print('finish',collections.Counter(r['finish'] for r in rs)); s=[r['seconds'] for r in rs]; print('sec mean',sum(s)/len(s),'max',max(s))
print('calls',collections.Counter(json.dumps(r.get('calls',{}).get('calls') if isinstance(r.get('calls'),dict) else None) for r in rs).most_common(6))
"
