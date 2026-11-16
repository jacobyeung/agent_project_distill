"""Launch T2 as one governed stream: t2_reader | ratelimit.py | tar xf (into /scratch/jjyeung/k1/src). No restart."""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'; W = Path(__file__).resolve().parent
LIST = '/scratch/jjyeung/orch_cd/k1_ops/work/MP4_LIST.txt'; DEST = '/scratch/jjyeung/k1/src'; BYTES = 2897489920
src = subprocess.Popen(['/usr/bin/python3', '-s', str(W / 't2_reader.py'), LIST], stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
tx = subprocess.Popen(['tar', 'xf', '-', '-C', DEST], stdin=rl.stdout)
rl.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', 'k1_ops3_t2_mp4', '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--member-pid', str(tx.pid), '--rl-pid', str(rl.pid),
                '--expected-bytes', str(BYTES), '--tier', '3', '--kind', 'copy', '--nominal-mbps', '8',
                '--io-weight', '1', '--tunnel-weight', '0', '--allow-resume'], check=True)
print('%s registered reader=%d ratelimit=%d tar=%d bytes=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.pid, rl.pid, tx.pid, BYTES), flush=True)
src.wait(); rl.wait(); tx.wait()
print('%s exit reader=%d ratelimit=%d tar=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, tx.returncode), flush=True)
sys.exit(1 if (src.returncode or rl.returncode or tx.returncode) else 0)
