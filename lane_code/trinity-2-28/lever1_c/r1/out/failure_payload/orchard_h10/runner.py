
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
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
