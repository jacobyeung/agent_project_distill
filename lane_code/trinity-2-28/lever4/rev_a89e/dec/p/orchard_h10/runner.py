
<<HEX 0>>
"""Opaque JSON transport; canonical hashes retain their logical representation."""
import json

if not hasattr(json, '_a0_loads'):
    json._a0_loads = json.loads
    json._a0_dumps = json.dumps

wire_loads = json._a0_loads
wire_dumps = json._a0_dumps
TAG = 'a0'


def raw(data):
    value = wire_loads(data)
    if isinstance(value, dict) and set(value) == {TAG} and isinstance(value[TAG], str):
        return bytes.fromhex(value[TAG])
    return data.encode() if isinstance(data, str) else data


def pack(data):
    if isinstance(data, str):data=data.encode()
    return (wire_dumps({TAG:data.hex()},separators=(',', ':'))+'\n').encode()


def loads(data, *args, **kwargs):
    value=wire_loads(data,*args,**kwargs)
    if isinstance(value,dict) and set(value)=={TAG} and isinstance(value[TAG],str):
        return wire_loads(bytes.fromhex(value[TAG]),*args,**kwargs)
    return value


def load(stream, *args, **kwargs):return loads(stream.read(), *args, **kwargs)


def dumps(value, *args, **kwargs):
    data = wire_dumps(value, *args, **kwargs)
    return pack(data).decode().rstrip('\n') if kwargs.get('indent') is not None else data


def dump(value, stream, *args, **kwargs):
    stream.write(pack(wire_dumps(value, *args, **kwargs)).decode())


def install():
    json.loads=loads;json.load=load;json.dumps=dumps;json.dump=dump

<</HEX>>
"""One process per GPU, with a barrier between question types."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from orchard_h10.common import ORDER, canonical, write, opaque


def append(path, value):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(value,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())


def control(config):
    root=Path(config['output'])/'metadata'/'a'
    root.mkdir(parents=True,exist_ok=True,mode=0o700);root.chmod(0o700)
    if not (root/'5.py').exists():
        code=(Path(__file__).parent/'entry.py').read_bytes()
        (root/'5.py').write_bytes(b"exec(bytes.fromhex('"+code.hex().encode()+b"'))\n")
    return root


def commands(config, kind, index, cards, stop_at, finish_by):
    root=control(config)
    t=ORDER.index(kind) if kind in ORDER else len(ORDER)
    cfg=dict(action=2,package=config['package'],config=config,type=t,index=index,
             cards=len(cards),stop_at=stop_at,finish_by=finish_by)
    name=f'{t}{index}.json';write(root/name,cfg)
    argv=[config['python'],'-B','-I','5.py',name]
    opaque(argv)
    return argv


def worker_args(cfg):
    config=cfg['config'];p=Path(config['package']);t=cfg['type'];i=cfg['index']
    root=Path(config['output'])/'metadata'/'a'
    source=Path(config.get('items',p/'items/devs1_routed.json')) if t<len(ORDER) else Path(config['optional']['items'])
    dest=root/f'{t}.json'
    with open(source,'rb') as stream:raw=stream.read()
    import fcntl
    with (root/f'{t}.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if dest.exists():
            with open(dest,'rb') as stream:stored=stream.read()
            if stored!=raw:raise ValueError('Item input changed')
        else:dest.write_bytes(raw)
    args=['--export-pin',config['export_pin'],'--items',str(dest),'--export',config['export'],'--artifact-manifest',config['binding'],
          '--reader-root',str(p/'b'),'--settings',config['settings'],
          '--out',str(Path(config['output'])/'metadata/journals'/str(t)/str(i)),
          '--arms',','.join(config.get('arms',['own'])),'--shard',f"{i}/{cfg['cards']}",'--device',config.get('device','cuda:0'),
          '--stop-at',str(cfg['stop_at']),'--finish-by',str(cfg['finish_by']),
          '--stop-file',str(config.get('stop_file',Path(config['output'])/'metadata/STOP'))]
    if config.get('export_cache'):
        args+=['--export-cache',config['export_cache'],'--allocation',config['allocation']]
    if config.get('modes'):args+=['--modes',','.join(config['modes'])]
    if t<len(ORDER):args+=['--types',ORDER[t]]
    else:args+=['--modes','none']
    if config.get('single_worker'):
        args[args.index('--types')+1]=','.join(config['types'])
        args[args.index('--out')+1]=str(Path(config['output'])/'metadata/journals')
        args+=['--type-journals']
    return args


def optional_ready(config):
    spec=config.get('optional')
    if not spec:return False
    from orchard_h10.common import sha
    receipt=Path(spec['receipt'])
    if not receipt.exists():return False
    value=json.loads(receipt.read_text())
    if sha(receipt)!=spec['sha256'] or value.get('verified') is not True:
        raise ValueError('Optional archive verification differs')
    return True


def environment(config, card, index):
    p=Path(config['package']); out=Path(config.get('cache_root',Path(config['output'])/'cache'))/str(index)
    out.mkdir(parents=True,exist_ok=True)
    env={k:os.environ[k] for k in ('PATH','LD_LIBRARY_PATH','B8_DELAY') if k in os.environ}
    env.update(CUDA_VISIBLE_DEVICES=card,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out),
               HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',
               OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',NUMEXPR_NUM_THREADS='4')
    for j,name in enumerate(('XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR','TORCHINDUCTOR_CACHE_DIR','TORCH_HOME')):
        env[name]=str(out/str(j));Path(env[name]).mkdir(exist_ok=True)
    # CPU fixtures use a local path whose ancestor is the lane name. Production
    # uses only the stable token namespace, and scans the entire environment.
    if config.get('device')!='cpu':opaque([f'{k}={v}' for k,v in env.items()])
    return env


def summarize(config, cards):
    from h1eval.h10.launch import read_records, selected, select_types
    from h1eval.items import load_manifest
    from h1eval.modes import DEFAULT_MODES, plan
    from h1eval.cli import modes
    items=load_manifest(config.get('items',Path(config['package'])/'items/devs1_routed.json'))['items']
    root=Path(config['output'])/'metadata/journals';counts=[]
    for kind in config.get('types') or list(ORDER):
        t=ORDER.index(kind)
        for i in range(len(cards)):
            chosen=select_types(items,selected(items,f'{i}/{len(cards)}'),kind)
            expected=plan(chosen,config.get('arms',['own']),[{'name':'none'},*modes(','.join(config['modes']) if config.get('modes') else DEFAULT_MODES)])
            rows=read_records(root/str(t)/str(i)/'items.jsonl')
            actual={(r['id'],r['arm'],r['mode']) for r in rows}
            if not actual<=expected:raise ValueError('Journal contains unplanned reads')
            counts.append(dict(type=t,shard=f'{i}/{len(cards)}',completed=len(actual),expected=len(expected)))
    if optional_ready(config):
        extra=load_manifest(config['optional']['items'])['items']
        for i in range(len(cards)):
            expected=plan(selected(extra,f'{i}/{len(cards)}'),['own'],[{'name':'none'}])
            rows=read_records(root/str(len(ORDER))/str(i)/'items.jsonl')
            actual={(r['id'],r['arm'],r['mode']) for r in rows}
            if not actual<=expected:raise ValueError('Unplanned optional read')
            counts.append(dict(type=len(ORDER),shard=f'{i}/{len(cards)}',completed=len(actual),expected=len(expected)))
    total=sum(r['completed'] for r in counts); expected=sum(r['expected'] for r in counts)
    return dict(completed=total,expected=expected,complete=total==expected,shards=counts)


def run(config, cards, end_time, *, prefix=(), clock=time.time, launcher=subprocess.Popen):
    if not 1 <= len(cards) <= 4 or len(set(cards))!=len(cards):raise ValueError('Require 1–4 distinct assigned cards')
    out=Path(config['output']);(out/'metadata').mkdir(parents=True,exist_ok=True);(out/'logs').mkdir(exist_ok=True)
    types=config.get('types') or list(ORDER)
    identity=dict(plan=config['plan_sha256'],inputs=config.get('inputs_sha256'),cards=len(cards),order=list(ORDER),types=types,arms=config.get('arms',['own']),
                  stage1_select_rule=config.get('stage1_select_rule','null_argmax'),modes=config.get('modes'))
    actual=json.loads(Path(config['settings']).read_text()) if config.get('settings') else config
    identity.update(perception_memo=actual.get('perception_memo','off'),
                    perception_memo_modules=actual['perception_memo_modules'],
                    perception_memo_verify_ids=actual.get('perception_memo_verify_ids',[]),
                    settings_sha256=canonical(actual))
    identity_path=out/'metadata/IDENTITY.json'
    if identity_path.exists() and json.loads(identity_path.read_text())!=identity:
        raise ValueError('Resume requires the same plan and GPU shard count')
    write(identity_path,identity)
    stop_at=end_time-config.get('stop_margin',1800);finish_by=end_time-config.get('return_margin',1200)
    marker=Path(config.get('stop_file',out/'metadata/STOP'))
    # A resume archive deliberately omits the allocation-local stop marker.
    def stop(number, frame):
        marker.write_text(str(number)+'\n')
    old={n:signal.signal(n,stop) for n in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT)}
    failure=None
    try:
        for kind in (types[:1] if config.get('single_worker') else (*types,*(['optional'] if optional_ready(config) else []))):
            t=ORDER.index(kind) if kind in ORDER else len(ORDER)
            if clock()>=stop_at or marker.exists():break
            processes=[]
            with ExitStack() as stack:
                try:
                    for i,card in enumerate(cards):
                        argv=[*prefix,*commands(config,kind,i,cards,stop_at,finish_by)]
                        opaque(argv)
                        log=stack.enter_context((out/'logs'/f'{t}{i}.log').open('ab'))
                        append(out/'STEPS.jsonl',dict(event='start',type=t,shard=f'{i}/{len(cards)}',utc=clock(),argv=argv))
                        processes.append((i,launcher(argv,env=environment(config,card,i),cwd=Path(config['output'])/'metadata/a',stdout=log,stderr=subprocess.STDOUT)))
                except Exception as error:
                    marker.write_text('launch failure\n');failure=str(error)
                # A process failure forbids another type; all siblings drain to their own guard.
                for i,process in processes:
                    rc=process.wait()
                    append(out/'STEPS.jsonl',dict(event='exit',type=t,shard=f'{i}/{len(cards)}',utc=clock(),returncode=rc))
                    if rc not in (0,75):
                        failure=f'Worker {t}/{i} exited {rc}'
                        marker.write_text('worker failure\n')
                    if rc==75:marker.write_text('deadline\n')
            if failure:break
        summary=summarize(config,cards)
        summary.update(stopped=not summary['complete'] and failure is None,failure=failure)
        summary['optional_admitted']=optional_ready(config)
        write(out/'SUMMARY.json',summary)
        # Aggregate measured timing even when no shard has reached ten reads yet.
        from h1eval.h10.launch import read_records
        samples=[]
        for kind in (*types,*(['optional'] if optional_ready(config) else [])):
            t=ORDER.index(kind) if kind in ORDER else len(ORDER)
            for path in sorted((out/'metadata/journals'/str(t)).glob('*/items.jsonl')):
                samples.extend(r['seconds'] for r in read_records(path))
        write(out/'metadata/projection.json',dict(sample_reads=len(samples),
            seconds_per_read=sum(samples)/len(samples) if samples else None,
            projected_gpu_hours=summary['expected']*sum(samples)/len(samples)/3600 if samples else None,
            excludes_model_loading=True))
        return summary
    finally:
        for n,handler in old.items():signal.signal(n,handler)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('end',type=float)
    a=p.parse_args();cfg=json.loads(Path(a.config).read_text())
    result=run(cfg,os.environ['CUDA_VISIBLE_DEVICES'].split(','),a.end,prefix=cfg['prefix'])
    raise SystemExit(1 if result['failure'] else 0)
