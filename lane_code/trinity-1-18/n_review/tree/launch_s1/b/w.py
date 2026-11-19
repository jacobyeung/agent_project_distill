"""Execute the pinned implementation without descriptive process arguments."""
import importlib
import json
import os
from pathlib import Path
import sys
from v import checked, tree, write, pin
from i import authorize, identity, pick, granted
from q0 import enabled, attempt_id

def main(root,mode,arm,*,preflight=False):
    root=Path(root)
    os.environ.setdefault('K3', str(root/'o'/(os.environ.get('SLURM_JOB_ID','local')+'.stop')))
    os.environ.setdefault('R1_STOP_FILE', os.environ['K3'])
    if (root/'o'/(os.environ.get('SLURM_JOB_ID','local')+'.stop')).exists(): raise SystemExit(75)
    auth,cfg=authorize(root,mode,arm)
    if enabled():
        run=importlib.import_module('student_pilot.carrier_c1_run')
        job=attempt_id()
        if mode in ('t','u','s','x'):
            cfg['authorization']=pin(root/'o'/(job+'.3.json'))
        return dispatch(root,mode,arm,auth,cfg,run,root/'o'/job,job)
    cur=json.loads((root/'k/0.json').read_text());job=os.environ['SLURM_JOB_ID']
    # Each rank checks only the small runtime inventory; large inputs are checked
    # by rank zero in the implementation before broadcast.
    tree({'path':cur['record']['file'],'sha256':cur['record']['sha256']},os.environ['TRAINER'],cur['commit'])
    sys.path.insert(0,os.environ['TRAINER'])
    run=importlib.import_module('student_pilot.carrier_c1_run')
    if preflight:
        return run
    out=root/'o'/job
    launch_path=root/'k/launch.json'
    launch=json.loads(launch_path.read_text()) if launch_path.is_file() else {}
    if mode=='p' and launch.get('in_job_admission'):
        import signal
        from d import contract
        from student_pilot.s1_admission import admit
        value=contract(launch,cfg)
        destination=Path(value['directory'])
        destination.mkdir(parents=True,exist_ok=True)
        def stop(*_):
            raise SystemExit(75)
        signal.signal(signal.SIGUSR1,stop)
        admit(pin(root/launch['config']['file']),destination,value['frame_roots'],
              threads=16,prepare_only=True)
        return
    if mode in ('g','h'):
        run.authenticate(cfg)
        allocation=root/'o'/(job+'.3.json')
        if json.loads(allocation.read_text())!=dict(config_sha256=identity(cfg),new_gpus=1,job_id=job,verdict='GO'):
            raise ValueError('Allocation receipt differs')
        from b3900003 import execute
        execute(out,mode,cfg,cur)
        return
    if mode=='o':
        guard=importlib.import_module('tests.test_carrier_c1_overfit')
        os.environ.pop('C1_OVERFIT_REPORT',None)
        report=guard.overfit(cfg['carrier_placement'])
        ok=report['rows']==32 and report['steps']==200 and report['initial_mean_rotation_deg']>30 and report['final_mean_rotation_deg']<30
        write(out.with_suffix('.0.json'),dict(status='PASS' if ok else 'FAIL',source_revision=cur['commit'],
            placement=cfg['carrier_placement'],rows=32,steps=200,rotation_deg=report['final_mean_rotation_deg'],detail=report))
        if not ok: raise ValueError('Learning guard failed')
        return
    run.authenticate(cfg)
    if mode in ('j','n'):
        from x import operation_code
        operation_code(root)
    if mode=='j':
        data=json.loads((root/'k/8.json').read_text())
        from x import routing_input, scanned
        spec=routing_input(root,data['input'])
        values=[data['input']]+[spec[k] for k in ('source','rgb_index','division')]
        values.append({'path':cur['f3_manifest']['file'],'sha256':cur['f3_manifest']['sha256']})
        if spec.get('direct_source') is not None: values.append(spec['direct_source'])
        scanned(root,values)
        module=importlib.import_module('student_pilot.carrier_c1_routing')
        module.build_routing_stream(spec['source'],spec['rgb_index'],spec['division'],
            spec['output'],spec['processor'],allow_paired_anchor=spec.get('allow_paired_anchor',False),
            scene_role=spec.get('scene_role','train'),direct_source=spec.get('direct_source'))
        write(out.with_suffix('.9.json'),{'status':'PASS','input':data['input'],
              'output':pin(Path(spec['output'])/'receipt.json')});return
    if cfg.get('training_mode')=='final':
        from x import scanned
        if os.environ.get('RANK','0')=='0':
            scanned(root,list(cfg['streams'].values())+[cfg['depth_init']])
            scanned(root,[{'path':cur['f3_manifest']['file'],'sha256':cur['f3_manifest']['sha256']}])
            if mode in ('t','u','e','n','x'):
                scanned(root,[cfg['preparation']])
                if cfg.get('admission'): scanned(root,[cfg['admission']])
            if mode in ('u','x') and auth['resume']!='latest': scanned(root,[auth['resume']])
            if mode in ('e','n'): scanned(root,[{'path':cur['f2']['file'],'sha256':cur['f2']['sha256']}])
            if cfg.get('init_artifact'): scanned(root,[cfg['init_artifact']['artifact']])
            for stream,value in cfg['streams'].items():
                if stream=='mdg':
                    continue
                source=json.loads(checked(value).read_text())
                if source.get('schema')=='c1-pose-mix-v1':
                    refused_pose_sources(source)
                    scanned(root,[s[k] for s in source['sources']
                                  for k in ('receipt','clips_plan','dense_plan','teacher','model') if k in s])
                elif mode=='p':
                    # Training legs trust the preparation receipt, which pins every database once.
                    scanned(root,[source['database']])
            source=json.loads(checked(cfg['streams']['routing']).read_text())
            if source.get('scene_role')!='train': raise ValueError('Input selection differs')
        if mode=='p':
            run.prepare(cfg);return
    else:
        previous_inputs(root,cfg,cur)
    if mode in ('t','u','s','e','l','q','n','x'):
        allocation=root/'o'/(job+'.3.json')
        if json.loads(allocation.read_text())!=dict(config_sha256=identity(cfg),new_gpus=granted(auth,mode,arm),job_id=job,verdict='GO'):
            raise ValueError('Allocation receipt differs')
        cfg['authorization']=pin(allocation)
    if mode=='n':
        import torch
        from x import scanned
        scanned(root,[auth['artifact'],auth['heldout']])
        artifact=json.loads(checked(auth['artifact']).read_text())
        if artifact.get('step') not in (100,200): raise ValueError('Artifact step differs')
        heldout=json.loads(checked(auth['heldout']).read_text())
        if heldout.get('schema')!='c1-routing-stream-v1' or heldout.get('scene_role')!='heldout':
            raise ValueError('Input selection differs')
        scanned(root,[heldout['database']])
        module=importlib.import_module('student_pilot.carrier_c1_canary')
        torch.cuda.set_device(0)
        module.run(cfg,auth['artifact'],auth['heldout'],out.with_suffix('.8.json'),torch.device('cuda:0'))
        return
    dispatch(root,mode,arm,auth,cfg,run,out,job)

# A4 r_s is exactly the clean camera pool's 392 ScanNet clips (scene audit 20261110), an evaluation set: never train on it.
REFUSED_POSE_RECEIPTS={'521fcc555b6375a92c9388b7e7b67167f9531bc343994a60d4f2d7a054c87f3a'}

def refused_pose_sources(spec):
    for s in spec.get('sources',[]):
        pin=s.get('receipt') or {}
        if pin.get('sha256') in REFUSED_POSE_RECEIPTS or '/a4/r_s/' in pin.get('path',''):
            raise ValueError('Pose source refused: A4 r_s is the clean camera evaluation pool')

def previous_inputs(root,cfg,cur):
    pins=json.loads((root/'k/5.json').read_text())
    if cfg['streams']!={'pose':pins['preparation']}: raise ValueError('Input source differs')
    if os.environ.get('RANK','0')=='0':
        cert=json.loads((root/'ANON_OK.json').read_text())
        for key in ('preparation','admission','database','model'):
            if pins[key] not in cert['external']: raise ValueError('Input scan absent')
            checked(pins[key])
        frame={'path':cur['f3_manifest']['file'],'sha256':cur['f3_manifest']['sha256']}
        if frame not in cert['external']: raise ValueError('Input scan absent')
        checked(frame)
        previous=json.loads(checked(pins['preparation']).read_text())
        admission=json.loads(checked(pins['admission']).read_text())
        if (previous['database']!=pins['database'] or previous['model']!=pins['model']
                or admission['verdict']!='PASS' or admission['preparation']!=pins['preparation']
                or admission['config_sha256']!=previous['config_sha256']): raise ValueError('Input admission differs')
def dispatch(root,mode,arm,auth,cfg,run,out,job):
    cur=json.loads((root/'k/0.json').read_text())
    if mode=='p':
        run.prepare(cfg);return
    if mode=='c':
        # First-batch check: array task k checks ranks [k*size, (k+1)*size); a plain job checks every rank.
        world,array=cfg['world_size'],os.environ.get('SLURM_ARRAY_TASK_ID')
        task,size=(int(array),int(auth.get('check_group_size',4))) if array else (0,world)
        device='cuda' if run.torch.cuda.is_available() else 'cpu'
        run.first_batch_check(cfg,list(range(task*size,min(world,(task+1)*size))),out.with_suffix(f'.c{task}.json'),device=device)
        if cur.get('trainer_old_commit') and not array:
            # Step 1's rows again on CP1-R's trainer; ab.py records its own failure and never fails the check.
            import subprocess
            write(out.with_suffix('.abcfg.json'),cfg)
            try:
                subprocess.run([sys.executable,'-B',str(root/'b/ab.py'),str(Path(os.environ['TRAINER']).parent/cur['trainer_old_commit']),
                                str(out.with_suffix('.abcfg.json')),str(out)],check=False,timeout=3600)
            except subprocess.TimeoutExpired:
                write(out.with_suffix('.abcmp.json'),dict(schema='c1-trainer-ab-v1',status='TIMEOUT',inert=False))
        return
    if mode=='d':
        report=run.dryrun(cfg,out.with_suffix('.1.json'))
        write(out.with_suffix('.2.json'),dict(status=report['status'],config_sha256=identity(cfg),report=pin(out.with_suffix('.1.json'))));return
    if mode in ('t','u','s','x'):
        if mode in ('u','x') and not pick(auth,'resume',arm): raise ValueError('Explicit continuation pin required')
        cfg['milestone_gate']=pick(auth,'milestone_gate',arm)
        run.train(cfg,smoke_steps=3 if mode=='s' else None,resume_pin=pick(auth,'resume',arm) if mode in ('u','x') else None,
                  **({'export_binding':auth['export_binding']} if mode=='x' else {}))
        if mode=='s' and os.environ.get('RANK','0')=='0':
            report=json.loads((Path(cfg['output'])/'smoke'/job/'smoke.json').read_text())
            report.update(source_revision=cur['commit'],placement=cfg['carrier_placement'],config_sha256=identity(cfg))
            write(out.with_suffix('.4.json'),report)
        return
    import torch
    if not pick(auth,'artifact',arm): raise ValueError('Artifact pin absent')
    if cfg.get('training_mode')=='final':
        from x import scanned
        scanned(root,[auth['artifact']])
        if json.loads(checked(auth['artifact']).read_text()).get('step') not in (100,200):
            raise ValueError('Artifact step differs')
    operation=run.probe if mode=='q' else run.evaluate
    operation(cfg,pick(auth,'artifact',arm),out.with_suffix('.5.json'),torch.device('cuda:0'))

if __name__=='__main__': main(*sys.argv[1:])
