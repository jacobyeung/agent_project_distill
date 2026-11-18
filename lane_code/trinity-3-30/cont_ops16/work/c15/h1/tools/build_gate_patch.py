"""Build a deterministic two-file patch for an existing prepared round-4 bundle."""
import base64,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
target=H/'evidence/fix6_before/payload'
if not target.exists():target=H/'payload'
records={}
for name in ('g.sh','sums.txt'):
    old=(H/'evidence/fix5_before/payload'/name).read_bytes()
    new=(target/name).read_bytes()
    records[name]=dict(old=sha(old),new=sha(new),data=base64.b64encode(new).decode())
old=(H/'evidence/fix5_before/payload/sums.txt').read_text().splitlines()
new=(target/'sums.txt').read_text().splitlines()
assert len(old)==len(new)
assert [a for a,b in zip(old,new) if a!=b]==[records['g.sh']['old']+'  g.sh']
assert [b for a,b in zip(old,new) if a!=b]==[records['g.sh']['new']+'  g.sh']
script='''#!/bin/bash
set -euo pipefail
umask 077
python3 -B - <<'P'
import base64,hashlib,json,os,stat,subprocess
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28')
'''+ 'records='+repr(records)+'''\ndef sha(data):return hashlib.sha256(data).hexdigest()
try:
    for p in (B.parent,B):
        if p.is_symlink() or not p.is_dir() or stat.S_IMODE(p.stat().st_mode)!=0o700:
            raise ValueError('bundle and parent must be real mode-0700 directories')
    for name in ('gate.json','ready.json','compare.json'):
        if (B/name).exists() or (B/name).is_symlink():raise ValueError('gate or final evidence already exists')
    prepared={}
    for name,r in records.items():
        p=B/name
        if not stat.S_ISREG(p.lstat().st_mode) or p.stat().st_nlink!=1:raise ValueError('linked patch target: '+name)
        data=p.read_bytes()
        if sha(data)!=r['old']:raise ValueError('old bytes differ: '+name)
        for suffix in ('.r4','.r5'):
            if (B/(name+suffix)).exists() or (B/(name+suffix)).is_symlink():raise ValueError('patch backup or temporary target exists')
        payload=base64.b64decode(r['data'],validate=True)
        if sha(payload)!=r['new']:raise ValueError('embedded patch digest differs: '+name)
        prepared[name]=(payload,stat.S_IMODE(p.stat().st_mode))
    subprocess.run(['sha256sum','-c','sums.txt'],cwd=B,check=True)
    # Prepare both new files before changing either active file. Every old byte is retained.
    for name,(payload,mode) in prepared.items():
        with (B/(name+'.r5')).open('xb') as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
        (B/(name+'.r5')).chmod(mode)
    for name in prepared:
        (B/name).rename(B/(name+'.r4'))
        (B/(name+'.r5')).rename(B/name)
    for name,r in records.items():
        if sha((B/name).read_bytes())!=r['new'] or sha((B/(name+'.r4')).read_bytes())!=r['old']:
            raise ValueError('patch readback differs')
    subprocess.run(['sha256sum','-c','sums.txt'],cwd=B,check=True)
except (OSError,ValueError,subprocess.CalledProcessError) as exc:
    raise SystemExit('Patch refused or incomplete: '+str(exc))
print('Patch verified. Prepared evidence retained. Run g.sh with PY_GATE and BW_GATE.')
P
'''
p=H/'build/g_patch.sh';p.write_text(script);p.chmod(0o700)
assert p.stat().st_size<1_000_000
print('g_patch.sh',p.stat().st_size,sha(p.read_bytes()))
