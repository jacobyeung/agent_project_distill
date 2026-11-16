"""Fresh-process tiny loader around the actual reviewed make_real interface."""
import json
import os
from pathlib import Path
import runpy
import sys
import time
from types import SimpleNamespace as NS
from unittest.mock import patch

K=Path(__file__).resolve().parents[1]
B=Path('/scratch/jjyeung/orch_n30/b04_e2ehook')
# runner passes the exact production Python/-m command after this test prefix.
argv=sys.argv[1:];assert argv[1:4]==['-B','-m','h1eval.h10.launch']
args=argv[4:]
from h1eval.h10.launch import reader_factory
reader_factory(B)
from e2e_reader import parity
import torch
from PIL import Image

image=Image.new('RGB',(4,4)); original=parity.bind_item
def bind(item,settings,**kw):
    value=original(item,settings,verify=False)
    value['frames']['native_frames']=[image]*len(value['frames']['native_frames'])
    return value

def load(*args,**kw):
    model=torch.nn.Linear(2,2).eval()
    processor=NS(tokenizer=NS(),_routing_tokens={'ids':{'move':7}})
    return model,processor,dict(config={},export={'frame_layout':'duplicate'})

def generate(self,item):
    if os.environ.get('B8_DELAY'):time.sleep(float(os.environ['B8_DELAY']))
    return dict(text='</think><answer>1.00 meters</answer>',finish='eos',calls={'records':[]},tokens=[1])

sys.argv=['h1eval.h10.launch',*args]
with patch.object(parity,'Artifact',return_value=NS(verify=lambda:NS())), \
     patch.object(parity,'load_native',side_effect=load), \
     patch.object(parity,'install_hook',side_effect=lambda m,h:h), \
     patch.object(parity,'CallHook',return_value=NS()), \
     patch.object(parity,'bind_item',side_effect=bind), \
     patch.object(parity,'score',return_value={'answer':0.}), \
     patch.object(parity,'policy',return_value=NS()), \
     patch.object(parity.ParityGenerator,'__call__',generate):
    runpy.run_module('h1eval.h10.launch',run_name='__main__')
