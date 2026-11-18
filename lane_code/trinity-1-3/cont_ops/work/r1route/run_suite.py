from pathlib import Path
import importlib.util,json,sys,unittest
path=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(path.parent))
spec=importlib.util.spec_from_file_location('suite',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
if path.parent.parent.name=='b2':
    if hasattr(module,'PROD'):module.PROD=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1g/out/src')
    if hasattr(module,'B'):module.B=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1g/out')
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
summary=dict(suite=str(path),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped))
Path(sys.argv[2]).write_text(json.dumps(summary,indent=2)+'\n')
sys.exit(not result.wasSuccessful())
