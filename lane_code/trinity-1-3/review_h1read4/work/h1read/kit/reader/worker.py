"""One fresh process per full accepted family."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import shutil
import time
from contextlib import nullcontext
import read_filter as F
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trinity_read as T
from records import records, write


def validate(family, cfg, tasks):
    path = HERE/'e193_items.json'
    if T.sha(path) != '2ab22b681533c48b7a8ba9a78b7d95d1ea78c4d76beb13ad2784d42738f2cbf1':
        raise ValueError('Item pin differs')
    inventory = T.load(path)['families'][family]
    if (cfg['cells'] != inventory['cells'] or cfg['source_sha256'] != inventory['source_sha256']
            or cfg['datasets'][0]['rows']['sha256'] != inventory['tasks_sha256']):
        raise ValueError('Protocol pin differs')
    actual = {t['example_id']:t['question_type'] for t in tasks}
    if len(actual) != len(tasks) or actual != inventory['items']:
        raise ValueError('Item membership differs')
    protocol_path = HERE/'PROTOCOL.json'
    if T.sha(protocol_path) != 'a2db00df9fbb1c084ca5c3dabc7ce05091210968485079a6fc634b28cd9aa1fd':
        raise ValueError('Protocol reference changed')
    protocol = T.load(protocol_path)[family]
    for key, expected in protocol.items():
        actual = {k:cfg[key][k] for k in expected} if key == 'devs1' else cfg[key]
        if actual != expected:
            raise ValueError('Accepted protocol differs: '+key)


def bind(config, family, work, reader=None, kit=None, camera=None):
    reader = Path(reader or '/scratch/jjyeung/orch_cd/legs1_reads')
    kit = Path(kit or '/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt')
    sys.path.insert(0, str(reader/'out'))
    import direct
    if T.sha(direct.__file__) != 'd16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a':
        raise ValueError('Reader pin differs')
    spec = config['spec']; work = Path(work)
    if family == 'camera':
        from paired_read import Bridge
        direct = Bridge(reader, family, spec, camera=camera)
    T.dump(work/'models.json', spec['models'])
    dest = work/'a0'
    direct.bind(NS(dest=str(dest), models=str(work/'models.json'), export=spec['artifact']['path'],
                   sha256=spec['artifact']['sha256'], step=spec['step'], family=family, kit=str(kit),
                   frames_root=str(work/'f0'), dry=True, parent_standin=False))
    cfg = T.load(dest/'request.json')
    vendor, _ = direct.modules()
    origin = vendor.R3 if family == 'main' else vendor.R4
    data, media, _ = origin.kit_import(dest/'kit')
    from worker import select_tasks
    tasks = sorted(select_tasks(data.tasks_for(cfg['datasets'][0], cfg['roots']), cfg['cells'][0]),
                   key=lambda t:(t['benchmark'], t['example_id']))
    validate(family, cfg, tasks)
    _, _, _, captures = origin.payload(direct.PAYLOADS[family])
    captures = {t['native']:captures[t['native']] for t in tasks}
    return direct, origin, media, dest, cfg, tasks, captures


def run(config, family):
    if family == 'a7':
        from x7 import run as run_extra
        return run_extra(config)
    started = time.monotonic()
    spec = config['spec']; work = Path(spec['run'])/family
    direct, origin, media, dest, cfg, tasks, captures = bind(config, family, work)
    full_tasks = tasks
    population = F.population(tasks, spec)
    tasks = F.select(tasks, spec)
    if 'types' in spec: cfg['types'] = spec['types']
    base_bytes = sum(r['bytes'] for r in T.load(spec['models']['base']['manifest']['path'])['files'])
    weights = T.load(Path(spec['artifact']['path']).parent/'full_weights/full_weights.json')
    model_bytes = sum(r['bytes'] for r in weights['files'])
    rgb = {f['sha256']:c['hw'][0]*c['hw'][1]*3 for c in captures.values() for f in c['frames']}
    reserve = base_bytes+model_bytes+2*sum(rgb.values())+2*1024**3
    if shutil.disk_usage(work).free < 200*1024**3+reserve:
        raise ValueError('Family staging would breach the local free-space floor')
    T.dump(work/'DISK.json', dict(additional_bytes=reserve, floor_bytes=200*1024**3))
    cfg['build_only'] = False
    cfg['legs1']['export_verification'] = direct.check_export(spec['artifact']['path'],
        spec['artifact']['sha256'], spec['models']['base']['path'], spec['step'])
    cfg['legs1']['export_bytes_verified'] = True
    cfg['binding'] = hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ('binding','output')}, sort_keys=True).encode()).hexdigest()
    T.dump(dest/'request.json', cfg)
    need = {f['sha256'] for c in captures.values() for f in c['frames']}
    sys.path.insert(0, str(HERE.parent/'proof'))
    from phase_b import pull_frames
    pull_frames(need, '/project/community/jjyeung/cp4tk_fr/k6tk', work/'f0', spec['interpreters']['p1cpu'])
    frame_sha = origin.make_frames(cfg, full_tasks, captures, media, work/'f0', dest/'frames')
    T.dump(dest/'BIND_STATUS.json', dict(ready=True, dry=False, tasks=len(tasks), frames_sha256=frame_sha))
    provider = F.task_provider(spec, lambda rows: validate(family, cfg, rows)) if 'types' in spec else nullcontext()
    with provider:
        direct.launch(NS(dest=str(dest), attempt='a0'))
        for rel in ('0', 'budget_2048/0', 'budget_4096/0'):
            summary = T.load(dest/'results'/rel/'summary_a0.json')
            if not summary['parity_pass']:
                raise ValueError('Prompt or pixel parity failed')
            if any(x['missing'] or x['completed'] != x['expected'] for x in summary['benchmarks'].values()):
                raise ValueError('Incomplete family')
        import report
        report.export_merged(cfg, 'a0', work/'report')
    with (dest/'results/budget_2048/0/items_a0.jsonl').open() as journal:
        values = records(family, T.load(work/'report/B2048.json'), journal, spec['step'])
    if len(values) != len(tasks) or {r['id'] for r in values} != {t['example_id'] for t in tasks}:
        raise ValueError('Return membership differs')
    write(work/'ITEMS.jsonl', values)
    T.dump(work/'COMPLETE.json', dict(items=len(values), family=family, seconds=time.monotonic()-started,
                                     artifact=spec['artifact'], source_sha256=cfg['source_sha256'], **({'population':population} if 'types' in spec else {})))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--config', required=True)
    p.add_argument('--family', required=True, choices=('main','away','forward','camera','a7'))
    args = p.parse_args(); run(T.load(args.config), args.family)
