"""Prepare the single external rehearsal entrypoint and its bounded helpers."""
from pathlib import Path
import json
import sys

L=Path(__file__).resolve().parents[2];D=L/'work/build24f'
sys.path.insert(0,str(L/'work/build24'))
import joblib as J

# Keep the proven tiny-model and retained-store boundaries. The native trainer,
# admission, first-step report, checkpoint, export and persistence stay intact.
s=(L/'work/build24e/boundary.py').read_text().replace("D=L/'work/build24e'","D=L/'work/build24f'")
s=s.replace("os.environ['S1_REHEARSAL_ATTEMPT']='b24d_go'", "phase=os.environ.get('TK_REHEARSAL_PHASE','fresh');assert phase in ('fresh','budget','resume')\nos.environ['S1_REHEARSAL_ATTEMPT']='b24f_'+phase")
s=s.replace("sys.executable=str(D/'cpu_python')","sys.executable=str(D/'cpu_python')")
s=s.replace("if stream not in ('vqa','pointing'):return build_stream(source,division,directory,stream,**kw)", "# All four synthetic stores were produced by the retained native fixture.\n        assert stream in ('vqa','pointing','pose','routing')")
start=s.index("if helper.endswith('/u.py'):")
end=s.index("with P.scope(aliases):runpy.run_path",start)
s=s[:start]+'''if helper.endswith('/u.py'):
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
            J.write(D/'rehearsal'/('states_'+phase+'.json'),states)
    def run_steps(model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank=0,start_step=0,*a,**kw):
        # Change only loop scheduling. Config admission and export identity use
        # the authenticated fixture config with the production recipe.
        effective=native_recipe(cfg)
        effective.update(resume_every_seconds=1,milestones=[2],steps={'fresh':3,'budget':1000,'resume':5}[phase])
        N.C.recipe_for=lambda c:effective
        record=dict(phase=phase,rank=rank,start_step=start_step,optimizer_state_entries_at_start=len(optimizer.state),TK_JOB_START=os.environ['TK_JOB_START'],events=events,effective_recipe=effective)
        target=D/'rehearsal'/(phase+'_rank'+str(rank)+'.json');J.write(target,record)
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
''' + s[end:]
(D/'boundary.py').write_text(s)
s=(L/'work/build24e/cpu_python').read_text().replace("str(D/'boundary.py')","str(D/'boundary.py')")
(D/'cpu_python').write_text(s);(D/'cpu_python').chmod(0o755)
s=(L/'work/build24e/fixture_gates.py').read_text().replace("D=L/'work/build24e'","D=L/'work/build24f'")
s=s.replace("os.environ['S1_REHEARSAL_ATTEMPT']='b24d_go'","os.environ['S1_REHEARSAL_ATTEMPT']='b24f_fresh'")
(D/'fixture_gates.py').write_text(s)
# Reuse only synthetic byte stores; every retained source must match its native pin.
J.write(D/'REHEARSAL_OVERRIDES.json',dict(
 production_config_edited=False,smoke_steps=None,world_size=4,backend='gloo',
 config_fields={'output':'/tmp/q_22c714e1/train','r1_training.stop_after_step':6,'checkpoint_disk_guard.reserve_bytes':0,
                'code':'new tree seal','preparation/admission/authorization/host_receipt/review':'native fixture pins, never production approval'},
 loop_only_fields={'recipe.resume_every_seconds':1,'recipe.milestones':[2],
                   'recipe.steps':{'fresh':3,'budget':1000,'resume':5}},
 environment={'TK_JOB_START':'fresh/resume: batch-driver epoch; budget: epoch minus 90000',
              'S1_CPU_REHEARSAL':'1','S1_REHEARSAL_ATTEMPT':'b24f_<phase>','CUDA_VISIBLE_DEVICES':'',
              'OMP_NUM_THREADS':8,'torch_threads_per_rank':2},
 timing={'fresh_step_2_delay_seconds':1.05,'purpose':'exercise native elapsed-time checkpoint predicate'},
 copier={'target':'rehearsal/target','sessions':'local empty fixture map','writer':'local byte-part stub',
         'm2_object':'same fixed object as production m100; stub only'},
 stand_ins=['Tiny native model and synthetic RGB/labels; retained native prepared stores',
            'CPU/gloo and fixture frame host','Fixture-only host/review receipts','Local GCS transport'],
 expected={'fresh':[0,3],'budget':[3,4],'resume':[4,5],'milestone_export':2,'timed_checkpoint':2,'budget_stop_export':4}))
print('Rehearsal sources prepared; distributed execution is intentionally external.')
