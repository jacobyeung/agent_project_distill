"""Governed pull of one Orchard archive straight to trinity-1-18 (nothing stored on trinity-3-30).
reader (stopped until the governor continues it; ssh orchard cat FILE as its child) | ratelimit.py | ssh trinity-1-18.ib 'cat > DEST.partial'
usage: pull_launch.py ORCHARD_FILE BYTES DEST_DIR_ON_1_18 PRIORITY  (stream-extracts into DEST_DIR; sha256 of the stream to DEST_DIR/../own_400.stream.sha256)"""
import subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM

H = '/scratch/jjyeung/io_governor'
LANE = 'k1fwd1_own400'
SRC, BYTES, DEST, PRIORITY = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
READER = r'''
import os, signal, subprocess, sys
os.kill(os.getpid(), signal.SIGSTOP)
child = subprocess.Popen(['ssh', '-o', 'ControlMaster=auto', '-o', 'ControlPath=/tmp/cm-n30-orchard-%r', '-o', 'ControlPersist=60m',
                          '-o', 'ConnectTimeout=60', '-o', 'BatchMode=yes', 'orchard', 'cat ' + sys.argv[1]], stdout=subprocess.PIPE)
while True:
    block = child.stdout.read(65536)
    if not block:
        break
    sys.stdout.buffer.write(block)
    sys.stdout.buffer.flush()
sys.exit(child.wait())
'''
src = subprocess.Popen(['/usr/bin/python3', '-s', '-c', READER, SRC], stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', H + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'],
                      stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
import os
TSSH = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh'
sink = subprocess.Popen(['timeout', '7200', 'bash', TSSH, 'trinity-1-18.ib',
                         "set -e; test ! -e %s; mkdir -p $(dirname %s); cat > %s.partial" % (DEST, DEST, DEST)], stdin=rl.stdout,
                        env=dict(os.environ, LCS_ROBUST_SYNC='1', LCS_STAGE_TIMEOUT_OWNER='1'))
rl.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']:
        break
    time.sleep(.01)
else:
    raise RuntimeError('reader did not stop or ratelimit.py did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', H + '/register.py', '--lane', LANE, '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(BYTES), '--tier', '3',
                '--kind', 'pull', '--nominal-mbps', '8', '--io-weight', '1', '--tunnel-weight', '1', '--allow-resume',
                '--priority', PRIORITY], check=True)
print('%s registered reader=%d ratelimit=%d sink=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.pid, rl.pid, sink.pid), flush=True)
src.wait(); rl.wait(); sink.wait()
print('%s exit reader=%d ratelimit=%d sink=%d' % (time.strftime('%FT%TZ', time.gmtime()), src.returncode, rl.returncode, sink.returncode), flush=True)
sys.exit(1 if (src.returncode or rl.returncode or sink.returncode) else 0)
