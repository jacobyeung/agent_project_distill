from pathlib import Path
import sys,os,unittest,json,types
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4v';sys.path.insert(0,str(L/'work/tree_r1c'))
package=types.ModuleType('tests');package.__path__=[str(L/'work/tree_r1c/tests')];sys.modules['tests']=package
os.environ['R2_FIXTURES']='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/fixtures'
os.environ['R2_LANE_ROOT']='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21'
os.environ['R2_PROOFS']=str(D/'targeted_proofs');Path(os.environ['R2_PROOFS']).mkdir(exist_ok=True)
names=['tests.test_r2_build9fix.Fixes.'+n for n in ('test_status_authentication_and_whitespace','test_M02_interspan_status','test_extent_pin_and_reader','test_scene_gate')]+['tests.test_r1_build13']
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
r=unittest.TextTestRunner(verbosity=2).run(suite)
(D/'TREE_TESTS.json').write_text(json.dumps(dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,failures=[str(x) for x in r.failures],errors=[str(x) for x in r.errors]),indent=2)+'\n')
raise SystemExit(not r.wasSuccessful())
