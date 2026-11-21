import os,sys,json,resource
# One case per child process, mirroring s1_admission.admit's order: soft address-space limit, empty device mask,
# import torch, set_num_threads / interop threads, then (fix cases) restore, then the first device use on cuda:0.
case=sys.argv[1]
r={'case':case,'nvml_check':os.environ.get('PYTORCH_NVML_BASED_CUDA_CHECK')}
try:
    s0,h0=resource.getrlimit(resource.RLIMIT_AS);r['as_before']=[s0,h0]
    vis=os.environ.get('CUDA_VISIBLE_DEVICES');r['visible']=vis
    if case in ('lim','both','restore','fixed'):
        lim=180*(1<<30);resource.setrlimit(resource.RLIMIT_AS,(min(v for v in (s0,h0,lim) if v>0),h0));r['as_soft']=resource.getrlimit(resource.RLIMIT_AS)[0]
    if case in ('mask','both','fixed','maskcount'):os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch;r['torch']=torch.__version__
    torch.set_num_threads(4)
    if torch.get_num_interop_threads()!=1:torch.set_num_interop_threads(1)
    if case=='maskcount':r['count_under_mask']=torch.cuda.device_count();r['avail_under_mask']=torch.cuda.is_available()
    if case in ('restore','fixed'):resource.setrlimit(resource.RLIMIT_AS,(s0,h0));r['as_restored']=resource.getrlimit(resource.RLIMIT_AS)[0]
    if case in ('mask','both','fixed','maskcount'):
        if vis is None:os.environ.pop('CUDA_VISIBLE_DEVICES',None)
        else:os.environ['CUDA_VISIBLE_DEVICES']=vis
    d=torch.device('cuda:0');x=torch.zeros(1,device=d);r['ok']=True;r['dev']=torch.cuda.get_device_name(0);r['avail']=torch.cuda.is_available()
except BaseException as e:
    r['ok']=False;r['error']=(type(e).__name__+': '+str(e))[:600]
print(json.dumps(r))
