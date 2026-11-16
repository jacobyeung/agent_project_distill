"""Start gated_tar.py (stopped) | ratelimit.py > media.tar.part, register it, wait, verify, rename. Never retries."""
import hashlib, json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
M = Path('/scratch/jjyeung/orch_n30/evalx27/work/media_stream')
PY = '/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/.venv312/bin/python'
NEED = '/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/media/NEED_261.json'
hexname = (M / 'HEX').read_text().strip(); part = M / (hexname + '.tar.part'); final = M / (hexname + '.tar')
expected = int((M / 'EXPECTED_BYTES').read_text())
with open(part, 'xb') as sink:
    src = subprocess.Popen([PY, str(M / 'gated_tar.py'), NEED], stdout=subprocess.PIPE)
    rl = subprocess.Popen(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=sink)
src.stdout.close()
for _ in range(1000):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']: break
    time.sleep(.01)
else:
    raise SystemExit('reader did not reach gate or ratelimit did not start; inspect, do not retry')
subprocess.run(['/usr/bin/python3', '-s', '/scratch/jjyeung/io_governor/register.py', '--lane', 'evalx27_rv_media_read', '--pid', str(src.pid),
                '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(expected), '--tier', '3', '--kind', 'copy',
                '--nominal-mbps', '8', '--allow-resume', '--priority', '25'], check=True)
print('registered reader=%d ratelimit=%d bytes=%d %s' % (src.pid, rl.pid, expected, time.strftime('%FT%TZ', time.gmtime())), flush=True)
src.wait(); rl.wait()
if src.returncode or rl.returncode:
    raise SystemExit('stream failed: reader=%d ratelimit=%d; no restart' % (src.returncode, rl.returncode))
h = hashlib.sha256(); n = 0
with open(part, 'rb') as f:
    for b in iter(lambda: f.read(1 << 20), b''): h.update(b); n += len(b)
if n != expected: raise SystemExit('size %d != expected %d' % (n, expected))
part.rename(final)
(M / 'TAR.json').write_text(json.dumps(dict(archive=str(final), bytes=n, sha256=h.hexdigest(), utc=time.strftime('%FT%TZ', time.gmtime()))))
print('complete', final, n, h.hexdigest(), flush=True)
