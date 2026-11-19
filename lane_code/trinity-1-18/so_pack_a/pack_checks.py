"""Isolated probes; this file never starts a remote command."""
import ast, builtins, copy, io, json, math, os, runpy, signal, subprocess, sys, tarfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pack as P

def materialize(package,work):
    f,pay,pub,plan=P.structure(package)
    src=P.extract(pay,work/'s');sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
    return f,pay,pub,plan,src

def rows(value):
    if isinstance(value,list):
        for x in value:
            for r in rows(x):yield r
    elif isinstance(value,dict):
        if 'student_input' in value or 'source_frame_indices' in value or ('frame_indices' in value and any(k in value for k in ('total_num_frames','fps','num_frames'))):yield value
        else:
            for x in value.values():
                for r in rows(x):yield r

def native_dry_predicates(base,plan,pay,op,desc,memory):
    """Applicable dry2/dry2b predicates, with D's native 580-item contract."""
    from collections import Counter
    order=plan['order'];types=base.get('types',order)
    P.need(not base.get('optional'),'Dry optional inputs')
    if types==order:
        family='full';name='items/devs1_routed.json';expected=636;indices=[3,0,1,2,4]
        counts=dict(object_abs_distance=150,room_size_estimation=36,camera_displacement=150,camera_rotation=150,camera_movement_direction=150)
    elif types==['room_size_estimation']:
        family='room';name='items/room134.json';expected=134;indices=[4];counts={'room_size_estimation':134}
    elif types==['object_abs_distance']:
        family='distance';name='items/dist580.json';expected=580;indices=[3];counts={'object_abs_distance':580}
    else:raise P.Rejected('Dry selected type order differs')
    P.need(plan.get('stage1_select_rule')=='candidates_argmax' and plan.get('perception_memo')=='on' and plan.get('perception_memo_modules')==['g3t'] and plan.get('perception_memo_verify_ids',[])==[],'Dry settings differ')
    P.need(plan['stage1_select_rule'] in op['RULES'],'Dry rule absent from RULES')
    P.need(len(desc)==1 and desc[0]['types']==indices and desc[0]['expected']==expected,'Dry descriptor count/type order differs')
    P.need(desc[0]['stage1_select_rule']=='candidates_argmax' and desc[0]['perception_memo']=='on','Dry descriptor settings differ')
    P.need(memory['fits'] is True and memory['basis']=='fixed_g3t_shapes' and memory['sam_measurement_required'] is False,'Dry memory differs')
    P.need(name in pay,'Dry full-reader manifest missing')
    got=Counter(r['question_type'] for r in json.loads(pay[name])['items'])
    P.need(sum(got.values())==expected and dict(got)==counts,'Dry per-type item counts differ')
    return dict(family=family,expected=expected,types=indices,item_counts=dict(got))

def dry_fill_identity(inputs,base,plan,pins,helper):
    """Exact dry binding predicates and one authenticated policy archive slot."""
    P.need(not inputs.get('optional') and inputs.get('types')==base.get('types'),'Dry filled selection differs')
    binding=plan['export_binding']
    P.need(all(pins.get(k)==binding[k] for k in ('run','step','member_directory','lineage','object')),'Dry export binding differs')
    P.need(all(pins['preparation'][k]['sha256']==v for k,v in binding['preparation_sha256'].items()),'Dry preparation binding differs')
    assignments={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(helper).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='REVIEWED_ARCHIVE_SHA256'}
    P.need(pins.get('archive_sha256')==inputs['archives'][0]['sha256']==assignments['REVIEWED_ARCHIVE_SHA256'],'Dry archive0 differs')
    # Full SHA equality is stronger than the dry harness's 05dc8f79 prefix.
    # The authenticated base slot supplies the pin, including in rebound fixtures.
    policy_sha=base['archives'][4]['sha256'];slots=[i for i,a in enumerate(inputs['archives']) if a['sha256']==policy_sha]
    P.need(slots==[4],'Dry policy archive slot count differs');return 4

def logic(package,w,c):
    f,pay,pub,plan,src=materialize(package,w)
    import torch
    torch.set_num_threads(8)
    data=[]
    for n,b in pay.items():
        if n.endswith('.json'):data.extend(rows(json.loads(b)))
        if n.endswith('.jsonl'):
            for line in b.decode().splitlines():
                if line.strip():data.extend(rows(json.loads(line)))
    for pin in c.get('row_files',[]):
        P.need(P.file_digest(pin['path'])==pin['sha256'],'External rows differ')
        for line in Path(pin['path']).read_text().splitlines():
            if line.strip():data.extend(rows(json.loads(line)))
    count=0
    for r in data:
        v=r.get('student_input',r);n=v.get('total_num_frames');fps=v.get('fps')
        P.need(type(n) is int and n>0,'Frame row total_num_frames must be positive integer')
        P.need(type(fps) in (float,int) and math.isfinite(fps) and fps>0,'Frame row fps must be positive finite')
        indices=v.get('source_frame_indices',v.get('frame_indices'))
        if indices is not None:P.need(indices and all(type(i) is int and 0<=i<n for i in indices),'Frame row indices differ')
        if 'student_input' in r:
            from student_pilot.carrier_c1_data import layout_inputs
            layout_inputs(r,layout=plan.get('export_binding',{}).get('frame_layout','duplicate'))
        count+=1
    P.need(count>0 or c.get('no_rows') is True,'Zero frame rows checked; supply pinned row_files or explicit no_rows')
    entries={'h1eval/h10/launch.py'}|set(c.get('isolated_entries',[]))
    entries|={n for n in pay if Path(n).name=='worker.py' and '/tests/' not in '/'+n and not n.startswith('tree/')}
    for i,n in enumerate(sorted(entries)):
        P.safe_name(n);P.need(n in pay,'Missing isolated entry '+n)
        code='import runpy,sys,torch;torch.set_num_threads(8);sys.path[:0]=sys.argv[2:];'+('import h1eval.h10.launch' if n=='h1eval/h10/launch.py' else 'runpy.run_path(sys.argv[1],run_name="preflight_import")')
        P.run([c.get('python',P.PYTHON),'-I','-s','-B','-c',code,str(src/n),str(src/'b'),str(src/'tree'),str(src)],w,w/('i%d.log'%i))
    op=runpy.run_path(str(package/'a/6.py'));desc=op['descriptors'](str(src));memory=op['memory_bound']()
    P.need(memory['fits'] and not op['memory_bound'](allocation_bytes=1)['fits'],'Memory bound differs')
    from orchard_h10.common import ORDER
    base=P.read(package/'a/0.json');types=base.get('types',list(ORDER))
    P.need(not base.get('optional'),'Unexpected optional input')
    P.need(set(ORDER[t] for d in desc for t in d['types'])==set(types),'Operator type mismatch')
    dry=native_dry_predicates(base,plan,pay,op,desc,memory)
    for d in desc:
        for k in ('stage1_select_rule','perception_memo','perception_memo_modules'):P.need(d[k]==plan[k],'Operator setting differs: '+k)
    settings={k:plan[k] for k in ('stage1_select_rule','perception_memo','perception_memo_modules')};settings.update(perception_memo_verify_ids=plan.get('perception_memo_verify_ids',[]),save_own_depth=False,types=types)
    P.write(w/'2.json',settings)
    cfg=dict(package=str(src),output=str(w/'r'),settings=str(w/'2.json'),plan_sha256=pub['plan_sha256'],inputs_sha256='0'*64,operator_sha256=P.digest(f['a/6.py']),python=sys.executable,export=str(w/'e'),binding=str(w/'b.json'),export_pin=str(w/'p.json'),device='cpu',prefix=[])
    rehearsal=op['rehearsal'](cfg)
    P.need(len(rehearsal)==len(desc) and all(r['expected']==desc[i]['expected'] for i,r in enumerate(rehearsal)),'Rehearsal counts differ')
    from h1eval.items import load_manifest,read_contract
    manifests=[]
    for n,b in pay.items():
        if n.startswith('items/') and n.endswith('.json') and json.loads(b).get('schema')=='h1-items-v1':load_manifest(src/n);manifests.append(n)
    for r in rehearsal:
        args=r['args'];m=load_manifest(args[args.index('--items')+1]);read_contract(m,args[args.index('--arms')+1].split(','),[{'name':x} for x in args[args.index('--modes')+1].split(',')],','.join(r['types']))
        P.need(sum(1 for x in m['items'] if x['question_type'] in r['types'])==r['expected'],'Selected item count differs')
    return dict(native_dry=dry,rows_checked=count,isolated_entries=sorted(entries),memory=memory,manifests=manifests,rehearsal=rehearsal)

def guard(package,w,c):
    f,pay,pub,plan,src=materialize(package,w)
    from orchard_h10.common import install_process_guard, template
    root=w/'a';root.mkdir(mode=0o700);(root/'a').mkdir(mode=0o700)
    op=runpy.run_path(str(package/'a/5.py'))
    # Execute the exact CPU helper environment assignments, including its
    # removal of the template's forbidden sampler variable.
    J=template()[1];os.environ['SLURM_JOB_ID']='123'
    main_node=next(n for n in ast.parse(f['a/5.py']).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    env_nodes=[];collect=False
    for n in main_node.body:
        if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='env' for x in n.targets):collect=True;env_nodes.append(n)
        elif collect and isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='env':env_nodes.append(n)
        elif collect:break
    P.need(env_nodes,'Native CPU environment assignments absent')
    ns=dict(J=J,root=root,os=os);exec(compile(ast.Module(body=env_nodes),'<native environment>','exec'),ns)
    virtual='/tmp/a123'+pub['token']
    for k,v in ns['env'].items():P.opaque(k+'='+str(v).replace(str(root),virtual),c.get('forbidden_extra',()))
    for arg in J.namespace(root):P.opaque(str(arg).replace(str(root),virtual),c.get('forbidden_extra',()))
    install_process_guard(root)
    proof=op['check_bundle_guard'](package,root)
    P.write(root/'a/1.json',dict(action=1,config={}))
    calls=[]
    def terminal(argv,**kw):calls.append(argv)
    proof=op['dispatch_operator'](root,proof,[sys.executable,'-I','-s','-B',str(root/'a/5.py'),str(root/'a/1.json')],terminal)
    P.need(len(calls)==1 and proof['events']==['guard_installed','write_test','operator_dispatch'],'Guard/dispatch order differs')
    # Native guard must reject literal argv, environment values and cwd.
    for args,kw in [(['/bin/echo','model'],{}),(['/bin/true'],{'env':{'A':'dataset'}}),(['/bin/true'],{'cwd':'/tmp/benchmark'})]:
        try:subprocess.run(args,**kw)
        except ValueError:pass
        else:raise P.Rejected('Native guard accepted a forbidden surface')
    proof['python']=sys.version;return proof

def trap(package,w,c):
    text=(package/'BATCH.sh').read_text();P.need("<<'A' &\n" in text and '\nA\n' in text,'Missing background batch wrapper')
    front,rest=text.split("<<'A' &\n",1);body,back=rest.rsplit('\nA\n',1)
    P.need('trap fin EXIT' in front and 'USR1' in back,'Missing EXIT/USR1 trap')
    remote=P.ROOT+'/'+P.PREFIX+P.read(package/'0.json')['token']
    # Substitute only paths and the Python body; execute the actual shell traps.
    front=front.replace(remote,str(w/'p')).replace('/tmp/a${SLURM_JOB_ID:-0}.l',str(w/'0.log'))
    front=front.replace('$(nvidia-smi -L 2>/dev/null | wc -l)','0')
    (w/'p/a').mkdir(parents=True,mode=0o700)
    for label,child,expected,send in [('failure',"print('fixture traceback',flush=True)\nraise SystemExit(23)",23,False),('signal',"import signal,time\nfrom pathlib import Path\ndef stop(*a):\n Path(%r).write_text('slot');raise SystemExit(0)\nsignal.signal(signal.SIGUSR1,stop)\nPath(%r).write_text('ready')\ntime.sleep(10)"%(str(w/'slot'),str(w/'ready')),0,True)]:
        script=w/(label+'.sh');script.write_text(front+"<<'A' &\n"+child+'\nA\n'+back)
        env=P.environment(w);env['SLURM_JOB_ID']='123';p=subprocess.Popen(['bash',str(script)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if send:
            end=time.monotonic()+5
            while not (w/'ready').exists() and p.poll() is None and time.monotonic()<end:time.sleep(.02)
            P.need((w/'ready').exists(),'Signal child never ready');p.send_signal(signal.SIGUSR1)
        out,err=p.communicate(timeout=15);P.need(p.returncode==expected,'Batch exit status differs')
        capture=(w/'p/a/x123').read_text();P.need('node ' in capture and ('exit '+str(expected)) in capture,'EXIT diagnostics absent')
        if not send:P.need('fixture traceback' in capture,'Traceback tail missing')
        else:P.need((w/'slot').exists(),'USR1 not forwarded')
    return dict(exit_status=23,diagnostics=True,usr1_forwarded=True)

def stop(package,w,c):
    f,pay,pub,plan,src=materialize(package,w)
    import torch
    torch.set_num_threads(8)
    from orchard_h10 import runner
    op=runpy.run_path(str(package/'a/6.py'));settings={k:plan[k] for k in ('stage1_select_rule','perception_memo','perception_memo_modules')};settings.update(perception_memo_verify_ids=[],save_own_depth=False);P.write(w/'2.json',settings)
    cfg=dict(package=str(src),output=str(w/'r'),settings=str(w/'2.json'),plan_sha256=pub['plan_sha256'],inputs_sha256='0'*64,operator_sha256=P.digest(f['a/6.py']),python=sys.executable,export=str(w/'e'),binding=str(w/'b.json'),export_pin=str(w/'p.json'),device='cpu',prefix=[])
    cfg=op['prepare'](cfg)[0];cfg.update(stop_margin=0,return_margin=0)
    child=w/'1.py';child.write_text("import sys,time\nfrom pathlib import Path\ns=Path(sys.argv[1]);end=time.time()+3\nwhile not s.exists() and time.time()<end:time.sleep(.01)\nif s.exists():Path(sys.argv[2]).write_text('slot')\nraise SystemExit(0 if s.exists() else 9)\n")
    def launch(argv,**kw):
        # Only the decoder child is replaced; native commands, handlers and summary run.
        p=subprocess.Popen([sys.executable,'-I','-s','-B',str(child),cfg['stop_file'],str(w/'slot')],**kw)
        os.kill(os.getpid(),signal.SIGUSR1);return p
    result=runner.run(cfg,['0'],time.time()+10,launcher=launch)
    P.need((w/'slot').exists() and Path(cfg['stop_file']).exists() and result['stopped'] and not result['failure'],'Native stop handshake failed')
    return dict(slot=True,summary=result,scope='read runner with cooperative tiny CPU child; trainer ranks not covered')

class Mirrors:
    """Map only declared absolute prefixes; keep virtual paths in native metadata."""
    def __init__(self,mapping):self.mapping=sorted(((str(k),str(v)) for k,v in mapping.items()),key=lambda x:-len(x[0]));self.saved=[]
    def path(self,p):
        if isinstance(p,int):return p
        s=os.fsdecode(p)
        for old,new in self.mapping:
            if s==old or s.startswith(old+'/'):return new+s[len(old):]
        return p
    def patch(self,obj,name):
        original=getattr(obj,name)
        def wrapped(path,*args,**kw):return original(self.path(path),*args,**kw)
        self.saved.append((obj,name,original));setattr(obj,name,wrapped)
    def __enter__(self):
        for obj,name in [(builtins,'open'),(io,'open'),(tarfile,'bltn_open')]+[(os,n) for n in ('stat','lstat','mkdir','chmod','access','readlink','listdir','scandir')]:self.patch(obj,name)
        # Python 3.6 pathlib binds os functions at import time.
        if hasattr(Path,'_accessor'):
            acc=Path()._accessor
            for n in ('open','stat','lstat','mkdir','chmod','readlink','listdir','scandir'):
                if hasattr(acc,n):self.patch(acc,n)
        return self
    def __exit__(self,*args):
        for obj,name,value in reversed(self.saved):setattr(obj,name,value)

def validate_mirrors(c):
    total=0;mapping={}
    for remote,spec in c.get('mirrors',{}).items():
        P.opaque(remote,c.get('forbidden_extra',()));path=Path(spec['path']);P.need(path.is_file(),'Missing mirror: '+remote);size=path.stat().st_size;total+=size
        P.need(total<=c.get('max_read_bytes',1024**3),'Mirrors exceed explicitly authorized read budget')
        P.need(size==spec['bytes'] and P.file_digest(path)==spec['sha256'],'Mirror hash/size differs: '+remote);mapping[remote]=str(path)
    return mapping

def login(package,w,c):
    P.need(sys.version_info[:3]==(3,6,8),'Require actual login Python 3.6.8')
    f,pay,pub,plan=P.structure(package);sources={n:b for n,b in f.items() if n.endswith('.py')}
    sources.update({n:b for n,b in pay.items() if n.startswith('orchard_h10/') and n.endswith('.py')});sources.update(P.bundle(f['BATCH.sh']))
    for n,b in sources.items():
        if n.endswith('.py'):compile(b,n,'exec')
    state=Path(c['work'])/'BUILD.json'
    if state.is_file():
        b=P.built(c);P.need(P.untar(Path(b['delivery']).read_bytes())==f,'Login probe delivery differs')
    else:
        raw=w/'1.tgz';raw.write_bytes(P.tar_bytes(f));b=dict(token=pub['token'],delivery=str(raw),sha256=P.file_digest(raw))
    remote=P.remote_path(b);local=w/P.PREFIX if False else w/(P.PREFIX+pub['token'])
    with Mirrors({remote:str(local)}):exec(compile(P.place_code(b),'place','exec'),{})
    P.need(P.package_files(local)==f,'Generated place altered bytes')
    P.need(local.stat().st_mode&0o777==0o700 and (local/'a').stat().st_mode&0o777==0o700,'Place directory modes differ')
    P.need(all(x.stat().st_mode&0o777==0o600 for x in local.rglob('*') if x.is_file()),'Place file modes differ')
    return dict(python=sys.version,generated_place_executed=True,compiled_sources=len(sources),delivery_sha256=b['sha256'],recorded_delivery=state.is_file())

def preserved(base,filled):
    P.need(len(filled['archives'])==len(base['archives'])+1,'Fill must append preparation archive')
    P.need(filled['archives'][1:-1]==base['archives'][1:],'Fill dropped or changed dependency/env archive')
    P.need(filled.get('types')==base.get('types') and not filled.get('optional'),'Fill changed type/optional selection')

def resolve_inputs(inputs,base,cfg,c,mapping,remote,local):
    from orchard_h10.job import check_inputs
    from orchard_h10.export_pins import load
    with Mirrors(dict(mapping,**{remote:str(local)})):
        check_inputs(inputs,cfg,package=Path(remote));pins=load(inputs,Path(remote))
    preserved(base,inputs)
    policy_slot=dry_fill_identity(inputs,base,cfg,pins,(local/'a/4.py').read_text())
    owners={};total=0
    def mapped(path):
        if path.startswith(remote+'/'):return str(local)+path[len(remote):]
        P.need(path in mapping,'Missing archive mirror '+path);return mapping[path]
    for index,a in enumerate(inputs['archives']):
        parts=[];h=__import__('hashlib').sha256()
        for spec in a['parts']:
            path=mapped(spec['path']);P.need(Path(path).stat().st_size==spec['bytes'] and P.file_digest(path)==spec['sha256'],'Archive part pin differs')
            with open(path,'rb') as stream:
                for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
            parts.append(path)
        P.need(h.hexdigest()==a['sha256'],'Whole archive pin differs')
        # Sequential multipart reader uses bounded reads and no joined disk copy.
        class Stream:
            def __init__(self):self.i=0;self.f=open(parts[0],'rb')
            def read(self,n):
                out=[]
                while n and self.i<len(parts):
                    b=self.f.read(n);out.append(b);n-=len(b)
                    if not b:
                        self.f.close();self.i+=1
                        if self.i<len(parts):self.f=open(parts[self.i],'rb')
                return b''.join(out)
            def close(self):self.f.close()
        stream=Stream()
        try:
            with tarfile.open(fileobj=stream,mode='r|*') as t:
                seen=set()
                for m in t:
                    name=m.name
                    while name.startswith('./'):name=name[2:]
                    name=name.rstrip('/')
                    if not name:continue
                    P.safe_name(name);P.need(name not in seen,'Duplicate archive member');seen.add(name)
                    P.need(m.isfile() or m.isdir(),'Archive link/special member')
                    if m.isdir():continue
                    logical=str(Path('/scratch/jjyeung')/Path(a['destination']).relative_to('sj')/name)
                    P.need(logical not in owners,'Duplicate logical member '+logical)
                    hh=__import__('hashlib').sha256();small=[]
                    with t.extractfile(m) as f:
                        for block in iter(lambda:f.read(1024**2),b''):
                            hh.update(block)
                            if m.size<=4*1024**2:small.append(block)
                    owners[logical]=(m.size,hh.hexdigest(),b''.join(small),index)
        finally:stream.close()
    for name,pin in inputs['files'].items():
        P.need(pin['path'] in owners,'Unresolved input '+name);size,h,_,_=owners[pin['path']];P.need(size==pin['bytes'] and h==pin['sha256'],'Input member differs '+name)
    for key in ('python','frames_root','sam_source'):
        target=inputs[key];P.need(target in owners or any(n.startswith(target+'/') for n in owners),'Unresolved '+key)
    policy_paths=[inputs['files'][inputs[k]]['path'] for k in ('policy_receipt','environment_receipt')]+list(inputs['policy'].values())
    P.need(all(owners[n][3]==policy_slot for n in policy_paths),'Policy/environment archive membership differs')
    policy=json.loads(owners[inputs['files'][inputs['policy_receipt']]['path']][2]);P.need(policy.get('authorized') is True and all(policy.get(k)==inputs['policy'][k] for k in ('vnice','terminator')),'Policy authorization differs')
    assets=json.loads(P.untar((local/'0.tgz').read_bytes())['orchard_h10/vendor/ORCHARD_ASSETS.json'])
    for key in ('vnice','terminator'):P.need(owners[inputs['policy'][key]][1]==assets[key+'_sha256'],'Policy executable differs')
    prep=P.untar((local/'a/6').read_bytes());want={v['path']:v for v in pins['preparation'].values()};P.need(set(prep)==set(want),'Preparation inventory differs')
    for n,s in want.items():P.need(P.digest(prep[n])==s['sha256'] and len(prep[n])==s['bytes'],'Preparation member differs')
    return dict(policy_archive_slot=policy_slot,dry_binding_passed=True,archives=len(inputs['archives']),members=len(owners),environment_resolved=inputs['files'][inputs['environment_receipt']]['path'] in owners)

def fill(package,w,c):
    P.need(sys.version_info[:3]==(3,6,8),'Require actual login Python 3.6.8')
    original_files,_,_,original_plan=P.structure(package,c)
    P.export_identity(c,original_files,original_plan)
    if c.get('fill_mode','mirrors')=='structural':
        import pack_structural as S
        reference=S.dependency_reference(json.loads(original_files['a/0.json']),c)
        original=P.fingerprint(P.package_files(package));target,small=S.rebind(w/'standins',package)
        cfg=dict(c,fill_mode='mirrors',mirrors=small['mirrors'],fill=small['fill'],remote_input_pins={k:dict(bytes=v['bytes']) for k,v in small['mirrors'].items()},max_read_bytes=10*1024**2)
        result=fill(target,w,cfg);result.update(mode='structural',source_tree=original,dependency_reference=reference,standin_bytes=sum(x['bytes'] for x in small['mirrors'].values()),production_archive_identity=False)
        P.need(P.fingerprint(P.package_files(package))==original,'Structural probe changed delivery');return result
    P.need(c.get('fill_mode','mirrors')=='mirrors','Unknown fill mode')
    mapping=validate_mirrors(c);f,pay,pub,plan=P.structure(package);remote=P.ROOT+'/'+P.PREFIX+pub['token'];local=P.extract(f,w/(P.PREFIX+pub['token']))
    assets=json.loads(pay['orchard_h10/vendor/ORCHARD_ASSETS.json'])
    required=[dict(path=p,bytes=n,sha256=h) for group in assets['groups'] for p,n,h in group]+[assets['bwrap_pin']]
    for pin in required:
        P.need(pin['path'] in mapping,'Missing template/bwrap mirror '+pin['path'])
        P.need(c['mirrors'][pin['path']]['sha256']==pin['sha256'] and c['mirrors'][pin['path']]['bytes']==pin['bytes'],'Template/bwrap pin differs')
    argv=P.fill_argv(c,remote);saved=sys.argv[:]
    try:
        with Mirrors(dict(mapping,**{remote:str(local)})):
            sys.argv=argv[4:];runpy.run_path(remote+'/a/4.py',run_name='__main__')
            filled=P.read(local/'a/1.json');base=P.read(local/'a/0.json');preserved(base,filled)
            sys.argv=[remote+'/3.py','check','--gpus','1','--time',c['remote']['walltime']]
            runpy.run_path(remote+'/3.py',run_name='__main__')
            from orchard_h10.common import read_config
            cfg=read_config(local)
            # Execute the delivered submit entry under 3.6; only sbatch is replaced.
            calls=[];original_run=subprocess.run
            def sbatch(argv,**kwargs):
                P.need(Path(argv[0]).name=='sbatch','Unexpected submit process')
                P.submit_privacy(argv,pub['token'])
                P.need(kwargs['input']==f['BATCH.sh'],'Submit wrapper bytes differ')
                calls.append(argv);return subprocess.CompletedProcess(argv,0,b'123;local\n',b'')
            try:
                subprocess.run=sbatch
                sys.argv=[remote+'/3.py','submit','--gpus','1','--time',c['remote']['walltime']]
                try:runpy.run_path(remote+'/3.py',run_name='__main__')
                except SystemExit as e:P.need(e.code==0,'Native submit failed')
            finally:subprocess.run=original_run
            P.need(len(calls)==1,'Native submit did not call stub sbatch')
        resolution=resolve_inputs(filled,base,cfg,c,mapping,remote,local)
        dry=native_dry(c,w,mapping,remote,local,filled)
    finally:sys.argv=saved
    P.privacy(local,c)
    return dict(python=sys.version,fill_executed=True,entry_check_executed=True,submit_executed=True,pool=pool_probe(package,w,c),resolution=resolution,native_dry=dry)

def native_dry(c,w,mapping,remote,local,filled):
    """Run the pinned native dryres checker without changing its source bytes."""
    import contextlib
    pin=c.get('native_dry');P.need(pin is not None,'Required input missing: native_dry (pinned dryres_d.py)')
    P.required_inputs(dict(required_inputs=[dict(pin,name='native_dry')]))
    P.need('sha256' in pin,'Required input pin missing: native_dry.sha256')
    saved=sys.argv[:];log=w/'native_dry.log'
    try:
        sys.argv=[pin['path'],remote+'/a/1.json',remote+'/a/0.json',filled['archives'][-1]['sha256']]
        with log.open('w') as output,contextlib.redirect_stdout(output),Mirrors(dict(mapping,**{remote:str(local)})):
            try:runpy.run_path(pin['path'],run_name='__main__')
            except SystemExit as error:P.need(error.code==0,'Native dry harness refused; see '+str(log))
        result=P.read(log);P.need(result.get('passed') is True,'Native dry harness did not pass')
        return dict(path=pin['path'],sha256=pin['sha256'],python=sys.version,result=result)
    finally:sys.argv=saved

def pool_probe(package,w,c):
    script=P.adapted_script(c,'gpu',P.ROOT+'/'+P.PREFIX+P.read(package/'0.json')['token'],package)
    bodies=P.heredocs(script);P.need(len(bodies)==2,'Expected receipt and pool predicates')
    body=bodies[1];tree=ast.parse(body)
    root=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='root' for t in n.targets))
    pool=w/'pool';pool.mkdir(mode=0o700);(pool/'0').write_bytes(b'x')
    def check(expected):
        try:
            with Mirrors({root:str(pool)}):exec(compile(body,'native pool','exec'),{})
        except ValueError:
            P.need(not expected,'Valid pool rejected')
        else:P.need(expected,'Invalid pool accepted')
    check(True)
    # Inject only the stat size for the boundary case; walk the real temporary pool.
    original_stat=os.stat
    def large(path,*args,**kwargs):
        value=original_stat(path,*args,**kwargs)
        if str(path) in (root+'/0',str(pool/'0')):
            fields=list(value);fields[6]=75000001;return os.stat_result(fields)
        return value
    try:os.stat=large;check(False)
    finally:os.stat=original_stat
    return dict(python=sys.version,positive=True,oversize_rejected=True,synthetic_size=True)

def receipt(package,w,c):
    """Run the sealed submit receipt predicate on exact native CPU writer output."""
    predicate_python=subprocess.check_output(['/usr/bin/python3','-I','-s','-B','-c','import sys;print(sys.version)'],env=P.environment(w),timeout=30).decode().strip()
    P.need(predicate_python.startswith('3.6.8'),'Require actual receipt Python 3.6.8')
    f,pay,pub,plan=P.structure(package);local=P.extract(f,w/'p');root=w/'a';root.mkdir(mode=0o700)
    script=P.adapted_script(c,'gpu',P.ROOT+'/'+P.PREFIX+pub['token'],package)
    code=P.heredocs(script)[0];tree=ast.parse(code)
    pairs=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Compare) and isinstance(n.left,ast.ListComp):
            try:value=ast.literal_eval(n.comparators[0])
            except (ValueError,TypeError):continue
            if isinstance(value,list) and value and isinstance(value[0],tuple):pairs=value
    types=P.read(package/'a/0.json').get('types',[])
    records=[dict(passed=True,set=name,item=item,frames=['0'*64]*32,record=dict(id=item,complete=True,type=types[0],output=dict(finish='eos',scores=dict(answer=.5))),official_score=dict(parse_failed=False,score=.5)) for name,item in pairs]
    full=dict(passed=True,device='cpu',records=records)
    requested=['/usr/bin/python3','-I',str(root/'a/5.py'),str(root/'a/1.json')]
    g=dict(passed=True,operator_sha256=P.digest(f['a/6.py']),operator_sha256_before=P.digest(f['a/6.py']),operator_sha256_after=P.digest(f['a/6.py']),write_test=dict(bytes=4*1024**2,sha256=P.digest(b'fixture')),pool=str(root/'wpool'),token=pub['token'],guard_target_sha256=P.digest(pay['orchard_h10/vendor/return_io.py']),batch_sha256=P.digest(f['BATCH.sh']),path='7.py',guard_target='6.py',action='test',events=['guard_installed','write_test','operator_dispatch'],requested_argv=requested,dispatched_argv=requested[:-2]+[str(root/'7.py'),str(root/'a/1.json')])
    memory=runpy.run_path(str(package/'a/6.py'))['memory_bound']()
    cpu_tree=ast.parse(f['a/5.py']);node=next(n for n in ast.walk(cpu_tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='write' and n.args and isinstance(n.args[0],ast.BinOp) and isinstance(n.args[0].right,ast.Constant) and n.args[0].right.value=='CPU.json')
    value=eval(compile(ast.Expression(node.args[1]),'<native CPU receipt>','eval'),dict(entry_sequence=dict(g,entry_sequence_passed=True),bundle_guard=g,full=full,memory=memory,cfg=pub,sha=P.file_digest,package=local,sequence=local/'a/6.py',proof={'fixture':True},ready={'fixture':True},root=root))
    def check(v,label,expect):
        P.write(local/'a/c/CPU.json',v);P.write(local/'a/c/MEMORY.json',v['memory'])
        if 'full_reader' in v:P.write(local/'a/c/FULL_READER.json',v['full_reader'])
        r=subprocess.run(['/usr/bin/python3','-I','-s','-B','-',str(local)],input=code.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=P.environment(w),timeout=30)
        (w/(label+'.log')).write_bytes(r.stdout+r.stderr);P.need((r.returncode==0)==expect,'Native receipt predicate differs: '+label)
    validator=next((n for n in cpu_tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_full_reader'),None)
    validator_cases=0
    if validator is not None:
        ns={};exec(compile(ast.Module(body=[validator],type_ignores=[]),'<native full reader validator>','exec'),ns)
        validate=ns['validate_full_reader'];P.need(validate([{'full_reader':full}])==full,'Native reader validator differs')
        changes=[(['passed'],False),(['device'],'cuda'),(['records'],[]),(['records',0,'record','complete'],False),(['records',0,'record','type'],'invalid'),(['records',0,'record','output','finish'],'invalid'),(['records',0,'official_score','parse_failed'],True)]
        for keys,new in changes:
            bad=copy.deepcopy(full);d=bad
            for key in keys[:-1]:d=d[key]
            d[keys[-1]]=new
            try:validate([{'full_reader':bad}])
            except (ValueError,KeyError):validator_cases+=1
            else:raise P.Rejected('Native full reader validator accepted corruption')
    check(value,'good',True)
    mutations=[(['passed'],False),(['bundle_guard_passed'],False),(['entry_sequence_passed'],False),(['payload'],'0'*64),(['plan'],'0'*64),(['operator_sha256'],'0'*64),(['inputs'],'0'*64),(['bundle_guard','batch_sha256'],'0'*64),(['entry_sequence','events'],[]),(['entry_sequence','guard_target_sha256'],'0'*64),(['entry_sequence','write_test','bytes'],1),(['entry_sequence','write_test','sha256'],'invalid'),(['entry_sequence','requested_argv'],[]),(['memory','fits'],False)]
    if 'full_reader' in value:mutations += [(['full_reader_passed'],False),(['full_reader','records',0,'set'],'invalid'),(['full_reader','records',0,'item'],'invalid'),(['full_reader','records',0,'frames'],[]),(['full_reader','records',0,'official_score','score'],.25)]
    for i,(keys,new) in enumerate(mutations):
        v=copy.deepcopy(value);d=v
        for key in keys[:-1]:d=d[key]
        d[keys[-1]]=new;check(v,'bad'+str(i),False)
    return dict(synthetic_receipt_only=True,negative_cases=len(mutations),full_reader_validator_cases=validator_cases,full_reader_validator=validator is not None,python=sys.version,predicate_python=predicate_python)

def main():
    mode,package,work,config=sys.argv[1:];os.umask(0o077);P.limits();w=Path(work);result=globals()[mode](Path(package),w,P.read(config));result['passed']=True;P.write(w/'1.json',result)
if __name__=='__main__':main()
