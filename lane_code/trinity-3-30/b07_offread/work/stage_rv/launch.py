"""Launch stream A (/data2 -> /scratch tar) or B (/data2 -> Orchard pool tar), gated, behind ratelimit.py."""
import json, os, subprocess, sys, time
sys.path.insert(0, '/scratch/jjyeung/io_governor')
from signal_helper import identity, COMM
which = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
GOV = '/scratch/jjyeung/io_governor'
pairs = json.load(open(os.path.join(here, 'LIST_%s.json' % which)))
size = sum(os.stat(s).st_size for s, _ in pairs)
expected = size + 512 * (len(pairs) + 2) + 10240  # tar headers, end blocks, record padding (upper bound)
tok = json.load(open(os.path.join(here, 'TOKENS.json')))
src = subprocess.Popen([sys.executable, os.path.join(here, 'gated_tar.py'), os.path.join(here, 'LIST_%s.json' % which)], stdout=subprocess.PIPE)
if which == 'A':
    sink = open(os.path.join(here, 'A.tar'), 'xb')
    rl = subprocess.Popen([sys.executable, '-s', GOV + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=sink)
    tail = None
else:
    d = '/project/community/jjyeung/okh7/' + tok['pool']; f = d + '/' + tok['obj'] + '.tar'
    rl = subprocess.Popen([sys.executable, '-s', GOV + '/ratelimit.py', '-q', '-L', '1000', '-B', '65536'], stdin=src.stdout, stdout=subprocess.PIPE)
    remote = 'umask 022; mkdir -p %s && cat > %s.part && mv %s.part %s && sha256sum %s && stat -c %%s %s' % (d, f, f, f, f, f)
    tail = subprocess.Popen([sys.executable, os.path.join(here, 'lazy_ssh.py'), remote],
                            stdin=rl.stdout, stdout=open(os.path.join(here, 'B.remote.out'), 'w'), stderr=subprocess.STDOUT)
    rl.stdout.close()
src.stdout.close()
for _ in range(500):
    if identity(src.pid)['state'] == 'T' and identity(rl.pid)['comm'] == COMM['ratelimit']:
        break
    time.sleep(.01)
else:
    raise RuntimeError('gate or ratelimit did not start; inspect, do not retry')
args = [sys.executable, GOV + '/register.py', '--lane', 'b07_offread_rv' + which, '--pid', str(src.pid),
        '--member-pid', str(rl.pid), '--rl-pid', str(rl.pid), '--expected-bytes', str(expected), '--tier', '3',
        '--kind', 'copy' if which == 'A' else 'push', '--nominal-mbps', '8' if which == 'A' else '4', '--allow-resume']
if which == 'A':
    args += ['--io-weight', '1']
if tail is not None:
    args += ['--member-pid', str(tail.pid)]
subprocess.run(args, check=True)
print('registered', which, 'src', src.pid, 'rl', rl.pid, 'bytes', expected, flush=True)
src.wait(); rl.wait()
if tail is not None:
    tail.wait()
print('done', which, src.returncode, rl.returncode, None if tail is None else tail.returncode, flush=True)
