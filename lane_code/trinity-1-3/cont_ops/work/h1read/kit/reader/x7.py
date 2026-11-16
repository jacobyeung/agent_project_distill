"""Pinned additional item population using the accepted prompt and budget pipeline."""
import asyncio
import copy
from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import time
import types
from types import SimpleNamespace as NS

HERE=Path(__file__).resolve().parent
CONSTANTS={'object_counting':62.2,'object_abs_distance':29.5,'object_size_estimation':18.3,
 'room_size_estimation':33.1,'object_rel_direction_easy':51.6,'object_rel_direction_medium':35.6,
 'object_rel_direction_hard':30.7,'obj_appearance_order':25.0,'object_rel_distance':25.0}
COUNTS={'object_counting':385,'object_abs_distance':290,'object_size_estimation':293,
 'room_size_estimation':98,'object_rel_direction_easy':192,'object_rel_direction_medium':194,
 'object_rel_direction_hard':192,'obj_appearance_order':246,'object_rel_distance':279}

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,allow_nan=False)+'\n')

def validate_items(rows,registration):
    from collections import Counter
    if len(rows)!=2169 or len({r['id'] for r in rows})!=2169:
        raise ValueError('Item membership differs')
    if dict(Counter(r['question_type'] for r in rows))!=COUNTS:
        raise ValueError('Type denominator differs')
    if len({r['room'] for r in rows})!=98:raise ValueError('Room membership differs')
    refs=set()
    for row in rows:
        indices=row['source_frame_indices']
        if len(indices)!=32 or indices!=sorted(set(indices)) or len(row['frame_refs'])!=32:
            raise ValueError('Invalid frame selection')
        if any(type(i) is not int or not 0<=i<row['total_num_frames'] for i in indices):
            raise ValueError('Invalid source index')
        if row['fps']<=0 or not row['answer'] or row['room']!=row['scene']:
            raise ValueError('Invalid item metadata')
        refs.update(row['frame_refs'])
    if refs!=set(registration['frames']):raise ValueError('Frame inventory differs')
    return rows

def stage_assets(registration,work):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    files=registration['files']
    for f in files.values():
        path=Path(f['path'])
        if path.is_symlink() or path.stat().st_size!=f['bytes'] or sha(path)!=f['sha256']:
            raise ValueError('Asset bytes differ')
    if shutil.disk_usage(work).free < 200*1024**3+sum(v['bytes'] for v in registration['frames'].values()):
        raise ValueError('Asset staging would breach the local free-space floor')
    rows=validate_items([json.loads(l) for l in Path(files['e52a690b.jsonl']['path']).read_text().splitlines()],registration)
    destination=work/'f0';destination.mkdir()
    seen=set()
    with tarfile.open(files['d81f4a26.tar']['path'],'r:') as archive:
        for member in archive:
            name=member.name
            if (name not in registration['frames'] or name in seen or not member.isfile()
                or Path(name).is_absolute() or '..' in Path(name).parts
                or member.uid or member.gid or member.mtime or member.uname or member.gname):
                raise ValueError('Unexpected asset member')
            pin=registration['frames'][name]
            if member.size!=pin['bytes']:raise ValueError('Frame size differs')
            raw=archive.extractfile(member).read()
            if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('Frame digest differs')
            path=destination/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            seen.add(name)
    if seen!=set(registration['frames']):raise ValueError('Incomplete asset')
    dump(work/'ASSET_CHECK.json',dict(files=files,members=len(seen),verified=True))
    return rows,destination

def install_layout(root):
    """Adapt only layout guards/receipt literals in three authenticated modules."""
    result={}
    for name in ('think_settings','budget','budget_merge'):
        path=Path(root)/(name+'.py');old=path.read_text()
        # All occurrence counts are pinned so an upstream edit cannot expand this patch.
        expected={'think_settings':1,'budget':3,'budget_merge':1}[name]
        if old.count("'duplicate'")!=expected:raise ValueError('Layout source differs')
        new=old.replace("'duplicate'","'spread'")
        module=types.ModuleType(name);module.__file__=str(path)
        sys.modules[name]=module
        exec(compile(new,str(path),'exec'),module.__dict__)
        result[name]=dict(source_sha256=hashlib.sha256(old.encode()).hexdigest(),
                          effective_sha256=hashlib.sha256(new.encode()).hexdigest(),replacements=expected)
    return result

def score_policy(original,task,raw,tokens,cap=16384,finish='stop'):
    result=original(task,raw,tokens,cap=cap,finish=finish)
    if result['hit_token_cap'] or result['parse_failed'] or not result['response_text'].strip():
        result=dict(result,score=0.0)
    return result

def compact(rows,step):
    result=[]
    for row in rows:
        task=row['question_type']
        if row['status']!='complete':raise ValueError('Incomplete output')
        result.append(dict(id=row['id'],family='a7',task_type=task,room=row['room'],scene=row['scene'],
            level=next((l for l in ('easy','medium','hard') if task.endswith('_'+l)),None),
            prediction=row['extracted_answer'],score=row['score'],budget=2048,step=step,
            scoring_basis='answer',pair_id=None,count_kind=row.get('subtype') if task=='object_counting' else None))
    return result

def run(config, reader=None, runtime=None):
    started=time.monotonic();spec=config['spec'];work=Path(spec['run'])/'a7'
    rows,frame_root=stage_assets(config['extra'],work)
    reader=Path(reader or '/scratch/jjyeung/orch_cd/legs1_reads')
    runtime=Path(runtime or '/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt')
    sys.path.insert(0,str(reader/'out'))
    import direct
    if sha(direct.__file__)!='d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a':
        raise ValueError('Reader pin differs')
    direct.check_export(spec['artifact']['path'],spec['artifact']['sha256'],spec['models']['base']['path'],spec['step'])
    vendor,_=direct.modules();origin=vendor.R3
    dest=work/'a0';dest.mkdir();source_sha=origin.copy_kit(runtime,dest/'kit')
    contract=json.loads((HERE/'e193_contract.json').read_text())['main']
    if source_sha!=contract['source_sha256']:raise ValueError('Evaluator source differs')
    root=dest/'kit/evaluator';sys.path.insert(0,str(root))
    import data,scoring
    original=scoring.score_item
    scoring.score_item=lambda task,raw,tokens,cap=16384,finish='stop':score_policy(original,task,raw,tokens,cap,finish)
    data.tasks_for=lambda dataset,roots:copy.deepcopy(rows)
    layout_pins=install_layout(root)
    cell=copy.deepcopy(contract['cells'][0]);cell['layout']='spread'
    cfg={k:copy.deepcopy(contract[k]) for k in ('max_tokens','temperature','thinking','max_model_len','max_seqs','inflight','engine_version','gpus')}
    cfg.update(models=spec['models'],cells=[cell],datasets=[dict(benchmark='devrows')],roots={},
        source_sha256=source_sha,build_only=False,smoke_items=0,
        items_sha256=config['extra']['files']['e52a690b.jsonl']['sha256'],layout_pins=layout_pins)
    cfg['binding']=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
    cfg['output']=str(dest/'results');dump(dest/'request.json',cfg)
    data.tasks_for=lambda dataset,roots:copy.deepcopy(rows)
    # Install the loader before worker imports it. Native parity still checks prompt tokens and pixels.
    import media
    by_id={r['example_id']:r for r in rows}
    @lru_cache(maxsize=8)
    def arrays_for(refs):
        import numpy as np
        from PIL import Image
        arrays=[]
        for name in refs:
            path=frame_root/name
            if sha(path)!=config['extra']['frames'][name]['sha256']:raise ValueError('Frame changed')
            with Image.open(path) as image:
                if image.mode!='RGB' or image.size!=(640,480):raise ValueError('Invalid RGB frame')
                arrays.append(np.array(image))
        return np.stack(arrays)
    def load_frames(task,layout,cache,frames_sha256,**kwargs):
        expected=by_id[task['example_id']]
        if layout!='spread' or any(task[k]!=expected[k] for k in expected):raise ValueError('Frame binding differs')
        arrays=arrays_for(tuple(expected['frame_refs']))
        indices=expected['source_frame_indices'];fps=expected['fps']
        audit=dict(metadata=dict(fps=fps,frames_indices=indices,total_num_frames=expected['total_num_frames'],height=480,width=640),
            anchor_indices=indices,source_frame_indices=indices,timestamps=[i/fps for i in indices],
            pixel_sha256=media.pixel_digest(arrays),layout='spread')
        return arrays,audit
    media.load=load_frames
    from evalpath.official import build_prompt_context
    dump(dest/'PROMPT_PINS.json',{r['id']:hashlib.sha256(build_prompt_context(r,'ours').encode()).hexdigest() for r in rows})
    dump(dest/'frames/0.json',dict(binding=cfg['binding'],items=cfg['items_sha256'],frames=config['extra']['frames']))
    frame_sha=sha(dest/'frames/0.json')
    dump(dest/'BIND_STATUS.json',dict(ready=True,tasks=len(rows),layout='spread',frames_sha256=frame_sha))
    import stage
    reserve=2*sum(r['bytes'] for r in json.loads(Path(spec['models']['base']['manifest']['path']).read_text())['files'])+4*1024**3
    if shutil.disk_usage(work).free<200*1024**3+reserve:raise ValueError('Model space floor')
    base=stage.prepare(spec['models']['base'],None,dest/'models/b0')
    model=stage.prepare(spec['artifact'],base,dest/'models/a0')
    if importlib.import_module('vllm').__version__!=cfg['engine_version']:raise ValueError('Engine version differs')
    # The outer reader worker runs as __main__, leaving this name for the evaluator.
    worker=importlib.import_module('worker')
    args=NS(config=str(dest/'request.json'),model=str(model),cell=0,cache=str(dest/'frames'),
        frames_sha256=frame_sha,rank=0,world=1,attempt='a0',budget_only=False)
    asyncio.run(worker.run(args))
    import merge,budget_merge
    merge.merge(cfg,0,'a0');budget_merge.merge_budgets(cfg,0,'a0')
    for arm in ('0','budget_2048/0','budget_4096/0'):
        summary=json.loads((dest/'results'/arm/'summary_a0.json').read_text())
        if not summary['parity_pass'] or any(v['missing'] or v['completed']!=v['expected'] for v in summary['benchmarks'].values()):
            raise ValueError('Incomplete output or parity failure')
    scored=[json.loads(l) for l in (dest/'results/budget_2048/0/items_a0.jsonl').read_text().splitlines()]
    if {r['id'] for r in scored}!=set(by_id) or len(scored)!=len(rows):raise ValueError('Return membership differs')
    from records import write
    write(work/'ITEMS.jsonl',compact(scored,spec['step']))
    dump(work/'COMPLETE.json',dict(items=len(rows),family='a7',seconds=time.monotonic()-started,
        artifact=spec['artifact'],source_sha256=source_sha,layout_pins=layout_pins))
