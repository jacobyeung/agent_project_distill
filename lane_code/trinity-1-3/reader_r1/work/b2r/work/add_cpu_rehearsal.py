from pathlib import Path
p=Path('out/tower_sequence.py');s=p.read_text()
a=s.index(" if config.get('measure_memory'):");b=s.index(' return result',a)
s=s[:a]+" if config.get('measure_memory'):\n  result[0]['full_reader']=full_reader_rehearsal(configs[0])\n"+s[b:]
insert='''
def full_reader_rehearsal(config):
 """Exercise staged RGBs and the real reader with deterministic CPU model stubs."""
 from contextlib import ExitStack
 from types import SimpleNamespace as NS
 from unittest.mock import patch
 import numpy as np
 import torch
 from PIL import Image
 from e2e_reader import parity,real
 from student_pilot import sam3_tower,carrier_c1_decode as decode,tower_read
 from h1eval.h10 import launch,parity_adapter
 from h1eval.items import load_manifest
 from evalpath import runtime
 from evalpath.run import score_item
 from orchard_h10.common import write,sha
 if config.get('device')!='cpu':raise ValueError('CPU rehearsal requires CPU')
 package=Path(config['package'])
 manifest=load_manifest(package/'items/room134.json')
 settings=json.loads(Path(config['settings']).read_text())
 expected=dict(stage1_select_rule='null_argmax',perception_memo='on',
   perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,
   types=['room_size_estimation'])
 if any(settings.get(k)!=v for k,v in expected.items()):raise ValueError('Rehearsal settings differ')
 # Never fabricate a restore or alter the staged settings in the allocated check.
 if not (Path(config['export'])/'RESTORE.json').is_file():raise ValueError('Restore is absent')
 root=Path(config['output'])/'metadata/full_reader'
 root.mkdir(parents=True,exist_ok=False)
 class Budget:
  def __init__(self,*a,**k):pass
  def __call__(self,*args):return args[-1]
  def receipt(self,*a):return {'cpu_stub':True}
 class Tokenizer:
  chunks=['<think>','</think><answer>21.52</answer>']
  eos_token_id=2
  def convert_tokens_to_ids(self,t):return 3 if t=='<tool_response>' else 4
  def encode(self,s,**kw):return [1000+x for x in s.encode()]
  def decode(self,ids,**kw):return ''.join(self.chunks[i-10] if 10<=i<12 else chr(i-1000) if i>=1000 else '' for i in ids)
 def logits(i):
  z=torch.full((1,1,1300),-100.);z[0,0,10+i if i<2 else 2]=100.
  return NS(logits=z,past_key_values=None)
 reports=[]
 for ordinal,name in enumerate(('dev-S1','R0-dev')):
  item=next(r for r in manifest['items'] if r['id'] in manifest['sets'][name])
  index=manifest['items'].index(item);journal=root/str(ordinal)
  args=launch.parser().parse_args(['--items',str(package/'items/room134.json'),
    '--export',config['export'],'--artifact-manifest',config['binding'],
    '--reader-root',str(package/'b'),'--out',str(journal),'--export-pin',config['export_pin'],
    '--settings',config['settings'],'--types','room_size_estimation','--arms','tower',
    '--modes','none','--device','cpu','--shard',f'{index}/{len(manifest["items"])}','--type-journals'])
  art=NS(manifest=dict(components={k:dict(files=[dict(rel=k+'/weights',
    sha256=hashlib.sha256(k.encode()).hexdigest(),bytes=1)]) for k in ('g3t','sam3')}),
    allowed=set(),env_roots=(),write_roots=(),code=set())
  art.verify=lambda:art
  art.files=lambda component:[Path(settings['sam3'][k]).resolve() for k in ('checkpoint_path','receipt_path')]+[Path('model.safetensors'),Path('config.json')]
  proc=NS(tokenizer=Tokenizer(),_routing_tokens={'ids':{}});model=NS();loads=[];seq=[0];seen=[]
  def load(*a,**k):
   if k.get('device')!='cpu':raise ValueError('Model stub requires CPU')
   loads.append(1);return model,proc,{'config':{},'export':{'frame_layout':'duplicate'}}
  def prefill(*a,**k):
   seq[0]=0
   heads=NS(pose9=np.tile([0.,0.,0.,0.,0.,0.,1.,1.,1.],(32,1)),gravity=np.array([0.,-1.,0.]),
     depth_map=torch.ones(32,1,1,1),depth_head=NS(query=lambda d,uv:torch.full(uv.shape[:2],3.)))
   return NS(heads=heads,native=NS(generation_config=NS(eos_token_id=2)),cap=10000,stream=None,output=logits(0))
  def consume(*a,**k):seq[0]+=1;return logits(seq[0]),None
  def prompt(processor,row,*a):
   si=row['student_input']
   if si['question']!=item['question'] or si['frame_indices']!=item['source_frame_indices']:
    raise ValueError('Prompt item binding differs')
   for f in si['frames']:
    digest=sha(f['path'])
    if digest!=f['sha256']:raise ValueError('Prompt frame SHA256 differs')
    with Image.open(f['path']) as im:
     im.load();seen.append(dict(path=f['path'],sha256=digest,size=list(im.size)))
   return dict(input_ids=torch.ones(1,1,dtype=torch.long),attention_mask=torch.ones(1,1,dtype=torch.long))
  original_audit=real.Audit
  with ExitStack() as stack:
   stubs=[patch.object(parity,'install',lambda *a:None),patch.object(parity,'Artifact',lambda *a,**k:art),
    patch.object(parity,'load_native',load),patch.object(parity,'install_hook',lambda m,h:h),
    patch.object(parity,'_head',lambda *a:NS()),patch.object(parity,'policy',lambda:NS(ThinkingBudget=Budget,DECODE_BUDGET=1)),
    patch.object(sam3_tower,'Sam3Tower',lambda *a:NS()),patch.object(runtime,'prompt_batch',prompt),
    patch.object(tower_read,'FrozenG3TTower',side_effect=AssertionError('Direct room stub must not invoke G3T')),
    patch.object(decode,'_prepare_decode',prefill),patch.object(decode,'consume_cache_tokens',consume),
    patch.object(real,'Audit',lambda a,**k:original_audit(a,enforce=False))]
   for stub in stubs:stack.enter_context(stub)
   result=launch.run_types(args,make_real=parity_adapter.make_capped_real)
  rows=launch.read_records(journal/'4/0/items.jsonl')
  if result['completed']!=1 or len(rows)!=1 or len(loads)!=1 or len(seen)!=32:
   raise ValueError('Full reader did not complete exactly one item')
  row=rows[0];output=row['output']
  if (row['id']!=item['id'] or row['complete'] is not True or row['type']!='room_size_estimation'
      or row['arm']!='tower' or row['mode']!='none' or output['finish']!='eos'
      or output['calls']['records']!=[] or output['tokens']!=[10,11,2]):
   raise ValueError('Full reader finished record differs')
  score=score_item(item,parity.decoded(output))
  if score['parse_failed'] or output['scores']['answer']!=score['score']:
   raise ValueError('Official score differs')
  environment=json.loads((journal/'4/0/environment.json').read_text())
  if any(environment['binding'].get(k)!=v for k,v in expected.items()):
   raise ValueError('Full reader type or settings binding differs')
  reports.append(dict(passed=True,set=name,item=item['id'],frames=seen,record=row,
    official_score=score,environment_binding=environment['binding']))
 proof=dict(passed=True,device='cpu',records=reports,
   stubbed=['artifact audit enforcement','weights and model forward','tokenizer','prompt tensor construction','decode budget policy'],
   real=['launch','mixed native mapping','frame SHA256 and PNG decode','ParityGenerator','generate_real','CallHook','decode loop','official scoring'])
 write(root/'FULL_READER.json',proof)
 return proof

'''
s=s.replace('\ndef run(config,end,',insert+'\ndef run(config,end,')
p.write_text(s)
p=Path('out/node_check.py');s=p.read_text();s=s.replace("    memory=json.loads(J.physical(root,cfg['logical']+'/r/metadata/MEMORY.json').read_text())", "    rehearsal=json.loads(J.physical(root,cfg['logical']+'/r/REHEARSAL.json').read_text())\n    full=validate_full_reader(rehearsal)\n    write(results/'FULL_READER.json',full)\n    memory=json.loads(J.physical(root,cfg['logical']+'/r/metadata/MEMORY.json').read_text())")
s=s.replace("dict(passed=True,memory=memory,plan=", "dict(passed=True,full_reader_passed=True,full_reader=full,memory=memory,plan=")
s=s.replace('\ndef main():', '''
def validate_full_reader(rehearsal):
    if len(rehearsal)!=1:raise ValueError('CPU read count differs')
    full=rehearsal[0]['full_reader']
    if full.get('passed') is not True or full.get('device')!='cpu':raise ValueError('Full reader failed')
    records=full.get('records',[])
    if [r['set'] for r in records]!=['dev-S1','R0-dev']:raise ValueError('Full reader sets differ')
    for r in records:
        row=r['record'];output=row['output']
        if (r.get('passed') is not True or row.get('complete') is not True or row['id']!=r['item']
            or row['type']!='room_size_estimation' or output['finish']!='eos'
            or len(r['frames'])!=32 or r['official_score']['parse_failed']
            or output['scores']['answer']!=r['official_score']['score']):
            raise ValueError('Full reader record failed')
    return full


def main():''')
p.write_text(s)
p=Path('out/tower_bootstrap.py');s=p.read_text().replace("if not (proof['passed'] is True and", "if not (proof['passed'] is True and proof.get('full_reader_passed') is True\n        and proof.get('full_reader',{}).get('passed') is True and")
p.write_text(s)
