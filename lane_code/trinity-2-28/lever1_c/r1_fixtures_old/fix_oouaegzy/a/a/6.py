
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
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
