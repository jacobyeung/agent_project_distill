"""Local-only runtime extraction and explicit path relocation; Python 3.6 compatible."""
import hashlib
import os
from pathlib import Path
import shutil
import tarfile
from common228 import Refusal, beneath, checked, local, read, sha, write

AP='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap'
FSW='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
UV='/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu'

def runtime_path(name, mapping):
    path=Path(name)
    if path.is_absolute() or '..' in path.parts:raise Refusal('Unsafe runtime member')
    for prefix in sorted(mapping,key=len,reverse=True):
        if beneath(path,prefix):return local(Path(mapping[prefix])/path.relative_to(prefix))
    if any(beneath(Path(prefix),path) for prefix in mapping):return None
    raise Refusal('Unregistered runtime namespace: '+name)

def runtime_link(name, link, mapping):
    # Only the two absolute links admitted by the package's orchard_stage are allowed.
    absolute={
        'sj/envs/p1cpu/bin/python3.12':'/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12',
        'm/ap/19252904/e/bin/python':UV+'/bin/python3.12'}
    if Path(link).is_absolute():
        if absolute.get(name)!=link:raise Refusal('Unregistered absolute runtime link')
        return runtime_path('sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12',mapping)
    resolved=os.path.normpath(str(Path(name).parent/link))
    if resolved.startswith('../'):raise Refusal('Runtime link escapes archive')
    return runtime_path(resolved,mapping)

def extract_runtime(group, archive_mapping, *, limit):
    from stage228 import PartStream
    stream=PartStream(group['parts'],archive_mapping);inventory={};seen=set();total=0
    namespace=group['namespace_map']
    try:
        with tarfile.open(fileobj=stream,mode='r|*') as archive:
            for member in archive:
                name=str(Path(member.name))
                if name in seen:raise Refusal('Duplicate runtime member')
                seen.add(name)
                if len(seen)>200000:raise Refusal('Runtime member count exceeds package limit')
                target=runtime_path(name,namespace)
                if target is None:
                    if not member.isdir():raise Refusal('Namespace parent must be a directory')
                    continue
                if member.isdir():
                    if target.is_symlink():raise Refusal('Runtime directory is a symlink')
                    target.mkdir(parents=True,exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True)
                # Do not write through a directory symlink, even one pointing elsewhere on scratch.
                if target.parent.resolve()!=target.parent.absolute():raise Refusal('Runtime parent crosses a symlink')
                if member.issym():
                    resolved=runtime_link(name,member.linkname,namespace)
                    if resolved is None:raise Refusal('Runtime link targets namespace parent')
                    link=os.path.relpath(str(resolved),str(target.parent))
                    if target.is_symlink():
                        if os.readlink(str(target))!=link:raise Refusal('Existing runtime link differs')
                    elif target.exists():raise Refusal('Existing runtime path is not a link')
                    else:target.symlink_to(link)
                    inventory[str(target)]=dict(link=link);continue
                if member.islnk():
                    source=runtime_path(member.linkname,namespace)
                    if source is None or source.is_symlink() or not source.is_file():raise Refusal('Unsafe runtime hardlink')
                    if target.exists():
                        if not os.path.samefile(str(source),str(target)):raise Refusal('Existing runtime hardlink differs')
                    else:os.link(str(source),str(target))
                    inventory[str(target)]=dict(hardlink=str(source));continue
                if not member.isfile() or target.is_symlink():raise Refusal('Unsafe runtime file')
                total+=member.size
                if total>limit:raise Refusal('Runtime expansion exceeds aggregate allowance')
                digest=hashlib.sha256();n=0;exists=target.exists()
                old=target.open('rb') if exists else None
                new=None if exists else target.open('xb')
                try:
                    with archive.extractfile(member) as source:
                        for chunk in iter(lambda:source.read(1024*1024),b''):
                            digest.update(chunk);n+=len(chunk)
                            if old is not None:
                                if old.read(len(chunk))!=chunk:raise Refusal('Existing runtime file differs: '+str(target))
                            else:new.write(chunk)
                    if old is not None and old.read(1):raise Refusal('Existing runtime file is longer')
                finally:
                    if old:old.close()
                    if new:new.close()
                if n!=member.size:raise Refusal('Truncated runtime member')
                if not exists:target.chmod(member.mode&0o777)
                inventory[str(target)]=dict(bytes=n,sha256=digest.hexdigest())
        # tar readers may stop at the end marker before consuming the final pinned part.
        while stream.read(1024*1024):pass
    finally:stream.close()
    return dict(files=inventory,expanded_bytes=total,archive_sha256=stream.digest.hexdigest())

def relocate_runtime(plan, *, enabled=False):
    if not enabled:raise Refusal('Runtime relocation is OFF; requires explicit --relocate-runtime')
    stage=local(plan['stage_root']);data=local(Path(plan['logical'])/'d')
    receipt=stage/'RUNTIME_RELOCATION.json'
    if receipt.exists():
        result=read(receipt)
        for row in result['files']:checked(row['path'],row['after'])
        return result
    extracted={}
    for name in ('INPUT_EXTRACTION.json','RUNTIME_EXTRACTION.json'):
        extracted.update(read(stage/name)['files'])
    env=plan['environment'];base=local(env['local_base_env'])
    replacements={AP:str(stage/'runtime/m/ap'),FSW:str(stage/'runtime/fsw'),
        UV:str(Path(env['local_base_python']).parents[1])}
    result=dict(enabled=True,changes='Absolute runtime prefixes only; sealed reader and overlay bytes unchanged.',files=[])
    # Preserve and authenticate each file before replacing an Orchard namespace prefix.
    # v/boot.py is included because it may name the base interpreter or stdlib path.
    for path in (data/'v/py',data/'v/boot.py',base/'pyvenv.cfg'):
        local(path)
        if str(path) not in extracted:raise Refusal('Runtime relocation input lacks an extraction pin: '+str(path))
        checked(path,extracted[str(path)]);before=path.read_bytes();after=before
        for source,dest in replacements.items():after=after.replace(source.encode(),dest.encode())
        if b'/lustre/' in after or b'/home/' in after:raise Refusal('Unresolved external prefix in '+str(path))
        saved=stage/'relocation_originals'/str(path.relative_to('/scratch/jjyeung'))
        saved.parent.mkdir(parents=True,exist_ok=True)
        with saved.open('xb') as stream:stream.write(before)
        path.write_bytes(after)
        result['files'].append(dict(path=str(path),original=str(saved),before=extracted[str(path)],
            after=dict(bytes=len(after),sha256=hashlib.sha256(after).hexdigest())))
    if not (base/'bin/python').is_file():raise Refusal('Relocated runtime interpreter is missing')
    write(receipt,result);return result
