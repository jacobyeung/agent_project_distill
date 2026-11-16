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

from orchard_h10.common import ORDER, canonical, write


def append(path, value):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(value,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())


def commands(config, kind, index, cards, stop_at, finish_by):
    p=Path(config['package']); out=Path(config['output'])/'metadata'/'journals'/str(ORDER.index(kind))/str(index)
    return [config['python'],'-B','-m','h1eval.h10.launch',
            '--items',config.get('items',str(p/'items/devs1_routed.json')),'--export',config['export'],
            '--artifact-manifest',config['binding'],'--reader-root',str(p/'b'),
            '--settings',config['settings'],'--out',str(out),'--arms','own',
            '--types',kind,'--shard',f'{index}/{len(cards)}',
            '--device',config.get('device','cuda:0'),
            '--stop-at',str(stop_at),'--finish-by',str(finish_by),
            '--stop-file',str(Path(config['output'])/'metadata/STOP')]


def environment(config, card, index):
    p=Path(config['package']); out=Path(config['output'])/'cache'/str(index)
    out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES=card,PYTHONPATH=f'{p}/b:{p}/tree:{p}',
             PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out),HF_HUB_OFFLINE='1',
             TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',
             OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',NUMEXPR_NUM_THREADS='4')
    for name in ('XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR','TORCHINDUCTOR_CACHE_DIR','TORCH_HOME'):
        env[name]=str(out/name.lower());Path(env[name]).mkdir(exist_ok=True)
    env.pop('H10_OVERLAY',None);env.pop('H10_TOWER_FROM',None);env.pop('H10_SETTINGS',None)
    return env


def summarize(config, cards):
    from h1eval.h10.launch import read_records, selected, select_types
    from h1eval.items import load_manifest
    from h1eval.modes import DEFAULT_MODES, plan
    from h1eval.cli import modes
    items=load_manifest(config.get('items',Path(config['package'])/'items/devs1_routed.json'))['items']
    root=Path(config['output'])/'metadata/journals';counts=[]
    for t,kind in enumerate(ORDER):
        for i in range(len(cards)):
            chosen=select_types(items,selected(items,f'{i}/{len(cards)}'),kind)
            expected=plan(chosen,['own'],[{'name':'none'},*modes(DEFAULT_MODES)])
            rows=read_records(root/str(t)/str(i)/'items.jsonl')
            actual={(r['id'],r['arm'],r['mode']) for r in rows}
            if not actual<=expected:raise ValueError('Journal contains unplanned reads')
            counts.append(dict(type=kind,shard=f'{i}/{len(cards)}',completed=len(actual),expected=len(expected)))
    total=sum(r['completed'] for r in counts); expected=sum(r['expected'] for r in counts)
    return dict(completed=total,expected=expected,complete=total==expected,shards=counts)


def run(config, cards, end_time, *, prefix=(), clock=time.time, launcher=subprocess.Popen):
    if not 1 <= len(cards) <= 4 or len(set(cards))!=len(cards):raise ValueError('Require 1–4 distinct assigned cards')
    out=Path(config['output']);(out/'metadata').mkdir(parents=True,exist_ok=True);(out/'logs').mkdir(exist_ok=True)
    identity=dict(plan=config['plan_sha256'],inputs=config.get('inputs_sha256'),cards=len(cards),order=list(ORDER),arms=['own'])
    identity_path=out/'metadata/IDENTITY.json'
    if identity_path.exists() and json.loads(identity_path.read_text())!=identity:
        raise ValueError('Resume requires the same plan and GPU shard count')
    write(identity_path,identity)
    stop_at=end_time-config.get('stop_margin',1800);finish_by=end_time-config.get('return_margin',1200)
    marker=out/'metadata/STOP'
    # A resume archive deliberately omits the allocation-local stop marker.
    def stop(number, frame):
        marker.write_text(str(number)+'\n')
    old={n:signal.signal(n,stop) for n in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT)}
    failure=None
    try:
        for t,kind in enumerate(ORDER):
            if clock()>=stop_at or marker.exists():break
            processes=[]
            with ExitStack() as stack:
                try:
                    for i,card in enumerate(cards):
                        argv=[*prefix,*commands(config,kind,i,cards,stop_at,finish_by)]
                        log=stack.enter_context((out/'logs'/f'{t}{i}.log').open('ab'))
                        append(out/'STEPS.jsonl',dict(event='start',type=kind,shard=f'{i}/{len(cards)}',utc=clock(),argv=argv))
                        processes.append((i,launcher(argv,env=environment(config,card,i),cwd=config['package'],stdout=log,stderr=subprocess.STDOUT)))
                except Exception as error:
                    marker.write_text('launch failure\n');failure=str(error)
                # A process failure forbids another type; all siblings drain to their own guard.
                for i,process in processes:
                    rc=process.wait()
                    append(out/'STEPS.jsonl',dict(event='exit',type=kind,shard=f'{i}/{len(cards)}',utc=clock(),returncode=rc))
                    if rc not in (0,75):
                        failure=f'Worker {t}/{i} exited {rc}'
                        marker.write_text('worker failure\n')
                    if rc==75:marker.write_text('deadline\n')
            if failure:break
        summary=summarize(config,cards)
        summary.update(stopped=not summary['complete'] and failure is None,failure=failure)
        write(out/'SUMMARY.json',summary)
        # Aggregate measured timing even when no shard has reached ten reads yet.
        from h1eval.h10.launch import read_records
        samples=[]
        for path in sorted((out/'metadata/journals').glob('*/*/items.jsonl')):
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
