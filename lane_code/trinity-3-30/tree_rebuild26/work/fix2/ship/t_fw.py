# Harness: proves the forward wrapper from the kit's a.py runs in a fresh child.
import os,sys,json,resource,dis,textwrap,types,itertools
from pathlib import Path
os.environ['CUDA_VISIBLE_DEVICES']=''
ttree,kit,work,mode=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4]
kitb=kit/'b'
sys.path.insert(0,str(kitb));sys.path.insert(0,str(ttree));sys.path.insert(0,str(kitb))
def emit(k,v):print(k,json.dumps(v,default=str),flush=True)
import torch
os.environ['FWT_STUB']='1';os.environ['FWT_JOB']='job-value'
import launch_r1.production_proof as proof_module
native=proof_module.forward
ops=[(i.opname,i.argval) for i in dis.get_instructions(proof_module._run) if i.argval=='forward']
emit('T1_run_resolves_forward',ops)
if mode=='after':
    a=(kitb/'a.py').read_text().splitlines(keepends=True)
    i=next(n for n,l in enumerate(a) if l.strip()=="if mode=='q':")
    j=next(n for n in range(i,len(a)) if a[n].strip()=='from launch_r1.production_proof import run')
    block=textwrap.dedent(''.join(a[i+1:j]))
    g=dict(__name__='kitblock')
    try:exec(block,g);emit('block_exec','real s1_admission')
    except ImportError as e:
        sm=types.ModuleType('student_pilot.s1_admission');sm.admit=lambda *a,**k:None
        sys.modules['student_pilot.s1_admission']=sm;exec(block,g);emit('block_exec','stub s1_admission after '+repr(e)[:200])
    emit('T1_wrapper_installed',dict(name=proof_module.forward.__name__,is_wrapper=proof_module.forward is g['spawned_forward'],job_limit=g['job_limit']))
# Calls forward exactly as _run does: a global-name lookup in production_proof's namespace.
via_run=types.FunctionType(compile('def f(cfg,root,step,device):\n return forward(cfg,root,step,device)\n','<run>','exec').co_consts[0],proof_module.__dict__)
cfg=dict(world_size=2);root=work/('root_'+mode);root.mkdir(exist_ok=True);step=400
job_limit=resource.getrlimit(resource.RLIMIT_AS)
# Poison the parent: query the device while the mask is empty, mark torch, lower the soft limit, change threads.
os.environ['CUDA_VISIBLE_DEVICES']='';emit('parent_poison',dict(device_count=torch.cuda.device_count(),available=torch.cuda.is_available(),initialized=torch.cuda.is_initialized()))
torch._fwt_marker=1;torch.set_num_threads(3)
low=64<<30;resource.setrlimit(resource.RLIMIT_AS,(low,job_limit[1]))
os.environ['CUDA_VISIBLE_DEVICES']=''
from launch_r1.entry import host_environment
from student_pilot.r1_persisted import scope,proof_scope
jt=work/('jt_'+mode);jt.mkdir(exist_ok=True);count=itertools.count()
def run_call(fn,raise_kind=''):
    os.environ['FWT_RAISE']=raise_kind
    info=work/f'info_{mode}_{next(count)}.json';os.environ['FWT_INFO']=str(info)
    with host_environment(jt),scope({'1'*64:'/outer/a'}),proof_scope(),scope({'0'*64:'/inner/b'}):
        try:r=('ok',fn(cfg,root,step,'cpu'))
        except BaseException as e:r=('raise',type(e).__module__+'.'+type(e).__qualname__,str(e))
    return r,(json.loads(info.read_text()) if info.exists() else None)
emit('parent',dict(pid=os.getpid(),job_limit=job_limit,lowered_soft=low,threads=torch.get_num_threads()))
r,i=run_call(via_run);emit('T1T2_call',dict(result=r[0],child=i,in_child=i['pid']!=os.getpid()))
if mode=='after':
    ref,ref_i=run_call(native);ref_f=(root/'f.json').read_bytes()
    got,got_i=run_call(via_run);got_f=(root/'f.json').read_bytes()
    strip=lambda d:{k:v for k,v in d.items() if k!='peak_rss_bytes'}
    emit('T4_equal',dict(equal_except_rss=strip(ref[1])==strip(got[1]),same_keys=sorted(ref[1])==sorted(got[1]),f_json_equal=ref_f==got_f,
        rss_inproc=ref[1]['peak_rss_bytes'],rss_child=got[1]['peak_rss_bytes'],records=got[1]['records'],ref_pid=ref_i['pid'],got_pid=got_i['pid']))
    for k in ('value','key','os','runtime','custom'):
        a1,_=run_call(native,k);b1,bi=run_call(via_run,k)
        emit('T3_'+k,dict(inproc=a1,child=b1,same=a1==b1,child_pid=bi and bi['pid']))
    b1,_=run_call(via_run,'exit');emit('T3_exit',dict(child=b1,caught_by_run=b1[1]=='builtins.RuntimeError'))
    resource.setrlimit(resource.RLIMIT_AS,job_limit)
print('DONE',mode)
