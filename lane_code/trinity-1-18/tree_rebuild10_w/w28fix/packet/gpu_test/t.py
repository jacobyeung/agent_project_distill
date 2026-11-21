# usage: t.py <case> <kit> <new work dir under /tmp> [old|new] [meta=<folder>] [sim] [trace] [fail=<where>] [path=<dir>]...
# One case per process. Prints one JSON line; appends every full traceback to <work>/tb_raw.txt. The name of the
# model family is replaced by 'm' in everything this script writes.
#   job          the kit's own b/a.py run unmodified as the entry in mode q, with three stand-ins: the plan
#                (b/pl.py), production_proof.run (the device-touching steps of _run, lines 123-176, in its order
#                and wording) and the body of admit (its opening statements, then the device call its prepare
#                phase reaches). The kit's wrappers, guard and hooks are the real bytes.
#   job_noguard  the same with b/mg.py's guard replaced by an empty block: the library's native behaviour.
#                fail=admit|forward|uncaught|selection injects an exception there and fail=bound overfills the
#                traceback file, to show what the kit writes to <work>/ns/tb.txt.
#   order        which unmasked step initializes the library: the processor load or the model build.
#   api, api_noguard   initialize unmasked and ask the device name (which fixes the library's device count, as
#                the import of the model library does), then under the mask (and the kit's guard) call the
#                current-device query, create a device tensor, ask availability and count; lift; open.
#   api_uncached_noguard   the same without the device-name query and without a guard: the library's own count
#                query, first made under the mask, stays 0 after the lift.
#   fresh, fresh_noguard, fresh_import   a process that has not initialized: mask (and guard), queries or the
#                import of the model library module; lift; open.
import os,re,sys,json,hashlib,types,runpy,traceback,importlib,importlib.util
from pathlib import Path
case,kit,work=sys.argv[1],Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve()
opts=sys.argv[4:];SIM='sim' in opts;TRACE='trace' in opts
role=next((o for o in opts if o in ('old','new')),'new')
meta=next((Path(o[5:]) for o in opts if o.startswith('meta=')),None)
FAIL=next((o[5:] for o in opts if o.startswith('fail=')),None)
for extra in [o[5:] for o in opts if o.startswith('path=')]:sys.path.insert(0,extra)
H=lambda s:bytes.fromhex(s).decode()
MODULE=H('7472616e73666f726d6572732e6d6f64656c732e7177656e335f352e6d6f64656c696e675f7177656e335f35')
TREE=H('73747564656e745f70696c6f74')
WORD=H('7177656e');scrub=lambda text:re.sub(WORD,'m',text,flags=re.I)
LOADER=H('6465636f75706c65645f765f72756e');RUNNER=H('636172726965725f63315f72756e')
NAMES={"chat_template.jinja":"a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715","config.json":"d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05","merges.txt":"a9d356d7bdf1ef4949e3e748e95b8e10ad9d4e2e838eddc38a0a7b6b94d1db8d","model.safetensors.index.json":"26d3539b516be613f39563617cb9d33b3f83d401298125be392c80cefb8f7fe5","preprocessor_config.json":"27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516","tokenizer.json":"5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42","tokenizer_config.json":"316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8","video_preprocessor_config.json":"7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13","vocab.json":"ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003"}
R=dict(case=case,role=role,fail=FAIL,pid=os.getpid(),sim=SIM,marks=[]);T=dict(result={},calls={})
work.mkdir(parents=True);TB=work/'tb_raw.txt'
masked=lambda:os.environ.get('CUDA_VISIBLE_DEVICES')==''

def initialized():
    import torch
    f=torch.cuda.is_initialized
    return bool(getattr(f,'__wrapped__',f)())

def mark(name,**more):
    R['marks'].append(dict(at=name,visible=os.environ.get('CUDA_VISIBLE_DEVICES'),initialized=initialized(),**more))

def who(error):
    frames=traceback.extract_tb(error.__traceback__)
    names=[f.filename.replace(os.sep,'/') for f in frames]
    if any(n.endswith('/b/mg.py') for n in names):by='(i) mg.py'
    elif any(n.endswith('/b/fw.py') for n in names):by='(ii) fw.py'
    elif frames and '/torch/' in names[-1]:by='(iii) torch'
    else:by='other'
    return by,['%s/%s:%d %s'%(Path(f.filename).parent.name,Path(f.filename).name,f.lineno,f.name) for f in frames[-9:]]

def keep(where,error):
    with TB.open('a') as f:
        f.write('=== case=%s role=%s where=%s\n'%(case,role,where))
        f.write(scrub(''.join(traceback.format_exception(type(error),error,error.__traceback__)))+'\n')

def failure(where,error):
    keep(where,error);by,frames=who(error)
    return dict(where=where,text=type(error).__name__+':'+str(error)[:300],raised_by=by,frames=frames)

def install_sim():
    # CPU rehearsal only: a stand-in driver below the library's own python code. The first count query
    # fixes the answer for the process, as the library's native count does.
    import torch
    S=dict(count=None,count_queries=0,init_calls=0,device_queries=0);R['sim_driver']=S
    def count():
        S['count_queries']+=1
        if S['count'] is None:S['count']=0 if masked() else 1
        return S['count']
    def init():
        S['init_calls']+=1
        if count()==0:raise RuntimeError('No CUDA GPUs are available')
    def device():
        S['device_queries']+=1
        return 'cpu'
    torch._C._cuda_getDeviceCount,torch._C._cuda_init,torch._C._cuda_getDevice=count,init,device
    if getattr(torch.cuda,'_cudart',None) is None:torch.cuda._cudart=object()
    if not hasattr(torch._C,'_cuda_getCurrentRawStream'):torch._C._cuda_getCurrentRawStream=lambda *a:0
    # The library's own count: 0 under an empty mask, else the driver's (no management library here).
    torch.cuda._device_count_nvml=lambda:0 if masked() else -1
    torch.cuda.default_generators=(torch.Generator(),)

def sim_norm():
    # CPU rehearsal only: fla cannot import on this node (no usable triton), so the model library's own name for
    # fla's fused norm gets a stand-in with fla's constructor (fla 0.6.0 modules/norm/fused_norm_gate.py:967-992).
    # The branch that passes device=<current device> to it is the library's own code.
    import torch
    library=importlib.import_module(MODULE)
    if library.FusedRMSNormGated is None:
        class FusedRMSNormGated(torch.nn.Module):
            def __init__(self,hidden_size,elementwise_affine=True,eps=1e-5,activation='swish',device=None,dtype=None):
                super().__init__()
                self.weight=torch.nn.Parameter(torch.empty(hidden_size,device=device,dtype=dtype))
                torch.nn.init.ones_(self.weight)
        library.FusedRMSNormGated=FusedRMSNormGated;R['sim_norm']='stand-in bound'
    else:R['sim_norm']='fla bound'

def install_trace():
    import torch
    cuda=torch.cuda;log=T['calls']
    def wrap(name,fn):
        def traced(*a,**k):
            st=traceback.extract_stack()[:-1]
            chain=' < '.join('%s/%s:%d:%s'%(Path(f.filename).parent.name,Path(f.filename).name,f.lineno,f.name) for f in reversed(st[-16:]))
            key=(name,masked(),chain);log[key]=log.get(key,0)+1
            return fn(*a,**k)
        traced.__name__=name;traced.__wrapped__=fn
        return traced
    for name,fn in list(vars(cuda).items()):
        if isinstance(fn,types.FunctionType) and fn.__module__=='torch.cuda':setattr(cuda,name,wrap(name,fn))

def calls_report():
    rows=[dict(fn=k[0],masked=k[1],n=n,chain=k[2]) for k,n in sorted(T['calls'].items(),key=lambda kv:(kv[0][1],kv[0][0]))]
    (work/'calls.json').write_text(scrub(json.dumps(rows,indent=1)))
    brief={}
    for row in rows:
        outside=[p for p in row['chain'].split(' < ') if not p.startswith(('cuda/__init__.py','work/','ship/')) and ':traced' not in p]
        key='%s %s @ %s'%('masked' if row['masked'] else 'unmasked',row['fn'],outside[0] if outside else '?')
        brief[key]=brief.get(key,0)+row['n']
    R['cuda_calls']=brief

def prepare_library():
    import torch
    R['v']=torch.__version__;R['visible_at_start']=os.environ.get('CUDA_VISIBLE_DEVICES')
    if SIM:install_sim()
    if TRACE:install_trace()
    return torch

def open_device():
    import torch
    R['initialized_before_open']=initialized()
    if SIM:
        torch.cuda.init();x=torch.ones(64,64);R['sum']=float((x@x).sum());R['dev']='sim: host memory'
    else:
        x=torch.ones(1024,1024,device='cuda:0');R['sum']=float((x@x).sum())
    R['count_after_lift']=torch.cuda.device_count();R['available_after_lift']=torch.cuda.is_available()
    if not SIM:
        try:R['dev']=torch.cuda.get_device_name(0)
        except BaseException as e:R['dev_error']=failure('device name after lift',e)

def kit_guard():
    spec=importlib.util.spec_from_file_location('mask_guard',kit/'b/mg.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    R['guard_sha256']=hashlib.sha256((kit/'b/mg.py').read_bytes()).hexdigest()[:16]
    return module.guard

from contextlib import contextmanager
@contextmanager
def no_guard():
    yield

def toy(cfg,label):
    # production_proof.py:125 training_components -> r1_training.py:50-51 -> r1_components.py:49-51 ->
    # r1_absence.py:77 build(cfg): the tree's two-layer model on the meta device.
    build=importlib.import_module(TREE+'.r1_absence').build
    if SIM:sim_norm()
    if FAIL=='uncaught' and 'unmasked' in label:raise AssertionError('injected uncaught failure')
    model=build(cfg)
    norms=[m for m in model.modules() if 'RMSNormGated' in type(m).__name__]
    mark(label,norm_classes=sorted({type(m).__name__ for m in norms}),
         norm_weight_devices=sorted({str(m.weight.device) for m in norms if getattr(m,'weight',None) is not None}))

def processor(label):
    if meta is None:
        mark(label+': skipped, no metadata folder');return
    y=work/'y'
    if not y.exists():
        y.mkdir()
        for name,h in NAMES.items():
            raw=(meta/h[:16]).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('metadata bytes differ: '+name)
            (y/name).write_bytes(raw)
    loaded=importlib.import_module(TREE+'.'+LOADER).processor_for(str(y))
    mark(label,processor=type(loaded).__name__)

def stub_admit(config_pin,output,roots,*,threads=16,memory_gib=256,sample_size=64,max_seconds=86400,
               rank_limit=None,attempt=None,prepare_only=False):
    # s1_admission.py:135-146, then the call its prepare phase reaches at :225 run.prepare(selected) ->
    # the first statement of prepare -> r2_contract.py:72-73 -> training_components -> ... -> r1_absence.build.
    import resource
    if os.environ.get("CUDA_VISIBLE_DEVICES")!="":
        raise ValueError("The admission command requires CUDA_VISIBLE_DEVICES to be empty")
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    limit=int(memory_gib*(1<<30))
    resource.setrlimit(resource.RLIMIT_AS,(min(value for value in (soft,hard,limit) if value>0),hard))
    import torch
    torch.set_num_threads(threads)
    try:
        if torch.get_num_interop_threads()!=1:torch.set_num_interop_threads(1)
    except RuntimeError as e:R['interop_note']=str(e)[:80]
    T['limit_inside_admit']=resource.getrlimit(resource.RLIMIT_AS)[0]
    mark('inside admit, mask on, before the model build')
    toy(T['cfg'],'inside admit, mask on, after the model build')
    if FAIL=='admit':raise RuntimeError('injected admit failure')
    return dict(config=None)

def stub_first_batch(cfg,ranks,out_path,steps=1,device='cpu',progress_dir=None,rank_limit=None,encode_only=False,start_step=0):
    # The forward opens its device here (first_batch_check: device = torch.device(device)).
    import torch
    if FAIL=='forward':raise RuntimeError('injected forward failure')
    if SIM:torch.cuda.init()
    target=torch.device('cpu' if SIM else device)
    x=torch.ones(1024,1024,device=target);s=float((x@x).sum())
    R['forward_device']=str(x.device);R['forward_sum']=s
    records=[dict(rank=r,stream='t',loss=s,finite=True) for r in ranks]
    Path(out_path).write_text(json.dumps(records))
    return records

SKELETON='''
def _test_run(request, output, *, stage=None):
    root = Path(output).resolve(); root.mkdir(parents=True, exist_ok=True)
    result = dict(status='REFUSE',GO=False,steps=[],forward='not requested')
    try:
        cfg = request['cfg']
        import os
        memory = request.get('memory_gib',192)
        device = request.get('device','cpu')
        _t.mark('start of the steps')
        _t.toy(cfg,'after step training_components, unmasked (line 125)')
        result['steps'].append('training_components')
        _t.processor('after step p_opener_witness, unmasked (line 130)')
        result['steps'].append('p_opener_witness')
        from student_pilot.s1_admission import admit
        directory=root/'p';directory.mkdir(exist_ok=True)
        visible = os.environ.get('CUDA_VISIBLE_DEVICES')
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        try:
            prepared = admit(None,directory,request['frame_roots'],threads=8,
                             memory_gib=memory,prepare_only=True)
        finally:
            if visible is None:
                os.environ.pop('CUDA_VISIBLE_DEVICES',None)
            else:
                os.environ['CUDA_VISIBLE_DEVICES'] = visible
        result['steps'].extend(['s1_routing.build','s1_admission.prepare'])
        _t.mark('after admit, mask lifted (line 148)')
        if _t.native_forward(forward):
            _t.before_forward()
            result['forward']=forward(cfg,root,0,device)
        else:
            result['forward']=_t.replaced_forward(forward,device)
        result['steps'].append('all_rank_full_forward')
        result['status']='TEST_PASS'
    except (ValueError,KeyError,TypeError,OSError,RuntimeError,ImportError) as error:
        result['refusal']=type(error).__name__+':'+str(error)
        _t.refused(error)
    _t.result.update(result)
    return result
'''.replace('student_pilot',TREE)

def fake_plan():
    plan=types.ModuleType('pl')
    def plan_payload(kit_,resolved,root,*,regeneration=False):
        import resource
        proof=importlib.import_module('launch_r1.production_proof')
        admission=importlib.import_module(TREE+'.s1_admission')
        admission.admit=stub_admit
        tree_forward=proof.forward
        def before_forward():
            importlib.import_module(TREE+'.'+RUNNER).first_batch_check=stub_first_batch
        def replaced_forward(wrapper,device):
            # A kit that replaced the forward would run the real first batch in its own process, for
            # which this test has no data; the device is opened here instead.
            R['forward_wrapper']=getattr(wrapper,'__name__','?')
            return stub_first_batch(T['cfg'],[0],Path(root)/'q'/'f_direct.json',device=device)
        def refused(error):
            R['refusal_failure']=failure('steps',error)
        proof._t=types.SimpleNamespace(mark=mark,toy=toy,processor=processor,result=T['result'],refused=refused,
            native_forward=lambda f:f is tree_forward,before_forward=before_forward,replaced_forward=replaced_forward)
        exec(compile(SKELETON,'steps_of_run','exec'),proof.__dict__)
        proof.run=proof.__dict__['_test_run']
        T['limit_at_plan']=resource.getrlimit(resource.RLIMIT_AS)[0]
        if FAIL=='selection':
            # The kit's wrapper of the host selection check, called with a configuration it must refuse.
            try:importlib.import_module('launch_r1.entry').check_host_selection({},Path(root),{},{})
            except BaseException as e:R['selection_failure']=failure('selection',e)
        (Path(root)/'plan.json').write_text(json.dumps(dict(config={})))
        request=dict(cfg=T['cfg'],frame_roots=[],device='cuda:0')
        return request,{},types.SimpleNamespace(close=lambda:None)
    plan.plan_payload=plan_payload
    return plan

def capsule(path):
    import base64
    v=json.loads(Path(path).read_text());raw=base64.b64decode(v['payload'],validate=True)
    if hashlib.sha256(raw).hexdigest()!=v['sha256']:raise ValueError('capsule')
    return json.loads(raw)

def job(guarded=True):
    import resource
    prepare_library()
    T['cfg']=capsule(kit/'k/c.json')
    R['kit_seal']=hashlib.sha256((kit/'SHA256SUMS.txt').read_bytes()).hexdigest()[:8]
    R['guard_sha256']=hashlib.sha256((kit/'b/mg.py').read_bytes()).hexdigest()[:16]
    sys.modules['pl']=fake_plan()
    if not guarded:
        empty=types.ModuleType('mg');empty.guard=no_guard;sys.modules['mg']=empty
    root=work/'ns'/'p';(work/'ns').mkdir()
    handover=work/'h.json';handover.write_text(json.dumps({'_resolved':{}}))
    os.environ.setdefault('SLURM_JOB_ID','0')
    saved=sys.argv;sys.argv=[str(kit/'b/a.py'),'q',str(root),str(handover)]
    limit=resource.getrlimit(resource.RLIMIT_AS)[0]
    import contextlib
    try:
        with contextlib.redirect_stdout(sys.stderr):runpy.run_path(str(kit/'b/a.py'),run_name='__main__')
        R['entry']='returned'
    except SystemExit as e:R['entry']='exit %s'%e.code
    except BaseException as e:
        R['entry_failure']=failure('entry',e)
        hook=sys.excepthook
        if hook is not sys.__excepthook__:
            try:hook(type(e),e,e.__traceback__)
            except BaseException as again:R['hook_failure']=failure('excepthook',again)
    finally:sys.argv=saved
    result=T['result'];R['status']=result.get('status');R['steps']=result.get('steps');R['refusal']=result.get('refusal')
    R['forward']=result.get('forward') if not isinstance(result.get('forward'),dict) else 'returned by the tree forward'
    R['limit']=dict(before=limit,at_plan=T.get('limit_at_plan'),inside_admit=T.get('limit_inside_admit'),after=resource.getrlimit(resource.RLIMIT_AS)[0])
    proof=sys.modules.get('launch_r1.production_proof')
    R['kit_hooks']=dict(refusal_hook='str' in vars(proof) if proof else None,
                        admit_wrapper=getattr(sys.modules[TREE+'.s1_admission'].admit,'__name__',None) if TREE+'.s1_admission' in sys.modules else None)
    kit_tb=work/'ns'/'tb.txt'
    if FAIL=='bound' and proof is not None and 'str' in vars(proof):
        sizes=[]
        for i in range(5):
            vars(proof)['str'](RuntimeError('y'*100000));sizes.append(kit_tb.stat().st_size if kit_tb.exists() else 0)
        R['bound_sizes']=sizes
    R['r0']=(work/'ns'/'p'/'r0.json').exists()
    if kit_tb.exists():
        text=kit_tb.read_text(errors='replace')
        R['kit_tb']=dict(bytes=kit_tb.stat().st_size,mode=oct(kit_tb.stat().st_mode&0o777),records=[l for l in text.splitlines() if l.startswith('=== ')])
        with TB.open('a') as f:f.write('=== the kit\'s own tb.txt of case=%s role=%s follows\n'%(case,role)+scrub(text)+'\n')
    else:R['kit_tb']=None
    refusal=R.get('refusal_failure') or {}
    if not guarded:R['expected']='TEST_PASS';R['as_expected']=R['status']=='TEST_PASS'
    elif role=='old':
        R['expected']='refusal RuntimeError:No CUDA GPUs are available raised by (i) mg.py'
        R['as_expected']=R['refusal']=='RuntimeError:No CUDA GPUs are available' and refusal.get('raised_by')=='(i) mg.py'
    elif FAIL is None:
        R['expected']='TEST_PASS and no tb.txt'
        R['as_expected']=R['status']=='TEST_PASS' and R['kit_tb'] is None
    else:
        records=(R['kit_tb'] or {}).get('records',[]);one=len(records)==1 and (R['kit_tb'] or {}).get('mode')=='0o600'
        if FAIL=='selection' and records:
            records=[' '.join(records[0].split()[:4])+' *'];R['status_with_selection']=R['status'];R['refusal']='TEST_PASS' if R['status']=='TEST_PASS' else R['refusal']
        want=dict(selection=('where=selection *','TEST_PASS'),admit=('where=admit RuntimeError','RuntimeError:injected admit failure'),
                  forward=('where=refusal RuntimeError','RuntimeError:injected forward failure'),
                  uncaught=('where=uncaught AssertionError',None))
        if FAIL=='bound':
            R['expected']='tb.txt grows 65536, 131072, 196608, 204800, 204800'
            R['as_expected']=R.get('bound_sizes')==[65536,131072,196608,204800,204800]
        else:
            R['expected']='one record "%s" in tb.txt, mode 0600, refusal %s'%want[FAIL]
            R['as_expected']=one and records[0].endswith(want[FAIL][0]) and R['refusal']==want[FAIL][1] and (FAIL!='uncaught' or R['r0'])
        R['as_expected']=bool(R['as_expected']) and R['limit']['before']==R['limit']['after']

def api(guarded=True,cached=True):
    torch=prepare_library()
    guard=kit_guard() if guarded else no_guard
    if SIM:torch.cuda.init()
    else:torch.zeros(1,device='cuda:0')
    if cached:R['count_before_mask']=torch.cuda.device_count() if SIM else (torch.cuda.get_device_name(0) and torch.cuda.device_count())
    mark('initialized unmasked')
    visible=os.environ.get('CUDA_VISIBLE_DEVICES');os.environ['CUDA_VISIBLE_DEVICES']=''
    try:
        with guard():
            try:R['current_device_under_mask']=torch.cuda.current_device()
            except BaseException as e:R['current_device_under_mask']=failure('current_device',e)
            if not SIM:
                try:torch.zeros(1,device='cuda:0');R['tensor_under_mask']='no error'
                except BaseException as e:R['tensor_under_mask']=failure('tensor',e)
            R['available_under_mask']=torch.cuda.is_available();R['count_under_mask']=torch.cuda.device_count()
    finally:
        if visible is None:os.environ.pop('CUDA_VISIBLE_DEVICES',None)
        else:os.environ['CUDA_VISIBLE_DEVICES']=visible
    open_device()
    answer=R['current_device_under_mask']
    if not cached:
        R['expected']='count 0 under the mask and still 0 after the lift; the device itself opens'
        R['as_expected']=R['count_under_mask']==0 and R['count_after_lift']==0
    elif guarded and role=='old':
        R['expected']='current_device raises through (i) mg.py; the device opens after the lift'
        R['as_expected']=isinstance(answer,dict) and answer['raised_by']=='(i) mg.py'
    else:
        R['expected']='current_device answers; the device opens after the lift'
        R['as_expected']=not isinstance(answer,dict)

def fresh(mode):
    torch=prepare_library()
    guard=kit_guard() if mode!='noguard' else no_guard
    visible=os.environ.get('CUDA_VISIBLE_DEVICES');os.environ['CUDA_VISIBLE_DEVICES']=''
    try:
        with guard():
            if mode=='import':
                importlib.import_module(MODULE);R['imported']=True
            R['available_under_mask']=torch.cuda.is_available();R['count_under_mask']=torch.cuda.device_count()
            try:R['current_device_under_mask']=torch.cuda.current_device()
            except BaseException as e:R['current_device_under_mask']=failure('current_device',e)
            mark('under the mask')
    finally:
        if visible is None:os.environ.pop('CUDA_VISIBLE_DEVICES',None)
        else:os.environ['CUDA_VISIBLE_DEVICES']=visible
    if mode=='noguard':
        R['expected']='the device does not open after the lift (the unguarded query fixed the count at 0)'
        try:open_device();R['as_expected']=False
        except BaseException as e:R['open_failure']=failure('open',e);R['as_expected']=True
    else:
        R['expected']='available False, count 0, current_device raises, the device opens after the lift'
        open_device()
        R['as_expected']=R['available_under_mask'] is False and R['count_under_mask']==0 and isinstance(R['current_device_under_mask'],dict)

def order():
    prepare_library()
    sys.path.insert(0,str(kit/'b'))
    import tarfile
    control=capsule(kit/'k/a.json');source=kit/control['source']['path']
    with tarfile.open(source) as t:t.extractall(work/'s',filter='data')
    sys.path.insert(0,str(work/'s'))
    cfg=capsule(kit/'k/c.json')
    mark('start')
    processor('after the processor load alone')
    toy(cfg,'after the model build')
    R['expected']='not initialized after the processor load, initialized after the model build'
    R['as_expected']=R['marks'][-1]['initialized'] is True and (meta is None or R['marks'][-2]['initialized'] is False)

try:
    if case=='job':job()
    elif case=='job_noguard':job(guarded=False)
    elif case=='api':api()
    elif case=='api_noguard':api(guarded=False)
    elif case=='api_uncached_noguard':api(guarded=False,cached=False)
    elif case=='fresh':fresh('guard')
    elif case=='fresh_noguard':fresh('noguard')
    elif case=='fresh_import':fresh('import')
    elif case=='order':order()
    else:raise ValueError('case')
    R['ok']=True
except BaseException as e:
    R['ok']=False;R['failure']=failure('case',e);R.setdefault('as_expected',False)
if TRACE:
    try:calls_report()
    except BaseException as e:R['trace_failure']=str(e)[:200]
print(scrub(json.dumps(R)))
