"""Build the guarded local-to-operator patch; retain every replaced byte and receipt."""
import base64,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1];old=H/'evidence/fix6_before/payload'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={n:dict(old=sha(old/n) if (old/n).exists() else None,new=sha(H/'payload'/n),data=base64.b64encode((H/'payload'/n).read_bytes()).decode()) for n in sorted(p.name for p in (H/'payload').iterdir() if p.is_file()) if not (old/n).exists() or sha(old/n)!=sha(H/'payload'/n)}
ids=json.loads((H/'ids.json').read_text());oldids=json.loads((old/'ids.json').read_text())
script='''#!/bin/bash
set -euo pipefail
umask 077
python3 -B - <<'P'
import base64,hashlib,json,os,stat,subprocess
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28')
'''+f'records={records!r}\nold_identity={oldids["identity"]!r}\nnew_kit={ids["tokens"]["kit"]!r}\nnew_root={ids["tokens"]["root"]!r}\n'+'''
backup=B/'v_8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exists(p):return p.exists() or p.is_symlink()
# All refusals precede changes; mutable evidence is checked semantically and retained verbatim.
for p in (B.parent,B):
    if p.is_symlink() or not p.is_dir() or stat.S_IMODE(p.stat().st_mode)!=0o700:
        raise SystemExit('Patch refused: directory must be private')
for p in (backup,B.parent/('x_'+new_kit),B.parent/'r'/new_root):
    if exists(p):raise SystemExit('Patch refused: target exists')
prepared={}
for n,r in records.items():
    p=B/n
    if r['old'] is None:
        if exists(p):raise SystemExit('Patch refused: new target exists '+n)
    elif not stat.S_ISREG(p.lstat().st_mode) or p.stat().st_nlink!=1:
        raise SystemExit('Patch refused: linked target '+n)
    if n in ('review.json','staging.json'):
        value=json.loads(p.read_text())
        if value.get('config_sha256')!=old_identity:raise SystemExit('Patch refused: foreign evidence '+n)
    elif r['old'] is not None and sha(p)!=r['old']:raise SystemExit('Patch refused: old bytes differ '+n)
    raw=base64.b64decode(r['data'],validate=True)
    if hashlib.sha256(raw).hexdigest()!=r['new']:raise SystemExit('Patch refused: embedded digest '+n)
    prepared[n]=(raw,stat.S_IMODE(p.stat().st_mode) if r['old'] is not None else 0o600)
subprocess.run(['sha256sum','-c','sums.txt'],cwd=B,check=True)
# Retire identity-bound evidence and derived directories; leave routing archive/t/u and old KH alone.
retire=['p','e','q','p.json','e.json','c.json','archive.json','gate.json','ready.json',
        'result.json','compare.json','anon.json','go.json']
for n in retire:
    if (B/n).is_symlink():raise SystemExit('Patch refused: linked evidence '+n)
backup.mkdir(mode=0o700)
prior={n:sha(B/n) for n,r in records.items() if r['old'] is not None}
for n,(raw,mode) in prepared.items():
    with (backup/(n+'.new')).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    (backup/(n+'.new')).chmod(mode)
for n in retire:
    if exists(B/n):(B/n).rename(backup/n)
for n in records:
    if n in prior:(B/n).rename(backup/n)
    (backup/(n+'.new')).rename(B/n)
    if sha(B/n)!=records[n]['new'] or (n in prior and sha(backup/n)!=prior[n]):raise SystemExit('Patch readback differs')
subprocess.run(['sha256sum','-c','sums.txt'],cwd=B,check=True)
print('Patch verified. Selection pins verified. Independent review, certification and the production CPU proof are required before go.json.')
P
'''
p=H/'build/c_patch.sh';p.write_text(script);p.chmod(0o700)
(H/'evidence/fix8_patch_manifest.json').write_text(json.dumps({n:{k:v for k,v in r.items() if k!='data'} for n,r in records.items()},indent=2)+'\n')
print('c_patch.sh',p.stat().st_size,sha(p),'changed',list(records))
