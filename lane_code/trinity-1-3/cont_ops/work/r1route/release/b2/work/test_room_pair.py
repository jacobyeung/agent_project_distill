import copy,json,sys,tempfile,unittest,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W;P=O/'src'
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P),str(O)]
import e2e_reader
import room_pair as R,tower_sequence as T
from h1eval.items import load_manifest,sha
from h1eval.cli import code_hash
from h1eval.h10.parity_adapter import reader_code_hash
from h1eval.h10 import parity_adapter
from orchard_h10.common import write,canonical
class Pair(unittest.TestCase):
 def make(self):
  root=Path(tempfile.mkdtemp(prefix='pair_',dir=W/'work/tmp'));m=load_manifest(P/'items/room134.json');public=json.loads((O/'package/0.json').read_text());inp=json.loads((O/'inputs_tower.json').read_text())
  write(root/'metadata/IDENTITY.json',dict(plan=public['plan_sha256'],inputs=canonical({k:v for k,v in inp.items() if k!='resume'}),operator_sha256=sha(O/'tower_sequence.py'),cards=1,reads=T.descriptors(P),schedule=T.SCHEDULE))
  d=root/'metadata/reads/0/metadata/journals/4/0';d.mkdir(parents=True);write(d/'STARTED.json',{'type':'room_size_estimation'})
  settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,types=['room_size_estimation'])
  binding=dict(**settings,item_set_sha256=m['item_set_sha256'],items_sha256=sha(P/'items/room134.json'),reader_sha256=code_hash(P/'b/e2e_reader'),evaluator_code_sha256=code_hash(),parity_code_sha256=reader_code_hash(P/'b'),maker_sha256=sha(Path(parity_adapter.__file__)),arms=['tower'],modes=[{'name':'none'}],lineage='SFT',step=544,count=134,ids=[r['id'] for r in m['items']],settings_sha256=canonical(settings),export_sha256='fixture',artifact_manifest_sha256='fixture',mapping_sha256='fixture',fixture=True)
  write(d/'environment.json',dict(binding=binding,settings=settings))
  rows=[]
  for i,item in enumerate(m['items']):
   output=dict(text=f"<think></think><answer>{item['ground_truth']}</answer>",finish='eos',calls={'records':[]})
   if i==0:output.update(finish='max_calls',strict_no_answer=True)
   if i==1:output.update(text='unparsed',calls={'records':[dict(call='<move bad>',family='move',served=True,response='error: malformed_call')]})
   rows.append(dict(id=item['id'],room_key=item['room_key'],type='room_size_estimation',arm='tower',mode='none',intervention={'name':'none'},complete=True,output=output,seconds=1.))
  (d/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
  return root,d,rows
 def test_synthetic_cli_and_sets(self):
  root,d,rows=self.make();result=R.score_return(root,True)
  self.assertEqual({k:v['expected'] for k,v in result['sets'].items()},{'dev-S1':36,'R0-dev':98,'all':134})
  self.assertAlmostEqual(result['sets']['all']['mra'],132/134);self.assertEqual(result['sets']['all']['capped_reads'],1);self.assertEqual(result['sets']['all']['malformed_calls'],1)
  self.assertEqual(len(result['per_item']),134)
  with self.assertRaisesRegex(ValueError,'Fixture'):R.score_return(root)
  p=subprocess.run([sys.executable,'-B',str(O/'room_pair.py'),'--return-root',str(root),'--out',str(O/'synthetic_scores'),'--allow-fixture'],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr);write(O/'SCORING_TEST.json',dict(passed=True,root=str(root),sets=result['sets'],synthetic=True))
 def test_bad_binding_duplicate_and_partial(self):
  root,d,rows=self.make();env=json.loads((d/'environment.json').read_text())
  for field,val in [('stage1_select_rule','null_argmax'),('perception_memo','off'),('perception_memo_modules',[]),('perception_memo_verify_ids',['x']),('types',['object_abs_distance']),('reader_sha256','0'*64),('item_set_sha256','0'*64)]:
   bad=copy.deepcopy(env);bad['binding'][field]=val;write(d/'environment.json',bad)
   with self.assertRaisesRegex(ValueError,'binding differs'):R.score_return(root,True)
  write(d/'environment.json',env)
  with (d/'items.jsonl').open('a') as f:f.write(json.dumps(rows[0])+'\n')
  with self.assertRaisesRegex(ValueError,'Duplicate'):R.score_return(root,True)
  (d/'items.jsonl').write_text(json.dumps(rows[0])+'\n');r=R.score_return(root,True);self.assertEqual(r['sets']['all']['completed'],1);self.assertEqual(len(r['sets']['all']['missing']),133)
if __name__=='__main__':unittest.main(verbosity=2)
