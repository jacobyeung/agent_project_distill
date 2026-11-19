from pathlib import Path
import json,shutil,subprocess,os
from copy import deepcopy
L=Path(__file__).resolve().parents[2];B=L/'work/build21';O=B/'proofs/capacity'
COUNTS={'pose':16000,'vqa':32000,'routing':16000,'pointing':8000}
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
def guard(stage):
    subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
    current=size(L);capacity=size(O);start=json.loads((B/'STORAGE_START.json').read_text())['workspace']
    value=dict(stage=stage,workspace=current,starting=start,capacity=capacity,free=shutil.disk_usage('/scratch').free)
    O.mkdir(parents=True,exist_ok=True)
    with (O/'STORAGE.jsonl').open('a') as f:f.write(json.dumps(value)+'\n')
    if value['free']<85*1024**3 or current-start>3_500_000_000 or capacity>3_000_000_000:raise ValueError('CAPACITY_STORAGE_GUARD')
    print(json.dumps(value),flush=True)
def population(path,row,stream,check):
    check('source '+stream)
    count=COUNTS[stream]
    if path.exists():
        # Every source is deterministic and was produced by this fixture.
        with path.open() as f:actual=sum(1 for _ in f)
        if actual==count:return
    with path.open('w') as f:
        for i in range(count):
            value=dict(row,qid=stream+str(i));f.write(json.dumps(value,separators=(',',':'))+'\n')
    print('source',stream,count,path.stat().st_size,flush=True)
def pose_manifests(root,row,make):
    guard('pose sources')
    result=[]
    for group in range(8):
        directory=root/('pose_source'+str(group));manifest=directory/'MANIFEST.json'
        if manifest.exists():
            from student_pilot.p3_provenance import file_pin
            result.append(file_pin(manifest));continue
        rows=[dict(row,qid='pose'+str(group*2000+i)) for i in range(2000)]
        result.append(make(directory,rows,'pose','pose'+str(group)))
    from student_pilot.r1_mix import allocate
    card=json.loads((L/'work/build19/proofs/native/card.json').read_text())
    proof=allocate(card,dict(pose=16000,direction=32000,camera_displacement=16000,pointing=8000))
    (root/'CAPACITY.json').write_text(json.dumps(dict(source=str(L/'work/build19/proofs/native/card.json'),counts=COUNTS,allocation=proof,synthetic_only=True),indent=2))
    return result
