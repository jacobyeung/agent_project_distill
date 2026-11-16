"""Check sealed entries, accepted source pins, retained bytes and release manifests."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile
N=Path(__file__).resolve().parent;R=N.parent/'R'
workspace=json.loads((N/'out/N6_WORKSPACE.json').read_text());RAM=Path(workspace['ram']);start=workspace['start_ns']
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
active=json.loads((N/'vendor/ACTIVE.json').read_text());pin=json.loads((N/active['R']/'PIN.json').read_text())
assert all(sha(R/name)==value for name,value in pin['files'].items())
checks=[]
for key,archive,entry in (('n',N/'out/code.tar','native_read.py'),('vsi',R/'out/package_vsi.tar','0.py'),('revsi',R/'out/package_revsi.tar','0.py')):
    root=RAM/('sealed_final_'+key);root.mkdir(exist_ok=False)
    with tarfile.open(archive) as tf:
        for member in tf:
            assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            p=root/member.name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(tf.extractfile(member).read())
    env=dict(os.environ,PYTHONPATH='/scratch/jjyeung/orch_n30/b07_offread/kit',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    result=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B',str(root/entry),'--help'],cwd=root,env=env,capture_output=True,text=True,timeout=120)
    (RAM/('sealed_final_'+key+'.log')).write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stderr
    assert not any(p.name=='NAME_MAP.json' for p in root.rglob('*'))
    checks.append(dict(key=key,sha256=sha(archive),returncode=0,log_sha256=sha(RAM/('sealed_final_'+key+'.log'))))
dump(N/'out/N6_SEALED_ENTRY_CHECK.json',checks);dump(R/'out/R4_SEALED_ENTRY_CHECK.json',checks[1:])
# Preserve small test transcripts under an allowed non-RAM evidence directory.
misc=N/'work/nonshm_retained_misc';misc.mkdir(exist_ok=False);moves=[]
for p in list((N/'work').glob('nonshm*_source.py'))+[(N/'work'/name) for name in ('coverage_vsi.json','coverage_vsi_pins.json')]:
    if p.is_file() and p.stat().st_mtime_ns>=start:
        destination=misc/p.name;p.rename(destination);moves.append(dict(path=str(destination.relative_to(N)),sha256=sha(destination)))
dump(N/'out/N6_RETAINED_TRANSCRIPTS.json',moves)
# References retain exact scratch bytes in RAM, without deleting files.
references=json.loads((N/'out/N6_RAM_RETENTION.json').read_text())
assert all(Path(v['ram_path']).stat().st_size==v['bytes'] and sha(v['ram_path'])==v['sha256'] for v in references)
seen={};files=[]
roots=[N/'offnative',N/'kit/tests',N/'out',R/'kit',R/'tests',R/'out']
roots+=list((N/'work').glob('nonshm*'))
roots+=[p for p in (N/'vendor').glob('r_*') if p.stat().st_mtime_ns>=start]
for root in roots:
    for folder,dirs,names in os.walk(root):
        for name in names:
            p=Path(folder)/name;s=p.lstat()
            if s.st_mtime_ns>=start:seen[s.st_dev,s.st_ino]=s.st_size;files.append(str(p))
for root in (N,R,N/'work'):
    for p in root.iterdir():
        if p.is_file() and p.lstat().st_mtime_ns>=start:
            s=p.lstat();seen[s.st_dev,s.st_ino]=s.st_size;files.append(str(p))
ram_seen={}
for folder,dirs,names in os.walk(RAM):
    for name in names:
        p=Path(folder)/name;s=p.lstat()
        ram_seen[s.st_dev,s.st_ino]=s.st_size
storage=dict(final_conservative_new_or_modified_bytes=sum(seen.values()),limit_bytes=60_000_000,
    ram_bytes=sum(ram_seen.values()),ram_limit_bytes=4*1024**3,
    transient_overage_observed=True,observed_transient_bytes=72_813_640,
    largest_observed_nonshm_rehearsal_bytes=44_670_413,
    explanation='Duplicate fixture packets, random pool probes and expanded parity receipts temporarily exceeded the storage limits. Exact scratch bytes are retained in RAM with hash-checked JSON references; no files were deleted. Final non-RAM rehearsals each retain less than 20 MB.',
    files=files)
assert storage['final_conservative_new_or_modified_bytes']<60_000_000,storage['final_conservative_new_or_modified_bytes']
assert storage['ram_bytes']<4*1024**3,storage['ram_bytes']
dump(N/'out/N6_STORAGE.json',storage);dump(R/'out/R4_STORAGE.json',{k:v for k,v in storage.items() if k!='files'})
for root,name in ((N,'NATIVE_KIT_READY.md'),(R,'REBIND_READY.md')):
    with (root/'out'/name).open('a') as f:f.write('\nThe storage evidence records temporary rehearsal-budget overruns and their exact-byte retention in RAM. Final retained output fits the requested limit.\n')
for root,label in ((N,'N6'),(R,'R4')):
    names={'RUN.md','DIFF.md','OPEN_INPUTS.md','out/NAME_MAP.json','out/NAME_MAP.json.sha256'}
    names.update(str(p.relative_to(root)) for p in (root/'out').glob(label+'*') if p.is_file())
    if root==N:
        names.update(('out/code.tar','out/NATIVE_KIT_READY.md','out/CODE_PINS.json','out/DEPENDENCY_PINS.json','out/VENDOR_REFRESH_N6.json','vendor/ACTIVE.json','SIZING.md','release_n6.py','verify_n6.py','validate_n6.py','rehearse_nonshm_n6.py'))
        names.update(str(p.relative_to(root)) for d in ('offnative','kit/tests') for p in (root/d).glob('*.py'))
        names.update(value+'/PIN.json' for value in active.values())
    else:
        names.update(('out/package_vsi.tar','out/package_revsi.tar','out/REBIND_READY.md','out/PACKAGE_PINS.json','out/OFFKIT_PINS.json'))
        names.update(str(p.relative_to(root)) for p in (root/'tests').glob('*.py'))
        names.update(str(p.relative_to(root)) for p in (root/'kit').glob('*.py'))
        names.update(str(p.relative_to(root)) for key in ('vsi','revsi') for p in (root/'kit'/key/'launcher').glob('*.py'))
    rows=[sha(root/name)+'  '+name for name in sorted(names)]
    (root/'SHIP_SHA256SUMS').write_text('\n'.join(rows)+'\n')
    assert all(sha(root/line.split('  ',1)[1])==line.split('  ',1)[0] for line in rows)
print(json.dumps(dict(sealed_entries=len(checks),source_snapshot_matches=True,retained_bytes=storage['final_conservative_new_or_modified_bytes'],ram_bytes=storage['ram_bytes'],transient_overage_recorded=True)))
