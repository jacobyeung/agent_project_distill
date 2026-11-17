import io,json,os,sys,tempfile,threading,time,unittest,tarfile,hashlib
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src'
sys.path[:0]=[str(O),str(P/'b'),str(P/'tree'),str(P),str(P/'orchard_h10/vendor')]
import e2e_reader
import tower_sequence as T,unpack_return as U,chain_save
from orchard_h10 import runner
from orchard_h10.common import write,sha,canonical
from h1eval.h10 import launch,parity_adapter
from h1eval.items import load_manifest

class Fixes(unittest.TestCase):
 def config(self):
  root=Path(tempfile.mkdtemp(prefix='fix_',dir=W/'work/tmp'));(root/'e').mkdir();write(root/'e/RESTORE.json',{})
  bind=root/'binding.json';write(bind,dict(root=str(root),name='fixture',sha256='a'*64))
  settings=root/'settings.json';write(settings,dict(export_dir=str(root/'e'),artifact_manifest=str(bind),stage1_select_rule='null_argmax',perception_memo='off',perception_memo_verify_ids=[]))
  return dict(package=str(P),output=str(root/'r'),settings=str(settings),python=sys.executable,export=str(root/'e'),binding=str(bind),export_pin=str(O/'export_544.json'),plan_sha256='a',inputs_sha256='b',operator_sha256=sha(O/'tower_sequence.py'),prefix=[],device='cpu')
 def workers(self,cfg):
  for c in T.prepare(cfg).values():
   entry=runner.control(c)/'5.py'
   entry.write_text("import sys\nsys.path.insert(0,"+repr(str(W/'work'))+")\nfrom fixture_worker import main\nmain()\n")
 def test_production_members_all_six_journals(self):
  cfg=self.config();self.workers(cfg)
  result=T.run(cfg,time.time()+4000,['0']);self.assertTrue(result['complete'],result)
  r=Path(cfg['output']);members=chain_save.members(r);journals=sorted(n for n in members if n.endswith('/items.jsonl'))
  self.assertEqual(len(journals),6);self.assertEqual(result['completed'],786)
  for name in journals:
   folder=str(Path(name).parent)
   for file in ('items.jsonl','environment.json','progress.json','SUMMARY.json','STEPS.jsonl','worker.log','STARTED.json'):
    self.assertIn(folder+'/'+file,members)
  self.assertFalse(any('cache' in Path(n).parts for n in members))
  pids=[]
  for i,count in ((0,636),(1,150)):
   rr=r/'metadata/reads'/str(i)
   self.assertEqual(json.loads((rr/'metadata/LOADS.json').read_text()),[count])
   pids.append({json.loads(line)['output']['fixture_pid'] for f in rr.glob('metadata/journals/*/*/items.jsonl') for line in f.read_text().splitlines()})
  self.assertTrue(all(len(v)==1 for v in pids));self.assertNotEqual(pids[0],pids[1])
  U.validate_journals(r)
  write(O/'RETURN_MEMBERS.json',dict(passed=True,root=str(r),members=sorted(members),journals=journals,process_ids=[list(v) for v in pids],result=result))
 def test_top_stop_reaches_running_subprocess_and_returns_partial(self):
  cfg=self.config();cfg['fixture_stop']=str(Path(cfg['output'])/'metadata/READY');self.workers(cfg)
  errors=[]
  def stop():
   ready=Path(cfg['fixture_stop']);until=time.monotonic()+15
   while not ready.exists() and time.monotonic()<until:time.sleep(.02)
   if not ready.exists():errors.append('worker never ready');return
   (Path(cfg['output'])/'metadata/STOP').write_text('operator stop\n')
  t=threading.Thread(target=stop);t.start();result=T.run(cfg,time.time()+4000,['0']);t.join()
  self.assertEqual(errors,[]);self.assertIsNone(result['failure']);self.assertEqual(result['completed'],1);self.assertFalse(result['complete'])
  r=Path(cfg['output']);members=chain_save.members(r);journals=[n for n in members if n.endswith('/items.jsonl')]
  self.assertEqual(len(journals),1);self.assertEqual(len(members[journals[0]].read_text().splitlines()),1);U.validate_journals(r)
  write(O/'STOP_PROOF.json',dict(passed=True,result=result,journals=journals,root=str(r)))
 def test_unpack_refuses_missing_started_segment(self):
  cfg=self.config();r=Path(cfg['output']);d=r/'metadata/reads/0/metadata/journals/3/0';write(d/'STARTED.json',{})
  with self.assertRaisesRegex(ValueError,'Started segment has no journal'):U.validate_journals(r)
  write(d/'environment.json',{});(d/'items.jsonl').write_text('');U.validate_journals(r)
  write(d.parent.parent/'0/0/STARTED.json',{})
  with self.assertRaisesRegex(ValueError,'Started segment has no journal'):U.validate_journals(r)
 def test_deadline_keeps_partial_summary_and_progress(self):
  cfg=self.config();c=T.prepare(cfg)[0];runner.control(c)
  args=launch.parser().parse_args(runner.worker_args(dict(config=c,type=3,index=0,cards=1,stop_at=time.time()+100,finish_by=time.time()+200)))
  items=load_manifest(args.items)['items']
  def maker(*a,**kw):
   count=[0]
   def gen(item):
    count[0]+=1
    if count[0]==2:raise launch.ReadDeadline()
    return dict(text='1',finish='eos')
   return gen
  with patch.object(parity_adapter,'map_items',return_value=({r['id']:r for r in items},{'sha256':'a'*64})),self.assertRaises(launch.ReadDeadline):
   launch.run_types(args,make_real=maker)
  r=Path(cfg['output']);U.validate_journals(r)
  d=Path(c['output'])/'metadata/journals/3/0'
  self.assertEqual(json.loads((d/'SUMMARY.json').read_text())['completed'],1)
  self.assertTrue(json.loads((d/'progress.json').read_text())['stopped'])

 def test_b04_reuse_rejects_rule_and_memo_from_launcher(self):
  from parity_kit import provenance as V
  cfg=self.config();root=Path(cfg['output']).parent;s=json.loads(Path(cfg['settings']).read_text());meta=root/'meta.json';write(meta,{})
  s.update(config=str(meta),tasks=[],frames_json=str(meta),dense_manifest=str(meta),request=str(meta))
  b04=root/'b04';j=b04/'gpu_results/own_depth_p0';j.mkdir(parents=True)
  receipt=dict(schema='parity-load-v2',arm='own_depth',keys=[],dense_frame_counts={},runtime_identity={},runtime_identity_sha256=V.digest({}),restore={},restore_pin={'sha256':sha(root/'e/RESTORE.json')},artifact_manifest=json.loads(Path(cfg['binding']).read_text()),inputs=dict(settings=dict(s,arm='own_depth'),tasks=[],**{k:{'sha256':sha(meta)} for k in ('frames_json','dense_manifest','request','config')}))
  receipt['settings_sha256']=V.digest(receipt['inputs']['settings']);write(j/'LOAD_RECEIPT.json',receipt);(j/'items.jsonl').write_text('')
  args=launch.parser().parse_args(['--items',str(P/'items/devs1_routed.json'),'--export',cfg['export'],'--artifact-manifest',cfg['binding'],'--reader-root',str(P/'b'),'--out',str(root/'journal'),'--export-pin',cfg['export_pin'],'--settings',cfg['settings'],'--tower-from',str(b04),'--arms','tower','--modes','none','--device','cpu'])
  items=load_manifest(args.items)['items']
  for field,value in [('stage1_select_rule','candidates_argmax'),('perception_memo','on'),('perception_memo_verify_ids',['x'])]:
   changed=dict(s);changed[field]=value
   if field=='perception_memo_verify_ids':
    changed['perception_memo']='verify';receipt['inputs']['settings']['perception_memo']='verify';receipt['settings_sha256']=V.digest(receipt['inputs']['settings']);write(j/'LOAD_RECEIPT.json',receipt)
   write(Path(cfg['settings']),changed)
   with patch.object(parity_adapter,'map_items',return_value=({r['id']:r for r in items},{'sha256':'a'*64})),self.assertRaisesRegex(ValueError,'Tower perception settings differ: '+field):
    launch.run(args,make_real=lambda *a,**k:None)

if __name__=='__main__':unittest.main(verbosity=2)
