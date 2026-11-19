"""Share unchanged source bytes in three named retained CPU fixtures."""
from pathlib import Path
import hashlib,json,os,uuid,subprocess
L=Path('/scratch/jjyeung/orch_n30/so_read');m=json.loads((L/'out_round5/patches/MANIFEST.json').read_text())
base=Path(m['verification_root'])/'src';count=0;saved=0
roots=['daa1422c05d34fb3ad406472cac5155a','c0d6c90c1c6e4755b0030ae8ce71a723','5b1d5df29bb34b6cb0ff872fb0084a0b']
for name in roots:
 root=L/'work/test-artifacts'/name/'built/src'
 for rel,pin in m['base_pin']['inventory'].items():
  p=root/rel;ref=base/rel
  if not p.is_file() or p.is_symlink() or p.stat().st_ino==ref.stat().st_ino:continue
  raw=p.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=pin:continue
  assert raw==ref.read_bytes()
  sole=p.stat().st_nlink==1
  tmp=p.with_name(p.name+'.share'+uuid.uuid4().hex)
  os.link(ref,tmp);os.replace(tmp,p)
  assert p.read_bytes()==raw
  count+=1;saved+=len(raw) if sole else 0
print('Preserved all paths and bytes; shared',count,'unchanged files across three named retained fixtures.')
print('Unique file bytes released:',saved)
print(subprocess.check_output(['du','-sb',str(L)],text=True).strip())
