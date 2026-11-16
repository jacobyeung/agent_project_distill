"""Pull the packed 2,200 pinned ARKit PNGs from Orchard as one governed stream: cmd_reader(ossh cat) | ratelimit.py | file."""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'; W = Path(__file__).resolve().parent; BYTES = 605480960
OSSH = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh'
out = W / 'k1_arkit_pinned_2200.tar'
with open(out, 'xb') as sink:
    src = subprocess.Popen(['/usr/bin/python3', '-s', str(W / 'cmd_reader.py'), 'timeout', '3600', 'bash', OSSH,
                            'cat /project/community/jjyeung/okh7/k1tmp/k1_arkit_pinned_2200.tar'], stdout=subprocess.PIPE)
    rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=sink)
src.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', 'k1_ops3_ark_pinned', '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(BYTES), '--tier', '3',
                '--kind', 'pull', '--nominal-mbps', '8', '--io-weight', '1', '--tunnel-weight', '1', '--allow-resume',
                '--priority', '30'], check=True)
print('%s registered reader=%d ratelimit=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.pid, rl.pid), flush=True)
src.wait(); rl.wait()
print('%s exit reader=%d ratelimit=%d bytes=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, out.stat().st_size), flush=True)
sys.exit(1 if (src.returncode or rl.returncode) else 0)
