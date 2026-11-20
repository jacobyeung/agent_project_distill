"""CPU model/store/frame-host boundary; execute the unmodified kit helper."""
from pathlib import Path
import json,os,runpy,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k5 import L,D,R
from rehearsal_inputs_k5 import usage,plan_bytes,check_budget,frame_host,PLAN_LIMIT,DISK_LIMIT
O=L/'work/build24/proofs/capacity'
sys.path[:0]=[str(L/'work/build24'),str(R/'source'),str(L/'work/build21')]
os.environ['R2_TREE']=str(R/'source')
import torch
set_threads=torch.set_num_threads
torch.set_num_threads=lambda n:set_threads(min(n,1))
import native24 as N
from student_pilot import r1_persisted as P,r1_rooms as Rooms,r1_direction_twins as Twins
from student_pilot.p3_provenance import load
import joblib as J
N.torch.set_num_threads(2)
import tempfile
tempfile.tempdir=str(R/'tmp')
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
os.environ['S1_REHEARSAL_ATTEMPT']='b24k5_'+phase
os.environ['OMP_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
helper=sys.argv[1];sys.argv=sys.argv[1:]
if (R/'p2/plan.json').exists():
    frame_host(J.load(R/'p2/plan.json')['request']['frame_roots'][0])
if helper.endswith('/t.py'):sys.executable=str(D/'rehearsal_cpu_python_k5')
if helper.endswith('/a.py'):
    # Check the native plan before any byte copier runs. A polling guard alone
    # cannot bound a burst of filesystem writes between samples.
    sys.path.insert(0,str(Path(helper).parent))
    import pl
    import px
    native_resolver=px.resolver
    def fixture_resolver(kit,root,sources):
        # Supply only hash-verified fixture inputs; native lookup/checks remain intact.
        for pin in J.load(R/'FIXTURE_CLOSURE.json')['supplied']:
            p=Path(pin['path'])
            if not p.is_relative_to('/scratch/jjyeung/orch_n30'):
                raise ValueError('Fixture source outside scratch')
            from z import checked
            checked(p,pin['sha256'],pin['bytes'])
            sources[pin['sha256']]=str(p)
        return native_resolver(kit,root,sources)
    px.resolver=fixture_resolver
    native_plan=pl.plan_payload
    def bounded_plan(*args,**kwargs):
        request,paths,stage=native_plan(*args,**kwargs)
        plan=J.load(Path(args[2])/'plan.json')
        planned=plan_bytes(plan['entries']);current=usage(R)
        budget=dict(planned_bytes=planned,**current,plan_limit=PLAN_LIMIT,disk_limit=DISK_LIMIT)
        J.write(Path(args[2])/'STAGING_BUDGET.json',budget)
        J.write(R/'STAGING_BUDGET.json',budget)
        check_budget(planned,max(current['new_bytes'],current['allocated_bytes']))
        # The host boundary maps the fixture's sole logical RGB path to exactly
        # the native planner's staged frame directory.
        frame_host(request['frame_roots'][0])
        layout=J.load(R/'INPUT_LAYOUT.json')
        resolved=args[1]
        overwritten=set(resolved['small_files'])
        overwritten.update(x['sha256'] for x in resolved.get('external_metadata',[]))
        overwritten.update(x['sha256'] for x in J.load(Path(args[0])/'k/p.json')['uploads'])
        def linked_stage(received,directory):
            directory=Path(directory)
            if received!=plan['entries']:raise ValueError('R1_STAGING_PLAN_DIFFERS')
            (directory/'u').mkdir(exist_ok=True)
            for h,item in layout['stores'].items():
                if h in overwritten:raise ValueError('Fixture store would be overwritten by native copier')
                entry=received.get('u/'+h)
                if entry is None or entry['sha256']!=h or entry['bytes']!=item['bytes']:
                    raise ValueError('Fixture store differs from native staging plan')
                # Both names lie in this namespace's writable mount. Native
                # staging authenticates the existing file and never rewrites it.
                cached=directory.parents[1]/'inputs/stores'/h
                os.link(cached,directory/'u'/h)
            return stage(received,directory)
        linked_stage.close=stage.close
        return request,paths,linked_stage
    pl.plan_payload=bounded_plan
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
            J.write(R/('states_'+phase+'.json'),states)
    def run_steps(model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank=0,start_step=0,*a,**kw):
        # Change only loop scheduling. Config admission and export identity use
        # the authenticated fixture config with the production recipe.
        effective=native_recipe(cfg)
        effective.update(resume_every_seconds=1,milestones=[2],steps={'fresh':3,'budget':1000,'resume':5}[phase])
        N.C.recipe_for=lambda c:effective
        record=dict(phase=phase,rank=rank,start_step=start_step,optimizer_state_entries_at_start=len(optimizer.state),resume_pin=None if phase=='fresh' else 'latest',TK_JOB_START=os.environ['TK_JOB_START'],events=events,effective_recipe=effective)
        target=R/(phase+'_rank'+str(rank)+'.json');J.write(target,record)
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
