from pathlib import Path
import sys,json,os
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24');F=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m2c/tiny_routing_v3')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1'),str(L/'out/kit_qd/b')]
import native24 as N
N.C.processor_for=N.processor
from z import load,write
from i import refresh
from student_pilot.p3_provenance import file_pin,pinned
from launch_r1.entry import check_host_selection
import rg
root=Path('/tmp/qd/p/q');root.mkdir(parents=True)
cfg=load(F/'cfg.json')
pin=write(root.parent/'input.json',cfg)
refreshed=refresh(dict(config=pin,staged_pins=[pin]),root.parent/'refresh')
cfg=load(pinned(refreshed['config']))
if sys.argv[1]=='r':
 value=rg.regenerate(cfg,root,compare=False)
 write(F/'selected.json',value)
else:
 request=dict(routing_selection=file_pin(F/'selected.json'))
 host=dict(assertions={});check_host_selection(cfg,root,request,host)
 assert host['assertions']['routing_selection']
 write(F/'q_result.json',host)
