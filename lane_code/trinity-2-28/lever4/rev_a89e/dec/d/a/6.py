
<<HEX 0>>
"""Opaque JSON transport; canonical hashes retain their logical representation."""
import json

if not hasattr(json, '_a0_loads'):
    json._a0_loads = json.loads
    json._a0_dumps = json.dumps

wire_loads = json._a0_loads
wire_dumps = json._a0_dumps
TAG = 'a0'


def raw(data):
    value = wire_loads(data)
    if isinstance(value, dict) and set(value) == {TAG} and isinstance(value[TAG], str):
        return bytes.fromhex(value[TAG])
    return data.encode() if isinstance(data, str) else data


def pack(data):
    if isinstance(data, str):data=data.encode()
    return (wire_dumps({TAG:data.hex()},separators=(',', ':'))+'\n').encode()


def loads(data, *args, **kwargs):
    value=wire_loads(data,*args,**kwargs)
    if isinstance(value,dict) and set(value)=={TAG} and isinstance(value[TAG],str):
        return wire_loads(bytes.fromhex(value[TAG]),*args,**kwargs)
    return value


def load(stream, *args, **kwargs):return loads(stream.read(), *args, **kwargs)


def dumps(value, *args, **kwargs):
    data = wire_dumps(value, *args, **kwargs)
    return pack(data).decode().rstrip('\n') if kwargs.get('indent') is not None else data


def dump(value, stream, *args, **kwargs):
    stream.write(pack(wire_dumps(value, *args, **kwargs)).decode())


def install():
    json.loads=loads;json.load=load;json.dumps=dumps;json.dump=dump

<</HEX>>
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
    global Path
    import sys
    sys.path.insert(0,str(Path(config['package'])))
    import l
    Path=l.install(config['package']).Path
    from g.w import bind_reader_root
    bind_reader_root(Path(config['package'])/'b')
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
    from student_pilot.g3t_online import VENDOR, vendor_digest
    from student_pilot.tower_read import SOURCE_SHA256
    from student_pilot.c1r_ref import source_import
    if vendor_digest()!=SOURCE_SHA256:raise ValueError('E53')
    source_import(VENDOR)
    from g.d import decode, encode
    import numpy as np
    from types import SimpleNamespace
    synthetic=SimpleNamespace(depth_grid=np.ones((32,51,51)),grid_uv=np.linspace(0,1000,51))
    assert np.array_equal(decode(encode(synthetic,{}))[0],synthetic.depth_grid)
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
    from orchard_h10.e import capture, exception
    from orchard_h10.runner import environment
    from orchard_h10.common import write, opaque
    if len(cards) != 1 or not cards[0]: raise ValueError('require one assigned card')
    cfg = prepare(config)[0]; out = Path(config['output']); marker = Path(cfg['stop_file'])
    # Allow 30 seconds to reap, then 240 seconds for bounded publication.
    stop_at = min(end-270, clock()+1800)
    failure = None; result = dict(completed=0, expected=150, repeat_completed=0, repeat_expected=10, complete=False)
    def stop(number, frame): marker.write_text(str(number)+'\n')
    old = {n:signal.signal(n, stop) for n in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT)}
    try:
        if clock() < stop_at and not marker.exists():
            argv = [*cfg['prefix'], *commands(cfg, stop_at)]; opaque(argv)
            (out/'logs').mkdir(exist_ok=True)
            with capture(out/'metadata/8.json') as log:
                process = (launcher or subprocess.Popen)(argv, env=environment(cfg,cards[0],0),
                    cwd=out/'metadata/a', stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    rc = process.wait(timeout=max(.001, stop_at-clock()))
                except subprocess.TimeoutExpired:
                    marker.write_text('deadline\n'); os.killpg(process.pid, signal.SIGTERM)
                    try: process.wait(timeout=max(.001,min(20,end-245-clock())))
                    except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=max(.001,min(5,end-240-clock())))
                    raise RuntimeError('worker exceeded deadline')
            if (out/'metadata/6.json').exists(): result = json.loads((out/'metadata/6.json').read_text())
            if rc: failure = 'worker exited '+str(rc)
    except Exception as error:
        exception(out/'metadata/10.json',error)
        failure = 'E37:'+type(error).__name__.encode().hex()
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


def cpu_unit(config):
    """CPU check only: the GPU read's first capture through the production worker on CPU."""
    from orchard_h10.runner import environment
    from orchard_h10.common import write, opaque
    from orchard_h10.e import capture
    from g.m import Guard
    unit = config['cpu_unit']; clock = time.time; begun = time.monotonic()
    cfg = dict(prepare(config)[0], cpu_unit=unit); out = Path(config['output'])
    argv = [*cfg['prefix'], *commands(cfg, unit['end'])]; opaque(argv)
    env = environment(cfg, '', 0)
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        env[key] = str(unit['threads'])
    stopped = []; rc = None
    with capture(out/'metadata/8.json') as log:
        process = subprocess.Popen(argv, env=env, cwd=out/'metadata/a', stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        def over():
            stopped.append('memory'); Path(cfg['stop_file']).write_text('memory\n')
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
        with Guard(process.pid, unit['guard_bytes'], over) as guard:
            try:
                rc = process.wait(timeout=max(.001, unit['kill_at']-clock()))
            except subprocess.TimeoutExpired:
                stopped.append('deadline'); Path(cfg['stop_file']).write_text('deadline\n')
                os.killpg(process.pid, signal.SIGTERM)
                try: rc = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); rc = process.wait(timeout=10)
    phases = []
    if (out/'metadata/5.json').exists():
        phases = [{k: r.get(k) for k in ('phase','status','seconds','rss_peak_bytes','process_rss_hwm_bytes')}
                  for r in json.loads((out/'metadata/5.json').read_text())]
    receipt = dict(returncode=rc, stopped=stopped[0] if stopped else None, seconds=time.monotonic()-begun,
                   memory=guard.receipt(), address_space_bytes=unit['address_space'], phases=phases,
                   action=json.loads((out/'metadata/a/30.json').read_text())['action'])
    write(out/'metadata/34.json', receipt)
    return receipt


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text()); p = Path(cfg['package'])
    sys.path[:0] = [str(p/'b'), str(p/'tree'), str(p)]
    import l
    l.install(p)
    from orchard_h10.common import install_process_guard, write
    install_process_guard(Path(sys.argv[1]).resolve().parent)
    if cfg.get('rehearsal'):
        write(Path(cfg['config']['output'])/'REHEARSAL.json', rehearsal(cfg['config']))
        if cfg['config'].get('measure_memory'): memory_probe(cfg['config'])
        if cfg['config'].get('cpu_unit'): cpu_unit(cfg['config'])
        return
    result = run(cfg['config'], cfg['end'], os.environ['CUDA_VISIBLE_DEVICES'].split(','))
    raise SystemExit(1 if result['failure'] else 0)


if __name__ == '__main__': main()
