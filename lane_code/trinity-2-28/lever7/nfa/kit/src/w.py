"""Private dispatch. Only this numeric entry and its numeric config reach argv.
Read 1 takes each item list in reverse; read 0 keeps it."""
import json
from pathlib import Path
import sys

cfg=json.loads(Path(sys.argv[1]).read_text())
p=Path(cfg['package'])
sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
from orchard_h10.common import install_process_guard
install_process_guard(Path(sys.argv[1]).resolve().parent)
if cfg['action']!=2 or cfg['config']['q'] not in (0,1):raise ValueError('Invalid dispatch')
from orchard_h10.runner import worker_args
from h1eval.h10 import launch
if cfg['config']['q']==1:
    kept=launch.selected
    def selected(items, value):
        return kept(items, value)[::-1]
    launch.selected=selected
raise SystemExit(launch.main(worker_args(cfg)))
