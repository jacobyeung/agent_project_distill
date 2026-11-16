"""Regression: ON changes the sensor keypoint session's provider audit."""
import json,subprocess,sys,unittest
from pathlib import Path
W=Path(__file__).resolve().parent;L=W.parents[1]

def worker(arm):
    tree=L/'work/trees'/('r5_base' if arm=='base' else 'r5_applied')
    sys.path[:0]=[str(tree),str(tree/'generator/derivgen_v7'),str(L/'work/tests_r5')]
    if arm=='on':
        from trace_format.contracts import contract_epoch
        ctx=contract_epoch(True);ctx.__enter__()
    from fixtures_contracts import fixture,masks
    from student_pilot import ground_lifting
    from derivgen.ground_v313 import Session
    session=Session(ground_lifting,fixture('landscape')[1](),None,
        instances=lambda n:[dict(instance_id='1',masks=masks(n).masks,prob=[1.]*32)],
        multi_instance=False,keypoint_calls=True,geometry_mode='sensor')
    session.execute('<ground obj="chair">')
    print(json.dumps(dict(provider=session.box_provider_id,event=session.events[0])))

class ProviderContract(unittest.TestCase):
    def test_defined_heading_provider_audit_is_stable(self):
        values={}
        for arm in ('base','on'):
            p=subprocess.run([sys.executable,'-I','-s','-B',__file__,'worker',arm],capture_output=True,text=True,check=True)
            values[arm]=json.loads(p.stdout)
        (W/'provider_reproduction.json').write_text(json.dumps(dict(source_path=__file__,arms=values),indent=2))
        self.assertEqual(values['base']['event']['response'],values['on']['event']['response'])
        self.assertEqual(values['base']['event']['audit'],values['on']['event']['audit'],
            'No named contract permits changing the sensor provider on a defined-heading keypoint row')

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':worker(sys.argv[2])
    else:unittest.main()
