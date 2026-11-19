"""One governed stream: gate(reader) -> ratelimit.py -> sink.py (local copy + sha256) -> consumer. Register unless --dry."""
import argparse, json, os, signal, subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
G = '/scratch/jjyeung/io_governor'
p = argparse.ArgumentParser()
p.add_argument('--lane', required=True); p.add_argument('--expected-bytes', type=int, required=True)
p.add_argument('--reader', required=True, help='JSON list'); p.add_argument('--consumer', required=True, help='JSON list')
p.add_argument('--local', required=True); p.add_argument('--priority', type=int, default=100); p.add_argument('--dry', action='store_true')
a = p.parse_args()
py = sys.executable
r = subprocess.Popen([py, '-s', 'gate.py'] + json.loads(a.reader), stdout=subprocess.PIPE)
rl = subprocess.Popen([py, '-s', G + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=r.stdout, stdout=subprocess.PIPE)
r.stdout.close()
sk = subprocess.Popen([py, '-s', 'sink.py', a.local], stdin=rl.stdout, stdout=subprocess.PIPE)
rl.stdout.close()
c = subprocess.Popen(json.loads(a.consumer), stdin=sk.stdout)
sk.stdout.close()
for _ in range(500):
    if identity(r.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit did not start; inspect, do not retry')
print('reader=%d ratelimit=%d sink=%d consumer=%d ready' % (r.pid, rl.pid, sk.pid, c.pid), flush=True)
if a.dry:
    os.kill(r.pid, signal.SIGCONT)
else:
    subprocess.run([py, '-s', G + '/register.py', '--lane', a.lane, '--pid', str(r.pid), '--member-pid', str(rl.pid),
                    '--member-pid', str(sk.pid), '--member-pid', str(c.pid), '--rl-pid', str(rl.pid),
                    '--expected-bytes', str(a.expected_bytes), '--tier', '3', '--kind', 'push', '--nominal-mbps', '0.001',
                    '--allow-resume', '--priority', str(a.priority)], check=True)
    print('registered; waiting for governor', flush=True)
rc = [x.wait() for x in (r, rl, sk, c)]
print('exit codes reader/ratelimit/sink/consumer', rc, flush=True)
sys.exit(1 if any(rc) else 0)
