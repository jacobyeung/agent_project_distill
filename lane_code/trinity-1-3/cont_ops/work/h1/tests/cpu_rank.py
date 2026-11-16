import copy,json,os,signal,sys,tempfile,time
from pathlib import Path
H=Path(os.environ['H1_PACKET']);tempfile.tempdir=os.environ['TMPDIR']
def guard(event,args):
 if event in ('os.remove','os.rmdir','shutil.rmtree'):raise RuntimeError('deletion refused')
sys.addaudithook(guard)
sys.path.insert(0,str(H/'build/tree'))
import torch,torch.distributed as dist
from unittest.mock import patch
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from tests.test_carrier_c1 import fixture
from student_pilot.h1 import pose_targets
from student_pilot.h1_r0 import Reserve
rank=int(os.environ['LOCAL_RANK']);torch.set_num_threads(1)
dist.init_process_group('gloo')
out=Path(os.environ['CPU_RUN']);mode=os.environ['CPU_CASE']
try:
 model,batch,target=fixture(16, training_mode="final")
 production=json.loads((H/'build/fx/k'/ (json.loads((H/'build/fx/k/1.json').read_text())['0']+'.json')).read_text())
 reserve=Reserve(production['h1']['r0_rooms']);assert len(reserve.rooms)==372
 raw=dict(question_type='camera_displacement',gt_pose9=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*32,gt_up=[0.,-1.,0.])
 pose,pc=pose_targets({'routing':raw},batch,production['h1']);assert pc['supervised']==1
 # Exercise the H1 S2 branch in the native model with all 32 frame carriers.
 value=model(batch,pose,stream='routing');assert torch.isfinite(value['loss']);value['loss'].backward();model.zero_grad(set_to_none=True)
 (out/f'first_batch_rank{rank}.json').write_text(json.dumps(dict(rank=rank,loss=float(value['loss'].detach()),pose_supervised=pc['supervised'],r0_rooms=len(reserve.rooms),model='native_tiny',production_admission=False)))
 # Reduced CPU batches retain H1's real loop, stop logic, 1000-step LR horizon and 100/200 exports.
 model,batch,target=fixture(4)
 recipe=copy.deepcopy(model.recipe);recipe.update(steps=1000,world_size=4,mix=['pose'],milestones=[100,200],resume_every_seconds=99999,wall_seconds=86400,stop_before_seconds=3600,export_at_stop=True)
 model.recipe=recipe
 wrapped=run.wrap_model(model,torch.device('cpu'),mixed_precision=False)
 optimizer=torch.optim.AdamW(parameter_groups(wrapped,recipe),weight_decay=.01)
 class Rows:
  h1=production['h1']
  def get(self,stream,index):return batch,target,{}
 rows=Rows();cfg=dict(output=str(out),recipe=recipe,base_identity='fixture',trace_program_version='3.13',training_mode='final',h1=production['h1'])
 bound=dict(world_size=4,fixture=True)
 if rank==0:
  (out/'inputs').mkdir(exist_ok=True);(out/'inputs/fixture.json').write_text('{}\n');(out/'binding.json').write_text(json.dumps(bound)+'\n')
 dist.barrier();stop=[False]
 signal.signal(signal.SIGUSR1,lambda *_:stop.__setitem__(0,True))
 native=run.optimize_step
 def step(*args,**kwargs):
  result=native(*args,**kwargs)
  if mode=='signal' and args[7]==3:
   (out/f'ready{rank}').write_text('3\n')
   end=time.monotonic()+60
   while not (out/'release').exists():
    if time.monotonic()>end:raise RuntimeError('parent did not release step')
    time.sleep(.05)
  return result
 with patch.object(run,'recipe_for',return_value=recipe),patch.object(run,'optimize_step',side_effect=step):
  report=run.run_steps(model,wrapped,optimizer,rows,{'pose':8},out,cfg,bound,torch.device('cpu'),rank=rank,stop=stop,distributed=True)
 (out/f'rank{rank}.json').write_text(json.dumps(dict(last_step=report['last_step'],status=report['status'],reason=report['stop_reason'],stopped_for_resume=report['stopped_for_resume'],received_signal=stop[0])))
 assert report['last_step']==(3 if mode=='signal' else 200),report['last_step']
finally:dist.destroy_process_group()
