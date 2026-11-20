import sys, os, json, traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
limits()
sys.path[:0]=[str(KIT/'b'),str(TREE)]
from unittest.mock import patch
import ep,rd,rg
from student_pilot import s1_routing,mdg_parent
import torch
torch.set_num_threads(1);torch.set_num_interop_threads(1)
root=Path(os.environ['TEST_ROOT']);job=os.environ['SLURM_JOB_ID']
checks=[];runs=[]
def check(label,v,**details):checks.append(dict(assertion=label,pass_=bool(v),**details))
for index,(mode,prefix,publisher) in enumerate([('q','p','ep'),('r','dr/p','ep'),('q','p','rd'),('r','dr/p','rd')]):
 node=root/(mode+'_'+publisher);j=str(int(job)+index);target=Path(NROOT)/'o'/j
 try:
  point=put(node/'point.json',dict(division={}))
  cfg=dict(streams=dict(pointing=point))
  emitted=[]
  def builder(config,output,division,model):
   for rel in [prefix+'/q/selection/materialization.json',prefix+'/q/selection/receipt.json',prefix+'/i/pool/r.json',prefix+'/q/base/materialization.json']:
    source=T.parent/'fixtures'/mode/rel
    emitted.append(raw(node/rel,source.read_bytes()))
   raise ValueError('synthetic-routing-build-raised')
  error=None
  try:
   with patch.object(s1_routing,'build',side_effect=builder) as mocked,patch.object(mdg_parent,'model_pin',return_value={}):
    rg.regenerate(cfg,node/prefix/'q')
  except ValueError as e:error=str(e)
  finally:
   if publisher=='ep':ep.publish(KIT,node,j,1)
   else:rd.publish(KIT,node,j,1)
  check(mode+' '+publisher+' native routing build raises',error=='synthetic-routing-build-raised' and mocked.call_count==1,observed=error)
  manifest=load(target/'a6.json')
  check(mode+' '+publisher+' independent artifact set',len(manifest)==7 and {'materialization.json','receipt.json','refresh.json'} <= set(manifest))
  for leaf,item in manifest.items():
   actual=target/leaf;source=node/item['source']
   check(mode+' '+publisher+' raw publication '+leaf,actual.read_bytes()==source.read_bytes() and sha(actual)==item['sha256'] and actual.stat().st_size==item['bytes'],sha256=sha(actual),source=item['source'])
  check(mode+' '+publisher+' failure status retained',load(target/'r1.json')['returncode']==1)
  check(mode+' '+publisher+' standalone materialization survived',('a1m.json' if mode=='q' else 'b1m.json') in manifest)
  check(mode+' '+publisher+' refresh alias maps r.json',manifest['refresh.json']['source']==prefix+'/i/pool/r.json')
  runs.append(dict(mode=mode,publisher=publisher,job=j,raised=error,manifest=manifest,emitted=emitted))
 except Exception:
  check(mode+' '+publisher+' case completed',False,error=traceback.format_exc())
result=dict(case='publication_build_raises',verdict='PASS' if checks and all(c['pass_'] for c in checks) else 'FAIL',assertions=checks,runs=runs,target_files=['b/ep.py','b/rd.py','b/rg.py','b/z.py'],limitations=['Native routing builder and model pin are synthetic fixtures; native rg.regenerate and ep/rd publication execute unchanged kit bytes. No production routing build is claimed.'])
put(root.parent/'case_result.json',result)
print(json.dumps(result))
raise SystemExit(0 if result['verdict']=='PASS' else 1)
