"""Bind the admitted reader protocol to the official six-task cohort."""
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'proof'))
sys.path.insert(0,str(HERE/'out'))
sys.path.insert(0,str(HERE/'evaluator'))
from common import sha,load,dump,BASE_SHA
from export_check import check_export
EXPORT_SHA='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
ROWS_SHA='d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc'
COUNTS={'object_counting':565,'object_size_estimation':953,'object_rel_direction_easy':217,
        'object_rel_direction_medium':378,'object_rel_direction_hard':373,'object_rel_distance':710,
        'obj_appearance_order':618,'route_planning':194}
CELL=dict(model='cp1m200',layout='duplicate',benchmarks=['official5130'],frames=32,
          decoding='greedy',thinking=True,max_tokens=16384,name='a0')


def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def binding(cfg):
    return hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ('binding','output')},sort_keys=True).encode()).hexdigest()


def model_specs(models):
    b,s=models['base'],models['cp1m200']
    if b['kind']!='snapshot' or b['manifest']['sha256']!=BASE_SHA:
        raise ValueError('Base snapshot differs')
    if s['kind']!='c1_export' or s['sha256']!=EXPORT_SHA:
        raise ValueError('Step-544 artifact differs')
    from common import local
    for p in (b['path'],b['manifest']['path'],s['path']):
        if not Path(p).is_absolute():raise ValueError('Require absolute model paths')
        local(p)


def code_pins():
    return {str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.rglob('*'))
            if p.is_file() and (p.suffix in ('.py','.json')) and 'work' not in p.relative_to(HERE).parts}


def tasks(cfg):
    from data import tasks_for
    return sorted(tasks_for(cfg['datasets'][0],cfg['roots']),key=lambda t:(t['benchmark'],t['example_id']))


def membership(cfg):
    from collections import Counter
    rows=tasks(cfg)
    if cfg.get('mode') == 'proof':
        from selection import select
        expected = sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/COHORT_OFFICIAL6.jsonl')))
        if [t['example_id'] for t in rows] != expected:raise ValueError('Proof membership differs')
        return rows
    if dict(Counter(t['question_type'] for t in rows))!=COUNTS:
        raise ValueError('Six-task membership differs')
    return rows


def bind(dest,models,rows,video_root,mode='production'):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    model_specs(models)
    if sha(rows)!=ROWS_SHA:raise ValueError('Official questions differ')
    verification=check_export(models['cp1m200']['path'],EXPORT_SHA,models['base']['path'],544)
    pins=code_pins()
    cfg=dict(models=models,cells=[dict(CELL)],datasets=[dict(benchmark='official5130',
        rows=dict(path=str(Path(rows).resolve()),sha256=ROWS_SHA),question_types=sorted(COUNTS))],
        roots=dict(video_root=str(Path(video_root).resolve())),gpus=1,build_only=False,
        max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,
        smoke_items=0,engine_version='0.32.0',source_sha256=hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),
        reader=dict(step=544,decision_arm='B2048',code_pins=pins,export_verification=verification))
    cfg['mode']=mode
    if mode == 'proof':
        from selection import select
        cfg['datasets'][0]['example_ids']=sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/COHORT_OFFICIAL6.jsonl')))
    cfg['binding']=binding(cfg);cfg['output']=str(dest/'results')
    ts=membership(cfg)
    from evalpath.official import build_prompt_context
    dump(dest/'PROMPT_PINS.json',{t['example_id']:hashlib.sha256(build_prompt_context(t,'ours').encode()).hexdigest() for t in ts})
    dump(dest/'CODE_PINS.json',pins);dump(dest/'request.json',cfg)
    return cfg


def verify_bound(dest):
    dest=Path(dest);cfg=load(dest/'request.json')
    if cfg['binding']!=binding(cfg) or cfg['build_only'] or cfg['cells']!=[CELL]:raise ValueError('Request differs')
    model_specs(cfg['models']);membership(cfg)
    if code_pins()!=cfg['reader']['code_pins']:raise ValueError('Reader source changed')
    status=load(dest/'BIND_STATUS.json')
    if not status['ready'] or sha(dest/'frames/0.json')!=status['frames_sha256']:raise ValueError('Frame stage differs')
    return cfg,status


def launch(dest,attempt='a0'):
    dest=Path(dest);cfg,status=verify_bound(dest)
    if cfg.get('mode') == 'proof':
        import fakes
        fakes.install_engine([t['example_id'] for t in tasks(cfg)])
    else:
        if not os.environ.get('CUDA_VISIBLE_DEVICES') or ',' in os.environ['CUDA_VISIBLE_DEVICES']:
            raise ValueError('Require one visible GPU')
        import vllm
        if vllm.__version__!=cfg['engine_version']:raise ValueError('Engine version differs')
    check_export(cfg['models']['cp1m200']['path'],EXPORT_SHA,cfg['models']['base']['path'],544)
    import stage,worker,merge,budget_merge
    base=stage.prepare(cfg['models']['base'],None,dest/'m/0')
    path=stage.prepare(cfg['models']['cp1m200'],base,dest/'m/1')
    a=SimpleNamespace(config=str(dest/'request.json'),model=str(path),cell=0,cache=str(dest/'frames'),
        frames_sha256=status['frames_sha256'],rank=0,world=1,attempt=attempt,budget_only=False)
    asyncio.run(worker.run(a))
    merged=merge.merge(cfg,0,attempt)
    if not merged['parity_pass']:raise ValueError('Processor parity failed')
    budget_merge.merge_budgets(cfg,0,attempt)
    return merged
