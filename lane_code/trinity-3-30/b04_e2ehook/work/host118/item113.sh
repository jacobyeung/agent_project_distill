R=/dev/shm/jjyeung/b04/host/b04_e2ehook/parity_kit/host_results/cpu_first_c
/scratch/jjyeung/envs/vllm/bin/python -c "
import json
for l in open('$R/items.jsonl'):
    r=json.loads(l); print({k:(v if len(json.dumps(v))<300 else json.dumps(v)[:300]) for k,v in r.items() if k not in ('tokens','text','audit')})
    print('TEXT', r.get('text','')[-700:])
"
