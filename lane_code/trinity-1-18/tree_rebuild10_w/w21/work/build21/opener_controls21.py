from pathlib import Path
import importlib.util, io, json, sys, unittest
B=Path(__file__).resolve().parent;L=B.parents[1];T=L/'work/tree_r1'
sys.path[:0]=[str(T),str(B)]
import opener_tests21 as tests
before=json.loads((B/'proofs/opener_before/TESTS.json').read_text())
assert not before['successful'] and before['failures']
original=tests.O
source=(T/'student_pilot/r2_openers.py').read_text()
records=[]
for name,old,new,test in [
    ('incomplete_start_context','start(start_context(receipt))','start(receipt)',
     'test_initialize_uses_full_context_and_witness'),
    ('context_identity_not_checked',"identity(cfg) != receipt.get('config_sha256')",'False',
     'test_context_identity_and_missing_refusals'),
]:
    assert old in source
    p=B/'mutant/r2_openers.py';p.parent.mkdir(exist_ok=True)
    p.write_text(source.replace(old,new,1))
    spec=importlib.util.spec_from_file_location('student_pilot.mutant_openers',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    tests.O=module
    stream=io.StringIO()
    try:result=unittest.TextTestRunner(stream=stream).run(unittest.TestSuite([tests.Opener21(test)]))
    finally:tests.O=original
    assert not result.wasSuccessful(),name
    records.append(dict(mutation=name,caught=True,test=test,log=stream.getvalue()))
out=B/'proofs/opener_controls';out.mkdir(exist_ok=True)
(out/'RESULT.json').write_text(json.dumps(dict(before_fails=True,mutations=records),indent=2))
print('Both opener mutations refused; failing-before test retained.')
