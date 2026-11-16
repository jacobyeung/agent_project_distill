import hashlib,json,os,subprocess,sys,unittest,uuid,runpy
from pathlib import Path
from unittest.mock import patch,Mock
B=Path(__file__).resolve().parents[2]
RROOT=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'
sys.path[:0]=[str(RROOT),str(RROOT/'orchard_native')]
import orchard_results as R
import orchard_launcher as L
import native_job as J
PLAN='a'*64

class Returns(unittest.TestCase):
 def setUp(self):
  self.root=B/'work/return_tests'/uuid.uuid4().hex;self.root.mkdir(parents=True)
  self.pool=self.root/'pool';self.source=self.root/'source';self.source.mkdir()
  (self.source/'COMPLETE.json').write_text(json.dumps(dict(plan_sha256=PLAN,synthetic=False)))
  self.token='a'+uuid.uuid4().hex
  self.bindir=self.root/'bin';self.bindir.mkdir()
  cli=self.bindir/'gcloud'
  cli.write_text('#!/bin/sh\nexec '+sys.executable+' -I -s -B '+str(B/'out/tests/fake_gcloud.py')+' "$@"\n');cli.chmod(0o755)
  self.env=patch.dict(os.environ,{'PATH':str(self.bindir)+':'+os.environ['PATH'],
    'C8R_CLOUD_STORE':str(self.root/'cloud'),'SLURM_JOB_ID':'42'})
  self.env.start();self.auth=patch.object(R,'AUTHORIZED_POOL',self.pool);self.auth.start()
 def tearDown(self):
  self.auth.stop();self.env.stop()
 def publish(self,**kw):
  kw.setdefault('cloud_config','/fixture/config')
  return R.publish(self.source,self.pool,self.token,PLAN,0,**kw)
 def remote(self,argv):
  argv=list(argv)
  # The fixture honors the requested interpreter even for nested transport readers.
  argv=[sys.executable if arg=='python3' else arg for arg in argv]
  return subprocess.run(argv,capture_output=True,timeout=20)
 def fetch(self,mode='pilot'):
  cfg=dict(token=self.token,plan_sha256=PLAN,mode=mode,assets=dict(gcloud_config='/fixture/config'))
  return R.fetch_return(cfg,dict(status='SUBMITTED',job=42),self.root,self.remote)
 def test_write_probe_pass(self):
  v=R.write_test(self.pool,self.token)
  self.assertTrue(v['verified']);self.assertEqual(v['bytes'],4*1024**2)
  self.assertEqual(list(self.pool.iterdir()),[])
 def test_write_probe_refusal(self):
  self.pool.write_text('not a directory')
  with self.assertRaises(subprocess.CalledProcessError):R.write_test(self.pool,self.token)
 def test_probe_hash_refusal(self):
  with patch.object(R.hashlib,'sha256',side_effect=[Mock(hexdigest=lambda:'a'),Mock(hexdigest=lambda:'b')]):
   with self.assertRaisesRegex(ValueError,'readback'):R.pool_worker('test',self.pool,self.token,1)
 def test_probe_in_process_pass(self):
  self.assertTrue(R.pool_worker('test',self.pool,self.token,1)['verified'])
 def test_probe_short_write(self):
  stream=Mock();stream.write.return_value=0
  with patch.object(R.tempfile,'TemporaryFile') as f:
   f.return_value.__enter__.return_value=stream
   with self.assertRaisesRegex(OSError,'Short pool write'):R.pool_worker('test',self.pool,self.token,1)
 def test_probe_pool_cap(self):
  with patch.object(R,'POOL_LIMIT',1):
   with self.assertRaises(R.S.BudgetError):R.pool_worker('test',self.pool,self.token,1)
 def test_probe_deadline(self):
  process=Mock();process.communicate.side_effect=subprocess.TimeoutExpired('fixture',60)
  with patch.object(R.subprocess,'Popen',return_value=process):
   with self.assertRaises(TimeoutError):R.write_test(self.pool,self.token)
  process.kill.assert_called_once()
  self.assertEqual(process.communicate.call_args.kwargs['timeout'],60)
 def test_probe_elapsed_deadline(self):
  with patch.object(R,'pool_operation',return_value={'verified':True,'bytes':4*1024**2}),patch.object(R.time,'monotonic',side_effect=[0,61]):
   with self.assertRaises(TimeoutError):R.write_test(self.pool,self.token)
 def test_probe_missing_confirmation(self):
  with patch.object(R,'pool_operation',return_value={}):
   with self.assertRaisesRegex(ValueError,'did not verify'):R.write_test(self.pool,self.token)
 def test_both_channels(self):
  result=self.publish();self.assertEqual(result['verified_channels'],['pool','gcs'])
  R.verify(result,self.pool/self.token/'result.tar.gz',PLAN)
  receipt=json.loads((self.source/'RETURN_RECEIPT.json').read_text())
  self.assertTrue(receipt['returned'])
  for obj in receipt['channels']['gcs']['objects'].values():
   self.assertTrue(obj['verified']);self.assertEqual(obj['generation'],'73')
  calls=[json.loads(x) for x in (self.root/'cloud/calls.jsonl').read_text().splitlines()]
  self.assertTrue(all(c['config']=='/fixture/config' for c in calls))
  self.assertTrue(all(c['argv'][2].endswith('#73') for c in calls if c['argv'][:2]==['storage','cat']))
  self.assertTrue(result['proof_channels']['pool']['verified'])
  self.assertTrue(result['proof_channels']['gcs']['verified'])
  self.assertEqual(json.loads((self.pool/self.token/'RETURN_RECEIPT.json').read_text()),receipt)
  self.assertEqual(json.loads((self.root/'cloud'/self.token/'RETURN_RECEIPT.json').read_text()),receipt)
 def test_pool_fallback(self):
  with patch.dict(os.environ,{'C8R_CLOUD_FAIL':'1'}):v=self.publish()
  self.assertEqual(v['verified_channels'],['pool']);self.assertEqual(v['status'],'COMPLETE')
 def test_gcs_fallback(self):
  self.pool.write_text('blocked')
  v=self.publish();self.assertEqual(v['verified_channels'],['gcs'])
 def test_neither_channel(self):
  self.pool.write_text('blocked')
  with patch.dict(os.environ,{'C8R_CLOUD_FAIL':'1'}):v=self.publish()
  self.assertFalse(v['complete']);self.assertEqual(v['status'],'INCOMPLETE')
 def test_gcs_corruption_refused(self):
  with patch.dict(os.environ,{'C8R_CLOUD_CORRUPT':'1'}):v=self.publish()
  self.assertEqual(v['verified_channels'],['pool'])
  receipt=json.loads((self.source/'RETURN_RECEIPT.json').read_text())
  self.assertIn('SHA256',receipt['channels']['gcs']['error'])
 def test_gcs_metadata_refused(self):
  with patch.dict(os.environ,{'C8R_CLOUD_BAD_META':'1'}):v=self.publish()
  self.assertEqual(v['verified_channels'],['pool'])
  with patch.dict(os.environ,{'C8R_CLOUD_BAD_META':'1'}):
   (self.pool/self.token/'EXIT.json').write_text('{}')
   with self.assertRaisesRegex(RuntimeError,'Neither return verified'):self.fetch()
 def test_fresh_pool_token(self):
  self.pool.mkdir();(self.pool/self.token).mkdir()
  v=self.publish();self.assertEqual(v['verified_channels'],['gcs'])
 def test_caps_and_full(self):
  self.assertEqual((R.mode_limit('pilot'),R.mode_limit('full'),R.POOL_LIMIT),(100_000_000,300_000_000,1024**3))
  v=self.publish(mode='full');R.verify(v,self.pool/self.token/'result.tar.gz',PLAN)
  self.assertEqual(self.fetch(mode='full')['channel'],'pool')
 def test_archive_cap_refusal(self):
  with patch.object(R,'mode_limit',return_value=R.EXIT_RESERVE+1):
   with self.assertRaises(R.S.BudgetError):self.publish()
 def test_pool_cap_refusal(self):
  v=self.publish();local=Path(v['local_return'])
  with patch.object(R,'POOL_LIMIT',1):
   with self.assertRaises(R.S.BudgetError):R.pool_worker('publish',self.pool,'b'+uuid.uuid4().hex,4*1024**2,local)
 def test_pool_mode_cap_refusal(self):
  v=self.publish()
  with patch.object(R,'mode_limit',return_value=1):
   with self.assertRaises(R.S.BudgetError):R.pool_worker('publish',self.pool,'b'+uuid.uuid4().hex,4*1024**2,v['local_return'])
 def test_local_overhead_cap(self):
  with patch.object(R,'usage',return_value=100_000_001):
   with self.assertRaises(R.S.BudgetError):self.publish()
 def test_pool_copy_corruption(self):
  v=self.publish();original=R.sha
  with patch.object(R,'sha',side_effect=lambda p:'x'*64 if str(p).endswith('.partial') else original(p)):
   with self.assertRaisesRegex(ValueError,'readback'):R.pool_worker('publish',self.pool,'b'+uuid.uuid4().hex,4*1024**2,v['local_return'])
 def test_pool_copy_short_write(self):
  v=self.publish();original=Path.open;stream=Mock();stream.write.return_value=0
  class Short:
   def __enter__(self):return stream
   def __exit__(self,*a):return False
  def opened(path,*a,**kw):
   return Short() if str(path).endswith('.partial') else original(path,*a,**kw)
  with patch.object(Path,'open',opened):
   with self.assertRaisesRegex(OSError,'Short pool copy'):R.pool_worker('publish',self.pool,'b'+uuid.uuid4().hex,4*1024**2,v['local_return'])
 def test_pool_proof_helper(self):
  v=self.publish();local=Path(v['local_return'])
  self.assertTrue(R.pool_worker('receipt',self.pool,self.token,1,local)['verified'])
  with self.assertRaisesRegex(ValueError,'No pool return'):R.pool_worker('receipt',self.pool,'b'+uuid.uuid4().hex,1,local)
  proof=local/'RETURN_RECEIPT.json';data=json.loads(proof.read_text());data['token']='wrong';proof.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'identity differs'):R.pool_worker('receipt',self.pool,self.token,1,local)
 def test_pool_proof_capacity_and_readback(self):
  v=self.publish();local=Path(v['local_return'])
  with patch.object(R,'EXIT_RESERVE',1):
   with self.assertRaises(R.S.BudgetError):R.pool_worker('receipt',self.pool,self.token,1,local)
  original=R.sha
  with patch.object(R,'sha',side_effect=lambda p:'x'*64 if Path(p)==self.pool/self.token/'RETURN_RECEIPT.json' else original(p)):
   with self.assertRaisesRegex(ValueError,'proof readback'):R.pool_worker('receipt',self.pool,self.token,1,local)
 def test_proof_cap(self):
  original=R.upload
  def upload(local,*a,**kw):
   result=original(local,*a,**kw)
   with (Path(local)/'JOB.log').open('a') as s:s.write('x'*20001)
   return result
  with patch.object(R,'mode_limit',return_value=20000),patch.object(R,'upload',side_effect=upload):v=self.publish()
  self.assertFalse(v['proof_channels']['gcs']['verified'])
  self.assertIn('cap',v['proof_channels']['gcs']['error'])
 def test_pool_copy_and_readback(self):
  v=self.publish();local=Path(v['local_return']);token='b'+uuid.uuid4().hex
  result=R.pool_worker('publish',self.pool,token,4*1024**2,local)
  self.assertTrue(result['verified']);R.verify(json.loads((self.pool/token/'EXIT.json').read_text()),self.pool/token/'result.tar.gz',PLAN)
 def test_fetch_pool(self):
  self.publish();v=self.fetch();self.assertEqual(v['channel'],'pool');self.assertTrue(v['return_proof']['returned'])
 def test_fetch_gcs(self):
  self.pool.write_text('blocked');self.publish()
  v=self.fetch();self.assertEqual(v['channel'],'gcs');self.assertTrue(v['return_proof']['returned'])
 def test_fetch_foreign_proof(self):
  self.publish();p=self.pool/self.token/'RETURN_RECEIPT.json';v=json.loads(p.read_text());v['job']='wrong';p.write_text(json.dumps(v))
  result=self.fetch();self.assertIsNone(result['return_proof']);self.assertIn('proof',result['fallback_errors'])
 def test_fetch_neither(self):
  with self.assertRaisesRegex(RuntimeError,'Neither return verified'):self.fetch()
 def test_fetch_uncertain_submission(self):
  with self.assertRaisesRegex(ValueError,'uncertain'):R.fetch_return({},dict(status='UNCERTAIN'),self.root,self.remote)
 def test_fetch_archive_pin_refused(self):
  self.publish();p=self.pool/self.token/'EXIT.json';v=json.loads(p.read_text());v['archive']['bytes']=300_000_001;p.write_text(json.dumps(v))
  self.assertEqual(self.fetch()['channel'],'gcs')
 def test_fetch_bad_generation(self):
  self.publish();(self.pool/self.token/'EXIT.json').write_text('{}')
  with patch.dict(os.environ,{'C8R_CLOUD_BAD_META':'1'}):
   with self.assertRaisesRegex(RuntimeError,'Invalid GCS return metadata'):self.fetch()
 def test_fetch_gcs_short_read(self):
  self.pool.write_text('blocked');self.publish();original=self.remote
  def remote(argv):
   result=original(argv)
   if 'cat' in argv and any('result.tar.gz#' in x for x in argv):result.stdout=result.stdout[:-1]
   return result
  cfg=dict(token=self.token,plan_sha256=PLAN,mode='pilot',assets=dict(gcloud_config='/fixture/config'))
  with self.assertRaisesRegex(RuntimeError,'size differs'):R.fetch_return(cfg,dict(status='SUBMITTED',job=42),self.root,remote)
 def test_fetch_identity_refusal(self):
  v=self.publish();p=self.pool/self.token/'EXIT.json';x=json.loads(p.read_text());x['token']='wrong';p.write_text(json.dumps(x))
  self.assertEqual(self.fetch()['channel'],'gcs')
 def test_fetch_archive_corruption(self):
  self.publish();(self.pool/self.token/'result.tar.gz').write_bytes(b'bad')
  self.assertEqual(self.fetch()['channel'],'gcs')
 def test_launcher_api(self):
  cfg=dict(token=self.token);sub=dict(status='SUBMITTED',job=42)
  (self.root/'CONFIG.json').write_text(json.dumps(cfg));(self.root/'SUBMISSION.json').write_text(json.dumps(sub))
  with patch.object(R,'fetch_return',return_value={'ok':True}) as f:
   self.assertEqual(L.fetch(self.root),{'ok':True});self.assertEqual(f.call_args.args[:3],(cfg,sub,self.root))
 def test_invalid_identity(self):
  for pool,token,rate in ((self.pool,'bad',1),(self.root/'wrong',self.token,1),(self.pool,self.token,0)):
   with self.assertRaises(ValueError):R.identity(pool,token,rate)
  with self.assertRaises(ValueError):R.mode_limit('other')
  with self.assertRaises(ValueError):R.publish(self.source,self.pool,self.token,'wrong',0)
  with self.assertRaises(ValueError):self.publish(cloud_config='relative')
  with self.assertRaises(ValueError):R.identity(Path('relative'),self.token)
  with self.assertRaises(ValueError):R.pool_worker('test',Path('relative'),self.token,1)
  with self.assertRaises(ValueError):R.pool_worker('unknown',self.pool,self.token,1)
 def test_default_cloud_config(self):
  v=R.publish(self.source,self.pool,self.token,PLAN,0)
  self.assertEqual(v['verified_channels'],['pool','gcs'])
 def test_helper_entrypoint(self):
  with patch.object(sys,'argv',[R.__file__]):
   with self.assertRaises(SystemExit):runpy.run_path(R.__file__,run_name='__main__')
  with patch.object(sys,'argv',[R.__file__,'--pool-worker','test',str(self.pool),self.token,'1']):
   runpy.run_path(R.__file__,run_name='__main__')
 def test_job_refuses_before_staging(self):
  cfg=json.loads((B.parents[1]/'work/p9/metadata/CONFIG.json').read_text())
  with patch.object(J.S,'physical',return_value=self.source),patch.object(J.R,'write_test',side_effect=OSError('probe failed')),patch.object(J,'context') as context,patch.object(J.S,'stage') as stage,patch.object(J,'card',return_value={}),patch.object(J.J,'stop'),patch.object(J.R,'publish',return_value={'status':'FAILED'}),patch.object(J.signal,'signal'):
   self.assertNotEqual(J.run(self.root,cfg),0)
   context.assert_not_called();stage.assert_not_called()
  self.assertIn('probe failed',(self.source/'FAILED.json').read_text())

if __name__=='__main__':unittest.main()
