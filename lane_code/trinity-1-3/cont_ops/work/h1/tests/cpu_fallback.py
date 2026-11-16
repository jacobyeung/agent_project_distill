import copy,json,os,sys,tempfile,time
from contextlib import ExitStack
from pathlib import Path
H=Path(os.environ['H1_PACKET']);out=Path(os.environ['CPU_RUN']);tempfile.tempdir=os.environ['TMPDIR']
def guard(event,args):
 if event in ('os.remove','os.rmdir','shutil.rmtree'):raise RuntimeError('deletion refused')
sys.addaudithook(guard);sys.path.insert(0,str(H/'build/tree'))
import torch,torch.distributed as dist
from unittest.mock import patch
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from tests.test_carrier_c1 import fixture
from tests.test_carrier_c1_run import RunnerTests
from student_pilot.h1 import pose_targets
from student_pilot.h1_r0 import Reserve
production=json.loads((H/'build/fx/k'/ (json.loads((H/'build/fx/k/1.json').read_text())['0']+'.json')).read_text())
torch.set_num_threads(1)
m,b,t=fixture(16, training_mode="final");raw=dict(question_type='camera_displacement',gt_pose9=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*32,gt_up=[0.,-1.,0.])
p,pc=pose_targets({'routing':raw},b,production['h1']);v=m(b,p,stream='routing');v['loss'].backward()
assert torch.isfinite(v['loss']) and pc['supervised']==1
(out/'s2.json').write_text(json.dumps(dict(loss=float(v['loss'].detach()),pose_supervised=pc['supervised'],rooms=len(Reserve(production['h1']['r0_rooms']).rooms))))
model,batch,target=fixture(4);recipe=copy.deepcopy(model.recipe)
recipe.update(steps=1000,world_size=1,mix=['pose'],milestones=[100,200],resume_every_seconds=99999,wall_seconds=86400,stop_before_seconds=3600,export_at_stop=True)
model.recipe=recipe;optimizer=torch.optim.AdamW(parameter_groups(model,recipe),weight_decay=.01)
class Rows:
 h1=production['h1']
 def get(self,stream,index):return batch,target,{}
rows=Rows();cfg=dict(output=str(out),recipe=recipe,base_identity='fixture',trace_program_version='3.13',training_mode='final',h1=production['h1'],first_step_admission='all_rank_native_v1',checkpoint_disk_guard=dict(reserve_bytes=0))
bound=dict(world_size=1,fixture=True)
(out/'inputs').mkdir(exist_ok=True);(out/'inputs/fixture.json').write_text('{}\n');(out/'binding.json').write_text(json.dumps(bound)+'\n')
from student_pilot import fsdp_training
with RunnerTests().local_collectives(),patch.object(run,'recipe_for',return_value=recipe),patch.object(fsdp_training,'publication_state',side_effect=lambda m:m.state_dict()):
 report=run.run_steps(model,model,optimizer,rows,{'pose':8},out,cfg,bound,torch.device('cpu'),distributed=False)
assert report['status']=='H1_STOP' and report['last_step']==200 and report['stopped_for_resume'] is False
assert (out/'m100/artifact.json').is_file() and (out/'m200/artifact.json').is_file()
(out/'result.json').write_text(json.dumps(dict(status=report['status'],last_step=report['last_step'],stopped_for_resume=report['stopped_for_resume'],stop_reason=report['stop_reason'],lr_horizon=recipe['steps'],elapsed_seconds=report['elapsed_seconds'],scope='native tiny model and optimizer, real checkpoint/export; one rank with local collective stand-ins')))
