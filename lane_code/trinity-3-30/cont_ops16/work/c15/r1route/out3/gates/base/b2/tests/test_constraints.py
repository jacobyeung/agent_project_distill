"""W5 constraints adapted to the sealed room-only package."""
import ast,copy,hashlib,json,sys,tarfile,unittest
from pathlib import Path
O=Path(__file__).resolve().parents[1];P=O/'src';B=Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/bases/b1')
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P),str(O)]
import e2e_reader
from orchard_h10.common import canonical,sha,read_config,opaque,submit_argv
from orchard_h10.job import check_inputs,verify_config
class Constraints(unittest.TestCase):
 def setUp(self):self.cfg=read_config(O/'package');self.inputs=json.loads((O/'inputs_tower.json').read_text())
 def test_plan_admission(self):verify_config(self.cfg);check_inputs(self.inputs,self.cfg,package=O/'package')
 def test_export_and_g3t_pins(self):
  old=json.loads((B/'inputs_tower.json').read_text());self.assertEqual(self.inputs['files'],old['files']);self.assertEqual((O/'export_544.json').read_bytes(),(B/'export_544.json').read_bytes())
  for k in ('artifact','heads','full_weights','g3t_weights','sam_checkpoint','selector_weights'):
   v=copy.deepcopy(self.inputs);v['files'][k]['sha256']='0'*64
   with self.assertRaises(ValueError):check_inputs(v,self.cfg,package=O/'package')
 def test_export_size_guards(self):
  for k in ('artifact','heads','full_weights'):
   v=copy.deepcopy(self.inputs);v['files'][k]['bytes']+=1
   with self.assertRaises(ValueError):check_inputs(v,self.cfg,package=O/'package')
 def test_single_room_archive_destination(self):
  a=self.inputs['archives'][-1];self.assertEqual(a['destination'],'sj/b01ec87a6f29b/d/f')
  for dest in ('../x','sj/b01ec87a6f29b/p','sj/b01ec87a6f29b/d/unknown','/tmp/x'):
   v=copy.deepcopy(self.inputs);v['archives'][-1]['destination']=dest
   with self.assertRaises(ValueError):check_inputs(v,self.cfg,package=O/'package')
 def test_payload_pins(self):
  with tarfile.open(O/'0.tgz') as t:
   data={m.name:t.extractfile(m).read() for m in t}
  for n,pin in self.cfg['payload_pins'].items():self.assertEqual(dict(bytes=len(data[n]),sha256=hashlib.sha256(data[n]).hexdigest()),pin)
 def test_unchanged_reader_and_scorers(self):
  for folder in ('b/e2e_reader','b/parity_kit','b/heads','tree'):
   for p in (B/'src'/folder).rglob('*'):
    if p.is_file() and p.suffix!='.pyc':self.assertEqual(p.read_bytes(),(P/p.relative_to(B/'src')).read_bytes())
  self.assertEqual((B/'src/h1eval/scorers.py').read_bytes(),(P/'h1eval/scorers.py').read_bytes())
 def test_return_path_and_caps(self):
  self.assertEqual(self.cfg['pool'],'/project/community/jjyeung/okh7/ae71c903')
  for n in ('chain_save.py','return_io.py','stdout_transfer.py','TRANSPORT.json'):
   self.assertEqual((P/'orchard_h10/vendor'/n).read_bytes(),(B/'src/orchard_h10/vendor'/n).read_bytes())
 def test_opaque_surface_and_walltime(self):
  token=(O/'TOKEN').read_text().strip();self.assertRegex(token,'^[a-f][0-9a-f]{12}$')
  for p in (B.parent/'PROMPT.md',B/'REPORT.md'):self.assertNotIn(token,p.read_text())
  opaque(submit_argv(token,1,'02:30:00'));opaque([(O/'package/BATCH.sh').read_text()])
  for a in self.inputs['archives']:opaque([p['path'] for p in a['parts']])
  self.assertEqual(self.cfg['budget_gpu_seconds'],9000)
 def test_settings_and_types(self):
  self.assertEqual(self.inputs['types'],['room_size_estimation']);self.assertEqual(self.cfg['perception_memo'],'on');self.assertEqual(self.cfg['perception_memo_modules'],['g3t']);self.assertEqual(self.cfg['perception_memo_verify_ids'],[])
if __name__=='__main__':unittest.main(verbosity=2)
