"""Governed push to Orchard of a staged folder on trinity-1-18 (streamed over IB through this host, nothing lands here): python3 gov_push24.py LANE BYTES PRIORITY REMOTE_SRC_DIR REMOTE_DIR
root = this script's child 'src' (SIGSTOPs itself before any payload; runs tar as its own child; never execs) (cat TAR) | ratelimit.py | ssh orchard 'tar xf -' into a new folder"""
import os, signal, subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
H = '/scratch/jjyeung/io_governor'
if sys.argv[1] == '--src':
    os.kill(os.getpid(), signal.SIGSTOP)
    sys.exit(subprocess.call(['bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh', 'trinity-1-18.ib', 'cd %s && tar chf - n q u' % sys.argv[2]]))
lane, nbytes, prio, stage, remote = sys.argv[1:6]
assert remote.startswith('/project/community/jjyeung/okh7/x_') and "'" not in remote and stage.startswith('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/')
src = subprocess.Popen(['/usr/bin/python3', '-s', __file__, '--src', stage], stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
sink = subprocess.Popen(['timeout', '14400', 'ssh', '-o', 'ControlMaster=auto', '-o', 'ControlPath=/tmp/cm-n30-orchard-%r', '-o', 'ControlPersist=60m',
                         '-o', 'ConnectTimeout=60', '-o', 'BatchMode=yes', 'orchard', "test ! -e '%s' && mkdir '%s' && cd '%s' && tar xf - && echo EXTRACTED" % (remote, remote, remote)], stdin=rl.stdout)
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
