"""One governed stream: gate(reader) -> ratelimit.py -> (--out local file | --consumer cmd). No tee: each member writes its bytes once."""
import argparse, json, os, signal, subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
G = '/scratch/jjyeung/io_governor'
p = argparse.ArgumentParser()
p.add_argument('--lane', required=True); p.add_argument('--expected-bytes', type=int, required=True)
p.add_argument('--reader', required=True, help='JSON list'); p.add_argument('--out'); p.add_argument('--consumer', help='JSON list')
p.add_argument('--io-weight'); p.add_argument('--kind', default='copy'); p.add_argument('--priority', default='100'); p.add_argument('--dry', action='store_true')
a = p.parse_args()
assert bool(a.out) != bool(a.consumer), 'exactly one of --out/--consumer'
py = sys.executable
r = subprocess.Popen([py, '-s', 'gate.py'] + json.loads(a.reader), stdout=subprocess.PIPE)
if a.out:
    sink = open(a.out, 'xb')
    rl = subprocess.Popen([py, '-s', G + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=r.stdout, stdout=sink)
    procs, members = [r, rl], [rl]
else:
    rl = subprocess.Popen([py, '-s', G + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=r.stdout, stdout=subprocess.PIPE)
    c = subprocess.Popen(json.loads(a.consumer), stdin=rl.stdout); rl.stdout.close()
    procs, members = [r, rl, c], [rl, c]
r.stdout.close()
for _ in range(500):
    if identity(r.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit did not start; inspect, do not retry')
print('pids', [x.pid for x in procs], 'ready', flush=True)
if a.dry:
    os.kill(r.pid, signal.SIGCONT)
else:
    cmd = [py, '-s', G + '/register.py', '--lane', a.lane, '--pid', str(r.pid)]
    for m in members: cmd += ['--member-pid', str(m.pid)]
    cmd += ['--rl-pid', str(rl.pid), '--expected-bytes', str(a.expected_bytes), '--tier', '3', '--kind', a.kind,
            '--nominal-mbps', '0.001', '--allow-resume', '--priority', a.priority] + (['--io-weight', a.io_weight] if a.io_weight else [])
    subprocess.run(cmd, check=True); print('registered; waiting for governor', flush=True)
rc = [x.wait() for x in procs]
print('exit codes', rc, flush=True); sys.exit(1 if any(rc) else 0)
