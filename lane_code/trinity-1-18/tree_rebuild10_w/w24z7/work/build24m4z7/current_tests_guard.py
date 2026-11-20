from pathlib import Path
import sys,os,json,unittest,importlib.util,hashlib,runpy,base64
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z7/current_suite_guard';D.mkdir();K=J/'out/kit_n_go'
s=importlib.util.spec_from_file_location('copier_current',K/'b/pc.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
names=C.read(K/'k/y.json')
def fixture(label,job='41',sessions=True):
 r=D/label;r.mkdir();k=r/'k';(k/'k').mkdir(parents=True);x=r/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700);n=r/'n';n.mkdir();(n/'p/q/r').mkdir(parents=True)
 C.put(k/'k/p.json',dict(n_root=str(x)));C.put(k/'k/n.json',dict(output='/run/469ddece'));C.put(k/'k/y.json',names)
 if sessions:
  p=x/'n_s'/('sess_'+job+'.json');C.put(p,{v+'.j'+job+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+v+'/'+str(i) for v in names['objects'].values() for i in range(4)});p.chmod(0o600)
 return k,x,n
def copier(label,job='41'):
 k,x,n=fixture(label,job);return C.Copier(k,n,job,writer=J/'work/enospc7_guard/fake_gc_run.py')
def state(c,name,step):
 d=c.train/name;d.mkdir();p=d/('complete.json' if name.startswith('checkpoint_') else 'artifact.json');C.put(p,dict(step=step,tag=name));(d/'q.bin').write_bytes(b'q'*8192);return p

class Current(unittest.TestCase):
 def test_listing_budget(self):
  c=copier('budget');state(c,'m100',100);state(c,'checkpoint_7',7)
  (c.root/'t.log').write_bytes(b'q\n'*300000)
  self.assertLessEqual(c.small(),C.CAP)
  self.assertEqual({r['name'] for r in C.read(c.live/'markers.json')},{'m100/artifact.json','checkpoint_7/complete.json'})
  self.assertFalse((c.live/'q.bin').exists())
 def test_retry_idempotence_and_local_state(self):
  c=copier('retry');state(c,'m100',100)
  sink=D/'sink';os.environ['FAKE_SINK']=str(sink)
  with patch.object(C.subprocess,'run') as run:
   run.return_value.returncode=1;c.exports()
  self.assertFalse((c.state/'gcs_m100.done').exists());self.assertIn('pending',C.read(c.state/'gcs_m100.json')['status'])
  c.exports();done=c.state/'gcs_m100.done';stamp=done.stat().st_mtime_ns;before=list(sink.iterdir());c.exports()
  self.assertEqual(stamp,done.stat().st_mtime_ns);self.assertEqual(before,list(sink.iterdir()));self.assertTrue((c.live/'UPLOAD_NO_RECEIPTS.json').exists())
  self.assertEqual(C.read(done)['sha256'],C.sha(next(c.spool.glob('*.tar'))))
 def test_allocation_names_and_slot_limit(self):
  a=copier('claims1','41');b=copier('claims2','42')
  self.assertNotEqual(a.claim(['m100'],'a')[1],b.claim(['m100'],'a')[1])
  labels=['ck%02d'%i for i in range(16)]
  keys=[a.claim(labels,str(i))[1] for i in range(16)]
  self.assertEqual(len(set(keys)),16);self.assertEqual(a.claim(labels,'1')[1],keys[1])
  with self.assertRaisesRegex(ValueError,'E97'):a.claim(labels,'17')
 def test_missing_and_incomplete(self):
  k,x,n=fixture('missing',sessions=False)
  with self.assertRaisesRegex(ValueError,'file missing'):C.Copier(k,n,'41')
  p=x/'n_s/sess_41.json';p.write_text('{}');p.chmod(0o600)
  with self.assertRaisesRegex(ValueError,'E101'):C.Copier(k,n,'41')
 def test_private_modes_and_symlinks(self):
  k,x,n=fixture('permissions');p=x/'n_s/sess_41.json';p.chmod(0o644)
  with self.assertRaisesRegex(ValueError,'file mode'):C.Copier(k,n,'41')
  p.chmod(0o600);p.rename(x/'n_s/actual.json');p.symlink_to(x/'n_s/actual.json')
  with self.assertRaises(ValueError):C.Copier(k,n,'41')
 def test_stop_uses_dedicated_object(self):
  c=copier('stop');state(c,'checkpoint_7',7);os.environ['FAKE_SINK']=str(D/'sink_stop')
  c.checkpoints();c.stop_checkpoint()
  self.assertTrue((c.state/'gcs_checkpoint_7.done').exists());self.assertTrue((c.state/'gcs_checkpoint_7_stop.done').exists())
  self.assertEqual(C.read(c.state/'ckstop.json')['status'],'gcs');self.assertFalse(c.checkpoint.exists())
 def test_empty_stop_safe(self):
  c=copier('empty');c.stop_checkpoint();self.assertEqual(C.read(c.state/'ckstop.json')['status'],'no completed checkpoint')
 def test_gc_rejects_wrong_digest(self):
  g=runpy.run_path(str(K/'b/gc.py'),run_name='gc_test');p=D/'q.bin';p.write_bytes(b'q'*128)
  class Reply:
   status=200
   def read(self):return b'{"size":128,"md5Hash":"wrong"}'
  class Conn:
   def __init__(self,*a,**kw):pass
   def putrequest(self,*a):pass
   def putheader(self,*a):pass
   def endheaders(self):pass
   def send(self,*a):pass
   def getresponse(self):return Reply()
  with patch.object(g['http'].client,'HTTPSConnection',Conn),patch.object(g['time'],'sleep'):
   with self.assertRaisesRegex(OSError,'size/md5 mismatch'):
    g['upload']('https://local.invalid/x',p,0,128,'q9/x')
  # A mismatched response cannot become an upload receipt.

if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Current))
 (D/'RESULT.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),status='PASS' if r.wasSuccessful() else 'FAIL'),indent=2)+'\n')
 raise SystemExit(not r.wasSuccessful())
