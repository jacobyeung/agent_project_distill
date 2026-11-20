import json,sys,importlib.util
from pathlib import Path
from unittest.mock import patch
tree,helper,cfgpath,samples,output=sys.argv[1:]
sys.path.insert(0,tree)
from student_pilot import carrier_c1_run as run
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
spec=importlib.util.spec_from_file_location('pc',helper);pc=importlib.util.module_from_spec(spec);spec.loader.exec_module(pc)
class Tokenizer:
 eos_token='<|im_end|>';eos_token_id=1
 def __init__(self):self.added={}
 def encode(self,text,**kwargs):return [ord(c)+10 for c in text]
 def get_vocab(self):return self.added.copy()
 def add_tokens(self,values):
  for v in values:self.added[str(v)]=1000+len(self.added)
 def convert_tokens_to_ids(self,v):return self.added[v]
class Processor:
 def __init__(self):self.tokenizer=Tokenizer()
 def apply_chat_template(self,messages,tokenize=False,add_generation_prompt=False):
  prompt='user\n'+messages[0]['content'][1]['text']+'\nassistant\n'
  return prompt if add_generation_prompt else prompt+messages[-1]['content']+self.tokenizer.eos_token+'\n'
cfg=json.loads(Path(cfgpath).read_bytes())
with patch.object(run,'processor_for',return_value=Processor()),patch.object(run.rehearsal,'fixture_manifest',return_value={}):
 processor=run.processor_for_receipt({'root':'fixture'},cfg)
value=dict(tree_sha256=digest(inventory(tree)),rows=pc.evaluate(processor,cfg,json.loads(Path(samples).read_bytes())))
Path(output).write_text(json.dumps(value))
