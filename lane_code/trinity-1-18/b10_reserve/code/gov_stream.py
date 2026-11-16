"""Launch one governed read stream: gated tar reader (list of files under ROOT) | ratelimit.py | tar x into DEST.

Run under setsid from /scratch on this host. Registers with the IO governor (tier 3) and waits; never restarts.
usage: gov_stream.py --lane NAME --list FILE --root /data2/... --dest /scratch/... --priority 15
"""
import argparse, os, subprocess, sys, time
from pathlib import Path
G = '/scratch/jjyeung/io_governor'
sys.path.insert(0, G)
from signal_helper import identity, COMM  # noqa: E402
from ioconfig import CFG  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument('--lane', required=True); p.add_argument('--list', required=True)
p.add_argument('--root', required=True); p.add_argument('--dest', required=True)
p.add_argument('--priority', type=int, default=15)
a = p.parse_args()
assert Path.cwd().as_posix().startswith('/scratch/') and a.dest.startswith('/scratch/')
if (Path(CFG['streams_dir']) / (a.lane + '.json')).exists():
    p.error('record exists; rename it first')
rels = [l.strip() for l in open(a.list) if l.strip()]
size = sum(os.path.getsize(os.path.join(a.root, r)) for r in rels) + 1536 * len(rels) + 10240
os.makedirs(a.dest, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))
src = subprocess.Popen([sys.executable, '-s', os.path.join(here, 'gated_tar_reader.py'), a.list, a.root], stdout=subprocess.PIPE)
rl = subprocess.Popen([sys.executable, '-s', os.path.join(G, 'ratelimit.py'), '-q', '-L', '1000', '-B', '65536'],
                      stdin=src.stdout, stdout=subprocess.PIPE)
sink = subprocess.Popen(['tar', 'xf', '-', '-C', a.dest], stdin=rl.stdout)
src.stdout.close(); rl.stdout.close()
for _ in range(1000):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']:
        break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not reach the gate or ratelimit did not start; inspect, do not retry')
subprocess.run([sys.executable, '-s', os.path.join(G, 'register.py'), '--lane', a.lane, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(size), '--tier', '3',
                '--kind', 'copy', '--nominal-mbps', '8', '--allow-resume', '--priority', str(a.priority)], check=True)
print('Registered %s reader=%d ratelimit=%d sink=%d bytes=%d files=%d' % (a.lane, src.pid, rl.pid, sink.pid, size, len(rels)), flush=True)
src.wait(); rl.wait(); sink.wait()
rc = (src.returncode, rl.returncode, sink.returncode)
print('EXIT', rc, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), flush=True)
if any(rc):
    raise SystemExit('transfer failed %r; no automatic restart' % (rc,))
