"""Bind the admitted reader protocol to the ReVSI five-category cohort."""
import asyncio
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import sys
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'proof'))
sys.path.insert(0,str(HERE/'out'))
sys.path.insert(0,str(HERE/'evaluator'))
from common import sha,load,dump,BASE_SHA
from export_check import check_export
STEPS=(200,400,600,800,1000)
ROWS_SHA='511c7e8a190235bd17b87a903db569abd5f6b245f444b50dfc3785c06f9be1e9'
COUNTS={'object_counting_single':86,'object_counting_multiple':49,
        'object_rel_direction_forward_easy':20,'object_rel_direction_backward_hard':20,
        'object_rel_direction_forward_hard':15,'object_rel_direction_backward_easy':13,
        'object_rel_distance_closest':84,'object_rel_distance_farthest':56,
        'object_size_estimation':273,'route_planning':63}
CELL=dict(model='cp1m200',layout='duplicate',benchmarks=['revsi'],frames=32,
          decoding='greedy',thinking=True,max_tokens=16384,name='a0')


def dataset(rows):
    directory=Path(rows).parent
    names={'rows':'i1.json','membership':'i2.json',
           'videos':'i3.json','indices':'i4.json'}
    spec=dict(benchmark='revsi',set='official999',tier=32,question_types=sorted(COUNTS))
    for key,name in names.items():
        path=directory/name
        spec[key]=dict(path=str(path.resolve()),sha256=sha(path))
    if spec['indices']['sha256']!='290111cf9c2bfa8fec66e70395922b830c2738633abf736600489cdff4b429b2':raise ValueError('Source indices differ')
    return spec



def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def binding(cfg):
    return hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ('binding','output')},sort_keys=True).encode()).hexdigest()


def model_specs(models):
    b,s=models['base'],models['cp1m200']
    if b['kind']!='snapshot' or b['manifest']['sha256']!=BASE_SHA:
        raise ValueError('Base snapshot differs')
    if s['kind']!='c1_export' or not isinstance(s.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',s['sha256']) or s['sha256']=='0'*64:
        raise ValueError('Unbound artifact')
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
        expected = sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/c5.jsonl')))
        if [t['example_id'] for t in rows] != expected:raise ValueError('Proof membership differs')
        return rows
    if dict(Counter(t['question_type'] for t in rows))!=COUNTS:
        raise ValueError('Five-category membership differs')
    return rows


def bind(dest,models,rows,video_root,mode='production',step=400):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    model_specs(models)
    if type(step) is not int or step not in STEPS:raise ValueError('Invalid step')
    if sha(rows)!=ROWS_SHA:raise ValueError('Official questions differ')
    verification=check_export(models['cp1m200']['path'],models['cp1m200']['sha256'],models['base']['path'],step)
    pins=code_pins()
    cfg=dict(models=models,cells=[dict(CELL)],datasets=[dataset(rows)],
        roots=dict(revsi_video_root=str(Path(video_root).resolve())),gpus=1,build_only=False,
        max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,
        smoke_items=0,engine_version='0.32.0',source_sha256=hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),
        reader=dict(step=step,decision_arm='B2048',code_pins=pins,export_verification=verification))
    cfg['mode']=mode
    if mode == 'proof':
        from selection import select
        cfg['datasets'][0]['example_ids']=sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/c5.jsonl')))
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
    check_export(cfg['models']['cp1m200']['path'],cfg['models']['cp1m200']['sha256'],cfg['models']['base']['path'],cfg['reader']['step'])
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
