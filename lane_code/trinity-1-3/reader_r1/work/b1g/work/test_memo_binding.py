import io,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src'
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P),str(O)]
import torch,scipy
from e2e_reader import perception_memo as M
from h1eval.h10 import launch,parity_adapter,merge
from h1eval.items import load_manifest
from orchard_h10.common import write,sha
import tower_sequence as T

def fixture_maker(*args,**kwargs):return lambda item:dict(text='<answer>0</answer>',finish='eos')

class Binding(unittest.TestCase):
 def fresh(self):return Path(tempfile.mkdtemp(prefix='memo_',dir=W/'work/tmp'))
 def prepare(self,policy):
  from orchard_h10 import prepare
  from parity_kit import stage_restore,build_manifest
  root=self.fresh();(root/'d').mkdir();(root/'p').mkdir()
  pins=json.loads((O/'export_544.json').read_text());inputs=json.loads((O/'inputs_tower.json').read_text())
  logical='/scratch/jjyeung/b01ec87a6f29b'
  inputs=json.loads(json.dumps(inputs).replace(logical,str(root)));inputs['_export']=pins
  # Staged metadata pins are real; only unavailable model restore and runtime versions are stubs.
  modules={'torchvision':NS(__name__='torchvision',__version__='fixture'),
           'transformers':NS(__name__='transformers',__version__='5.12.0')}
  versions=dict(torch=torch.__version__,torchvision='fixture',transformers='5.12.0',scipy=scipy.__version__)
  rec=Path(inputs['files'][inputs['environment_receipt']]['path']);write(rec,dict(versions=versions))
  def stage(*args,**kw):
   export=Path(args[3]);export.mkdir(parents=True);write(export/'RESTORE.json',dict(fixture=True))
  with patch.dict(sys.modules,modules),patch.object(stage_restore,'stage',stage),patch.object(build_manifest,'build',return_value=dict(schema='fixture')):
   prepare.run(dict(logical=str(root),**policy),inputs)
  settings=json.loads((root/'d/settings.json').read_text())
  for k,v in policy.items():self.assertEqual(settings[k],v)
  return root,settings
 def test_empty_root_settings_binding_resume_merge(self):
  items=load_manifest(P/'items/devs1_routed.json')['items'];proof=[]
  for i,rule in enumerate(T.RULES):
   policy={k:v for k,v in T.descriptors(P)[i].items() if k in ('stage1_select_rule','perception_memo','perception_memo_verify_ids','perception_memo_modules')}
   root,settings=self.prepare(policy);path=root/'d/settings.json';binding=root/'d/binding.json'
   args=launch.parser().parse_args(['--items',str(P/'items/devs1_routed.json'),'--export',str(root/'d/e'),
      '--artifact-manifest',str(binding),'--reader-root',str(P/'b'),'--out',str(root/'journal'),
      '--export-pin',str(O/'export_544.json'),'--settings',str(path),'--types','object_abs_distance',
      '--arms','tower','--modes','none','--device','cpu'])
   with patch.object(parity_adapter,'map_items',return_value=({r['id']:r for r in items},{'sha256':'a'*64})),patch('sys.stdout',new=io.StringIO()):
    launch.run(args,make_real=fixture_maker)
    env=json.loads((root/'journal/environment.json').read_text())
    for k,v in policy.items():self.assertEqual(env['binding'][k],v)
    for missing in ('perception_memo','stage1_select_rule','perception_memo_verify_ids','perception_memo_modules'):
     changed=dict(settings);changed.pop(missing);write(path,changed)
     with self.assertRaises(KeyError):launch.run(args,make_real=fixture_maker)
    for field,value in [('perception_memo_modules',[]),('perception_memo','off'),('perception_memo_verify_ids',policy['perception_memo_verify_ids'][:-1] if i==1 else [])]:
     if settings.get(field)==value:continue
     changed=dict(settings);changed[field]=value
     if field=='perception_memo':changed.update(perception_memo_verify_ids=[])
     write(path,changed)
     with self.assertRaisesRegex(ValueError,'Resume binding differs'):launch.run(args,make_real=fixture_maker)
    write(path,settings)
    other=self.fresh();modified=json.loads(json.dumps(env));modified['binding']['perception_memo']='off';write(other/'environment.json',modified)
    with self.assertRaisesRegex(ValueError,'Shard bindings differ'):merge.merge([root/'journal',other],root/'merge')
    with self.assertRaisesRegex(ValueError,'perception_memo'):
     launch.tower_records(other,env['binding'],[])
   proof.append(dict(read=i,settings=str(path),environment=str(root/'journal/environment.json'),policy=policy,
                     completed=len(launch.read_records(root/'journal/items.jsonl'))))
  (O/'MEMO_BINDING.json').write_text(json.dumps(dict(passed=True,real_prepare_function=True,stubbed=['model restore','manifest build','runtime version receipt'],reads=proof),indent=2)+'\n')
 def test_schedule_identity_and_missing(self):
  root,settings=self.prepare(dict(stage1_select_rule='null_argmax',perception_memo_modules=['g3t'],perception_memo='off',perception_memo_verify_ids=[]))
  cfg=dict(package=str(P),output=str(root/'r'),settings=str(root/'d/settings.json'),python=sys.executable,
           export='e',binding='b',export_pin='p',plan_sha256='a',inputs_sha256='b',operator_sha256=sha(O/'tower_sequence.py'),prefix=[],device='cpu')
  configs=T.prepare(cfg)
  # One policy identity for all segments in each logical read, despite effective modes.
  for i in (0,1):
   values=[Path(c['settings']).read_bytes() for r,c in configs.items() if r==i]
   self.assertTrue(all(v==values[0] for v in values))
  for missing in ('perception_memo','stage1_select_rule','perception_memo_verify_ids','perception_memo_modules'):
   value=dict(settings);value.pop(missing);write(root/'d/settings.json',value)
   with self.assertRaises(KeyError):T.prepare(cfg)
 def test_production_parity_policy_and_resume_ordinal(self):
  from e2e_reader import parity
  from contextlib import ExitStack
  art=NS();art.verify=lambda:art
  proc=NS(tokenizer=None,_routing_tokens={'ids':{}})
  tasks=[dict(id=str(i),room='fixture',question_type='object_abs_distance') for i in range(32)]
  tasks.append(dict(id='camera',room='fixture',question_type='camera_rotation'))
  class Generator:
   def __init__(self,*a,**kw):self.perception=a[3]
   def __call__(self,item):
    memo=getattr(self.perception,'memo',None)
    if memo is not None:memo.begin_read()
    return dict(text='0',finish='eos',memo=None if memo is None else memo.report())
  for mode in ('off','on','verify'):
   settings=dict(arm='own_depth',frames_json={'captures':{}},dense_manifest={'captures':{}},
     stage1_select_rule='null_argmax',perception_memo_modules=['g3t'],perception_memo=mode,
     perception_memo_verify_ids=[str(i) for i in range(30)] if mode=='verify' else [])
   with ExitStack() as stack:
    for name,value in dict(install=lambda *a:None,Artifact=lambda *a,**k:art,
      load_native=lambda *a,**k:(None,proc,{'config':{},'export':{'frame_layout':'duplicate'}}),
      CallHook=lambda *a:None,install_hook=lambda *a:None,policy=lambda:NS(),
      ParityGenerator=Generator,bind_item=lambda *a,**k:{},score=lambda *a:{}).items():
     stack.enter_context(patch.object(parity,name,value))
    gen=parity.make_real(None,dict(root='fixture',name='fixture',sha256='fixture'),tasks,settings=settings)
    for index in (30,0,29,32):
     result=gen(tasks[index])
     if mode=='off':self.assertIsNone(result['memo'])
     else:
      expected='verify' if mode=='verify' and index<30 else 'on'
      self.assertEqual(result['memo']['effective'],expected)
      self.assertEqual(result['memo']['item_id'],tasks[index]['id'])
 def test_explicit_id_policy(self):
  m=M.Memo(perception_memo_modules=['g3t'],perception_memo='verify',perception_memo_verify_ids=('distance-a',))
  for identifier in ('camera-a','distance-a','distance-z'):
   m.item_id=identifier;m.begin_read();self.assertEqual(m.mode,'verify' if identifier=='distance-a' else 'on')

if __name__=='__main__':unittest.main(verbosity=2)
