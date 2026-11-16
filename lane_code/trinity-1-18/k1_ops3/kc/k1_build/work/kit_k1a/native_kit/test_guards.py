"""CPU tests of plan partitioning and supervisor behavior; no subprocess or signal is issued."""
import sys,unittest,uuid,json,trace
from pathlib import Path
from unittest.mock import patch,MagicMock
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));counts={}
def local(frame,event,arg):
 if event=='line':counts.setdefault(frame.f_code.co_filename,set()).add(frame.f_lineno)
 return local
def tracer(frame,event,arg):
 if event=='call' and frame.f_code.co_filename in TARGETS:return local
 return None
TARGETS={str(HERE/n) for n in ['watchdog.py','shard.py','build_manifest.py']};sys.settrace(tracer)
import watchdog,shard,build_manifest
ROOT=HERE.parent/'work'/('guards_'+uuid.uuid4().hex[:8]);ROOT.mkdir()
class Guards(unittest.TestCase):
 def test_partitions_are_disjoint_complete(self):
  m=dict(captures=[dict(canonical=str(i)) for i in range(17)],synthetic=False)
  parts=shard.partition(m,8);ids=[c['canonical'] for _,p in parts for c in p['captures']]
  self.assertEqual(len(ids),17);self.assertEqual(len(set(ids)),17)
  self.assertEqual(max(len(p['captures']) for _,p in parts),3)
 def test_partition_limits(self):
  for n in [0,17]:
   with self.assertRaises(ValueError):shard.partition({},n)
 def args(self,name):return ['watchdog','--python','unused','--manifest','unused','--out',str(ROOT/name),'--stall-seconds','1']
 def test_supervisor_success(self):
  child=MagicMock();child.poll.return_value=0;child.returncode=0
  with patch.object(sys,'argv',self.args('success')),patch.object(watchdog.subprocess,'Popen',return_value=child) as p:
   self.assertEqual(watchdog.main(),0);self.assertTrue(p.call_args.kwargs['start_new_session'])
 def test_supervisor_nonzero_no_retry(self):
  child=MagicMock();child.poll.return_value=2;child.returncode=2
  with patch.object(sys,'argv',self.args('failure')),patch.object(watchdog.subprocess,'Popen',return_value=child) as p:
   self.assertEqual(watchdog.main(),2);self.assertEqual(p.call_count,1)
  self.assertFalse(json.loads((ROOT/'failure/HALTED.json').read_text())['automatic_retry'])
 def test_stall_signals_only_owned_group(self):
  child=MagicMock();child.poll.return_value=None;child.pid=987654
  with patch.object(sys,'argv',self.args('stall')),patch.object(watchdog.subprocess,'Popen',return_value=child),patch.object(watchdog.time,'monotonic',side_effect=[0,10]),patch.object(watchdog.os,'killpg') as signal:
   self.assertEqual(watchdog.main(),3);signal.assert_called_once_with(987654,watchdog.signal.SIGTERM)
 def test_halted_refuses_launch(self):
  root=ROOT/'halted';root.mkdir();(root/'HALTED.json').write_text('{}')
  with patch.object(sys,'argv',self.args('halted')),patch.object(watchdog.subprocess,'Popen') as p:
   with self.assertRaises(ValueError):watchdog.main()
   p.assert_not_called()
 def test_builder_refuses_duplicate_admitted_ids(self):
  import bindings as B
  r=ROOT/'registry.json';r.write_text('{}');a=ROOT/'admitted.json';a.write_text('["same","same"]')
  with self.assertRaises(ValueError):build_manifest.build(dict(scene_registry=B.pin(r),admitted_ids=B.pin(a)))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards));sys.settrace(None);cov={}
 for p in TARGETS:
  lines=set(trace._find_executable_linenos(p));hit=counts.get(p,set())&lines
  cov[Path(p).name]=dict(executable_lines=len(lines),covered_lines=len(hit),coverage_pct=round(len(hit)/len(lines)*100,2),missing=sorted(lines-hit))
 (HERE.parent/'out/GUARD_COVERAGE.json').write_text(json.dumps(dict(tests=result.testsRun,success=result.wasSuccessful(),coverage=cov),indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
