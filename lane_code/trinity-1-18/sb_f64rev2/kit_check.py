import hashlib, importlib.util, json, os, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
KIT=ROOT.parent/'sb_f64fix/kit'
tempfile.tempdir=str(ROOT/'tmp')
sys.path[:0]=[os.environ['F64_TREE'], str(KIT/'scripts'),str(KIT/'read')]
reads={str(Path(__file__)),str(ROOT/'run_cpu.sh')}
def guard(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute()
        if (args[2] or 0)&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            if not p.is_relative_to(ROOT): raise RuntimeError('write outside workspace: '+str(p))
        elif str(p).startswith('/scratch/jjyeung/orch_n30/'):
            reads.add(str(p))
    if event in ('os.remove','os.rmdir'):
        raise RuntimeError('retain outputs: '+str(args))
sys.addaudithook(guard)
class RetainedDirectory:
    def __init__(self,suffix=None,prefix=None,dir=None,**kw): self.name=tempfile.mkdtemp(suffix=suffix,prefix=prefix,dir=str(ROOT/'tmp'))
    def __enter__(self): return self.name
    def __exit__(self,*args): return False
    def cleanup(self): pass
tempfile.TemporaryDirectory=RetainedDirectory
import torch
torch.set_num_threads(8)
suite=unittest.TestSuite()
for name in ['test_f64_layout','test_nest_store','test_token_audit','test_f64_fix']:
    spec=importlib.util.spec_from_file_location(name,KIT/'tests'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(mod))
result=unittest.TextTestRunner(verbosity=2).run(suite)
provenance={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(reads) if Path(p).is_file() and not Path(p).is_relative_to(ROOT/'tmp')}
value=dict(command='bash run_cpu.sh kit_check.py',input_sha256=provenance,tests=result.testsRun,failures=[(str(t),m) for t,m in result.failures],errors=[(str(t),m) for t,m in result.errors],skipped=[(str(t),m) for t,m in result.skipped])
(ROOT/'out/kit_review.json').write_text(json.dumps(value,indent=2)+'\n')
