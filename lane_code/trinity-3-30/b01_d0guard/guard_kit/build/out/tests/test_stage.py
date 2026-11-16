import hashlib,io,json,pathlib,sys,tarfile,unittest,uuid
from types import SimpleNamespace as NS
from unittest.mock import patch
B=pathlib.Path(__file__).resolve().parents[2];K=B/'out/guard_kit'
sys.path[:0]=[str(K),str(K/'reviewed')]
import export_stage as E
import guard_export as G
import guard_core as C
class Stage(unittest.TestCase):
 def setUp(self):
  self.root=B/'work/stage_tests'/uuid.uuid4().hex;self.root.mkdir(parents=True)
 def archive(self,extra=None):
  path=self.root/'export.tar'
  with tarfile.open(path,'w',format=tarfile.USTAR_FORMAT) as t:
   for name,data in [('m200/artifact.json',b'{}'),('m200/heads.pt',b'head fixture'),('m200/full_weights/full_weights.json',b'{}')]:
    m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
   if extra is not None:t.addfile(extra)
  d=dict(object='q8/8865619b/359fcc3c_m200.tar',bytes=path.stat().st_size,sha256=C.sha(path))
  done=self.root/'input.done';done.write_text(d['object']+' '+str(d['bytes'])+' '+d['sha256']+'\n')
  return path,done,d
 def run_stage(self,path,done,d):
  root=self.root/'job';root.mkdir()
  # Unit boundaries: storage path/quota and full tensor checker. Admission code is unchanged.
  with patch.object(E,'writable',side_effect=lambda x:pathlib.Path(x).absolute()),patch.object(E.T,'writable',side_effect=lambda x:pathlib.Path(x).absolute()),patch.object(E.T,'kit_stage',return_value=NS(room=lambda *a:None)),patch.object(E,'run_export_checker',return_value={'status':'VERIFIED','step':200}) as checker:
   result=G.stage(root,path,done,200,d,E)
   self.assertTrue(checker.call_args.args[4])
   return result
 def test_reviewed_source_identical(self):
  source=B.parents[1]/'work/from13/readk/kit/launcher/export_stage.py'
  self.assertEqual(source.read_bytes(),(K/'reviewed/export_stage.py').read_bytes())
 def test_parse_reviewed_equal(self):
  for step in C.STEPS:
   raw=('q8/8865619b/359fcc3c_m'+str(step)+'.tar 42 '+'e'*64+'\n').encode()
   self.assertEqual(C.parse_done(raw,C.RUN,step),E.parse_done(raw,C.RUN,step))
 def test_exact_archive(self):
  result=self.run_stage(*self.archive());self.assertEqual(result['status'],'complete');self.assertEqual(result['checker_mode'],'full')
 def test_changed_done_after_plan(self):
  path,done,d=self.archive();d=dict(d,sha256='f'*64)
  with self.assertRaisesRegex(ValueError,'changed after'):self.run_stage(path,done,d)
 def test_hard_link_refused(self):
  m=tarfile.TarInfo('m200/linked');m.type=tarfile.LNKTYPE;m.linkname='m200/heads.pt'
  with self.assertRaisesRegex(ValueError,'Unsafe member'):self.run_stage(*self.archive(m))
 def test_symlink_refused(self):
  m=tarfile.TarInfo('m200/linked');m.type=tarfile.SYMTYPE;m.linkname='heads.pt'
  with self.assertRaisesRegex(ValueError,'Unsafe member'):self.run_stage(*self.archive(m))
 def test_other_step_member_refused(self):
  m=tarfile.TarInfo('m400/heads.pt')
  with self.assertRaisesRegex(ValueError,'Unsafe member'):self.run_stage(*self.archive(m))
 def test_traversal_refused(self):
  m=tarfile.TarInfo('m200/../outside')
  with self.assertRaisesRegex(ValueError,'Unsafe member'):self.run_stage(*self.archive(m))
 def test_duplicate_member_refused(self):
  m=tarfile.TarInfo('m200/heads.pt')
  with self.assertRaisesRegex(ValueError,'Duplicate tar member'):self.run_stage(*self.archive(m))
 def test_wrong_digest_before_extract(self):
  path,done,d=self.archive();path.write_bytes(b'x'+path.read_bytes()[1:])
  with self.assertRaisesRegex(ValueError,'digest'):self.run_stage(path,done,d)
  self.assertFalse((self.root/'job/exports').exists())
if __name__=='__main__':unittest.main(verbosity=2)
