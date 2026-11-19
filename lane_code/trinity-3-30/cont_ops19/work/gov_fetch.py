"""Governed pull of one >=20 MB return: python gov_fetch.py LANE BYTES OUTFILE PRIORITY -- <shell command printed by fetch, without the '> target' redirect>
root = this script's child 'src' (SIGSTOPs itself before any payload; runs the transport as its own child; never execs) | ratelimit.py | OUTFILE"""
import os, signal, subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'
if sys.argv[1] == '--src':
    os.kill(os.getpid(), signal.SIGSTOP)
    sys.exit(subprocess.call(['bash', '-c', sys.argv[2]]))
lane, nbytes, out, prio = sys.argv[1:5]; cmd = sys.argv[sys.argv.index('--') + 1]
with open(out, 'xb') as sink:
    src = subprocess.Popen(['/usr/bin/python3', '-s', __file__, '--src', cmd], stdout=subprocess.PIPE)
    rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=sink)
src.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('src did not stop or ratelimit did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', lane, '--pid', str(src.pid), '--member-pid', str(rl.pid),
                '--rl-pid', str(rl.pid), '--expected-bytes', nbytes, '--tier', '3', '--kind', 'pull', '--nominal-mbps', '8',
                '--io-weight', '1', '--allow-resume', '--priority', prio], check=True)
print('%s registered src=%d rl=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.pid, rl.pid), flush=True)
src.wait(); rl.wait()
print('%s exit src=%d rl=%d bytes=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, os.path.getsize(out)), flush=True)
sys.exit(1 if (src.returncode or rl.returncode) else 0)
