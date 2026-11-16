import importlib.util,json,os,pathlib,sys,unittest
B=pathlib.Path(__file__).resolve().parents[1];A=B.parents[1];W=A/'work/from113/work';ROOT=B/'out/guard_kit/sj/orch_cd/evalx/work/milestone'
sys.path[:0]=[str(W/'np226'),str(W/'pyextra'),str(W/'tree'),str(ROOT/'orchard_native'),str(ROOT/'native/out2'),str(ROOT)]
os.environ['LEGS1_TREE']=str(W/'tree')
suite=unittest.TestSuite();adapt=[]
for name in ('test_core','test_guard'):
 source=A/'work/from113/builds/02_c8r/out/tests'/(name+'.py')
 text=source.read_text().replace("W=B.parents[1]/'work'",'W=Path('+repr(str(W))+')').replace("ROOT=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'",'ROOT=Path('+repr(str(ROOT))+')')
 target=B/'out/tests'/(name+'.py');target.write_text(text)
 spec=importlib.util.spec_from_file_location(name,target);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(m));adapt.append(dict(source=str(source),copy=str(target),changes='Only input and code root constants; test bodies unchanged'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
(B/'out/C8R_TESTS.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),adaptations=adapt),indent=2)+'\n')
sys.exit(not result.wasSuccessful())
