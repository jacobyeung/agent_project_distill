"""Governed pull of one Orchard file to trinity-2-28 (streamed through this host, nothing lands here):
python3 gov_pull_point.py LANE BYTES PRIORITY
root = this script's child 'src' (SIGSTOPs itself before any payload; runs ssh-cat as its own child; never execs) | ratelimit.py | ssh trinity-2-28.ib 'cat > DEST'"""
import os, signal, subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'
SRC = '/project/community/jjyeung/okh7/7c9f2d84/rows.sqlite'
DEST = '/scratch/jjyeung/orch_n30/fb_pack/in/pointing/rows_c09bb5ca.sqlite'
if sys.argv[1] == '--src':
    os.kill(os.getpid(), signal.SIGSTOP)
    sys.exit(subprocess.call(['timeout', '3600', 'ssh', '-o', 'ControlMaster=auto', '-o', 'ControlPath=/tmp/cm-n30-orchard-%r', '-o', 'ControlPersist=60m',
                              '-o', 'ConnectTimeout=60', '-o', 'BatchMode=yes', 'orchard', "cat '%s'" % SRC], stdin=subprocess.DEVNULL))
lane, nbytes, prio = sys.argv[1:4]
src = subprocess.Popen(['/usr/bin/python3', '-s', __file__, '--src'], stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
sink = subprocess.Popen(['bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh', 'trinity-2-28.ib',
                         "mkdir -p %s && cat > %s.part && mv %s.part %s && sha256sum %s && stat -c %%s %s" % (os.path.dirname(DEST), DEST, DEST, DEST, DEST, DEST)], stdin=rl.stdout)
rl.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise RuntimeError('src did not stop or ratelimit did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', lane, '--pid', str(src.pid), '--member-pid', str(rl.pid),
                '--rl-pid', str(rl.pid), '--expected-bytes', nbytes, '--tier', '3', '--kind', 'copy', '--nominal-mbps', '8',
                '--io-weight', '1', '--allow-resume', '--priority', prio], check=True)
print('%s registered src=%d rl=%d sink=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.pid, rl.pid, sink.pid), flush=True)
src.wait(); rl.wait(); sink.wait()
print('%s exit src=%d rl=%d sink=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, sink.returncode), flush=True)
sys.exit(1 if (src.returncode or rl.returncode or sink.returncode) else 0)
