from pathlib import Path
import sys, os, json, time, cProfile, pstats, hashlib, sqlite3, statistics
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parent/'tree'))
import torch
torch.set_num_threads(8)
from student_pilot.s1_admission import FrameAudit
from student_pilot import orchard_paths as paths
from student_pilot.common import binding
from student_pilot.p3_provenance import file_pin
root=Path(__file__).resolve().parent/'profile_fixture'
root.mkdir(exist_ok=True)
paths.PROJECT=root
frames=root/'data2root/deep/native/pinned/frames'
frames.mkdir(parents=True,exist_ok=True)
os.environ['STUDENT_ORCHARD']='1'
os.environ['STUDENT_FRAME_ROOT_MAP']=json.dumps({'/data2':str(root/'data2root')})
pins=[]
for i in range(1024):
    p=frames/f'{i:06}.bin';p.write_bytes(hashlib.sha256(str(i).encode()).digest()*8)
    pins.append(dict(path='/data2/deep/native/pinned/frames/'+p.name,sha256=file_pin(p)['sha256']))
row=dict(student_input=dict(frames=pins[:32]))
output=root/'audit';output.mkdir(exist_ok=False)
a=FrameAudit(output,[frames],sample_size=8)
pr=cProfile.Profile();start=time.perf_counter();pr.enable()
for i in range(2048):
    row['student_input']['frames']=[pins[(i*17+j)%len(pins)] for j in range(32)]
    a.keep(row,'source'+str(i%4))
r=a.finish();a.close();pr.disable()
result=dict(fixture=True,rows=2048,references=65536,unique=1024,bytes_per_file=256,seconds=time.perf_counter()-start)
pr.dump_stats(str(root/'audit.prof'))
with (root/'audit_profile.txt').open('w') as f:pstats.Stats(pr,stream=f).sort_stats('cumtime').print_stats(35)
print(json.dumps(result),flush=True)
(root/'result.json').write_text(json.dumps(result,indent=2)+'\n')

def resolve(pin):
    p=paths.resolve_read(pin['path']).resolve()
    assert p.is_relative_to(frames) and p.is_file()
    return str(p)
for workers in (0,4,8):
    start=time.perf_counter()
    pool=ThreadPoolExecutor(max_workers=workers) if workers else None
    for i in range(128):
        chunk=pins[i:i+32]
        values=list(pool.map(resolve,chunk)) if pool else [resolve(p) for p in chunk]
    if pool:pool.shutdown()
    print(json.dumps(dict(fixture=True,kind='resolve',workers=workers,refs=128*32,seconds=time.perf_counter()-start)),flush=True)
for workers in (0,4,8):
    start=time.perf_counter();pool=ThreadPoolExecutor(max_workers=workers) if workers else None
    for i in range(64):
        chunk=pins[i:i+32]
        values=list(pool.map(lambda p:binding(p['path'],p['sha256']),chunk)) if pool else [binding(p['path'],p['sha256']) for p in chunk]
    if pool:pool.shutdown()
    print(json.dumps(dict(fixture=True,kind='hash256',workers=workers,refs=64*32,seconds=time.perf_counter()-start)),flush=True)
