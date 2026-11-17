"""Differential refute: FIX2 launcher (review_h1read2 copy) vs FIX3 (copy of live kit)."""
import importlib.util, itertools, sys, copy
from pathlib import Path
from types import SimpleNamespace as NS
NEW=Path('/scratch/jjyeung/orch_n30/review_h1read3/work/k/kit/launcher')
OLD=Path('/scratch/jjyeung/orch_n30/review_h1read2/work/k/kit/launcher')
def load(root,name,tag):
    sys.path.insert(0,str(root))
    for m in ('binding','export_stage','orchard_job','orchard_stage','chain_save'): sys.modules.pop(m,None)
    spec=importlib.util.spec_from_file_location(tag,root/(name+'.py')); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    sys.path.pop(0); return mod
Bn=load(NEW,'binding','Bn'); Bo=load(OLD,'binding','Bo')
En=load(NEW,'export_stage','En'); Eo=load(OLD,'export_stage','Eo')
def out(f,*a):
    try: return ('ok',f(*a))
    except Exception as e: return ('err',type(e).__name__,str(e))
runs=['359fcc3c','17c4ffa4','469ddece','deadbeef','']
steps=[-1,0,1,50,100,137,200,201,400,543,544,545,1000,True,544.0,'544',None]
gens=[None,'m100','m200','m544','mstop','mstopB','mstopC','mstopD','']
nss=['8865619b','00000000']
fails=[];newok=[]
for r,s,g,n in itertools.product(runs,steps,gens,nss):
    a=out(Bo.expected,r,s,g,n); b=out(Bn.expected,r,s,g,n)
    if a!=b:
        if r=='469ddece' and b[0]=='ok' and (s,g,n)==(544,'mstop','8865619b') and type(s) is int: newok.append((r,s,g,n))
        else: fails.append(('expected',r,s,g,n,a,b))
    if b[0]=='ok':
        v=b[1]; assert Bn.validate(v)==v
        for k,bad in [('done','/x'),('claim',None),('object','q8/8865619b/469ddece_m544.tar'),('generation','m544'),('step',543),('namespace','00000000'),('run','359fcc3c')]:
            t=dict(v); t[k]=bad
            if out(Bn.validate,t)[0]=='ok' and t!=v: fails.append(('validate-accepts-tampered',k,v))
        raw=(v['object']+' 21583032320 '+'a'*64+'\n').encode()
        for claim in [None,b'm544\n',b'm543\n',('m'+str(v['step'])+'\n').encode()]:
            o=out(Bo.parse,raw,v,claim) if out(Bo.expected,r,s,g,n)[0]=='ok' else None; p=out(Bn.parse,raw,v,claim)
            if o is not None and o!=p: fails.append(('parse',v,claim,o,p))
print('expected new successes:',newok)
# logical_artifact
J=sys.modules.get('orchard_job')
import importlib
FSW=En.J.FSW
for r,s in itertools.product(runs+['469ddece'],[1,100,200,543,544,545,1000]):
    path=str(FSW/'ap/8865619b/runs'/r/('m'+str(s))/'artifact.json')
    a=out(Eo.logical_artifact,None,path,s); b=out(En.logical_artifact,None,path,s)
    if a!=b and not (r=='469ddece' and s==544): fails.append(('logical',r,s,a,b))
    # cross step: 469 m544 path with other steps
    p544=str(FSW/'ap/8865619b/runs/469ddece/m544/artifact.json')
    if s!=544 and out(En.logical_artifact,None,p544,s)[0]=='ok': fails.append(('logical-cross',s))
# stage_export gate only
class Stop(Exception):pass
for r,s in itertools.product(runs,steps):
    res=[]
    for E in (Eo,En):
        orig=E.T.writable; E.T.writable=lambda p:Path(p)
        origc=E.completed_local; E.completed_local=lambda *a,**k:(_ for _ in ()).throw(Stop())
        try: E.stage_export(NS(root='/tmp/x',run=r,step=s,tar='/tmp/a.tar',done='/tmp/d',full=True,bwrap='b')); res.append('ran')
        except Stop: res.append('passed-gate')
        except Exception as e: res.append(str(e))
        finally: E.T.writable=orig; E.completed_local=origc
    if res[0]!=res[1] and not ((r,s)==('469ddece',544) and type(s) is int): fails.append(('gate',r,s,res))
    if res[1]=='passed-gate' and r=='469ddece': print('gate passes for',r,repr(s))
# parse_done unchanged
for r,s in itertools.product(runs,[100,200,544]):
    raw=('q8/8865619b/'+r+'_m'+str(s)+'.tar 5 '+'a'*64+'\n').encode()
    if out(Eo.parse_done,raw,r,s)!=out(En.parse_done,raw,r,s): fails.append(('parse_done',r,s))
print('FAILS',len(fails));[print(f) for f in fails[:20]]
sys.exit(1 if fails else 0)
