
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
"""Job-private staging, reviewed bwrap namespace, and template result return."""
import io
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tarfile
import time

from orchard_h10.common import ORDER, canonical, sha, template, write, opaque, checked_run, read_config


def verify_config(cfg):
    if canonical({k:v for k,v in cfg.items() if k not in ('plan_sha256','payload_sha256','payload_bytes')})!=cfg['plan_sha256']:
        raise ValueError('Plan digest differs')


def check_inputs(inputs, cfg, *, package=None):
    """Fail closed until every unresolved archive and dependency has a full pin."""
    from orchard_h10.export_pins import load, admit
    export = load(inputs, package or Path('/project/community/jjyeung')/cfg['token'])
    import re
    valid=lambda value:isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value)
    if 'types' in inputs:
        types=inputs['types']
        if (not isinstance(types,list) or not types
                or any(not isinstance(kind,str) or kind not in ORDER for kind in types)
                or types!=[kind for kind in ORDER if kind in types]):
            raise ValueError('Invalid type selection')
    if inputs.get('schema')!=1 or not inputs.get('archives'):raise ValueError('Unresolved input archives')
    for a in inputs['archives']:
        if not valid(a.get('sha256')) or not a.get('parts') or a.get('expanded_bytes',0)<=0:
            raise ValueError('Unresolved archive pin or size')
        for part in a['parts']:
            if not valid(part.get('sha256')) or part.get('bytes',0)<=0:raise ValueError('Unresolved archive part')
            if not str(part.get('path','')).startswith('/project/community/jjyeung/'):
                raise ValueError('Stage additional inputs to the registered community namespace')
        target=Path(a['destination'])
        if target.is_absolute() or '..' in target.parts or str(target)!=str(Path('sj')/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'d'):
            raise ValueError('Additional archives must unpack under the stable data root')
    needed={'artifact','heads','full_weights','g3t_weights','g3t_config','base_config','original_model'}
    if not needed<=inputs.get('files',{}).keys():raise ValueError('Unresolved dependency files')
    for name,f in inputs['files'].items():
        if not valid(f.get('sha256')) or f.get('bytes',0)<=0:raise ValueError('Unresolved file pin: '+name)
        path=Path(f.get('path',''))
        if not path.is_relative_to(Path(cfg['logical'])/'d') or '..' in path.parts:
            raise ValueError('Input file must live under the stable data root')
    admit(inputs, cfg, export)
    for name,prefix in [('g3t_weights','d460957b'),('g3t_config','5aeb2acd')]:
        if not inputs['files'][name]['sha256'].startswith(prefix):raise ValueError('E51')
    for key in ('frames_root',):
        path=Path(inputs.get(key,''))
        if '..' in path.parts or not path.is_relative_to(Path(cfg['logical'])/'d'):raise ValueError('Missing logical '+key)
    if not inputs.get('python') or not inputs.get('policy',{}).get('vnice') or not inputs['policy'].get('terminator'):
        raise ValueError('Python or vnice/terminator contract unresolved')
    # A new/overlaid environment needs authenticated archives; the template environment alone
    # does not establish torchvision, transformers 5.12+, scipy, or SAM dependencies.
    if not inputs.get('environment_receipt') or not inputs.get('policy_receipt'):
        raise ValueError('Require pinned environment and policy receipts in files')
    for key in ('environment_receipt','policy_receipt'):
        if inputs[key] not in inputs['files']:raise ValueError('Unpinned '+key)
    if inputs.get('optional'):
        optional=inputs['optional'];idx=optional['archive']
        if type(idx) is not int or not 0<=idx<len(inputs['archives']):raise ValueError('Optional archive index differs')
        if optional['sha256']!=inputs['archives'][idx]['sha256']:raise ValueError('Optional archive pin differs')
        path=Path(optional['root'])
        if not path.is_relative_to(Path(cfg['logical'])/'d') or '..' in path.parts:raise ValueError('Optional root differs')
    return inputs


def restore_resume(spec, out, cfg, S):
    if not spec:return
    source=Path(spec['path'])
    if source.stat().st_size!=spec['bytes'] or sha(source)!=spec['sha256']:
        raise ValueError('Resume archive differs')
    # Read only the returned journal subtree. Terminal and stop markers are allocation-local.
    with tarfile.open(source) as archive:
        identity=json.load(archive.extractfile('metadata/IDENTITY.json'))
        if identity['plan']!=cfg['plan_sha256']:raise ValueError('Resume plan differs')
        seen=set();total=0
        for entry in archive:
            S.relative(entry.name);total+=entry.size
            if not entry.isfile() or entry.name in seen or total>512*1024**2:raise ValueError('Unsafe resume')
            seen.add(entry.name)
            if entry.name=='metadata/IDENTITY.json' or entry.name.startswith('metadata/journals/'):
                target=Path(out)/entry.name;target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as f:f.write(archive.extractfile(entry).read())


def stage(root, cfg, inputs, S, J):
    from pathlib import Path
    started=time.monotonic()
    root=Path(root); receipts={}; archives=root/'a';archives.mkdir()
    assets=json.loads((Path(__file__).parent/'vendor/ORCHARD_ASSETS.json').read_text())
    payload=dict(path=str(Path('/project/community/jjyeung')/cfg['token']/'0.tgz'),
                 bytes=cfg['payload_bytes'],sha256=cfg['payload_sha256'])
    receipts['code']=S.copy_parts([payload],archives/'c',lambda p:Path(p['path']).open('rb'))
    with (archives/'c').open('rb') as stream:
        S.extract_stream(stream,J.physical(root,cfg['logical']+'/p'),None,32*1024**2)
    for rel,pin in cfg['payload_pins'].items():
        if S.sha(J.physical(root,cfg['logical']+'/p/'+rel))!=pin['sha256']:raise ValueError('Code payload differs')
    from orchard_h10.s import preflight, extract, materialize
    package=J.physical(root,cfg['logical']+'/p')
    preflight(package)
    captures=json.loads((package/'g/2.json').read_text())
    index={}
    # Exact template parts and symlink policy; no template D0 export fetch or unrelated reads.
    from orchard_h10.boot import launch, environment_archive, interpreter_archive, PYTHON_PREFIX
    for i,group in enumerate(assets['groups']):
        if i==0:
            receipts['0']=interpreter_archive(group,root,S)
            continue
        if i!=1:continue
        parts=[dict(path=p,bytes=n,sha256=h) for p,n,h in group]
        dest=archives/str(i)
        receipts[str(i)]=S.copy_parts(parts,dest,lambda p:Path(p['path']).open('rb'))
        S.room(root,dest.stat().st_size);S.unpack(dest,root,links=True)
    bwrap=assets['bwrap_pin']
    receipts['bwrap']=S.copy_parts([bwrap],root/'bwrap',lambda p:Path(p['path']).open('rb'))
    (root/'bwrap').chmod(0o700)
    for i in (3,4):
        receipts['a'+str(i)]=environment_archive(inputs['archives'][i],root,S)
    for name in ('vnice','terminator'):
        if S.sha(J.physical(root,inputs['policy'][name]))!=assets[name+'_sha256']:raise ValueError('E86')
    pre_bytes=payload['bytes']+bwrap['bytes']+sum(p[1] for g in assets['groups'][:2] for p in g)+sum(p['bytes'] for i in (3,4) for p in inputs['archives'][i]['parts'])
    launch(root,cfg,inputs,J,pre_bytes,time.monotonic()-started)
    for i,group in enumerate(assets['groups']):
        if i==1:continue
        parts=[dict(path=p,bytes=n,sha256=h) for p,n,h in group]
        dest=archives/str(i)
        receipts[str(i)]=S.copy_parts(parts,dest,lambda p:Path(p['path']).open('rb'))
        S.room(root,dest.stat().st_size)
        S.unpack(dest,root,links=True,exclude_prefix=PYTHON_PREFIX if i==0 else None)
    for i,a in enumerate(inputs['archives']):
        if i in (3,4):continue
        dest=archives/('a'+str(i))
        receipts['a'+str(i)]=S.copy_parts(a['parts'],dest,lambda p:Path(p['path']).open('rb'),expected_sha=a['sha256'])
        S.room(root,a['expanded_bytes'])
        with dest.open('rb') as stream:
            extract(S,stream,root/a['destination'],a['expanded_bytes'],inputs['retain_roots'],dest,index)
    materialize(index,captures['captures'][captures['first']],J.physical(root,cfg['logical']+'/d'))
    write(J.physical(root,cfg['logical']+'/d/9.json'),dict(index=index,**captures))
    for name,f in inputs['files'].items():
        path=J.physical(root,f['path'])
        if path.suffix=='.json':
            import hashlib
            raw=_a0['raw'](path.read_bytes())
            valid=len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']
        else:valid=path.stat().st_size==f['bytes'] and S.sha(path)==f['sha256']
        if not valid:raise ValueError('E52')
    for name in ('vnice','terminator'):
        path=J.physical(root,inputs['policy'][name])
        if S.sha(path)!=assets[name+'_sha256']:raise ValueError('Policy script differs: '+name)
    # Provenance receipts must attest the paths actually admitted; do not execute a terminator.
    policy=json.loads(J.physical(root,inputs['files'][inputs['policy_receipt']]['path']).read_text())
    if policy.get('vnice')!=inputs['policy']['vnice'] or policy.get('terminator')!=inputs['policy']['terminator'] or policy.get('authorized') is not True:
        raise ValueError('Policy receipt does not authorize these scripts')
    write(root/'STAGING.json',receipts)
    return receipts


def upload_capture(root, cfg, out, return_token, R):
    """Best-effort large-object publication; normal return always follows."""
    from orchard_h10.common import write, sha, opaque
    path = Path(root)/'sj'/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'c/0.gz'
    result = dict(uri=R.GCS_ROOT+'/'+return_token+'c/0.gz', generation=None,
                  bytes=0, sha256=None, items=0, verified=False, error=None)
    try:
        if Path(out).resolve() in path.resolve().parents or str(path).startswith('/project/'):
            raise ValueError('invalid local capture path')
        progress = Path(out)/'metadata/4.json'
        if progress.exists(): result['items'] = json.loads(progress.read_text())['items']
        if not path.is_file(): raise ValueError('capture absent')
        result.update(bytes=path.stat().st_size, sha256=sha(path))
        if result['bytes'] > 1_000_000_000: raise ValueError('capture cap exceeded')
        # Use the same service configuration as the normal return, with no inherited secrets.
        env = {k:v for k,v in os.environ.items() if k in ('PATH','HOME','USER','TMPDIR')}
        env['CLOUDSDK_CONFIG'] = R.CLOUD_CONFIG
        opaque([str(path), result['uri'], *[k+'='+v for k,v in env.items()]])
        subprocess.run(['gcloud','storage','cp',str(path),result['uri']], env=env,
                       check=True, capture_output=True, timeout=1800)
        desc = subprocess.run(['gcloud','storage','objects','describe',result['uri'],'--format=json'],
                              env=env, check=True, capture_output=True, text=True, timeout=60)
        meta = json.loads(desc.stdout); generation = str(meta.get('generation',''))
        if not generation.isdigit() or int(meta.get('size',-1)) != result['bytes']:
            raise ValueError('object metadata differs')
        result['generation'] = generation
        check = path.parent/'1.gz'
        with check.open('xb') as stream:
            subprocess.run(['gcloud','storage','cat',result['uri']+'#'+generation], env=env,
                           check=True, stdout=stream, stderr=subprocess.PIPE, timeout=1800)
        if check.stat().st_size != result['bytes'] or sha(check) != result['sha256']:
            raise ValueError('object readback differs')
        result['verified'] = True
    except Exception as error:
        result['error'] = 'E36:'+type(error).__name__.encode().hex()
    write(Path(out)/'metadata/CAPTURE.json', result)
    return result


def main(root):
    root=Path(root);public=json.loads((root/'0.json').read_text())
    cfg=read_config(Path('/project/community/jjyeung')/public['token']);verify_config(cfg)
    os.umask(0o077)
    from orchard_h10.common import install_process_guard
    install_process_guard(root)
    S,J,R,I,A=template(); job=os.environ['SLURM_JOB_ID']
    n=int(os.environ['A_N']);seconds=int(os.environ['A_T'])
    start=float(os.environ.get('SLURM_JOB_START_TIME',time.time()))
    end=min(start+seconds,float(os.environ.get('SLURM_JOB_END_TIME',start+seconds)))
    out=J.physical(root,cfg['logical']+'/r');out.mkdir(parents=True)
    (out/'metadata').mkdir();(out/'logs').mkdir()
    if not job.isdigit() or not 0<int(job)<2**32:raise ValueError('Invalid allocation ID')
    return_token=cfg['token']+format(int(job),'08x')
    write(out/'metadata/RETURN_ID.json',dict(token=return_token,job=job))
    from orchard_h10.e import capture
    from orchard_h10.budget import window, finish, WORK_RESERVE
    scope=window(end-WORK_RESERVE,R)
    failed=None;summary=None;pool_ready=False
    def interrupted(number,frame):
        (out/'metadata/STOP').write_text(str(number)+'\n')
    for number in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT):signal.signal(number,interrupted)
    try:
        scope.__enter__()
        write(out/'metadata/STORAGE.json',J.storage_proof(root,job=job))
        R.write_test(cfg['pool'],return_token);pool_ready=True
        shared=Path('/project/community/jjyeung')/cfg['token']
        if sha(shared/'a/1.json')!=os.environ['A_I'] or sha(shared/'2.json')!=os.environ['A_C']:
            raise ValueError('Submitted input or CPU receipt changed')
        inputs=check_inputs(json.loads((shared/'a/1.json').read_text()),cfg)
        cpu=json.loads((shared/'2.json').read_text())
        if cpu.get('plan')!=cfg['plan_sha256'] or cpu.get('inputs')!=os.environ['A_I'] or cpu.get('passed') is not True:
            raise ValueError('CPU receipt does not bind this submission')
        from orchard_h10.export_pins import load
        export_pins=load(inputs,shared)
        stage(root,cfg,inputs,S,J)
        write(root/'1.json',inputs)
        if time.time()>=end-cfg['stop_margin'] or (out/'metadata/STOP').exists():raise ValueError('No read budget after staging')
        for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
        env=J.environment(root)
        p=cfg['logical']+'/p'
        env={k:v for k,v in env.items() if 'sam' not in k.lower()}
        env.update(OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',
                   OPENBLAS_NUM_THREADS='16',CUDA_VISIBLE_DEVICES='')
        dispatch=root/'a';dispatch.mkdir(mode=0o700,exist_ok=True)
        (dispatch/'5.py').write_bytes((Path(__file__).parent/'entry.py').read_bytes())
        write(dispatch/'0.json',dict(action=0,package=p,config=cfg,inputs={**inputs,'_export':export_pins}))
        opaque([f'{k}={v}' for k,v in env.items()])
        with capture(out/'metadata/11.json') as log:
            checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'0.json')],
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        restore_resume(inputs.get('resume'),out,cfg,S)
        run_cfg=dict(export_pin=cfg['logical']+'/d/6.json',export_cache=cfg['logical']+'/d/7.json',allocation=job,package=p,output=cfg['logical']+'/r',python=inputs['python'],
                     export=cfg['logical']+'/d/e',binding=cfg['logical']+'/d/binding.json',
                     settings=cfg['logical']+'/d/settings.json',plan_sha256=cfg['plan_sha256'],
                     inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),
                     types=inputs.get('types') or list(ORDER),
                     stop_margin=cfg['stop_margin'],return_margin=cfg['return_margin'],
                     prefix=['bash',inputs['policy']['vnice']])
        if inputs.get('optional'):
            receipt=J.physical(root,cfg['logical']+'/d/8.json')
            run_cfg['optional']=dict(items=p+'/items/r0dev.json',receipt=cfg['logical']+'/d/8.json',sha256=sha(receipt))
        write(dispatch/'1.json',dict(action=1,package=p,config=run_cfg,end=end))
        cards=os.environ.get('CUDA_VISIBLE_DEVICES','').split(',')
        if len(cards)!=n or not all(cards) or not 1<=n<=4 or n*seconds>18000:
            raise ValueError('Allocation differs from GPU/hour contract')
        # Retain assigned GPU evidence once; no occupancy polling or scheduler operations.
        evidence=checked_run(['nvidia-smi','--query-gpu=uuid,name,memory.used','--format=csv'],capture_output=True,text=True,check=True)
        write(out/'metadata/CARDS.json',dict(visible=cards,query=evidence.stdout))
        env['CUDA_VISIBLE_DEVICES']=','.join(cards)
        with capture(out/'metadata/12.json') as log:
            result=checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'1.json')],
                                  env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError('Allocation runner failed; no retry')
        summary=json.loads((out/'SUMMARY.json').read_text())
    except Exception as error:
        from orchard_h10.e import exception
        exception(out/'metadata/9.json',error)
        failed='E98:'+type(error).__name__.encode().hex();write(out/'FAILED.json',dict(error=failed))
    finally:
        scope.__exit__(None,None,None)
        if summary and summary['complete'] and not failed:
            write(out/'COMPLETE.json',dict(plan_sha256=cfg['plan_sha256'],synthetic=False,items=summary['completed']))
        write(out/'metadata/ALLOCATION.json',dict(end=end,plan=cfg['plan_sha256'],failure=failed,summary=summary))
        if pool_ready:
            finish(root,cfg,out,return_token,R,end,upload_capture,write,failed)
        # The template marks partial archives incomplete; SUMMARY distinguishes a clean stop.
    if failed:raise SystemExit(1)
