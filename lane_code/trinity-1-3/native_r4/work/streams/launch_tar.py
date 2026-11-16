"""Gated tar stream from /data*: bash child (SIGSTOP self; tar cf - as a child, never exec) | ratelimit.py | tar xf - -C DEST.
usage: launch_tar.py LANE EXPECTED_BYTES SRC_PARENT SRC_NAME DEST_DIR. Never retries."""
import json, subprocess, sys, time, os
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
STREAMS = Path('/data3/jjyeung/orch_n13_20261026/io_governor/streams')
lane, expected, parent, name, dest = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], Path(sys.argv[5])
dest.mkdir(parents=True, exist_ok=False)
log = lambda *a: print(time.strftime('%FT%TZ', time.gmtime()), *a, flush=True)
src = subprocess.Popen(['bash', '-c', 'kill -STOP $$; p=$0; shift 0; tar cf - -C "$p" "$@"; exit $?', parent] + name.split(","), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/ratelimit.py', '-q', '-L', '1000', '-B', '65536'],
                      stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
sink = subprocess.Popen(['tar', 'xf', '-', '-C', str(dest)], stdin=rl.stdout)
rl.stdout.close()
for _ in range(1000):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise SystemExit('reader did not reach gate or ratelimit did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/register.py', '--lane', lane, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(expected), '--tier', '3',
                '--kind', 'copy', '--nominal-mbps', '8', '--allow-resume', '--priority', os.environ.get('PRIO', '50')], check=True)
log('registered', lane, 'reader', src.pid, 'ratelimit', rl.pid, 'bytes~', expected)
src.wait(); rl.wait(); sink.wait()
rec = STREAMS / (lane + '.json')
if src.returncode or rl.returncode or sink.returncode:
    raise SystemExit('stream failed: reader=%d ratelimit=%d sink=%d; no restart' % (src.returncode, rl.returncode, sink.returncode))
if rec.exists(): rec.rename(STREAMS / ('%s.done.%d' % (lane, int(time.time()))))
n = sum(1 for _ in dest.rglob('*.png'))
(dest.parent / (dest.name + '.RECEIPT.json')).write_text(json.dumps(dict(lane=lane, dest=str(dest), source=parent + '/' + name, png_files=n,
    utc=time.strftime('%FT%TZ', time.gmtime())), indent=1))
log('complete', dest, n, 'png')
