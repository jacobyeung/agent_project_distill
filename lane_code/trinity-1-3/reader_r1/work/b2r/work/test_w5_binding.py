import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W/'out';B=W.parent/'b1g/out/src'
class Comparison(unittest.TestCase):
 def test_all_36_native_frames_digests_and_type_settings(self):
  root=Path(tempfile.mkdtemp(prefix='w5_binding_',dir=W/'work/tmp'));values=[]
  for name,src in [('w5',B),('w6',O/'src')]:
   dest=root/name
   r=subprocess.run([sys.executable,'-B',str(W/'work/binding_snapshot.py'),str(src),str(dest)],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
   self.assertEqual(r.returncode,0,r.stdout+r.stderr);values.append(json.loads((dest/'SNAPSHOT.json').read_text()))
  a,b=values
  self.assertEqual(len(a['rows']),36);self.assertEqual(a['rows'],b['rows']);self.assertEqual(a['records'],b['records'])
  self.assertEqual(a['types'],b['types']);self.assertEqual(a['policy'],b['policy'])
  self.assertEqual(b['durable_types'],['room_size_estimation'])
  proof=dict(passed=True,rows=36,source_w5=str(B),source_w6=str(O/'src'),root=str(root),
   equal=['native task','resolved anchor and dense paths','pinned frame SHA256','indices and slots','mapping digests','effective type selection','settings','finished journal type'],
   digest_scope='Pinned metadata comparison; real dev-S1 image bytes remain Orchard-only.',
   durable_types_w5=a['durable_types'],durable_types_w6=b['durable_types'],
   note='W6 explicitly persists the effective type list; both sources select and journal the same 36 room rows.')
  (O/'W5_BINDING_EQUIVALENCE.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
