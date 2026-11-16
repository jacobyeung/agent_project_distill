"""Pinned local staging through build R's reviewed archive reader."""
from pathlib import Path
from .paths import r_launcher
from .io import owned, sha, dump

def archive(source, expected_sha256, destination, *, max_bytes):
    source=Path(source)
    destination=owned(destination)
    if source.stat().st_size>max_bytes or sha(source)!=expected_sha256:
        raise ValueError('staging archive identity or byte limit differs')
    if destination.exists():
        raise ValueError('stage destination exists; no retry or overwrite')
    destination.mkdir(parents=True)
    launcher=r_launcher().launcher('revsi999t32')
    with source.open('rb') as stream:
        files=launcher.S.extract_stream(stream,destination,step=None,limit=max_bytes,links=False)
    receipt=dict(source_sha256=expected_sha256,files=files,bytes=sum(v['bytes'] for v in files.values()),
                 source='Build R orchard_stage.extract_stream; links=False')
    dump(destination/'RECEIPT.json',receipt)
    return receipt

def validate_media(entries, *, production):
    names=[r['relative_path'] for r in entries]
    if len(names)!=len(set(names)):
        raise ValueError('duplicate media path')
    missing=[]
    import re
    for row in entries:
        name=Path(row['relative_path'])
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('unsafe media path')
        if not re.fullmatch('[0-9a-f]{64}',row.get('sha256') or '') or not isinstance(row.get('bytes'),int):
            missing.append(row['relative_path'])
    if production and missing:
        raise ValueError('media lacks content pins: '+str(len(missing)))
    return dict(files=len(entries),missing=missing)


def reviewed_modules(benchmark='revsi999t32'):
    """Import the reviewed implementations without modifying their source bytes."""
    from .paths import R, module
    import sys
    root=R/('kit/revsi/launcher' if benchmark=='revsi999t32' else 'kit/vsi/launcher')
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    import s1, export_stage, gate
    for obj,name in ((s1,'s1.py'),(export_stage,'export_stage.py'),(gate,'gate.py')):
        if Path(obj.__file__).resolve()!=root/name:
            raise ValueError('reviewed staging module shadowed: '+name)
    return s1,export_stage,gate


def stage_reviewed(root, config, physical, *, benchmark='revsi999t32', media_sources=None):
    """The R gate selects step-544 or the authenticated D0 stager unchanged."""
    s1, export_stage, gate=reviewed_modules(benchmark)
    gate.validate(config)
    import orchard_stage
    originals=[]
    source_originals=[]
    # Runtime symlinks retain R's checks; hard links are refused before extraction.
    for owner in (s1,orchard_stage):
        original=owner.unpack
        originals.append((owner,original))
        def checked_unpack(path,destination,_original=original,**kwargs):
            reject_hardlinks(path)
            return _original(path,destination,**kwargs)
        owner.unpack=checked_unpack
        if media_sources is not None and hasattr(owner,'video_source'):
            source_originals.append((owner,owner.video_source))
            def media_source(row,media_root):
                return Path(media_sources[row['relative_path']])
            owner.video_source=media_source
    try:
        receipt=gate.stage(root,config,physical)
        gate.after(root,config,receipt)
        return receipt
    finally:
        for owner,original in originals:owner.unpack=original
        for owner,original in source_originals:owner.video_source=original


def stage_files(entries, destination, *, benchmark='revsi999t32'):
    """Copy pinned tower/media files using R's hash-checked streaming primitive."""
    s1,_,_=reviewed_modules(benchmark)
    destination=owned(destination)
    destination.mkdir(parents=True,exist_ok=False)
    seen=set();receipts={}
    for row in entries:
        name=row['logical_path']
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or name in seen:
            raise ValueError('unsafe or duplicate staged path')
        seen.add(name)
        target=owned(destination/path);target.parent.mkdir(parents=True,exist_ok=True)
        receipts[name]=s1.copy_parts([row],target,lambda part:Path(part['path']).open('rb'),
                                     expected_sha=row['sha256'],check_space=True)
    dump(destination/'STAGED.json',receipts)
    return receipts


def reject_hardlinks(path):
    import tarfile
    with tarfile.open(path) as archive:
        for item in archive:
            if item.islnk():raise ValueError('input tar contains a hard link: '+item.name)
