import sys, os, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *
limits()
assert not (T/'RUN_STARTED.json').exists(), 'This suite is single-use.'
put(T/'RUN_STARTED.json', dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), pid=os.getpid()))
prepare_sandbox()
raw(T/'bin/python3', '#!/bin/bash\nexec '+PY+' -I -s -B '+str(T/'exec_python.py')+' "$@"\n')
(T/'bin/python3').chmod(0o755)
cases = []
names = ['h_valid', 'h_no_policy', 'h_bad_host', 'rd_success', 'rd_missing', 'rd_bad_job',
         'rv_absent', 'rv_pass', 'rv_identity', 'rv_malformed', 'rv_notpass', 'rv_mode']
for i, name in enumerate(names, 2421):
    base = T/'cases'/name
    record = command(name, base/'root', base/'project', str(i),
                     [str(T/'bin/python3'), '-I', '-s', '-B', str(T/'case.py'), name, str(i)])
    p = base/'case_result.json'
    case = load(p) if p.exists() else dict(case=name, verdict='FAIL', assertions=[dict(assertion='case result produced', pass_=False)])
    case['command_exit_code'] = record['exit_code']
    case['elapsed_seconds'] = record['seconds']
    cases.append(case)
    put(T/'case_results.json', cases)

def copier_fixture(name, job):
    from base64 import b64decode
    base = T/'cases'/name
    root, project = base/'root', base/'project'
    export = root/'p/q/r/m100'
    payload = raw(export/'payload.txt', 'tiny synthetic export\n'*16)
    put(export/'artifact.json', dict(step=100, synthetic=True, files={'payload.txt': payload}))
    put(export/'config.json', dict(step=100, synthetic=True))
    raw(root/'p/q/r/metrics_0.jsonl', '{"step":100,"loss":1.25}\n')
    put(root/'p/q/r/run_0.json', dict(step=100, status='stopped', synthetic=True))
    for leaf in ('q.log', 'rooms.log', 'h.log', 'rv.log', 't.log'):
        raw(root/leaf, 'tiny synthetic test log\n')
    put(root/'p/r0.json', dict(status='synthetic'))
    raw(root/f'{job}.steps', '100\n')
    names = load(KIT/'k/y.json')
    names = json.loads(b64decode(names['payload'])) if 'payload' in names else names
    key = names['objects']['m100']
    sessions = {key+f'.part{i:02d}-of-04': 'https://127.0.0.1:1/refused' for i in range(4)}
    put(project/'n_s/fake-endpoint.json', sessions)
    put(project/'n_s/sess.json', sessions)
    (project/'n_s').chmod(0o700)
    (project/'n_s/fake-endpoint.json').chmod(0o600)
    (project/'n_s/sess.json').chmod(0o600)
    raw(root/'live_spool/private/sess.json.receipts.jsonl', json.dumps(dict(name=key+'.part03-of-04', bytes=2560, offset=7680, synthetic=True, generation='synthetic-fixture-prior-part'))+'\n')
    (root/'live_spool/private').chmod(0o700)
    return root, project

raw(T/'trap_driver.sh', '''set -eu
umask 077
ROOT="$TEST_KIT"
N="$TEST_ROOT"
export ROOT N
exec 9>"$N/shell.xtrace"
BASH_XTRACEFD=9
PS4='+ pid=$BASHPID line=$LINENO '
set -x
source "$ROOT/b/pc.sh"
printf '%s %s\\n' "$TK_COPY_PID" "$TK_LOG_PID" > "$N/copier_pids"
sleep 0.2
exit 7
''')

for name, job, trap in [('pc_export', '2440', False), ('pc_finish', '2441', True)]:
    root, project = copier_fixture(name, job)
    if trap:
        args = ['/bin/bash', str(T/'trap_driver.sh')]
    else:
        args = [str(T/'bin/python3'), '-I', '-s', '-B', str(KIT/'b/pc.py'), str(KIT), str(root), job,
                '--final', '--sessions', NROOT+'/n_s/fake-endpoint.json']
    record = command(name, root, project, job, args)
    checks = []
    def check(label, condition, **detail):
        checks.append(dict(assertion=label, pass_=bool(condition), **detail))
    live = project/'o'/job/'live'
    marker_path = live/'gcs_m100.json'
    marker = load(marker_path) if marker_path.exists() else None
    check('failure marker produced', marker is not None, observed=marker)
    check('transport reached with usable sessions', marker is not None and marker.get('status') == 'upload pending retry' and marker.get('returncode') == 1)
    check('no false done marker', not (live/'gcs_m100.done').exists())
    check('session directory and file modes valid', (project/'n_s').stat().st_mode & 0o777 == 0o700 and (project/'n_s/fake-endpoint.json').stat().st_mode & 0o777 == 0o600)
    check('private synthetic session copied after validation', (root/'live_spool/private/sess.json').is_file() and load(root/'live_spool/private/sess.json') == load(project/'n_s/fake-endpoint.json'))
    check('work status preserved' if trap else 'copier records failure without failing worker', record['exit_code'] == (7 if trap else 0))
    check('completed within native publication bound', record['seconds'] < (165 if trap else 150), elapsed_seconds=record['seconds'])
    events = []
    for path in (T/'traces').glob(f'python-{job}-*.jsonl'):
        events.extend(json.loads(line) for line in path.read_text().splitlines())
    check('writer attempted a socket in denied sandbox', any(e['event'] == 'socket.__new__' for e in events))
    check('transport refusal observed', any(e['event'] == 'exception' and e.get('file','').endswith('/gc.py') and 'Operation not permitted' in e.get('message','') for e in events))
    check('native writer executed', any(e['event'] == 'executable_source' and e.get('path') == str(KIT/'b/gc.py') for e in events))
    if trap:
        trace = (root/'shell.xtrace').read_text()
        check('tk_live_finish invoked with work status', 'tk_live_finish 7' in trace)
        check('final publication preceded evidence', trace.find('/b/pc.py') < trace.rfind('/b/pc.py') < trace.rfind('/b/ep.py'))
        check('final branch reached', '--final' in trace)
        check('both copier waits precede final', trace.count(' wait ') >= 2 and trace.rfind(' wait ') < trace.find('--final'))
        receipt = load(project/'o'/job/'r1.json')
        check('published work status preserved', receipt['returncode'] == 7)
    case = dict(case=name, verdict='PASS' if all(c['pass_'] for c in checks) else 'FAIL', assertions=checks,
                marker=marker, command_exit_code=record['exit_code'], elapsed_seconds=record['seconds'],
                target_files=['b/pc.py', 'b/gc.py'] + (['b/pc.sh', 'b/sr.py', 'b/ep.py', 'b/z.py'] if trap else []))
    cases.append(case)
    put(T/'case_results.json', cases)
put(T/'RUN_FINISHED.json', dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), cases=len(cases)))
print('SUITE COMPLETE', flush=True)
