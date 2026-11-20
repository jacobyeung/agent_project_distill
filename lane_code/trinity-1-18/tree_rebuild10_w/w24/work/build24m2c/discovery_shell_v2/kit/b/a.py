from pathlib import Path
import sys,os,json
sys.path[:0]=[str(Path(__file__).resolve().parent),'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1']
import z
root=Path(sys.argv[2]);assert not root.exists();root.mkdir(parents=True)
mode=sys.argv[1];F=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m2c/discovery_shell_v2')
(root/'s').symlink_to('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1',target_is_directory=True)
if mode=='r':
 z.write(root/'routing_selection.json',z.load(F/'selected.json'))
 for name in ('receipt.json','materialization.json'):
  source=F.parent/'tiny_routing_v3/r/p/q/selection'/name
  destination=root/'q/selection'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(source.read_bytes())
else:
 from pl import selection_pin
 pin,source=selection_pin(Path(__file__).resolve().parents[1],root.parent/'routing_selection.json')
 assert z.load(source)==z.load(F/'selected.json')
 cfg=z.load(F/'prepared.json')
 from student_pilot.carrier_c1_run import identity
 from launch_r1.entry import ASSERTIONS
 host=z.write(root/'q/host.json',dict(status='PASS',config_identity=identity(cfg),assertions=dict.fromkeys(ASSERTIONS,True),loader_audit=dict(complete=True),stager='hook',staging_plan_sha256='1'*64,routing_selection=pin,regenerated_sha256=z.load(source)['regenerated_sha256'],routing_substituted=False))
 config=z.write(root/'prepared.json',cfg)
 z.write(root/'q/RESULT.json',dict(status='ADMIT',config=config,host_receipt=host,init_milestone=400))
print('fixture boundary '+mode,flush=True)
