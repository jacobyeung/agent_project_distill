"""Resolve recovered local evidence only after checking its pinned bytes."""
from pathlib import Path
from rebind import ROOT,load,sha
from cprime_gate import digest

SNAP=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_08f3a7b2')
A=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_9dd2fbb7')

def launch_contract():
    source=Path(load(SNAP/'out/proof/DERIVATION.json')['fixture_paths'][0])/'k/launch.json'
    contract=load(source)['in_job_admission']
    assert digest(contract)==load(SNAP/'out/operator/ids.json')['contract']
    return contract

def local_pin(pin):
    name=Path(pin['path']).name
    choices=[ROOT/'out/records'/name,A/'work/records'/name,ROOT/'work/records'/name]
    for p in choices:
        if p.is_file() and sha(p)==pin['sha256']:return {**pin,'path':str(p)}
    raise FileNotFoundError('Missing pinned input '+str(pin)+'; checked '+str(choices))

def recover_h1():
    """Recover only exact manifest-pinned H1 bytes into a local writable copy."""
    import io,os,sys,tarfile,hashlib
    from rebind import H,write,enc
    source=H/'build/fx';dest=ROOT/'work/cprime_h1/fx';dest.mkdir(parents=True,exist_ok=True)
    manifest={n:h for h,n in (line.split('  ',1) for line in (source/'SHA256SUMS.txt').read_text().splitlines())}
    donors={}
    # The mirror preserves the modes needed to reproduce D0's pinned tar.
    d0=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/base/tree_b01ce449')
    sys.path.insert(0,str(ROOT/'work/tree'))
    from student_pilot.source_seal import inventory
    payload=io.BytesIO()
    with tarfile.open(fileobj=payload,mode='w') as tf:
        for name in sorted(inventory(d0)):
            p=d0/name;raw=p.read_bytes();m=tarfile.TarInfo(name);m.size=len(raw)
            m.mode=0o755 if os.access(p,os.X_OK) else 0o644;tf.addfile(m,io.BytesIO(raw))
    raw=payload.getvalue();name='k/t_b01ce449beffe35b.tar';assert hashlib.sha256(raw).hexdigest()==manifest[name]
    p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);donors[sha(p)]=p
    for root in (ROOT/'out/operator',A/'work/records',ROOT/'work/records'):
        for p in root.iterdir():
            if p.is_file():donors[sha(p)]=p
    sys.path.insert(0,str(ROOT/'work/tree'))
    from student_pilot.source_seal import inventory
    from student_pilot.p3_provenance import source_files
    d0=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/base/tree_b01ce449')
    original=H/'build/tree';files={**inventory(d0),**inventory(original)}
    expected=__import__('derive_deployment').H1_TREE
    assert digest(files)==expected
    tree=ROOT/'work/cprime_h1/tree';tree.mkdir(parents=True,exist_ok=True)
    payload=io.BytesIO()
    with tarfile.open(fileobj=payload,mode='w') as tf:
        for name,h in sorted(files.items()):
            src=original/name if (original/name).is_file() else d0/name
            raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
            p=tree/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            mode=0o755 if (d0/name).exists() and os.access(d0/name,os.X_OK) else 0o644
            p.chmod(mode);m=tarfile.TarInfo(name);m.size=len(raw);m.mode=mode;tf.addfile(m,io.BytesIO(raw))
    archive_name='k/t_'+expected[:16]+'.tar';raw=payload.getvalue();assert hashlib.sha256(raw).hexdigest()==manifest[archive_name]
    arc=dest/archive_name;arc.parent.mkdir(parents=True,exist_ok=True);arc.write_bytes(raw);donors[sha(arc)]=arc
    import importlib.util
    spec=importlib.util.spec_from_file_location('recovered_h1_provenance',tree/'student_pilot/p3_provenance.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sources={str(p.relative_to(tree)):sha(p) for p in module.source_files([tree/'student_pilot/carrier_c1_run.py'])}
    code=dict(schema='c1-sealed-source-v1',commit='sha256:'+expected,tree_sha256=expected,files=files,sources=sources,operation_sources=sources,
        archive=load(source/'k/launch.json')['source_seal']['archive'])
    raw=(enc(code)+'\n').encode();assert hashlib.sha256(raw).hexdigest()==manifest['k/7.json']
    p=dest/'k/7.json';p.write_bytes(raw);donors[sha(p)]=p
    restored=[];missing=[]
    for n,h in manifest.items():
        src=source/n if (source/n).is_file() else donors.get(h)
        if src is None:missing.append(dict(file=n,sha256=h));continue
        assert sha(src)==h,n
        p=dest/n;p.parent.mkdir(parents=True,exist_ok=True)
        if p!=src:p.write_bytes(src.read_bytes());p.chmod(src.stat().st_mode & 0o777)
        if not (source/n).is_file():restored.append(n)
    (dest/'SHA256SUMS.txt').write_bytes((source/'SHA256SUMS.txt').read_bytes())
    write(ROOT/'out/H1_RECOVERY_CPRIME.json',dict(source=str(source),recovered=str(dest),source_manifest_sha256=sha(source/'SHA256SUMS.txt'),
        reconstructed_tree_sha256=expected,restored=restored,missing=missing))
    return dest
