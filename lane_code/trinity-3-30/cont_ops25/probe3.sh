cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild && /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json
d=json.load(open('kit2/kit/rerun2/items544.json'))
it=d if isinstance(d,list) else d.get('items',d)
it=it if isinstance(it,list) else list(it.values())
out={}
for x in it:
    c=x.get('capture') or ''
    v=c.split('/')[-1]
    if v in "41069054 41291643 42899535 45663051 47332598 41159782 45261332 43828368 43649603 44358634".split():
        t=x.get('task',{}); out[v]=dict(src=t.get('source_frame_indices') or x.get('source_indices'), total=t.get('total_num_frames'), lb=t.get('total_num_frames_lower_bound'), native=t.get('native'))
print(json.dumps(out))
PY
