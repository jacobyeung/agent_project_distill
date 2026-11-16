"""CPU-only GT materialization with owned leases and immutable no-retry terminals."""
from __future__ import annotations
import argparse, fcntl, json, os, signal, subprocess, sys, time, traceback
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import common as b

@contextmanager
def locked(path, nonblocking=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0))
        yield


def coord_claim(scene):
    import coordination as c
    store=c.Coord(str(b.COORD)); wid=b.work_id(scene)
    for directory in (store.leases,store.completed,store.failed,store.status):
        b.require(Path(directory).is_dir(),'coord store missing')
    if store.is_failed(wid): return False,'already-failed; no retry'
    return c.do_claim(store,wid,{'command':f'CPU GT only; {b.ROOT}; scene={scene}','pid':os.getpid(),'split':'train50k','seed':17,'config_hash':b.CONTRACT_SHA})


def coord_end(scene,success,note):
    import coordination as c
    b.lease(scene)
    store=c.Coord(str(b.COORD)); wid=b.work_id(scene)
    b.require(not store.is_completed(wid) and not store.is_failed(wid),'terminal destination exists')
    c.move_lease(store,wid,store.completed if success else store.failed,status='completed' if success else 'failed',ended_at=b.utc(),result=note)
    directory=Path(store.completed if success else store.failed)/f'{wid}.lock'/'lease.json'
    return b.pin(directory)


def heartbeat(scene):
    import coordination as c
    b.lease(scene)
    c.cmd_heartbeat(c.Coord(str(b.COORD)),SimpleNamespace(work_id=b.work_id(scene),status=None,note='CPU GT materialization; '+str(b.ROOT)))


def terminal(scene,status,**kwargs):
    return b.write(b.JOBS/scene/'TERMINAL.json',dict(scene=scene,status=status,ended_at=b.utc(),owner=b.OWNER,work_id=b.work_id(scene),no_retry=True,**kwargs))


def skip(scene,blocking_class):
    job=b.JOBS/scene
    if (job/'TERMINAL.json').exists(): return
    won,reason=coord_claim(scene)
    proof=coord_end(scene,False,blocking_class) if won else None
    terminal(scene,'skipped_blocked',blocking_class=blocking_class,prior_disposition=b.CONFIG['prior_dispositions'].get(scene),lease_terminal=proof,lease_claim=dict(won=won,reason=reason),process=b.identity())


def execute(stage,argv,job,scene,deadline,dry):
    b.verify_scripts()
    record=dict(stage=stage,argv=argv,started_at=b.utc(),environment=b.ENV,wrapper=b.verify_scripts())
    b.write(job/f'{stage}_START.json',record)
    proc=None
    with (job/f'{stage}.log').open('xb') as log:
        try:
            proc=subprocess.Popen(argv,env=b.ENV,cwd=b.ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            b.write(job/f'{stage}_PROCESS.json',b.identity(proc.pid))
            heartbeat_at=time.monotonic()
            while proc.poll() is None:
                if time.time()>=deadline: raise TimeoutError('six-hour/job cap reached')
                if not dry and time.monotonic()-heartbeat_at>=45:
                    heartbeat(scene);heartbeat_at=time.monotonic()
                time.sleep(1)
            b.require(proc.returncode==0,f'{stage} refused with exit {proc.returncode}; see {job}/{stage}.log')
        except BaseException:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=15)
            raise
        finally:
            b.write(job/f'{stage}_END.json',dict(record,ended_at=b.utc(),return_code=proc.returncode if proc else None,log=b.pin(job/f'{stage}.log')))


def worker(scene,deadline,dry=False):
    b.require_env();b.verify_scripts();b.verify_sources()
    plan=b.scene_plan(scene,dry=dry)
    job=b.ROOT/'dry_run' if dry else b.JOBS/scene
    job.mkdir(parents=True,exist_ok=True)
    owned=False; status='failed';error=None;validation=None
    def interrupted(signum,frame): raise InterruptedError(f'owned worker received signal {signum}')
    signal.signal(signal.SIGTERM,interrupted)
    with locked(job/'WORKER.lock',True):
        b.require(not (job/'START.json').exists() and not (job/'TERMINAL.json').exists(),'no retry: job already started or terminal')
        b.write(job/'START.json',dict(scene=scene,process=b.identity(),deadline=deadline,started_at=b.utc(),contract=b.pin(b.ROOT/'CONTRACT.json'),dry=dry))
        try:
            if not dry:
                owned,reason=coord_claim(scene)
                b.write(job/'LEASE_CLAIM.json',dict(won=owned,reason=reason))
                if not owned:
                    terminal(scene,'skipped_blocked',blocking_class='coordination_conflict',reason=reason,process=b.identity())
                    return
            b.verify_pin(plan['frames_receipt'])
            argv=[b.PYTHON,'-B',str(b.PACKAGE/'prepare_gt_scene.py')]
            args=['--scene',scene,'--frames-receipt',plan['frames_receipt']['path'],
                  '--frames-receipt-sha256',plan['frames_receipt']['sha256'],
                  '--contract',str(b.CONTRACT),'--contract-sha256',b.CONTRACT_SHA]
            execute('prepare',argv+['prepare',*args,'--output',plan['output']],job,scene,deadline,dry)
            execute('validate',[b.PYTHON,'-B',str(b.ROOT/'validate_scene.py'),'--scene',scene]+(['--dry'] if dry else []),job,scene,deadline,dry)
            validation=b.pin(job/'VALIDATION.json');b.verify_sources(); status='completed'
        except BaseException as exc:
            error=f'{type(exc).__name__}: {exc}'
            b.write(job/'ERROR.json',dict(error=error,traceback=traceback.format_exc()))
        finally:
            proof=coord_end(scene,status=='completed',f'{status}; validation={validation}; error={error}') if owned else None
            result=dict(validation=validation,error=error,lease_terminal=proof,process=b.identity())
            if dry: b.write(job/'TERMINAL.json',dict(scene=scene,status=status,ended_at=b.utc(),**result))
            elif not (job/'TERMINAL.json').exists():terminal(scene,status,**result)
    if status!='completed': raise RuntimeError(error)


def census():
    result={}
    for row in b.load_plan():
        path=b.JOBS/row['scene']/'TERMINAL.json'
        if path.exists():result[row['scene']]=b.read_json(path)
    return result


def publish_ready(final=False):
    with locked(b.READY/'REGISTRY.lock'):
        terms=census()
        completed=sorted(s for s,t in terms.items() if t['status']=='completed')
        count=len(completed); index_path=b.READY/'READY_INDEX.json'
        previous=b.read_json(index_path)['ready_count'] if index_path.exists() else 0
        threshold=((previous//b.CONFIG['registry_every'])+1)*b.CONFIG['registry_every']
        if count<threshold and not (final and count>previous):return
        if not count:return
        if not final: completed=completed[:threshold]; count=len(completed)
        rows=[]
        for scene in completed:
            term=terms[scene]; b.verify_pin(term['validation']); b.verify_pin(term['lease_terminal'])
            lease=b.read_json(term['lease_terminal']['path'])
            b.require(lease['agent_id']==b.OWNER and lease['status']=='completed','completion ownership mismatch')
            value=b.read_json(term['validation']['path'])
            b.require(value['status']=='PASS' and value['validated_slots']==32,'incomplete validation')
            b.require(value['source_contract']==b.pin(b.CONTRACT) and value['script_manifest']==b.pin(b.ROOT/'CONTRACT.json'),'validation contract drift')
            for spec in value['output_files'].values():b.verify_pin(spec)
            rows.append(dict(scene=scene,runtime_scene_id=value['runtime_scene_id'],question_count=value['membership']['question_count'],qids=value['membership']['qids'],taskmix=value['membership']['taskmix'],scene_receipt=value['scene_receipt'],validation=term['validation'],output_size_bytes=value['output_size_bytes']))
        target=b.READY/f'REGISTRY_{count:02d}.json'
        reg=b.write(target,b.registry([r['scene_receipt'] for r in rows]))
        from collect import registry_rows
        b.require(len(registry_rows({'assets_registry':str(target)}))==count,'reviewed registry gate mismatch')
        index=dict(schema='req232-additional-ready-index-v1',ready_count=count,expected_count=234,question_count=sum(r['question_count'] for r in rows),scenes=rows,registry=reg,dispositions={s:t['status'] for s,t in terms.items()},training_only=True,benchmark_score_claim=False)
        b.write(index_path,index,replace=True)
        lines=[]
        for path in sorted(b.READY.glob('REGISTRY_[0-9]*.json')):lines.append(f'{b.sha(path)}  {path}')
        b.write(b.READY/'REGISTRY_SHA256.txt','\n'.join(lines)+'\n',replace=True)


def health(write=False):
    terms=census(); counts={k:sum(t['status']==k for t in terms.values()) for k in ('completed','failed','skipped_blocked')}
    hosts={}
    for host in b.CONFIG['host_caps']:
        state=b.ROOT/f'HOST_{host}.json'
        if state.exists():hosts[host]=b.read_json(state)
    started=min((v['started_epoch'] for v in hosts.values()),default=time.time())
    elapsed=max(1,time.time()-started); success=counts['completed'];remaining=234-len(terms)
    result=dict(checked_at=b.utc(),counts=counts,remaining=remaining,elapsed_seconds=elapsed,successes_per_hour=success*3600/elapsed,eta_seconds=remaining*elapsed/(success+counts['failed']) if success+counts['failed'] else None,hosts=hosts,registry=b.read_json(b.READY/'READY_INDEX.json')['registry'] if (b.READY/'READY_INDEX.json').exists() else None)
    if write:
        with locked(b.ROOT/'STATUS.lock'):
            b.write(b.ROOT/'HEALTH.json',result,replace=True)
            b.write(b.ROOT/'STATUS.md',f"GT materialization: {success} completed, {counts['failed']} failed, {counts['skipped_blocked']} skipped, {remaining} pending or running.\nChecked: {result['checked_at']}. Rate: {result['successes_per_hour']:.1f} successful scenes/hour. ETA seconds: {result['eta_seconds']}.\nRegistry: {result['registry']}.\nHosts: {json.dumps(hosts,sort_keys=True)}\n",replace=True)
    return result


def process_progress(pid):
    try:
        root=Path('/proc')/str(pid)
        io={k:int(v) for k,v in (line.split(':') for line in (root/'io').read_text().splitlines())}
        fields=(root/'stat').read_text().rsplit(')',1)[1].split()
        return dict(read_chars=io['rchar'],read_bytes=io['read_bytes'],cpu_ticks=int(fields[11])+int(fields[12]))
    except (FileNotFoundError,ProcessLookupError):return {'exited':True}


def debug(active):
    result={}
    for scene,p in active.items():
        job=b.JOBS/scene;logs={}
        for name in ('inspect','prepare','validate'):
            path=job/f'{name}.log'
            if path.exists():
                with path.open('rb') as handle:
                    handle.seek(max(0,path.stat().st_size-1800));logs[name]=handle.read().decode(errors='replace')
        children={}
        for receipt in job.glob('*_PROCESS.json'):
            child=b.read_json(receipt)
            if b.same_process(child):children[receipt.name]=process_progress(child['pid'])
        result[scene]=dict(return_code=p.poll(),process=b.identity(p.pid) if p.poll() is None else None,logs=logs,progress=process_progress(p.pid),children=children)
    return result


def controller():
    b.require_env();b.verify_scripts();b.verify_sources()
    host=b.host();slots=b.CONFIG['host_caps'][host];hosts=list(b.CONFIG['host_caps'])
    d_count=sum(line.split()[0].startswith('D') for line in subprocess.check_output(['/bin/ps','-eo','stat='],text=True).splitlines() if line.split())
    if os.cpu_count()<32 or d_count>8: slots=min(slots,8)
    b.write(b.ROOT/'RESOURCE_CHECK.json',dict(nproc=os.cpu_count(),d_state=d_count,slots=slots,checked_at=b.utc()))
    with locked(b.ROOT/f'CONTROLLER_{host}.lock',True):
        start=b.ROOT/f'CONTROLLER_{host}_START.json'
        b.require(not start.exists(),'controller restart prohibited')
        epoch=time.time(); deadline=epoch+b.CONFIG['max_seconds']
        b.write(start,dict(process=b.identity(),started_at=b.utc(),started_epoch=epoch,deadline=deadline,slots=slots,contract=b.pin(b.ROOT/'CONTRACT.json')))
        plan=b.load_plan()
        if host==hosts[0]:
            for row in plan:
                if row['blocking_class']:skip(row['scene'],row['blocking_class'])
        eligible=sorted((r for r in plan if r['blocking_class'] is None),key=lambda r:(-r['question_count'],r['scene']))
        queue=[r['scene'] for i,r in enumerate(eligible) if i%len(hosts)==hosts.index(host)]
        active={};next_check=time.time()+60;interval=60;empty=0;last_count=0;last_signature=None;defect_checks=0;stop=None
        try:
            while queue or active:
                if time.time()>=deadline:stop='six-hour cap reached'
                for scene,p in list(active.items()):
                    if p.poll() is not None:
                        if not (b.JOBS/scene/'TERMINAL.json').exists():
                            stop=f'worker exited without terminal: {scene}; rc={p.returncode}'
                            try: proof=coord_end(scene,False,stop)
                            except (ValueError,FileNotFoundError):proof=None
                            terminal(scene,'failed',error=stop,lease_terminal=proof)
                        active.pop(scene)
                if stop:
                    for p in active.values():
                        if p.poll() is None:p.terminate()
                    for p in active.values():p.wait(timeout=40)
                    active.clear()
                    for scene in queue:skip(scene,'supervision_halt: '+stop)
                    queue.clear()
                while queue and len(active)<slots:
                    scene=queue.pop(0);job=b.JOBS/scene;job.mkdir(parents=True,exist_ok=True)
                    if (job/'TERMINAL.json').exists() or (job/'START.json').exists():
                        raise RuntimeError(f'no retry: existing job {scene}')
                    with (job/'worker.log').open('xb') as log:
                        p=subprocess.Popen([b.PYTHON,'-B',str(b.ROOT/'run_batch.py'),'worker','--scene',scene,'--deadline',str(deadline)],cwd=b.ROOT,env=b.ENV,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                    b.write(job/'LAUNCH.json',dict(process=b.identity(p.pid),controller=b.identity(),launched_at=b.utc()))
                    active[scene]=p
                b.write(b.ROOT/f'HOST_{host}.json',dict(process=b.identity(),started_epoch=epoch,checked_at=b.utc(),active={s:b.identity(p.pid) for s,p in active.items() if p.poll() is None},queued=len(queue),status='stopped' if stop else 'running',stop=stop),replace=True)
                publish_ready()
                if time.time()>=next_check:
                    terms=census();count=sum(t['status'] in ('completed','failed') for t in terms.values())
                    alive=all(p.poll() is None for p in active.values())
                    progress=count>last_count
                    check=dict(checked_at=b.utc(),processes_alive=alive,terminals=count,terminal_delta=count-last_count,interval_seconds=interval)
                    if not progress and active:
                        empty+=1;interval=60
                        if empty>=2:
                            details=debug(active);check['debug']=details
                            signature=b.digest_value({s:{'logs':d['logs'],'return_code':d['return_code'],'progress':d['progress'],'children':d['children']} for s,d in details.items()})
                            defect_checks=defect_checks+1 if signature==last_signature else 1
                            last_signature=signature
                            if defect_checks>=2:stop='two diagnostic checks found no terminal, log, I/O, or CPU progress'
                    elif progress:
                        empty=0;defect_checks=0;interval=min(600,interval+60)
                    b.write(b.ROOT/'health_receipts'/f'{host}_{time.time_ns()}.json',check)
                    last_count=count;next_check=time.time()+interval
                health(write=True)
                if queue or active:time.sleep(5)
            publish_ready(final=True)
            b.write(b.ROOT/f'HOST_{host}.json',dict(process=b.identity(),started_epoch=epoch,checked_at=b.utc(),active={},queued=0,status='stopped' if stop else 'finished',stop=stop),replace=True)
            health(write=True)
            final_report()
        except BaseException as exc:
            b.write(b.ROOT/f'CONTROLLER_{host}_ERROR.json',dict(error=str(exc),traceback=traceback.format_exc()))
            for p in active.values():
                if p.poll() is None:p.terminate()
            for p in active.values():p.wait(timeout=40)
            for scene in queue:skip(scene,'controller_error: '+str(exc))
            publish_ready(final=True);health(write=True);final_report()
            raise


def compare_dry():
    job=b.ROOT/'dry_run'; reference=Path(b.CONFIG['dry_reference']['path']).parent; target=job/'assets'
    b.verify_pin(b.CONFIG['dry_reference'])
    differences=[];equal=[]
    for old in sorted(reference.iterdir()):
        if not old.is_file():continue
        new=target/old.name;b.require(new.is_file(),f'missing dry file {old.name}')
        if b.sha(old)==b.sha(new):equal.append(old.name);continue
        b.require(old.suffix=='.json',f'non-JSON content hash changed: {old.name}')
        a=b.read_json(old);c=b.read_json(new)
        def normalize(value):
            if isinstance(value,list):return [normalize(x) for x in value]
            if isinstance(value,dict):
                result={k:normalize(v) for k,v in value.items()}
                if set(('path','sha256','size_bytes'))<=set(value):
                    path=Path(value['path'])
                    if path.is_relative_to(reference) or path.is_relative_to(target):
                        rel=path.relative_to(reference if path.is_relative_to(reference) else target)
                        result['path']='<OUTPUT>/'+str(rel)
                        # Dependent JSON pin bytes change when embedded output paths change.
                        if path.suffix=='.json':
                            normalized=normalize(b.read_json(path));result['sha256']=b.digest_value(normalized);result['size_bytes']=len(b.canonical(normalized))
                return result
            return value
        b.require(normalize(a)==normalize(c),f'unexplained content change: {old.name}')
        differences.append(dict(file=old.name,reference_sha256=b.sha(old),dry_sha256=b.sha(new),explanation='Output absolute paths differ; dependent JSON hashes and byte sizes follow those paths. Normalized complete JSON content matches.'))
    result=dict(status='PASS',reference=b.CONFIG['dry_reference'],dry=b.pin(target/'scene_receipt.json'),byte_identical_files=equal,explained_differences=differences,validation=b.pin(job/'VALIDATION.json'))
    b.write(b.ROOT/'DRY_RUN_COMPARISON.json',result);print(json.dumps(result))


def final_report():
    from datetime import datetime
    terms=census(); rows=[]
    for plan in b.load_plan():
        scene=plan['scene']; job=b.JOBS/scene; term=terms.get(scene,{})
        refusal=job/'assets/REFUSAL_RECEIPT.json'
        detail=b.read_json(refusal) if refusal.exists() else {}
        prior=term.get('prior_disposition') or {}
        start=b.read_json(job/'START.json')['started_at'] if (job/'START.json').exists() else None
        end=term.get('ended_at')
        elapsed=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds() if start and end else 0
        rows.append(dict(scene=scene,status=term.get('status','missing'),question_count=plan['question_count'],
            elapsed_seconds=elapsed,gate=detail.get('stage',term.get('blocking_class')),error=detail.get('error',term.get('error',prior.get('error'))),
            terminal=b.pin(job/'TERMINAL.json') if term else None))
    ready=b.read_json(b.READY/'READY_INDEX.json') if (b.READY/'READY_INDEX.json').exists() else None
    success=[r for r in rows if r['status']=='completed']
    result=dict(schema='req232-scannet-final-report-v1',ended_at=b.utc(),scene_count=234,question_count=12662,
        successes=len(success),failures=[r for r in rows if r['status']!='completed'],scenes=rows,
        successful_questions=sum(r['question_count'] for r in success),registry=ready['registry'] if ready else None,
        preparer=b.CONFIG['preparer'],wrapper=b.pin(b.ROOT/'CONTRACT.json'),collector_admissions=0,paid_api_calls=0,gpu_runs=0)
    b.write(b.ROOT/'FINAL_REPORT.json',result)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['controller','worker','dry-run','compare-dry','health'])
    parser.add_argument('--scene');parser.add_argument('--deadline',type=float)
    args=parser.parse_args()
    if args.command=='controller':controller()
    elif args.command=='worker':worker(args.scene,args.deadline)
    elif args.command=='dry-run':worker(b.CONFIG['dry_scene'],time.time()+1800,dry=True);compare_dry()
    elif args.command=='compare-dry':compare_dry()
    else:print(json.dumps(health(),indent=2))

if __name__=='__main__':main()
