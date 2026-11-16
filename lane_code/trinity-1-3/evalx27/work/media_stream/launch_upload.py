"""gated_reader.py <HEX>.tar (stopped) | ratelimit.py | ossh.sh 'cat > okh7/<HEX>.tar' ; register, wait. Never retries."""
import json, shlex, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
M = Path('/scratch/jjyeung/orch_n30/evalx27/work/media_stream')
OSSH = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh'
hexname = (M / 'HEX').read_text().strip(); tar = M / (hexname + '.tar'); info = json.loads((M / 'TAR.json').read_text())
assert tar.stat().st_size == info['bytes']
dest = '/project/community/jjyeung/okh7/%s.tar' % hexname
remote = 'set -e; test ! -e %s; umask 077; set -C; cat > %s' % (shlex.quote(dest), shlex.quote(dest))
src = subprocess.Popen(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/gated_reader.py', str(tar)], stdout=subprocess.PIPE)
rl = subprocess.Popen(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
src.stdout.close()
up = subprocess.Popen(['timeout', '7200', 'bash', OSSH, remote], stdin=rl.stdout)
rl.stdout.close()
for _ in range(1000):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise SystemExit('reader did not reach gate or ratelimit did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/register.py', '--lane', 'evalx27_rv_media_upload', '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(info['bytes']), '--tier', '3', '--kind', 'push',
                '--nominal-mbps', '8', '--io-weight', '1', '--allow-resume', '--priority', '25'], check=True)
print('registered reader=%d ratelimit=%d ssh=%d bytes=%d %s' % (src.pid, rl.pid, up.pid, info['bytes'], time.strftime('%FT%TZ', time.gmtime())), flush=True)
src.wait(); rl.wait(); up.wait()
print('rc reader=%d ratelimit=%d ssh=%d %s' % (src.returncode, rl.returncode, up.returncode, time.strftime('%FT%TZ', time.gmtime())), flush=True)
if src.returncode or rl.returncode or up.returncode: raise SystemExit('upload failed; no restart')
print('complete', dest, info['sha256'], flush=True)
