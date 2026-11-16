"""Install the immutable offline guard before importing any tests or kit module."""
from pathlib import Path
import os
import sys
import uuid
import json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'))
import offline_guard
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import pytest
visited=set()
paired_path=str(ROOT/'paired.py')
def record(frame,event,arg):
    if frame.f_code.co_filename==paired_path and event=='line':visited.add(frame.f_lineno)
    return record if frame.f_code.co_filename==paired_path else None
class LineEvidence:
    @pytest.hookimpl(wrapper=True,tryfirst=True)
    def pytest_runtest_call(self,item):
        old=sys.gettrace()
        if item.path.name=='test_paired.py':sys.settrace(record)
        try:return (yield)
        finally:sys.settrace(old)
result=pytest.main(['-p','no:cacheprovider','--basetemp',str(ROOT/'evidence'/('pytest_'+uuid.uuid4().hex)),*sys.argv[1:]],plugins=[LineEvidence()])
(ROOT/'evidence/PAIRED_EXECUTED_LINES.json').write_text(json.dumps(sorted(visited))+'\n')
raise SystemExit(result)
