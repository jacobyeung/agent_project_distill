import sys, importlib.util, numpy as np, torch
W='/scratch/jjyeung/orch_n30/reader_r1/work/b1'
R='/scratch/jjyeung/orch_n30/review_rr1b1'
sys.path[:0]=[R+'/p/b',R+'/p/tree',R+'/p/b/heads/selector']
from selector_head import load_head
HEAD,_=load_head(W+'/in/replay/sel/run_iso')
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
new=load(R+'/p/b/e2e_reader/stage1.py','s1new')
old=load(W+'/in/pkg/p/b/e2e_reader/stage1.py','s1old')
rng=np.random.default_rng(1); n_null=n_cand=0; bad=[]
def mk(mod,rule=None):
    o=mod.StageOne.__new__(mod.StageOne); o.head=HEAD
    if rule: o.rule=rule; o.diagnostics={}
    return o
for t in range(3000):
    n=int(rng.integers(1,31)); x=torch.tensor(rng.normal(size=(n,58))*rng.choice([.1,1,5]),dtype=torch.float64)
    nm=str(rng.choice(['chair','table','sofa','lamp','tv']))
    inp=dict(x=x,name=nm)
    slots=HEAD.with_null(x,None,nm); assert len(slots)==n+1
    o=mk(old).select(inp)
    nn=mk(new,'null_argmax').select(inp)
    # with diagnostics record present
    d=mk(new,'null_argmax'); d.diagnostics[nm]=dict(candidates=[dict(logit=None) for _ in range(min(n,30))])
    nd=d.select(inp)
    c=mk(new,'candidates_argmax').select(inp)
    ref=int(np.argmax(slots[:n].detach().numpy()))
    if not (o==nn==nd): bad.append(('null',t,o,nn,nd))
    if c!=ref or c<0: bad.append(('cand',t,c,ref))
    if o==-1: n_null+=1
    if o!=c: n_cand+=1
# ties
class H:
    def __init__(s,v): s.v=torch.tensor(v)
    def with_null(s,*a): return s.v
for v,want in (([3.,3.,9.],0),([1.,5.,5.,9.],1),([2.,2.,2.,2.],0)):
    o=new.StageOne.__new__(new.StageOne); o.head=H(v); o.rule='candidates_argmax'; o.diagnostics={}
    got=o.select(dict(x=torch.zeros(len(v)-1,58),name='a'))
    if got!=want: bad.append(('tie',v,got,want))
print('trials 3000 null_wins',n_null,'rule_differs',n_cand,'bad',bad[:5],len(bad))
