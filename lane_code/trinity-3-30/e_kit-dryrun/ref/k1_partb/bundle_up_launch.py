"""Upload the Part B source bundle as ONE governed stream: file_reader | ratelimit.py | gsutil cp - OBJECT. No retry."""
import subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'; W = '/scratch/jjyeung/orch_n30/k1_ops3/work/partb'
SRC = '/scratch/jjyeung/orch_n30/k1_ops3/work/partb/upload/d6e92a81.tar'; BYTES = 44328960; OBJ = 'gs://cmu-gpucloud-jjyeung/q8/b7e31d84a90c62f5/d6e92a81.tar'; LANE = 'k1_ops5_upb7e31d84'
src = subprocess.Popen(['/usr/bin/python3', '-s', W + '/file_reader.py', SRC], stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
up = subprocess.Popen(['/home/jjyeung/google-cloud-sdk/bin/gsutil', '-q', 'cp', '-', OBJ], stdin=rl.stdout)
rl.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', LANE, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(BYTES), '--tier', '3',
                '--kind', 'push', '--nominal-mbps', '8', '--io-weight', '1', '--tunnel-weight', '1', '--allow-resume',
                '--priority', '30'], check=True)
print('%s registered %s reader=%d ratelimit=%d gsutil=%d' % (time.strftime('%FT%TZ', time.gmtime()), LANE, src.pid, rl.pid, up.pid), flush=True)
src.wait(); rl.wait(); up.wait()
print('%s exit reader=%d ratelimit=%d gsutil=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, up.returncode), flush=True)
sys.exit(1 if (src.returncode or rl.returncode or up.returncode) else 0)
