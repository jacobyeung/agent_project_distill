"""Verify sealed entry points, current source pins and storage bounds locally."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tarfile
N=Path(__file__).resolve().parent;R=N.parent/'R'
RAM=Path(json.loads((N/'out/N5_WORKSPACE.json').read_text())['ram'])
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
active=json.loads((N/'vendor/ACTIVE.json').read_text())
pin=json.loads((N/active['R']/'PIN.json').read_text())
assert all(sha(R/n)==h for n,h in pin['files'].items())
checks=[]
for key,archive,entry in (('n',N/'out/code.tar','native_read.py'),('vsi',R/'out/package_vsi.tar','0.py'),('revsi',R/'out/package_revsi.tar','0.py')):
    root=RAM/('sealed_'+key);root.mkdir(exist_ok=False)
    with tarfile.open(archive) as tf:
        for member in tf:
            assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            p=root/member.name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(tf.extractfile(member).read())
    env=dict(os.environ,PYTHONPATH='/scratch/jjyeung/orch_n30/b07_offread/kit',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    r=subprocess.run([sys.executable,'-B',str(root/entry),'--help'],cwd=root,env=env,capture_output=True,text=True,timeout=120)
    (RAM/('sealed_'+key+'.log')).write_text(r.stdout+r.stderr)
    checks.append(dict(key=key,archive_sha256=sha(archive),returncode=r.returncode,log_sha256=sha(RAM/('sealed_'+key+'.log'))))
    assert r.returncode==0,r.stderr
    # No logical name map is present in the staged file tree.
    assert not any(p.name=='NAME_MAP.json' for p in root.rglob('*'))
dump(N/'out/N5_SEALED_ENTRY_CHECK.json',checks);dump(R/'out/R3_SEALED_ENTRY_CHECK.json',checks[1:])
# Count unique new/modified inodes in the bounded source and evidence directories.
start=(N/'out/N5_WORKSPACE.json').stat().st_mtime_ns
seen={};touched=[]
roots=[N/'offnative',N/'kit/tests',N/'out',R/'kit',R/'tests',R/'out']
roots += [p for p in (N/'vendor').glob('r_*') if p.stat().st_mtime_ns>=start]
for root in roots:
    for folder,dirs,files in os.walk(root):
        for name in files:
            p=Path(folder)/name;s=p.stat()
            if s.st_mtime_ns>=start:
                seen[(s.st_dev,s.st_ino)]=s.st_size;touched.append(str(p))
for root in (N,R):
    for p in root.iterdir():
        if p.is_file() and p.stat().st_mtime_ns>=start:
            s=p.stat();seen[(s.st_dev,s.st_ino)]=s.st_size;touched.append(str(p))
ram={}
for folder,dirs,files in os.walk(RAM):
    for name in files:
        p=Path(folder)/name
        if p.is_symlink():continue
        s=p.stat();ram[(s.st_dev,s.st_ino)]=s.st_size
assert sum(seen.values())<60_000_000
assert sum(ram.values())<4*1024**3
storage=dict(conservative_new_or_modified_bytes=sum(seen.values()),limit_bytes=60_000_000,ram_bytes=sum(ram.values()),ram_limit_bytes=4*1024**3,files=touched)
dump(N/'out/N5_STORAGE.json',storage);dump(R/'out/R3_STORAGE.json',{k:v for k,v in storage.items() if k!='files'})
for root,label in ((N,'N5'),(R,'R3')):
    old=[line.split('  ',1)[1] for line in (root/'SHIP_SHA256SUMS').read_text().splitlines()]
    names={n for n in old if not (n.startswith('out/N') or n.startswith('out/R2') or n.startswith('out/VENDOR_REFRESH_N4'))}
    names.update(str(p.relative_to(root)) for p in (root/'out').glob(label+'*') if p.is_file())
    names.update(('out/NAME_MAP.json','out/NAME_MAP.json.sha256','RUN.md','DIFF.md','OPEN_INPUTS.md'))
    if root==N:
        names.update(('release_n5.py','verify_n5.py','kit/tests/test_n5.py','out/NATIVE_KIT_READY.md','out/VENDOR_REFRESH_N5.json','out/CODE_PINS.json','out/DEPENDENCY_PINS.json','vendor/ACTIVE.json'))
        names.update(value+'/PIN.json' for value in active.values())
    else:names.update(('tests/test_random_names.py','out/REBIND_READY.md','out/PACKAGE_PINS.json','out/ORCHARD_NAMES.md'))
    rows=[sha(root/name)+'  '+name for name in sorted(names) if (root/name).is_file()]
    (root/'SHIP_SHA256SUMS').write_text('\n'.join(rows)+'\n')
    assert all(sha(root/line.split('  ',1)[1])==line.split('  ',1)[0] for line in rows)
print(json.dumps({'sealed_entries':len(checks),'new_or_modified_bytes':sum(seen.values()),'ram_bytes':sum(ram.values()),'source_snapshot_matches':True}))
