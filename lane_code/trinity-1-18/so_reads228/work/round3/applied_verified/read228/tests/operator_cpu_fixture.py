"""CPU process-boundary fixture: real imports/operator/summarize, fake GPU worker only."""
import os
from pathlib import Path
import shutil
import sys
import types
from unittest.mock import patch
kit=Path(sys.argv[1]);sys.path.insert(0,str(kit))
import operator228 as operator
import common228 as C
import torch
torch.set_num_threads(8)
real_popen=operator.subprocess.Popen

class Sampler:
    def __init__(self,*args):self.process=types.SimpleNamespace(poll=lambda:None)
    def __enter__(self):return self
    def __exit__(self,*args):pass

class Worker:
    returncode=0
    def __init__(self,command,**kwargs):
        assert '/usr/bin/bwrap' not in command
        assert kwargs['start_new_session'] is True
        assert kwargs['env']['CUDA_VISIBLE_DEVICES'].startswith('GPU-')
        self.worker=operator.read(command[-2])['worker']
        journal=Path(self.worker['config']['output'])/'metadata/journals/3/0'
        journal.mkdir(parents=True,exist_ok=True)
        for name in ('items.jsonl','environment.json'):
            shutil.copyfile(kit/'reference/metadata/reads/0/metadata/journals/3/0'/name,journal/name)
    def poll(self):return 0

def spawn(command,**kwargs):
    if str(kit/'worker228.py') in command:return Worker(command,**kwargs)
    return real_popen(command,**kwargs)

with patch.object(operator,'target_host',return_value='trinity-2-28'),\
     patch.object(operator,'Sampler',Sampler),patch.object(operator.subprocess,'Popen',side_effect=spawn),\
     patch.object(operator,'policy_check',side_effect=lambda **kw:C.policy_check(paths={name:kit/'evidence/q'/(name+'.sh') for name in ('vnice','terminator')})):
    raise SystemExit(operator.main(sys.argv[2:]))
