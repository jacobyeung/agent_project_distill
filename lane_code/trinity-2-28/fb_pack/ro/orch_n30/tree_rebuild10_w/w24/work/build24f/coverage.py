from pathlib import Path
import ast,difflib,importlib.util,json,sys,trace,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';sys.path.insert(0,str(D))
import persistence_tests as T
T.D=D/'coverage';T.D.mkdir(exist_ok=True)
t=trace.Trace(count=True,trace=False)
r=t.runfunc(unittest.TextTestRunner(verbosity=1).run,unittest.defaultTestLoader.loadTestsFromTestCase(T.Persistence24F))
p=L/'work/tree_r1/launch_r2/persistence.py';old=(L/'attic/build24f/persistence.py').read_text().splitlines();new=p.read_text().splitlines();changed=set()
for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new).get_opcodes():
 if tag in ('insert','replace'):changed.update(range(c+1,d+1))
statements={x.lineno for x in ast.walk(ast.parse(p.read_text())) if isinstance(x,ast.stmt)}&changed
hit={line for (filename,line),count in t.results().counts.items() if Path(filename)==p and count}
v=dict(tests_passed=r.wasSuccessful(),changed_statement_lines=sorted(statements),covered=sorted(statements&hit),uncovered=sorted(statements-hit))
(D/'COVERAGE.json').write_text(json.dumps(v,indent=2)+'\n');print(v)
assert r.wasSuccessful() and not v['uncovered']
