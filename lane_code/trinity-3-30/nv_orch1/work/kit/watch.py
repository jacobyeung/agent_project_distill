"""nv_orch1 watcher on trinity-3-30 (tmux nvo_watch). Every 60 s: reads ALLOC.md, the distill inbox, main's meter and nvkey2's meter on Trinity;
pulls the Orchard runner's meter, WAF flag and queue state in one ossh call; applies the ramp plan (work/ramp_plan.json) to Orchard ctl files;
on any BLOCK or 'STOP nv_orch1' line, a WAF 429 on either source, or a new INBOX_TO_DISTILL_ORCH_* file: STOP + scancel every nv_orch1 job,
BLOCK line (WAF only) and a BLOCKER event. Log: work/watch.log; state: work/watch_state.json."""
import json, os, re, subprocess, time, glob
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'; B = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'
D0 = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918'; ALLOC = '/data3/jjyeung/orch_n13_20261026/nv_slots/ALLOC.md'
HB = '/home/jjyeung/agent_project/agent/scratch/devin_lanes/argon_static_nv2_1119/out/HEARTBEAT.log'; NVK2 = B + '/events/nvkey/METER.json'
OSSH = ['timeout', '240', 'bash', B + '/tools/ossh.sh', 'bash -s']; J = open(W + 'ORCHARD_DIR').read().strip()
def utc(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def log(m):
    with open(W + 'watch.log', 'a') as f: f.write('%s %s\n' % (utc(), m))
def ossh(script):
    try: return subprocess.run(OSSH, input=script, capture_output=True, text=True, timeout=260).stdout
    except Exception as e: return 'OSSH FAIL %r' % e
def tail_lines(p, n=4000):
    try:
        with open(p, 'rb') as f:
            f.seek(0, 2); s = f.tell(); f.seek(max(0, s - 200000)); return f.read().decode(errors='ignore').splitlines()[-n:]
    except OSError: return []
st = json.load(open(W + 'watch_state.json')) if os.path.exists(W + 'watch_state.json') else {}
st.setdefault('alloc_n', len(open(ALLOC).read().splitlines())); st.setdefault('t0', time.time()); st.setdefault('applied', []); st.setdefault('stopped', None)
st.setdefault('inbox_seen', sorted(os.path.basename(p) for p in glob.glob(D0 + '/INBOX_TO_DISTILL_ORCH_*')))
def save(): json.dump(st, open(W + 'watch_state.json.tmp', 'w')); os.replace(W + 'watch_state.json.tmp', W + 'watch_state.json')
def event(kind, slug, body):
    T = time.strftime('%Y%m%dT%H%MZ', time.gmtime()); open('%s/events/nvkey/%s_%s_nv_orch1_%s.md' % (B, T, kind, slug), 'w').write(body)
def stop_all(why, waf_rate=None):
    out = ossh('touch %s/ctl/STOP; export TZ=UTC; for j in $(squeue -h -u jjyeung -p preempt -o "%%i %%j" | awk \'$2 ~ /^a15_cot_ap/ {print $1}\' | grep -x -F -f %s/log/JOBIDS); do scancel $j; echo cancelled $j; done; squeue -u jjyeung -o "%%i %%j %%P %%T"\n' % (J, J))
    st['stopped'] = [utc(), why]; save(); log('STOP ALL: %s | %s' % (why, out.replace('\n', ' ; ')[:400]))
    if waf_rate is not None:
        with open(ALLOC, 'a') as f: f.write('%s BLOCK distill nv_orch1: WAF 429 on the Orchard source at %s requests/min (5-min mean); all Orchard traffic stopped; no probe; restart only on the orchestrator\'s word\n' % (utc()[:16] + 'Z', waf_rate))
    event('BLOCKER', 'orchard_stopped', '# nv_orch1 BLOCKER: all Orchard NV traffic stopped\nWhy: %s\nAction: ctl/STOP written and every nv_orch1 preempt job cancelled (%s). Restart only on an ORCH answer.\n' % (why, out.replace('\n', '; ')[:300]))
while True:
    try:
        lines = open(ALLOC).read().splitlines(); new = lines[st['alloc_n']:]; st['alloc_n'] = len(lines)
        why = None
        for l in new:
            if 'STOP nv_orch1' in l and 'stops me' not in l: why = 'ALLOC: ' + l[:160]
            elif re.search(r'^\S+\s+BLOCK\b', l): why = 'ALLOC BLOCK: ' + l[:160]
        inbox = sorted(os.path.basename(p) for p in glob.glob(D0 + '/INBOX_TO_DISTILL_ORCH_*'))
        newin = [x for x in inbox if x not in st['inbox_seen']]; st['inbox_seen'] = inbox
        if newin: why = why or 'main inbox: ' + ', '.join(newin)
        try:
            m2 = json.load(open(NVK2)); sr = str(m2.get('stop_reason') or '')
            if '429' in sr and 'WAF' in sr.upper(): why = why or 'nvkey2 meter: ' + sr[:120]
        except Exception: m2 = {}
        gov = [l for l in tail_lines(HB, 400) if ' gov:' in l][-1:]
        gtot = None
        if gov:
            mm = re.search(r'total ([0-9.]+)', gov[0]); gtot = float(mm.group(1)) if mm else None
        if new: subprocess.run(OSSH, input="cat >> %s/ALLOC.md <<'EOFA'\n%s\nEOFA\n" % (J, '\n'.join(new)), capture_output=True, text=True, timeout=200)
        plan = json.load(open(W + 'ramp_plan.json')) if os.path.exists(W + 'ramp_plan.json') else []
        todo = [p for p in plan if p['at'] <= utc() and p['at'] not in st['applied']]
        ctl = ''
        if todo and not why and not st['stopped']:
            p = todo[-1]
            if gtot is not None and gtot > p.get('max_main', 60): log('ramp step %s held: main gov total %s' % (p['at'], gtot))
            else:
                ctl = 'echo %s > %s/ctl/RATE; echo %s > %s/ctl/INFLIGHT; ' % (p['rate'], J, p['inflight'], J)
                for q in todo: st['applied'].append(q['at'])
                with open(ALLOC, 'a') as f: f.write('%s HOLD distill nv_orch1: Orchard source now %s requests/min (step of the ramp 8/16/32; main gov total %s, nvkey2 %s/min); stops at any BLOCK or WAF 429\n' % (utc()[:16] + 'Z', p['rate'], gtot, m2.get('req_min5')))
                log('ramp step applied: rate %s inflight %s' % (p['rate'], p['inflight']))
        o = ossh('%sexport TZ=UTC; cat %s/meter/METER.json 2>/dev/null; echo; cat %s/ev/WAF429 2>/dev/null; echo "Q $(squeue -h -u jjyeung -p preempt -o "%%i %%j %%T" | tr "\\n" ";")"; for f in %s/out/*.jsonl; do echo "N $(basename $f) $(wc -l < $f)"; done\n' % (ctl, J, J, J))
        rate5 = None
        try: met = json.loads(o.splitlines()[0]); rate5 = met.get('req_min5')
        except Exception: met = {}
        if 'WAF 429' in o: why = why or 'Orchard WAF 429: ' + [l for l in o.splitlines() if 'WAF' in l][0][:160]
        log('main_gov %s nvkey2 %s orchard %s inflight %s list$ %s proxy$ %s stop %s | %s' % (gtot, m2.get('req_min5'), rate5, met.get('inflight'), met.get('dollars_list_total'), met.get('proxy_total'), met.get('stop_reason'), ' '.join(l for l in o.splitlines()[1:] if l.startswith(('Q ', 'N ')))[:300]))
        if why and not st['stopped']: stop_all(why, rate5 if 'WAF' in why else None)
        save()
    except Exception as e: log('ERR %r' % e)
    time.sleep(60)
