"""CPU planning and production wrapper, executed inside the staged namespace."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import trinity_read as T


def bind_plan(config, family, work, ids=None, first=None, reader=None, kit=None, camera=None):
    if family not in T.FAMILIES:
        raise ValueError('Unknown dev-S1 direct family')
    fixture_reader = reader is not None
    reader = Path(reader or '/scratch/jjyeung/orch_cd/legs1_reads')
    kit = Path(kit or '/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt')
    sys.path.insert(0, str(reader/'out'))
    import direct
    spec = config['spec']; work = Path(work)
    if family == 'camera' or spec.get('model_slot') or spec.get('paired_protocol'):
        import paired_read as P
        direct = P.Bridge(reader, family, spec, camera=camera or (T.physical(T.DEFAULT_ROOT, P.CAMERA) if fixture_reader else None))
    T.dump(work/'models.json', spec['models'])
    dest = work/'direct'/family
    direct.bind(NS(dest=str(dest), models=str(work/'models.json'), export=spec['artifact']['path'],
                   sha256=spec['artifact']['sha256'], step=spec['step'], family=family, kit=str(kit),
                   frames_root=str(work/'pulled'), dry=True, parent_standin=False))
    cfg = T.load(dest/'request.json')
    if family in ('main', 'camera') and (family == 'camera' or spec.get('model_slot') or spec.get('paired_protocol')):
        spec['cell_used'] = cfg['cells'][0]
        spec['protocol_reference'] = 'e193c2a3c'
    vendor, _ = direct.modules(); origin = vendor.R3 if family == 'main' else vendor.R4
    data, media, _ = origin.kit_import(dest/'kit')
    from worker import select_tasks
    all_tasks = select_tasks(data.tasks_for(cfg['datasets'][0], cfg['roots']), cfg['cells'][0])
    from milestone import validate_binding
    validate_binding(family, cfg, all_tasks)
    tasks = T.selected_tasks(all_tasks, ids, first)
    _, _, _, captures = origin.payload(direct.PAYLOADS[family])
    captures = {t['native']:captures[t['native']] for t in tasks}
    need = T.needed(captures, tasks)
    estimates = {f['sha256']:c['hw'][0]*c['hw'][1]*3 for c in captures.values() for f in c['frames']}
    report = dict(family=family, items=len(tasks), family_items=len(all_tasks), ids=[t['example_id'] for t in tasks],
                  need=need, frames=len(need), captures=len(captures), estimated_frame_bytes=estimates)
    T.dump(work/'NEED.json', report)
    return direct, origin, data, media, dest, cfg, tasks, captures, report


def install_filter(data, ids):
    """Filter the shared loader and its already imported aliases; preserve sorted worker order."""
    original = data.tasks_for; wanted = set(ids)
    def filtered(spec, roots):
        if spec['benchmark'] != 'devrows': raise ValueError('Only devrows may reach the reader')
        tasks = original(spec, roots)
        return T.selected_tasks(tasks, list(wanted))
    for module in list(sys.modules.values()):
        if module is not None and getattr(module, 'tasks_for', None) is original:
            module.tasks_for = filtered
    data.tasks_for = filtered


def run(request, config):
    work = Path(request['work'])
    direct, origin, data, media, dest, cfg, tasks, captures, report = bind_plan(
        config, request['family'], work, request.get('ids'), request.get('first'))
    if request['action'] == 'need':
        return report
    if request['action'] != 'read': raise ValueError('Unknown worker action')
    root = Path(os.environ['A_JOB_ROOT'])
    missing = sorted(set(report['need'])-set(T.store_index(root)))
    if missing:
        (work/'NEED.txt').write_text(''.join(h+'\n' for h in missing))
        raise ValueError('NEED: frames absent; refusing launch')
    spec = config['spec']
    cfg['smoke_items'] = len(tasks) if len(tasks) < report['family_items'] else 0
    cfg['build_only'] = False
    cfg['legs1']['export_verification'] = direct.check_export(
        spec['artifact']['path'], spec['artifact']['sha256'], spec['models']['base']['path'], spec['step'])
    cfg['legs1']['export_bytes_verified'] = True
    selection = dict(ids=report['ids'], family=request['family'],
                     order=['benchmark', 'example_id'], wrapper_sha256=T.sha(__file__))
    cfg['trinity_selection'] = selection
    cfg['binding'] = hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ('binding','output')}, sort_keys=True).encode()).hexdigest()
    T.dump(dest/'request.json', cfg)
    T.dump(dest/'SELECTION.json', selection)
    sys.path.insert(0, str(Path(spec['package'])/'proof'))
    import phase_b
    phase_b.pull_frames(set(report['need']), T.STORE, work/'pulled', spec['interpreters']['p1cpu'])
    frame_sha = origin.make_frames(cfg, tasks, captures, media, work/'pulled', dest/'frames')
    T.dump(dest/'BIND_STATUS.json', dict(ready=True, dry=False, tasks=len(tasks),
                                      smoke_items=cfg['smoke_items'], frames_sha256=frame_sha))
    install_filter(data, report['ids'])
    direct.launch(NS(dest=str(dest), attempt=request['attempt']))
    summaries = {}
    for arm, rel in [('ON16k','0'), ('B2048','budget_2048/0'), ('B4096','budget_4096/0')]:
        summary = T.load(dest/'results'/rel/('summary_'+request['attempt']+'.json'))
        summaries[arm] = summary
        if not summary['parity_pass']:
            raise ValueError('Prompt/pixel parity failed for '+arm)
        for benchmark in summary['benchmarks'].values():
            if benchmark['missing'] or benchmark['completed'] != benchmark['expected']:
                raise ValueError('Incomplete item coverage for '+arm)
    T.dump(work/'SUMMARIES.json', summaries)
    # Use the accepted report's label rules, including released-answer primary scores.
    import importlib
    report_module = importlib.import_module('report')
    report_module.export_merged(cfg, request['attempt'], work/'report')
    T.dump(work/'SPEC.json', spec)
    T.dump(work/'CODE_PINS.json', dict(wrapper=T.sha(__file__), direct=T.sha(direct.__file__),
                                     evaluator=T.load(dest/'kit/CODE_PINS.json')))
    T.dump(work/'COMPLETE.json', dict(family=request['family'], ids=report['ids'], arms=list(summaries)))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--input', required=True)
    args = parser.parse_args(); request = T.load(args.input)
    config = T.load(request.get('config', os.environ['A_JOB_CONFIG']))
    result = run(request, config)
    print(json.dumps({k:result[k] for k in ('family','items','frames')}, sort_keys=True))
