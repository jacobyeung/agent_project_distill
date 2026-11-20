"""One isolated read and its recorded-call worker."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

RULES = ('candidates_argmax',)
COUNTS = (0, 0, 0, 150, 0)
SCHEDULE = ((0, 3),)


def descriptors(package):
    items = json.loads((Path(package)/'items/devs1_routed.json').read_text())['items']
    verify = [r['id'] for r in items if r['question_type'] == 'object_abs_distance'][:30]
    return [dict(arm='tower', modes=['none'], stage1_select_rule='candidates_argmax',
                 save_own_depth=False, perception_memo='verify', perception_memo_modules=['g3t'],
                 perception_memo_verify_ids=verify, types=[3], expected=150)]


def sealed_write(path, value):
    from orchard_h10.common import write
    if path.exists() and json.loads(path.read_text()) != value: raise ValueError('read identity differs')
    write(path, value)


def prepare(config):
    from orchard_h10.common import canonical
    from e2e_reader.perception_memo import settings as memo_settings
    if config.get('optional'): raise ValueError('unexpected optional input')
    base = Path(config['output']); settings = json.loads(Path(config['settings']).read_text())
    memo_settings(settings, required=True)
    spec = descriptors(config['package'])[0]
    chosen = dict(settings, **{k:spec[k] for k in ('stage1_select_rule','save_own_depth',
                  'perception_memo','perception_memo_verify_ids','perception_memo_modules')})
    identity = dict(plan=config['plan_sha256'], inputs=config['inputs_sha256'],
                    operator_sha256=config['operator_sha256'], cards=1,
                    reads=[spec], schedule=[list(x) for x in SCHEDULE])
    sealed_write(base/'metadata/IDENTITY.json', identity)
    path = base/'metadata/reads/0/metadata/0.json'; sealed_write(path, chosen)
    sealed_write(path.parent/'READ_IDENTITY.json', dict(identity, read=0, settings_sha256=canonical(chosen)))
    return {0:dict(config, settings=str(path), capture=str(base.parent/'c/0.gz'),
                   cache_root=str(base/'cache/0'), stop_file=str(base/'metadata/STOP'),
                   single_worker=True, arms=['tower'], modes=['none'], types=['object_abs_distance'],
                   stage1_select_rule='candidates_argmax', **memo_settings(chosen))}


def commands(config, stop_at):
    from orchard_h10.runner import control
    from orchard_h10.common import write, opaque
    root = control(config)
    write(root/'30.json', dict(action=3, package=config['package'], config=config, stop_at=stop_at))
    argv = [config['python'], '-B', '-I', '5.py', '30.json']
    opaque(argv)
    return argv


def rehearsal(config):
    from orchard_h10.runner import control, worker_args
    cfg = prepare(config)[0]; root = control(cfg)
    args = worker_args(dict(config=cfg, type=3, index=0, cards=1, stop_at=1, finish_by=2))
    chosen = json.loads(Path(cfg['settings']).read_text())
    assert chosen['stage1_select_rule'] == 'candidates_argmax'
    assert chosen['perception_memo'] == 'verify' and chosen['perception_memo_modules'] == ['g3t']
    assert chosen['perception_memo_verify_ids'] == descriptors(config['package'])[0]['perception_memo_verify_ids']
    assert args[args.index('--arms')+1] == 'tower' and args[args.index('--modes')+1] == 'none'
    argv = commands(cfg, 1)
    assert json.loads((root/'30.json').read_text())['action'] == 3
    # Exercise the actual tower socket and selector with CPU weight doubles.
    from unittest.mock import patch
    from types import SimpleNamespace
    import torch
    from e2e_reader import stage1, real
    made = []
    def init(obj, detect, head, geometry, rule='null_argmax'):
        obj.rule=rule; obj.head=head; obj.diagnostics={}; made.append(obj)
    head = SimpleNamespace(with_null=lambda *a:torch.tensor([1.,2.,100.]))
    with patch.object(stage1.StageOne,'__init__',init), patch.object(real,'TowerG3T',return_value=None), patch('e2e_reader.geometry.frame_count',return_value=32):
        real.real_perception(None,device='cpu',perception_memo_modules=['g3t'],
                            sam3_tower=object(),selector_head=head,stage1_select_rule=RULES[0]).socket(None,None)
    assert made[0].select(dict(x=torch.zeros(2,58),name='x')) == 1
    from g.w import capture_path, load_rows
    assert capture_path(cfg) == Path(config['output']).resolve().parent/'c/0.gz'
    assert len(load_rows()) == 150
    return [dict(read=0, types=cfg['types'], args=args, worker_argv=argv, settings=chosen, expected=150)]


def run(config, end, cards, launcher=None, clock=time.time):
    from orchard_h10.runner import environment
    from orchard_h10.common import write, opaque
    if len(cards) != 1 or not cards[0]: raise ValueError('require one assigned card')
    cfg = prepare(config)[0]; out = Path(config['output']); marker = Path(cfg['stop_file'])
    # Reserve two 1800 s transfers, a 60 s describe, and the parent's normal return margin.
    stop_at = end-max(config.get('stop_margin',1800), 5100)
    failure = None; result = dict(completed=0, expected=150, repeat_completed=0, repeat_expected=10, complete=False)
    def stop(number, frame): marker.write_text(str(number)+'\n')
    old = {n:signal.signal(n, stop) for n in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT)}
    try:
        if clock() < stop_at and not marker.exists():
            argv = [*cfg['prefix'], *commands(cfg, stop_at)]; opaque(argv)
            (out/'logs').mkdir(exist_ok=True)
            with (out/'logs/3.log').open('ab') as log:
                process = (launcher or subprocess.Popen)(argv, env=environment(cfg,cards[0],0),
                    cwd=out/'metadata/a', stdout=log, stderr=subprocess.STDOUT)
                try:
                    rc = process.wait(timeout=max(1, stop_at-clock()+180))
                except subprocess.TimeoutExpired:
                    marker.write_text('deadline\n'); process.terminate()
                    try: process.wait(timeout=30)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()
                    raise RuntimeError('worker exceeded deadline')
            if (out/'metadata/6.json').exists(): result = json.loads((out/'metadata/6.json').read_text())
            if rc: failure = 'worker exited '+str(rc)
    except Exception as error:
        failure = type(error).__name__+': '+str(error)
    finally:
        for n, handler in old.items(): signal.signal(n, handler)
    result['failure'] = failure or result.get('failure')
    result['complete'] = bool(result['complete'] and not result['failure'])
    write(out/'SUMMARY.json', result)
    return result


def memory_bound(*, captures=(60,), allocation_bytes=200*1024**3):
    g3t = (64*9+64+32+32*51*51*5+51+2)*8
    per_capture = g3t+1024**2; allowance = 64*1024**3
    reads = [dict(read=i, captures=n, memo_bytes=n*per_capture,
                  memo_plus_transient_bytes=(n+3)*per_capture,
                  host_budget_bytes=(n+3)*per_capture+allowance) for i,n in enumerate(captures)]
    return dict(basis='fixed_g3t_shapes', perception_memo_modules=['g3t'], sam_memo_bytes=0,
                sam_measurement_required=False, g3t_capture_bytes_upper=g3t,
                python_overhead_bytes_per_capture=1024**2, transient_capture_copies=3,
                runtime_allowance_bytes=allowance, job_host_bytes=allocation_bytes,
                reads=reads, fits=all(r['host_budget_bytes']<=allocation_bytes for r in reads))


def memory_probe(config):
    from orchard_h10.common import write
    settings = json.loads(Path(config['settings']).read_text())
    if settings['perception_memo_modules'] != ['g3t']: raise ValueError('memo modules differ')
    result = memory_bound(); write(Path(config['output'])/'metadata/MEMORY.json', result)
    if not result['fits']: raise ValueError('memory bound exceeds plan')
    return result


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text()); p = Path(cfg['package'])
    sys.path[:0] = [str(p/'b'), str(p/'tree'), str(p)]
    from orchard_h10.common import install_process_guard, write
    install_process_guard(Path(sys.argv[1]).resolve().parent)
    if cfg.get('rehearsal'):
        write(Path(cfg['config']['output'])/'REHEARSAL.json', rehearsal(cfg['config']))
        if cfg['config'].get('measure_memory'): memory_probe(cfg['config'])
        return
    result = run(cfg['config'], cfg['end'], os.environ['CUDA_VISIBLE_DEVICES'].split(','))
    raise SystemExit(1 if result['failure'] else 0)


if __name__ == '__main__': main()
