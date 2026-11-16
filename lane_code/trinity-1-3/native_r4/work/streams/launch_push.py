"""Gated push to Orchard: bash child (SIGSTOP self; tar cf - as a child, never exec) | ratelimit.py | ossh 'cat > REMOTE.part'.
usage: launch_push.py LANE EXPECTED_BYTES SRC_DIR NAMES(comma) REMOTE_PATH. Verifies sha256 on Orchard, renames .part. Never retries."""
import hashlib, json, subprocess, sys, time, os
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
OSSH = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh'
STREAMS = Path('/data3/jjyeung/orch_n13_20261026/io_governor/streams')
lane, expected, srcdir, names, remote = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4].split(','), sys.argv[5]
log = lambda *a: print(time.strftime('%FT%TZ', time.gmtime()), *a, flush=True)
src = subprocess.Popen(['bash', '-c', 'kill -STOP $$; d=$0; tar cf - -C "$d" "$@"; exit $?', srcdir] + names, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
tee = subprocess.Popen(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
d = os.path.dirname(remote)
sink = subprocess.Popen(['timeout', '14400', 'bash', OSSH, 'mkdir -p %s && cat > %s.part' % (d, remote)], stdin=tee.stdout)
tee.stdout.close()
for _ in range(1000):
    if identity(src.pid)['state'] == 'T' and identity(tee.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise SystemExit('reader did not reach gate or ratelimit did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/register.py', '--lane', lane, '--pid', str(src.pid),
                '--member-pid', str(tee.pid), '--rl-pid', str(tee.pid), '--expected-bytes', str(expected), '--tier', '3',
                '--kind', 'push', '--io-weight', '1', '--nominal-mbps', '8', '--allow-resume', '--priority', os.environ.get('PRIO', '50')], check=True)
log('registered', lane, 'reader', src.pid, 'ratelimit', tee.pid, 'bytes', expected)
src.wait(); tee.wait(); sink.wait()
rec = STREAMS / (lane + '.json')
if src.returncode or tee.returncode or sink.returncode:
    raise SystemExit('stream failed: reader=%d ratelimit=%d sink=%d; no restart' % (src.returncode, tee.returncode, sink.returncode))
if rec.exists(): rec.rename(STREAMS / ('%s.done.%d' % (lane, int(time.time()))))
# local reference sha of the same tar bytes
h = hashlib.sha256(); p = subprocess.Popen(['tar', 'cf', '-', '-C', srcdir] + names, stdout=subprocess.PIPE)
for b in iter(lambda: p.stdout.read(1 << 20), b''): h.update(b)
p.wait(); local = h.hexdigest()
r = subprocess.run(['timeout', '1200', 'bash', OSSH, 'sha256sum %s.part' % remote], stdout=subprocess.PIPE, universal_newlines=True)
remote_sha = (r.stdout.split() or [''])[0]
receipt = dict(lane=lane, remote=remote, local_tar_sha256=local, remote_sha256=remote_sha, utc=time.strftime('%FT%TZ', time.gmtime()))
Path(sys.argv[0]).with_name(lane + '.RECEIPT.json').write_text(json.dumps(receipt, indent=1))
if local != remote_sha: raise SystemExit('verify failed: %s' % json.dumps(receipt))
subprocess.run(['timeout', '120', 'bash', OSSH, 'mv %s.part %s' % (remote, remote)], check=True)
log('complete', remote, local)
