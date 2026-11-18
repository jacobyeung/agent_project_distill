"""Run the exact embedded operator code using lane paths and the allowed Python."""
from pathlib import Path
import hashlib
import json
import stat
import subprocess
import sys
import tempfile

W = Path(__file__).resolve().parent
T = Path(tempfile.mkdtemp(prefix='scripts_', dir=W))
O = T/'okh7'
KH = O/'x_69d2930d'
BACK = O/'auth_x69'
(KH/'k').mkdir(parents=True)
(KH/'k/4.json').write_bytes((W/'4.p.json').read_bytes())
for p in (O, KH, KH/'k'):
    p.chmod(0o700)
(KH/'k/keep.json').write_bytes(b'{"unchanged":true}\n')

def run(name, args=(), ok=True):
    script=(W/name).read_text()
    code=script.split("<<'PY_AUTH'\n",1)[1].rsplit('\nPY_AUTH\n',1)[0]
    code=code.replace('/project/community/jjyeung/okh7', str(O))
    p=subprocess.run([sys.executable,'-B','-I','-c',code,*args],text=True,capture_output=True)
    assert (p.returncode==0)==ok, (name,p.returncode,p.stdout,p.stderr)
    print(name, 'PASS' if ok else 'EXPECTED REFUSAL', p.stdout.strip() or p.stderr.strip())
    return p

run('restore.sh',ok=False)
run('install.sh')
assert (KH/'k/4.json').read_bytes()==(W/'4.train.json').read_bytes()
assert (BACK/'4.p.json').read_bytes()==(W/'4.p.json').read_bytes()
assert stat.S_IMODE(BACK.stat().st_mode)==0o700
assert stat.S_IMODE((KH/'k/4.json').stat().st_mode)==0o600
run('install.sh',ok=False)
run('restore.sh', ['--all-workers-authorized-171377'])
assert (KH/'k/4.json').read_bytes()==(W/'4.p.json').read_bytes()
assert sorted(p.name for p in (KH/'k').iterdir())==['4.json','keep.json']
assert (KH/'k/keep.json').read_bytes()==b'{"unchanged":true}\n'
run('restore.sh', ['--all-workers-authorized-171377'],ok=False)
run('install.sh',ok=False)
assert (KH/'k/4.json').read_bytes()==(W/'4.p.json').read_bytes()
print('PASS byte-exact round trip, modes 0700/0600, original backup retained, k/ inventory unchanged, repeat operations refused')

# Wrong originals must refuse before creating a backup directory.
O=T/'wrong';KH=O/'x_69d2930d';BACK=O/'auth_x69'
(KH/'k').mkdir(parents=True)
(KH/'k/4.json').write_bytes(b'{}\n')
run('install.sh',ok=False)
assert not BACK.exists()
print('PASS wrong original sha refuses before backup or live mutation')
