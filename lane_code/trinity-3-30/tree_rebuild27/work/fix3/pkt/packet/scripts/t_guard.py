# CPU mechanics of b/mg.py and of its use in b/a.py. The two driver entry points are replaced by counters, so no
# driver call can happen in this test; the real device test runs on Orchard.
import sys,os,json,resource,textwrap,types
S,KB=sys.argv[1:3]
os.environ['CUDA_VISIBLE_DEVICES']=''
sys.path.insert(0,S);sys.path.insert(1,KB)
import torch
def out(k,v):print(k,json.dumps(v,sort_keys=True,default=str),flush=True)
calls=[]
def counted_count():calls.append('getDeviceCount');return 0
def counted_init():calls.append('init');raise RuntimeError('STUB: the driver init entry was reached')
torch._C._cuda_getDeviceCount=counted_count;torch._C._cuda_init=counted_init
from mg import guard
native=(torch.cuda.is_available,torch.cuda.device_count,torch.cuda._lazy_init)
out('HEAD',dict(torch=torch.__version__,compiled=torch.cuda._is_compiled(),CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES']))
n=len(calls);value=torch.cuda.is_available()
out('CONTROL_unguarded_query_under_mask',dict(is_available=value,driver_entry_calls=calls[n:]))
r={}
with guard():
    n=len(calls)
    r['patched_inside']=[torch.cuda.is_available is not native[0],torch.cuda.device_count is not native[1],torch.cuda._lazy_init is not native[2]]
    r['is_available']=torch.cuda.is_available();r['device_count']=torch.cuda.device_count()
    try:torch.cuda._lazy_init();r['lazy_init']='no error'
    except RuntimeError as error:r['lazy_init']=str(error)
    try:torch.zeros(1,device='cuda:0');r['open_device']='no error'
    except Exception as error:r['open_device']=type(error).__name__+':'+str(error)[:80]
    import importlib
    module=importlib.import_module('transformers.models.qwen3_5.modeling_qwen3_5')
    r['real_import']=module.__name__;r['fast_path']=bool(module.is_fast_path_available)
    r['driver_entry_calls_while_masked']=calls[n:]
    os.environ['CUDA_VISIBLE_DEVICES']='0';n=len(calls);torch.cuda.is_available()
    r['calls_with_a_device_mask_inside_block']=calls[n:];os.environ['CUDA_VISIBLE_DEVICES']=''
r['originals_restored']=all(a is b for a,b in zip((torch.cuda.is_available,torch.cuda.device_count,torch.cuda._lazy_init),native))
out('GUARD',r)
try:
    with guard():raise KeyError('x')
except KeyError:pass
out('GUARD_restores_after_exception',all(a is b for a,b in zip((torch.cuda.is_available,torch.cuda.device_count,torch.cuda._lazy_init),native)))
# The real block of a.py (mode q), as fix_spawn's harness runs it; native_admit is replaced by a probe.
a=(os.path.join(KB,'a.py'));lines=open(a).read().splitlines(keepends=True)
i=next(k for k,l in enumerate(lines) if l.strip()=="if mode=='q':")
j=next(k for k in range(i,len(lines)) if lines[k].strip()=='from launch_r1.production_proof import run')
g=dict(__name__='kitblock');exec(textwrap.dedent(''.join(lines[i+1:j])),g)
import student_pilot.s1_admission as admission_module, launch_r1.production_proof as proof_module
seen={}
def probe(*args,**kwargs):
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);resource.setrlimit(resource.RLIMIT_AS,(180<<30,hard))
    n=len(calls)
    seen.update(mask=os.environ.get('CUDA_VISIBLE_DEVICES'),patched=torch.cuda.is_available is not native[0],
        is_available=torch.cuda.is_available(),device_count=torch.cuda.device_count(),driver_entry_calls=calls[n:],args=[list(args),kwargs])
    return dict(config='returned')
g['native_admit']=probe
before=resource.getrlimit(resource.RLIMIT_AS)
# production_proof._run sets the empty mask, calls admit, then lifts the mask (lines 139-148).
visible='0';os.environ['CUDA_VISIBLE_DEVICES']=''
try:returned=admission_module.admit('pin','dir',[],threads=8,memory_gib=180,prepare_only=True)
finally:os.environ['CUDA_VISIBLE_DEVICES']=visible
out('A_PY_BLOCK',dict(admit_is_wrapper=admission_module.admit is g['restoring_admit'],forward_is_spawn_wrapper=proof_module.forward is g['spawned_forward'],
    inside_admit=seen,returned=returned,limit_before=before,limit_after=resource.getrlimit(resource.RLIMIT_AS),
    originals_after_admit=all(a is b for a,b in zip((torch.cuda.is_available,torch.cuda.device_count,torch.cuda._lazy_init),native))))
print('DONE')
