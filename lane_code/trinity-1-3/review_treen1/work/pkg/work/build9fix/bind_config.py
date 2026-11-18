from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import file_pin,pinned
remove=dict(path='/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json',sha256='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411')
pinned(remove)
division=file_pin('/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json')
assert division['sha256'].startswith('0d28fdd4')
cfg=json.loads((B/'inputs/config.json').read_text())
cfg['remove_files']=[p for p in cfg['remove_files'] if p['path']!=remove['path']]+[remove]
cfg['scene_division']=division;cfg['extent_receipt']=file_pin(B/'inputs/extents.json')
def refresh(value):
    if isinstance(value,dict):
        if set(value)=={'path','sha256'}:
            p=Path(value['path'])
            if p.is_relative_to(L) and p.is_file():return file_pin(p)
        return {k:refresh(v) for k,v in value.items()}
    if isinstance(value,list):return [refresh(v) for v in value]
    return value
cfg=refresh(cfg)
(B/'inputs/config.json').write_text(json.dumps(cfg,indent=2)+'\n')
(B/'F6_BINDING.json').write_text(json.dumps(dict(remove=remove,division=division),indent=2)+'\n')
print(json.dumps(dict(remove=remove,division=division)))
