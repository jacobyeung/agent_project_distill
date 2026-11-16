# Reviewer copy of tests/cpu_supervisor.py: in the fileonly case the i.py relay delivers nothing (as when /proc is denied).
import importlib.util,json,os,signal,sys,tempfile
from pathlib import Path
H=Path(os.environ['H1_PACKET']);root=Path(sys.argv[1]);tempfile.tempdir=os.environ['TMPDIR']
sys.path.insert(0,str(root/'b'))
spec=importlib.util.spec_from_file_location('real_supervisor',H/'build/fx/b/i.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod.authorize=lambda *a:({'new_gpus':{'t':4}},dict(output=os.environ['CPU_RUN'],world_size=4,recipe=dict(world_size=4),stall_guard=dict(startup_seconds=180,idle_seconds=180,checkpoint_grace_seconds=60,poll_seconds=1)))
mod.launcher=lambda *a:[sys.executable,'-B','-m','torch.distributed.run','--standalone','--nnodes=1','--nproc-per-node=4',str(root/'b/w.py')]
if os.environ.get('CPU_CASE')=='fileonly':
    def relay(pid):
        Path(os.environ['CPU_RUN'],'relay_suppressed').write_text('1\n')
    mod.relay=relay
mod.main(*sys.argv[1:])
