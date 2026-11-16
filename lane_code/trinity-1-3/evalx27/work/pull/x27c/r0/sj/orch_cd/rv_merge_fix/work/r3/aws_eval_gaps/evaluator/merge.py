"""Merge all ranks, retain failures, and gate all benchmark numbers."""
import json
from collections import Counter
from pathlib import Path
from data import tasks_for
from evalpath.items import digest
from scoring import benchmark_summary,score_item
from parity import probe_tasks
from cells import frame_count,check_layout,check_pinned_frames
from journal import records,retain
from provenance import verify_annotation


IDENTITY=('benchmark','example_id','question_type')
PINNED=('ground_truth','options','question','scene','num_frames','revsi_tier','revsi_set','source_frame_indices','video_path','video_sha256')


def check_row(r,task,frames,layout):
    """Admit a journal row only if it answers its pinned task at the cell's frame count with the pinned ground truth."""
    check_layout(r,layout)
    if any(r.get(f)!=task.get(f) for f in IDENTITY) or r.get('frames')!=frames:
        raise ValueError('Journal row identity differs from its pinned task: '+r['key'])
    if r.get('status')!='complete':return
    if any(r.get(f)!=task.get(f) for f in PINNED if f in task or f in r):
        raise ValueError('Journal row differs from its pinned task: '+r['key'])
    check_pinned_frames(r,task,layout)
    again=score_item(task,r['raw_generation'],r['output_tokens'],cap=r['max_new_tokens'],finish=r['finish_reason'])
    if again['score']!=r['score'] or again['response_text']!=r['response_text']:
        raise ValueError('Journal score differs from the pinned rescore: '+r['key'])


def merge(cfg,cell_index,attempt):
    cell=cfg['cells'][cell_index]
    frames=frame_count(cell)
    directory=Path(cfg['output'])/str(cell_index)
    directory.mkdir(parents=True,exist_ok=True)
    tasks=[t for s in cfg['datasets'] if s['benchmark'] in cell['benchmarks'] for t in tasks_for(s,cfg['roots'])]
    tasks=sorted(tasks,key=lambda t:(t['benchmark'],t['example_id']))
    if cfg.get('smoke_items'):tasks=tasks[:cfg['smoke_items']]
    binding=digest({'request':cfg['binding'],'cell':cell_index})
    by_key={t['benchmark']+':'+t['example_id']:t for t in tasks}
    rows={}
    original_rows={}
    annotations=[]
    for rank in range(cfg['gpus']):
        p=directory/('g'+str(rank)+'.jsonl')
        if not p.exists():continue
        if p.with_suffix('.annotation.json').exists():
            annotations.append(verify_annotation(p,cfg,cell_index).metadata)
        for r,_ in records(p):
            retain(original_rows,r)
            r=dict(r)
            if r['binding']!=binding:raise ValueError('Resume binding differs')
            r.setdefault('frames',frames)
            r.setdefault('anchor_indices',r.get('media',{}).get('anchor_indices'))
            if 'frame_set' in cell:
                r.setdefault('frame_set',cell['frame_set'])
                r.setdefault('anchor_slots',r.get('media',{}).get('anchor_slots'))
            if r['key'] not in by_key:raise ValueError('Unexpected journal membership')
            check_row(r,by_key[r['key']],frames,cell['layout'])
            retain(rows,r)
    expected={t['benchmark']+':'+t['example_id'] for t in tasks}
    if set(rows)-expected:raise ValueError('Unexpected journal membership')
    checks=[]
    for rank in range(cfg['gpus']):
        p=directory/('p'+str(rank)+'_'+attempt+'.json')
        if p.exists():
            parity_record=json.loads(p.read_text())
            if parity_record.get('layout') != cell['layout']:raise ValueError('Parity shard layout differs')
            checks.extend(parity_record['checks'])
    identities={(c.get('benchmark'),c['example_id']) for c in checks}
    probes=probe_tasks(cfg,tasks)
    wanted={(t['benchmark'],t['example_id']) for t,_ in probes}
    pixels=[c['pixels'] for c in checks if 'pixels' in c]
    parity=(len(checks)==len(probes) and identities==wanted and all(c.get('prompt_equal') for c in checks)
            and len(pixels)==sum(i<2 for _,i in probes) and all(p.get('pass') for p in pixels))
    result=dict(model=cell['model'],layout=cell['layout'],decoding=cell.get('decoding','greedy'),binding=binding,attempt=attempt,
                frames=frames,anchor_indices={k:r['anchor_indices'] for k,r in sorted(rows.items())},
                parity_pass=parity,parity_checks=checks,smoke_items=cfg.get('smoke_items',0),benchmarks={})
    if 'frame_set' in cell:
        result.update(frame_set=cell['frame_set'],anchor_slots={k:r['anchor_slots'] for k,r in sorted(rows.items())})
    for name in cell['benchmarks']:
        ts=[t for t in tasks if t['benchmark']==name]
        rs=[r for r in rows.values() if r['benchmark']==name]
        verified=parity and not cfg.get('smoke_items') and (name!='revsi' or all(t.get('sidecar_verified') for t in ts))
        summary=benchmark_summary(rs,ts,verified)
        summary.update(layout=cell['layout'],frames=frames,anchor_indices={r['example_id']:r['anchor_indices'] for r in rs})
        if 'frame_set' in cell:
            summary.update(frame_set=cell['frame_set'],anchor_slots={r['example_id']:r['anchor_slots'] for r in rs})
        short=[{**r,**r['at_4096']} if r.get('status')=='complete' else r for r in rs]
        summary['at_4096']=benchmark_summary(short,ts,verified)
        summary['missing']=len(ts)-len(rs)
        done=[r for r in rs if r.get('status')=='complete']
        summary['processed_height_width']=dict(Counter('x'.join(map(str,r['processed_height_width'])) for r in done if r.get('processed_height_width')))
        summary['visual_tokens_per_frame']=dict(Counter(str(r['visual_tokens_per_frame']) for r in done if r.get('visual_tokens_per_frame') is not None))
        if name=='revsi':summary['sidecar_verified']=all(t.get('sidecar_verified') for t in ts)
        result['benchmarks'][name]=summary
    if annotations:result['annotations']=annotations
    (directory/('summary_'+attempt+'.json')).write_text(json.dumps(result,indent=1,allow_nan=False)+'\n')
    with (directory/('items_'+attempt+'.jsonl')).open('w') as f:
        for key in sorted(rows):f.write(json.dumps(rows[key],allow_nan=False)+'\n')
    return result
