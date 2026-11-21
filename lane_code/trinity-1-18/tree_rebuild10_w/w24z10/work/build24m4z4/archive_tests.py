from pathlib import Path
import sys,os,json,unittest,importlib.util,hashlib,tarfile,subprocess,shutil
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z4/archive_cases';D.mkdir();K=J/'out/kit_n_go'
s=importlib.util.spec_from_file_location('copier_archive',K/'b/pc.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
names=C.read(K/'k/y.json')
def fixture(label):
 r=D/label;r.mkdir();k=r/'k';(k/'k').mkdir(parents=True);x=r/'x';x.mkdir();(x/'n_s').mkdir(mode=0o700);n=r/'n';n.mkdir();(n/'p/q/r').mkdir(parents=True)
 C.put(k/'k/p.json',dict(n_root=str(x)));C.put(k/'k/n.json',dict(output='/run/469ddece'));C.put(k/'k/y.json',names)
 p=x/'n_s/sess_41.json';C.put(p,{v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+v+'/'+str(i) for v in names['objects'].values() for i in range(4)});p.chmod(0o600)
 return C.Copier(k,n,'41',writer=D/'writer.py')
# Run the real gc.py, injecting one failed part at its HTTPS boundary.
writer=(J/'work/enospc4/fake_gc_run.py').read_text().replace("W=Path(__file__).resolve().parent", "W=Path("+repr(str(J/'work/enospc4'))+")")
writer=writer.replace(" def getresponse(self):\n  p=Path(os.environ['FAKE_SINK']);p.mkdir(exist_ok=True)",''' def getresponse(self):
  p=Path(os.environ['FAKE_SINK']);p.mkdir(exist_ok=True)
  if self.path.endswith('/2?') and not (p/'failed_once').exists():
   (p/'failed_once').write_text('1')
   raise OSError('E104')
  with (p/'requests.jsonl').open('a') as f:f.write(json.dumps(dict(name=self.name))+'\\n')''')
writer=writer.replace("self.name=hashlib.sha256(path.encode()).hexdigest()", "self.path=path;self.name=hashlib.sha256(path.encode()).hexdigest()")
writer=writer.replace("raise SystemExit(m['main']", "m['upload'].__globals__['time'].sleep=lambda _:None\nraise SystemExit(m['main']")
(D/'writer.py').write_text(writer)

class Archive(unittest.TestCase):
 def test_failed_part_retry_and_idempotence(self):
  c=fixture('retry');(c.root/'t.log').write_bytes(os.urandom(32768));os.environ['FAKE_SINK']=str(D/'sink')
  subprocess.run([sys.executable,'-I','-s','-B',str(K/'b/o.py'),str(c.root),'7','0','--local'],env={**os.environ,'SLURM_JOB_ID':'41'},check=True)
  archive=c.root/'o/o.tar';original=archive.read_bytes();identity=C.sha(archive)
  c.exit_archive();self.assertFalse((c.state/'gcs_o.done').exists())
  receipts=c.spool/'private/sess.json.receipts.jsonl'
  self.assertEqual(len(receipts.read_text().splitlines()),3)
  c.exit_archive();done=c.state/'gcs_o.done';stamp=done.stat().st_mtime_ns
  rows=[json.loads(s) for s in receipts.read_text().splitlines()];self.assertEqual(len(rows),4)
  c.exit_archive();self.assertEqual(done.stat().st_mtime_ns,stamp);self.assertEqual(len(receipts.read_text().splitlines()),4)
  requests=[json.loads(s) for s in (D/'sink/requests.jsonl').read_text().splitlines()]
  self.assertEqual(len(requests),4);self.assertEqual(len({r['name'] for r in requests}),4)
  self.assertEqual(C.read(done)['sha256'],identity);self.assertEqual(archive.read_bytes(),original)
  self.assertEqual((c.target/'o/41/o.tar').read_bytes(),original)
  with tarfile.open(archive) as t:self.assertEqual(json.load(t.extractfile('RESULT.json'))['proof_rc'],7)
  (c.root/'t.log').write_text('changed after completion')
  subprocess.run([sys.executable,'-I','-s','-B',str(K/'b/o.py'),str(c.root),'8','0','--local'],env={**os.environ,'SLURM_JOB_ID':'41'},check=True)
  self.assertEqual(archive.read_bytes(),original)
  (D/'RETRY.json').write_text(json.dumps(dict(status='PASS',first_receipts=3,final_receipts=4,successful_objects=4,duplicate_objects=0,bytes=len(original),sha256=identity,RESULT_inside=True,immutable_on_rerun=True),indent=2)+'\n')
 def test_cap_and_result(self):
  c=fixture('cap')
  for name in ('q.log','rooms.log','h.log','t.log'):
   with (c.root/name).open('wb') as f:f.seek(12_000_000);f.write(b'TAIL')
  with (c.root/'rooms.json').open('wb') as f:f.seek(9_000_001);f.write(b'0')
  subprocess.run([sys.executable,'-I','-s','-B',str(K/'b/o.py'),str(c.root),'0','0','--local'],env={**os.environ,'SLURM_JOB_ID':'41'},check=True)
  archive=c.root/'o/o.tar'
  with tarfile.open(archive) as t:
   members=t.getmembers();self.assertEqual(sum(m.size for m in members if m.name.endswith('.log')),40_000_000)
   self.assertNotIn('rooms.json',t.getnames());self.assertIn('RESULT.json',t.getnames())
   for name in ('q.log','rooms.log','h.log','t.log'):self.assertEqual(t.extractfile(name).read()[-4:],b'TAIL')
  self.assertLessEqual(archive.stat().st_size,50_000_000)
  (D/'CAP.json').write_text(json.dumps(dict(status='PASS',archive_bytes=archive.stat().st_size,cap_bytes=C.CAP,log_bytes=40_000_000,metadata_budget=9_000_000),indent=2)+'\n')
 def test_archive_sessions_required(self):
  c=fixture('sessions');p=c.sessions;v=C.read(p)
  for i in range(4):v.pop(names['objects']['o']+'.j41'+f'.part{i:02d}-of-04')
  C.put(p,v);p.chmod(0o600);(c.spool/'private/sess.json').rename(c.spool/'private/held.json')
  with self.assertRaisesRegex(ValueError,'E101'):C.Copier(c.kit,c.root,'41')

if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Archive))
 (D/'RESULT.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),status='PASS' if r.wasSuccessful() else 'FAIL'),indent=2)+'\n')
 raise SystemExit(not r.wasSuccessful())
