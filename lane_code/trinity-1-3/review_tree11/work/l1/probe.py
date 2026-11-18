import sys,json,tempfile
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_tree11/work/eat/b')
from types import SimpleNamespace
import torch
from eat1 import run as R
from eat1.tests.test_eat1 import FixedMathContract
mk=FixedMathContract('test_valid_fixed_math').make
out={}
def go(name,gen,items=1):
    model,art=mk()
    reader=SimpleNamespace(model=model,generate=lambda f,q:gen(model))
    try:
        recs,lines,decl=R.observe(reader,[dict(frames='x',question='q')]*items,art,trace_lines=False,audit=False,monitor=False)
        out[name]=dict(a1=R.judge_a1(recs,art,[])['status'],errors=[r['error'] for r in recs],offenders=[o['kind'] for o in getattr(art,'buffer_offenders',[])])
    except Exception as e: out[name]='RAISE '+type(e).__name__+': '+str(e)[:120]
def mutate(m): m.math.scale.fill_(7.); return dict(text='7',answer='7',calls=[])
def mutate_raise(m): m.math.scale.fill_(7.); raise RuntimeError('boom')
def mutate_restore(m):
    m.math.scale.fill_(7.); v=float(m.math(torch.tensor(1.))); m.math.scale.fill_(2.); return dict(text=str(v),answer=str(v),calls=[])
def clean(m): return dict(text=str(float(m.math(torch.tensor(1.)))),answer='2',calls=[])
go('clean',clean); go('mutate_in_generate',mutate); go('mutate_then_raise',mutate_raise); go('mutate_restore_within_item',mutate_restore)
print(json.dumps(out,indent=1))
