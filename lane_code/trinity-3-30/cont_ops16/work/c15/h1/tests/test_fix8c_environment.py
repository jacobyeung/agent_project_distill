"""Small local host and nested production-namespace tests; no staging or GPU."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H/'tools'))
import proof_prepare as p

out = Path(tempfile.mkdtemp(prefix='env8c_', dir=H/'evidence/fix8_admission'))
kh = out/'kit'
kh.mkdir(mode=0o700)
for n in ('k', 'b', 'o', 'arm', 'runs'):
    (kh/n).mkdir(mode=0o700)
bw = out/'pinned-only'
shutil.copyfile('/usr/bin/bwrap', bw)
bw.chmod(0o700)
pin = dict(file=str(bw), sha256=p.sha(bw))
(kh/'k/0.json').write_text(json.dumps(dict(bwrap=pin)))
assert p.kit_bwrap(kh) == str(bw)
for bad in (dict(pin, sha256='0'*64), dict(pin, file='bwrap'),
            dict(pin, file=str(out/'absent'))):
    (kh/'k/0.json').write_text(json.dumps(dict(bwrap=bad)))
    try:
        p.kit_bwrap(kh)
    except ValueError:
        pass
    else:
        raise AssertionError('Bad bwrap pin accepted')
(kh/'k/0.json').write_text(json.dumps(dict(bwrap=pin)))
bw.chmod(0o600)
try:
    p.kit_bwrap(kh)
except ValueError:
    pass
else:
    raise AssertionError('Non-executable pin accepted')
bw.chmod(0o700)

with patch.dict(os.environ, {'PATH': '/absent', 'HOME': '/absent', 'BASH_ENV': '/absent',
                            'LD_LIBRARY_PATH': '/absent', 'PYTHONPATH': '/absent',
                            'SLURM_JOB_ID': '123'}, clear=True):
    p.environment()
    p.host_preflight()
    assert os.environ['PATH'] == p.HOST_PATH and os.environ['HOME'] == '/home/jjyeung'
    assert os.environ['SLURM_JOB_ID'] == '123' and 'BASH_ENV' not in os.environ
    assert 'LD_LIBRARY_PATH' not in os.environ and 'PYTHONPATH' not in os.environ
with patch.object(p.shutil, 'which', side_effect=lambda n, **kw: None if n == 'flock' else n):
    try:
        p.host_preflight()
    except ValueError as e:
        assert 'flock' in str(e)
    else:
        raise AssertionError('Missing production tool accepted')

work = out/'private/work'
p.create_work(work)
rs = out/'r/slots'
# The production operator root's r/ directory may also be absent.
bin_dir = out/'bin'
bin_dir.mkdir()
for name in p.HOST_TOOLS:
    (bin_dir/name).symlink_to(shutil.which(name, path=p.HOST_PATH))
args = p.command(p.kit_bwrap(kh), kh, work, rs)
# Mask the installed host binary as well as excluding bwrap from PATH lookup.
mask = out/'unavailable'
mask.write_bytes(b'')
mask.chmod(0o600)
pos = args.index('--chdir')
args[pos:pos] = ['--ro-bind', str(mask), '/usr/bin/bwrap']
env = dict(PATH=str(bin_dir), HOME='/absent', CUDA_VISIBLE_DEVICES='', LC_ALL='C')
script = 'set -e\nif command -v bwrap; then exit 91; fi\n'+p.namespace_probe(str(bw))

# Exercise tk_bwrap verbatim, including all staged bind flags. Tiny test sources
# stand in for archives; only target/source variables use fixture paths.
for n in ('stage/aws/u/ap/key/u', 'nx/runs', 'nx/u', 'nx/data2root', 'nx/models',
          'nr', 'stage/c7d31ddd/data2root', 'stage/c7d31ddd/rr/models',
          'stage/epochs', 'job'):
    (work/'tmp'/n).mkdir(parents=True, exist_ok=True)
(work/'tmp/stage/aws/u/sentinel').write_text('pinned fixture')
c = (H/'build/fx/b/c.sh').read_text()
fn = c[c.index('tk_bwrap() {'):c.index('\ntk_env() {')]
script += '\nCUR='+shlex.quote(str(kh/'k/0.json'))+'\n'
script += '''tk_current() { /usr/bin/python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1]))[sys.argv[2]]; print(d["file"],d["sha256"])' "$CUR" "$1"; }
tk_step() { printf '%s\\n' "$*"; }
sha_is() { [[ "$(sha256sum < "$1" | cut -d' ' -f1)" == "$2" ]]; }
S=/tmp/stage U=/tmp/stage/aws/u NX=/tmp/nx NR=/tmp/nr K=key
AS=/home/jjyeung/as AL=/home/jjyeung/al X=/home/jjyeung/as/ap/key
P=/home/jjyeung/project EPOCHS=/home/jjyeung/epochs RR=rr TK_JOBDIR=/tmp/job
'''+fn+'''
tk_bwrap
"${BW[@]}" /bin/bash -c 'set -e
test "$(cat /home/jjyeung/as/sentinel)" = "pinned fixture"
test "$(cat /home/jjyeung/al/sentinel)" = "pinned fixture"
test -r /proc/self/status
test -w /dev/null
echo nested > /home/jjyeung/as/ap/key/runs/sentinel
echo job > /tmp/job/sentinel
if touch /home/jjyeung/forbidden; then exit 92; fi'
'''
r = subprocess.run(args, input=script, text=True, capture_output=True, env=env)
(out/'nested.log').write_text(r.stdout+r.stderr)
assert r.returncode == 0, r.stderr
assert (work/'tmp/nr/sentinel').read_text().strip() == 'nested'
assert (work/'tmp/job/sentinel').read_text().strip() == 'job'
assert not (kh/'runs/sentinel').exists()
report = dict(status='PASS', path=str(out), host_bwrap_masked=True,
              exact_outer_flags=True, verbatim_tk_bwrap=True, wrong_sha_refused=True,
              malformed_missing_nonexecutable_refused=True, missing_tool_refused=True,
              nonlogin_environment=True, production_preparation='NOT RUN')
(H/'evidence/fix8_admission/environment8c_tests.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
