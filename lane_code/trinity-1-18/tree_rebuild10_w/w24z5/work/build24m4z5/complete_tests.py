from pathlib import Path
import importlib.util,json,os,sys,unittest,shutil
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z5';K=J/'out/kit_n';R=D/'complete';R.mkdir()
s=importlib.util.spec_from_file_location('pc',K/'b/pc.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
def fixture(label):
 r=R/label;r.mkdir();k=r/'k';(k/'k').mkdir(parents=True);x=r/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700);n=r/'n';n.mkdir()
 for name in ('n','y'):shutil.copy2(K/('k/'+name+'.json'),k/('k/'+name+'.json'))
 C.put(k/'k/p.json',dict(n_root=str(x)))
 C.put(x/'n_s/sess_41.json',{v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+str(i) for v in C.read(k/'k/y.json')['objects'].values() for i in range(4)})
 c=C.Copier(k,n,'41');c.final_pass=True
 for name,marker in [('checkpoint_7','complete.json'),('m7','artifact.json'),('m100','artifact.json')]:C.put(c.train/name/marker,dict(step=int(name.split('_')[-1]) if '_' in name else int(name[1:])))
 return c
class Complete(unittest.TestCase):
 def test_all_pending_destinations(self):
  required=['gcs_checkpoint_7_stop.done','gcs_m7.done','gcs_m100.done','logs.done','gcs_o.done','o_copy.done','gcs_checkpoint_7.done']
  for missing in required:
   c=fixture(missing);calls=[]
   for name in required:
    if name!=missing:C.put(c.state/name,dict(complete=True))
   def once(**kw):
    calls.append(1)
    if len(calls)==2:C.put(c.state/missing,dict(complete=True))
   with patch.object(C,'Copier',return_value=c),patch.object(c,'pass_once',side_effect=once),patch.object(C.time,'sleep'),patch.object(sys,'argv',['pc',str(c.kit),str(c.root),'41','--final']):C.main()
   self.assertEqual(len(calls),2,missing)
 def test_cache_every_use(self):
  for label,bad in [('empty',b''),('partial',b'{'),('incomplete',b'{}')]:
   c=fixture(label);p=c.spool/'private/sess.json';p.write_bytes(bad)
   with self.assertRaises(ValueError):C.Copier(c.kit,c.root,'41')
   with self.assertRaises(ValueError):c.send(c.train/'m7',c.train/'m7/artifact.json',['mstop'])
  c=fixture('mode');p=c.spool/'private/sess.json';p.chmod(0o644)
  with self.assertRaisesRegex(ValueError,'file mode'):C.Copier(c.kit,c.root,'41')
  p.chmod(0o600);p.parent.chmod(0o755)
  with self.assertRaisesRegex(ValueError,'directory mode'):C.Copier(c.kit,c.root,'41')
 def test_atomic_interruption(self):
  p=R/'receipt.json';C.put(p,dict(old=True))
  with patch.object(C.os,'replace',side_effect=OSError('interrupted')):
   with self.assertRaises(OSError):C.put(p,dict(new=True))
  self.assertEqual(C.read(p),dict(old=True));self.assertEqual(C.read(p.with_name(p.name+'.part')),dict(new=True))
 def test_live_report_and_priority(self):
  c=fixture('live');c.final_pass=False
  self.assertIsNone(c.stop_marker())
  C.put(c.train/'run_41.json',dict(last_step=7,stop_reason='budget_or_signal',steps=[]))
  self.assertEqual(c.stop_marker().parent.name,'checkpoint_7')
  order=[]
  def send(directory,marker,labels,**kwargs):order.append(directory.name)
  with patch.object(c,'send',side_effect=send):c.stop_checkpoint();c.exports();c.checkpoints();c.exit_archive()
  self.assertEqual(order,['checkpoint_7','m7','m100'])
 def test_deadline_sources(self):
  with patch.dict(os.environ,{'TK_JOB_START':'1000','SLURM_JOB_END_TIME':'90000'},clear=True):self.assertEqual(C.deadlines(),(89220,89400))
  with patch.dict(os.environ,{'TK_JOB_START':'1000'},clear=True):self.assertEqual(C.deadlines({'recipe':{'wall_seconds':3600}}),(3820,4000))
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Complete))
(D/'COMPLETE.json').write_text(json.dumps(dict(tests=r.testsRun,status='PASS' if r.wasSuccessful() else 'FAIL'),indent=2)+'\n')
raise SystemExit(not r.wasSuccessful())
