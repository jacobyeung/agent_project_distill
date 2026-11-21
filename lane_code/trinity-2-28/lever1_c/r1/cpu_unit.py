"""CPU check: run the job's first real capture through the production worker on CPU.

The Orchard CPU check (no GPU assigned) already boots, stages and rehearses.
This patch makes it then launch the production worker exactly as the GPU
operator does (operator commands -> numeric entry action 3 -> g.w.run), with
the full step-544 carrier, heads and G3T weights on CPU, and requires that
unit to run clean before CPU.json can pass. a/9.py and the GPU bootstrap
require the same receipt.
"""

# Allocation end E = min(start + plan seconds, SLURM_JOB_END_TIME). The worker
# must stop by E-360 s; the operator kills it at E-330 s, so CPU.json is written
# well before Slurm's USR1 at E-120 s and the supervisor's failure fallback.
UNIT_STOP_S = 360
UNIT_KILL_S = 330
# Worker address space (CPU unit only; the GPU worker has no cap) and the
# page-cache-aware guard (cgroup charge minus file LRU) for the 200G job.
ADDRESS_SPACE = 180*1024**3
GUARD_BYTES = 170*1024**3
# Seconds on 16 EPYC 9224 threads in the pinned environment (tmp/bench, see
# REPORT.md); the worker multiplies the sum by UNIT_SAFETY and adds the margin.
ESTIMATES = dict(first_model={'32': 400, '64': 1200}, load=420, prefill=150, margin=60)

HELPERS = '''

def unit_config(cfg):
    """Deadlines, threads and limits for the CPU real unit."""
    import time
    start=float(os.environ.get('SLURM_JOB_START_TIME',time.time()))
    seconds=int(cfg.get('budget_gpu_seconds',3000))
    end=min(start+seconds,float(os.environ.get('SLURM_JOB_END_TIME',start+seconds)))
    threads=len(os.sched_getaffinity(0))
    return dict(end=end-%(stop)d,kill_at=end-%(kill)d,allocation_end=end,threads=threads,
                slurm_cpus=os.environ.get('SLURM_CPUS_PER_TASK'),address_space=%(space)d,
                guard_bytes=%(guard)d,estimates=%(estimates)r)


def collect_unit(root, cfg, package):
    """Read the worker and operator receipts; never raises."""
    from orchard_h10.common import template
    J=template()[1]
    try:
        meta=J.physical(root,cfg['logical']+'/r/metadata')
        unit=json.loads((meta/'33.json').read_text()) if (meta/'33.json').exists() else dict(passed=False,status='absent')
        process=json.loads((meta/'34.json').read_text()) if (meta/'34.json').exists() else dict(returncode=None,stopped='absent')
        unit['process']=process
        unit['passed']=bool(unit.get('passed') is True and process.get('returncode')==0
                            and process.get('stopped') is None and process.get('memory',{}).get('over') is False)
    except Exception as error:
        unit=dict(passed=False,status='unreadable',error=(type(error).__name__+': '+str(error))[:2048])
    if not unit['passed']:
        try:
            raw=json.dumps(unit)
            if len(raw)>100_000:unit={k:unit.get(k) for k in ('passed','status','failure','error','stages','admission','process','unit')};raw=json.dumps(unit)[:100_000]
            with (package/'a/31.json').open('w') as stream:stream.write(raw)
        except Exception:pass
    return unit

''' % dict(stop=UNIT_STOP_S, kill=UNIT_KILL_S, space=ADDRESS_SPACE, guard=GUARD_BYTES, estimates=ESTIMATES)

OPERATOR = '''

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
            stopped.append('memory'); Path(cfg['stop_file']).write_text('memory\\n')
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
        with Guard(process.pid, unit['guard_bytes'], over) as guard:
            try:
                rc = process.wait(timeout=max(.001, unit['kill_at']-clock()))
            except subprocess.TimeoutExpired:
                stopped.append('deadline'); Path(cfg['stop_file']).write_text('deadline\\n')
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
'''


def patch(nf, pf, B, here):
    op = nf['a/6.py'].decode()
    op = B.once(op, "\n\ndef main():\n", OPERATOR + "\n\ndef main():\n")
    op = B.once(op, "        if cfg['config'].get('measure_memory'): memory_probe(cfg['config'])\n",
                "        if cfg['config'].get('measure_memory'): memory_probe(cfg['config'])\n"
                "        if cfg['config'].get('cpu_unit'): cpu_unit(cfg['config'])\n")
    nf['a/6.py'] = op.encode()
    s = nf['a/5.py'].decode()
    s = B.once(s, "\n\ndef main():\n", HELPERS + "\ndef main():\n")
    s = B.once(s, "    write(dispatch/'1.json',dict(action=1,package=run_cfg['package'],config=run_cfg,rehearsal=True))\n",
               "    run_cfg['cpu_unit']=unit_config(cfg)\n"
               "    write(dispatch/'1.json',dict(action=1,package=run_cfg['package'],config=run_cfg,rehearsal=True))\n")
    start = s.index("    with __import__('orchard_h10.e',fromlist=['capture']).capture(root/'22.json') as log:\n        entry_sequence=dispatch_operator(")
    stop = s.index("check=True)\n", start) + len("check=True)\n")
    block = s[start:stop]
    indented = ''.join('    '+line if line.strip() else line for line in block.splitlines(True))
    s = s[:start] + "    try:\n" + indented + "    finally:\n        real=collect_unit(root,cfg,package)\n" \
        "    compare('CPU real unit passed',True,real['passed'])\n" + s[stop:]
    s = B.once(s, "    write(results/'CPU.json',dict(boot=", "    write(results/'CPU.json',dict(real_unit=real,real_unit_passed=True,boot=")
    nf['a/5.py'] = s.encode()
    s = nf['a/9.py'].decode()
    s = B.once(s, "print('All CPU receipt checks passed')", CHECK + "print('All CPU receipt checks passed')")
    nf['a/9.py'] = s.encode()


CHECK = '''u=c['real_unit']
assert c['real_unit_passed'] is True and u['passed'] is True and u['mode']=='cpu' and u['status']=='complete',dict(check='CPU real unit',status=u.get('status'),error=u.get('error'))
assert [x['name'] for x in u['stages']]==['bind','first_model','load','prefill','record'],dict(check='CPU real unit stages',found=[x['name'] for x in u['stages']])
assert u['stages'][2]['step']==544 and 'torch.bfloat16' in u['stages'][2]['dtypes'] and u['stages'][2]['locations']==['cpu']
k=u['checks']
assert k['clean'] is True and k['grid']['shape']==[32,51,51] and k['grid']['dtype']=='float16' and k['grid']['finite'] is True
assert k['scale']['finite'] is True and k['scale']['value']>0 and k['K']['finite'] is True and k['prefills']==1 and k['decode_steps']==0
assert u['failure'] is None and u['completed']==1 and u['admission']['reason'] in ('first_unit','time_guard','over_budget')
assert u['environment']['threads']==u['unit']['threads']>=1 and u['environment']['cuda_visible']==''
r=u['process']
assert r['returncode']==0 and r['stopped'] is None and r['memory']['over'] is False and r['action']==3
'''


def bootstrap(data):
    """GPU bootstrap: the CPU proof must include the passing real unit."""
    return B_once(data, b" if not (proof['passed'] is True and",
                  b" if not (proof['passed'] is True and proof.get('real_unit_passed') is True and proof.get('real_unit',{}).get('passed') is True and")


def B_once(data, old, new):
    if data.count(old) != 1:
        raise ValueError('patch anchor')
    return data.replace(old, new)
