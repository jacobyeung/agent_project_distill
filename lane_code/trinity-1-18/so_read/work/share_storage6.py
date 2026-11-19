"""Share immutable base files in completed pre-task fixtures; preserve every path."""
import hashlib,json,os,subprocess,uuid
from datetime import datetime,timezone
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
m=json.loads((L/'out_round6/patches/MANIFEST.json').read_text());base=Path(m['verification_root'])/'src'
cut=datetime(2026,11,19,15,13,3,tzinfo=timezone.utc).timestamp()
count=saved=0
for d in (L/'work/test-artifacts').iterdir():
    if d.stat().st_mtime>=cut:continue
    root=d/'built/src'
    if not root.is_dir():continue
    for rel,pin in m['base_pin']['inventory'].items():
        p=root/rel;ref=base/rel
        if not p.is_file() or p.is_symlink():continue
        st=p.stat()
        if st.st_size<1024 or st.st_nlink>1 or st.st_ino==ref.stat().st_ino:continue
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=pin:continue
        assert raw==ref.read_bytes()
        temp=p.with_name(p.name+'.share6'+uuid.uuid4().hex)
        os.link(ref,temp);os.replace(temp,p)
        count+=1;saved+=len(raw)
    if saved>250_000_000:break
print('Immutable fixture paths preserved:',count,'unique bytes shared:',saved)
print(subprocess.check_output(['du','-sb',str(L)],text=True).strip())
