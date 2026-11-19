"""Exercise launch bindings and record source-authenticated statement coverage."""
from pathlib import Path
import ast, datetime, hashlib, json, os, sys, unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build22';T=L/'work/tree_r1'
sys.path[:0]=[str(D),str(L/'work/build21'),str(T),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(D/'proofs/new_tests'))
O=D/'proofs/new_tests';O.mkdir(parents=True,exist_ok=True)
from monitor9 import Monitor
monitor=Monitor(T)
scanner=L/'work/build21/environment21f.py';source=scanner.read_bytes();hits=set()
def trace(frame,event,arg):
    if frame.f_code.co_filename!=str(scanner):return None
    if event=='line':hits.add(frame.f_lineno)
    return trace
sys.settrace(trace)
suite=unittest.defaultTestLoader.loadTestsFromNames(['tests22','direction_test','absence_test','scanner_test','neutral_test'])
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.settrace(None);monitor.save(O)
assert source==scanner.read_bytes()
(O/'SCANNER_COVERAGE.json').write_text(json.dumps(dict(path=str(scanner.relative_to(L)),
    sha256=hashlib.sha256(source).hexdigest(),hits=sorted(hits)),indent=2)+'\n')
(O/'TESTS.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
    successful=result.wasSuccessful(),timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
raise SystemExit(not result.wasSuccessful())
