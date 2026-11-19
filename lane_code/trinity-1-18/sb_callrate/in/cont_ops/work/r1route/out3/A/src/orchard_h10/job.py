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
    export = load(inputs, package or Path('/project/community/jjyeung/okh7')/('a15_cot_ap'+cfg['token']))
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
    needed={'artifact','heads','full_weights','g3t_weights','g3t_config','sam_checkpoint',
            'sam_receipt','selector_weights','selector_config','base_config','original_model'}
    if not needed<=inputs.get('files',{}).keys():raise ValueError('Unresolved dependency files')
    for name,f in inputs['files'].items():
        if not valid(f.get('sha256')) or f.get('bytes',0)<=0:raise ValueError('Unresolved file pin: '+name)
        path=Path(f.get('path',''))
        if not path.is_relative_to(Path(cfg['logical'])/'d') or '..' in path.parts:
            raise ValueError('Input file must live under the stable data root')
    admit(inputs, cfg, export)
    expected={'sam_checkpoint':'9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e',
              'selector_weights':'6d97c52407b7e106a7b475040558ba313589514c23c33b6994f4e7a0bb1df6c1'}
    for name,h in expected.items():
        if inputs['files'][name]['sha256']!=h:raise ValueError('Registered dependency differs: '+name)
    for name,prefix in [('g3t_weights','d460957b'),
                        ('g3t_config','5aeb2acd'),('sam_checkpoint','9999e234')]:
        if not inputs['files'][name]['sha256'].startswith(prefix):raise ValueError('Registered pin prefix differs: '+name)
    for key in ('frames_root','sam_source'):
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
    root=Path(root); receipts={}; archives=root/'a';archives.mkdir()
    assets=json.loads((Path(__file__).parent/'vendor/ORCHARD_ASSETS.json').read_text())
    payload=dict(path=str(Path('/project/community/jjyeung/okh7')/('a15_cot_ap'+cfg['token'])/'0.tgz'),
                 bytes=cfg['payload_bytes'],sha256=cfg['payload_sha256'])
    receipts['code']=S.copy_parts([payload],archives/'c',lambda p:Path(p['path']).open('rb'))
    with (archives/'c').open('rb') as stream:
        S.extract_stream(stream,J.physical(root,cfg['logical']+'/p'),None,32*1024**2)
    for rel,pin in cfg['payload_pins'].items():
        if sha(J.physical(root,cfg['logical']+'/p/'+rel))!=pin['sha256']:raise ValueError('Code payload differs')
    # Exact template parts and symlink policy; no template D0 export fetch or unrelated reads.
    for i,group in enumerate(assets['groups']):
        parts=[dict(path=p,bytes=n,sha256=h) for p,n,h in group]
        dest=archives/str(i)
        receipts[str(i)]=S.copy_parts(parts,dest,lambda p:Path(p['path']).open('rb'))
        S.room(root,dest.stat().st_size);S.unpack(dest,root,links=True)
    bwrap=assets['bwrap_pin']
    receipts['bwrap']=S.copy_parts([bwrap],root/'bwrap',lambda p:Path(p['path']).open('rb'))
    (root/'bwrap').chmod(0o700)
    for i,a in enumerate(inputs['archives']):
        dest=archives/('a'+str(i))
        receipts['a'+str(i)]=S.copy_parts(a['parts'],dest,lambda p:Path(p['path']).open('rb'),expected_sha=a['sha256'])
        S.room(root,a['expanded_bytes'])
        with dest.open('rb') as stream:
            S.extract_stream(stream,root/a['destination'],None,a['expanded_bytes'],links=True)
    for name,f in inputs['files'].items():
        path=J.physical(root,f['path'])
        if path.stat().st_size!=f['bytes'] or S.sha(path)!=f['sha256']:raise ValueError('Input differs: '+name)
    for name in ('vnice','terminator'):
        path=J.physical(root,inputs['policy'][name])
        if S.sha(path)!=assets[name+'_sha256']:raise ValueError('Policy script differs: '+name)
    # Provenance receipts must attest the paths actually admitted; do not execute a terminator.
    policy=json.loads(J.physical(root,inputs['files'][inputs['policy_receipt']]['path']).read_text())
    if policy.get('vnice')!=inputs['policy']['vnice'] or policy.get('terminator')!=inputs['policy']['terminator'] or policy.get('authorized') is not True:
        raise ValueError('Policy receipt does not authorize these scripts')
    write(root/'STAGING.json',receipts)
    return receipts


def main(root):
    root=Path(root);public=json.loads((root/'0.json').read_text())
    cfg=read_config(Path('/project/community/jjyeung/okh7')/('a15_cot_ap'+public['token']));verify_config(cfg)
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
    failed=None;summary=None;pool_ready=False
    def interrupted(number,frame):
        (out/'metadata/STOP').write_text(str(number)+'\n')
    for number in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT):signal.signal(number,interrupted)
    try:
        write(out/'metadata/STORAGE.json',J.storage_proof(root,job=job))
        R.write_test(cfg['pool'],return_token);pool_ready=True
        shared=Path('/project/community/jjyeung/okh7')/('a15_cot_ap'+cfg['token'])
        if sha(shared/'a/1.json')!=os.environ['A_I'] or sha(shared/'2.json')!=os.environ['A_C']:
            raise ValueError('Submitted input or CPU receipt changed')
        inputs=check_inputs(json.loads((shared/'a/1.json').read_text()),cfg)
        cpu=json.loads((shared/'2.json').read_text())
        if cpu.get('plan')!=cfg['plan_sha256'] or cpu.get('inputs')!=os.environ['A_I'] or cpu.get('passed') is not True:
            raise ValueError('CPU receipt does not bind this submission')
        from orchard_h10.export_pins import load
        export_pins=load(inputs,shared)
        write(out/'metadata/EXPORT_PIN.json',export_pins)
        write(out/'metadata/INPUTS.json',inputs)
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
        with (out/'logs/0.log').open('wb') as log:
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
        evidence=checked_run(['nvidia-smi','--query-gpu=uuid,name,memory.used','--format=csv'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,check=True)
        write(out/'metadata/CARDS.json',dict(visible=cards,query=evidence.stdout))
        env['CUDA_VISIBLE_DEVICES']=','.join(cards)
        with (out/'logs/1.log').open('wb') as log:
            result=checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'1.json')],
                                  env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError('Allocation runner failed; no retry')
        summary=json.loads((out/'SUMMARY.json').read_text())
    except Exception as error:
        failed=str(error);write(out/'FAILED.json',dict(error=failed))
    finally:
        if summary and summary['complete'] and not failed:
            write(out/'COMPLETE.json',dict(plan_sha256=cfg['plan_sha256'],synthetic=False,items=summary['completed']))
        write(out/'metadata/ALLOCATION.json',dict(end=end,plan=cfg['plan_sha256'],failure=failed,summary=summary))
        if pool_ready:
            returned=R.publish(out,cfg['pool'],return_token,cfg['plan_sha256'],1 if failed else 0)
            write(root/'RETURN.json',returned)
        # The template marks partial archives incomplete; SUMMARY distinguishes a clean stop.
    if failed:raise SystemExit(1)
