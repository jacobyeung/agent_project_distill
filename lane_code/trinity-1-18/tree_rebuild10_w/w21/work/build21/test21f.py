"""Run scanner controls with retained outputs and changed-statement coverage."""
from pathlib import Path
import ast,difflib,hashlib,json,shutil,sys,unittest
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21f'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
paths=[B/'naming21.py',B/'environment21f.py'];hits={str(p):set() for p in paths}
sources={p:p.read_text() for p in paths}
scanner_only='--scanner-only' in sys.argv
if scanner_only:
    for name in ('TESTS.json','COVERAGE.json'):
        target=D/('REGRESSION_'+name)
        assert not target.exists()
        shutil.copyfile(D/name,target)
naming_path=str(B/'naming21.py')
def trace(frame,event,arg):
    path=frame.f_code.co_filename
    if path not in hits:return None
    if path==naming_path and frame.f_code.co_name not in ('<module>','scan_decoded','scan_python_environment'):
        return None
    if event=='line':hits[path].add(frame.f_lineno)
    return trace
def size():
    return sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
class Result(unittest.TextTestResult):
    sizes=[]
    def startTest(self,test):
        n=size();assert n<=200_000_000
        self.sizes.append(dict(test=str(test),phase='before',bytes=n));super().startTest(test)
    def stopTest(self,test):
        n=size();assert n<=200_000_000
        self.sizes.append(dict(test=str(test),phase='after',bytes=n));super().stopTest(test)
sys.settrace(trace)
import naming_test21c,naming_test21d
for module,field,name in ((naming_test21c,'C','regression21c'),(naming_test21d,'D','regression21d')):
    output=D/name;(output/'proofs').mkdir(parents=True,exist_ok=True);setattr(module,field,output)
tests=['naming_test21f.Naming21f']
regressions = ['naming_test21c.Naming21c.'+name for name in (
    'test_base_fails_exact_name','test_p_files_mutation','test_map_keys_and_relative_values',
    'test_nested_capsule_and_unknown_map','test_capsule_authentication','test_result_archive_member_literal',
    'test_invalid_source_inventory')]
regressions += ['naming_test21d.Naming21d.'+name for name in unittest.defaultTestLoader.getTestCaseNames(naming_test21d.Naming21d)
    if name not in ('test_final_kit','test_python_environment_forms')]
if not scanner_only:tests+=regressions
suite=unittest.defaultTestLoader.loadTestsFromNames(tests)
result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
sys.settrace(None)
coverage={}
for p in paths:
    assert p.read_text()==sources[p],str(p)+' changed during tests'
    statements={n.lineno for n in ast.walk(ast.parse(sources[p])) if isinstance(n,ast.stmt)}
    prior=L/'attic/build21f'/p.name
    old=prior.read_text().splitlines() if prior.exists() else []
    changed=set()
    for tag,i,j,a,b in difflib.SequenceMatcher(a=old,b=sources[p].splitlines()).get_opcodes():
        if tag!='equal':changed.update(range(a+1,b+1))
    changed_statements=statements & changed
    covered=statements & hits[str(p)]
    coverage[str(p.relative_to(L))]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        statements=len(statements),covered=len(covered),hits=sorted(hits[str(p)]),missing=sorted(statements-covered),
        changed_statements=len(changed_statements),changed_covered=len(changed_statements & covered),
        changed_missing=sorted(changed_statements-covered))
(D/'COVERAGE.json').write_text(json.dumps(coverage,indent=2)+'\n')
(D/'TESTS.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
    successful=result.wasSuccessful(),selection=tests,storage=result.sizes),indent=2)+'\n')
raise SystemExit(not result.wasSuccessful())
