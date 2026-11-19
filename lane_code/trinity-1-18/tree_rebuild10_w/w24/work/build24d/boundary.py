"""CPU model/store/frame-host boundary; execute the unmodified kit helper."""
from pathlib import Path
import json,os,runpy,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';O=L/'work/build24/proofs/capacity'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import native24 as N
from student_pilot import r1_persisted as P,r1_rooms as Rooms,r1_direction_twins as Twins
from student_pilot.p3_provenance import load
import joblib as J
N.torch.set_num_threads(2)
synthetic=load(O/'TWIN_BOUNDARY.json')['pins']
Twins.ROWS=synthetic['rows']['sha256'];Twins.BINDING=synthetic['binding']['sha256'];Twins.ALIASES=synthetic['aliases']['sha256'];Rooms.STORE=synthetic['source_database']['sha256']
N.C.processor_for=N.processor
import student_pilot.decoupled_v_run as V
V.processor_for=N.processor
u=os.uname();os.uname=lambda:os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))
os.environ['STUDENT_R2_FRAME_HOST']='1'
os.environ['OMP_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
helper=sys.argv[1];sys.argv=sys.argv[1:]
if helper.endswith('/t.py'):sys.executable=str(D/'cpu_python')
if helper.endswith('/a.py') and sys.argv[-2].endswith('/p2'):
    # Reuse the stores produced by the first native pass; the reader still
    # authenticates every database and every twin. No database is copied.
    from copy import deepcopy
    cached=J.load(D/'go/p/q/c.json')
    from student_pilot.p3_provenance import pinned,file_pin
    def augment(cfg,output):
        receipt=J.load(pinned(cached['streams']['vqa']))
        assert receipt['source_receipt']==cfg['streams']['vqa']
        assert cfg['r1_training']['direction_twins']==cached['r1_training']['direction_twins']
        cfg=deepcopy(cfg);cfg['streams']['vqa']=cached['streams']['vqa']
        cfg['r1_training']['direction_augmented']=cached['r1_training']['direction_augmented']
        Twins.verify_augmented(cfg,receipt['database']);return cfg
    Twins.augment=augment
    build_stream=N.D.build_stream
    phase=next((D/'go/p/q/p').glob('prepare_*'))
    def retained(source,division,directory,stream,**kw):
        if stream not in ('vqa','pointing'):return build_stream(source,division,directory,stream,**kw)
        value=J.load(phase/stream/'receipt.json');pinned(value['database'])
        assert source==cached['streams'][stream]
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        J.write(directory/'receipt.json',value);return value
    N.D.build_stream=retained
if helper.endswith('/u.py'):
    # CPU gloo stands in for the GPU communication boundary. Keep native
    # collectives, with enough startup time for serial fixture-store checks.
    from datetime import timedelta
    init_group=N.C.dist.init_process_group;new_group=N.C.dist.new_group
    def cpu_init(*a,**kw):
        kw['timeout']=timedelta(seconds=600);return init_group(*a,**kw)
    def cpu_group(*a,**kw):
        kw['timeout']=timedelta(seconds=600);return new_group(*a,**kw)
    N.C.dist.init_process_group=cpu_init;N.C.dist.new_group=cpu_group
    # Observe the real optimizer and real training loop, without replacing either.
    original=N.C.run_steps;optimize=N.C.optimize_step;events=[]
    def run_steps(model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank=0,start_step=0,*a,**kw):
        record=dict(rank=rank,optimizer_state_entries_at_start=len(optimizer.state),start_step=start_step,events=events)
        J.write(D/'go'/('rank'+str(rank)+'.json'),record)
        result=original(model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank,start_step,*a,**kw)
        record.update(last_step=result['last_step'],optimizer_state_entries_at_end=len(optimizer.state),status=result['status'],events=events)
        J.write(D/'go'/('rank'+str(rank)+'.json'),record);return result
    def step(*a,**kw):
        result=optimize(*a,**kw);events.append(dict(step=a[6],info=result[0]));return result
    N.C.run_steps=run_steps;N.C.optimize_step=step
with P.scope(aliases):runpy.run_path(helper,run_name='__main__')
