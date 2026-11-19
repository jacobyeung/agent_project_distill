"""Private dispatch. Only this numeric entry and its numeric config reach argv."""
import json
from pathlib import Path
import sys

cfg=json.loads(Path(sys.argv[1]).read_text())
p=Path(cfg['package'])
sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
from orchard_h10.common import install_process_guard
install_process_guard(Path(sys.argv[1]).resolve().parent)
action=cfg['action']
if action==0:
    from orchard_h10.prepare import run
    run(cfg['config'],cfg['inputs'])
elif action==1:
    import os
    from orchard_h10.runner import run
    result=run(cfg['config'],os.environ['CUDA_VISIBLE_DEVICES'].split(','),cfg['end'],prefix=cfg['config']['prefix'])
    raise SystemExit(1 if result['failure'] else 0)
elif action==2:
    from orchard_h10.runner import worker_args
    from h1eval.h10.launch import main
    raise SystemExit(main(worker_args(cfg)))
else:raise ValueError('Invalid dispatch')
