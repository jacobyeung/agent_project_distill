from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];N=L.parent;B=L/'work/build12'
roots=['work/design/b04_inputs/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a',
 'work/design/b04_inputs/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/scale/work/run1',
 'work/design/b04_inputs/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso',
 'work/design/b04_inputs/scratch/jjyeung/k1/run_tower_sam_2/3912542710353e09']
records=[]
for rel in roots:
    src=N/rel;dst=L/rel;dst.mkdir(parents=True,exist_ok=True)
    for p in src.iterdir():
        if not p.is_file():continue
        if p.name not in ('scale_head.json','scale_head.safetensors','selector_head.json','selector_head.safetensors','tower.npz','PHASE_COMPLETE.json','candidates.json') and 'snapshots' not in p.parts:continue
        if 'snapshots' in p.parts and p.suffix not in ('.json','.txt','.jinja'):continue
        q=dst/p.name
        if not q.exists():q.symlink_to(p)
        records.append(dict(local=str(q),source=str(p),bytes=p.stat().st_size))
p=L/'work/build10/launch_b04_local10.py';p.write_text(p.read_text().replace("L.parent/'work/design", "L/'work/design"))
(B/'B04_READONLY_INPUTS.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(files=len(records))))
