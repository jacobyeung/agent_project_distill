"""Production native worker and merger driven by recorded CPU replay outputs."""
import json,sys,types
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
import native_routed as native
from routing import CP1_SHA,PROTOCOL
from test_routing import table
from evalpath.items import sha256

class Pipeline(unittest.TestCase):
 def test_worker_shards_resume_and_strict_merge(self):
  rows=[json.loads(x) for x in (ROOT/'inputs/replay_generations.jsonl').read_text().splitlines()]
  tasks=[{k:r[k] for k in ('benchmark','example_id','question_type','ground_truth','options','question','scene_name')} for r in rows]
  directory=ROOT/'checks/native_pipeline';directory.mkdir(exist_ok=True)
  # Keep each invocation independently replayable without removing old journals.
  import tempfile
  directory=Path(tempfile.mkdtemp(dir=directory))
  policy=table();policy['routes'][tasks[0]['question_type']]=dict(action='routed',ci95=[.01,.1])
  table_path=directory/'table.json';table_path.write_text(json.dumps(policy))
  cfg=dict(until='2999-01-01T00:00:00Z',binding='fixture',gpus=2,output=str(directory/'out'),datasets=[],roots={},models={'cp1m200':{'sha256':CP1_SHA},'base':{'path':'/no-weights'}},
    cells=[dict(model='cp1m200',layout='duplicate',frames=32,benchmarks=['devrows'])],
    routing=dict(table=dict(path=str(table_path),sha256=sha256(table_path)),cfg={},trainer={}))
  path=directory/'cfg.json';path.write_text(json.dumps(cfg))
  import torch
  seen=[];lookup={r['example_id']:r for r in rows}
  def fake_prompt(p,row,cfg,kind):return dict(input_ids=torch.ones((1,3),dtype=torch.int64),qid=row['qid'],video_grid_thw=torch.tensor([[32,2,2]]))
  def generate(model,p,batch,*args):
   r=lookup[batch['qid']];seen.append(r['example_id'])
   return dict(text=r['raw_generation'],generated_tokens=r['output_tokens'],finish=r['finish_reason'],calls=[])
  trainer=types.ModuleType('student_pilot.carrier_c1_run');trainer.move=lambda x,d:x
  parent=types.ModuleType('student_pilot');parent.carrier_c1_run=trainer
  with patch.dict(sys.modules,{'student_pilot':parent,'student_pilot.carrier_c1_run':trainer}), \
       patch.object(native,'selected_tasks',return_value=tasks), \
       patch.object(native,'row_from_cache',side_effect=lambda t,*a:({'qid':t['example_id']},{})), \
       patch.object(native,'assert_prompt_equal'), \
       patch('evalpath.runtime.load_model',return_value=(object(),object(),{'cpu_replay':True})), \
       patch('evalpath.runtime.prompt_batch',side_effect=fake_prompt), \
       patch('evalpath.runtime.generate',side_effect=generate), \
       patch('native_direct.native_generate',side_effect=generate), \
       patch('evalpath.routed_parity.run_suite',return_value={'pass':True,'cpu_replay':True}):
   for rank in range(2):native.worker(str(path),str(directory),0,rank,'fixture','replay')
   summary=native.merge_native(cfg,0,'replay')
   self.assertEqual(summary['benchmarks']['devrows']['completed'],12)
   self.assertEqual(summary['benchmarks']['devrows']['numbers_status'],'eligible')
   self.assertEqual(len(seen),12)
   for rank in range(2):native.worker(str(path),str(directory),0,rank,'fixture','resume')
   self.assertEqual(len(seen),12)
   self.assertEqual(native.merge_native(cfg,0,'resume')['benchmarks']['devrows']['completed'],12)
   # Reuse authenticated direct answers and generate only routed items.
   source=directory/'direct.jsonl'
   direct=[dict(r,checkpoint_sha256=CP1_SHA,layout='duplicate',frames=32,route_action='direct') for r in rows]
   source.write_text(''.join(json.dumps(r)+'\n' for r in direct))
   reuse_cfg={**cfg,'output':str(directory/'reuse'), 'routing':{**cfg['routing'],'direct_answers':{'devrows':dict(path=str(source),sha256=sha256(source))}}}
   reuse_path=directory/'reuse.json';reuse_path.write_text(json.dumps(reuse_cfg));seen.clear()
   for rank in range(2):native.worker(str(reuse_path),str(directory),0,rank,'fixture','reuse')
   self.assertEqual(len(seen),sum(t['question_type']==tasks[0]['question_type'] for t in tasks))
   reused=native.merge_native(reuse_cfg,0,'reuse')
   self.assertEqual(reused['benchmarks']['devrows']['reused_direct'],len(tasks)-len(seen))
   self.assertEqual(reused['benchmarks']['devrows']['numbers_status'],'eligible')
   # The deadline is checked again between generations, not only at startup.
   deadline_cfg={**cfg,'output':str(directory/'deadline')};dp=directory/'deadline.json';dp.write_text(json.dumps(deadline_cfg));seen.clear()
   calls=[0]
   def expired(_):
    calls[0]+=1
    return calls[0]>=3
   with patch.object(native,'deadline_reached',side_effect=expired):
    native.worker(str(dp),str(directory),0,0,'fixture','deadline')
   self.assertEqual(len(seen),1)
   self.assertEqual(native.merge_native(deadline_cfg,0,'deadline')['benchmarks']['devrows']['numbers_status'],'do not count')
   journal=Path(cfg['output'])/'0/g0.jsonl'
   records=[json.loads(x) for x in journal.read_text().splitlines() if x.strip()]
   records[0]['score']=999
   journal.write_text('\n'.join(json.dumps(r) for r in records)+'\n')
   with self.assertRaisesRegex(ValueError,'score differs'):native.merge_native(cfg,0,'resume')
if __name__=='__main__':unittest.main()
