"""Governed pull of one deterministic Orchard tar.gz stream straight into trinity-1-18 (nothing stored on 3-30 or Orchard).
reader (stopped until the governor continues it; ssh orchard REMOTE_CMD as its child) | ratelimit.py | ssh trinity-1-18.ib receiver
The receiver hashes the stream to DEST/../own_544_fov.stream.sha256 and extracts it into DEST (no archive file kept).
usage: pull2.py REMOTE_CMD BYTES DEST_DIR_ON_1_18 PRIORITY"""
import subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM

H = '/scratch/jjyeung/io_governor'
LANE = 'k1fwd2_fov544'
SRC, BYTES, DEST, PRIORITY = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
READER = r'''
import os, signal, subprocess, sys
os.kill(os.getpid(), signal.SIGSTOP)
child = subprocess.Popen(['ssh', '-o', 'ControlMaster=auto', '-o', 'ControlPath=/tmp/cm-n30-orchard-%r', '-o', 'ControlPersist=60m',
                          '-o', 'ConnectTimeout=60', '-o', 'BatchMode=yes', 'orchard', sys.argv[1]], stdout=subprocess.PIPE)
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
RECV = ("set -e; test ! -e %s; mkdir -p %s; cd %s; /usr/bin/python3 -c 'import hashlib,subprocess,sys\n"
        "h=hashlib.sha256();n=0;p=subprocess.Popen([\"tar\",\"xzf\",\"-\",\"--no-same-owner\"],stdin=subprocess.PIPE)\n"
        "for b in iter(lambda:sys.stdin.buffer.read(1<<20),b\"\"):h.update(b);n+=len(b);p.stdin.write(b)\n"
        "p.stdin.close();r=p.wait();open(\"../own_544_fov.stream.sha256\",\"w\").write(h.hexdigest()+\" \"+str(n)+\" tar=\"+str(r)+\"\\n\");sys.exit(r)'")
TSSH = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh'
sink = subprocess.Popen(['timeout', '7200', 'bash', TSSH, 'trinity-1-18.ib',
                         RECV % (DEST, DEST, DEST)], stdin=rl.stdout,
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
