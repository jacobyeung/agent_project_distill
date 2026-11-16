"""Gated Orchard pull: (bash: SIGSTOP self; exec ossh REMOTE [< STDIN]) | ratelimit.py > OUT.part; register; wait; verify; rename.
usage: launch_pull.py LANE EXPECTED_BYTES SHA256|- OUT REMOTE_CMD [STDIN_FILE]. Never retries."""
import hashlib, json, subprocess, sys, time, os
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
OSSH = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh'
STREAMS = Path('/data3/jjyeung/orch_n13_20261026/io_governor/streams')
lane, expected, want, out, remote = sys.argv[1], int(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), sys.argv[5]
stdin = sys.argv[6] if len(sys.argv) > 6 else '/dev/null'
part = out.with_name(out.name + '.part')
log = lambda *a: print(time.strftime('%FT%TZ', time.gmtime()), *a, flush=True)
with open(part, 'xb') as sink, open(stdin, 'rb') as sin:
    src = subprocess.Popen(['bash', '-c', 'kill -STOP $$; timeout 14400 bash "$0" "$1"; exit $?', OSSH, remote],
                           stdin=sin, stdout=subprocess.PIPE)
    rl = subprocess.Popen(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/ratelimit.py', '-q', '-L', '1000', '-B', '65536'],
                          stdin=src.stdout, stdout=sink)
src.stdout.close()
for _ in range(1000):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise SystemExit('reader did not reach gate or ratelimit did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/register.py', '--lane', lane, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(abs(expected)), '--tier', '3',
                '--kind', 'pull', '--io-weight', '1', '--nominal-mbps', '8', '--allow-resume', '--priority', os.environ.get('PRIO', '50')], check=True)
log('registered', lane, 'reader', src.pid, 'ratelimit', rl.pid, 'bytes', expected)
src.wait(); rl.wait()
rec = STREAMS / (lane + '.json')
if src.returncode or rl.returncode:
    raise SystemExit('stream failed: reader=%d ratelimit=%d; no restart' % (src.returncode, rl.returncode))
h = hashlib.sha256(); n = 0
with open(part, 'rb') as f:
    for b in iter(lambda: f.read(1 << 20), b''): h.update(b); n += len(b)
if rec.exists(): rec.rename(STREAMS / ('%s.done.%d' % (lane, int(time.time()))))
receipt = dict(lane=lane, out=str(out), bytes=n, sha256=h.hexdigest(), expected_bytes=expected, expected_sha256=want,
               utc=time.strftime('%FT%TZ', time.gmtime()))
(out.parent / (out.name + '.RECEIPT.json')).write_text(json.dumps(receipt, indent=1))
if (expected > 0 and n != expected) or (want != '-' and h.hexdigest() != want):
    raise SystemExit('verify failed: %s' % json.dumps(receipt))
part.rename(out)
log('complete', out, n, h.hexdigest())
