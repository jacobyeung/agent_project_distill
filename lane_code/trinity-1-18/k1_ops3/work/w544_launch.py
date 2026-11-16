"""Pull ONE step-544 export part as a governed stream: gcs_reader | ratelimit.py | file. usage: w544_launch.py N (0-3)"""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'; W = Path(__file__).resolve().parent; n = int(sys.argv[1]); BYTES = 5395758080
LANE = sys.argv[2] if len(sys.argv) > 2 else 'k1_ops3_w544'
obj = 'gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar.part%02d-of-04' % n
out = Path('/scratch/jjyeung/k1/m544_parts/469ddece_mstop.tar.part%02d-of-04' % n); out.parent.mkdir(exist_ok=True)
with open(out, 'xb') as sink:
    src = subprocess.Popen(['/usr/bin/python3', '-s', str(W / 'gcs_reader.py'), obj], stdout=subprocess.PIPE)
    rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=sink)
src.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', LANE + '_p%02d' % n, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(BYTES), '--tier', '3',
                '--kind', 'pull', '--nominal-mbps', '8', '--io-weight', '1', '--tunnel-weight', '1', '--allow-resume',
                '--priority', '40'], check=True)
print('%s registered part%02d reader=%d ratelimit=%d' % (time.strftime('%FT%TZ', time.gmtime()), n, src.pid, rl.pid), flush=True)
src.wait(); rl.wait()
print('%s exit part%02d reader=%d ratelimit=%d bytes=%d' % (time.strftime('%FT%TZ', time.gmtime()), n, src.returncode, rl.returncode, out.stat().st_size), flush=True)
sys.exit(1 if (src.returncode or rl.returncode) else 0)
