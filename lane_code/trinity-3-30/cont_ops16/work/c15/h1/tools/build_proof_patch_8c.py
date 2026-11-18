"""Build the proof-only patch for an installed round-8 bundle."""
import base64
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parents[1]
OLD = H/'evidence/fix8c_before/payload'
NAME = 'a_8c74b291.sh'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
prior = {n: sha((OLD/n).read_bytes()) for n in (NAME, 'sums.txt')}
assert prior[NAME] == 'f1f6a1519b6a27a190363672bd8a428b2e635e367461c87a0150c3a440aba40a'
assert prior['sums.txt'] == '80bb318e2af519f12f382b9f5e947fbbffdc447c5120c1dde607fb997fbff06c'
raw = (H/'build'/NAME).read_bytes()
assert raw == (H/'payload'/NAME).read_bytes()
old_line = (prior[NAME]+'  '+NAME+'\n').encode()
new_line = (sha(raw)+'  '+NAME+'\n').encode()
sums = (OLD/'sums.txt').read_bytes()
assert sums.count(old_line) == 1
new_sums = sums.replace(old_line, new_line)
assert new_sums == (H/'payload/sums.txt').read_bytes()
after = {NAME: sha(raw), 'sums.txt': sha(new_sums)}
script = '''#!/bin/bash
set -euo pipefail
umask 077
exec /usr/bin/python3 -I -B - <<'P'
import base64,hashlib,os,stat
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28')
'''+f'name={NAME!r}\nprior={prior!r}\nafter={after!r}\nblob={base64.b64encode(raw).decode()!r}\n'+'''
backup=B/'v_8c'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def refuse(why):raise SystemExit('Patch refused: '+why)
for p in (B.parent,B):
    info=p.lstat()
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode)!=0o700 or info.st_uid!=os.geteuid():
        refuse('directory must be owned and private: '+str(p))
if backup.exists() or backup.is_symlink():refuse('backup exists')
old={};modes={}
for n,h in prior.items():
    p=B/n;info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.geteuid():
        refuse('target must be owned, regular and unlinked: '+n)
    old[n]=p.read_bytes();modes[n]=stat.S_IMODE(info.st_mode)
    if sha(old[n])!=h:refuse('old hash differs: '+n)
raw=base64.b64decode(blob,validate=True)
line=(prior[name]+'  '+name+'\\n').encode()
if old['sums.txt'].splitlines(keepends=True).count(line)!=1:refuse('checksum line differs')
prepared={name:raw,'sums.txt':old['sums.txt'].replace(line,(sha(raw)+'  '+name+'\\n').encode())}
if any(sha(v)!=after[n] for n,v in prepared.items()):refuse('new hash differs')
# All content and path refusals precede mutation. Keep the replaced bytes.
backup.mkdir(mode=0o700)
for n,v in prepared.items():
    p=backup/(n+'.new')
    with p.open('xb') as f:f.write(v);f.flush();os.fsync(f.fileno())
    p.chmod(modes[n])
for n in prepared:
    (B/n).rename(backup/n)
    (backup/(n+'.new')).rename(B/n)
    if sha((B/n).read_bytes())!=after[n] or sha((backup/n).read_bytes())!=prior[n]:
        raise SystemExit('Patch readback differs: '+n)
print('Proof patch verified; old proof and sums retained in '+str(backup))
P
'''
dst=H/'build/c_patch_8c.sh'
dst.write_text(script);dst.chmod(0o700)
(H/'evidence/fix8c_patch_manifest.json').write_text(json.dumps(dict(
    old=prior,new=after,patch_sha256=sha(script.encode()),backup='BUN/v_8c',
    unchanged=['KH manifest','config identity','go binding','s.sh']),indent=2)+'\n')
print(dst.name,len(script),sha(script.encode()))
