"""Regression: a served bare ground must retain OFF/base parity."""
import json,os,subprocess,sys,unittest
from pathlib import Path
W=Path(__file__).resolve().parent;L=W.parents[1]

def worker(arm):
    tree=L/'work/trees'/('r5_base' if arm=='base' else 'r5_applied')
    sys.path[:0]=[str(tree),str(tree/'generator/derivgen_v7'),str(L/'work/tests_r5')]
    if arm!='base':
        from trace_format.contracts import contract_epoch
        ctx=contract_epoch(arm=='on');ctx.__enter__()
    from fixtures_contracts import fixture,masks
    from derivgen.ground_v312 import Session,render
    from student_pilot import ground_lifting
    geometry=fixture('landscape')[1]()
    session=Session(ground_lifting,geometry,lambda name:(masks(name).masks,[1.]*32))
    item=dict(qid='bare-ground-regression',type='object_abs_distance',question='How far is the chair from the table?',options=[],roles=dict(a='chair',b='table'))
    try:
        row=render(item,session,lambda s:len(s.split()))
        from derivgen.calculator import _json
        result=dict(status='rendered',row=row,lifted=session.objects,registered=_json(session.registry._points))
    except Exception as exc:
        result=dict(status='error',error_type=type(exc).__name__,error=str(exc))
    print(json.dumps(result,sort_keys=True))

class OffParity(unittest.TestCase):
    def test_bare_ground_matches_base(self):
        values={}
        for arm in ('base','off','on'):
            p=subprocess.run([sys.executable,'-I','-s','-B',__file__,'worker',arm],text=True,capture_output=True,check=True)
            values[arm]=json.loads(p.stdout)
        (W/'off_parity_reproduction.json').write_text(json.dumps(dict(source_path=__file__,arms=values),indent=2))
        self.assertEqual(values['base']['status'],'rendered')
        self.assertEqual(values['base'],values['off'],'OFF must render the same complete row as base')

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':worker(sys.argv[2])
    else:unittest.main()
