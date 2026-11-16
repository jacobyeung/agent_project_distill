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
from token_audit import check_score,prefix_score,load_tokenizer


IDENTITY=('benchmark','example_id','question_type')
PINNED=('ground_truth','options','question','scene','num_frames','revsi_tier','revsi_set','source_frame_indices','video_path','video_sha256')


def check_row(r,task,frames,cell,*,historical=False,budget_context=None):
    """Validate layout, task, protocol and diagnostics before admitting a row."""
    check_layout(r,cell['layout'])
    if any(r.get(f)!=task.get(f) for f in IDENTITY) or r.get('frames')!=frames:
        raise ValueError('Journal row identity differs from its pinned task: '+r['key'])
    for name in ('thinking','model','decoding'):
        if name not in r and historical:continue
        if r.get(name)!=cell.get(name):
            raise ValueError('Journal '+name+' differs from its cell: '+r['key'])
    if r.get('status')!='complete':return
    if any(r.get(f)!=task.get(f) for f in PINNED if f in task or f in r):
        raise ValueError('Journal row differs from its pinned task: '+r['key'])
    check_pinned_frames(r,task,cell['layout'])
    if budget_context is not None:
        text,cap,finish=budget_context.scoring(r,task,cell)
    else:
        if r.get('budget') is not None:
            raise ValueError('Budget row requires authenticated budget-arm context')
        if r['max_new_tokens']!=cell['max_tokens']:
            raise ValueError('Journal cap differs from its cell: '+r['key'])
        text,cap,finish=r['raw_generation'],cell['max_tokens'],r['finish_reason']
    again=score_item(dict(task,thinking=cell['thinking']),text,r['output_tokens'],cap=cap,finish=finish)
    if budget_context is not None and r.get('derivation_error'):
        # Authenticated failed derivations are explicitly unanswered, in denominator.
        again=budget_context.error_score(r,again)
    check_score(r,again)
    return again


def merge(cfg,cell_index,attempt,*,tokenizer=None,budget_context=None):
    cell=cfg['cells'][cell_index]
    if cfg.get('budget_arm') and budget_context is None:
        raise ValueError('Budget merge requires authenticated budget-arm context')
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
    short_rows={}
    annotations=[]
    for rank in range(cfg['gpus']):
        p=directory/('g'+str(rank)+'.jsonl')
        if not p.exists():continue
        historical=False
        if p.with_suffix('.annotation.json').exists():
            annotation=verify_annotation(p,cfg,cell_index)
            annotations.append(annotation.metadata)
            cell=annotation.cell(cell_index)
            historical=True
        for r,_ in records(p):
            retain(original_rows,r)
            r=dict(r)
            if r['binding']!=binding:raise ValueError('Resume binding differs')
            r.setdefault('anchor_indices',r.get('media',{}).get('anchor_indices'))
            if r['key'] not in by_key:raise ValueError('Unexpected journal membership')
            check_row(r,by_key[r['key']],frames,cell,historical=historical,budget_context=budget_context)
            retain(rows,r)
            if r.get('status')=='complete':
                if tokenizer is None:tokenizer=load_tokenizer(cfg)
                if budget_context is not None:
                    short=budget_context.prefix(r,by_key[r['key']],cell)
                else:
                    short=prefix_score(r,by_key[r['key']],cell,tokenizer)
                short_rows[r['key']]=dict(r,**short)
    expected={t['benchmark']+':'+t['example_id'] for t in tasks}
    if set(rows)-expected:raise ValueError('Unexpected journal membership')
    checks=[]
    for rank in range(cfg['gpus']):
        p=directory/('p'+str(rank)+'_'+attempt+'.json')
        if p.exists():checks.extend(json.loads(p.read_text())['checks'])
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
        summary.update(frames=frames,anchor_indices={r['example_id']:r['anchor_indices'] for r in rs})
        if 'frame_set' in cell:
            summary.update(frame_set=cell['frame_set'],anchor_slots={r['example_id']:r['anchor_slots'] for r in rs})
        short=[short_rows[r['key']] if r.get('status')=='complete' else r for r in rs]
        summary['at_4096']=benchmark_summary(short,ts,verified)
        summary['missing']=len(ts)-len(rs)
        done=[r for r in rs if r.get('status')=='complete']
        summary['processed_height_width']=dict(Counter('x'.join(map(str,r['processed_height_width'])) for r in done if r.get('processed_height_width')))
        summary['visual_tokens_per_frame']=dict(Counter(str(r['visual_tokens_per_frame']) for r in done if r.get('visual_tokens_per_frame') is not None))
        if name=='revsi':summary['sidecar_verified']=all(t.get('sidecar_verified') for t in ts)
        result['benchmarks'][name]=summary
    if annotations:result['annotations']=annotations
    if cfg.get('budget_arm'):result['budget_arm']=cfg['budget_arm']
    (directory/('summary_'+attempt+'.json')).write_text(json.dumps(result,indent=1,allow_nan=False)+'\n')
    with (directory/('items_'+attempt+'.jsonl')).open('w') as f:
        for key in sorted(rows):f.write(json.dumps(rows[key],allow_nan=False)+'\n')
    return result
