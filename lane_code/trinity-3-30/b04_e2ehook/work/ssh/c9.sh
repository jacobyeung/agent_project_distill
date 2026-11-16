python3 - <<'P'
import json,collections
d=json.load(open('/dev/shm/jjyeung/exports/m544/model.safetensors.index.json'))
k=list(d['weight_map']); c=collections.Counter('.'.join(x.split('.')[:2]) for x in k); print(len(k)); print(c.most_common(25))
print([x for x in k if 'head' in x and 'lm_head' not in x][:20])
P
cat /dev/shm/jjyeung/exports/m544/config.json | head -c 1500; echo
ls /scratch/jjyeung/orch_n30/trin_read /scratch/jjyeung/orch_n30/native_r2 /scratch/jjyeung/orch_n30/native_r3 2>&1 | head -40
