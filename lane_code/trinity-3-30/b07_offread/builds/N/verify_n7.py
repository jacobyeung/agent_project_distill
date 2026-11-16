"""Verify sealed entry points, release manifests and storage without deleting files."""
from pathlib import Path
import hashlib,json,os,secrets,subprocess,tarfile
N=Path(__file__).resolve().parent;R=N.parent/'R'
W=json.loads((N/'out/N7_WORKSPACE.json').read_text());RAM=Path(W['ram'])
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
checks=[]
for key,archive,entry in [('n',N/'out/code.tar','native_read.py'),('vsi',R/'out/package_vsi.tar','0.py'),('revsi',R/'out/package_revsi.tar','0.py')]:
    root=RAM/('sealed_'+key+'_'+secrets.token_hex(6));root.mkdir()
    with tarfile.open(archive) as tf:
        for m in tf:
            assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
            p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(tf.extractfile(m).read())
    env=dict(os.environ,PYTHONPATH='/scratch/jjyeung/orch_n30/b07_offread/kit',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',A0_BUILD_SECRET_FILE=str(root/'absent_secret'))
    result=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B',str(root/entry),'--help'],cwd=root,env=env,capture_output=True,text=True,timeout=120)
    log=RAM/('sealed_'+key+'_'+secrets.token_hex(6)+'.log');log.write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stderr[-3000:]
    assert not any(p.name=='NAME_MAP.json' for p in root.rglob('*'))
    checks.append(dict(packet=key,sha256=sha(archive),returncode=0,log_sha256=sha(log),runtime_secret_unavailable=True))
for owner,label in ((N,'N7'),(R,'R5')):dump(owner/'out'/(label+'_SEALED_ENTRY_CHECK.json'),checks if owner==N else checks[1:])
active=json.loads((N/'vendor/ACTIVE.json').read_text());pin=json.loads((N/active['R']/'PIN.json').read_text())
assert all(sha(R/n)==h for n,h in pin['files'].items())
# Count every new or modified inode conservatively, including rewritten archives.
seen={};changed=[]
roots=[N/'offnative',N/'kit/tests',N/'out',R/'kit',R/'tests',R/'out']
roots += [p for p in (N/'vendor').glob('r_*') if p.stat().st_mtime_ns>=W['start_ns']]
for root in roots:
    for folder,dirs,names in os.walk(root):
        for name in names:
            p=Path(folder)/name;s=p.lstat()
            if s.st_mtime_ns>=W['start_ns']:seen[s.st_dev,s.st_ino]=s.st_size;changed.append(str(p))
for root in (N,R):
    for p in root.iterdir():
        if p.is_file() and p.lstat().st_mtime_ns>=W['start_ns']:
            s=p.lstat();seen[s.st_dev,s.st_ino]=s.st_size;changed.append(str(p))
ram_seen={}
for folder,dirs,names in os.walk('/dev/shm/b07_n7'):
    for name in names:
        p=Path(folder)/name;s=p.lstat();ram_seen[s.st_dev,s.st_ino]=s.st_size
size=sum(seen.values());ram_size=sum(ram_seen.values())
assert size<60_000_000,size
assert ram_size<4*1024**3,ram_size
prod=json.loads((N/'out/N7_PRODROOT.json').read_text())
assert all(row['bytes']<20_000_000 for row in prod)
storage=dict(new_or_modified_bytes=size,limit_bytes=60_000_000,ram_bytes=ram_size,ram_limit_bytes=4*1024**3,
    production_roots=[dict(root=v['root'],bytes=v['bytes']) for v in prod],production_root_limit_bytes=20_000_000,
    accounting='Unique new or modified inodes, including full replacement archives; unchanged hardlinked snapshot files excluded.',files=changed)
for owner,label in ((N,'N7'),(R,'R5')):dump(owner/'out'/(label+'_STORAGE.json'),storage if owner==N else {k:v for k,v in storage.items() if k!='files'})
for owner,label in ((N,'N7'),(R,'R5')):
    names={'RUN.md','DIFF.md','OPEN_INPUTS.md','out/NAME_MAP.json','out/NAME_MAP.json.sha256'}
    names.update(str(p.relative_to(owner)) for p in (owner/'out').glob(label+'*') if p.is_file())
    if owner==N:
        names.update(('out/code.tar','out/NATIVE_KIT_READY.md','out/CODE_PINS.json','out/DEPENDENCY_PINS.json','vendor/ACTIVE.json','SIZING.md','release_n7.py','verify_n7.py','validate_n7.py','rehearse_prodroot_n7.py'))
        names.update(str(p.relative_to(owner)) for d in ('offnative','kit/tests') for p in (owner/d).glob('*.py'))
        names.update(v+'/PIN.json' for v in active.values())
    else:
        names.update(('out/package_vsi.tar','out/package_revsi.tar','out/REBIND_READY.md','out/PACKAGE_PINS.json','out/OFFKIT_PINS.json'))
        names.update(str(p.relative_to(owner)) for p in (owner/'tests').glob('*.py'))
        names.update(str(p.relative_to(owner)) for p in (owner/'kit').glob('*.py'))
        names.update(str(p.relative_to(owner)) for k in ('vsi','revsi') for p in (owner/'kit'/k/'launcher').glob('*.py'))
    lines=[sha(owner/n)+'  '+n for n in sorted(names)]
    (owner/'SHIP_SHA256SUMS').write_text('\n'.join(lines)+'\n')
    assert all(sha(owner/line.split('  ',1)[1])==line.split('  ',1)[0] for line in lines)
print(json.dumps(dict(sealed_entries=len(checks),snapshot_matches=True,new_or_modified_bytes=size,ram_bytes=ram_size)))
