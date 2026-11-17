"""Real launch -> capped parity -> generate_real, with frozen modules stubbed on CPU."""
import hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from contextlib import ExitStack
from types import SimpleNamespace as NS
from unittest.mock import patch
import test_memo as F
W=F.W;P=F.P;O=W/'out';torch=F.torch;np=F.np;M=F.M
from e2e_reader import parity,real
from student_pilot import sam3_tower
from h1eval.h10 import launch,parity_adapter
from h1eval.items import load_manifest,digest,canonical
from orchard_h10.common import write
from evalpath import runtime

class Budget:
 def __init__(self,*a,**k):pass
 def __call__(self,*args):return args[-1]
 def receipt(self,*a):return {'fixture':True}

class Multi(unittest.TestCase):
 def test_real_multitype_off_on_verify(self):
  manifest=load_manifest(P/'items/devs1_routed.json');order=['object_abs_distance','camera_displacement','camera_rotation','camera_movement_direction','room_size_estimation']
  items=[];captures={}
  for kind in order:
   subset=[i for i in manifest['items'] if i['question_type']==kind][:4 if kind==order[0] else 2]
   for j,item in enumerate(subset):captures[item['id']]=j%2
   items+=subset
  items=canonical(items);manifest.update(items=items,count=len(items),item_set_sha256=digest(items),r0_check={**manifest['r0_check'],'checked':len(items),'found':0})
  tasks={r['id']:dict(r,room=r['room_key'],answer=r['ground_truth']) for r in items}
  reports={};baseline=None
  for mode in ('off','on','verify'):
   M._sessions.clear();M._disabled=False;F.G3T.calls=0
   root=Path(tempfile.mkdtemp(prefix='multi_',dir=W/'work/tmp'));(root/'e').mkdir();write(root/'e/RESTORE.json',{})
   write(root/'items.json',manifest);write(root/'b.json',dict(root=str(root),name='fixture',sha256='a'*64))
   ids=[r['id'] for r in items if r['question_type']==order[0]] if mode=='verify' else []
   settings=dict(export_dir=str(root/'e'),artifact_manifest=str(root/'b.json'),stage1_select_rule='null_argmax',perception_memo_modules=['g3t'],perception_memo=mode,perception_memo_verify_ids=ids,
    arm='own_depth',frames_json={'captures':{}},dense_manifest={'captures':{}},sam3={'checkpoint_path':str(root/'s'),'receipt_path':str(root/'s')},selector_head='fixture')
   write(root/'s.json',settings)
   args=launch.parser().parse_args(['--items',str(root/'items.json'),'--export',str(root/'e'),'--artifact-manifest',str(root/'b.json'),'--reader-root',str(P/'b'),'--out',str(root/'journal'),'--export-pin',str(O/'export_544.json'),'--settings',str(root/'s.json'),'--types',','.join(order),'--arms','tower','--modes','none','--device','cpu','--type-journals'])
   sam=F.Sam();art=F.artifact();art.verify=lambda:art;art.files=lambda component:[root/'s',Path('model.safetensors'),Path('config.json')]
   tok=F.Tokenizer();proc=NS(tokenizer=tok,_routing_tokens={'ids':{'move':11,'ground':12,'gap':14}});model=NS();loads=[];seq=[0]
   head=NS(with_null=lambda x,*a:torch.cat((torch.arange(len(x),dtype=torch.float64)+1,torch.tensor([-10.]))))
   def load(*a,**k):loads.append(1);return model,proc,{'config':{},'export':{'frame_layout':'duplicate'}}
   def prefill(*a,**k):
    seq[0]=0;heads=NS(pose9=np.tile([0.,0.,0.,0.,0.,0.,1.,1.,1.],(32,1)),gravity=np.array([0.,-1.,0.]),depth_map=torch.ones(32,1,1,1),depth_head=NS(query=lambda d,uv:torch.full(uv.shape[:2],3.)))
    return NS(heads=heads,native=NS(generation_config=NS(eos_token_id=2)),cap=10000,stream=None,output=F.logits(0))
   def consume(*a,**k):seq[0]+=1;return F.logits(seq[0]),None
   original_audit=real.Audit
   with ExitStack() as stack:
    patches=[patch.object(parity_adapter,'map_items',return_value=(tasks,{'sha256':'a'*64})),patch.object(parity,'install',lambda *a:None),patch.object(parity,'Artifact',lambda *a,**k:art),patch.object(parity,'load_native',load),patch.object(parity,'install_hook',lambda m,h:h),patch.object(parity,'_head',lambda *a:head),patch.object(parity,'policy',lambda:NS(ThinkingBudget=Budget,DECODE_BUDGET=1)),patch.object(sam3_tower,'Sam3Tower',lambda *a:sam),patch.object(parity,'bind_item',lambda item,*a,**k:dict(id=item['id'],row={'question_type':item['question_type']},frames=F.frames(captures[item['id']]))),patch.object(runtime,'prompt_batch',lambda *a:dict(input_ids=torch.ones(1,1,dtype=torch.long),attention_mask=torch.ones(1,1,dtype=torch.long))),patch.object(F.tower_read,'FrozenG3TTower',F.G3T),patch.object(F.decode,'_prepare_decode',prefill),patch.object(F.decode,'consume_cache_tokens',consume),patch.object(real,'Audit',lambda a,**k:original_audit(a,enforce=False))]
    for p in patches:stack.enter_context(p)
    result=launch.run_types(args,make_real=parity_adapter.make_capped_real)
   rows=[json.loads(line) for kind in order for f in (root/'journal'/str(__import__('orchard_h10.common',fromlist=['ORDER']).ORDER.index(kind))).glob('*/items.jsonl') for line in f.read_text().splitlines()]
   values=[dict(id=r['id'],type=r['type'],text=r['output']['text'],tokens=r['output']['tokens'],calls=r['output']['calls'],scores=r['output']['scores'],finish=r['output']['finish'],answer=F.answer_text(r['output'])) for r in rows]
   raw=json.dumps(values,sort_keys=True).encode()
   if baseline is None:baseline=raw
   self.assertEqual(raw,baseline);self.assertEqual(len(loads),1);self.assertEqual(result['completed'],12)
   self.assertTrue(all(r['output']['finish']=='max_calls' for r in rows if r['type']==order[-1]))
   self.assertEqual(F.G3T.calls,{'off':12,'on':2,'verify':4}[mode]);self.assertEqual(sam.calls,10)
   events=[] if mode=='off' else next(iter(M._sessions.values())).events
   self.assertTrue(all(e['equal'] for e in events))
   reports[mode]=dict(output_sha256=hashlib.sha256(raw).hexdigest(),model_loads=len(loads),g3t_calls=F.G3T.calls,sam_calls=sam.calls,events=events,root=str(root),types=order,reads=len(rows))
   print('multi-type',mode,'passed',flush=True)
  write(O/'MULTITYPE_AB.json',dict(passed=True,modes=reports,scope='Real run_types, capped parity.make_real, ParityGenerator, generate_real, decode loop, StageOne, servers, scorer. Frozen modules, model forward, frames and artifact checks are CPU stubs.'))

if __name__=='__main__':unittest.main(verbosity=2)
