from pathlib import Path
import json,sys,hashlib
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/build13'
(L/'work/tmp').mkdir(exist_ok=True)
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,write,file_pin,pinned
def write(p,value):p.write_text(json.dumps(value,indent=2))
I=B/'inputs';I.mkdir(exist_ok=True)
old=L/'work/n1fix2/inputs';remote=Path('/scratch/jjyeung/orch_n30/r1_pkt/work/derive_7fh23bg8/b/k')
cfg=load(old/'config.json')
def local(pin):
    candidates=[old/Path(pin['path']).name,remote/Path(pin['path']).name]
    prefix='/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/'
    if pin['path'].startswith(prefix): candidates.insert(0,L/pin['path'][len(prefix):])
    for p in candidates:
        if p.is_file() and file_pin(p)['sha256']==pin['sha256']:
            return {**pin,'path':str(p)}
    raise ValueError('Missing authorized local pin '+str(pin))
for key in ('exclusions','report_exclusions','dev_scene_exclusions','benchmark_scene_exclusions','exclude_qids','scene_division','extent_receipt'):
    if cfg.get(key): cfg[key]=local(cfg[key])
cfg['remove_files']=[local(p) for p in cfg['remove_files']]
for key in ('mix','row_sources','registry','store_parameter'):
    cfg['r1_training'][key]=local(cfg['r1_training'][key])
cfg['streams']['vqa']=local(cfg['streams']['vqa'])
write(I/'config.json',cfg)
print(json.dumps(dict(config=file_pin(I/'config.json'),vqa=load(pinned(cfg['streams']['vqa'])))))
