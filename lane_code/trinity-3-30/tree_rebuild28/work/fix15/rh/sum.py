"""Summary of one rehearsal run folder: sum.py <run> <result> <t0>. Writes <run>/summary.json, prints it."""
import json, math, re, sys, time
from pathlib import Path
run, result, t0 = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
log = run / 'log'
def lines(p):
    out = []
    for x in (p.read_text(errors='replace').splitlines() if p.exists() else []):
        try: out.append(json.loads(x))
        except ValueError: pass
    return out
ev = {}
for p in sorted(log.glob('ev_rank*.jsonl')):
    for r in lines(p): ev.setdefault(str(r.get('rank')), []).append(r)
t_launch = int((log / 't0').read_text()) if (log / 't0').exists() else None
ranks = {}
for rk, rs in sorted(ev.items()):
    st = {}
    for r in rs:
        if r['kind'] == 'END': st[r['stage']] = st.get(r['stage'], 0) + r['seconds']
    start = next((r for r in rs if r['kind'] == 'START'), {})
    ranks[rk] = dict(up=bool(start), pid=start.get('pid'), cvd=start.get('cvd'), master=start.get('master'),
                     stage_seconds={k: round(v, 1) for k, v in st.items()},
                     last=(rs[-1]['kind'] + ':' + str(rs[-1].get('stage', rs[-1].get('step', '')))) if rs else None)
steps = {}
for rk, rs in ev.items():
    for r in rs:
        if r['kind'] == 'STEP':
            steps.setdefault(r['step'], {})[rk] = dict(seconds=r['seconds'], stream_means=r['stream_means'], finite=r['finite'],
                                                     peak_allocated_gib=r['peak_allocated_gib'], peak_reserved_gib=r['peak_reserved_gib'],
                                                     skipped=r.get('skipped'))
first_end = min((r['t'] for rs in ev.values() for r in rs if r['kind'] == 'STEP'), default=None)
first_begin = min((r['t'] for rs in ev.values() for r in rs if r['kind'] == 'STEP_BEGIN'), default=None)
errors = [dict(rank=rk, where=r.get('where'), type=r.get('type'), message=r.get('message'), traceback=r.get('traceback'))
          for rk, rs in ev.items() for r in rs if r['kind'] == 'ERROR']
raw = (log / 't.raw.log').read_text(errors='replace') if (log / 't.raw.log').exists() else ''
tbs = [m.group(0)[-6000:] for m in re.finditer(r'Traceback \(most recent call last\):.*?(?=\n\S[^\n]*\n(?![ \t])|\Z)', raw, re.S)]
smi = {}
for x in (log / 'smi.csv').read_text().splitlines() if (log / 'smi.csv').exists() else []:
    f = [v.strip() for v in x.split(',')]
    if len(f) >= 4 and f[2].isdigit():
        smi[f[1]] = max(smi.get(f[1], 0), int(f[2]))
metrics = sorted(run.glob('w/top/p/q/r/smoke/*/metrics_*.jsonl'))
smoke = sorted(run.glob('w/top/p/q/r/smoke/*/smoke.json'))
losses = {str(s): {rk: v['stream_means'] for rk, v in per.items()} for s, per in sorted(steps.items())}
finite = bool(steps) and all(v['finite'] for per in steps.values() for v in per.values())
out = dict(schema='a15-rehearsal-summary-v1', NOT_EVIDENCE_FOR_THE_CARD=True, run=str(run), result=result,
    driver_seconds=int(time.time()) - t0, launch_utc=time.strftime('%FT%TZ', time.gmtime(t_launch)) if t_launch else None,
    ranks_up=sum(1 for v in ranks.values() if v['up']), ranks=ranks,
    seconds_launch_to_first_step_begin=round(first_begin - t_launch, 1) if first_begin and t_launch else None,
    seconds_launch_to_first_step_end=round(first_end - t_launch, 1) if first_end and t_launch else None,
    steps_done={str(s): sorted(per) for s, per in sorted(steps.items())},
    step_seconds_max_over_ranks={str(s): max(v['seconds'] for v in per.values()) for s, per in sorted(steps.items())},
    losses_per_stream=losses, losses_finite=finite,
    peak_gpu_mib_nvidia_smi=smi, peak_allocated_gib_tree={str(s): {rk: v['peak_allocated_gib'] for rk, v in per.items()} for s, per in sorted(steps.items())},
    tree_metrics_files=[str(p) for p in metrics], tree_smoke_report=str(smoke[0]) if smoke else None,
    t_rc=(log / 't.rc').read_text().strip() if (log / 't.rc').exists() else None,
    errors=errors, tracebacks_in_output=tbs[:6], accept=(log / 'accept.log').read_text(errors='replace')[-1500:] if (log / 'accept.log').exists() else None)
(run / 'summary.json').write_text(json.dumps(out, indent=1, default=str) + '\n')
short = {k: v for k, v in out.items() if k not in ('errors', 'tracebacks_in_output', 'ranks', 'accept')}
short['errors'] = [dict(rank=e['rank'], where=e['where'], type=e['type'], message=(e['message'] or '')[:300]) for e in errors][:8]
print(json.dumps(short, default=str)[:6000])
