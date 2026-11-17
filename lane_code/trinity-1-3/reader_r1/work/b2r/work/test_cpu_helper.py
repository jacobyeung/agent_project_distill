"""CPU helper orchestration and fail-closed receipts; namespace/restore are explicit local stubs."""
import copy,io,json,os,sys,tempfile,unittest
from contextlib import ExitStack,redirect_stdout
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src'
sys.path[:0]=[str(O),str(P/'b'),str(P/'tree'),str(P)]
from e2e_reader import parity
from orchard_h10 import common,job
import node_check as N
import tower_sequence as T

class Helper(unittest.TestCase):
 def invoke(self,fault=None):
  base=Path(tempfile.mkdtemp(prefix='helper_',dir=W/'work/tmp'));root=base/'root';root.mkdir();results=base/'results'
  evidence=json.loads((O/'LOCAL_CPU_CHECK.json').read_text());staged=Path(evidence['root'])
  settings=json.loads((staged/'archive_layout.json').read_text()) if (staged/'archive_layout.json').exists() else None
  # Read the exact settings used by the successful local operator rehearsal.
  dirs=sorted(staged.glob('archive_layout_*/settings.json'));settings=json.loads(dirs[-1].read_text())
  S,J,*_=common.template();logical=common.read_config(O/'package')['logical'];events=[]
  fake_j=NS(physical=J.physical,namespace=lambda r:[],environment=lambda r:{},storage_proof=lambda *a,**k:{'local_fixture':True})
  def stage(*a):
   events.append('stage');(root/'a').mkdir()
  def checked(argv,**kwargs):
   dispatch=json.loads(Path(argv[-1]).read_text())
   if dispatch.get('action')==0:
    self.assertEqual(events,['stage']);events.append('restore')
    common.write(J.physical(root,logical+'/d/READY.json'),{'fixture_restore':True})
    common.write(J.physical(root,logical+'/d/settings.json'),settings)
   else:
    self.assertEqual(events,['stage','restore']);events.append('full_reader')
    c=dispatch['config'];c.update(package=str(P),settings=str(J.physical(root,logical+'/d/settings.json')),
      output=str(J.physical(root,logical+'/r')),export=settings['export_dir'],binding=settings['artifact_manifest'],
      export_pin=str(staged/'sj/b01ec87a6f29b/d/6.json'))
    if fault=='reader':raise RuntimeError('injected reader failure')
    result=T.rehearsal(c);T.memory_probe(c)
    if fault=='record':result[0]['full_reader']['records'][0]['record']['complete']=False
    common.write(J.physical(root,logical+'/r/REHEARSAL.json'),result)
  with ExitStack() as stack:
   for stub in [patch.object(N.tempfile,'mkdtemp',return_value=str(root)),patch.object(common,'template',return_value=(S,fake_j)),
     patch.object(common,'install_process_guard',lambda r:None),patch.object(job,'stage',stage),
     patch.object(common,'checked_run',checked),patch.dict(os.environ,SLURM_JOB_ID='123'),
     patch.object(sys,'argv',['5.py','--package',str(O/'package'),'--sequence',str(O/'tower_sequence.py'),'--results',str(results)])]:stack.enter_context(stub)
   with redirect_stdout(io.StringIO()):
    if fault:
     with self.assertRaises((ValueError,RuntimeError)):N.main()
    else:N.main()
  return results,events
 def test_success_publishes_both_finished_records(self):
  results,events=self.invoke();cpu=json.loads((results/'CPU.json').read_text())
  self.assertEqual(events,['stage','restore','full_reader']);self.assertTrue(cpu['passed']);self.assertTrue(cpu['full_reader_passed'])
  self.assertEqual([r['set'] for r in cpu['full_reader']['records']],['dev-S1','R0-dev'])
  self.assertEqual(cpu['full_reader'],json.loads((results/'FULL_READER.json').read_text()))
  common.write(O/'CPU_HELPER_TEST.json',dict(passed=True,results=str(results),events=events,
    local_stubs=['allocation','namespace','storage proof','stage orchestration','export restore'],
    real=['package admission','operator authentication','full-reader rehearsal','receipt validation and publication']))
 def test_reader_exception_publishes_no_pass(self):
  results,_=self.invoke('reader');self.assertFalse((results/'CPU.json').exists())
 def test_unfinished_record_publishes_no_pass(self):
  results,_=self.invoke('record');self.assertFalse((results/'CPU.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
