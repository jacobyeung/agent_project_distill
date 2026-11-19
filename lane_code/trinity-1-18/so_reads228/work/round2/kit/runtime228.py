"""Local-only runtime extraction with package namespace links preserved; Python 3.6 compatible."""
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
        if beneath(path,prefix):
            target=Path(mapping[prefix])/path.relative_to(prefix)
            local(target.parent)
            return target
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
    stream=PartStream(group['parts'],archive_mapping);inventory={};members=[];seen=set();total=0;conflicts=[]
    namespace=group['namespace_map']
    try:
        with tarfile.open(fileobj=stream,mode='r|*') as archive:
            for member in archive:
                name=str(Path(member.name))
                if name in seen:raise Refusal('Duplicate runtime member')
                seen.add(name)
                members.append(dict(name=name,bytes=member.size,type=member.type.decode('ascii'),link=member.linkname))
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
                    link=member.linkname  # Preserve the package link; bwrap supplies its absolute target.
                    if target.is_symlink():
                        if os.readlink(str(target))!=link:conflicts.append(str(target))
                    elif target.exists():conflicts.append(str(target))
                    else:target.symlink_to(link)
                    inventory[str(target)]=dict(link=link);continue
                if member.islnk():
                    source=runtime_path(member.linkname,namespace)
                    if source is None or source.is_symlink() or not source.is_file():raise Refusal('Unsafe runtime hardlink')
                    if target.exists():
                        if not os.path.samefile(str(source),str(target)):conflicts.append(str(target))
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
                                if old.read(len(chunk))!=chunk:conflicts.append(str(target))
                            else:new.write(chunk)
                    if old is not None and old.read(1):conflicts.append(str(target))
                finally:
                    if old:old.close()
                    if new:new.close()
                if n!=member.size:raise Refusal('Truncated runtime member')
                if not exists:target.chmod(member.mode&0o777)
                inventory[str(target)]=dict(bytes=n,sha256=digest.hexdigest())
        # tar readers may stop at the end marker before consuming the final pinned part.
        while stream.read(1024*1024):pass
    finally:stream.close()
    if conflicts:raise Refusal('Existing runtime members differ; preserved: '+str(sorted(set(conflicts))))
    if group.get('sha256') and group['sha256']!=stream.digest.hexdigest():raise Refusal('Runtime archive hash differs')
    return dict(files=inventory,members=members,expanded_bytes=total,archive_sha256=stream.digest.hexdigest())

def relocate_runtime(plan, *, enabled=False):
    raise Refusal('Runtime relocation is OFF and unavailable: use the package namespace; pinned bytes must remain unchanged')
