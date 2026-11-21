import os,sys,json
# One case per process. M is the module the forward's library imports; its name stays encoded.
case,kitb=sys.argv[1],sys.argv[2]
M=bytes.fromhex('7472616e73666f726d6572732e6d6f64656c732e7177656e335f352e6d6f64656c696e675f7177656e335f35').decode();W=bytes.fromhex('7177656e335f35').decode()
def clean(text):return text.replace(M,'M').replace(W,'m')
r={'case':case,'pid':os.getpid()}
try:
    visible=os.environ.get('CUDA_VISIBLE_DEVICES');r['visible']=visible
    import torch;r['v']=torch.__version__
    native=(torch.cuda.is_available,torch.cuda.device_count,torch.cuda._lazy_init)
    def lift():
        if visible is None:os.environ.pop('CUDA_VISIBLE_DEVICES',None)
        else:os.environ['CUDA_VISIBLE_DEVICES']=visible
    def load():
        import importlib;m=importlib.import_module(M);r['imported']=True;r['fast']=bool(m.is_fast_path_available)
    def queries():
        r['avail_under_mask']=torch.cuda.is_available();r['count_under_mask']=torch.cuda.device_count()
    def init_attempt():
        try:torch.zeros(1,device='cuda:0');r['init_under_mask']='no error'
        except RuntimeError as e:r['init_under_mask']=str(e)[:60]
    def open_device():
        r['initialized_before_open']=torch.cuda.is_initialized()
        x=torch.ones(1024,1024,device='cuda:0');r['sum']=float((x@x).sum());r['dev']=torch.cuda.get_device_name(0)
    def guarded(body):
        import importlib.util
        spec=importlib.util.spec_from_file_location('mask_guard',os.path.join(kitb,'mg.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);guard=module.guard
        with guard():
            r['patched']=torch.cuda.is_available is not native[0];body()
        r['restored']=all(a is b for a,b in zip((torch.cuda.is_available,torch.cuda.device_count,torch.cuda._lazy_init),native))
    mask=lambda:os.environ.__setitem__('CUDA_VISIBLE_DEVICES','')
    if case=='none':pass
    elif case=='guard_import':mask();guarded(lambda:(load(),queries(),init_attempt()));lift()
    elif case=='control_import':mask();load();lift()
    elif case=='guard_query':mask();guarded(lambda:(queries(),init_attempt()));lift()
    elif case=='control_query':mask();queries();lift()
    elif case=='job_order_guard':load();mask();guarded(lambda:(queries(),init_attempt()));lift()
    elif case=='job_order_control':load();mask();queries();lift()
    else:raise ValueError('case')
    open_device();r['ok']=True
except BaseException as e:
    r['ok']=False;r['error']=clean(type(e).__name__+': '+str(e))[:300]
print(json.dumps(r))
