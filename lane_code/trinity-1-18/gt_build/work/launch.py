"""One governed stream: reader.py | ratelimit.py | tar xf - -C DEST, registered tier 3 priority 45. No restart.
usage: launch.py LANE ROOT LIST DEST EXPECTED_BYTES"""
import os, subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'; W = '/scratch/jjyeung/orch_n30/gt_build/work'
lane, root, lst, dest, nbytes = sys.argv[1:6]
os.makedirs(dest, exist_ok=True)
src = subprocess.Popen(['/usr/bin/python3', '-s', W + '/reader.py', root, lst, f'{W}/SIZES_{lane}.tsv'], stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
tx = subprocess.Popen(['tar', 'xf', '-', '-C', dest], stdin=rl.stdout)
rl.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', lane, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--member-pid', str(tx.pid), '--rl-pid', str(rl.pid),
                '--expected-bytes', nbytes, '--tier', '3', '--kind', 'copy', '--nominal-mbps', '8',
                '--io-weight', '1', '--tunnel-weight', '0', '--allow-resume', '--priority', '45'], check=True)
print('%s registered %s reader=%d ratelimit=%d tar=%d bytes=%s' % (time.strftime('%FT%TZ', time.gmtime()), lane, src.pid, rl.pid, tx.pid, nbytes), flush=True)
src.wait(); rl.wait(); tx.wait()
print('%s exit %s reader=%d ratelimit=%d tar=%d' % (time.strftime('%FT%TZ', time.gmtime()), lane, src.returncode, rl.returncode, tx.returncode), flush=True)
sys.exit(1 if (src.returncode or rl.returncode or tx.returncode) else 0)
