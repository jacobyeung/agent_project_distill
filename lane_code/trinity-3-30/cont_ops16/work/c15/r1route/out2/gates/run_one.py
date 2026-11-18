import importlib.util,json,sys,unittest,os
from pathlib import Path
path=Path(sys.argv[1]).resolve();target=Path(sys.argv[2]).resolve();arg=sys.argv[3:]
sys.argv=[str(path)]+arg
sys.path.insert(0,str(path.parent))
records=[]
class Result(unittest.TextTestResult):
 def addSuccess(self,t):super().addSuccess(t);records.append(dict(test=t.id(),status='passed'))
 def addError(self,t,e):super().addError(t,e);records.append(dict(test=t.id(),status='blocked' if issubclass(e[0],FileNotFoundError) else 'error',detail=self._exc_info_to_string(e,t)))
 def addFailure(self,t,e):super().addFailure(t,e);records.append(dict(test=t.id(),status='failed',detail=self._exc_info_to_string(e,t)))
 def addSkip(self,t,r):super().addSkip(t,r);records.append(dict(test=t.id(),status='blocked',detail=r))
try:
 spec=importlib.util.spec_from_file_location('suite',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 suite=unittest.defaultTestLoader.loadTestsFromModule(m)
 r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
except Exception as e:
 import traceback
 records.append(dict(test=str(path),status='blocked' if isinstance(e,FileNotFoundError) else 'error',detail=traceback.format_exc()))
counts={s:sum(v['status']==s for v in records) for s in ('passed','failed','error','blocked')}
target.write_text(json.dumps(dict(suite=str(path),records=records,counts=counts),indent=2)+'\n')
print(counts)
