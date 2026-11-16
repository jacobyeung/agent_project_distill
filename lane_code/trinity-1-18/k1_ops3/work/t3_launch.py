"""Launch T3 as one governed internet stream: wa_gov.py (fetch, store PNGs) | ratelimit.py | cat > /dev/null. No restart."""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'; W = Path(__file__).resolve().parent; K = '/scratch/jjyeung/orch_cd/k1_ops/work'
PY = '/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python'; BYTES = 730000000
err = open(W / 'WA.log', 'a')
src = subprocess.Popen([PY, '-s', '-B', str(W / 'wa_gov.py'), '7500000', '/scratch/jjyeung/orch_cd/p2_build/c5d3/k6bin/bin/wa.py',
                        K + '/D3_FETCH_PLAN.json', '/scratch/jjyeung/k1_frames', 'k1', str(W / 'WA_OUT.jsonl'), '1'],
                       stdout=subprocess.PIPE, stderr=err, env={'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'PATH': '/usr/bin:/bin'})
rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
sink = subprocess.Popen(['cat'], stdin=rl.stdout, stdout=subprocess.DEVNULL)
rl.stdout.close()
for _ in range(3000):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('fetcher did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', 'k1_ops3_t3_arkit', '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--member-pid', str(sink.pid), '--rl-pid', str(rl.pid),
                '--expected-bytes', str(BYTES), '--tier', '3', '--kind', 'pull', '--nominal-mbps', '7.5',
                '--io-weight', '1', '--tunnel-weight', '1', '--allow-resume', '--priority', '30'], check=True)
print('%s registered fetcher=%d ratelimit=%d sink=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.pid, rl.pid, sink.pid), flush=True)
src.wait(); rl.wait(); sink.wait()
print('%s exit fetcher=%d ratelimit=%d sink=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, sink.returncode), flush=True)
sys.exit(1 if (src.returncode or rl.returncode or sink.returncode) else 0)
