"""Pull ONE step-544 export part as a governed stream: gcs_reader | ratelimit.py | file. usage: w544_launch.py N (0-3)"""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'; W = Path('/scratch/jjyeung/orch_n30/k1_ops3/work'); BYTES = 67143680
LANE = 'k1_ops4_meta'
obj = 'gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/metadata_e10fbb95487f3baf.tar'
out = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/partb/meta/e10fbb95.tar')
with open(out, 'xb') as sink:
    src = subprocess.Popen(['/usr/bin/python3', '-s', str(W / 'gcs_reader.py'), obj], stdout=subprocess.PIPE)
    rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=sink)
src.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', LANE, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(BYTES), '--tier', '3',
                '--kind', 'pull', '--nominal-mbps', '8', '--io-weight', '1', '--tunnel-weight', '1', '--allow-resume',
                '--priority', '30'], check=True)
print('%s registered meta reader=%d ratelimit=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.pid, rl.pid), flush=True)
src.wait(); rl.wait()
print('%s exit meta reader=%d ratelimit=%d bytes=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, out.stat().st_size), flush=True)
sys.exit(1 if (src.returncode or rl.returncode) else 0)
