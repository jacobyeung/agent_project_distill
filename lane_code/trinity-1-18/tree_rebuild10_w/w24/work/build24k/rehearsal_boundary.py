"""CPU model/store/frame-host boundary; execute the unmodified kit helper."""
from pathlib import Path
import json,os,runpy,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';O=L/'work/build24/proofs/capacity'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import native24 as N
from student_pilot import r1_persisted as P,r1_rooms as Rooms,r1_direction_twins as Twins
from student_pilot.p3_provenance import load
import joblib as J
N.torch.set_num_threads(2)
import tempfile
tempfile.tempdir=str(D/'rehearsal_k/tmp')
sys.path.insert(0,str(D))
from rehearsal_model import install, install_preparation
install(N.C)
install_preparation()
synthetic=load(O/'TWIN_BOUNDARY.json')['pins']
Twins.ROWS=synthetic['rows']['sha256'];Twins.BINDING=synthetic['binding']['sha256'];Twins.ALIASES=synthetic['aliases']['sha256'];Rooms.STORE=synthetic['source_database']['sha256']
N.C.processor_for=N.processor
import student_pilot.decoupled_v_run as V
V.processor_for=N.processor
u=os.uname();os.uname=lambda:os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))
os.environ['STUDENT_R2_FRAME_HOST']='1'
phase=os.environ.get('TK_REHEARSAL_PHASE','fresh');assert phase in ('fresh','budget','resume')
os.environ['S1_REHEARSAL_ATTEMPT']='b24k_'+phase
os.environ['OMP_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
helper=sys.argv[1];sys.argv=sys.argv[1:]
if helper.endswith('/t.py'):sys.executable=str(D/'rehearsal_cpu_python')
if helper.endswith('/a.py') and sys.argv[1]=='r':
    sys.path.insert(0,str(Path(helper).parent))
    import rg
    native_regenerate=rg.regenerate
    rg.regenerate=lambda cfg,root: native_regenerate(cfg,root,compare=False)
if helper.endswith('/u.py'):
    import resource,time,math
    # The batch driver's RSS monitor includes all four ranks and the copier.
    from datetime import timedelta
    init_group=N.C.dist.init_process_group;new_group=N.C.dist.new_group
    def cpu_init(*a,**kw):
        kw['timeout']=timedelta(seconds=600);return init_group(*a,**kw)
    def cpu_group(*a,**kw):
        kw['timeout']=timedelta(seconds=600);return new_group(*a,**kw)
    N.C.dist.init_process_group=cpu_init;N.C.dist.new_group=cpu_group
    from launch_r2 import persistence
    original=N.C.run_steps;optimize=N.C.optimize_step;native_recipe=N.C.recipe_for
    native_train=N.C.train;native_milestone=persistence.milestone
    events=[];states=[]
    def training(cfg,*a,**kw):
        print(json.dumps(dict(event='clock',rank=os.environ['RANK'],TK_JOB_START=os.environ['TK_JOB_START'],phase=phase)),flush=True)
        return native_train(cfg,resume_pin=None if phase=='fresh' else 'latest')
    def save(cfg,directory,kind,rank=0,distributed=True):
        native_milestone(cfg,directory,kind,rank,distributed)
        marker=Path(directory)/('complete.json' if kind=='checkpoint' else 'artifact.json')
        if rank==0:
            value=J.load(marker);states.append(dict(kind=kind,step=value['step'],path=str(marker),sha256=J.sha(marker),passed=True))
            J.write(D/'rehearsal_k'/('states_'+phase+'.json'),states)
    def run_steps(model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank=0,start_step=0,*a,**kw):
        # Change only loop scheduling. Config admission and export identity use
        # the authenticated fixture config with the production recipe.
        effective=native_recipe(cfg)
        effective.update(resume_every_seconds=1,milestones=[2],steps={'fresh':3,'budget':1000,'resume':5}[phase])
        N.C.recipe_for=lambda c:effective
        record=dict(phase=phase,rank=rank,start_step=start_step,optimizer_state_entries_at_start=len(optimizer.state),TK_JOB_START=os.environ['TK_JOB_START'],events=events,effective_recipe=effective)
        target=D/'rehearsal_k'/(phase+'_rank'+str(rank)+'.json');J.write(target,record)
        try:result=original(model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank,start_step,*a,**kw)
        finally:N.C.recipe_for=native_recipe
        record.update(last_step=result['last_step'],status=result['status'],stop_reason=result['stop_reason'],elapsed_seconds=result['elapsed_seconds'],events=events)
        J.write(target,record);return result
    def step(*a,**kw):
        result=optimize(*a,**kw)
        if phase=='fresh' and a[6]==2:time.sleep(1.05)
        events.append(dict(step=a[6],info=result[0]))
        return result
    N.C.train=training;N.C.run_steps=run_steps;N.C.optimize_step=step;persistence.milestone=save
with P.scope(aliases):runpy.run_path(helper,run_name='__main__')
