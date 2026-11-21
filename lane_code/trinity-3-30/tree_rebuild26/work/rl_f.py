import os,sys,json,resource,subprocess
# Mechanism test for the forward-in-a-fresh-interpreter fix: poison the parent (empty mask + device query,
# 180 GiB soft address-space limit), restore the mask, then start a new interpreter that touches cuda:0.
case=sys.argv[1]
if case=='child':
    r={'case':'child','pid':os.getpid(),'visible':os.environ.get('CUDA_VISIBLE_DEVICES')}
    try:
        s=json.loads(os.environ['T_AS']);resource.setrlimit(resource.RLIMIT_AS,tuple(s));r['as']=resource.getrlimit(resource.RLIMIT_AS)
        import torch;r['initialized_at_start']=torch.cuda.is_initialized()
        x=torch.ones(1024,1024,device='cuda:0');r['ok']=True;r['sum']=float(x.sum());r['dev']=torch.cuda.get_device_name(0)
    except BaseException as e:r['ok']=False;r['error']=(type(e).__name__+': '+str(e))[:500]
    print(json.dumps(r));sys.exit(0)
r={'case':case,'pid':os.getpid()}
try:
    s0,h0=resource.getrlimit(resource.RLIMIT_AS);vis=os.environ.get('CUDA_VISIBLE_DEVICES')
    if case in ('maskcount','fix'):
        resource.setrlimit(resource.RLIMIT_AS,(180*(1<<30),h0));os.environ['CUDA_VISIBLE_DEVICES']=''
        import torch;r['count_under_mask']=torch.cuda.device_count();r['avail_under_mask']=torch.cuda.is_available()
        if vis is None:os.environ.pop('CUDA_VISIBLE_DEVICES',None)
        else:os.environ['CUDA_VISIBLE_DEVICES']=vis
    else:import torch
    if case=='fix':
        env=dict(os.environ,T_AS=json.dumps([s0,h0]))
        p=subprocess.run([sys.executable,'-I','-s','-B',__file__,'child'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
        r['child']=p.stdout.decode()[-800:];r['ok']='"ok": true' in r['child']
        try:torch.zeros(1,device='cuda:0');r['parent_cuda']='ok'
        except BaseException as e:r['parent_cuda']=(type(e).__name__+': '+str(e))[:200]
    else:
        torch.zeros(1,device='cuda:0');r['ok']=True
except BaseException as e:r['ok']=False;r['error']=(type(e).__name__+': '+str(e))[:500]
print(json.dumps(r))
