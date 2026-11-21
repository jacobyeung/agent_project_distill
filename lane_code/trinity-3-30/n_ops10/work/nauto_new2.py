"""n_ops9 nauto: agent-free watch of vehicle N (ORCH ORDER 20261121T0204Z). One cycle per call; makes NO ssh call.
Reads the batched watcher's files (n_ops1/work/mon: job, sleep, last.line, last.raw, state.json, hk.log), keeps the watcher alive,
writes on NFS: events/n_ops/N_WATCH_STATUS.md (rewritten), events/n_ops/N_WATCH_ALERTS.txt (append, one line per flag),
events/n_ops/<UTC>_BLOCKER_<flag>.md (only decision flags, once per job and flag). Exports/checkpoints marked done are read back
from GCS (mint_n.py check, local) and their upload rate is computed from the node's per-attempt log summary (@@ATTO in last.raw).
Runbook: events/n_ops/RUNBOOK_N_WATCH.md."""
import calendar, json, os, re, subprocess, sys, time
E = os.environ.get
W = '/scratch/jjyeung/orch_n30'; M = E('NA_M', W + '/n_ops1/work/mon'); A = E('NA_A', W + '/n_ops9/work/auto')
B = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'; EV = E('NA_EV', B + '/events/n_ops')
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'; MINT = W + '/n_ops1/work/gcs/mint_n.py'
LOOP = A + '/monloop3.sh'; HKA = E('NA_HKA', W + '/n_ops8/work/HOSTKEY_ALERT'); LEDGER = E('NA_LEDGER', W + '/n_ops1/work/ORCHARD_LEDGER.jsonl')
PFX = 'q9/22c714e1/469ddece_'
RB = {  # flag prefix -> (look closer, action by hand); full text in events/n_ops/RUNBOOK_N_WATCH.md
 'STATE_': ('tail -40 MON/last.raw; stage MON/extra.sh with: tail -40 X/o/<job>/j2.log X/o/<job>/j2.err; ls X/o/<job>/live', 'job ended: name the stage from j2.log/live tails; a launch leg that ended early is resumed only on the orchestrator word (resume sessions: runbook "Resume job")'),
 'NOT_ADMIT': ('grep -A3 @@QRES MON/last.raw', 'q refused admission: no training will start; tell tree_rebuild; the job ends itself'),
 'LOGERR_': ('grep -A14 "@@TAIL" MON/last.raw', 'read the error; if it is a refusal by name the job ends itself; otherwise ask the orchestrator before scancel'),
 'JOUT_ERR': ('grep -A8 @@JTAIL MON/last.raw', 'as LOGERR_'), 'OTAR_ERR': ('grep -A8 @@OTAR MON/last.raw', 'job finished with errors in its exit archive: report'),
 'NO_TRAIN_START': ('grep -A4 @@NR MON/last.raw', 'review.json installed but no t.log after 20 min: read q.log/rv.log tails'),
 'NO_FIRST_STEP': ('grep -A14 "@@TAIL t.log" MON/last.raw', 't.log exists, no step 1 in 45 min: read t.log tail; GPU util in @@GPU'),
 'NO_REVIEW_30MIN': ('grep -A4 @@NR MON/last.raw', 'WAITING_REVIEW 30 min without review.json: the reviewer lane must deliver; install per runbook "Review install"; the job refuses at 120 min'),
 'NO_RECEIPT_10MIN': ('grep -A20 @@LSTATE MON/last.raw; grep @@ATTO MON/last.raw', 'export exists but no upload receipt in 10 min: sessions unusable? read live gcs_*.json; never print session URIs'),
 'NONFINITE': ('tail -3 MON/steps.jsonl', 'non-finite loss on a rank: watch the next step; STOP_BAR (all 4 ranks, 2 steps) allows scancel'),
 'STOP_BAR': ('tail -3 MON/steps.jsonl', 'non-finite on all 4 ranks on two consecutive steps: scancel <job> (stage MON/extra.sh: scancel <job>) is allowed without asking'),
 'HELD': ('grep -A3 @@SQ MON/last.raw', 'held job waits for sessions: mint + install per runbook "Sessions", post sha256; the submitter releases'),
 'LOSS3X_': ('tail -5 MON/steps.jsonl', 'a stream is 3x above P for 3 steps: report to the orchestrator; no cancel without its word'),
 'NO_FIRST_CK': ('grep -A10 @@CK MON/last.raw', 'no checkpoint 25 min after step 1: report'), 'NO_EXPORT_': ('grep -A10 @@CK MON/last.raw; grep -A20 @@LIVE MON/last.raw', 'export overdue 45 min: report'),
 'READLOGS': ('cat MON/last.raw', 'two empty checks: Orchard unreachable or the job dir is gone; check ossh by hand once'),
 'RATE<55': ('grep @@ATTO MON/last.raw', 'QUESTION to the orchestrator: stop checkpoint at risk; the last ordinary checkpoint becomes the resume point'),
 'STOP_NOT_UPLOADED': ('ls X/../n_ck/<job>; mint_n.py check ...ckstop.tar.j<job>.part0N-of-04', 'pick the resume checkpoint (n_ck/<job> or the newest ck on GCS) with tree_rebuild'),
 'GCS_PART_MISSING': ('mint_n.py check <object>.j<job>.part0N-of-04', 'a done marker without its GCS parts: report; do not rely on that object'),
 'HOSTKEY': ('tail -20 MON/hk.log; cat n_ops8/work/HOSTKEY_ALERT', 'ORCH ANSWER 0658Z: post the full line to ORCH; a key other than the accepted one: mint or install no session until ORCH answers; read-only calls continue'),
 'WATCHER_DEAD': ('tmux ls; tail -3 MON/hist.txt', 'restart per runbook "Stop and restart"'), 'PROJECT_FS<22G': ('grep @@DF MON/last.raw', 'ORDER 2222Z: BLOCKER at 22 GiB; the stop checkpoint fallback needs size + 50 GiB'),
 'NAMEWORD': ('grep -A12 @@SCTL MON/last.raw', 'a kit word in name/command/workdir/stdout: report at once'), 'NAMEFORM': ('grep -A12 @@SCTL MON/last.raw', 'job name not a15_cot_ap<hex>: report at once'),
 'PROJECT_FS<10G': ('grep @@DF MON/last.raw; tail B/events/n_ops/PROJECT_FS_FREE.txt', 'ORDER 0912Z: ask the user to free space from B/events/n_ops/ORCHARD_REMOVAL_CANDIDATES_20261121.md (no agent removes anything on /project)'),
 'PROJECT_FS<8G_BEFORE_GATE': ('grep @@DF MON/last.raw; cat X/o/<job>_live/gate.txt', 'ORDER 0912Z item 5: the gate files, fallback copy and review install need space; ask the user now with the top entries of ORCHARD_REMOVAL_CANDIDATES_20261121.md'),
 'PROJECT_FS<5G': ('grep @@DF MON/last.raw', 'ORDER 0912Z: as PROJECT_FS<10G, now urgent'),
 'ADV_OTHERS': ('grep -A4 @@SQ MON/last.raw', 'another job of ours on advanced blocks the 4-GPU launch (QOSMaxGRESPerUser): name it to the orchestrator')}
def rb(key):
    for k, v in RB.items():
        if key.startswith(k): return v[0].replace('MON', M), v[1]
    return ('cat %s/last.raw' % M, 'see events/n_ops/RUNBOOK_N_WATCH.md')
DECISION = ('STATE_', 'NOT_ADMIT', 'JOUT_ERR', 'OTAR_ERR', 'LOGERR_', 'NO_TRAIN_START', 'NO_FIRST_STEP', 'NO_REVIEW_30MIN',
            'NO_RECEIPT_10MIN', 'NONFINITE', 'STOP_BAR', 'HELD', 'LOSS3X_', 'NO_FIRST_CK', 'NO_EXPORT_', 'READLOGS',
            'RATE<55', 'STOP_NOT_UPLOADED', 'GCS_PART_MISSING', 'HOSTKEY', 'WATCHER_DEAD', 'PROJECT_FS<22G', 'NAMEWORD', 'NAMEFORM', 'ADV_OTHERS', 'PROJECT_FS<10G', 'PROJECT_FS<8G_BEFORE_GATE', 'PROJECT_FS<5G')
TERMINAL = ('COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'NODE_FAIL', 'OUT_OF_MEMORY', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE')
now = time.time(); utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))
SP = A + '/state.json'; S = json.load(open(SP)) if os.path.exists(SP) else {}
def rd(p, d=''):
    try: return open(p).read()
    except Exception: return d
def sh(cmd, t=60):
    try: return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t).stdout
    except Exception as e: return 'ERR %s' % e
def alert(key, text):
    line = '%s %s %s' % (utc, key, text.replace('\n', ' ')[:600])
    open(EV + '/N_WATCH_ALERTS.txt', 'a').write(line + '\n'); S.setdefault('alog', []).append(line); S['alog'] = S['alog'][-12:]
def blocker(job, key, text, look, act):
    k = '%s|%s' % (job, key)
    if k in S.setdefault('blocked', {}): return
    hr = [t for t in S.setdefault('btimes', []) if now - t < 3600]
    if len(hr) >= 12: alert('BLOCKER_CAP', 'not written (12/h): %s %s' % (key, text[:200])); return
    S['blocked'][k] = utc; S['btimes'] = hr + [now]
    slug = re.sub(r'[^A-Za-z0-9_]+', '_', key)[:60]
    p = '%s/%s_BLOCKER_nauto_%s_job_%s.md' % (EV, time.strftime('%Y%m%dT%H%MZ', time.gmtime(now)), slug, job)
    body = ['# BLOCKER nauto (agent-free N watch, n_ops9/work/auto/nauto.py; to ORCH and tree_rebuild): %s on job %s' % (key, job),
            '1. Seen %s: %s' % (utc, text[:900]), '2. Look closer: %s' % look, '3. Action by hand: %s' % act,
            '4. Watch state: events/n_ops/N_WATCH_STATUS.md; all flags: events/n_ops/N_WATCH_ALERTS.txt; runbook: events/n_ops/RUNBOOK_N_WATCH.md.']
    open(p, 'w').write('\n'.join(body) + '\n'); alert('BLOCKER_WRITTEN', os.path.basename(p))
def tmux_has(s): return True if E('NA_NOTMUX') else subprocess.run(['tmux', 'has-session', '-t', s], capture_output=True).returncode == 0
job = rd(M + '/job', '0').strip() or '0'; line = rd(M + '/last.line').strip().splitlines(); line = line[-1] if line else ''
lm = re.match(r'^\S+ job=(\S+) ', line)
if not lm or lm.group(1) != job: line = ''  # n_ops10 (ORCH NOTE 0659Z): judge a job only from its own lines; a new job has no state until then
raw = rd(M + '/last.raw'); age = now - os.path.getmtime(M + '/last.line') if os.path.exists(M + '/last.line') else 1e9
try: slp = int(rd(M + '/sleep', '120').strip())
except Exception: slp = 120
# 1. host key (ORCH ANSWER 0658Z items 5-6, n_ops10): every line the watcher filtered is in mon/hk.log; the watch keeps running (no mon/stop).
# A warning line raises a BLOCKER. A fingerprint other than the accepted one, or a warning without any fingerprint, also writes HOSTKEY_ALERT,
# which makes sess_job.sh refuse to mint or install until ORCH answers. Lines naming only the accepted key without a warning are logged as alerts.
ACC = 'SHA256:lXwQfg9riWzIueT7rJbgpMFV4YEZuqAYP9ceieGEFDA'
hk = rd(M + '/hk.log').splitlines(); new_hk = hk[S.get('hk_n', 0):]; S['hk_n'] = len(hk)
warn = [l for l in new_hk if re.search(r'IDENTIFICATION HAS CHANGED|POSSIBLE DNS SPOOFING|Host key verification failed|Offending|has changed', l)]
fps = set(re.findall(r'SHA256:[A-Za-z0-9+/=]+', '\n'.join(new_hk))); other = sorted(fps - {ACC})
if warn or other:
    gate = bool(other) or not fps
    if gate and not os.path.exists(HKA): open(HKA, 'w').write(utc + '\n' + '\n'.join(new_hk[:12]) + '\n')
    alert('HOSTKEY', (warn or new_hk)[0])
    blocker(job, 'HOSTKEY', 'host-key line on the Orchard connection (fingerprints seen: %s; accepted %s; %s); watch keeps running: %s' % (
                ', '.join(sorted(fps)) or 'none', ACC, 'HOSTKEY_ALERT written, no mint or install' if gate else 'accepted key, mint not gated',
                ' / '.join(new_hk[:6])),
            'tail -20 %s/hk.log; cat %s' % (M, HKA), 'ORCH ANSWER 0658Z: tell ORCH with the full line; no session minted or installed until ORCH answers if the key is not the accepted one; read-only calls keep running; nobody edits ~/.ssh/config')
elif new_hk: alert('HOSTKEY_LINE', 'accepted key only: ' + new_hk[0])
# 2. watcher alive (restart unless stopped on purpose or a host-key alert stands)
if not tmux_has('nops_mon') and not os.path.exists(M + '/stop'):
    r = [t for t in S.get('restarts', []) if now - t < 3600]
    if len(r) < 3:
        subprocess.run(['tmux', 'new-session', '-d', '-s', 'nops_mon', 'bash ' + LOOP]); S['restarts'] = r + [now]; alert('WATCHER_RESTARTED', 'tmux nops_mon was gone; started bash ' + LOOP)
    else: blocker(job, 'WATCHER_DEAD', 'nops_mon died 3 times within an hour', 'tmux ls; tail -3 %s/hist.txt' % M, 'see runbook "Stop and restart"')
if age > max(3 * slp, 600) and not os.path.exists(M + '/stop'):
    if not S.get('stale'): alert('WATCHER_STALE', 'last.line %d min old' % (age / 60)); S['stale'] = 1
    if age > 1800: blocker(job, 'WATCHER_DEAD', 'last.line %d min old (watcher not reading Orchard)' % (age / 60), 'tmux capture-pane -pt nops_mon | tail; tail -3 %s/hist.txt' % M, 'see runbook "Stop and restart"')
else: S['stale'] = 0
# 3. flags in the newest parse line
fl = [f.strip() for f in line.split(' FLAG ', 1)[1].split(' | ')] if ' FLAG ' in line else []
def g(k):
    m = re.search(r'"%s":("?)([^",}\]]*)\1' % re.escape(k), line); return m.group(2) if m else None
st = g('state'); free = g('proj_free_G'); free = int(free) if free and free.isdigit() else None
if free is not None and free < 22: fl.append('PROJECT_FS<22G %d GiB free' % free)
if free is not None and free < 10: fl.append('PROJECT_FS<10G %d GiB free' % free)
if free is not None and free < 8 and not re.search(r'"step":\s*\d', line): fl.append('PROJECT_FS<8G_BEFORE_GATE %d GiB free' % free)
if free is not None and free < 5: fl.append('PROJECT_FS<5G %d GiB free' % free)
seen = S.setdefault('seen', {}).setdefault(job, {})
keys = set()
for f in fl:
    key = re.split(r'[ :]', f)[0]
    if key in ('PROJECT_DISK<150G', 'EMPTY1'): continue
    keys.add(key)
    if key not in seen:
        seen[key] = utc; alert(key, 'job %s: %s' % (job, f))
        if job not in ('0', 'none') and key.startswith(DECISION):
            blocker(job, key, '%s | line: %s' % (f, line[:700]), *rb(key))
for key in list(seen):
    if key not in keys and not key.startswith('_'): alert('CLEARED', 'job %s: %s' % (job, key)); seen.pop(key)
# 4. new job: mon/job is 0 or terminal and squeue shows a newer advanced job of ours
sq = [l.split('|') for l in re.findall(r'^\d+\|a15_cot_ap[^\n]*', raw, re.M)]
adv = [q for q in sq if len(q) > 3 and q[2] == 'advanced']
cur_dead = job in ('0', 'none') or (st or '').split(' ')[0] in TERMINAL
if cur_dead:
    new = sorted([q for q in adv if int(q[0]) > max(int(S.get('last_job', 0)), int(job) if job.isdigit() else 0)], key=lambda q: int(q[0]))
    if new:
        n = new[-1][0]; open(M + '/job', 'w').write(n + '\n'); open(M + '/sleep', 'w').write('60\n'); S['last_job'] = n
        open(LEDGER, 'a').write(json.dumps({'t': utc, 'job': n, 'name': new[-1][1], 'what': 'detected by nauto on advanced (%s); mon/job set' % new[-1][3], 'by': 'nauto'}) + '\n')
        alert('NEW_JOB', 'job %s %s %s on advanced; mon/job=%s sleep 60' % (n, new[-1][1], new[-1][3], n))
        S.setdefault('jobs', {})[n] = {'t': utc}
        json.dump(S, open(SP + '.tmp', 'w')); os.replace(SP + '.tmp', SP); sys.exit(0)
if job.isdigit(): S['last_job'] = str(max(int(S.get('last_job', 0)), int(job)))
J = S.setdefault('jobs', {}).setdefault(job, {})
sa = re.search(r'^@@SACCT\n(\d+\|[^\n]*)', raw, re.M)
if sa and sa.group(1).split('|')[0].split('.')[0] == job:
    p = sa.group(1).split('|'); J['name'] = p[1]; J['tres'] = p[7] if len(p) > 7 else ''
    J['gpu4'] = 'gres/gpu=4' in J['tres'] or 'gpu:4' in J['tres']
    if J['gpu4'] and os.path.exists(M + '/noadv') and job != '0' and p[3].split(' ')[0] in ('PENDING', 'RUNNING'):
        os.rename(M + '/noadv', M + '/noadv.used'); alert('NOADV_OFF', 'job %s requests 4 GPUs: mon/noadv -> noadv.used (ADV_OTHERS check on)' % job)
# 5. done markers (exports m*, checkpoints ck*, stop objects): GCS readback + rate from @@ATTO
def sect(a, b):
    m = re.search(r'^@@%s\n(.*?)(?=^@@%s)' % (a, b), raw, re.M | re.S); return m.group(1) if m else ''
done = sorted(set(re.findall(r'gcs_(\w+?)\.done', sect('LIVE', 'NR') + sect('LSTATE', 'RCPT'))))
att = {}
for l in re.findall(r'^@@ATTO (\{.*\})$', raw, re.M):
    try: d = json.loads(l); att[d['obj']] = d
    except Exception: pass
J.setdefault('rb', {})
for m in done:
    if m in J['rb'] or not job.isdigit(): continue
    obj = PFX + m + ('.log' if m == 'u' else '.tar'); parts = []
    for i in range(4):
        out = sh('%s %s check %s.j%s.part%02d-of-04' % (PY, MINT, obj, job, i), 60).strip().splitlines()
        try: parts.append(json.loads(out[-1]) if out else None)
        except Exception: parts.append(None)
    ok = [x for x in parts if isinstance(x, dict) and x.get('size')]
    size = sum(int(x['size']) for x in ok); rate = None; a = att.get(obj)
    if a and a.get('last_done') and a.get('first') and a['done'] == 4 and a['last_done'] > a['first']: rate = size / (a['last_done'] - a['first']) / 1e6
    J['rb'][m] = {'t': utc, 'parts_on_gcs': len(ok), 'bytes': size, 'rate_MBps': None if rate is None else round(rate, 1),
                  'md5': [x.get('md5Hash') for x in ok], 'created': [x.get('timeCreated') for x in ok]}
    alert('GCS_READBACK', 'job %s %s: %d/4 parts on GCS, %d B, rate %s MB/s' % (job, m, len(ok), size, 'n/a' if rate is None else '%.1f' % rate))
    if len(ok) < 4: blocker(job, 'GCS_PART_MISSING_' + m, 'done marker gcs_%s.done exists but only %d/4 parts of %s.j%s are on GCS' % (m, len(ok), obj, job),
                            '%s %s check %s.j%s.part0N-of-04 (N=0..3)' % (PY, MINT, obj, job), 'tell tree_rebuild; the stop/resume plan must not rely on %s' % m)
    if rate is not None and size >= 1e9:
        if rate < 55: blocker(job, 'RATE<55_' + m, 'upload of %s (%d B) ran at %.1f MB/s; the stop checkpoint is at risk (ORCH 0104Z)' % (m, size, rate), 'grep @@ATTO %s/last.raw' % M, 'QUESTION to ORCH: raise stop_before_seconds for the next leg or rely on the last ordinary checkpoint')
        elif rate < 84: alert('WARN_RATE<84', 'job %s %s %.1f MB/s (2x rule needs 84)' % (job, m, rate))
# Condition C cadence: first checkpoint and first export landed -> 300 s
if job.isdigit() and slp == 60 and any(k.startswith('m') for k in J['rb']) and any(k.startswith('ck') for k in J['rb']):
    open(M + '/sleep', 'w').write('300\n'); alert('CADENCE', 'job %s: first checkpoint and first export on GCS -> mon/sleep 300' % job)
# 6. job ended: the stop objects must be on GCS (4-GPU jobs that ran >= 20 h)
el = g('elapsed') or ''
if job.isdigit() and (st or '').split(' ')[0] in TERMINAL:
    J.setdefault('ended', now)
    if J.get('gpu4') and not J.get('stopcheck') and now - J['ended'] >= 600:
        J['stopcheck'] = utc; miss = []
        for m in ('ckstop', 'mstop'):
            n_ok = 0
            for i in range(4):
                out = sh('%s %s check %s%s.tar.j%s.part%02d-of-04' % (PY, MINT, PFX, m, job, i), 60).strip().splitlines()
                try: n_ok += bool(out and json.loads(out[-1]))
                except Exception: pass
            J['stop_' + m] = n_ok
            if n_ok < 4: miss.append('%s %d/4' % (m, n_ok))
        if miss: blocker(job, 'STOP_NOT_UPLOADED', 'job ended (%s) and the stop objects are incomplete on GCS: %s; project-fs fallback X/../n_ck/%s may hold the checkpoint' % (st, ', '.join(miss), job),
                         'cat %s/last.raw (@@NCK, @@LIVE); %s %s check %sckstop.tar.j%s.part00-of-04' % (M, PY, MINT, PFX, job), 'tree_rebuild picks the resume checkpoint (last ordinary ck on GCS, or n_ck/<job>)')
        else: alert('STOP_UPLOADED', 'job %s: ckstop and mstop 4/4 parts on GCS' % job)
# 7. STATUS
stp = None
try:
    rows = rd(M + '/steps.jsonl').strip().splitlines(); stp = rows[-1][:400] if rows else None
except Exception: pass
st_lines = ['# N watch status (nauto, rewritten every cycle; agent-free; runbook events/n_ops/RUNBOOK_N_WATCH.md)', 'Updated %s' % utc,
            '- Watcher: nops_mon %s, last Orchard read %d s ago (cadence %d s), mon/stop %s, host-key alert %s; nauto cycle 60 s.' % ('alive' if tmux_has('nops_mon') else 'DEAD', age, slp, 'present' if os.path.exists(M + '/stop') else 'absent', 'PRESENT' if os.path.exists(HKA) else 'none'),
            '- Job %s (%s): state %s, elapsed %s, left %s, stage %s, prep %s%% of 141 min, step %s, proj free %s GiB.' % (job, J.get('name', '?'), st, el, g('left'), g('stage'), g('prep_pct_vs141'), g('step'), free),
            '- Flags now: %s' % (' | '.join(fl) or 'none'), '- Newest parse line: %s' % line[:900], '- Last step row: %s' % stp,
            '- GCS readbacks (done markers): %s' % json.dumps({k: {x: v[x] for x in ('parts_on_gcs', 'bytes', 'rate_MBps', 't')} for k, v in J.get('rb', {}).items()}),
            '- Upload attempts (node summary): %s' % json.dumps({k.replace(PFX, ''): {x: v.get(x) for x in ('parts', 'done', 'att', 'err')} for k, v in att.items()})[:800],
            '- Blockers written: %s' % json.dumps({k: v for k, v in S.get('blocked', {}).items() if k.startswith(job + '|')}),
            '- Last alerts:'] + ['  ' + l[:300] for l in S.get('alog', [])[-8:]]
open(EV + '/N_WATCH_STATUS.md.tmp', 'w').write('\n'.join(st_lines) + '\n'); os.replace(EV + '/N_WATCH_STATUS.md.tmp', EV + '/N_WATCH_STATUS.md')
json.dump(S, open(SP + '.tmp', 'w')); os.replace(SP + '.tmp', SP)
