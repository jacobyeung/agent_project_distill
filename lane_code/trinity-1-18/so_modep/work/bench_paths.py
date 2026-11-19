from pathlib import Path
import os,sys,time,json,cProfile,pstats,sqlite3
sys.path.insert(0,str(Path(__file__).resolve().parent/'tree'))
import torch
torch.set_num_threads(8)
from student_pilot import orchard_paths as P
from student_pilot.s1_admission import FrameAudit
from student_pilot.p3_provenance import file_pin
root=Path(__file__).resolve().parent/'profile_fixture'
P.PROJECT=root
frames=root/'data2root/deep/native/pinned/frames'
os.environ['STUDENT_ORCHARD']='1';os.environ['STUDENT_FRAME_ROOT_MAP']=json.dumps({'/data2':str(root/'data2root')})
pins=[dict(path='/data2/deep/native/pinned/frames/'+f'{i:06}.bin',sha256=file_pin(frames/f'{i:06}.bin')['sha256']) for i in range(1024)]
results=[]
for enabled in ('0','1','1','0'):
    out=root/('paths_'+enabled+'_'+str(len(results)));out.mkdir()
    os.environ['S1_PREP_FAST_PATHS']=enabled
    a=FrameAudit(out,[frames],sample_size=8)
    start=time.perf_counter()
    for i in range(1024):a.keep(dict(student_input=dict(frames=[pins[(i*17+j)%1024] for j in range(32)])),'source'+str(i%4))
    a.finish();a.close()
    seconds=time.perf_counter()-start
    result=dict(enabled=enabled,rows=1024,references=32768,seconds=seconds,refs_per_second=32768/seconds,database_sha256=file_pin(out/'frame_inventory.sqlite')['sha256'])
    results.append(result);print(json.dumps(result),flush=True)
assert len({r['database_sha256'] for r in results})==1
(root/'path_results.json').write_text(json.dumps(results,indent=2)+'\n')
