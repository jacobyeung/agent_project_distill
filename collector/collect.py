#!/usr/bin/env python
"""Run ready training scenes through the existing resizable episode pool."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,signal,socket,subprocess,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path
import urllib.request
from training_assets import DATA_ROOT,COORD_ROOT,teacher_rows,sha,read_json,require_data_path
from pool_harness.atomicfs import publish_json_exclusive,AlreadyExists,replace_json
from pool_harness.state import Episode,EpisodeCatalog,EpisodeQueue,PoolConfig,TargetStore,Target
from pool_harness.pool import PoolController,WorkerLoop

HERE=Path(__file__).resolve().parent
PYTHON='/data2/jjyeung/envs/planner/bin/python'


def verify_source(config=None):
    from audit_package import verify_contract
    config=config or {'source_contract':os.environ['R1313_CONTRACT_PATH'],'source_contract_sha256':os.environ['R1313_CONTRACT_SHA256']}
    return verify_contract(config['source_contract'],config['source_contract_sha256'])


def coord_guard(config):
    from coordination import validate_work_id
    validate_work_id(config['work_id'])
    root=Path(config.get('coord_root',COORD_ROOT)).resolve()
    mode=config.get('mode','production')
    if mode=='production' and root!=COORD_ROOT:raise ValueError('production must use the normal shared collection lease')
    if mode=='offline_fixture' and not root.is_relative_to(DATA_ROOT/'runtime_control/gt_teacher_r1313'):raise ValueError('fixture lease must stay in the task namespace')
    if mode not in ('production','offline_fixture'):raise ValueError('unknown collection mode')
    lease=read_json(root/'LEASES'/(config['work_id']+'.lock')/'lease.json')
    elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(lease['last_heartbeat'])).total_seconds()
    if lease.get('work_id')!=config['work_id'] or lease.get('status') not in ('running','claimed') or lease['agent_id']!=config['agent_id'] or not 0<=elapsed<1800:raise RuntimeError('stale or foreign collection lease')
    return lease


def heartbeat(config):
    """Retry an idempotent lease heartbeat; timeout exhaustion is a recoverable tick."""
    env=dict(os.environ,AGENT_ID=config['agent_id'],PYTHONDONTWRITEBYTECODE='1')
    command=[PYTHON,'-B',str(HERE/'coordination.py'),'--root',config['coord_root'],'--work-id',config['work_id']]
    for attempt in range(3):
        try:
            subprocess.run(command,env=env,check=True,timeout=30,stdout=subprocess.DEVNULL)
            return True
        except subprocess.TimeoutExpired:
            delay=2**attempt if attempt<2 else 0
            print(json.dumps({'event':'coordination_heartbeat_timeout','attempt':attempt+1,
                              'backoff_seconds':delay,'work_id':config['work_id']}),flush=True)
            if delay:time.sleep(delay)
    return False


def validate_config(config,*,service=False):
    verify_source(config);coord_guard(config)
    root=require_data_path(config['run_root'])
    if config.get('schema')!='r1313-collection-config-v1':raise ValueError('collection config schema mismatch')
    if config['mode']=='production' and root!=DATA_ROOT/'collection_gt_r1313':raise ValueError('r1313 production run root is fixed')
    if config['mode']=='offline_fixture' and not root.is_relative_to(DATA_ROOT/'runtime_control/gt_teacher_r1313'):raise ValueError('fixture output must stay in the task namespace')
    if service and config['mode']!='production':raise ValueError('offline configs cannot launch provider workers')
    if type(config['episode_limit']) is not int or config['episode_limit']<0:raise ValueError('episode limit must be nonnegative')
    if sha(require_data_path(config['assets_registry']))!=config['assets_registry_sha256']:raise ValueError('asset registry changed; bind a new ready-scene config')
    registry_rows(config)
    return config


def load_config(path,*,service=False):
    path=require_data_path(path)
    config=validate_config(read_json(path),service=service)
    return dict(config,_config_path=str(path),_config_sha256=sha(path))


def registry_rows(config):
    registry=read_json(config['assets_registry'])
    if registry.get('schema')!='r1313-assets-registry-v1':raise ValueError('wrong training asset registry')
    by_scene={}
    for pin in registry['receipts']:
        if sha(pin['path'])!=pin['sha256']:raise ValueError('scene receipt drift')
        from gt_scene_assets import verify,validate_scene
        verify(pin)
        row=validate_scene(read_json(pin['path']))
        key=(row['dataset'],row['scene_name'])
        if key in by_scene:raise ValueError('duplicate scene receipt')
        by_scene[key]=pin
    return by_scene


def terminal(config,item):
    path=Path(config['run_root'])/'terminals'/f'{item.episode_id}.json'
    return path.exists() and read_json(path).get('episode_id')==item.episode_id


def objects(config):
    registry=registry_rows(config);rows=teacher_rows();budget=config.get('budget',16384)
    if budget==32768:
        if sha(config['topups'])!=config['topups_sha256']:raise ValueError('top-up selection drift')
        selected=read_json(config['topups']);mapping={r['row']['id']:r for r in selected}
        rows=[r for r in rows if r['id'] in mapping]
        for row in rows:
            authority=mapping[row['id']]
            if row!=authority['row'] or sha(authority['original_trace_path'])!=authority['original_trace_sha256']:raise ValueError('top-up original attempt drift')
            if not read_json(authority['original_trace_path']).get('budget_terminal'):raise ValueError('32k top-up lacks recorded output exhaustion')
    elif budget!=16384:raise ValueError('invalid budget')
    ready=[r for r in rows if (r['dataset'],r['scene_name']) in registry]
    ready.sort(key=lambda r:(r['dataset'],r['scene_name'],r['source_row_1based']))
    pending_assets=len(rows)-len(ready)
    if config.get('episode_limit',0):ready=ready[:config['episode_limit']]
    root=Path(config['run_root'])/f'pool_b{budget}'
    pool_config=PoolConfig('r1313_teacher',1024,spawn_stagger_seconds=3,poll_seconds=3,heartbeat_seconds=15,heartbeat_timeout_seconds=120,max_owners_per_shard=1024)
    target=TargetStore(root,pool_config)
    episodes=[Episode(r['id']+f'__b{budget}',hashlib.sha256((r['dataset']+'/'+r['scene_name']).encode()).hexdigest()[:16],
        {'row':r,'scene_receipt':registry[(r['dataset'],r['scene_name'])],'budget':budget}) for r in ready]
    queue=EpisodeQueue(root,EpisodeCatalog(episodes),target,lambda item:terminal(config,item))
    return target,queue,pending_assets


def initialize(target,workers):
    try:publish_json_exclusive(target.path,Target(workers,max(1,workers)).as_json())
    except AlreadyExists:target.read()


def child_env(config,item,claim):
    env=dict(os.environ)
    for key,value in verify_source(config)['effective_environment'].items():
        if value is None:env.pop(key,None)
        else:env[key]=str(value)
    row=item.payload['row'];pin=item.payload['scene_receipt'];budget=item.payload['budget']
    output=Path(config['run_root'])/'attempts'/row['id']/f'b{budget}'
    env.update(PYTHONDONTWRITEBYTECODE='1',HF_HOME='/data2/jjyeung/cache/huggingface',HUGGINGFACE_HUB_CACHE='/data2/jjyeung/cache/huggingface/hub',TORCH_HOME='/data2/jjyeung/cache/torch',PIP_CACHE_DIR='/data2/jjyeung/cache/pip',
        REQ73_RUN_OUTPUT_ROOT=str(output),REQ73_PLANNER_OUTPUT_BUDGET=str(budget),
        R1313_SCENE_RECEIPT=pin['path'],R1313_SCENE_RECEIPT_SHA256=pin['sha256'],R1313_WORK_ID=config['work_id'],R1313_AGENT_ID=config['agent_id'],
        R1313_EPISODE_CLAIM=str(claim.claim_path),R1313_EPISODE_CLAIM_SHA256=sha(claim.claim_path),R1313_EPISODE_ID=item.episode_id,R1313_QID=row['id'],
        R1313_CONTRACT_PATH=config['source_contract'],R1313_CONTRACT_SHA256=config['source_contract_sha256'],
        R1313_CONFIG_PATH=config['_config_path'],R1313_CONFIG_SHA256=config['_config_sha256'],
        R1308_ARCHIVE_BLOBS_ROOT=str(Path(config['run_root'])/'archive_blobs'),
        MPLCONFIGDIR=str(output/'runtime'/'matplotlib'),TMPDIR=str(output/'runtime'/'tmp'),
        XDG_CACHE_HOME=str(output/'runtime'/'cache'))
    return env,output


def worker(args):
    config=load_config(args.config,service=True);target,queue,_=objects(config)
    def stop_worker(_signum,_frame):raise SystemExit(143)
    signal.signal(signal.SIGTERM,stop_worker)
    def run(item,claim,failed):
        coord_guard(config)
        if shutil.disk_usage(config['run_root']).free<10*1024**3:raise RuntimeError('less than10GiB free; collection remains resumable')
        row=item.payload['row'];input_path=Path(config['run_root'])/'episode_inputs'/f'{row["id"]}.json'
        try:publish_json_exclusive(input_path,row)
        except AlreadyExists:
            if read_json(input_path)!=row:raise ValueError('episode input collision')
        env,output=child_env(config,item,claim)
        if output.exists():raise RuntimeError('attempt already exists; archive preserved, explicit recovery required')
        proc=subprocess.Popen([PYTHON,'-B',str(HERE/'run_experiment_r1313.py'),'--row',str(input_path),'--output',str(output)],env=env)
        try:
            while proc.poll() is None:
                if failed.is_set():raise RuntimeError('heartbeat failed; stopped owned child')
                time.sleep(1)
        finally:
            if proc.poll() is None:proc.terminate()
            proc.wait(timeout=30)
        publish_json_exclusive(Path(config['run_root'])/'terminals'/f'{item.episode_id}.json',
            {'episode_id':item.episode_id,'return_code':proc.returncode,'output':str(output),'question_id':row['id'],'budget':item.payload['budget'],'finished_unix':time.time()})
        # Error/partial terminals remain in the attempted denominator and never silently repeat.
    return WorkerLoop(queue,worker_id=args.worker_id,slot=args.slot,run_episode=run).run()


def start(args):
    from nondeleting_lifecycle import permanent_lock
    config=load_config(args.config,service=True)
    pool=Path(config['run_root'])/f"pool_b{config.get('budget',16384)}"
    with permanent_lock(pool/'CONTROLLER.lock',timeout_seconds=1):
        return _start(args,config)


def _start(args,config):
    target,queue,pending=objects(config)
    def stop_controller(_signum,_frame):raise SystemExit(143)
    signal.signal(signal.SIGTERM,stop_controller)
    Path(config['run_root']).mkdir(parents=True,exist_ok=True);initialize(target,args.workers)
    print(json.dumps({'ready_questions':len(queue.catalog.episodes),'pending_asset_questions':pending,'teacher_target':20000,'mode':'drain_bound_ready_scenes'}),flush=True)
    if not queue.catalog.episodes:raise RuntimeError('no question has a complete training geometry receipt')
    def command(worker_id,slot,_):return [PYTHON,'-B',str(HERE/'collect.py'),'worker','--config',str(args.config),'--worker-id',worker_id,'--slot',str(slot)]
    controller=PoolController(queue,target,run_epoch='run_'+uuid.uuid4().hex,command_factory=command,log_root=Path(config['run_root'])/'logs')
    last=0
    # Admission has already checked ownership. Keep a conservative local deadline
    # if NFS prevents subsequent confirmations; never extend it on a failed call.
    lease=coord_guard(config)
    age=(datetime.now(timezone.utc)-datetime.fromisoformat(lease['last_heartbeat'])).total_seconds()
    confirmed=time.monotonic()-age
    try:
        while True:
            if time.monotonic()-last>30:
                if heartbeat(config) is not False:confirmed=time.monotonic()
                last=time.monotonic()
                if last-confirmed>=1500:
                    replace_json(target.state_root/'BLOCKED.json',
                                 {'reason':'coordination_heartbeat_unconfirmed','seconds':last-confirmed})
                    return 2
            status=controller.tick()
            if status['blocked']:raise RuntimeError(json.dumps(status['blocked'],sort_keys=True))
            if not controller.active and status['census']['valid_complete']==status['census']['total']:return 0
            time.sleep(3)
    finally:
        controller.stop()


def watchdog(args):
    """Watch one owned controller and alarm on stalled finalized output; never relaunch blindly."""
    from nondeleting_lifecycle import permanent_lock
    config=load_config(args.config,service=True);target,queue,_=objects(config)
    root=Path(config['run_root']);pool=target.state_root
    def stop_watchdog(_signum,_frame):raise SystemExit(143)
    signal.signal(signal.SIGTERM,stop_watchdog)
    with permanent_lock(pool/'WATCHDOG.lock'):
        if (pool/'BLOCKED.json').exists():raise RuntimeError('pool has a durable BLOCKED receipt; operator review required')
        if queue.heartbeats.live_workers(target.config.heartbeat_timeout_seconds):raise RuntimeError('worker heartbeats remain live; drain the existing epoch first')
        initialize(target,args.workers);resize_workers(target,workers=args.workers)
        seen=set();finalized=0;null_predictions=0;last_progress=time.monotonic()
        proc=subprocess.Popen([PYTHON,'-B',str(HERE/'collect.py'),'start','--config',str(args.config),'--workers',str(args.workers)])
        try:
            while True:
                for path in (root/'terminals').glob('*.json'):
                    if path.name in seen:continue
                    terminal_row=read_json(path);qid=terminal_row['question_id']
                    trace_path=Path(terminal_row['output'])/'finalized'/qid/f'trace_{qid}.json'
                    if trace_path.is_file():
                        trace=read_json(trace_path);finalized+=1;last_progress=time.monotonic()
                        null_predictions+=trace.get('pred') is None
                        seen.add(path.name)
                status={'schema':'r1314-watchdog-status-v1','wall_time_ns':time.time_ns(),
                    'controller_pid':proc.pid,'finalized':finalized,'null_predictions':null_predictions,
                    'seconds_without_finalized_progress':time.monotonic()-last_progress}
                replace_json(pool/'WATCHDOG_STATUS.json',status)
                if null_predictions or status['seconds_without_finalized_progress']>=1800:
                    replace_json(pool/'WATCHDOG_ALARM.json',dict(status,reason='null_prediction_or_no_finalized_progress'))
                code=proc.poll()
                if code is not None:
                    replace_json(pool/'WATCHDOG_EXIT.json',dict(status,return_code=code))
                    return code
                time.sleep(30)
        finally:
            if proc.poll() is None:proc.terminate()
            proc.wait(timeout=90)


def bind(args):
    config={'schema':'r1313-collection-config-v1','mode':'production','run_root':str(require_data_path(args.run_root)),
        'collector_version':'r1315-tolerant-sparse-v1',
        'work_id':args.work_id,'agent_id':args.agent_id,'coord_root':str(COORD_ROOT),
        'assets_registry':str(require_data_path(args.assets_registry)),'assets_registry_sha256':sha(args.assets_registry),
        'source_contract':str(require_data_path(args.contract)),'source_contract_sha256':args.contract_sha256,
        'budget':args.budget,'episode_limit':args.episode_limit}
    if args.budget==32768:
        if not args.topups:raise ValueError('32k requires an offline TOPUPS.json selection')
        config.update(topups=str(require_data_path(args.topups)),topups_sha256=sha(args.topups))
    validate_config(config)
    _,queue,pending=objects(config)
    if not queue.catalog.episodes:raise ValueError('no ready training questions')
    identity={k:config[k] for k in ('work_id','agent_id','source_contract_sha256')}
    # The verified successor contract binds the original immutable run identity.
    identity['source_contract_sha256']=verify_source(config)['parent_source_contract']['sha256']
    identity.update(schema='r1313-run-identity-v1',membership_sha256=__import__('training_assets').MEMBERSHIP_SHA)
    root=Path(config['run_root'])
    try:publish_json_exclusive(root/'RUN_IDENTITY.json',identity)
    except AlreadyExists:
        if read_json(root/'RUN_IDENTITY.json')!=identity:raise ValueError('existing run root belongs to another source/owner; preserve it')
    output=require_data_path(args.output)
    publish_json_exclusive(output,config)
    print(json.dumps({'config':str(output),'config_sha256':sha(output),'ready_questions':len(queue.catalog.episodes),'pending_asset_questions':pending}));return 0



def resize_workers(target,*,workers=None,delta=None):
    with target.cap_lock():
        current=target.read()
        count=workers if workers is not None else current.total_workers+delta
        updated=Target(count,max(1,count));updated.validate(target.config.total_workers_max)
        replace_json(target.path,updated.as_json())
    print(json.dumps({'previous_workers':current.total_workers,'workers':count}));return count

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    for name in ('start','watchdog','worker','set-workers','readiness'):
        parser=sub.add_parser(name);parser.add_argument('--config',type=Path,required=True)
        if name in ('start','watchdog'):parser.add_argument('--workers',type=int,required=True)
        if name=='set-workers':
            capacity=parser.add_mutually_exclusive_group(required=True);capacity.add_argument('--workers',type=int);capacity.add_argument('--delta',type=int)
        if name=='worker':parser.add_argument('--worker-id',required=True);parser.add_argument('--slot',type=int,required=True)
    b=sub.add_parser('bind');b.add_argument('--run-root',type=Path,required=True);b.add_argument('--assets-registry',type=Path,required=True);b.add_argument('--contract',type=Path,required=True);b.add_argument('--contract-sha256',required=True);b.add_argument('--work-id',required=True);b.add_argument('--agent-id',required=True);b.add_argument('--budget',type=int,choices=(16384,32768),default=16384);b.add_argument('--episode-limit',type=int,default=0);b.add_argument('--topups',type=Path);b.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='bind':return bind(a)
    if a.command=='start':return start(a)
    if a.command=='watchdog':return watchdog(a)
    if a.command=='worker':return worker(a)
    config=load_config(a.config);target,queue,pending=objects(config)
    if a.command=='set-workers':resize_workers(target,workers=a.workers,delta=a.delta);return 0
    print(json.dumps({'ready':len(queue.catalog.episodes),'pending_assets':pending,'census':queue.census()},indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
