from pathlib import Path
import sys,os,json,importlib.util,subprocess,shutil,tarfile,unittest,time,base64,hashlib
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z5';mode=sys.argv[1];sys.argv=sys.argv[:1]
K=J/'out/kit_n';P=D/'before/kit_n/b/pc.py' if mode=='before' else K/'b/pc.py'
spec=importlib.util.spec_from_file_location('pc_probe',P);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
R=D/('probes_v3_'+mode);R.mkdir();names=C.read(K/'k/y.json')
def fixture(label):
 r=R/label;r.mkdir();k=r/'k';shutil.copytree(K,k)
 if mode=='before':
  for n in ('b/pc.py','b/o.py','b/pc.sh'):shutil.copy2(D/'before/kit_n'/n,k/n)
 x=r/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700);n=r/'n';n.mkdir();(n/'p/q/r').mkdir(parents=True)
 C.put(k/'k/p.json',dict(n_root=str(x)))
 p=x/'n_s/sess_41.json';C.put(p,{v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+str(i) for v in names['objects'].values() for i in range(4)});p.chmod(0o600)
 return C.Copier(k,n,'41')
def marker(c,name,step):
 p=c.train/name/('complete.json' if name.startswith('checkpoint') else 'artifact.json');p.parent.mkdir();C.put(p,dict(step=step));return p
class Findings(unittest.TestCase):
 def test_1_retry_every_incomplete(self):
  c=fixture('retry');marker(c,'m100',100)
  for n in ('gcs_o.done','o_copy.done','logs.done'):C.put(c.state/n,dict(ok=True))
  calls=[]
  def once(**kw):
   calls.append(1)
   if len(calls)==2:C.put(c.state/'gcs_m100.done',dict(ok=True))
  with patch.object(C,'Copier',return_value=c),patch.object(c,'pass_once',side_effect=once),patch.object(C.time,'sleep'),patch.object(sys,'argv',['pc',str(c.kit),str(c.root),'41','--final']):C.main()
  self.assertEqual(len(calls),2)
 def test_2_cache_refusal(self):
  c=fixture('cache');p=c.spool/'private/sess.json';p.write_text('')
  with self.assertRaises(ValueError):C.Copier(c.kit,c.root,'41')
 def test_2_atomic(self):
  calls=[];p=R/'atomic.json'
  with patch.object(C.os,'fsync',side_effect=lambda fd:calls.append('fsync')):
   C.put(p,dict(a=1))
  self.assertGreaterEqual(len(calls),2);self.assertEqual(C.read(p),dict(a=1))
 def test_3_live_no_archive(self):
  c=fixture('live');marker(c,'checkpoint_7',7);(c.root/'o').mkdir();(c.root/'o/o.tar').write_bytes(b'q')
  with patch.object(c,'send') as send:c.exit_archive();send.assert_not_called()
 def test_4_result_and_final_tail(self):
  c=fixture('result');(c.root/'t.log').write_text('first\n');(c.root/'j2.log').write_text('batch\n')
  def invoke(*args):subprocess.run([sys.executable,'-I','-s','-B',str(c.kit/'b/o.py'),str(c.root),*args,'--local'],env={**os.environ,'SLURM_JOB_ID':'41'},check=True)
  invoke('7','9');(c.root/'t.log').write_text('first\nlast\n');invoke('99','0','--freeze')
  with tarfile.open(c.root/'o/o.tar') as t:
   self.assertEqual(json.load(t.extractfile('RESULT.json'))['rooms_rc'],9)
   self.assertIn(b'last',t.extractfile('t.log').read())
   self.assertEqual(t.extractfile('j2.log').read(),b'batch\n')
  before=(c.root/'o/o.tar').read_bytes();invoke('0','0','--freeze');self.assertEqual(before,(c.root/'o/o.tar').read_bytes())
  c.copy_exit();self.assertEqual(C.read(c.target/'o/41/RESULT.json')['rooms_rc'],9)
 def test_5_order(self):
  c=fixture('order');calls=[]
  for name,label in [('stop_checkpoint','stop'),('exports','exports'),('small','logs'),('exit_archive','o'),('checkpoints','checkpoints')]:
   def action(label=label):calls.append(label)
   setattr(c,name,action)
  c.pass_once(final=True)
  self.assertEqual(calls,['stop','exports','logs','o','checkpoints'])
 def test_4_missing_result_is_not_zero(self):
  c=fixture('unknown_result')
  subprocess.run([sys.executable,'-I','-s','-B',str(c.kit/'b/o.py'),str(c.root),'143','0','--local','--freeze'],env={**os.environ,'SLURM_JOB_ID':'41'},check=True)
  self.assertIsNone(C.read(c.root/'o/RESULT.json')['rooms_rc'])
 def test_6_window(self):
  with patch.dict(os.environ,{'TK_JOB_START':'1000'},clear=True):
   self.assertTrue(hasattr(C,'deadlines'),'allocation deadline missing')
   self.assertEqual(C.deadlines({'recipe':{'wall_seconds':86400}}),(86620,86800))
 def test_7_wrapper_contract(self):
  p=J/('inputs/jn2.sh' if mode=='before' else 'out/jn3.sh');s=p.read_text()
  self.assertIn('except Exception as e:',s);self.assertIn("trap 'forward TERM' TERM",s);self.assertNotIn('exec bash "$ROOT/job.sh"',s)
 def test_8_rate_driver(self):
  p=J/('out/e2/e2.py' if mode=='before' else 'out/e3/e3.py')
  self.assertTrue('rate_bytes' in p.read_text());self.assertTrue('2 << 30' in p.read_text())

suite=unittest.defaultTestLoader.loadTestsFromTestCase(Findings)
result=unittest.TextTestRunner(verbosity=2).run(suite)
(D/('PROBES_'+mode.upper()+'.json')).write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful()),indent=2)+'\n')
raise SystemExit(0 if mode=='before' and not result.wasSuccessful() else int(not result.wasSuccessful()))
