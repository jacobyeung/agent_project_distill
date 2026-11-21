"""CPU real-batch scenarios through the delivered runtime (5.py run(c)) on a tiny export.

Usage: cpu_real_worker.py OUTPUT.json
Runs in either the local p1cpu interpreter or the pinned Orchard interpreter.
Scenarios: all rows admitted (float32 and bfloat16); time guard admits k=2; clock overrun mid-decode
after a row selection (partial evidence, path check passes); overrun before the
first prefill (path check fails). The failing case is finalized and fetched to
show that the CPU return is written.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1])
os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')


def mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return value


result = dict(passed=False, python=sys.executable, scenarios={})
try:
    fixture = mod('cpu_real_fixture', ROOT/'tests/cpu_real_fixture.py')
    fixture.torchvision_fixture(ROOT)
    t = mod('tfix', ROOT/'tests/test_fixes.py')
    t.Fixes.setUpClass()
    import torch, transformers
    result.update(transformers=transformers.__version__, torch=torch.__version__)
    ns = types.SimpleNamespace(ROOT=ROOT, B=t.B, C=t.C, FILES=t.FILES)

    def run(name, change=lambda runtime: None, dtype='float32'):
        p, cfg, _ = t.package()
        runtime = mod('rt_'+name, p/'5.py')
        change(runtime)
        with fixture.tiny_export(ns, p, cfg, dtype):
            runtime.run(p, 'c', time.time()+600)
        summary = t.C.loads((p/'a/1.json').read_bytes())
        real = summary['real_batch'] or {}
        brief = {k: real.get(k) for k in ('status', 'k', 'path_ok', 'steps', 'selects', 'select_needed', 'merge_s')}
        brief.update(passed=summary['passed'], reason=real.get('plan', {}).get('reason'),
                     prefills=len(real.get('prefill_each_s') or []),
                     finishes=[r.get('finish') for r in real.get('rows', [])],
                     agreement=(real.get('agreement') or {}).get('identical'),
                     peak_rss_bytes=real.get('peak_rss_bytes'))
        result['scenarios'][name] = brief
        return p, cfg, summary, runtime

    run('all_rows')
    run('bf16_all_rows', dtype='bfloat16')
    def guard(runtime):
        real = runtime.admission
        def engineered(first, rows, remaining, *a):
            # Leave room for two rows only; the real admission rule decides.
            return real(first, rows, 10+1.1*1.5*first+64*runtime.CPU_STEP_FRACTION*first)
        runtime.admission = engineered
    run('time_guard_k2', guard)
    def stepping(after):
        def change(runtime):
            calls = [0]
            def clock():
                calls[0] += 1
                return time.time()+(10**6 if calls[0] > after else 0)
            runtime.CLOCK = clock
        return change
    run('overrun_mid_decode', stepping(13))
    p, cfg, summary, runtime = run('overrun_before_prefill', stepping(0))
    # The failed CPU return is still finalized and fetched.
    t.ctl.finalize(p, p/'a', cfg, 'c', '123', time.time(), 0)
    t.ctl.fetch(p, p/'f', 'c')
    receipt = t.ctl.read(p/'f/1.json')
    result['overrun_fetch'] = dict(receipt_passed=receipt['passed'], return_bytes=receipt['bytes'])
    s = result['scenarios']
    result['admission'] = dict(
        fits=runtime.admission(50., 8, 2000.)[0], tight=runtime.admission(50., 8, 300.)[0],
        over=runtime.admission(50., 8, 10.), constants=dict(reserve_s=runtime.CPU_RESERVE_S,
        step_fraction=runtime.CPU_STEP_FRACTION, rows=list(runtime.CPU_ROWS), address_space=runtime.ADDRESS_SPACE))
    M = t.ctl.monitor(p)
    result['memory'] = dict(cpu_stop_bytes=M.memory_limit('c'), gpu_stop_bytes=M.memory_limit('g'))
    a = result['admission']
    result['passed'] = bool(
        s['all_rows']['passed'] and s['all_rows']['k'] == 8 and s['all_rows']['agreement'] is True
        and s['all_rows']['selects'] >= 1
        and s['bf16_all_rows']['passed'] and s['bf16_all_rows']['k'] == 8 and s['bf16_all_rows']['status'] == 'complete'
        and s['time_guard_k2']['passed'] and s['time_guard_k2']['k'] == 2 and s['time_guard_k2']['reason'] == 'time_guard'
        and s['time_guard_k2']['prefills'] == 2
        and s['overrun_mid_decode']['status'] == 'interrupted' and s['overrun_mid_decode']['passed']
        and s['overrun_mid_decode']['selects'] >= 1
        and s['overrun_before_prefill']['status'] == 'interrupted' and not s['overrun_before_prefill']['passed']
        and not result['overrun_fetch']['receipt_passed']
        and a['fits'] == 8 and a['tight'] == 4 and a['over'][0] == 2 and a['over'][1]['reason'] == 'over_budget'
        and result['memory']['cpu_stop_bytes'] == 150*1024**3 and runtime.ADDRESS_SPACE['c'] == 190*1024**3)
except BaseException as error:
    result.update(error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
output.write_text(json.dumps(result, indent=2, default=str)+'\n')
raise SystemExit(0 if result['passed'] else 1)
