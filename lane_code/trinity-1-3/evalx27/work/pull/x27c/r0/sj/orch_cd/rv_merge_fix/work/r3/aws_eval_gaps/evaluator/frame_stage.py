"""CPU-only official decoding into pinned lossless PNGs before engine startup."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time
from PIL import Image
from data import tasks_for
from evalpath.items import digest,sha256
from media import decode,identity,item_key,pixel_digest
from cells import frame_count


def write_json(path,value):
    path.write_text(json.dumps(value,sort_keys=True,allow_nan=False)+'\n')


def stage_one(task,layout,cache,frames=32,frame_set=None):
    key=digest(identity(task,layout,frames,frame_set))
    directory=Path(cache)/key
    directory.mkdir()  # A job-local stage has one writer per video/layout, no retries.
    receipt=dict(identity=identity(task,layout,frames,frame_set))
    try:
        selection={'frames':frames} if frames!=32 else {}
        if frame_set is not None:selection['frame_set']=frame_set
        arrays,audit=decode(task,layout,**selection)
        # Store each source frame once, retaining repeats in the ordered receipt.
        pins={};frames=[]
        for index,array in zip(audit['metadata']['frames_indices'],arrays):
            if index not in pins:
                path=directory/(str(index)+'.png')
                Image.fromarray(array).save(path,format='PNG',compress_level=1)
                pins[index]=dict(path=str(path.relative_to(cache)),sha256=sha256(path),index=index)
                if task['benchmark']=='pointing':pins[index]['pixel_sha256']=pixel_digest(array[None])
            frames.append(pins[index])
        receipt.update(audit=audit,frames=frames)
    except Exception as exc:
        # Keep per-item failure/scoring behavior; workers journal the same staged error.
        receipt['error']=type(exc).__name__+': '+str(exc)[:2000]
    path=directory/'0.json'
    write_json(path,receipt)
    return dict(path=str(path.relative_to(cache)),sha256=sha256(path)), 'error' in receipt


def stage(config,cache,workers):
    started=time.monotonic()
    cfg=json.loads(Path(config).read_text())
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    datasets={s['benchmark']:tasks_for(s,cfg['roots']) for s in cfg['datasets']}
    jobs={};items={}
    for cell in cfg['cells']:
        frames=frame_count(cell);frame_set=cell.get('frame_set')
        tasks=sorted((t for b in cell['benchmarks'] for t in datasets[b]),
                     key=lambda t:(t['benchmark'],t['example_id']))
        if cfg.get('smoke_items'):tasks=tasks[:cfg['smoke_items']]
        if cfg.get('routing',{}).get('direct_answers'):
            from routing import reuse_direct
            from evalpath.items import pinned
            table=json.loads(pinned(cfg['routing']['table']).read_text());reused={}
            for benchmark,pin in cfg['routing']['direct_answers'].items():
                reused.update(reuse_direct([t for t in tasks if t['benchmark']==benchmark],pin,table,cfg['routing'].get('direct_requests',{}).get(benchmark)))
            tasks=[t for t in tasks if t['benchmark']+':'+t['example_id'] not in reused]
        for task in tasks:
            layout=cell['layout'];key=digest(identity(task,layout,frames,frame_set))
            jobs[key]=(task,layout,cache,frames,frame_set)
            item=item_key(task,layout,frames,frame_set)
            if item in items and items[item]!=key:raise ValueError('Conflicting frame item')
            items[item]=key
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pins=dict(zip(jobs,executor.map(lambda args:stage_one(*args),jobs.values())))
    index=dict(schema=1,binding=cfg['binding'],source_sha256=cfg['source_sha256'],
               items={item:pins[key][0] for item,key in items.items()},
               decodes=len(jobs),errors=sum(v[1] for v in pins.values()),
               seconds=time.monotonic()-started,workers=workers)
    write_json(cache/'0.json',index)
    print(json.dumps({k:v for k,v in index.items() if k!='items'}),flush=True)
    return index


if __name__=='__main__':
    import av
    import sys
    if sys.version_info[:2]!=(3,12):raise ValueError('Require trainer Python 3.12')
    p=argparse.ArgumentParser()
    p.add_argument('config');p.add_argument('cache')
    p.add_argument('--workers',type=int,default=int(os.environ.get('SLURM_CPUS_PER_TASK','1')))
    a=p.parse_args()
    if a.workers<1:raise ValueError('Require positive CPU count')
    stage(a.config,a.cache,a.workers)
